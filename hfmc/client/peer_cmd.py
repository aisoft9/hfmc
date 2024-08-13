"""Peer related commands."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

from hfmc.client import peer_controller

if TYPE_CHECKING:
    from argparse import Namespace

    from hfmc.config.hfmc_config import Peer

logger = logging.getLogger(__name__)


def _print_peer_list(peers: List[tuple[Peer, bool]]) -> None:
    """Print peer list."""
    for peer, alive in peers:
        peer_name = f"{peer.ip}:{peer.port}"
        peer_stat = "alive" if alive else ""
        peer_str = f"{peer_name}\t{peer_stat}"
        logger.info(peer_str)


async def exec_cmd(args: Namespace) -> None:
    """Execute command."""
    if args.peer_command == "add":
        await peer_controller.add(args.ip, args.port)
    elif args.peer_command == "rm":
        await peer_controller.rm(args.ip, args.port)
    elif args.peer_command == "ls":
        peers = await peer_controller.get()
        _print_peer_list(peers)
    else:
        raise NotImplementedError
