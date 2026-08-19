from argparse import Namespace
import asyncio
import shutil

from .async_utils import autorun
from .prog_utils import advance_progress
from .unix_utils import run, risky
from .validate import check_assert

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Confirm

async def update(args: Namespace):
    console = Console()
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None, complete_style="bar.complete", finished_style="bar.complete"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console, refresh_per_second=5, expand=True
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

    systemd_tmpfiles_path_task = asyncio.create_task(systemd_tmpfiles_path())

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
            return

        r = await run([path, "--clean"], console)
        check_assert(0, r[0], "systemd-tmpfiles --clean returned non-zero exit code %value")
        progress.advance(task1)

    handle_apt_task = asyncio.create_task(handle_apt())
    handle_tmpfiles_task = asyncio.create_task(handle_tmpfiles())

    await handle_apt_task
    await handle_tmpfiles_task

    progress.stop()

    yn_update_initramfs = Confirm.ask("Update initramfs?", default=True)
    yn_update_grub = Confirm.ask("Update GRUB?", default=True)

    # TODO: Update initramfs, Update GRUB (plus [Y/n] prompt)

    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None, complete_style="bar.complete", finished_style="bar.complete"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console, refresh_per_second=5, expand=True
    )
    progress.start()

    env_task = progress.add_task("Gathering environment details", total=2)

    async def update_initramfs_path() -> str | None:
        p = shutil.which("update-initramfs")
        progress.advance(env_task)
        return p

    async def update_grub_path() -> str | None:
        p = shutil.which("update-grub")
        progress.advance(env_task)
        return p

    update_initramfs_path_task = asyncio.create_task(update_initramfs_path())
    update_grub_path_task = asyncio.create_task(update_grub_path())

    async def handle_update_initramfs():
        if not yn_update_initramfs:
            return

        path = await update_initramfs_path_task
        if not path:
            console.print(f"[sys.deb] ERROR: update-initramfs not found.", style='red')
            return

        task = progress.add_task("update-initramfs", total=1)
        r = await run(["update-initramfs", "-u"], console)
        check_assert(0, r[0], f"update-initramfs -u returned non-zero exit code %value")
        progress.advance(task)

    async def handle_update_grub():
        if not yn_update_grub:
            return

        path = await update_grub_path_task
        if not path:
            console.print(f"[sys.deb] ERROR: update-grub not found.", style='red')
            return

        task = progress.add_task("update-grub", total=1)
        r = await run(["update-grub"], console)
        check_assert(0, r[0], f"update-grub returned non-zero exit code %value")
        progress.advance(task)

    with risky():  # Ignores SIGINT and SIGTERM
        handle_update_initramfs_task = asyncio.create_task(handle_update_initramfs())
        handle_update_grub_task = asyncio.create_task(handle_update_grub())

        await handle_update_initramfs_task
        await handle_update_grub_task

    progress.stop()
