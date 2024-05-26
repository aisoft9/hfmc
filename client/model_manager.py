#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from prettytable import PrettyTable

from huggingface_hub import HfApi
from huggingface_hub import scan_cache_dir, hf_hub_download
from huggingface_hub.utils import LocalEntryNotFoundError

from client.http_client import alive_peers, search_model
from common.settings import HFFS_MODEL_DIR


class ModelManager:
    def init(self):
        if not os.path.exists(HFFS_MODEL_DIR):
            os.makedirs(HFFS_MODEL_DIR)

    async def search_model(self, repo_id, revision=None, file_name=None):
        active_peers = await alive_peers()
        avail_peers = []
        if len(active_peers) > 0:
            avail_peers = await search_model(active_peers, repo_id, revision, file_name)
        return (active_peers, avail_peers)

    def add(self, repo_id, file_name, revision="main"):
        try:
            path = hf_hub_download(repo_id,
                                   revision=revision,
                                   cache_dir=HFFS_MODEL_DIR,
                                   filename=file_name,
                                   endpoint="https://hf-mirror.com")

            print(path)
            return
        except LocalEntryNotFoundError:
            print("Cannot find target model in mirror site; try to download from hf.co")

        try:
            path = hf_hub_download(repo_id,
                                   revision=revision,
                                   cache_dir=HFFS_MODEL_DIR,
                                   filename=file_name,
                                   endpoint="https://hf-mirror.com/")

            print(path)
            return
        except LocalEntryNotFoundError:
            print("Cannot find target model in hf.co; double check the model info")

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
        print(hf_cache_info_table)

    def rm(self, repo_id, branch, revision):
        hf_cache_info = scan_cache_dir(cache_dir=self.download_dir)

        select_repo = None

        for repo in hf_cache_info.repos:
            if repo.repo_id == repo_id:
                select_repo = repo
                break

        if not select_repo:
            raise LookupError(repo_id + " Not Found!")

        to_delete_revisions_iter = None

        if revision:
            if len(revision) < 7:
                raise ValueError(revision + " too short!")

            to_delete_revisions_iter = map(lambda rev: rev.commit_hash,
                                           filter(lambda rev: rev.commit_hash.startswith(revision), select_repo.revisions))
        else:
            if branch:
                to_delete_revisions_iter = map(lambda rev: rev.commit_hash,
                                               filter(lambda rev: branch in rev.refs, select_repo.revisions))
            else:
                to_delete_revisions_iter = map(
                    lambda rev: rev.commit_hash, select_repo.revisions)

        to_delete_revisions = list(to_delete_revisions_iter)

        if not to_delete_revisions:
            raise LookupError("repo: {}, branch: {}, revision: {}. Not Found!".format(
                repo_id, branch, revision))

        for r in to_delete_revisions:
            print(r)

        sys.stdout.flush()
        confirm = input(
            "WARNING: revisions will be deleted! Enter [y/Y] to confirm: ")

        if confirm.strip() not in ["y", "Y"]:
            print("Cancel delete!")
            return

        sys.stdout.flush()

        delete_strategy = hf_cache_info.delete_revisions(*to_delete_revisions)
        delete_strategy.execute()
        print("success delete {} revisions, free space: {}.\n".format(
            len(to_delete_revisions), delete_strategy.expected_freed_size_str))
