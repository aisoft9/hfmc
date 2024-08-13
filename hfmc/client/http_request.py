"""Daemon client for connecting with (self or other) Daemons."""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, List

import aiohttp
from huggingface_hub import (  # type: ignore[import-untyped]
    get_hf_file_metadata,
    hf_hub_url,
)

from hfmc.common.context import HfmcContext
from hfmc.common.api_settings import (
    API_DAEMON_PEERS_ALIVE,
    API_DAEMON_PEERS_CHANGE,
    API_DAEMON_RUNNING,
    API_DAEMON_STOP,
    API_FETCH_FILE_CLIENT,
    API_FETCH_REPO_FILE_LIST,
    API_PEERS_PROBE,
    TIMEOUT_DAEMON,
    TIMEOUT_PEERS,
    ApiType,
)
from hfmc.common.peer import Peer
from hfmc.common.repo_files import RepoFileList

logger = logging.getLogger(__name__)


HTTP_STATUS_OK = 200


def _http_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession()


def _api_url(peer: Peer, api: ApiType) -> str:
    return f"http://{peer.ip}:{peer.port}{api}"


@asynccontextmanager
async def _quiet_request(
    sess: aiohttp.ClientSession,
    req: AsyncContextManager,
) -> AsyncIterator[aiohttp.ClientResponse | None]:
    try:
        async with sess, req as resp:
            yield resp
    except (
        aiohttp.ClientError,
        asyncio.exceptions.TimeoutError,
        TimeoutError,
        ConnectionError,
        RuntimeError,
    ) as e:
        logger.debug("HTTP Error: %s", e)
        yield None


@asynccontextmanager
async def _quiet_get(
    url: str,
    timeout: aiohttp.ClientTimeout,
) -> AsyncIterator[aiohttp.ClientResponse | None]:
    sess = _http_session()
    req = sess.get(url, timeout=timeout)
    async with _quiet_request(sess, req) as resp:
        try:
            yield resp
        except (OSError, ValueError, RuntimeError) as e:
            logger.debug("Failed to get response: %s", e)
            yield None


@asynccontextmanager
async def _quiet_head(
    url: str,
    timeout: aiohttp.ClientTimeout,
) -> AsyncIterator[aiohttp.ClientResponse | None]:
    sess = _http_session()
    req = sess.head(url, timeout=timeout)
    async with _quiet_request(sess, req) as resp:
        try:
            yield resp
        except (OSError, ValueError, RuntimeError) as e:
            logger.debug("Failed to get response: %s", e)
            yield None


async def ping(target: Peer) -> Peer:
    """Ping a peer to check if it is alive."""
    url = _api_url(target, API_PEERS_PROBE)
    async with _quiet_get(url, TIMEOUT_PEERS) as resp:
        target.alive = resp is not None and resp.status == HTTP_STATUS_OK
        target.epoch = int(time.time())
        return target


async def stop_daemon() -> bool:
    """Stop a daemon service."""
    url = _api_url(HfmcContext.get_daemon(), API_DAEMON_STOP)
    async with _quiet_get(url, TIMEOUT_DAEMON) as resp:
        return resp is not None and resp.status == HTTP_STATUS_OK


async def is_daemon_running() -> bool:
    """Check if daemon is running."""
    url = _api_url(HfmcContext.get_daemon(), API_DAEMON_RUNNING)
    async with _quiet_get(url, TIMEOUT_DAEMON) as resp:
        return resp is not None and resp.status == HTTP_STATUS_OK


async def get_alive_peers() -> List[Peer]:
    """Get a list of alive peers."""
    url = _api_url(HfmcContext.get_daemon(), API_DAEMON_PEERS_ALIVE)
    async with _quiet_get(url, TIMEOUT_DAEMON) as resp:
        if not resp:
            return []
        return [Peer(**peer) for peer in await resp.json()]


async def notify_peers_change() -> bool:
    """Notify peers about a change in peer list."""
    url = _api_url(HfmcContext.get_daemon(), API_DAEMON_PEERS_CHANGE)
    async with _quiet_get(url, TIMEOUT_DAEMON) as resp:
        return resp is not None and resp.status == HTTP_STATUS_OK


async def check_file_exist(
    peer: Peer,
    repo_id: str,
    file_name: str,
    revision: str,
) -> tuple[Peer, bool]:
    """Check if the peer has target file."""
    url = _api_url(
        peer,
        API_FETCH_FILE_CLIENT.format(
            repo=repo_id,
            revision=revision,
            file_name=file_name,
        ),
    )
    async with _quiet_head(url, TIMEOUT_PEERS) as resp:
        return (peer, resp is not None and resp.status == HTTP_STATUS_OK)


async def get_file_etag(
    endpoint: str,
    repo_id: str,
    file_name: str,
    revision: str,
) -> str | None:
    """Get the ETag of a file."""
    url = hf_hub_url(
        repo_id=repo_id,
        filename=file_name,
        revision=revision,
        endpoint=endpoint,
    )

    try:
        metadata = get_hf_file_metadata(url)
        if metadata:
            return metadata.etag
    except (OSError, ValueError):
        logger.debug(
            "Failed to get ETag: %s, %s, %s, %s",
            endpoint,
            repo_id,
            file_name,
            revision,
        )
    return None


async def check_repo_exist() -> tuple[Peer, bool]:
    """Check if the peer has target model."""
    raise NotImplementedError


async def get_repo_file_list(
    peer: Peer,
    repo_id: str,
    revision: str,
) -> RepoFileList | None:
    """Load the target model from a peer."""
    user, model = repo_id.strip().split("/")
    url = _api_url(
        peer,
        API_FETCH_REPO_FILE_LIST.format(
            user=user,
            model=model,
            revision=revision,
        ),
    )
    async with _quiet_get(url, TIMEOUT_PEERS) as resp:
        if not resp or resp.status != HTTP_STATUS_OK:
            return None
        return await resp.json()
