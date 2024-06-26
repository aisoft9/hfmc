#!/usr/bin/python3
import argparse
import asyncio
import os
import logging.handlers
import logging
import sys

from .common.peer_store import PeerStore
from .client import http_client
from .client.model_manager import ModelManager
from .client.peer_manager import PeerManager
from .server import http_server
from .common.settings import HFFS_LOG_DIR
from .client.daemon_manager import daemon_start, daemon_stop, daemon_status
from .client.uninstall_manager import uninstall_hffs

logger = logging.getLogger(__name__)


async def peer_cmd(args):
    with PeerStore() as store:
        peer_manager = PeerManager(store)

        if args.peer_command == "add":
            peer_manager.add_peer(args.IP, args.port)
        elif args.peer_command == "rm":
            peer_manager.remove_peer(args.IP, args.port)
        elif args.peer_command == "ls":
            await peer_manager.list_peers()
        else:  # no matching subcmd
            raise ValueError("Invalid subcommand")

    if args.peer_command in ("add", "rm"):
        await peer_manager.notify_peer_change()


async def model_cmd(args):
    model_manager = ModelManager()
    model_manager.init()

    if args.model_command == "search":
        await model_manager.search_model(args.repo_id, args.file, args.revision)
    elif args.model_command == "add":
        await model_manager.add(args.repo_id, args.file, args.revision)
    elif args.model_command == "ls":
        model_manager.ls(args.repo_id)
    elif args.model_command == "rm":
        model_manager.rm(args.repo_id, revision=args.revision,
                         file_name=args.file)
    else:
        raise ValueError("Invalid subcommand")


async def daemon_cmd(args):
    if args.daemon_command == "start":
        if args.daemon == "true":
            await daemon_start(args)
        else:
            await http_server.start_server(args.port)
    elif args.daemon_command == "stop":
        await daemon_stop()
    elif args.daemon_command == "status":
        await daemon_status()
    else:
        raise ValueError("Invalid subcommand")


async def uninstall_cmd():
    await uninstall_hffs()


async def exec_cmd(args, parser):
    try:
        if args.command == "peer":
            await peer_cmd(args)
        elif args.command == "model":
            await model_cmd(args)
        elif args.command == "daemon":
            await daemon_cmd(args)
        elif args.command == "uninstall":
            await uninstall_cmd()
        else:
            raise ValueError("Invalid command")
    except ValueError as e:
        print("{}".format(e))
        parser.print_usage()
    except Exception as e:
        print(f"{e}")


def arg_parser():
    parser = argparse.ArgumentParser(prog='hffs')
    subparsers = parser.add_subparsers(dest='command')

    # hffs daemon {start,stop} [--port port]
    daemon_parser = subparsers.add_parser('daemon')
    daemon_subparsers = daemon_parser.add_subparsers(dest='daemon_command')
    daemon_start_parser = daemon_subparsers.add_parser('start')
    daemon_start_parser.add_argument('--port', type=int, default=9009)
    daemon_start_parser.add_argument("--daemon", type=str, default="true")
    daemon_subparsers.add_parser('stop')
    daemon_subparsers.add_parser('status')

    # hffs peer {add,rm,ls} IP [--port port]
    peer_parser = subparsers.add_parser('peer')
    peer_subparsers = peer_parser.add_subparsers(dest='peer_command')
    peer_add_parser = peer_subparsers.add_parser('add')
    peer_add_parser.add_argument('IP')
    peer_add_parser.add_argument('--port', type=int, default=9009)
    peer_rm_parser = peer_subparsers.add_parser('rm')
    peer_rm_parser.add_argument('IP')
    peer_rm_parser.add_argument('--port', type=int, default=9009)
    peer_subparsers.add_parser('ls')

    # hffs model {ls,add,rm,search} [--repo-id id] [--revision REVISION] [--file FILE]
    model_parser = subparsers.add_parser('model')
    model_subparsers = model_parser.add_subparsers(dest='model_command')
    model_ls_parser = model_subparsers.add_parser('ls')
    model_ls_parser.add_argument('--repo_id')
    model_add_parser = model_subparsers.add_parser('add')
    model_add_parser.add_argument('repo_id')
    model_add_parser.add_argument('file')
    model_add_parser.add_argument('--revision', type=str, default="main")
    model_rm_parser = model_subparsers.add_parser('rm')
    model_rm_parser.add_argument('repo_id')
    model_rm_parser.add_argument('file')
    model_rm_parser.add_argument('--revision', type=str, default="main")
    model_search_parser = model_subparsers.add_parser('search')
    model_search_parser.add_argument('repo_id')
    model_search_parser.add_argument('file')
    model_search_parser.add_argument('--revision', type=str, default="main")

    # hffs uninstall
    subparsers.add_parser('uninstall')

    return parser.parse_args(), parser


def logging_level():
    # Only use DEBUG or INFO level for logging
    verbose = os.environ.get("HFFS_VERBOSE", None)
    return logging.DEBUG if verbose else logging.INFO


def logging_handler(args):
    # daemon's logs go to log files, others go to stdout
    if args.command == "daemon" and args.daemon_command == "start" and args.daemon == "false":
        os.makedirs(HFFS_LOG_DIR, exist_ok=True)
        log_path = os.path.join(HFFS_LOG_DIR, "hffs.log")
        handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=2*1024*1024, backupCount=5)
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(log_format))
    else:
        handler = logging.StreamHandler(stream=sys.stderr)
        log_format = "%(message)s"
        handler.setFormatter(logging.Formatter(log_format))

    return handler


def setup_logging(args):
    # configure root logger
    handler = logging_handler(args)

    level = logging_level()
    handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # suppress lib's info log
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)


async def async_main():
    args, parser = arg_parser()
    setup_logging(args)
    await exec_cmd(args, parser)


def main():
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
        # ignore error, async not run complete, error log may appear between async log
        pass
