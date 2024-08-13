"""Model management related commands."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

from prettytable import PrettyTable

from hfmc.client import model_controller

if TYPE_CHECKING:
    from argparse import Namespace

    from hfmc.client.model_controller import FileInfo, RepoInfo

logger = logging.getLogger(__name__)


def _tablize(names: List[str], rows: List[List[str]]) -> None:
    table = PrettyTable()
    table.field_names = names
    table.add_rows(rows)
    logger.info(table)


def _tablize_files(files: List[FileInfo]) -> None:
    if not files:
        logger.info("No files found.")
    else:
        names = ["REFS", "COMMIT", "FILE", "SIZE", "PATH"]
        rows = [
            [
                ",".join(f.refs),
                f.commit_8,
                str(f.file_name),
                str(f.size_on_disk_str),
                str(f.file_path),
            ]
            for f in files
        ]
        _tablize(names, rows)


def _tablize_repos(repos: List[RepoInfo]) -> None:
    if not repos:
        logger.info("No repos found.")
    else:
        names = ["REPO ID", "SIZE", "NB FILES", "LOCAL PATH"]
        rows = [
            [
                r.repo_id,
                f"{r.size_str:>12}",
                str(r.nb_files),
                str(
                    r.repo_path,
                ),
            ]
            for r in repos
        ]
        _tablize(names, rows)


def _ls(args: Namespace) -> None:
    if args.repo:
        files = model_controller.file_list(args.repo)
        _tablize_files(files)
    else:
        repos = model_controller.repo_list()
        _tablize_repos(repos)


async def _add(args: Namespace) -> None:
    if args.file is None and args.revision == "main":
        msg = (
            "In order to keep repo version integrity, when add a repo,"
            "You must specify the commit hash (i.e. 8775f753) with -v option."
        )
        logger.info(msg)
        return

    if args.file:
        target = f"File {args.repo}/{args.file}"
        success = await model_controller.file_add(
            args.repo,
            args.file,
            args.revision,
        )
    else:
        target = f"Model {args.repo}"
        success = await model_controller.repo_add(
            args.repo,
            args.revision,
        )

    if success:
        logger.info("%s added.", target)
    else:
        logger.info("%s failed to add.", target)


def _rm(args: Namespace) -> None:
    if args.file:
        if not args.revision:
            logger.info("Remove file failed, must specify the revision!")
            return

        target = "File"
        success = model_controller.file_rm(
            args.repo,
            args.file,
            args.revision,
        )
    else:
        target = "Model"
        success = model_controller.repo_rm(
            args.repo,
            args.revision,
        )

    if success:
        logger.info("%s remove is done.", target)
    else:
        logger.info("%s failed to remove.", target)


async def _search(args: Namespace) -> None:
    if args.file:
        target = "file"
        peers = await model_controller.file_search(
            args.repo,
            args.file,
            args.revision,
        )
    else:
        target = "model"
        peers = await model_controller.repo_search()

    if peers:
        logger.info(
            "Peers that have target %s:\n[%s]",
            target,
            ",".join(
                [f"{p.ip}:{p.port}" for p in peers],
            ),
        )
    else:
        logger.info("NO peer has target %s.", target)


async def exec_cmd(args: Namespace) -> None:
    """Execute command."""
    if args.model_command == "ls":
        _ls(args)
    elif args.model_command == "add":
        await _add(args)
    elif args.model_command == "rm":
        _rm(args)
    elif args.model_command == "search":
        await _search(args)
    else:
        raise NotImplementedError
