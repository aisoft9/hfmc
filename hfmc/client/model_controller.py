"""Manage models."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Coroutine, List, TypeVar

from huggingface_hub import hf_hub_download  # type: ignore[import-untyped]
from huggingface_hub.utils import GatedRepoError  # type: ignore[import-untyped]

from hfmc.client import http_request as request
from hfmc.common import hf_wrapper
from hfmc.common.context import HfmcContext
from hfmc.common.etag import save_etag
from hfmc.common.repo_files import RepoFileList, load_file_list, save_file_list

if TYPE_CHECKING:
    from pathlib import Path

    from hfmc.common.peer import Peer

logger = logging.getLogger(__name__)


T = TypeVar("T")


async def _safe_gather(
    tasks: List[Coroutine[Any, Any, T]],
) -> List[T]:
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, BaseException)]


async def file_search(
    repo_id: str,
    file_name: str,
    revision: str,
) -> List[Peer]:
    """Check which peers have target file."""
    alives = await request.get_alive_peers()
    tasks = [
        request.check_file_exist(alive, repo_id, file_name, revision)
        for alive in alives
    ]
    results = await _safe_gather(tasks)
    exists = {s[0] for s in results if s[1]}
    return [alive for alive in alives if alive in exists]


async def repo_search() -> List[Peer]:
    """Check which peers have target model."""
    raise NotImplementedError


async def _download_file(
    endpoint: str,
    repo_id: str,
    file_name: str,
    revision: str,
) -> bool:
    try:
        # hf_hub_download will send request to the endpoint
        # on /{user}/{model}/resolve/{revision}/{file_name:.*}
        # daemon server can handle the request and return the file
        _ = hf_hub_download(
            endpoint=endpoint,
            repo_id=repo_id,
            revision=revision,
            filename=file_name,
            cache_dir=HfmcContext.get_model_dir_str(),
        )

        etag = await request.get_file_etag(
            endpoint,
            repo_id,
            file_name,
            revision,
        )
        if not etag:
            return False

        save_etag(etag, repo_id, file_name, revision)
    except GatedRepoError:
        logger.info("Model is gated. Login with `hfmc auth login` first.")
        return False
    except (OSError, ValueError) as e:
        logger.info(f"Failed to download model. ERROR: {e}")
        logger.debug("Download file error", exc_info=e)
        return False
    return True


def _gen_endpoints(peers: List[Peer]) -> List[str]:
    peer_ends = [f"http://{peer.ip}:{peer.port}" for peer in peers]
    site_ends = ["https://hf-mirror.com", "https://huggingface.co"]
    return peer_ends + site_ends


async def file_add(
    repo_id: str,
    file_name: str,
    revision: str,
) -> bool:
    """Download and add model files to HFMC."""
    if hf_wrapper.get_file_info(repo_id, revision, file_name) is not None:
        # file is already downloaded
        return True

    peers = await file_search(repo_id, file_name, revision)
    endpoints = _gen_endpoints(peers)

    for endpoint in endpoints:
        logger.info("Try to add file %s from %s", file_name, endpoint)
        success = await _download_file(endpoint, repo_id, file_name, revision)

        if success:
            return True

    return False


async def _wait_first(
    tasks: List[Coroutine[Any, Any, T | None]],
) -> T | None:
    done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    if not done:
        return None
    for task in done:
        result = task.result()
        if result:
            return result
    return None


async def _file_list_from_peers(
    repo_id: str,
    revision: str,
) -> RepoFileList | None:
    alives = await request.get_alive_peers()
    if not alives:
        return None
    tasks = [request.get_repo_file_list(alive, repo_id, revision) for alive in alives]
    return await _wait_first(tasks)


async def _file_list_from_site(
    repo_id: str,
    revision: str,
) -> RepoFileList | None:
    endopints = _gen_endpoints([])
    for endpoint in endopints:
        files = hf_wrapper.get_repo_file_list(endpoint, repo_id, revision)
        if files:
            return files
    return None


async def _get_repo_file_list(
    repo_id: str,
    revision: str,
) -> RepoFileList | None:
    files = load_file_list(repo_id, revision)
    if not files:
        files = await _file_list_from_peers(repo_id, revision)
    if not files:
        files = await _file_list_from_site(repo_id, revision)
    if files:
        save_file_list(repo_id, revision, files)
    return files


async def repo_add(
    repo_id: str,
    revision: str,
) -> bool:
    """Download and add all files in a repo to HFMC."""
    normalized_rev = hf_wrapper.verify_revision(
        repo_id,
        revision,
        _gen_endpoints([]),
    )
    if not normalized_rev:
        logger.error("Failed to verify revision: %s", revision)
        return False

    files = await _get_repo_file_list(repo_id, normalized_rev)
    if not files:
        logger.error("Failed to get file list of %s", repo_id)
        return False

    for file_name in files:
        success = await file_add(repo_id, file_name, normalized_rev)
        if not success:
            logger.error("Failed to add file: %s", file_name)
            return False

    return True


@dataclass
class FileInfo:
    """Info of a model file."""

    file_name: Path = field()
    size_on_disk_str: str = field()
    file_path: Path = field()
    refs: set[str] = field()
    commit_8: str = field()


@dataclass
class RepoInfo:
    """Info of a repo."""

    repo_id: str = field()
    size_str: str = field()
    nb_files: int = field()
    repo_path: Path = field()


def file_list(repo_id: str) -> List[FileInfo]:
    """List files in target repo."""
    files: List[FileInfo] = []

    repo_info = hf_wrapper.get_repo_info(repo_id)
    if not repo_info:
        return files

    for rev in repo_info.revisions:
        for f in rev.files:
            fi = FileInfo(
                f.file_path.relative_to(rev.snapshot_path),
                f.size_on_disk_str,
                f.file_path,
                set(rev.refs),
                rev.commit_hash[:8],
            )
            files.extend([fi])

    return files


def repo_list() -> List[RepoInfo]:
    """List repos in the cache."""
    cache_info = hf_wrapper.get_cache_info()
    return [
        RepoInfo(
            repo.repo_id,
            f"{repo.size_on_disk_str:>12}",
            repo.nb_files,
            repo.repo_path,
        )
        for repo in cache_info.repos
    ]


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        _ = child.relative_to(parent)
    except ValueError:
        return False
    return True


def _rm_file(fp: Path, root_path: Path) -> None:
    if not fp.relative_to(root_path):
        logger.debug(
            "Cache structure error: path=%s, root=%s",
            str(fp),
            str(root_path),
        )
        raise ValueError

    # remove target file
    if fp.exists() and fp.is_file():
        fp.unlink()

    # remove parent directories if empty up to root_path
    parent_dir = fp.parent
    while _is_relative_to(parent_dir, root_path):
        if not any(parent_dir.iterdir()):
            parent_dir.rmdir()
            parent_dir = parent_dir.parent
        else:
            break


def _can_delete_blob(
    file_name: str,
    snapshot_path: Path,
    blob_path: Path,
) -> bool:
    """Delete blob only if there is NO symlink pointing to it."""
    if not snapshot_path.exists():
        # delete blob if snapshot path is not existing
        return True

    for snapshot_dir in snapshot_path.iterdir():
        snapshot_file = snapshot_dir / file_name
        if (
            snapshot_file.exists()
            and snapshot_file.is_symlink()
            and (snapshot_file.resolve() == blob_path)
        ):
            # there is still symlink pointing to the blob file
            # don't delete the blob
            return False

    return True


def file_rm(
    repo_id: str,
    file_name: str,
    revision: str,
) -> bool:
    """Remove target model file."""
    try:
        repo = hf_wrapper.get_repo_info(repo_id)
        rev = hf_wrapper.get_revision_info(repo_id, revision)
        f = hf_wrapper.get_file_info(repo_id, revision, file_name)

        if not repo or not rev or not f:
            logger.info(
                "Repo or file not found: repo=%s, file=%s, rev=%s",
                repo_id,
                file_name,
                revision,
            )
            return False

        # remove snapshot file
        _rm_file(f.file_path, repo.repo_path / "snapshots")

        # remove blob file
        # blob path and file path are the same on windows
        if f.blob_path != f.file_path and (
            _can_delete_blob(
                file_name,
                repo.repo_path / "snapshots",
                f.blob_path,
            )
        ):
            _rm_file(f.blob_path, repo.repo_path / "blobs")

        # if the snapshot dir is not longer existing, it means that the
        # revision is deleted entirely, hence all the refs pointing to
        # the revision should be deleted
        ref_dir = repo.repo_path / "refs"
        if not rev.snapshot_path.exists() and ref_dir.exists():
            ref_files = [ref_dir / ref for ref in rev.refs]
            for ref in ref_files:
                _rm_file(ref, ref_dir)
    except (OSError, ValueError):
        return False

    return True


def repo_rm(repo_id: str, revision: str | None) -> bool:
    """Remove target repo."""
    try:
        repo = hf_wrapper.get_repo_info(repo_id)
        if not repo:
            return True

        for rev in repo.revisions:
            if (
                revision
                and revision not in rev.refs
                and not rev.commit_hash.startswith(revision)
            ):
                continue

            # remove snapshot files
            for f in rev.files:
                file_rm(
                    repo_id,
                    str(f.file_path.relative_to(rev.snapshot_path)),
                    rev.commit_hash,
                )

    except (OSError, ValueError):
        return False

    return True
