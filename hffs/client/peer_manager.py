from typing import List
from ..common.peer import Peer
import logging

class PeerManager:
    DEFAULT_PORT = 8000

    def __init__(self, peer_store):
        self._peer_store = peer_store

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
        peers = self.get_peers()
        if len(peers) == 0:
            print("<empty>")
        for peer in self.get_peers():
            print(f"{peer.ip}:{peer.port}")
