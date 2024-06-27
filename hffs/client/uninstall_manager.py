#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import shutil

from ..common.settings import HFFS_ROOT, HFFS_HOME
from .daemon_manager import daemon_stop


async def uninstall_hffs():
    logging.warning("WARNING: will delete all hffs data on disk, can't recovery it!")

    rm_dir_list = [HFFS_ROOT, HFFS_HOME]
    logging.info("")

    for d in rm_dir_list:
        logging.info(d)

    logging.info("")
    first_confirm = input("UP directory will be delete! Enter y/Y to confirm:")

    if first_confirm not in ["y", "Y"]:
        logging.info("Canceled uninstall!")
        return

    second_confirm = input("\nPlease enter y/Y confirm it again, then start uninstall: ")

    if second_confirm not in ["y", "Y"]:
        logging.info("Canceled uninstall!")
        return

    await daemon_stop()

    for d in rm_dir_list:
        shutil.rmtree(d, ignore_errors=True)

    print("Uninstall success!")
