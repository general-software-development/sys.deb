from argparse import Namespace
import subprocess
import asyncio

from rich.console import Console
from rich.progress import Progress

from .unix_utils import run

async def refresh(args: Namespace):
    console = Console()

    with Progress(console=console) as p:
        task0 = p.add_task("Cleaning unused apt packages", total=3)
        task1 = p.add_task("Cleaning old tmpfiles", total=1)

        tmpfiles_clean = asyncio.create_task(run(["systemd-tmpfiles", "--clean"], console))
        tmpfiles_clean.add_done_callback(lambda *_, **__: p.advance(task1))

        assert 0 == (await run(["apt", "update"], console))[0]
        p.advance(task0)
        assert 0 == (await run(["apt", "autoclean"], console))[0]
        p.advance(task0)
        assert 0 == (await run(["apt", "autoremove"], console))[0]
        p.advance(task0)
        await tmpfiles_clean
