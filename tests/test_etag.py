"""Test save and load etag."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

import huggingface_hub as hf

from hffs.common.context import HffsContext
from hffs.common.etag import load_etag, save_etag
from hffs.config.hffs_config import HffsConfig

if TYPE_CHECKING:
    import py
    import pytest

ETAG = "1234"
REPO = "test_repo"
FILE = "test_file"
REV = "test_rev"


def test_save_and_load(
    monkeypatch: pytest.MonkeyPatch,
    tmpdir: py.path.local,
) -> None:
    """Test save etag."""

    def mock_module_path(*_: List[Any], **__: dict[str, Any]) -> str:
        return str(HffsContext.get_model_dir() / REPO / REV / FILE)

    monkeypatch.setattr(
        hf,
        "try_to_load_from_cache",
        mock_module_path,
    )

    conf = HffsConfig(cache_dir=str(tmpdir))

    HffsContext.init_with_config(conf)

    save_etag(ETAG, REPO, FILE, REV)
    etag = load_etag(REPO, FILE, REV)

    assert etag == ETAG