#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os.path
import sys
import os
import configparser

from .daemon_manager import is_service_running
from ..common.settings import save_home_path, get_home_path, reset_home_path


async def conf_cache_set(home_path):
    if not os.path.exists(home_path):
        raise FileNotFoundError(f"Dir not found, please create it! path: {home_path}")

    if not os.path.isdir(home_path):
        raise NotADirectoryError(f"Path not a dir, please specify a directory! path: {home_path}")

    if await is_service_running():
        raise LookupError("Service is running, please stop it first!")

    save_home_path(home_path)
    logging.info(f"Set home dir success! path: {home_path}")


async def conf_cache_get():
    try:
        home_path = get_home_path()
    except Exception as e:
        raise ValueError(f"Get home path encounter unknown error, check the error! ERROR: {e}")

    logging.info(f"home path: {home_path}")


async def conf_cache_reset():
    if await is_service_running():
        raise LookupError("Service is running, please stop it first!")

    reset_home_path()
