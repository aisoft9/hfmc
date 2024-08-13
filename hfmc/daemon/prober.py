"""Probing the liveness of other peers."""

from __future__ import annotations

import asyncio
import heapq
import logging
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from hfmc.common.peer import Peer

logger = logging.getLogger(__name__)


class PeerProber:
    """Prober for the liveness of other peers."""

    _peers: List[Peer]
    _actives: set
    _updates: set | None
    _probe_heap: List[tuple[int, Peer]]
    _probing: bool
    _probe_task: asyncio.Task[None] | None

    INTERVAL_SEC = 3

    def __init__(self, peers: List[Peer]) -> None:
        """Init PeerProber."""
        self._peers = peers
        self._actives = set()
        self._updates = None
        self._probe_heap = []
        self._probing = False
        self._probe_task = None

    def get_alives(self) -> List[Peer]:
        """Get live peer list."""
        return list(self._actives)

    def update_peers(self, peers: List[Peer]) -> None:
        """Accept a new list of peers to probe."""
        self._updates = set(peers)

    def _reset_peer_heap(self) -> None:
        self._probe_heap = []
        for peer in self._peers:
            heapq.heappush(self._probe_heap, (peer.epoch, peer))

    def _do_update_peers(self) -> None:
        if self._updates is not None:
            peers_removed = set(self._peers) - self._updates
            self._actives = self._actives - peers_removed

            self._peers = list(self._updates)
            self._updates = None

            self._reset_peer_heap()

    async def start_probe(self) -> None:
        """Start probing peers for liveness.

        This function uses asyncio to probe peers for liveness.
        It will wake up every {INTERVAL_SEC} seconds, pop a peer
        from the heap, and then send a ping request to the peer.
        The peer is taken out of the heap until we get a response from
        the peer or the ping request times out.
        After that, the peer is put back into the heap.
        """
        # pylint: disable=import-outside-toplevel
        from hfmc.client.http_request import ping  # resolve cyclic import

        if self._probing:
            return

        self._probing = True
        self._reset_peer_heap()

        if not self._probe_heap:
            logger.debug("No peers configured to probe")

        def probe_cb(task: asyncio.Task[Peer]) -> None:
            try:
                peer = task.result()

                if peer in self._peers:
                    heapq.heappush(self._probe_heap, (peer.epoch, peer))

                if peer.alive and peer in self._peers:
                    self._actives.add(peer)
                else:
                    self._actives.discard(peer)
            except asyncio.exceptions.CancelledError:
                logger.debug("probing is canceled")

        while self._probing:
            await asyncio.sleep(self.INTERVAL_SEC)

            self._do_update_peers()

            if self._probe_heap:
                _, peer = heapq.heappop(self._probe_heap)
                probe = asyncio.create_task(ping(peer))
                probe.add_done_callback(probe_cb)

    def set_probe_task(self, task: asyncio.Task[None]) -> None:
        """Save the coroutine task of probing to avoid gc."""
        self._probe_task = task

    def stop_probe(self) -> None:
        """Stop probing."""
        # TODO: cancel running probe tasks  # noqa: FIX002, TD002, TD003
        self._probing = False
        self._probe_heap = []
        self._actives = set()
        self._probe_task = None
