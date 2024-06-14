from typing import List
from ..common.peer import Peer
from .http_client import notify_peer_change, alive_peers


class PeerManager:
    DEFAULT_PORT = 9009

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

    async def list_peers(self):
        alives = await alive_peers()
        alives = set(alives)

        peers = sorted(self.get_peers())

        if len(peers) == 0:
            print("No peer is configured.")
            return

        print("List of peers:")
        for peer in peers:
            alive = "alive" if peer in alives else ""
            print(f"{peer.ip}\t{peer.port}\t{alive}")

    async def notify_peer_change(self):
        await notify_peer_change()
