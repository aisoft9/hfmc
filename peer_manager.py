import heapq
import os
import asyncio

from http_client import ping
from typing import List
from peer import Peer


class PeerStore:
    PEER_CONF_PATH = "./hffs-data/hffs_peers.conf"

    def __init__(self):
        self._peers = set()

        if not os.path.exists(self.PEER_CONF_PATH):
            with open(self.PEER_CONF_PATH, "w", encoding="utf-8") as f:
                pass

        with open(self.PEER_CONF_PATH, "r+", encoding="utf-8") as f:
            for line in f:
                ip, port = line.strip().split(":")
                peer = Peer(ip, port)
                self._peers.add(peer)

    def close(self):
        with open(self.PEER_CONF_PATH, "w", encoding="utf-8") as f:
            for peer in self._peers:
                f.write(f"{peer.ip}:{peer.port}\n")

    def add_peer(self, peer):
        self._peers.add(peer)

    def remove_peer(self, peer):
        self._peers.discard(peer)

    def get_peers(self):
        return self._peers


class PeerManager:
    DEFAULT_PORT = 8000

    def __init__(self, peer_store):
        self._peer_store = peer_store
        self._actives = set()
        self._probe_heap = [(peer.get_epoch(), peer)
                            for peer in peer_store.get_peers()]
        heapq.heapify(self._probe_heap)

    def add_peer(self, ip, port=None):
        peer = Peer(ip, port if port else self.DEFAULT_PORT)
        self._peer_store.add_peer(peer)

    def remove_peer(self, ip, port=None):
        peer = Peer(ip, port if port else self.DEFAULT_PORT)
        self._peer_store.remove_peer(peer)

    def get_peers(self) -> List[Peer]:
        return self._peer_store.get_peers()

    def list_peers(self):
        print("List of peers:")
        for peer in self.get_peers():
            print(f"{peer.ip}:{peer.port}")

    def get_actives(self):
        return list(self._actives)

    async def start_probe(self):
        """Start probing peers for liveness.

        This function uses asyncio to probe peers for liveness. It will wake up every 1 seconds, and 
        pop a peer from the heap. It will then send a ping request to the peer. The peer is taken out
        of the haep until we get a response from the peer or the ping request times out. After that,
        the peer is put back into the heap.
        """

        # Initialize the heap with the peers, sorted by their epoch
        for peer in self.get_peers():
            heapq.heappush(self._probe_heap, (peer.get_epoch(), peer))

        def probe_cb(task):
            peer = task.result()
            if isinstance(peer, Peer):
                heapq.heappush(self._probe_heap, (peer.get_epoch(), peer))
                if peer.is_alive() and peer not in self._actives:
                    self._actives.add(peer)

        while True:
            await asyncio.sleep(3)

            if len(self._probe_heap) == 0:
                continue

            _, peer = heapq.heappop(self._probe_heap)
            probe = asyncio.create_task(ping(peer))
            probe.add_done_callback(probe_cb)
