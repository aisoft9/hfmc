"""Handle requets related to peers."""

from aiohttp import web


async def pong(_: web.Request) -> web.Response:
    """Handle pings from peers."""
    return web.Response()
