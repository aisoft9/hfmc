"""A wrapper of huggingface_hub api."""

from __future__ import annotations
import logging
from typing import List

import huggingface_hub as hf  # type: ignore[import-untyped]
from huggingface_hub.hf_api import HfApi  # type: ignore[import-untyped]

from hfmc.common.context import HfmcContext
from hfmc.common.repo_files import RepoFileList

COMMIT_HASH_HEADER = hf.constants.HUGGINGFACE_HEADER_X_REPO_COMMIT
logger = logging.getLogger(__name__)


def get_cache_info() -> hf.HFCacheInfo:
    """Get cache info."""
    return hf.scan_cache_dir(HfmcContext.get_model_dir_str())


def get_repo_info(repo_id: str) -> hf.CachedRepoInfo | None:
    """Get repo info by repo_id."""
    cache_info = get_cache_info()
    for repo in cache_info.repos:
        if repo.repo_id == repo_id:
            return repo
    return None


def get_revision_info(
    repo_id: str,
    revision: str,
) -> hf.CachedRevisionInfo | None:
    """Get revision info by revision."""
    repo_info = get_repo_info(repo_id)

    if repo_info is None:
        return None

    for rev in repo_info.revisions:
        if revision in rev.refs or rev.commit_hash.startswith(revision):
            return rev

    return None


def get_file_info(
    repo_id: str,
    revision: str,
    filename: str,
) -> hf.CachedFileInfo | None:
    """Get file info by filename."""
    rev_info = get_revision_info(repo_id, revision)

    if rev_info is None:
        return None

    for f in rev_info.files:
        if rev_info.snapshot_path / filename == f.file_path:
            return f

    return None


def get_repo_file_list(
    endpoint: str,
    repo_id: str,
    revision: str,
) -> RepoFileList | None:
    """Load repo struct."""
    fs = hf.HfFileSystem(endpoint=endpoint)
    repo = f"{repo_id}@{revision}/"
    path = f"hf://{repo}"
    try:
        beg = len(repo)
        return [f[beg:] for f in fs.find(path)]
    except (ValueError, OSError, IOError):
        logger.debug(
            "Cannot load repo file list for %s, %s, %s",
            endpoint,
            repo_id,
            revision,
        )
        return None


def verify_revision(
    repo_id: str,
    revision: str,
    endpoints: List[str],
) -> str | None:
    """Verify if revision is valid."""
    # verify with local cache
    rev_info = get_revision_info(repo_id, revision)
    if rev_info:
        return rev_info.commit_hash

    # verify with remote endpoints
    for endpoint in endpoints:
        api = HfApi(endpoint=endpoint)
        try:
            model = api.model_info(repo_id, revision=revision)
            if model and model.sha:
                return model.sha
        except (OSError, IOError, ValueError):
            continue

    return None
