"""Handle requests to daemon."""

from dataclasses import asdict

from aiohttp import web
from aiohttp.web_runner import GracefulExit

from hffs.common.context import HffsContext
from hffs.config import config_manager


async def alive_peers(_: web.Request) -> web.Response:
    """Find alive peers."""
    alives = HffsContext.get_peer_prober().get_alives()
    return web.json_response([asdict(peer) for peer in alives])


async def peers_changed(_: web.Request) -> web.Response:
    """Update peers."""
    config = config_manager.load_config()
    new_peers = HffsContext.update_peers(config, HffsContext.get_peers())
    HffsContext.get_peer_prober().update_peers(new_peers)
    return web.Response()


async def stop_daemon(request: web.Request) -> None:
    """Stop the daemon."""
    HffsContext.get_peer_prober().stop_probe()

    resp = web.Response()
    await resp.prepare(request)
    await resp.write_eof()

    raise GracefulExit


async def daemon_running(_: web.Request) -> web.Response:
    """Check if daemon is running."""
    return web.Response()
