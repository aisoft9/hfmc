#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from pathlib import Path

from prettytable import PrettyTable
from huggingface_hub import scan_cache_dir, hf_hub_download, CachedRevisionInfo, CachedRepoInfo, HFCacheInfo
from . import http_client
from ..common.settings import HFFS_MODEL_DIR
from ..common.hf_adapter import save_etag

logger = logging.getLogger(__name__)


def _assume(pred, msg):
    if not pred:
        logger.info(msg)
        raise ValueError()


def _is_parent(parent: Path, child: Path):
    try:
        child.absolute().relative_to(parent.absolute())
        return True
    except ValueError:
        return False


def _rm_file(fp: Path, root_path: Path, msg: str):
    # fp is NOT in root_path, raise error
    _assume(_is_parent(root_path, fp), f"{fp} is not in {root_path}")

    # remove target file
    if fp.exists() and fp.is_file():
        fp.unlink()
        logger.debug(f"{msg}: {fp}")

    # remove parent directories if empty up to root_path
    parent_dir = fp.parent
    while _is_parent(root_path, parent_dir):
        if not any(parent_dir.iterdir()):
            parent_dir.rmdir()
            logger.debug(f"Remove {parent_dir}")
            parent_dir = parent_dir.parent
        else:
            break


def _match_repo(cache_info: HFCacheInfo, repo_id):
    for repo in cache_info.repos:
        if repo.repo_id == repo_id:
            return repo
    return None


def _match_rev(repo_info: CachedRepoInfo, revision):
    for rev in repo_info.revisions:
        if revision in rev.refs or rev.commit_hash.startswith(revision):
            return rev
    return None


def _match_file(rev_info: CachedRevisionInfo, file_name: str):
    file_path = rev_info.snapshot_path / file_name
    for f in rev_info.files:
        if f.file_path == file_path:
            return f
    return None


def _rm(repo_id, file_name, revision="main"):
    # check necessary arguments
    _assume(repo_id, "Missing repo_id")
    _assume(file_name, "Missing file_name")
    _assume(revision, "Missing revision")

    # match cached repo
    cache_info = scan_cache_dir(HFFS_MODEL_DIR)
    repo_info = _match_repo(cache_info, repo_id)
    _assume(repo_info, "No matching repo")

    # match cached revision
    rev_info = _match_rev(repo_info, revision)
    _assume(rev_info, "No matching revision")

    # match cached file
    file_info = _match_file(rev_info, file_name)
    _assume(file_info, "No matching file")

    # remove snapshot file
    _rm_file(file_info.file_path,
             repo_info.repo_path / "snapshots",
             "Remove snapshot file")

    # remove blob file
    _rm_file(file_info.blob_path,
             repo_info.repo_path / "blobs",
             "Remove blob")

    # if the snapshot dir is not longer existing, it means that the
    # revision is deleted entirely, hence all the refs pointing to
    # the revision should be deleted
    ref_dir = repo_info.repo_path / "refs"
    if not rev_info.snapshot_path.exists() and ref_dir.exists():
        ref_files = [ref_dir / ref for ref in rev_info.refs]
        for ref in ref_files:
            _rm_file(ref, ref_dir, "Remove ref file")


def _ls_repos():
    cache_info = scan_cache_dir(cache_dir=HFFS_MODEL_DIR)

    table = PrettyTable()
    table.field_names = [
        "REPO ID",
        "SIZE",
        "NB FILES",
        "LOCAL PATH",
    ]

    table.add_rows([
        repo.repo_id,
        "{:>12}".format(repo.size_on_disk_str),
        repo.nb_files,
        str(repo.repo_path),
    ]
        for repo in cache_info.repos
    )
    # Print the table to stdout
    print(table)


def _ls_repo_files(repo_id):
    cache_info = scan_cache_dir(HFFS_MODEL_DIR)
    repo_info = _match_repo(cache_info, repo_id)
    _assume(repo_info, "No matching repo")

    files = []
    for rev in repo_info.revisions:
        for f in rev.files:
            refs = ", ".join(rev.refs)
            commit = rev.commit_hash[:8]
            file_name = f.file_path.relative_to(rev.snapshot_path)
            files.append((refs, commit, file_name, f.size_on_disk_str))

    table = PrettyTable()
    table.field_names = ["REFS", "COMMIT", "FILE", "SIZE"]
    table.add_rows(files)
    print(table)


class ModelManager:
    def init(self):
        if not os.path.exists(HFFS_MODEL_DIR):
            os.makedirs(HFFS_MODEL_DIR)

    async def search_model(self, repo_id, file_name, revision="main"):
        active_peers = await http_client.alive_peers()
        avail_peers = await http_client.search_model(active_peers, repo_id, file_name, revision)
        return (active_peers, avail_peers)

    async def add(self, repo_id, file_name, revision="main"):
        async def do_download(endpoint):
            path = None

            try:
                path = hf_hub_download(repo_id,
                                       revision=revision,
                                       cache_dir=HFFS_MODEL_DIR,
                                       filename=file_name,
                                       endpoint=endpoint)
            except Exception as e:
                logger.info(
                    f"Failed to download model from {endpoint}. Reason: {e}")
                return False, None

            try:
                etag = await http_client.get_model_etag(endpoint, repo_id, file_name, revision)
                if not etag:
                    raise ValueError("ETag not found!")
                save_etag(etag, repo_id, file_name, revision)
            except Exception as e:
                logger.info(
                    f"Failed to save etag from {endpoint} for {repo_id}/{file_name}@{revision}")
                logger.debug(e)
                return False, None

            return True, path

        if not file_name:
            raise ValueError(
                "Current not support download full repo, file name must be provided!")

        _, avails = await self.search_model(repo_id, file_name, revision)

        for peer in avails:
            done, path = await do_download(f"http://{peer.ip}:{peer.port}")
            if done:
                logger.info(f"Download successfully: {path}")
                return

        logger.info("Cannot download from peers; try mirror sites")

        done, path = await do_download("https://hf-mirror.com")
        if done:
            logger.info(f"Download successfully: {path}")
            return

        logger.info("Cannot download from mirror site; try hf.co")

        done, path = await do_download("https://huggingface.co")
        if done:
            logger.info(f"Download successfully: {path}")
            return

        logger.info(
            "Cannot find target model in hf.co; double check the model info")

    def ls(self, repo_id):
        if not repo_id:
            _ls_repos()
        else:
            _ls_repo_files(repo_id)

    def rm(self, repo_id, file_name, revision="main"):
        try:
            _rm(repo_id, file_name, revision)
            logger.info("Success to delete file!")
        except ValueError:
            logger.info("Failed to remove model")
