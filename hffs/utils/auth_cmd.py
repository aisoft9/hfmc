"""Commands for authentication."""

from argparse import Namespace
from huggingface_hub import login, logout  # type: ignore[import-untyped]


async def exec_cmd(args: Namespace) -> None:
    """Execute command."""
    if args.auth_command == "login":
        login()
    elif args.auth_command == "logout":
        logout()
    else:
        raise NotImplementedError
