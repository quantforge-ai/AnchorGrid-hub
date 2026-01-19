# Contributing to QuantGrid

**Welcome to the Hive Mind!**

QuantGrid is the world's first federated learning network for finance. We're building collective intelligence through community contributions.

There are **two ways to contribute**:

1. **Code Contributions** - Improve the core infrastructure
2. **Intelligence Contributions** - Share your trained model weights (THE BIG ONE)

---

## Intelligence Contributions (Model Weights)

**This is what makes QuantGrid revolutionary.**

### Why Share Your Weights?

**The power of collective learning.**

When you share your trained LoRA adapter:
- You keep your data **100% private** (only weights are shared)
- Your expertise becomes part of the collective intelligence
- You gain access to everyone else's expertise
- You get credited on the global leaderboard
- The entire community benefits (including you!)

### What You Can Train On

Any financial domain expertise:
- **SEC Filings Analysis** (10-K, 10-Q, 8-K interpretation)
- **Earnings Call Summarization** (extracting key insights)
- **Technical Analysis** (chart pattern recognition)
- **News Sentiment** (financial news understanding)
- **Options Strategy** (complex derivatives)
- **Risk Assessment** (portfolio risk analysis)
- **Macro Economics** (FRED data interpretation)
- **And anything else related to finance!**

---

## Quick Start: Contribute Your First Adapter

### Step 1: Train Your Model

```python
from quantgrid.ml import FinancialLLM, TrainingConfig
from quantgrid.tools import TrainingPipeline
from quantgrid.core.zon_engine import ZONEngine

# Initialize ZON engine for efficient data encoding
zon = ZONEngine()

# 1. Prepare your private dataset in ZON format
# ZON is QuantGrid's token-efficient format - saves ~40% tokens vs JSON!
your_dataset_zon = """
q:Analyze this 10-K|i:Item 1. Business
Apple Inc. designs, manufactures...|o:Revenue up 15% YoY $394B, margin 43.3%, cash $166B. iPhone up 9%, Services up 14%. Bullish.
---
q:What's the RSI telling us?|i:AAPL RSI=25, MACD bullish crossover|o:Oversold + momentum = BUY signal. Entry $258, target $280.
---
q:Summarize earnings call|i:Q4 2023: Beat EPS $1.52 vs $1.39 est...|o:Beat on revenue & EPS. Services strong. iPhone demand solid. Guidance raised.
"""

# Convert ZON to training format
your_dataset = zon.parse_training_data(your_dataset_zon)

# 2. Configure training
config = TrainingConfig(
    model_name="my-sec-expert-v1",
    base_model="mistralai/Mistral-7B-v0.1",
    dataset_size=len(your_dataset),
    epochs=3,
    lora_r=16,        # Standardized
    lora_alpha=32,    # Standardized
)

# 3. Train the adapter
model = FinancialLLM()
model.prepare_for_training(config)
adapter_path = model.train(your_dataset, config)

print(f"Adapter trained: {adapter_path}")
```

### Step 2: Evaluate Locally

Before submitting, test your adapter:

```python
from quantgrid.hub import ProofOfLoss

# Evaluate on local benchmark
evaluator = ProofOfLoss()
metrics = evaluator.evaluate_adapter(
    model=model,
    tokenizer=model.tokenizer,
    num_examples=100
)

print(f"Loss: {metrics['loss']:.4f}")
print(f"Accuracy: {metrics['accuracy']:.2%}")
print(f"Passed Quality Gate: {metrics['passed']}")
```

### Step 3: Submit to Hub

```python
from quantgrid.hub import hub
import hashlib

# Calculate dataset hash (proof of work)
dataset_str = str(your_dataset).encode()
dataset_hash = hashlib.sha256(dataset_str).hexdigest()

# Submit to the collective
metadata = hub.contribute_intelligence(
    adapter_path=adapter_path,
    domain="sec_filings",  # Your domain
    dataset_hash=dataset_hash,
    training_examples=len(your_dataset),
    metadata={
        "description": "Expert at analyzing 10-K filings",
        "version": "1.0.0"
    }
)

print(f"Submitted! Adapter ID: {metadata.adapter_id}")
```

### Step 4: What Happens Next

1. **Automated Evaluation** - Your adapter runs on our hidden benchmark
2. **Quality Check** - If `Loss < Official_Model_Loss`, you pass
3. **Community Review** - Other developers test and vote
4. **Monthly Aggregation** - Top adapters merged into next release
5. **Global Recognition** - You appear on the contributor leaderboard!

---

## Quality Standards

### Minimum Requirements

To be accepted into the collective, your adapter must:

- **Performance**: Loss < Official Baseline (evaluated on hidden benchmark)  
- **Training Data**: Minimum 1,000 examples  
- **Documentation**: Clear description of what your adapter does  
- **License**: MIT or Apache 2.0 (open contribution)  
- **Integrity**: Passes security scan (no malicious code)

