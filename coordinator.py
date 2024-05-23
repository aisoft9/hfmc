import aiohttp
import asyncio
from peer_manager import PeerManager


class PeerFinder:
    def __init__(self, peer_manager: PeerManager):
        self.__peer_manager = peer_manager

    async def _peer_has_file(self, peer, repo_id, branch, revision):
        # Construct the URL to check
        url = f"http://{peer['ip']}:{peer['port']}/repos/{repo_id}/branches/{branch}/revisions/{revision}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200

    def find_peers(self, repo_id, branch=None, revision=None):
        peers = self.__peer_manager.get_peers()
        peers = [peer for peer in peers if self._peer_has_file(
            peer, repo_id, branch, revision)]
