"""Test cases for the daemon client."""

import pytest

from hfmc.client.http_request import ping
from hfmc.common.peer import Peer


@pytest.mark.asyncio()
async def test_peers_probe() -> None:
    """Test probe a live peer."""
    peer = Peer("127.0.0.2", 8080)
    await ping(peer)
