"""
AnchorGrid CLI - Discovery Commands

Commands for governed agent discovery
"""

import typer
from rich.console import Console
from rich import print
from rich.table import Table
from datetime import datetime, timedelta

app = typer.Typer()
console = Console()


@app.command()
def register(
    agent_id: str = typer.Option(..., help="Unique agent identifier"),
    capabilities: str = typer.Option(..., help="Comma-separated capabilities"),
    policy: str = typer.Option("finos-financial", help="Policy name"),
    anchor_cert: str = typer.Option(None, help="Path to Anchor certificate JSON"),
):
    """
    Register agent with Anchor verification
    
    Example:
        anchorgrid discovery register --agent-id FinanceBot --capabilities finance,analysis
    """
    from anchorgrid.core.discovery import discovery, RegistrationError
    
    # Parse capabilities
    cap_list = [c.strip() for c in capabilities.split(",")]
    
    # Mock Anchor certificate (in production, load from file)
    if not anchor_cert:
        # For demo: auto-generate valid cert
        mock_cert = {
            "score": 98,
            "hash": "0x7a3f9e2b1d8c...",
            "expires": (datetime.now() + timedelta(days=90)).isoformat()
        }
    else:
        # TODO: Load from file
        import json
        with open(anchor_cert) as f:
            mock_cert = json.load(f)
    
    console.print(f"\n🔍 Attempting to register: [bold]{agent_id}[/bold]")
    console.print(f"   Capabilities: {', '.join(cap_list)}")
    console.print(f"   Policy: {policy}\n")
    
    try:
        agent_info = discovery.register_agent(
            agent_id=agent_id,
            capabilities=cap_list,
            anchor_cert=mock_cert,
            policy=policy
        )
        
        console.print("✅ [bold green]Registration successful![/bold green]\n")
        console.print(f"   Agent ID: {agent_info.agent_id}")
        console.print(f"   Anchor Score: {agent_info.anchor_score}%")
        console.print(f"   Expires: {agent_info.expires_at.strftime('%Y-%m-%d')}\n")
        
    except RegistrationError as e:
        console.print(f"❌ [bold red]Registration failed:[/bold red] {str(e)}\n")


@app.command()
def discover_agents(
    capability: str = typer.Option(None, help="Required capability"),
    min_score: int = typer.Option(95, help="Minimum trust score"),
    policy: str = typer.Option(None, help="Required policy")
):
    """
    Discover agents by capability and trust score
    
    Example:
        anchorgrid discovery discover --capability finance --min-score 90
    """
    from anchorgrid.core.discovery import discovery
    
    console.print(f"\n🔍 Searching for agents...")
    if capability:
        console.print(f"   Capability: {capability}")
    console.print(f"   Minimum Score: {min_score}%")
    if policy:
        console.print(f"   Policy: {policy}\n")
    
    agents = discovery.discover(
        capability=capability,
        min_score=min_score,
        policy=policy
    )
    
    if not agents:
        console.print("❌ No agents found matching criteria.\n")
        return
    
    # Create table
    table = Table(title=f"🌐 Discovered Agents ({len(agents)})")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Capabilities", style="green")
    table.add_column("Score", justify="right")
    table.add_column("Policy")
    table.add_column("Status")
    
    for agent in agents:
        status = "🟢 Active" if not agent.is_expired() else "🔴 Expired"
        table.add_row(
            agent.agent_id,
            ", ".join(agent.capabilities),
            f"{agent.anchor_score}%",
            agent.policy,
            status
        )
    
    console.print(table)
    console.print()


@app.command()
def list_agents():
    """List all registered agents"""
    from anchorgrid.core.discovery import discovery
    
    agents = discovery.list_all()
    
    if not agents:
        console.print("\n❌ No agents registered.\n")
        return
    
    table = Table(title=f"📋 All Registered Agents ({len(agents)})")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Capabilities", style="green")
    table.add_column("Score", justify="right")
    table.add_column("Registered", style="dim")
    
    for agent in agents:
        table.add_row(
            agent.agent_id,
            ", ".join(agent.capabilities),
            f"{agent.anchor_score}%",
            agent.registered_at.strftime("%Y-%m-%d %H:%M")
        )
    
    console.print()
    console.print(table)
    console.print()


@app.command()
def cleanup():
    """Remove expired agents"""
    from anchorgrid.core.discovery import discovery
    
    console.print("\n🗑️  Running cleanup...")
    count = discovery.cleanup_expired()
    
    if count > 0:
        console.print(f"✅ Removed {count} expired agent(s)\n")
    else:
        console.print("✅ No expired agents found\n")


if __name__ == "__main__":
    app()
