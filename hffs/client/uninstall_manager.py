#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import shutil

from ..common.settings import HFFS_HOME
from .daemon_manager import daemon_stop


async def uninstall_hffs():
    logging.warning("WARNING: will delete all hffs data on disk, can't recovery it!")

    logging.info("\n{}\n".format(HFFS_HOME))

    first_confirm = input("UP directory will be delete! Enter y/Y to confirm:")

    if first_confirm not in ["y", "Y"]:
        logging.info("Canceled uninstall!")
        return

    second_confirm = input("\nPlease enter y/Y confirm it again, then start uninstall: ")

    if second_confirm not in ["y", "Y"]:
        logging.info("Canceled uninstall!")
        return

    await daemon_stop()
    shutil.rmtree(HFFS_HOME, ignore_errors=True)

    print("Uninstall success!")

