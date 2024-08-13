"""Daemon server."""

import asyncio
import logging
import sys

from aiohttp import web

from hfmc.common.context import HfmcContext
from hfmc.common.api_settings import (
    API_DAEMON_PEERS_ALIVE,
    API_DAEMON_PEERS_CHANGE,
    API_DAEMON_RUNNING,
    API_DAEMON_STOP,
    API_FETCH_FILE_DAEMON,
    API_FETCH_REPO_FILE_LIST,
    API_PEERS_PROBE,
)
from hfmc.daemon.handlers.daemon_handler import (
    alive_peers,
    daemon_running,
    peers_changed,
    stop_daemon,
)
from hfmc.daemon.handlers.fetch_handler import (
    download_file,
    get_repo_file_list,
    search_file,
)
from hfmc.daemon.handlers.peer_handler import pong
from hfmc.daemon.prober import PeerProber

logger = logging.getLogger(__name__)


def _setup_router(app: web.Application) -> None:
    app.router.add_head(API_FETCH_FILE_DAEMON, search_file)
    app.router.add_get(API_FETCH_FILE_DAEMON, download_file)
    app.router.add_get(API_FETCH_REPO_FILE_LIST, get_repo_file_list)

    app.router.add_get(API_PEERS_PROBE, pong)

    app.router.add_get(API_DAEMON_PEERS_ALIVE, alive_peers)
    app.router.add_get(API_DAEMON_STOP, stop_daemon)
    app.router.add_get(API_DAEMON_RUNNING, daemon_running)
    app.router.add_get(API_DAEMON_PEERS_CHANGE, peers_changed)


async def _start() -> None:
    prober = PeerProber(HfmcContext.get_peers())
    HfmcContext.set_peer_prober(prober)
    task = asyncio.create_task(prober.start_probe())  # probe in background
    prober.set_probe_task(task)  # keep strong reference to task

    app = web.Application()
    _setup_router(app)

    runner = web.AppRunner(app)
    await runner.setup()

    all_int_ip = "0.0.0.0"  # noqa: S104
    port = HfmcContext.get_port()
    site = web.TCPSite(runner=runner, host=all_int_ip, port=port)
    await site.start()

    await asyncio.sleep(sys.maxsize)  # keep daemon running


PORT_OCCUPIED = 48


async def start() -> None:
    """Start the daemon server with errors surpressed."""
    try:
        await _start()
    except OSError as e:
        if e.errno == PORT_OCCUPIED:
            port = HfmcContext.get_port()
            logger.info(
                "Target port is already in use. ",
                extra={"port": port},
            )
    except ValueError:
        logger.exception("Daemon start error.")
