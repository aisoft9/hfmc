#!/usr/bin/python3
import argparse
import sys
import asyncio

from client import http_client
from common.peer import Peer
from common.peer_store import PeerStore
from client.model_manager import ModelManager
from client.peer_manager import PeerManager
from server import http_server


peer_store = PeerStore()
peer_store.open()
peer_manager = PeerManager(peer_store)

model_manager = ModelManager()
model_manager.init()


def peer_cmd(args):
    if args.peer_command == "add":
        peer_manager.add_peer(args.IP, args.port)
    elif args.peer_command == "rm":
        peer_manager.remove_peer(args.IP, args.port)
    elif args.peer_command == "ls":
        peer_manager.list_peers()
    else:  # no matching subcmd
        raise ValueError("Invalid subcommand")


async def model_cmd(args):
    if args.model_command == "search":
        await model_manager.search_model(args.repo_id, args.file, args.revision)
    elif args.model_command == "add":
        model_manager.add(args.repo_id, args.file, args.revision)
    elif args.model_command == "ls":
        model_manager.ls(args.repo_id)
    elif args.model_command == "rm":
        model_manager.rm(args.repo_id, branch=args.revision,
                         revision=args.revision)
    else:
        raise ValueError("Invalid subcommand")


async def daemon_cmd(args):
    if args.daemon_command == "start":
        await http_server.start_server(args.port)
    elif args.daemon_command == "stop":
        await http_client.stop_server()
        print("HFFS daemon stopped!")


async def exec_cmd(args, parser):
    try:
        if args.command == "peer":
            peer_cmd(args)
        elif args.command == "model":
            await model_cmd(args)
        elif args.command == "daemon":
            await daemon_cmd(args)
        else:
            raise ValueError("Invalid command")
    except ValueError:
        parser.print_usage()


def arg_parser():
    parser = argparse.ArgumentParser(prog='hffs')
    subparsers = parser.add_subparsers(dest='command')

    # hffs daemon {start,stop} [--port port]
    daemon_parser = subparsers.add_parser('daemon')
    daemon_subparsers = daemon_parser.add_subparsers(dest='daemon_command')
    daemon_start_parser = daemon_subparsers.add_parser('start')
    daemon_start_parser.add_argument('--port', type=int, default=8000)
    daemon_subparsers.add_parser('stop')

    # hffs peer {add,rm,ls} IP [--port port]
    peer_parser = subparsers.add_parser('peer')
    peer_subparsers = peer_parser.add_subparsers(dest='peer_command')
    peer_add_parser = peer_subparsers.add_parser('add')
    peer_add_parser.add_argument('IP')
    peer_add_parser.add_argument('--port', type=int, default=8000)
    peer_rm_parser = peer_subparsers.add_parser('rm')
    peer_rm_parser.add_argument('IP')
    peer_rm_parser.add_argument('--port', type=int, default=8000)
    peer_subparsers.add_parser('ls')

    # hffs model {ls,add,rm,search} [--repo-id id] [--revision REVISION] [--file FILE]
    model_parser = subparsers.add_parser('model')
    model_subparsers = model_parser.add_subparsers(dest='model_command')
    model_ls_parser = model_subparsers.add_parser('ls')
    model_ls_parser.add_argument('--repo_id')
    model_add_parser = model_subparsers.add_parser('add')
    model_add_parser.add_argument('repo_id')
    model_add_parser.add_argument('--revision', type=str, default="main")
    model_add_parser.add_argument('--file')
    model_rm_parser = model_subparsers.add_parser('rm')
    model_rm_parser.add_argument('repo_id')
    model_rm_parser.add_argument('--revision', type=str, default="main")
    model_rm_parser.add_argument('--file')
    model_search_parser = model_subparsers.add_parser('search')
    model_search_parser.add_argument('repo_id')
    model_search_parser.add_argument('--revision', type=str, default="main")
    model_search_parser.add_argument('--file')

    return parser.parse_args(), parser


async def main():
    args, parser = arg_parser()
    try:
        await exec_cmd(args, parser)
    finally:
        peer_store.close()

if __name__ == "__main__":
    asyncio.run(main())