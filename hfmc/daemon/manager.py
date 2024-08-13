"""Manager of daemon service."""

from __future__ import annotations

import asyncio
import logging
import platform
import shutil
import signal
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from hfmc.client import http_request

if TYPE_CHECKING:
    from argparse import Namespace

logger = logging.getLogger(__name__)

HFMC_EXEC_NAME_GLOBAL = "hfmc"
HFMC_EXEC_NAME_LOCAL = "./main.py"
DELAY_SEC = 2


def _find_executable() -> str | None:
    executable = shutil.which(HFMC_EXEC_NAME_GLOBAL)
    if executable:
        return executable

    main_py = Path(HFMC_EXEC_NAME_LOCAL)
    if main_py.exists() and main_py.is_file():
        return "python " + HFMC_EXEC_NAME_LOCAL

    return None


async def daemon_is_running() -> bool:
    """Check if the HFMC Daemon is running."""
    return await http_request.is_daemon_running()


async def daemon_start(args: Namespace) -> bool:
    """Start the HFMC Daemon in a detached background process."""
    if await daemon_is_running():
        return True

    executable = _find_executable()
    if not executable:
        logger.error("Cannot find HFMC executable.")
        return False

    verbose = "--verbose" if args.verbose else ""
    command = f"{executable} {verbose} daemon start --detach"
    flags = (
        subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        if (platform.system() == "Windows")
        else 0
    )

    if platform.system() == "Linux":
        # deal with zombie processes on linux
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    await asyncio.create_subprocess_shell(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )

    await asyncio.sleep(DELAY_SEC)
    return await daemon_is_running()


async def daemon_stop() -> bool:
    """Stop the HFMC Daemon."""
    if not await daemon_is_running():
        return True

    await http_request.stop_daemon()

    await asyncio.sleep(DELAY_SEC)
    return not await daemon_is_running()
