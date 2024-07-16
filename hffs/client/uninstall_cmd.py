"""Uninstall HFFS by removing related directories."""

import logging
import shutil
from argparse import Namespace

from hffs.config import config_manager
from hffs.config.hffs_config import CONFIG_DIR, HffsConfigOption
from hffs.daemon import manager as daemon_manager

logger = logging.getLogger(__name__)


async def _uninstall() -> None:
    if await daemon_manager.daemon_is_running():
        logger.info("Stop daemon first by executing 'hffs daemon stop'.")
        return

    warning = (
        "WARNING: 'Uninstall' will delete all hffs data on disk, "
        "and it's not recoverable!."
    )
    logging.info(warning)

    confirm = input("Please enter 'Y/y' to confirm uninstall: ")

    if confirm not in ["Y", "y"]:
        logger.info("Cancel uninstall.")
        return

    cache_dir = config_manager.get_config(HffsConfigOption.CACHE, str)
    home_dir = str(CONFIG_DIR)
    to_rm = [cache_dir, home_dir]

    for d in to_rm:
        shutil.rmtree(d, ignore_errors=True)

    logger.info("HFFS is uninstalled.")


async def exec_cmd(args: Namespace) -> None:
    """Execute command."""
    if args.command == "uninstall":
        await _uninstall()
    else:
        raise NotImplementedError
