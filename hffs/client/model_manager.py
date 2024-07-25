#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import shutil
from pathlib import Path

from prettytable import PrettyTable
from huggingface_hub import scan_cache_dir, hf_hub_download, CachedRevisionInfo, CachedRepoInfo, HFCacheInfo
from . import http_client
from ..common.settings import HFFS_MODEL_DIR
from ..common.hf_adapter import save_etag, save_repo_info

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


def blob_has_multi_links(revisions, blob_path):
    same_blob_count = 0

    for rev in revisions:
        for f in rev.files:
            if f.blob_path == blob_path:
                same_blob_count = same_blob_count + 1

            if same_blob_count > 1:
                break

        if same_blob_count > 1:
            break

    return same_blob_count > 1


def _rm(repo_id, file_name, revision="main"):
    # check necessary arguments
    _assume(repo_id, "Missing repo_id")
    _assume(file_name, "Missing file_name")
    _assume(revision, "Missing revision")

    if os.path.isabs(file_name):
        raise LookupError("File path is path relative to repo, not the path in operating system!")

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

    # remove blob file, on platform not support symbol link, there are equal
    if file_info.blob_path != file_info.file_path:
        if not blob_has_multi_links(repo_info.revisions, file_info.blob_path):
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
            file_path = f.file_path
            files.append((refs, commit, file_name, f.size_on_disk_str, file_path))

    table = PrettyTable()
    table.field_names = ["REFS", "COMMIT", "FILE", "SIZE", "PATH"]
    table.add_rows(files)
    print(table)


class ModelManager:
    def init(self):
        if not os.path.exists(HFFS_MODEL_DIR):
            os.makedirs(HFFS_MODEL_DIR)

    async def search_model(self, repo_id, file_name, revision="main"):
        if file_name:
            await self.search_model_file(repo_id, file_name, revision)
        else:
            await self.search_full_model(repo_id, revision)

    async def search_model_file(self, repo_id, file_name, revision="main"):
        active_peers = await http_client.alive_peers()
        avail_peers = await http_client.search_model_file(active_peers, repo_id, file_name, revision)
        return (active_peers, avail_peers)

    async def search_full_model(self, repo_id, revision):
        active_peers = await http_client.alive_peers()
        avail_peers = await http_client.search_full_model(active_peers, repo_id, revision)
        logger.info("Peers who have the model revision:")
        logger.info(f"{avail_peers}")
        return avail_peers

    async def add(self, repo_id, file_name, revision="main"):
        if file_name:
            return await self.add_file(repo_id, file_name, revision)
        else:
            return await self.add_full_model(repo_id, revision)

    async def add_file(self, repo_id, file_name, revision="main"):
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

        _, avails = await self.search_model_file(repo_id, file_name, revision)

        for peer in avails:
            done, path = await do_download(f"http://{peer.ip}:{peer.port}")
            if done:
                logger.info(f"Download successfully: {path}")
                return True

        logger.info("Cannot download from peers; try mirror sites")

        done, path = await do_download("https://hf-mirror.com")
        if done:
            logger.info(f"Download successfully: {path}")
            return True

        logger.info("Cannot download from mirror site; try hf.co")

        done, path = await do_download("https://huggingface.co")
        if done:
            logger.info(f"Download successfully: {path}")
            return True

        logger.info(
            "Cannot find target model in hf.co; double check the model info")

        return False

    async def download_repo_files(self, endpoint, repo_id, revision):
        repo_info = await http_client.get_hf_repo_info(endpoint, repo_id, revision)

        assert repo_info is not None, f"Repo info returned from {endpoint} is None."
        assert repo_info.get("sha") is not None, "Repo info returned from server must have a revision sha."
        assert repo_info.get("siblings") is not None, "Repo info returned from server must have a siblings list."

        repo_files = [f.get("rfilename") for f in repo_info.get("siblings")]

        for f in repo_files:
            add_success = await self.add_file(repo_id=repo_id, file_name=f, revision=repo_info.get("sha"))

            if not add_success:
                raise LookupError("Failed to download file! repo: {0}, revision: {1}, file name: {2}."
                                  .format(repo_id, repo_info.get("sha"), f))

        save_repo_info(repo_info, repo_id, repo_info.get("sha"))

    async def add_full_model(self, repo_id, revision="main"):
        avail_peers = await self.search_full_model(repo_id, revision)
        to_download_site = []

        if avail_peers:
            select_peer = avail_peers[0]
            to_download_site.append(f"http://{select_peer.ip}:{select_peer.port}")

        to_download_site.extend(["https://hf-mirror.com", "https://huggingface.co"])

        for site in to_download_site:
            try:
                logger.info(f"Start to download repo from {site}!")
                await self.download_repo_files(endpoint=site, repo_id=repo_id, revision=revision)
                logger.info(f"Success download model {repo_id}")
                return
            except Exception as e:
                logger.info(f"Failed to download repo from {site}! ERROR: {e}")

    def ls(self, repo_id):
        if not repo_id:
            _ls_repos()
        else:
            _ls_repo_files(repo_id)

    def rm(self, repo_id, file_name, revision):
        if file_name:
            if revision:
                self.rm_file(repo_id, file_name, revision)
            else:
                self.rm_file(repo_id, file_name, "main")
        else:
            if revision:
                self.rm_model_revision(repo_id, revision)
            else:
                self.rm_model(repo_id)

    def rm_file(self, repo_id, file_name, revision="main"):
        try:
            _rm(repo_id, file_name, revision)
            logger.info("Success to delete file!")
        except ValueError:
            logger.info("Failed to remove model")

    def rm_model(self, repo_id):
        assert repo_id is not None, "Repo id can not be None!"

        cache_info = scan_cache_dir(HFFS_MODEL_DIR)
        repo_info = _match_repo(cache_info, repo_id)
        _assume(repo_info, "No matched repo!")

        repo_path = repo_info.repo_path
        logger.info(repo_path)

        confirm = input("UP path will be delete! Please entry [y/Y] to confirm: ")

        if confirm not in ['y', 'Y']:
            logger.info("Remove repo canceled!")
            return

        shutil.rmtree(repo_path, ignore_errors=True)
        logger.info("Remove success!")

    def rm_model_revision(self, repo_id, revision):
        assert repo_id is not None, "Repo id can not be None!"
        assert revision is not None, "Repo revision can not be None!"

        cache_info = scan_cache_dir(HFFS_MODEL_DIR)
        repo_info = _match_repo(cache_info, repo_id)
        _assume(repo_info, "No matched repo!")

        matched_revs_commit_hash = list(
            map(
                lambda rev: rev.commit_hash,
                filter(
                    lambda rev: revision in rev.refs or rev.commit_hash.startswith(revision), repo_info.revisions
                )
            )
        )

        _assume(matched_revs_commit_hash, "No matched revision!")

        for commit_hash in matched_revs_commit_hash:
            logger.info(commit_hash)

        confirm = input("UP commit will be delete! Please enter [y/Y] to confirm: ")

        if confirm not in ['y', 'Y']:
            logger.info("Remove repo commit canceled!")
            return

        delete_strategy = cache_info.delete_revisions(*matched_revs_commit_hash)
        delete_strategy.execute()

        logger.info("Remove success!")
