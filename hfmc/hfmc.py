"""Entrypoint of HFMC."""

import asyncio
import logging
from argparse import Namespace

from hfmc.client import model_cmd, peer_cmd, uninstall_cmd
from hfmc.common.context import HfmcContext
from hfmc.config import conf_cmd, config_manager
from hfmc.daemon import daemon_cmd
from hfmc.utils import auth_cmd, logging as logging_utils
from hfmc.utils.args import arg_parser

logger = logging.getLogger(__name__)


async def _exec_cmd(args: Namespace) -> None:
    if args.command == "daemon":
        exec_cmd = daemon_cmd.exec_cmd
    elif args.command == "peer":
        exec_cmd = peer_cmd.exec_cmd
    elif args.command == "model":
        exec_cmd = model_cmd.exec_cmd
    elif args.command == "conf":
        exec_cmd = conf_cmd.exec_cmd
    elif args.command == "auth":
        exec_cmd = auth_cmd.exec_cmd
    elif args.command == "uninstall":
        exec_cmd = uninstall_cmd.exec_cmd
    else:
        raise NotImplementedError

    await exec_cmd(args)


async def _async_main() -> None:
    config = config_manager.load_config()
    HfmcContext.init_with_config(config)

    args = arg_parser()
    logging_utils.setup_logging(args)

    await _exec_cmd(args)


def main() -> None:
    """Entrypoint of HFMC."""
    try:
        asyncio.run(_async_main())
    except (
        KeyboardInterrupt,
        asyncio.exceptions.CancelledError,
    ):
        # ignore interrupt and cancel errors as they are handled by daemon
        logger.info("Shutting down HFMC.")
