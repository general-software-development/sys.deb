import argparse
from argparse import Namespace
import asyncio
from . import unix_utils

from .refresh import refresh

def parse_args() -> Namespace:
    parser = argparse.ArgumentParser("sys.deb")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("refresh")
    sub.add_parser("update")
    sub.add_parser("restart")

    fs = sub.add_parser("fs")
    fs_sub = fs.add_subparsers(dest="fs_cmd", required=True)
    fs_sub.add_parser("commit")

    fs_check = fs_sub.add_parser("check")
    fs_check.add_argument("path")

    pkg = sub.add_parser("pkg")
    pkg_sub = pkg.add_subparsers(dest="pkg_cmd", required=True)

    check_install = pkg_sub.add_parser("check-install")
    check_install.add_argument("packages", nargs="+")

    install = pkg_sub.add_parser("install")
    install.add_argument("packages", nargs="+")

    return parser.parse_args()

def main() -> None:
    unix_utils.require_root()
    args = parse_args()
    if args.cmd:
        asyncio.run(refresh(args))
