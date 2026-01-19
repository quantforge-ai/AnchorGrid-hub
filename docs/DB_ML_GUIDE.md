# QuantGrid Database & ML Guide

The `quantgrid.db` and `quantgrid.ml` packages manage the persistence layer and the neural training infrastructure.

## Database Infrastructure (`quantgrid.db`)

QuantGrid uses a dual-database approach:
- **PostgreSQL/TimescaleDB**: For structured user data and high-frequency market history.
- **Weaviate**: For vector embeddings and semantic search.

### Key Models
- `User`: Identity and authentication.
- `Portfolio`: Asset holdings and tracking.
- `OHLCV`: Time-series market data.
- `Manifest`: Registry entries for community models.

### Vector Search
The `rag_service.py` (in services) interacts with the DB layer to perform semantic retrieval from SEC filings and news archives.

## Machine Learning Engine (`quantgrid.ml`)

The ML layer is focused on LoRA (Low-Rank Adaptation) fine-tuning for financial LLMs.

### 1. Financial LLM (`models.py`)
Base architectures and adapter loading logic.
- Optimized for Mistral-7B and Llama-3.
- Integrated Peft/LoRA support.

### 2. Standardized Trainer (`trainer.py`)
A wrapper for fine-tuning with enforced community standards.
- Consistent Rank/Alpha settings.
- Memory-efficient 4-bit training.

### 3. Model Registry
Management of local model weights and Hive Mind versioning.

## Usage Example

```python
from quantgrid.ml.trainer import QuantGridTrainer
from quantgrid.db import SessionLocal

# Run a training job
trainer = QuantGridTrainer()
trainer.train(dataset="my_research.zon", output_dir="./expert_model")

# Query the DB
with SessionLocal() as session:
    user = session.query(User).first()
```

---

## Performance
The database layer uses indexed OHLCV tables for fast historical lookup, while the ML layer utilizes bitsandbytes for 4-bit quantization, allowing 7B parameter models to be fine-tuned on consumer GPUs.
