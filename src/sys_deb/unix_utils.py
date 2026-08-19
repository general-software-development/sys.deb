import os
import sys
import subprocess
from rich.console import Console
from rich.text import Text
import asyncio

out_lock = asyncio.Lock()

def require_root() -> None:
    if os.geteuid() != 0:
        os.execvp("sudo", ["sudo", sys.executable, *sys.argv])

async def run(command: list[str], console: Console) -> tuple[int, list[str], list[str]]:  # exit_code, stdout, stderr
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    assert process.stdout
    assert process.stderr

    stdout_lines = []
    stderr_lines = []

    async def read(stream: asyncio.StreamReader, output: list[str], style=None):
        while line := await stream.readline():
            text = line.decode(errors="replace").rstrip("\n").strip()
            output.append(text)
            async with out_lock:
                console.print(Text.from_ansi(text.rstrip("\n")), style=style)

    await asyncio.gather(read(process.stdout, stdout_lines), read(process.stderr, stderr_lines, "red"))

    return await process.wait(), stdout_lines, stderr_lines
