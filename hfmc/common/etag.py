"""Manager etags for HFMC model files.

This module provides functions to manage etags for Hugging Face model files.
It is needed because huggingface_hub 0.23.0 does not save etags of model files
on Windows.
"""

from __future__ import annotations

import logging
from pathlib import Path

import huggingface_hub as hf  # type: ignore[import-untyped]

from hfmc.common.context import HfmcContext

logger = logging.getLogger(__name__)


def _get_etag_path(repo_id: str, filename: str, revision: str) -> Path | None:
    model_path = hf.try_to_load_from_cache(
        repo_id=repo_id,
        filename=filename,
        revision=revision,
        cache_dir=HfmcContext.get_model_dir_str(),
    )

    # model_path type is (str | Any | None)
    if model_path is None:
        return None

    if not isinstance(model_path, str):
        return None

    rel_path = Path(model_path).relative_to(HfmcContext.get_model_dir())
    return HfmcContext.get_etag_dir() / rel_path


def load_etag(repo_id: str, file_name: str, revision: str) -> str | None:
    """Load etag value from a etag cache file."""
    etag_path = _get_etag_path(repo_id, file_name, revision)

    if not etag_path or not etag_path.exists():
        return None

    return etag_path.read_text().strip()


def save_etag(etag: str, repo_id: str, file_name: str, revision: str) -> None:
    """Save etag value to a etag cache file."""
    etag_path = _get_etag_path(repo_id, file_name, revision)

    if not etag_path:
        logger.debug(
            "Failed to get etag path: repo_id=%s, file_name=%s, revision=%s",
            repo_id,
            file_name,
            revision,
        )
        raise ValueError

    if not etag_path.parent.exists():
        etag_path.parent.mkdir(parents=True, exist_ok=True)

    if not etag_path.exists():
        etag_path.touch()

    etag_path.write_text(etag)
