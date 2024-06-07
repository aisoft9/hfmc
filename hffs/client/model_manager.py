#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging

from prettytable import PrettyTable
from huggingface_hub import scan_cache_dir, hf_hub_download, DeleteCacheStrategy
from . import http_client
from ..common.settings import HFFS_MODEL_DIR
from ..common.hf_adapter import save_etag


def get_path_in_snapshot(repo_path, commit_hash, file_path):
    return os.path.normpath(f"{repo_path}/snapshots/{commit_hash}/{file_path}")


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
                logging.warning("Exception: {}".format(e))
                return False, None

            try:
                etag = await http_client.get_model_etag(endpoint, repo_id, file_name, revision)
                if not etag:
                    raise ValueError("ETag not found!")
                save_etag(etag, repo_id, file_name, revision)
            except Exception as e:
                logging.warning("Exception: {}".format(e))
                return False, None

            return True, path

        if not file_name:
            raise ValueError(
                "Current not support download full repo, file name must be provided!")

        _, avails = await self.search_model(repo_id, file_name, revision)

        for peer in avails:
            done, path = await do_download(f"http://{peer.ip}:{peer.port}")
            if done:
                logging.info(f"Download successfully: {path}")
                return

        logging.info("Cannot download from peers; try mirror sites")

        done, path = await do_download("https://hf-mirror.com")
        if done:
            logging.info(f"Download successfully: {path}")
            return

        logging.info("Cannot download from mirror site; try hf.co")

        done, path = await do_download("https://huggingface.co")
        if done:
            logging.info(f"Download successfully: {path}")
            return

        logging.info(
            "Cannot find target model in hf.co; double check the model info")

    def ls(self, repo_id):
        hf_cache_info = scan_cache_dir(cache_dir=HFFS_MODEL_DIR)

        hf_cache_info_table = PrettyTable()
        hf_cache_info_table.field_names = [
            "REPO ID",
            "REPO TYPE",
            "SIZE ON DISK",
            "NB FILES",
            "LAST_ACCESSED",
            "LAST_MODIFIED",
            "REFS",
            "LOCAL PATH",
        ]

        hf_cache_info_table.add_rows([
            repo.repo_id,
            repo.repo_type,
            "{:>12}".format(repo.size_on_disk_str),
            repo.nb_files,
            repo.last_accessed_str,
            repo.last_modified_str,
            ", ".join(sorted(repo.refs)),
            str(repo.repo_path),
        ]
            for repo in sorted(
            filter(lambda r: True if (not repo_id or repo_id == r.repo_id) else False,
                   hf_cache_info.repos),
            key=lambda repo: repo.repo_id)
        )
        # Print the table to stdout
        print(hf_cache_info_table)

    def rm(self, repo_id, revision, file_name):
        if not repo_id:
            raise ValueError("Repo id should not be empty!")

        cache_info = scan_cache_dir(cache_dir=HFFS_MODEL_DIR)
        matched_repos = list(
            filter(lambda r: r.repo_id == repo_id, cache_info.repos))
        only_one = 1

        if len(matched_repos) != only_one:
            raise LookupError("Not found! repo: {}".format(repo_id))

        matched_repo = matched_repos[0]
        to_delete_repo_path = []
        to_delete_refs_path = []
        to_delete_revs_path = []
        to_delete_blobs_path = []

        if not revision:
            if file_name:
                raise LookupError("File should be None when revision is None!")

            to_delete_repo_path.append(matched_repo.repo_path)
        else:
            matched_revs = list(filter(
                lambda rev1: rev1.refs and revision in rev1.refs, matched_repo.revisions))

            if matched_revs:
                to_delete_refs_path.append(
                    matched_repo.repo_path / "refs" / revision)
            else:
                matched_revs = list(filter(lambda rev2: rev2.commit_hash.startswith(
                    revision), matched_repo.revisions))

                if not matched_revs:
                    raise LookupError("Not found! rev: {}".format(revision))

                for rev in matched_revs:
                    if rev.refs:
                        for ref in rev.refs:
                            to_delete_refs_path.append(
                                matched_repo.repo_path / "refs" / ref)

                    to_delete_revs_path.append(rev.snapshot_path)

            if file_name:
                to_delete_refs_path = []
                to_delete_revs_path = []

                if len(matched_revs) != only_one:
                    raise LookupError(
                        "Revision should be unique when file not None! rev: {}".format(revision))

                matched_rev = matched_revs[0]

                for f in matched_rev.files:
                    if str(f.file_path) == get_path_in_snapshot(matched_repo.repo_path, matched_rev.commit_hash,
                                                                file_name):
                        to_delete_revs_path.append(f.file_path)

                        # 不支持符号链接的平台，blob_path == file_path, 不需要删除blob
                        if f.blob_path != f.file_path:
                            to_delete_blobs_path.append(f.blob_path)

                        break

                if not to_delete_revs_path:
                    raise LookupError("Not found! file: {}".format(file_name))

        show_delete_path = []

        show_delete_path.extend(to_delete_repo_path)
        show_delete_path.extend(to_delete_refs_path)
        show_delete_path.extend(to_delete_revs_path)
        show_delete_path.extend(to_delete_blobs_path)
        logging.info("Will delete the following files:")

        for p in show_delete_path:
            logging.info(p)

        confirm = input(
            "\nWARNING: files or dirs will be delete! Enter [y/Y] to confirm: ")

        if confirm.strip() not in ["y", "Y"]:
            logging.info("Cancel delete!")
            return

        delete_strategy = DeleteCacheStrategy(expected_freed_size=0,
                                              blobs=frozenset(
                                                  to_delete_blobs_path),
                                              refs=frozenset(
                                                  to_delete_refs_path),
                                              repos=frozenset(
                                                  to_delete_repo_path),
                                              snapshots=frozenset(to_delete_revs_path))

        delete_strategy.execute()
        logging.info("Delete success!")

