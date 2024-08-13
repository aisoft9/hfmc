"""Daemon related commands."""

import logging
from argparse import Namespace

from hfmc.daemon import manager as daemon_manager
from hfmc.daemon import server

logger = logging.getLogger(__name__)


async def _daemon_start(args: Namespace) -> None:
    if await daemon_manager.daemon_start(args):
        logger.info("Daemon started.")
    else:
        logger.error("Daemon failed to start.")


async def _daemon_start_detached() -> None:
    await server.start()


async def _daemon_stop() -> None:
    if await daemon_manager.daemon_stop():
        logger.info("Daemon stopped.")
    else:
        logger.error("Daemon failed to stop.")


async def _daemon_status() -> None:
    if await daemon_manager.daemon_is_running():
        logger.info("Daemon is running.")
    else:
        logger.info("Daemon is NOT running.")


async def exec_cmd(args: Namespace) -> None:
    """Execute command."""
    if args.daemon_command == "start" and args.detach:
        await _daemon_start_detached()
    elif args.daemon_command == "start":
        await _daemon_start(args)
    elif args.daemon_command == "stop":
        await _daemon_stop()
    elif args.daemon_command == "status":
        await _daemon_status()
    else:
        raise NotImplementedError
