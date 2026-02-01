# AnchorGrid Agents Guide

The `anchorgrid.agents` package implements the multi-agent AI system. It uses specialized agents that coordinate to perform complex financial research and market analysis.

## Agent Architecture

### 1. The Orchestrator (`orchestrator.py`)
The central brain of the system.
- Receives user queries.
- Decomposes tasks into sub-problems.
- Routes tasks to specialized agents.
- Synthesizes the final response.

### 2. Market Analyst (`market_analyst.py`)
Specialist in technical and quantitative data.
- Interprets charts and indicators.
- Identifies support/resistance and trend patterns.

### 3. Research Agent (`research_agent.py`)
Specialist in fundamental data and news.
- Performs RAG (Retrieval Augmented Generation) on SEC filings.
- Summarizes news sentiment and economic releases.

### 4. Risk Manager (`risk_manager.py`)
Specialist in portfolio safety.
- Calculates position sizing based on volatility.
- Provides stop-loss and take-profit recommendations.

### 5. Context Manager (`context_manager.py`)
Handles multi-turn conversation memory and state tracking.

## Intelligent Routing

The `llm_router.py` utility handles model execution with automatic failover:
1. **Ollama**: Local execution (Mistral/Llama)
2. **OpenRouter**: Cloud-based open-source models
3. **Primary Cloud**: Anthropic/OpenAI

## Usage Example

```python
from anchorgrid.agents import Orchestrator

# Initialize the system
orchestrator = Orchestrator()

# Run a complex query
query = "Analyze AAPL earnings and suggest a risk-managed trade setup."
report = await orchestrator.run(query)

print(report.summary)
print(f"Risk Profile: {report.risk_score}")
```

---

## ZON Format Protocol
Agents communicate using the **ZON (Zero Overhead Notation)** format to minimize token usage and maximize speed. See `docs/ZON_FORMAT.md` for details.
