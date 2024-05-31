import asyncio
import time
import aiohttp
import os

import aiohttp
import aiohttp.client_exceptions
import logging

from common.peer import Peer


async def ping(peer):
    alive = False
    seq = os.urandom(4).hex()

    logging.debug("[CLIENT]: probing", peer.ip, peer.port, seq)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{peer.ip}:{peer.port}/ping?seq={seq}") as response:
                if response.status == 200:
                    alive = True
    except Exception as e:
        logging.warning(e)

    peer.set_alive(alive)
    peer.set_epoch(int(time.time()))

    status_msg = "alive" if alive else "dead"
    logging.debug(f"[CLIENT]: Peer {peer.ip}:{peer.port} (seq:{seq}) is {status_msg}")
    return peer


async def alive_peers():
    peers = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/alive_peers") as response:
                if response.status == 200:
                    peer_list = await response.json()
                    peers = [Peer.from_dict(peer) for peer in peer_list]
                else:
                    logging.error("Failed to get alive peers, status code: {response.status}")
                return peers
    except aiohttp.client_exceptions.ClientConnectionError:
        logging.error("Make sure the HFFS service is up by running: python hffs.py start")
        return peers


async def timeout_coro(coro, timeout, default):
    try:
        return await asyncio.wait_for(coro, timeout)
    except TimeoutError:
        return default


async def search_coro(peer, repo_id, revision, file_name):
    """Check if a certain file exists in a peer's model repository

    Returns:
        Peer or None: if the peer has the target file, return the peer, otherwise None
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(f"http://{peer.ip}:{peer.port}/{repo_id}/resolve/{revision}/{file_name}") as response:
                if response.status == 200:
                    return peer
    except Exception:
        return None


async def do_search(peers, repo_id, revision, file_name):
    tasks = []

    async def search_peer_coro(peer):
        # for a single peer, search the model in it with search_coro, in addition
        # wrap search_coro with timeout_coro to have it finish in 10 seconds
        search = search_coro(peer, repo_id, revision, file_name)
        return await timeout_coro(search, 10, None)

    def all_finished(tasks):
        return all([task.done() for task in tasks])

    async with asyncio.TaskGroup() as g:
        for peer in peers:
            tasks.append(g.create_task(search_peer_coro(peer)))

        while not all_finished(tasks):
            await asyncio.sleep(1)
            print(".", end="")

        # add new line after the dots
        print("")

    return [task.result() for task in tasks if task.result() is not None]


async def search_model(peers, repo_id, file_name, revision):
    if not peers:
        logging.info("No active peers to search")
        return []

    logging.info("Will check the following peers:")
    logging.info(Peer.print_peers(peers))

    avails = await do_search(peers, repo_id, revision, file_name)

    logging.info("Peers who have the model:")
    logging.info(Peer.print_peers(avails))

    return avails


async def stop_server():
    """Send HTTP request to ask the server to stop"""
    pass
