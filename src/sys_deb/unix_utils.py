import os
import sys
import subprocess
from rich.console import Console
import asyncio

def require_root() -> None:
    if os.geteuid() != 0:
        os.execvp("sudo", ["sudo", sys.executable, *sys.argv])

async def run(command: list[str], console: Console) -> tuple[int, list[str], list[str]]:  # exit_code, stdout, stderr
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    assert process.stdout
    assert process.stderr

    stdout_lines = []
    stderr_lines = []

    async def read(stream: asyncio.StreamReader, output: list[str], style=None):
        while line := await stream.readline():
            output.append(line.decode())
            console.print(line.decode(), end="", style=style)

    await asyncio.gather(read(process.stdout), read(process.stderr, "red"))

    return await process.wait(), stdout_lines, stderr_lines
