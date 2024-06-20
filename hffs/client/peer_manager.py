import logging
import urllib3

from typing import List
from ..common.peer import Peer
from .http_client import notify_peer_change, alive_peers


def check_valid_ip_port(ip, port):
    converted_url = "{}:{}".format(ip, port)

    try:
        parsed_url = urllib3.util.parse_url(converted_url)

        if not parsed_url.host or not parsed_url.port:
            raise ValueError("Should be not None!")
    except Exception:
        raise ValueError("Invalid IP or port format! IP: {}, port:{}".format(ip, port))


class PeerManager:
    DEFAULT_PORT = 9009

    def __init__(self, peer_store):
        self._peer_store = peer_store

    def add_peer(self, ip, port=None):
        peer_port = port if port else self.DEFAULT_PORT
        check_valid_ip_port(ip, port)
        peer = Peer(ip, peer_port)
        self._peer_store.add_peer(peer)
        logging.info("Add success!")

    def remove_peer(self, ip, port=None):
        peer_port = port if port else self.DEFAULT_PORT
        check_valid_ip_port(ip, port)
        peer = Peer(ip, peer_port)
        self._peer_store.remove_peer(peer)
        logging.info("Remove success!")

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
