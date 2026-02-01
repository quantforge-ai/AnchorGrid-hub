# AnchorGrid Core Module

**The foundation of the governed agentic network.**

## Components

### 1. Universal Engine (`engine.py`)

Domain-agnostic AI reasoning wrapper around Ollama/LangChain.

**Purpose:** One brain that can reason across any domain (Finance, Medical, Legal).

```python
from anchorgrid.core.engine import engine

# Finance reasoning
response = engine.think(
    prompt="Analyze this stock",
    context="AAPL: $259.48, RSI: 42.3",
    domain="finance"
)

# Medical reasoning (same engine!)
response = engine.think(
    prompt="Analyze this scan",
    context="Tumor: 12mm, irregular shape",
    domain="medical"
)
```

**Key features:**
- ✅ Streaming output (token-by-token)
- ✅ 100% local (Ollama-based)
- ✅ Graceful degradation (works without LangChain)
- ✅ Domain-agnostic (universal intelligence)

---

### 2. Discovery Protocol (`discovery.py`)

**Proof-of-Integrity Discovery (PoID)** - The Bouncer for agent networks.

**The Problem:** Traditional networks let anyone join.  
**Our Solution:** Require cryptographic proof of Anchor compliance.

```python
from anchorgrid.core.discovery import discovery, RegistrationError

# Register agent with Anchor proof
try:
    agent = discovery.register_agent(
        agent_id="FinanceBot",
        capabilities=["finance", "analysis"],
        anchor_cert={
            "score": 98,
            "hash": "0x7a3f9e...",
            "expires": "2026-05-01T00:00:00"
        },
        policy="finos-financial"
    )
    print(f"✅ Registered: {agent.agent_id}")
except RegistrationError as e:
    print(f"❌ Rejected: {e}")

# Discover agents
finance_agents = discovery.discover(
    capability="finance",
    min_score=95
)
```

**Verification checks:**
1. Certificate format validation
2. Trust score minimum (default: 95%)
3. Expiration date check
4. Cryptographic signature (coming in Phase 4.2)

---

### 3. Registry (`registry.py`)

Multi-domain plugin registry with short IDs.

```python
from anchorgrid.core.registry import registry

# Get plugin metadata
plugin = registry.get_plugin("finance")
print(f"{plugin.full_name}: {plugin.description}")

# List all plugins
all_plugins = registry.list_plugins()
```

**Features:**
- ✅ Short IDs ("finance" vs "@anchorgrid/finance-core")
- ✅ Multi-domain support
- ✅ Proof-of-utility scores
- ✅ Community-contributed plugins

---

### 4. Security (`security.py`)

Anchor integration for cryptographic verification.

**Coming in Phase 4.2:**
- Certificate generation
- Signature verification
- Policy compliance checks
- Trust score calculation

---

## Architecture Diagram

```
┌──────────────────────────────────────┐
│         Discovery Protocol           │
│   (Agents find each other)           │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│      Verification Layer              │
│   (Anchor checks compliance)         │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│         Trust Registry               │
│   (Database of verified agents)      │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│       Universal Engine               │
│   (Domain-agnostic reasoning)        │
└──────────────────────────────────────┘
```

---

## Usage Examples

### Example 1: Register and Discover

```bash
# Terminal 1: Register FinanceBot
python -m anchorgrid.cli_discovery register \
  --agent-id FinanceBot \
  --capabilities "finance,analysis"

# Terminal 2: Discover finance agents
python -m anchorgrid.cli_discovery discover-agents \
  --capability finance
```

### Example 2: Build a Custom Agent

```python
from anchorgrid.core.engine import engine
from anchorgrid.core.discovery import discovery

class MyCustomAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        
        # Register with network
        discovery.register_agent(
            agent_id=agent_id,
            capabilities=["custom"],
            anchor_cert=self.get_anchor_cert(),
            policy="custom-policy"
        )
    
    def reason(self, prompt, context):
        """Use universal engine for reasoning"""
        return engine.think(
            prompt=prompt,
            context=context,
            domain="custom"
        )
```

---

## Development

### Running Tests

```bash
# Test discovery protocol
python -c "from anchorgrid.core.discovery import discovery; print('✅ OK')"

# Test engine
python -c "from anchorgrid.core.engine import engine; print('✅ OK')"

# Run demo
python demo_discovery.py
```

### Adding a New Verification Check

```python
# In discovery.py

class VerificationLayer:
    def verify_agent(self, agent_id, anchor_cert, policy):
        # Add your custom check here
        if not self._check_custom_rule(anchor_cert):
            return False, {"error": "Custom rule failed"}
        
        return True, {"score": anchor_cert["score"]}
```

---

## Phase Roadmap

- ✅ **Phase 1-3:** Universal engine, plugins, short IDs
- ✅ **Phase 4.1:** Basic discovery protocol (DONE)
- 🔄 **Phase 4.2:** Anchor signature verification (In Progress)
- 🔄 **Phase 4.3:** Trust registry persistence
- 🔄 **Phase 5:** Multi-domain expansion

---

**The Core module is the foundation. Everything else builds on top.** 🏗️
