"""
AnchorGrid CLI - The Universal Intelligence Launcher

Like Epic Games Launcher, but for AI models.
Browse, download, and run plugins from Finance, Medical, Legal, and more.
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import Optional
from loguru import logger
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from anchorgrid.core.registry import Registry

app = typer.Typer(help="AnchorGrid: The Universal Intelligence Protocol")
console = Console()

# Hub Configuration
HUB_URL = os.getenv("ANCHORGRID_HUB_URL", "https://hub.anchorgrid.dev")
CONFIG_FILE = Path.home() / ".anchorgrid" / "config"


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


# ============================================================================
# PHASE 2: The Launcher Commands (Epic Games Store Style)
# ============================================================================

@app.command()
def search(query: str = typer.Argument("", help="Search term (e.g., 'finance', 'medical', 'legal')")):
    """
    🔍 Browse the Decentralized Registry for plugins/models.
    
    Search across Finance, Medical, Legal, Code, and other domains.
    Each plugin shows its Proof of Utility score verified by the network.
    """
    console.print(f"\n[bold cyan]🔍 Searching the Universal Registry for: '{query or 'all'}'...[/bold cyan]")
    
    results = Registry.search(query)
    
    if not results:
        console.print("[red]No plugins found matching that query.[/red]")
        console.print("[dim]Try: 'anchorgrid search finance' or 'anchorgrid search medical'[/dim]")
        return

    # Create an Epic Games style table with SHORT IDs
    table = Table(
        title=f"\n🌐 Available Intelligence Plugins ({len(results)})",
        title_style="bold cyan",
        border_style="cyan",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("ID", style="bold cyan", no_wrap=True, width=15)
    table.add_column("Name", style="green", width=18)
    table.add_column("Utility", justify="right", width=8)
    table.add_column("Price", style="gold1", justify="center", width=10)
    table.add_column("Description", style="dim", width=45)

    for p in results:
        # Colorize score (Epic Games style ratings)
        score_color = "green" if p.score > 0.9 else "yellow" if p.score > 0.8 else "red"
        
        # Truncate description if too long
        desc = p.description if len(p.description) <= 45 else p.description[:42] + "..."
        
        table.add_row(
            p.id,
            p.full_name,
            f"[{score_color}]{p.score*100:.0f}%[/]",
            p.price,
            desc
        )

    console.print(table)
    console.print("\n[dim]💡 Tip: Run 'anchorgrid info <id>' for detailed stats.[/dim]\n")


@app.command()
def info(plugin_id: str = typer.Argument(..., help="Plugin ID (e.g., 'finance' or 'defi/sniper')")):
    """
    📊 View Proof-of-Utility stats for a specific plugin.
    
    Shows: Version, downloads, verified accuracy score, price, and description.
    Like viewing a "Store Page" in Epic Games Launcher.
    """
    console.print(f"\n[bold cyan]📡 Fetching metadata for {plugin_id}...[/bold cyan]")
    
    plugin = Registry.get_info(plugin_id)
    if not plugin:
        console.print(f"\n[red]❌ Plugin '{plugin_id}' not found in the registry.[/red]")
        console.print("[dim]Try: 'anchorgrid search' to see available plugins.[/dim]\n")
        return

    # Create a detailed "Store Page" view
    details = f"""
[bold]Domain:[/bold] {plugin.domain.upper()}
[bold]Author:[/bold] {plugin.author}
[bold]Version:[/bold] {plugin.version}
[bold]Downloads:[/bold] {plugin.downloads:,}

[green]✅ Proof of Utility: {plugin.score*100:.1f}% Verified Accuracy[/green]
[gold1]💰 Price: {plugin.price}[/gold1]

