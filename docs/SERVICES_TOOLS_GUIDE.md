# AnchorGrid Services & Tools Guide

The `anchorgrid.services` and `anchorgrid.tools` packages provide high-level abstractions and developer utilities for building production-grade financial applications.

## Production Services (`anchorgrid.services`)

These services encapsulate complex logic into simple, reusable components:

### 1. Market State Manager (`market_state_manager.py`)
The most critical service. It manages data tiers:
- **HOT**: Real-time Redis cache.
- **WARM**: Recent history in TimescaleDB.
- **COLD**: Archive file storage.

### 2. RAG Service (`rag_service.py`)
Retrieval Augmented Generation for document intelligence.

### 3. Quote Service (`quote_service.py`)
Unified interface for all underlying scrapers.

### 4. Shadow Watch (`shadow_watch.py`)
Behavioral tracking and trust-score calculation.

## Developer Tools (`anchorgrid.tools`)

### 1. API Discovery (`api_discovery.py`)
Auto-generates scrapers from any website by sniffing JSON traffic.

### 2. Training Pipeline (`training_pipeline.py`)
End-to-end workflow for generating fine-tuning datasets from raw web data.

### 3. Data Quality (`data_quality.py`)
Deduplication and filtering logic for cleaning massive financial datasets.

## Usage Example

```python
from anchorgrid.services import market_state_manager
from anchorgrid.tools.api_discovery import discover_apis

# Get real-time data through the management layer
data = await market_state_manager.get_market_data("AAPL")

# Discover new data sources
apis = discover_apis("https://new-fin-site.com/price/AAPL")
```

---

## Tooling Standards
All tools in the `anchorgrid.tools` package are designed to be run as standalone scripts or integrated into larger pipelines via the `grid run` command in the CLI.
