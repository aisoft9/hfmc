"""Configuration related commands."""

import logging
from argparse import Namespace

from hfmc.config import config_manager
from hfmc.config.hfmc_config import HfmcConfigOption

logger = logging.getLogger(__name__)


def _configure_cache(args: Namespace) -> None:
    if args.conf_cache_command == "set":
        conf = config_manager.set_config(
            HfmcConfigOption.CACHE,
            args.path,
            str,
        )
        logger.info("Set HFMC cache path: %s", conf)
    elif args.conf_cache_command == "get":
        conf = config_manager.get_config(HfmcConfigOption.CACHE, str)
        logger.info("HFMC cache path: %s", conf)
    elif args.conf_cache_command == "reset":
        conf = config_manager.reset_config(HfmcConfigOption.CACHE, str)
        logger.info("Reset HFMC cache path: %s", conf)


def _configure_port(args: Namespace) -> None:
    if args.conf_port_command == "set":
        conf = config_manager.set_config(
            HfmcConfigOption.PORT,
            args.port,
            str,
        )
        logger.info("Set HFMC port: %s", conf)
    elif args.conf_port_command == "get":
        conf = config_manager.get_config(HfmcConfigOption.PORT, str)
        logger.info("HFMC port: %s", conf)
    elif args.conf_port_command == "reset":
        conf = config_manager.reset_config(HfmcConfigOption.PORT, str)
        logger.info("Reset HFMC port: %s", conf)


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
