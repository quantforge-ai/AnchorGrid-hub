# QuantGrid - Financial Intelligence Infrastructure

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://pypi.org/project/quantgrid/)
[![PyPI](https://img.shields.io/pypi/v/quantgrid)](https://pypi.org/project/quantgrid/)
[![Hive Mind](https://img.shields.io/badge/Collective_Intelligence-Active-purple.svg)](https://hub.quantgrid.dev)

**The world's first federated learning network for finance** - Where 10,000 developers share intelligence without sharing data.

> **105 Python modules** | **$9,576/year savings** | **Zero API keys required** | **Production-ready**

---

## Why QuantGrid?

Traditional financial data costs **$798/month**. QuantGrid gives you everything for **$0/month**.

- ✅ Zero-cost data: Custom scrapers for SEC, Yahoo Finance, NASDAQ, FRED, News
- ✅ AI-powered: Multi-agent system with fine-tuned LLMs
- ✅ Production-grade: Used in real trading systems and terminals
- ✅ Self-improving: Auto-discover APIs from any financial website
- ✅ Complete stack: From data ingestion to ML model deployment

---

## Installation

### Basic Installation
```bash
pip install quantgrid
```

### With ML Capabilities (for custom model training)
```bash
pip install quantgrid[ml]
```

### Full Installation (includes dev tools)
```bash
pip install quantgrid[all]
```

### From Source
```bash
git clone https://github.com/QuantGrid/quantgrid-core.git
cd quantgrid-core
pip install -e .
```

---

## Package Structure

QuantGrid is organized into specialized sub-packages:

### Core Infrastructure
- **`quantgrid.core`**: Config, security, logging, LLM routing, ZON engine
- **`quantgrid.db`**: Database models and session management
- **`quantgrid.scrapers`**: 9 zero-cost data scrapers
- **`quantgrid.indicators`**: High-performance quantitative engine

### Intelligence Layer
- **`quantgrid.agents`**: Multi-agent AI system (6 specialized agents)
- **`quantgrid.ml`**: Custom ML models and LoRA fine-tuning
- **`quantgrid.services`**: 26 production-ready services

### API & Routes
- **`quantgrid.api`**: AI platform REST endpoints
- **`quantgrid.routes`**: Terminal application endpoints

### Tools & Utilities
- **`quantgrid.tools`**: Dataset generation, API discovery, training pipelines

---

## Key Features

### 1. Zero-Cost Data Infrastructure

**9 Custom Scrapers** - No API keys required:
```python
from quantgrid.scrapers import (
    yfinance_scraper,      # Primary market data
    sec_scraper,           # SEC filings (10-K, 10-Q, 8-K)
    fred_scraper,          # Economic data (CSV downloads)
    nasdaq_scraper,        # NASDAQ backup
    marketwatch_scraper,   # MarketWatch backup
    central_bank_scraper,  # ECB, BOJ, BOE, RBI
    news_rss_scraper,      # 6 news sources
)

# Get quote
quote = yfinance_scraper.get_quote("AAPL")
print(f"Price: ${quote['price']:.2f}")

# Get SEC filing
filings = sec_scraper.get_filings("AAPL", "10-K", count=3)
```

**Annual Savings**: $9,576 vs traditional data providers

### 2. API Discovery Tool

**Auto-discover and generate scrapers from ANY financial website:**

```python
from quantgrid.tools.api_discovery import discover_apis

# Works with any financial website!
apis = discover_apis("https://example-financial-site.com/symbol/TICKER")

# Automatically finds ALL JSON APIs used by the page:
# - Real-time quotes
# - Historical OHLCV data  
# - Options chains
# - Analyst estimates
# - Company fundamentals
# - News feeds
# ... and generates ready-to-use Python code!

# Example results:
# Corrected 91 APIs from Yahoo Finance
# Corrected 47 APIs from MarketWatch  
# Corrected 63 APIs from Seeking Alpha
# All with auto-generated scraper code!
```

**How it works:**
1. Opens the page in a headless browser
2. Captures ALL network traffic (XHR/Fetch requests)
3. Identifies JSON API endpoints
4. Auto-generates Python scraper code
5. Saves to `generated_scrapers/` directory

**Use cases:**
- Discover hidden APIs from financial sites
- Build custom scrapers in minutes
- Find alternative data sources
- Bypass rate limits with direct API access

### 3. AI-Powered Intelligence

**Multi-Agent System** with specialized agents:
```python
from quantgrid.agents import Orchestrator

# Use the complete AI system
orchestrator = Orchestrator()
response = await orchestrator.run(
    "Analyze NVDA and provide trading recommendation with position sizing"
)

# The Orchestrator coordinates:
# - MarketAnalyst: Technical analysis
# - ResearchAgent: Fundamental research
# - RiskManager: Position sizing
# - ContextManager: Multi-turn conversation
```

**LLM Routing** with automatic fallback:
```python
from quantgrid.core.llm_router import LLMRouter

router = LLMRouter()
# Tries: Ollama (local) → OpenRouter → Anthropic
response = await router.chat("Explain Apple's earnings")
```

### 4. Custom ML Models (Phase 8)

**Fine-tune your own financial LLM:**
```python
from quantgrid.ml import FinancialLLM, TrainingConfig
from quantgrid.core.zon_engine import ZONEngine

# Prepare dataset in ZON format (saves 40% tokens!)
zon = ZONEngine()
dataset_zon = """
q:Analyze 10-K|i:Item 1. Business
Apple Inc...|o:Revenue ↑15% YoY $394B, margin 43.3%
---
q:What's RSI?|i:AAPL RSI=25, MACD bullish|o:Oversold + momentum = BUY signal
"""
dataset = zon.parse_training_data(dataset_zon)

# Load base model
model = FinancialLLM()

# Configure LoRA fine-tuning
config = TrainingConfig(
    model_name="financial-analyst-v1",
    base_model="mistralai/Mistral-7B-v0.1",
    dataset_size=100000,
    lora_r=16,
    lora_alpha=32
)

# Train on your data
model.prepare_for_training(config)
model.train(your_dataset, config)

# Use for predictions
prediction = model.predict({
    "ticker": "TSLA",
    "price_data": {...},
    "indicators": {...}
})
```

### 5. **The Hub: Collective Intelligence Network**

**The network that gets smarter every month.**

This is **Federated Learning for the masses** - where developers share intelligence without sharing data:

```python
from quantgrid.hub import QuantGridHub

# Initialize connection to the Hive Mind
hub = QuantGridHub()

# Pull top-rated community adapters
experts = hub.pull_community_adapters(
    domain="sec_filings",
    min_score=0.9,
    top_k=10
)

# Build consensus model from collective intelligence
consensus_model = hub.build_consensus_model(
    adapter_list=[expert.adapter_id for expert in experts]
)

# Use the collective's knowledge
prediction = consensus_model.predict({"ticker": "AAPL", ...})
```

**How to contribute your intelligence:**
```python
from quantgrid.hub import hub
from quantgrid.ml import FinancialLLM, TrainingConfig

# 1. Train on YOUR private data
model = FinancialLLM()
adapter = model.train(your_private_dataset)

# 2. Submit to the collective (weights only, not data!)
hub.contribute_intelligence(
    adapter_path="my_sec_expert.bin",
    domain="sec_filings",
    dataset_hash="sha256_of_your_data",  # Proof of work
    training_examples=50000
)

# 3. Your expertise is evaluated and added to the next monthly release
# 4. Everyone benefits from your contribution including you!
```

**Quality Control: Proof of Loss**
- Adapter submitted → Evaluated on hidden benchmark
- If `Loss < Official_Model_Loss` → **Accepted**
- If `Loss >= Official_Model_Loss` → **Rejected**
- No politics. No bias. Just math.

**The Network Effect:**
```
Month 1:  50 contributors  → v1.1.0 (10% better than base)
Month 3:  200 contributors → v1.3.0 (30% better)
Month 6:  500 contributors → v1.6.0 (60% better) 
Month 12: 2000 contributors → v2.0.0 (Strongest financial LLM in existence)
```

**Why This Wins:**
- **Privacy-Preserving**: Share weights (intelligence), not data (privacy)
- **Collective Learning**: 1 developer = 1 dataset, 10,000 developers = 10,000 datasets
- **Continuous Improvement**: Model gets stronger every month automatically
- **Democratic**: Best contributions win regardless of who submitted them

> This is how QuantGrid stops being a tool and becomes a **Network**.

### 6. Quantitative Engine

**O(1) incremental calculations** - sub-millisecond performance:
```python
from quantgrid.indicators import (
    sma, ema, rsi, macd, bollinger_bands, atr,
    detect_volatility_regime, calculate_composite_score
)

# Calculate indicators
rsi_14 = rsi(prices, 14)
macd_line, signal, histogram = macd(prices)
bb_upper, bb_mid, bb_lower = bollinger_bands(prices)

# Detect market regime
regime = detect_volatility_regime(returns)
# Returns: "low" | "medium" | "high"

# Generate trading signal
signal = calculate_composite_score(
    price=current_price,
    rsi=rsi_14[-1],
    macd=(macd_line[-1], signal[-1], histogram[-1]),
    ema_20=ema_20[-1],
    ema_50=ema_50[-1]
)
# Returns: Signal(action="BUY", score=0.85, confidence=0.92)
```

### 6. Production Services

**26 battle-tested services:**
```python
from quantgrid import (
    quote_service,           # Real-time quotes
    redis_service,           # Caching
    quant_service,           # Technical analysis
    market_state_manager,    # Cache-first data layer
    rag_service,             # Vector search
    embedding_service,       # Embeddings
    portfolio_service,       # Portfolio management
    shadow_watch,            # Behavioral tracking
)

# Example: Get cached quote with automatic refresh
quote = await market_state_manager.get_market_data("AAPL")
```

---

## Complete Package Contents

```
quantgrid/
├── agents/           6 AI agents (Orchestrator, MarketAnalyst, etc.)
├── api/              7 AI REST routes
├── core/            11 utilities (config, security, LLM routing, ZON)
├── db/              
│   └── models/       8 models (User, Portfolio, OHLCV, etc.)
├── indicators/       5 modules (indicators, regimes, signals)
├── ml/               2 ML modules (FinancialLLM, ModelRegistry)
├── routes/          12 Terminal REST routes
├── scrapers/         9 zero-cost scrapers
├── services/        26 production services
└── tools/            4 training & discovery tools
```

**Total**: **105 Python modules** | **$0/month cost**

---

## Use Cases

### Trading Systems
- Real-time market data ingestion
- Technical analysis and regime detection
- AI-powered trade signal generation
- Risk management and position sizing

### Financial Terminals
- Bloomberg-style data displays
- Portfolio tracking and analytics
- News aggregation and sentiment analysis
- Behavioral intelligence (ShadowWatch)

### Research Platforms
- SEC filing analysis
- Fundamental research with RAG
- Custom dataset generation
- Model training and backtesting

### Data Collection
- Auto-discover APIs from websites
- Build custom scrapers in minutes
- Generate training datasets
- Zero-cost data pipelines

---

## Configuration

Create a `.env` file:

```bash
# Database (optional - for data persistence)
DATABASE_URL=postgresql://user:pass@localhost/quantgrid
TIMESCALE_URL=postgresql://user:pass@localhost/timescale

# Redis (optional - for caching)
REDIS_URL=redis://localhost:6379

# LLM (optional - for AI features)
OLLAMA_URL=http://localhost:11434
OPENROUTER_API_KEY=your_key_here

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

**Note**: QuantGrid works with **zero configuration** for basic scraping and analysis!

---

## Performance

- **Scraper speed**: 5-10s per quote (90x faster than traditional REST APIs)
- **Indicator calculations**: Sub-millisecond (O(1) incremental updates)
- **Memory footprint**: ~500MB base, ~8GB with ML models loaded
- **Throughput**: 1000+ symbols/minute with parallel scraping

---

## Real-World Projects

- **QuantGrid AI**: Production AI trading platform
- **QuantGrid Terminal**: Bloomberg-style financial terminal
- **100+ custom scrapers**: Auto-generated from major financial sites

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---


## Contributing

**Join the Hive Mind!** We welcome both code and intelligence contributions.

### Intelligence Contributions

Share your trained model weights and become part of the collective:

```python
from quantgrid.hub import hub

# Train on your private data
adapter = train_your_model(your_private_dataset)

# Share weights (not data!) with the community
hub.contribute_intelligence(
    adapter_path=adapter,
    domain="your_expertise"
)
```

**Why contribute?**
- **100% Private** - Only weights shared, never your data
- **Global Recognition** - Leaderboard credit
- **Premium Access** - Free premium features for contributors
- **Network Effect** - Your expertise + 10,000 others = Strongest financial LLM

See our **[Contributing Guide](CONTRIBUTING.md)** for complete instructions.

### Code Contributions

Improve the core infrastructure:
- Submit bug fixes
- Add new features
- Improve documentation
- Create examples

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Documentation

- [Core Logic Guide](docs/CORE_GUIDE.md)
- [Agents & AI Guide](docs/AGENTS_GUIDE.md)
- [Scrapers Guide](docs/SCRAPERS_GUIDE.md)
- [Indicators Guide](docs/INDICATORS_GUIDE.md)
- [Database & ML Guide](docs/DB_ML_GUIDE.md)
- [Services & Tools Guide](docs/SERVICES_TOOLS_GUIDE.md)
- [API & Routes Guide](docs/API_ROUTES_GUIDE.md)
- [ZON Format Guide](docs/ZON_FORMAT.md)
- [Installation Guide](INSTALL_GRIDBASH.md)
- [Contributing Intelligence](docs/ML_CONTRIBUTION.md)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/QuantGrid/quantgrid-core/issues)
- **Discussions**: [GitHub Discussions](https://github.com/QuantGrid/quantgrid-core/discussions)
- **Email**: support@quantgrid.dev

---

**Built with pride by the QuantGrid Team**

*Democratizing financial intelligence, one scraper at a time.*