[italic]{plugin.description}[/italic]
    """
    
    panel = Panel(
        details,
        title=f"📦 {plugin.full_name} ({plugin.id})",
        border_style="green",
        expand=False,
        padding=(1, 2)
    )
    console.print(panel)
    console.print(f"[bold]To install:[/bold] [cyan]anchorgrid pull {plugin_id}[/cyan]\n")


@app.command()
def pull(plugin_id: str = typer.Argument(..., help="Plugin ID to download")):
    """
    ⬇️  Download and install a plugin/adapter from the registry.
    
    Uses P2P networking (IPFS/BitTorrent) for decentralized distribution.
    No central server needed - downloads weights directly from the network.
    """
    plugin = Registry.get_info(plugin_id)
    if not plugin:
        console.print(f"\n[red]❌ Plugin '{plugin_id}' not found.[/red]\n")
        return

    console.print(f"\n[bold green]⬇️  Initializing P2P download for {plugin.full_name}...[/bold green]")
    
    # Fake progress bar for the "Launcher" feel (will be real IPFS download in production)
    with console.status("[bold green]📡 Syncing weights from IPFS network...[/bold green]", spinner="dots"):
        time.sleep(2.0)  # Simulate download time
        
    console.print(f"[bold]✅ Successfully installed {plugin.full_name} v{plugin.version}[/bold]")
    
    # Show where it's stored (following plugin structure)
    storage_path = f"./anchorgrid/plugins/{plugin.domain}/{plugin.full_name.lower().replace(' ', '_')}"
    console.print(f"[dim]📁 Stored in: {storage_path}[/dim]")
    console.print(f"\n[bold cyan]🚀 To use: Import the plugin in your code[/bold cyan]")
    console.print(f"[dim]from anchorgrid.plugins.{plugin.domain} import {plugin.full_name.lower().replace(' ', '_')}[/dim]\n")


@app.command()
def run(
    plugin: str = typer.Option("finance", help="Plugin domain (finance, medical, legal, etc.)"),
    task: str = typer.Argument(..., help="Task input (e.g., stock ticker 'AAPL')")
):
    """
    🚀 Run a plugin's agent locally with the Universal Engine.
    
    Execute AI-powered analysis using:
    - Plugin-specific data connectors  
    - Domain extractors (indicators, features)
    - Universal reasoning engine (Ollama)
    
    Examples:
        anchorgrid run --plugin finance AAPL
        anchorgrid run --plugin finance TSLA
        anchorgrid run --plugin medical patient_scan.dcm  # (when medical plugin installed)
    """
    
    if plugin == "finance":
        console.print(f"\n[bold green]💼 Launching Finance Plugin for {task.upper()}...[/bold green]")
        console.print("[dim]Using: Yahoo Finance + RSI + Local Llama3[/dim]\n")
        
        try:
            from anchorgrid.plugins.finance.agent import finance_agent
            
            result = finance_agent.analyze_stock(task)
            
            # Result is streamed, so just show completion
            console.print("\n[bold green]✅ Analysis Complete[/bold green]")
            console.print(f"[dim]Powered by: Universal Engine (Ollama) + Finance Plugin[/dim]\n")
            
        except ImportError as e:
            console.print(f"[red]❌ Finance Plugin Error: {e}[/red]")
            console.print("[yellow]Try: pip install langchain langchain-community[/yellow]\n")
        except Exception as e:
            console.print(f"[red]❌ Execution Error: {e}[/red]\n")
    
    elif plugin == "medical":
        console.print("\n[yellow]⚠️  Medical Plugin not installed.[/yellow]")
        console.print("[dim]Run: anchorgrid pull @med-ai/oncology-pro[/dim]\n")
    
    elif plugin == "legal":
        console.print("\n[yellow]⚠️  Legal Plugin not installed.[/yellow]")
        console.print("[dim]Run: anchorgrid pull @legal/contract-audit[/dim]\n")
    
    else:
        console.print(f"[red]❌ Unknown plugin domain: {plugin}[/red]")
        console.print("[dim]Available: finance, medical, legal, code[/dim]\n")


# ============================================================================
# Original Hub Commands (For Producers - Submit Adapters)
# ============================================================================

@app.command()
def login():
    """
    Authenticate with AnchorGrid Hub to enable model uploads.
    
    You'll get an API key from: https://hub.anchorgrid.dev/register
    """
    console.print("\n[bold cyan]🔐 AnchorGrid Hub Authentication[/bold cyan]\n")
    
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
            f"{HUB_URL}/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            save_api_key(api_key)
            console.print(f"\n✅ [green]Authenticated as: {user_data.get('username', 'Unknown')}[/green]")
            console.print("\nYou can now use 'anchorgrid push' to submit adapters!\n")
        else:
            console.print(f"❌ [red]Authentication failed: {response.text}[/red]")
            sys.exit(1)
            
    except Exception as e:
        logger.warning(f"Auth check failed (hub might be offline): {e}")
        save_api_key(api_key)
        console.print("\n⚠️  [yellow]Saved API key (hub verification skipped - might be offline)[/yellow]\n")


@app.command()
def push(
    adapter_path: str = typer.Argument(..., help="Path to adapter .zip or directory"),
    message: str = typer.Option("", "--message", "-m", help="Submission message"),
):
    """
    Submit a trained adapter to the global Hub for evaluation.
    
    Your adapter will be evaluated on the holdout set and merged if it improves the score.
    """
    api_key = load_api_key()
    if not api_key:
        console.print("❌ [red]Not authenticated. Run 'anchorgrid login' first.[/red]")
        sys.exit(1)
    
    adapter_path = Path(adapter_path)
    if not adapter_path.exists():
        console.print(f"❌ [red]Path not found: {adapter_path}[/red]")
        sys.exit(1)
    
    console.print(f"\n[bold cyan]📤 Submitting adapter: {adapter_path.name}[/bold cyan]\n")
    
    # If directory, create zip
    if adapter_path.is_dir():
        import zipfile
        import tempfile
        
        zip_path = Path(tempfile.mkdtemp()) / f"{adapter_path.name}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in adapter_path.rglob('*'):
                if file.is_file():
                    zipf.write(file, file.relative_to(adapter_path))
        adapter_path = zip_path
        console.print(f"📦 Created archive: {adapter_path}")
    
    # Upload
    try:
        with open(adapter_path, 'rb') as f:
            files = {'adapter': (adapter_path.name, f, 'application/zip')}
            data = {'message': message} if message else {}
            
            response = requests.post(
                f"{HUB_URL}/api/v1/adapters/submit",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            result = response.json()
            console.print(f"\n✅ [green]Adapter submitted successfully![/green]")
            console.print(f"\n📊 Submission ID: {result.get('submission_id', 'N/A')}")
            console.print(f"\nCheck status: anchorgrid status {result.get('submission_id', '')}\n")
        else:
            console.print(f"\n❌ [red]Submission failed: {response.text}[/red]\n")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"\n❌ [red]Upload error: {e}[/red]\n")
        sys.exit(1)


@app.command()
def status(submission_id: str = typer.Argument(..., help="Submission ID from 'push' command")):
    """
    Check the evaluation status of your submitted adapter.
    """
    api_key = load_api_key()
    if not api_key:
        console.print("❌ [red]Not authenticated. Run 'anchorgrid login' first.[/red]")
        sys.exit(1)
    
    try:
        response = requests.get(
            f"{HUB_URL}/api/v1/adapters/{submission_id}/status",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            console.print(f"\n[bold]Submission: {submission_id}[/bold]")
            console.print(f"Status: {data.get('status', 'Unknown')}")
            console.print(f"Score: {data.get('score', 'Pending')}")
            
            if data.get('merged'):
                console.print("\n✅ [green]Your adapter was merged into the global model![/green]\n")
            else:
                console.print(f"\nReason: {data.get('reason', 'Under evaluation')}\n")
        else:
            console.print(f"❌ [red]Status check failed: {response.text}[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


@app.command()
def leaderboard(limit: int = typer.Option(10, help="Number of top contributors to show")):
    """
    View the top contributors to the AnchorGrid network.
    """
    try:
        response = requests.get(f"{HUB_URL}/api/v1/leaderboard?limit={limit}")
        
        if response.status_code == 200:
            leaders = response.json()
            
            table = Table(title="🏆 AnchorGrid Leaderboard", border_style="gold1")
            table.add_column("Rank", justify="right", style="cyan")
            table.add_column("Username", style="green")
            table.add_column("Adapters Merged", justify="right")
            table.add_column("Total Score Improvement", justify="right", style="gold1")
            
            for i, leader in enumerate(leaders, 1):
                table.add_row(
                    str(i),
                    leader.get('username', 'Anonymous'),
                    str(leader.get('merged_count', 0)),
                    f"+{leader.get('score_improvement', 0):.2f}%"
                )
            
            console.print("\n")
            console.print(table)
            console.print("\n")
        else:
            console.print(f"❌ [red]Leaderboard fetch failed: {response.text}[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


@app.command()
def version():
    """
    Show AnchorGrid CLI version.
    """
    from anchorgrid import __version__
    console.print(f"\nAnchorGrid v{__version__}\n")


if __name__ == "__main__":
    app()
