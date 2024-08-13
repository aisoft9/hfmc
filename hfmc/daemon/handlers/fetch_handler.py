"""Handler model and file related requests."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Tuple

import aiofiles
from aiohttp import web

from hfmc.common import hf_wrapper, repo_files
from hfmc.common.etag import load_etag

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def _get_file_info(request: web.Request) -> tuple[str, str, str]:
    user = request.match_info["user"]
    model = request.match_info["model"]
    revision = request.match_info["revision"]
    file_name = request.match_info["file_name"]
    repo_id = f"{user}/{model}"
    return repo_id, file_name, revision


async def download_model(_: web.Request) -> web.Response:
    """Download model."""
    raise NotImplementedError


byte_range_re = re.compile(r"bytes=(\d+)-(\d+)?$")


def _get_byte_range(
    request: web.Request,
) -> tuple[int | None, int | None] | None:
    byte_range = request.headers.get("Range")

    if not byte_range or byte_range.strip() == "":
        return None, None

    m = byte_range_re.match(byte_range)
    err_msg = "Invalid byte range: Range=%s"

    if not m:
        logger.error(err_msg, byte_range)
        raise ValueError

    first, last = [int(x) if x else None for x in m.groups()]

    if first is not None and last is not None and last < first:
        logger.error(err_msg, byte_range)
        raise ValueError

    return first, last


async def _file_sender(
    writer: web.StreamResponse,
    file_path: Path,
    file_start: int | None,
    file_end: int | None,
) -> None:
    async with aiofiles.open(file_path, "rb") as f:
        if file_start is not None:
            await f.seek(file_start)

        buf_size = 2**18  # 256 KB buffer size

        while True:
            to_read = min(
                buf_size,
                file_end + 1 - await f.tell() if file_end else buf_size,
            )

            buf = await f.read(to_read)

            if not buf:
                break

            await writer.write(buf)

        await writer.write_eof()


async def download_file(
    request: web.Request,
) -> web.StreamResponse:
    """Download file."""
    br = _get_byte_range(request)
    if br is None:
        return web.Response(status=400)

    file_start, file_end = br
    repo_id, file_name, revision = _get_file_info(request)

    file_info = hf_wrapper.get_file_info(repo_id, revision, file_name)
    if not file_info:
        return web.Response(status=404)

    file_path = file_info.file_path
    if not file_path.exists():
        return web.Response(status=404)

    headers = {"Content-disposition": f"attachment; filename={file_name}"}
    response = web.StreamResponse(headers=headers)
    await response.prepare(request)
    await _file_sender(response, file_path, file_start, file_end)
    return response


async def search_model(_: web.Request) -> web.Response:
    """Search model."""
    raise NotImplementedError


async def search_file(
    request: web.Request,
) -> web.Response:
    """Search file."""
    repo_id, file_name, revision = _get_file_info(request)

    rev_info = hf_wrapper.get_revision_info(repo_id, revision)
    if not rev_info:
        return web.Response(status=404)

    file_info = hf_wrapper.get_file_info(repo_id, revision, file_name)
    if not file_info:
        return web.Response(status=404)

    etag = load_etag(repo_id, file_name, revision)
    return web.Response(
        headers={
            "ETag": etag or "",
            hf_wrapper.COMMIT_HASH_HEADER: rev_info.commit_hash,
            "Content-Length": str(file_info.size_on_disk),
            "Location": str(request.url),
        },
    )


def _get_repo_info(request: web.Request) -> Tuple[str, str]:
    user = request.match_info["user"]
    model = request.match_info["model"]
    revision = request.match_info["revision"]
    repo_id = f"{user}/{model}"
    return repo_id, revision


async def get_repo_file_list(request: web.Request) -> web.Response:
    """Get repo file list."""
    repo_id, revision = _get_repo_info(request)
    files = repo_files.load_file_list(repo_id, revision)
    if not files:
        return web.Response(status=404)
    return web.json_response(files)
