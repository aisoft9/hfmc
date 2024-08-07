"""Configuration related commands."""

import logging
from argparse import Namespace

from hffs.config import config_manager
from hffs.config.hffs_config import HffsConfigOption

logger = logging.getLogger(__name__)


def _configure_cache(args: Namespace) -> None:
    if args.conf_cache_command == "set":
        conf = config_manager.set_config(
            HffsConfigOption.CACHE,
            args.path,
            str,
        )
        logger.info("Set HFFS cache path: %s", conf)
    elif args.conf_cache_command == "get":
        conf = config_manager.get_config(HffsConfigOption.CACHE, str)
        logger.info("HFFS cache path: %s", conf)
    elif args.conf_cache_command == "reset":
        conf = config_manager.reset_config(HffsConfigOption.CACHE, str)
        logger.info("Reset HFFS cache path: %s", conf)


def _configure_port(args: Namespace) -> None:
    if args.conf_port_command == "set":
        conf = config_manager.set_config(
            HffsConfigOption.PORT,
            args.port,
            str,
        )
        logger.info("Set HFFS port: %s", conf)
    elif args.conf_port_command == "get":
        conf = config_manager.get_config(HffsConfigOption.PORT, str)
        logger.info("HFFS port: %s", conf)
    elif args.conf_port_command == "reset":
        conf = config_manager.reset_config(HffsConfigOption.PORT, str)
        logger.info("Reset HFFS port: %s", conf)


def _show_config() -> None:
    content = config_manager.get_config_yaml()
    logger.info(content)


async def exec_cmd(args: Namespace) -> None:
    """Execute command."""
    if args.conf_command == "cache":
        _configure_cache(args)
    elif args.conf_command == "port":
        _configure_port(args)
    elif args.conf_command == "show":
        _show_config()
    else:
        raise NotImplementedError
