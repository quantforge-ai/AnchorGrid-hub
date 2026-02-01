"""
Standalone Grid Bash Demo

Run this to see the boot sequence and shell WITHOUT needing
full AnchorGrid package dependencies.
"""

import os
import sys
import shlex
import subprocess
import platform
import shutil
import time
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.track import track

# --- BOOT SEQUENCE ---

console = Console()

LOGO = r"""
   ______     _     __   ____             __  
  / ____/____(_)___/ /  / __ )____ ______/ /_ 
 / / __/ ___/ / __  /  / __  / __ `/ ___/ __ \
/ /_/ / /  / / /_/ /  / /_/ / /_/ (__  ) / / /
\____/_/  /_/\__,_/  /_____/\__,_/____/_/ /_/ 
"""


def boot_sequence():
    """Matrix Glitch boot animation"""
    console.clear()
    
    # 1. Logo with gradient
    lines = LOGO.strip().split("\n")
    
    for i, line in enumerate(lines):
        blue_val = min(255, 100 + (i * 40))
        color = f"rgb(0,{blue_val},255)"
        console.print(line, style=color, justify="center")
        time.sleep(random.uniform(0.03, 0.08))

    console.print(
        "\n[bold italic white]   /// INITIALIZING HIVE MIND CONNECTION... ///   [/bold italic white]",
        justify="center"
    )
    console.print("\n")

    # 2. System diagnostics
    steps = [
        "Mounting File System...",
        "Verifying CUDA Cores...",
        "Loading LoRA Adapters (v2026.04)...",
        "Handshaking with Grid Node...",
        "Allocating Memory Buffers...",
        "ACCESS GRANTED"
    ]
    
    for step in track(steps, description="[cyan]Booting GridBash...[/cyan]", transient=True):
        time.sleep(random.uniform(0.1, 0.3))

    console.clear()
    console.print("[dim]GridBash v1.0 | Connected to Hive Mind[/dim]\n")


# --- SHELL ---

HISTORY_FILE = os.path.expanduser('~/.anchorgrid_history_demo')
GRID_COMMANDS = [
    'login', 'logout', 'status', 'ls', 'train', 'push', 'pull', 
    'trade', 'init', 'exit', 'clear', 'cls', 'whoami', 'help'
]

style = Style.from_dict({
    'env': '#00ff00 bold',
    'user': '#00ffff bold',
    'at': '#ffffff',
    'path': '#ff00ff italic',
})


class GridBash:
    def __init__(self):
        self.session = PromptSession(
            history=FileHistory(HISTORY_FILE),
            auto_suggest=AutoSuggestFromHistory(),
            completer=WordCompleter(GRID_COMMANDS, ignore_case=True)
        )
        self.user = "guest"
        self.cwd = os.getcwd()
        self.hive_connected = False

    def start(self):
        boot_sequence()
        
        while True:
            folder_name = os.path.basename(self.cwd) or '/'
            prompt = [
                ('class:env', '(grid) '),
                ('class:user', f'{self.user}'),
                ('class:at', '@'),
                ('class:path', f'{folder_name} $ '),
            ]

            try:
                text = self.session.prompt(prompt, style=style)
                self.execute(text)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

    def execute(self, text):
        text = text.strip()
        if not text:
            return

        parts = shlex.split(text)
        cmd = parts[0].lower()

        if cmd == 'exit':
            console.print("[yellow]Disconnecting... Goodbye.[/yellow]")
            sys.exit(0)
        elif cmd in ['clear', 'cls']:
            os.system('cls' if os.name == 'nt' else 'clear')
        elif cmd == 'help':
            self.show_help()
        elif cmd == 'login':
            self.user = "Tanishq"
            self.hive_connected = True
            console.print(f"✅ Authenticated as [bold cyan]{self.user}[/bold cyan]")
        elif cmd == 'logout':
            self.user = "guest"
            console.print("✅ Logged out")
        elif cmd == 'whoami':
            console.print(f"[cyan]{self.user}[/cyan]")
        elif cmd == 'status':
            self.show_status()
        elif cmd == 'cd':
            try:
                target = parts[1] if len(parts) > 1 else os.path.expanduser('~')
                os.chdir(target)
                self.cwd = os.getcwd()
            except:
                console.print(f"[red]cd: directory not found[/red]")
        else:
            subprocess.run(text, shell=True)

    def show_help(self):
        console.print("\n[bold cyan]Grid Bash Commands:[/bold cyan]\n")
        table = Table(show_header=False, box=None)
        table.add_row("[green]login[/green]", "Authenticate")
        table.add_row("[green]status[/green]", "System diagnostics")
        table.add_row("[green]help[/green]", "Show this help")
        table.add_row("[green]exit[/green]", "Exit Grid Bash")
        console.print(table)
        console.print("\n[dim]Try typing commands! All system commands work too.[/dim]\n")

    def show_status(self):
        table = Table(title="System Diagnostics", show_header=False, box=None)
        conn = "[green]🟢 Connected[/green]" if self.hive_connected else "[yellow]🔴 Offline[/yellow]"
        total, used, free = shutil.disk_usage(self.cwd)
        
        table.add_row("Identity", f"[cyan]{self.user}[/cyan]")
        table.add_row("Hive Status", conn)
        table.add_row("Storage", f"{used // (2**30)}GB / {total // (2**30)}GB")
        table.add_row("Core Version", "[green]v1.0[/green]")
        
        console.print(Panel(table, border_style="cyan"))


if __name__ == "__main__":
    try:
        GridBash().start()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
