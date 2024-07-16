"""Manage peers."""

from __future__ import annotations

from typing import List

from hffs.client import http_request as request
from hffs.config import config_manager
from hffs.config.hffs_config import HffsConfigOption, Peer


def _uniq_peers(peers: List[Peer]) -> List[Peer]:
    """Remove duplicate peers."""
    return list(set(peers))


async def add(ip: str, port: int) -> None:
    """Add a peer."""
    peers = config_manager.get_config(HffsConfigOption.PEERS, List[Peer])
    peers.append(Peer(ip=ip, port=port))
    config_manager.set_config(
        HffsConfigOption.PEERS,
        _uniq_peers(peers),
        List[Peer],
    )
    await request.notify_peers_change()


async def rm(ip: str, port: int) -> None:
    """Remove a peer."""
    peers = config_manager.get_config(HffsConfigOption.PEERS, List[Peer])
    peers = [peer for peer in peers if peer.ip != ip or peer.port != port]
    config_manager.set_config(
        HffsConfigOption.PEERS,
        _uniq_peers(peers),
        List[Peer],
    )
    await request.notify_peers_change()


async def get() -> List[tuple[Peer, bool]]:
    """Get all peers with liveness info."""
    peers = config_manager.get_config(HffsConfigOption.PEERS, List[Peer])

    # get_alive_peers uses Peer in HffsContext intead of Peer in HffsConfig
    alives = {Peer(ip=p.ip, port=p.port) for p in await request.get_alive_peers()}

    return [(peer, peer in alives) for peer in peers]
