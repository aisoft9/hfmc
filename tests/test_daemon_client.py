"""Test cases for the daemon client."""

import pytest

from hffs.client.http_request import ping
from hffs.common.peer import Peer


@pytest.mark.asyncio()
async def test_peers_probe() -> None:
    """Test probe a live peer."""
    peer = Peer("127.0.0.2", 8080)
    await ping(peer)
