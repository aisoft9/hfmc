import os
from .peer import Peer
from .settings import HFFS_HOME, HFFS_PEER_CONF
import logging

def create_file():
    os.makedirs(HFFS_HOME, exist_ok=True)
    if not os.path.exists(HFFS_PEER_CONF):
        with open(HFFS_PEER_CONF, "w", encoding="utf-8"):
            logging.info(f"Created {HFFS_PEER_CONF}")


class PeerStore:
    def __init__(self):
        self._peers = set()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        if traceback:
            logging.error(f"PeerStore error, type=<{type}>, value=<{value}>")
        self.close()

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
