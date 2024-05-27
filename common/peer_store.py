import os
from common.peer import Peer
from common.settings import HFFS_HOME, HFFS_PEER_CONF


def create_file():
    os.makedirs(HFFS_HOME, exist_ok=True)
    if not os.path.exists(HFFS_PEER_CONF):
        with open(HFFS_PEER_CONF, "w", encoding="utf-8"):
            print(f"Created {HFFS_PEER_CONF}")


class PeerStore:

    def __init__(self):
        self._peers = set()

    def _load_peers(self):
        with open(HFFS_PEER_CONF, "r+", encoding="utf-8") as f:
            for line in f:
                ip, port = line.strip().split(":")
                peer = Peer(ip, port)
                self._peers.add(peer)

    def open(self):
        create_file()
        self._load_peers()

    def close(self):
        with open(HFFS_PEER_CONF, "w", encoding="utf-8") as f:
            for peer in self._peers:
                f.write(f"{peer.ip}:{peer.port}\n")

    def add_peer(self, peer):
        self._peers.add(peer)

    def remove_peer(self, peer):
        self._peers.discard(peer)

    def get_peers(self):
        return self._peers
