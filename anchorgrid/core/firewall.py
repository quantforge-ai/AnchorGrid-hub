"""
AnchorGrid Core - Security Firewall

Detects and blocks sensitive files from entering repositories.
Part of the "Smart Guardian" system.
"""

import os
import subprocess
import fnmatch
import yaml
from pathlib import Path
from rich.console import Console

console = Console()

def load_grid_config(path=None):
    """Load config.grid from current directory or parent"""
    config_file = "config.grid"
    search_path = Path(path or os.getcwd())
    
    # Simple recursive search upwards
    while search_path != search_path.parent:
        target = search_path / config_file
        if target.exists():
            try:
                with open(target, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        search_path = search_path.parent
        
    return {}

def inspect_staged_files():
    """
    Scans files about to be pushed against firewall rules.
    Returns (violations, warnings)
    """
    # 1. Get staged files via git
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return [], []
        
    staged_files = result.stdout.strip().split("\n")
    if not staged_files or staged_files == ['']:
        return [], []

    # 2. Get rules from config.grid
    config = load_grid_config()
    firewall = config.get('firewall', {})
    block_patterns = firewall.get('block', [".env", "secrets.json", "*.pem", "anchorgrid_keys.py"])
    warn_patterns = firewall.get('warn', [])

    violations = []
    warnings = []

    for f in staged_files:
        # Check blocks
        for pattern in block_patterns:
            if fnmatch.fnmatch(f, pattern):
                violations.append(f)
                break
        
        # Check warnings
        for pattern in warn_patterns:
            if fnmatch.fnmatch(f, pattern):
                warnings.append(f)
                break
                
    return violations, warnings

def quarantine_files(files):
    """Moves blocked files to a secure stash - 'Digital Jail'"""
    for f in files:
        stash_msg = f"Grid-Auto-Quarantine: {f} (Blocked by Firewall)"
        
        # Move to stash (unstage + save)
        subprocess.run(["git", "reset", "HEAD", f])
        subprocess.run(["git", "stash", "push", "-m", stash_msg, f])
        
        console.print(f"[bold red]🛑 CONTAMINANT DETECTED:[/bold red] [cyan]{f}[/cyan] has been seized by the Grid Authority.")
        console.print(f"[dim]   It is now serving a life sentence in 'Solitary Confinement' (Stash).[/dim]")

def verify_push_safety():
    """
    Main entry point for shell push/submit commands.
    Returns True if safe to proceed.
    """
    violations, warnings = inspect_staged_files()
    
    if violations:
        console.print("\n[bold red]⚠️  SECURITY INTERCEPTED BY SMART GUARDIAN[/bold red]")
        quarantine_files(violations)
        console.print("[yellow]System sanitized. Please verify your staged changes before trying again.[/yellow]\n")
        return False
        
    if warnings:
        for w in warnings:
            console.print(f"[bold yellow]⚠️  PROBATION WARNING:[/bold yellow] [cyan]{w}[/cyan] makes the Grid nervous. Proceed?")
            from rich.prompt import Confirm
            if not Confirm.ask(""):
                return False
                
    return True
