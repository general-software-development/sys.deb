from argparse import Namespace
import asyncio
import shutil

from .async_utils import autorun
from .prog_utils import advance_progress
from .unix_utils import run
from .validate import check_assert

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

async def update(args: Namespace):
    console = Console()
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, complete_style="bar.complete", finished_style="bar.complete"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console, refresh_per_second=2, expand=False
    )
    console.rule("sys.deb update")
    progress.start()

    task0 = progress.add_task("apt update && apt full-upgrade && apt autoremove", total=3)
    task1 = progress.add_task("systemd-tmpfiles --clean", total=1)
    task2 = progress.add_task("Gathering environment details", total=1)

    async def systemd_tmpfiles_path() -> str | None:
        p = shutil.which("systemd-tmpfiles")
        progress.advance(task2)
        return p

    systemd_tmpfiles_path_task = asyncio.create_task(systemd_tmpfiles_path)

    async def handle_apt():
        r = await run(["apt-get", "update"], console)
        check_assert(0, r[0], "apt-get update returned non-zero exit code %value")
        progress.advance(task0)
        r = await run(["apt-get", "full-upgrade", "-y"], console)
        check_assert(0, r[0], "apt-get full-upgrade returned non-zero exit code %value")
        progress.advance(task0)
        r = await run(["apt-get", "autoremove", "-y"], console)
        check_assert(0, r[0], "apt-get autoremove returned non-zero exit code %value")
        progress.advance(task0)

    async def handle_tmpfiles():
        path = await systemd_tmpfiles_path_task

        if not path:
            console.print("\\[sys.deb] WARNING: Skipping systemd-tmpfiles --clean -- systemd-tmpfiles not found.", style='yellow')

        r = await run([path, "--clean"], console)
        check_assert(0, r[0], "systemd-tmpfiles --clean returned non-zero exit code %value")
        progress.advance(task1)

    handle_apt_task = asyncio.create_task(handle_apt())
    handle_tmpfiles_task = asyncio.create_task(handle_tmpfiles())

    await handle_apt_task
    await handle_tmpfiles_task

    progress.stop()

    # TODO: Update initramfs, Update GRUB (plus [Y/n] prompt)
