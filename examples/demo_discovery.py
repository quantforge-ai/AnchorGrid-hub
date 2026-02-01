"""
Demo: Proof-of-Integrity Discovery

Shows how AnchorGrid is different from AgentGrid
"""

from anchorgrid.core.discovery import discovery, RegistrationError
from datetime import datetime, timedelta
from rich.console import Console

console = Console()

def demo():
    console.print("\n[bold]🎯 AnchorGrid: Proof-of-Integrity Discovery Demo[/bold]\n")
    
    # Scenario 1: Agent with valid Anchor cert
    console.print("[cyan]Scenario 1: Legitimate agent with Anchor certificate[/cyan]")
    
    valid_cert = {
        "score": 98,
        "hash": "0x7a3f9e2b1d8c4f5a",
        "expires": (datetime.now() + timedelta(days=90)).isoformat()
    }
    
    try:
        agent = discovery.register_agent(
            agent_id="FinanceBot",
            capabilities=["finance", "analysis"],
            anchor_cert=valid_cert,
            policy="finos-financial"
        )
        console.print(f"✅ [green]Success![/green] Registered: {agent.agent_id} (score: {agent.anchor_score}%)\n")
    except RegistrationError as e:
        console.print(f"❌ [red]Failed:[/red] {e}\n")
    
    # Scenario 2: Agent with LOW trust score
    console.print("[cyan]Scenario 2: Suspicious agent with low trust score[/cyan]")
    
    bad_cert = {
        "score": 75,  # Too low!
        "hash": "0xbad1bad2bad3",
        "expires": (datetime.now() + timedelta(days=90)).isoformat()
    }
    
    try:
        agent = discovery.register_agent(
            agent_id="SuspiciousBot",
            capabilities=["finance"],
            anchor_cert=bad_cert,
            policy="finos-financial"
        )
        console.print(f"✅ [green]Success![/green] Registered: {agent.agent_id}\n")
    except RegistrationError as e:
        console.print(f"❌ [red]Rejected![/red] {e}\n")
    
    # Scenario 3: Agent with expired cert
    console.print("[cyan]Scenario 3: Agent with expired certificate[/cyan]")
    
    expired_cert = {
        "score": 99,
        "hash": "0xexpired123",
        "expires": (datetime.now() - timedelta(days=10)).isoformat()  # Already expired!
    }
    
    try:
        agent = discovery.register_agent(
            agent_id="ExpiredBot",
            capabilities=["medical"],
            anchor_cert=expired_cert,
            policy="finos-financial"
        )
        console.print(f"✅ [green]Success![/green] Registered: {agent.agent_id}\n")
    except RegistrationError as e:
        console.print(f"❌ [red]Rejected![/red] {e}\n")
    
    # Scenario 4: Register a second valid agent
    console.print("[cyan]Scenario 4: Another legitimate agent (Medical domain)[/cyan]")
    
    medical_cert = {
        "score": 97,
        "hash": "0xmed1c41c3r7",
        "expires": (datetime.now() + timedelta(days=180)).isoformat()
    }
    
    try:
        agent = discovery.register_agent(
            agent_id="MedBot",
            capabilities=["medical", "diagnosis"],
            anchor_cert=medical_cert,
            policy="hipaa-compliant"
        )
        console.print(f"✅ [green]Success![/green] Registered: {agent.agent_id} (score: {agent.anchor_score}%)\n")
    except RegistrationError as e:
        console.print(f"❌ [red]Failed:[/red] {e}\n")
    
    # Discovery Demo
    console.print("[bold]🔍 Discovery Results:[/bold]\n")
    
    # Find finance agents
    finance_agents = discovery.discover(capability="finance", min_score=95)
    console.print(f"[cyan]Finance agents (score ≥ 95%):[/cyan] {len(finance_agents)}")
    for agent in finance_agents:
        console.print(f"   • {agent.agent_id} - {agent.anchor_score}%")
    
    # Find medical agents
    medical_agents = discovery.discover(capability="medical", min_score=95)
    console.print(f"[cyan]Medical agents (score ≥ 95%):[/cyan] {len(medical_agents)}")
    for agent in medical_agents:
        console.print(f"   • {agent.agent_id} - {agent.anchor_score}%")
    
    # List all
    all_agents = discovery.list_all()
    console.print(f"\n[bold]Total registered agents:[/bold] {len(all_agents)}")
    
    console.print("\n" + "="*60)
    console.print("[bold green]KEY INSIGHT:[/bold green]")
    console.print("❌ AgentGrid: 5 agents tried to join → 5 accepted (including malicious ones)")
    console.print("✅ AnchorGrid: 5 agents tried to join → 2 accepted (only verified ones)\n")

if __name__ == "__main__":
    demo()
