import asyncio
import time
import os

import aiohttp
import aiohttp.client_exceptions
import logging

from ..common.peer import Peer
from huggingface_hub import hf_hub_url, get_hf_file_metadata
from ..common.settings import load_local_service_port, HFFS_API_PING, HFFS_API_PEER_CHANGE, HFFS_API_ALIVE_PEERS

logger = logging.getLogger(__name__)

LOCAL_HOST = "127.0.0.1"


def timeout_sess(timeout=60):
    return aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))


async def ping(peer, timeout=15):
    alive = False
    seq = os.urandom(4).hex()
    url = f"http://{peer.ip}:{peer.port}" + HFFS_API_PING + f"?seq={seq}"

    logger.debug(f"probing {peer.ip}:{peer.port}, seq = {seq}")

    try:
        async with timeout_sess(timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    alive = True
    except TimeoutError:
        pass
    except Exception as e:
        logger.warning(e)

    peer.set_alive(alive)
    peer.set_epoch(int(time.time()))

    status_msg = "alive" if alive else "dead"
    logger.debug(f"Peer {peer.ip}:{peer.port} (seq:{seq}) is {status_msg}")
    return peer


async def alive_peers(timeout=2):
    port = load_local_service_port()
    url = f"http://{LOCAL_HOST}:{port}" + HFFS_API_ALIVE_PEERS
    peers = []

    try:
        async with timeout_sess(timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    peer_list = await response.json()
                    peers = [Peer.from_dict(peer) for peer in peer_list]
                else:
                    err = f"Failed to get alive peers, HTTP status: {response.status}"
                    logger.error(err)
    except aiohttp.client_exceptions.ClientConnectionError:
        logger.warning("Cannot connect daemon for alive peers")
    except TimeoutError:
        logger.error("Timeout to connect daemon for alive peers")
    except Exception as e:
        logger.warning(e)

    return peers


async def search_coro(peer, repo_id, revision, file_name):
    """Check if a certain file exists in a peer's model repository

    Returns:
        Peer or None: if the peer has the target file, return the peer, otherwise None
    """
    try:
        async with timeout_sess(10) as session:
            async with session.head(f"http://{peer.ip}:{peer.port}/{repo_id}/resolve/{revision}/{file_name}") as response:
                if response.status == 200:
                    return peer
    except Exception:
        return None


async def do_search(peers, repo_id, revision, file_name):
    tasks = []

    def all_finished(tasks):
        return all([task.done() for task in tasks])

    async with asyncio.TaskGroup() as g:
        for peer in peers:
            coro = search_coro(peer, repo_id, revision, file_name)
            tasks.append(g.create_task(coro))

        while not all_finished(tasks):
            await asyncio.sleep(1)
            print(".", end="")

        # add new line after the dots
        print("")

    return [task.result() for task in tasks if task.result() is not None]


async def search_model(peers, repo_id, file_name, revision):
    if not peers:
        logger.info("No active peers to search")
        return []

    logger.info("Will check the following peers:")
    logger.info(Peer.print_peers(peers))

    avails = await do_search(peers, repo_id, revision, file_name)

    logger.info("Peers who have the model:")
    logger.info(Peer.print_peers(avails))

    return avails


async def get_model_etag(endpoint, repo_id, filename, revision='main'):
    url = hf_hub_url(
        repo_id=repo_id,
        filename=filename,
        revision=revision,
        endpoint=endpoint
    )

    metadata = get_hf_file_metadata(url)
    return metadata.etag


async def notify_peer_change(timeout=2):
    try:
        port = load_local_service_port()
    except LookupError:
        return

    url = f"http://{LOCAL_HOST}:{port}" + HFFS_API_PEER_CHANGE

    try:
        async with timeout_sess(timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.debug(f"Peer change http status: {response.status}")
    except TimeoutError:
        logger.error("Timeout to connect daemon for peer change")
    except Exception as e:
        logger.error(f"Peer change error: {e}")


async def stop_server():
    """Send HTTP request to ask the server to stop"""
    pass
