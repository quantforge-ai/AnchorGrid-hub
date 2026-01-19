"""
QuantGrid CLI - Developer Command Line Interface

Provides 'quantgrid push' command for seamless contributions to the Hive Mind.
"""

import os
import sys
import requests
from pathlib import Path
from typing import Optional
from loguru import logger
import typer
from rich.console import Console
from rich.prompt import Prompt

app = typer.Typer(help="🌐 QuantGrid: Federated Intelligence for Quantitative Finance")
console = Console()

# Hub Configuration
HUB_URL = os.getenv("QUANTGRID_HUB_URL", "https://hub.quantgrid.dev")
CONFIG_FILE = Path.home() / ".quantgrid" / "config"


def load_api_key() -> Optional[str]:
    """Load API key from config file"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            for line in f:
                if line.startswith("api_key="):
                    return line.split("=", 1)[1].strip()
    return None


def save_api_key(api_key: str):
    """Save API key to config file"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        f.write(f"api_key={api_key}\n")
    os.chmod(CONFIG_FILE, 0o600)  # Secure permissions


@app.command()
def login():
    """
    Authenticate with QuantGrid Hub to enable model uploads.
    
    You'll get an API key from: https://hub.quantgrid.dev/register
    """
    console.print("\n[bold cyan]🔐 QuantGrid Hub Authentication[/bold cyan]\n")
    
    console.print(f"1. Visit: [link]{HUB_URL}/register[/link]")
    console.print("2. Create an account if you haven't")
    console.print("3. Copy your API key\n")
    
    api_key = Prompt.ask("Paste your API key", password=True)
    
    if not api_key or not api_key.startswith("qg_live_"):
        console.print("❌ [red]Invalid API key format. Should start with 'qg_live_'[/red]")
        sys.exit(1)
    
    # Test the key
    try:
        response = requests.get(
            f"{HUB_URL}/",
            headers={"Authorization": api_key}
        )
        
        if response.status_code == 200:
            save_api_key(api_key)
            console.print("\n✅ [green]Authentication successful![/green]")
            console.print(f"🔑 API key saved to {CONFIG_FILE}")
            console.print("\n🚀 You can now run: [bold]quantgrid push <adapter_path>[/bold]\n")
        else:
            console.print(f"❌ [red]Authentication failed: {response.status_code}[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ [red]Connection error: {e}[/red]")
        console.print(f"💡 Make sure the Hub is running at {HUB_URL}")
        sys.exit(1)


@app.command()
def push(
    adapter_path: str = typer.Argument(..., help="Path to adapter .zip file"),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Your name/handle"),
):
    """
    Submit a trained adapter to the QuantGrid Hive Mind.
    
    Example:
        quantgrid push ./my_adapter.zip --author "Jane Doe"
    """
    console.print("\n[bold cyan]🚀 Uploading to QuantGrid Hub[/bold cyan]\n")
    
    # 1. Check API key
    api_key = load_api_key()
    if not api_key:
        console.print("❌ [red]Not authenticated. Run 'quantgrid login' first.[/red]\n")
        sys.exit(1)
    
    # 2. Verify file exists
    file_path = Path(adapter_path)
    if not file_path.exists():
        console.print(f"❌ [red]File not found: {adapter_path}[/red]\n")
        sys.exit(1)
    
    # 3. Upload to Hub
    console.print(f"📦 Preparing: {file_path.name}")
    file_size_mb = file_path.stat().st_size / 1024 / 1024
    console.print(f"💾 Size: {file_size_mb:.2f} MB\n")
    
    if not author:
        author = Prompt.ask("Your name/handle")
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/zip")}
            params = {"author": author}
            headers = {"Authorization": api_key}
            
            console.print(f"☁️  Uploading to {HUB_URL}/submit...")
            
            response = requests.post(
                f"{HUB_URL}/submit",
                files=files,
                params=params,
                headers=headers,
                timeout=300  # 5 min timeout for large files
            )
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"\n✅ [green]Upload successful![/green]")
                console.print(f"📝 Submission ID: [bold]{data['submission_id']}[/bold]")
                console.print(f"🕵️ Status: {data['status']}")
                console.print(f"\n💡 Check status: [bold]quantgrid status {data['submission_id']}[/bold]\n")
            else:
                console.print(f"\n❌ [red]Upload failed: {response.status_code}[/red]")
                console.print(f"Details: {response.text}\n")
                sys.exit(1)
                
    except Exception as e:
        console.print(f"\n❌ [red]Error: {e}[/red]\n")
        sys.exit(1)


@app.command()
def status(submission_id: str):
    """
    Check the status of a submission.
    
    Example:
        quantgrid status my_submission_id
    """
    api_key = load_api_key()
    if not api_key:
        console.print("❌ [red]Not authenticated. Run 'quantgrid login' first.[/red]\n")
        sys.exit(1)
    
    try:
        response = requests.get(
            f"{HUB_URL}/status/{submission_id}",
            headers={"Authorization": api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"\n📊 Submission: [bold]{data['submission_id']}[/bold]")
            console.print(f"🟢 Status: {data['status']}")
            if data.get("score"):
                console.print(f"🎯 Score: {data['score']:.4f}")
            console.print(f"💬 Message: {data['message']}\n")
        else:
            console.print(f"❌ [red]Failed: {response.status_code}[/red]\n")
            
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]\n")


@app.command()
def leaderboard(limit: int = 20):
    """
    View the global contributor leaderboard.
    
    Example:
        quantgrid leaderboard --limit 50
    """
    try:
        response = requests.get(f"{HUB_URL}/leaderboard?limit={limit}")
        
        if response.status_code == 200:
            data = response.json()
            console.print("\n[bold cyan]🏆 QuantGrid Global Leaderboard[/bold cyan]\n")
            
            if data.get("leaderboard"):
                for i, entry in enumerate(data["leaderboard"], 1):
                    console.print(f"{i}. {entry['author']} - {entry['score']:.4f}")
            else:
                console.print("📊 [yellow]Leaderboard coming soon[/yellow]\n")
        else:
            console.print(f"❌ [red]Failed: {response.status_code}[/red]\n")
            
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]\n")


@app.command()
def version():
    """Show QuantGrid version"""
    console.print("\n[bold cyan]QuantGrid CLI v1.0.0[/bold cyan]")
    console.print("🌐 Federated Intelligence for Quantitative Finance\n")


if __name__ == "__main__":
    app()
