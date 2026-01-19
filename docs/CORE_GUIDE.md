# QuantGrid Core Logic Guide

The `quantgrid.core` package contains the foundational utilities and infrastructure that power the entire ecosystem. It handles configuration, security, data serialization, and communication protocols.

## Key Modules

### 1. ZON Engine (`zon_engine.py`)
Implements the Zero Overhead Notation format.
- Token-efficient serialization for LLMs.
- Dataset parsing and generation.
- JSON-to-ZON conversion.

### 2. LLM Router (`llm_router.py`)
Universal interface for AI models.
- Support for Ollama, OpenRouter, and direct cloud APIs.
- Automatic retry and fallback logic.
- Cost-aware routing.

### 3. Smart Guardian Firewall (`firewall.py`)
Security layer for repository protection.
- Rules-based file inspection.
- Quarantine logic for sensitive data.
- Push safety validation.

### 4. Manifest System (`manifest.py`)
Standardized metadata for AI models.
- Domain-agnostic model tagging (Finance, Legal, etc.).
- Version tracking and quality scores.

### 5. Configuration & Logging (`config.py`, `logging.py`)
- Pydantic-based settings management.
- Structured JSON logging.
- Environment variable injection.

## Usage Example

```python
from quantgrid.core.llm_router import LLMRouter
from quantgrid.core.zon_engine import ZONEngine

# Route a prompt
router = LLMRouter()
response = await router.chat("Explain technical analysis.")

# Encode data for fine-tuning
zon = ZONEngine()
dataset = zon.parse_training_data("q:Hello|o:Hi")
```

---

## Security
The core includes the `security.py` module which manages JWT tokens, password hashing, and API key validation for the Hub and local API services.
