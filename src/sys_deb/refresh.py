from argparse import Namespace
import subprocess
import asyncio

from rich.console import Console
from rich.progress import Progress

from .unix_utils import run
from .validate import check_assert
from .async_utils import autorun

async def refresh(args: Namespace):
    console = Console()

    with Progress(console=console) as p:
        task0 = p.add_task("Cleaning unused apt packages", total=3)
        task1 = p.add_task("Cleaning old tmpfiles", total=1)
        task2 = p.add_task("Cleaning python package caches", total=2)
        task3 = p.add_task("Gathering environment details", total=1)

        tmpfiles_clean = asyncio.create_task(run(["systemd-tmpfiles", "--clean"], console))
        tmpfiles_clean.add_done_callback(lambda *_, **__: p.advance(task1))

        @autorun
        async def uv_installed_task():
            return True

        async def clean_apt():
            check_assert(0, (await run(["apt", "update"], console))[0], "apt update returned non-zero exit code %value.")
            p.advance(task0)
            check_assert(0, (await run(["apt", "autoclean"], console))[0], "apt autoclean returned non-zero exit code %value.")
            p.advance(task0)
            check_assert(0, (await run(["apt", "autoremove"], console))[0],
            "apt autoremove returned non-zero exit code %value.")
            p.advance(task0)

        clean_apt_task = asyncio.create_task(clean_apt)

        async def clean_pypack_cache():
            pip_cache_purge_1 = asyncio.create_task(run(["pip", "cache", "purge"]))

            def do_uv():

            
            check_assert(0, (await run(["pip", "cache", "purge"]))[0], "pip cache purge returned non-zero exit code %value.")


        await tmpfiles_clean
