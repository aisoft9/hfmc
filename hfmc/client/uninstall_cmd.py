"""Uninstall HFMC by removing related directories."""

import logging
import shutil
from argparse import Namespace

from hfmc.config import config_manager
from hfmc.config.hfmc_config import CONFIG_DIR, HfmcConfigOption
from hfmc.daemon import manager as daemon_manager

logger = logging.getLogger(__name__)


async def _uninstall() -> None:
    if await daemon_manager.daemon_is_running():
        logger.info("Stop daemon first by executing 'hfmc daemon stop'.")
        return

    warning = (
        "WARNING: 'Uninstall' will delete all hfmc data on disk, "
        "and it's not recoverable!."
    )
    logging.info(warning)

    confirm = input("Please enter 'Y/y' to confirm uninstall: ")

    if confirm not in ["Y", "y"]:
        logger.info("Cancel uninstall.")
        return

    cache_dir = config_manager.get_config(HfmcConfigOption.CACHE, str)
    home_dir = str(CONFIG_DIR)
    to_rm = [cache_dir, home_dir]

    for d in to_rm:
        shutil.rmtree(d, ignore_errors=True)

    logger.info("HFMC is uninstalled.")


async def exec_cmd(args: Namespace) -> None:
    """Execute command."""
    if args.command == "uninstall":
        await _uninstall()
    else:
        raise NotImplementedError
