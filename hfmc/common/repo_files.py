"""Handling repo file list."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from hfmc.common.context import HfmcContext

RepoFileList = List[str]

logger = logging.getLogger(__name__)


def _file_list_local_file(
    repo_id: str,
    revision: str,
) -> Path:
    return HfmcContext.get_repo_files_dir() / repo_id / revision / "files.json"


def load_file_list(
    repo_id: str,
    revision: str,
) -> Optional[RepoFileList]:
    """Load repo file list from local config."""
    path = _file_list_local_file(repo_id, revision)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_file_list(repo_id: str, revision: str, files: RepoFileList) -> None:
    """Save repo file list to local config."""
    path = _file_list_local_file(repo_id, revision)
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            path.write_text(json.dumps(files))
    except (ValueError, IOError, OSError) as e:
        logger.debug("Error when saving file list.", exc_info=e)
