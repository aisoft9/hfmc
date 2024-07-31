#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import json
import logging

from ..common.settings import HFFS_NOSHARE_CONF

logger = logging.getLogger(__name__)


def noshare_save(repos: [str]):
    with open(HFFS_NOSHARE_CONF, "w") as fp:
        json.dump(repos, fp)


def noshare_load():
    if not os.path.exists(HFFS_NOSHARE_CONF):
        return []

    with open(HFFS_NOSHARE_CONF, "r") as fp:
        return json.load(fp)


def is_noshare_repo(repo_id: str):
    exist_repos = noshare_load()
    return repo_id in exist_repos


def noshare_add(repo_id: str):
    exist_repos = noshare_load()

    if repo_id not in exist_repos:
        exist_repos.append(repo_id)

    noshare_save(exist_repos)
    logger.info("Add success!")


def noshare_ls():
    exist_repos = noshare_load()

    for r in exist_repos:
        logger.info(r)


def noshare_rm(repo_id: str):
    exist_repos = noshare_load()

    if repo_id in exist_repos:
        exist_repos.remove(repo_id)
        noshare_save(exist_repos)

    logger.info("Remove success!")
