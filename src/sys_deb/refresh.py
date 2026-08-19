from argparse import Namespace
import subprocess
import asyncio
import shutil

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

from .unix_utils import run
from .validate import check_assert
from .async_utils import autorun
from .prog_utils import advance_progress
from .templates import apt_color_output

import os
import shutil

async def refresh(args: Namespace):
    console = Console()
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None, complete_style="bar.complete", finished_style="bar.complete"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console, refresh_per_second=2, expand=True
        ) as p:
        task0 = p.add_task("Cleaning unused apt packages", total=3)
        task1 = p.add_task("Cleaning old tmpfiles", total=1)
        task2 = p.add_task("Cleaning python package caches", total=2)
        task3 = p.add_task("Gathering environment details", total=2)

        @autorun
        @advance_progress(p, task3)
        async def uv_installed_task() -> str | None:
            return shutil.which('uv')

        @autorun
        @advance_progress(p, task3)
        async def pip_installed_task() -> str | None:
            return shutil.which('pip')

        @autorun
        @advance_progress(p, task3)
        async def systemd_tmpfiles_installed_task() -> str | None:
            if p := shutil.which('systemd-tmpfiles'):
                return p

        @autorun
        async def clean_apt_task():
            check_assert(0, (await run(["apt-get", *apt_color_output, "update", "-y"], console))[0], "apt update returned non-zero exit code %value.")
            p.advance(task0)
            check_assert(0, (await run(["apt-get", *apt_color_output, "clean", "-y"], console))[0], "apt clean returned non-zero exit code %value.")
            p.advance(task0)
            check_assert(0, (await run(["apt-get", *apt_color_output, "autoremove", "-y"], console))[0],
            "apt autoremove returned non-zero exit code %value.")
            p.advance(task0)

        @autorun
        async def clean_tmpfiles():
            path = await systemd_tmpfiles_installed_task

            if not path:
                console.print("\\[sys.deb] ERROR: Skipping `systemd-tmpfiles --clean` as systemd-tmpfiles / systemd-standalone-tmpfiles were not found.", style="red")
                return

            r = await run([path, "--clean"], console)
            check_assert(0, r[0], f"{path} --clean returned non-zero exit code %value.")
            p.advance(task1)
            return r

        @autorun
        async def clean_pypack_cache_task():
            async def do_pip():
                path = await pip_installed_task
                if not path:
                    console.print(f"[sys.deb] ERROR: Skipping `pip cache purge` as pip was not found.", style="red")
                    return

                r = await run([path, "cache", "purge", "-v"], console)
                check_assert(0, r[0], "pip cache purge returned non-zero exit code %value")
                return r

            async def do_uv():
                path = await uv_installed_task
                if not path:
                    console.print(f"[sys.deb] WARNING: Skipping `uv cache prune` as pip was not found.", style="yellow")
                    return

                r = await run(["uv", "cache", "prune", "-v"], console)
                check_assert(0, r[0], "uv cache prune returned non-zero exit code %value")
                return r
            
            pip_task = asyncio.create_task(do_pip())
            pip_task.add_done_callback(lambda t: p.advance(task2) if pip_task.result() is not None else None)
            uv_task = asyncio.create_task(do_uv())
            uv_task.add_done_callback(lambda t: p.advance(task2) if uv_task.result() is not None else None)

            await pip_task
            await uv_task

        await clean_tmpfiles
        await clean_apt_task
        await clean_pypack_cache_task

        p.refresh()
