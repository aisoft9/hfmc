#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psutil
import logging
import time
import shutil
import platform
import signal
import subprocess
import asyncio

from ..common.settings import HFFS_EXEC_NAME
from .http_client import get_service_status, post_stop_service


async def is_service_running():
    try:
        _ = await get_service_status()
        return True
    except (ConnectionError, LookupError):
        return False
    except Exception as e:
        logging.info(f"If error not caused by service not start, may need check it! ERROR: {e}")
        return False


async def stop_service():
    try:
        await post_stop_service()
        logging.info("Service stopped success!")
    except (ConnectionError, LookupError):
        logging.info("Can not connect to service, may already stopped!")
    except Exception as e:
        raise SystemError(f"Failed to stop service! ERROR: {e}")


async def daemon_start(args):
    if await is_service_running():
        raise LookupError("Service already start!")

    exec_path = shutil.which(HFFS_EXEC_NAME)

    if not exec_path:
        raise FileNotFoundError(HFFS_EXEC_NAME)

    creation_flags = 0

    if platform.system() in ["Linux"]:
        # deal zombie process
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    elif platform.system() in ["Windows"]:
        creation_flags = subprocess.CREATE_NO_WINDOW

    cmdline_daemon_false = "--daemon=false"

    _ = subprocess.Popen([exec_path, "daemon", "start", "--port={}".format(args.port), cmdline_daemon_false],
                         stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         creationflags=creation_flags)

    wait_start_time = 3
    await asyncio.sleep(wait_start_time)

    if await is_service_running():
        logging.info("Service start success")
    else:
        raise LookupError("Service start but not running, check service or retry!")


async def daemon_stop():
    if not await is_service_running():
        logging.info("Service not running, stop nothing!")
        return

    await stop_service()

    wait_stop_time = 3
    await asyncio.sleep(wait_stop_time)

    if await is_service_running():
        raise LookupError("Stopped service but still running, check service or retry!")


async def daemon_status():
    if await is_service_running():
        logging.info("Service running.")
    else:
        logging.info("Service stopped.")
