from argparse import Namespace
import subprocess

from rich.console import Console
from rich.progress import Progress

from .unix_utils import run

async def refresh(args: Namespace):
    console = Console()

    with Progress(console=console) as p:
        out = subprocess.run([''])