### Evaluation Process

**Proof of Loss System:**
```
Adapter Submitted
    ↓
Automated Evaluation on Hidden Benchmark (1000 examples)
    ↓
Loss < Official Model? 
    ↓           ↓
   YES         NO
    ↓           ↓
  ACCEPT      REJECT
```

No politics. No bias. **Just math.**

---

## Contributor Leaderboard

Top contributors gain:

- **Global recognition** on hub.quantgrid.dev
- **Badges** on your GitHub profile
- **Early access** to new features
- **Premium features** for free
- **Potential bounties** for high-impact domains

### Scoring System

Your score is calculated from:
- **Evaluation Performance** (50%) - How much your adapter improves the model
- **Community Votes** (30%) - Real-world feedback from users
- **Training Scale** (10%) - Number of examples used
- **Adoption** (10%) - How many people use your adapter

---

## Privacy & Security

### What Gets Shared

- **Shared**: LoRA adapter weights (~100MB per adapter)  
- **Shared**: Evaluation metrics and performance scores  
- **Shared**: General domain description  

- **NOT Shared**: Your raw training data  
- **NOT Shared**: Your data sources or methodology  
- **NOT Shared**: Any personally identifiable information

### Security Checks

Every submission goes through:
1. **Malware Scan** - Check for malicious code
2. **Size Verification** - Must be reasonable size (~50-200MB)
3. **Format Validation** - Must be valid LoRA adapter
4. **Hallucination Check** - Tested for factual accuracy
5. **Bias Detection** - Screened for harmful biases

---

## Code Contributions

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/QuantGrid/quantgrid-core.git
cd quantgrid-core

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/

# Check code quality
black quantgrid/
ruff quantgrid/
mypy quantgrid/
```

### Contribution Workflow

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make changes** with clear commits
4. **Write tests** for new functionality
5. **Run all tests** to ensure nothing breaks
6. **Format code**: `black .` and `ruff --fix .`
7. **Submit PR** with clear description

### Code Standards

- **Python 3.11+** required
- **Type hints** for all functions
- **Docstrings** with examples
- **Test coverage** > 80%
- **Black** formatting
- **Ruff** linting

---

## Documentation Contributions

Help improve our docs:

- **API Documentation** - Document new features
- **Tutorials** - Write guides for common tasks
- **Examples** - Share your use cases
- **Translation** - Help translate to other languages

---

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment:

- **Be Respectful** - Treat everyone with kindness
- **Be Collaborative** - Help others learn and grow
- **Be Professional** - Keep discussions focused
- **Be Open-Minded** - Welcome diverse perspectives

### Communication Channels

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General questions and ideas
- **Discord** (coming soon) - Real-time chat
- **Email** - support@quantgrid.dev

---

## Bounty Program

We offer bounties for high-impact contributions:

### Active Bounties

- **$500** - First 10-K filing expert (Loss < 0.4)
- **$500** - Earnings call specialist (Loss < 0.4)
- **$1000** - Multi-domain expert (SEC + Earnings + Technical)
- **$2000** - Create evaluation benchmark (1000 verified examples)

Check [hub.quantgrid.dev/bounties](https://hub.quantgrid.dev/bounties) for current opportunities.

---

## Resources

### Training Guides

- [ML Training Guide](./docs/ML_TRAINING.md) - Complete training tutorial
- [Dataset Preparation](./docs/DATASET_PREP.md) - How to format your data
- [Evaluation Guide](./docs/EVALUATION.md) - Understanding metrics
- [Best Practices](./docs/BEST_PRACTICES.md) - Tips for success

### Example Contributions

See `examples/` directory for reference implementations:
- `sec_filings_adapter/` - SEC filing analysis example
- `earnings_calls_adapter/` - Earnings summarization example
- `technical_analysis_adapter/` - Chart pattern recognition

---

## Getting Help

**Stuck? We're here to help!**

1. **Check Documentation** - [docs/](./docs/)
2. **Search Issues** - Someone may have asked before
3. **Ask on Discussions** - Community support
4. **Email Us** - support@quantgrid.dev

---

## License

By contributing, you agree that your contributions will be licensed under the **MIT License**.

For intelligence contributions (model weights), you agree:
- Your adapter is licensed under MIT or Apache 2.0
- You have the right to share the trained weights
- You understand weights may be merged into the official model
- You retain credit for your contribution

---

## Thank You!

Every contribution makes QuantGrid stronger. Together, we're building the future of financial intelligence.

**Let's build the Hive Mind together!**

---

**Ready to contribute?**

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/quantgrid-core.git

# Start contributing!
cd quantgrid-core
pip install -e ".[dev]"
```

See you in the Hive!
