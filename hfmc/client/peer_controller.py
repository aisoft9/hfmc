"""Manage peers."""

from __future__ import annotations

from typing import List

from hfmc.client import http_request as request
from hfmc.config import config_manager
from hfmc.config.hfmc_config import HfmcConfigOption, Peer


def _uniq_peers(peers: List[Peer]) -> List[Peer]:
    """Remove duplicate peers."""
    return list(set(peers))


async def add(ip: str, port: int) -> None:
    """Add a peer."""
    peers = config_manager.get_config(HfmcConfigOption.PEERS, List[Peer])
    peers.append(Peer(ip=ip, port=port))
    config_manager.set_config(
        HfmcConfigOption.PEERS,
        _uniq_peers(peers),
        List[Peer],
    )
    await request.notify_peers_change()


async def rm(ip: str, port: int) -> None:
    """Remove a peer."""
    peers = config_manager.get_config(HfmcConfigOption.PEERS, List[Peer])
    peers = [peer for peer in peers if peer.ip != ip or peer.port != port]
    config_manager.set_config(
        HfmcConfigOption.PEERS,
        _uniq_peers(peers),
        List[Peer],
    )
    await request.notify_peers_change()


async def get() -> List[tuple[Peer, bool]]:
    """Get all peers with liveness info."""
    peers = config_manager.get_config(HfmcConfigOption.PEERS, List[Peer])

    # get_alive_peers uses Peer in HfmcContext intead of Peer in HfmcConfig
    alives = {Peer(ip=p.ip, port=p.port) for p in await request.get_alive_peers()}

    return [(peer, peer in alives) for peer in peers]
