import os
from common.peer import Peer


PEER_CONF_DIR = os.path.join(os.path.expanduser("~"), ".cache/hffs")
PEER_CONF_FILE = "hffs_peers.conf"
PEER_CONF_PATH = os.path.join(PEER_CONF_DIR, PEER_CONF_FILE)


def create_file():
    os.makedirs(PEER_CONF_DIR, exist_ok=True)
    if not os.path.exists(PEER_CONF_PATH):
        with open(PEER_CONF_PATH, "w", encoding="utf-8"):
            pass


class PeerStore:

    def __init__(self):
        self._peers = set()

    def _load_peers(self):
        with open(PEER_CONF_PATH, "r+", encoding="utf-8") as f:
            for line in f:
                ip, port = line.strip().split(":")
                peer = Peer(ip, port)
                self._peers.add(peer)

    def open(self):
        create_file()
        self._load_peers()

    def close(self):
        with open(PEER_CONF_PATH, "w", encoding="utf-8") as f:
            for peer in self._peers:
                f.write(f"{peer.ip}:{peer.port}\n")

    def add_peer(self, peer):
        self._peers.add(peer)

    def remove_peer(self, peer):
        self._peers.discard(peer)

    def get_peers(self):
        return self._peers
