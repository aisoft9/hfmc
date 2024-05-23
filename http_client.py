import asyncio
import time
import aiohttp
import os

import aiohttp
import aiohttp.client_exceptions

from peer import Peer


async def ping(peer):
    alive = False
    seq = os.urandom(4).hex()

    print("[CLIENT]: probing", peer.ip, peer.port, seq)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{peer.ip}:{peer.port}/ping?seq={seq}") as response:
                if response.status == 200:
                    alive = True
    finally:
        peer.set_alive(alive)
        peer.set_epoch(int(time.time()))

        print(
            f"[CLIENT]: Peer {peer.ip}:{peer.port} (seq:{seq}) is {'alive' if alive else 'dead'}")
        return peer


async def alive_peers():
    peers = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://127.0.0.1:8000/alive_peers") as response:
                if response.status == 200:
                    peer_list = await response.json()
                    peers = [Peer.from_dict(peer) for peer in peer_list]
    except aiohttp.client_exceptions.ClientConnectionError:
        print(f"Make sure the HFFS service is up by running: python hffs.py start")
    finally:
        return peers


async def timeout_coro(coro, timeout, default):
    async def _():
        try:
            return await asyncio.wait_for(coro, timeout)
        except TimeoutError:
            return default
    return _()

async def search_model(peers, repo_id, revision, file_name):
    if not peers:
        return []
    
    async def do_search(peer):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
                print(f"http://{peer.ip}:{peer.port}/model/{repo_id}/resolve/{revision}/{file_name}")
                async with session.head(f"http://{peer.ip}:{peer.port}/model/{repo_id}/resolve/{revision}/{file_name}") as response:
                    if response.status == 200:
                        return True
        except Exception:
            return False

    tasks = [do_search(peer) for peer in peers]
    results = await asyncio.gather(*tasks)
    return [peer for peer in results if peer]
