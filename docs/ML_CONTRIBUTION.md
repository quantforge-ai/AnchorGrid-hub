# Contributing Intelligence to the QuantGrid Hive Mind

This guide shows you how to **train and contribute your own financial models** to improve QuantGrid for everyone.

> **"Your private data stays private. Only the trained adapter leaves your machine."**

---

## Why Contribute?

When you contribute a trained adapter to QuantGrid:

1. **Your Intelligence Lives Forever**: Your model becomes part of the collective intelligence
2. **You're Listed as a Contributor**: Get credit in our global leaderboard
3. **Everyone Benefits**: Your specialized knowledge improves the system for all users
4. **No Data Sharing Required**: Only the trained weights are shared, never your raw data

---

## Prerequisites

**Hardware:**
- GPU with 12GB+ VRAM (RTX 3060, 4060 Ti, or better)
- 16GB+ System RAM
- Or: Use Google Colab (free GPU access)

**Software:**
```bash
pip install quantgrid[ml]
```

---

## Quick Start (3 Steps)

### Step 1: Prepare Your Dataset

Create a JSON file with financial question-answer pairs:

```json
[
  {
    "text": "Question: What was Apple's revenue in Q4 2023?\nAnswer: Apple reported $117.2B in revenue for Q4 2023, up 2% YoY."
  },
  {
    "text": "Question: Explain the impact of rising interest rates on tech stocks.\nAnswer: Rising rates reduce present value of future earnings, particularly affecting high-growth tech companies with distant cash flows."
  }
]
```

**Data Sources (No API Key Required!):**
- SEC EDGAR filings (10-K, 10-Q, 8-K)
- Earnings call transcripts
- Financial news articles
- Your proprietary research
- Hedge fund letters

**Recommended Size:** 500-5000 examples

---

### Step 2: Train Your Adapter

```python
from quantgrid.ml.trainer import QuantGridTrainer

# Initialize trainer (uses standardized LoRA settings)
trainer = QuantGridTrainer()

# Train on your data
trainer.train(
    dataset_path="my_sec_data.json",
    output_dir="./my_sec_adapter",
    num_epochs=3,
    batch_size=4,
)

# Output:
# Testing Complete! Adapter saved to ./my_sec_adapter
```

**What Happens:**
- Loads Mistral-7B in 4-bit (fits on 12GB GPU)
- Trains a LoRA adapter with **standardized settings** (Rank 16, Alpha 32)
- Saves only the adapter (~50MB) - base model stays frozen

**Training Time:** 2-6 hours depending on dataset size and GPU

---

### Step 3: Submit to the Hive Mind

#### 3a. Package Your Adapter

```python
from quantgrid.hub.submit import prepare_submission

prepare_submission(
    adapter_dir="./my_sec_adapter",
    author_name="Your Name",
    dataset_desc="SEC 10-K Filings 2020-2023",
)

# Output:
# READY FOR UPLOAD!
# File: quantgrid_submission_1704321600.zip
# Hash: a1b2c3d4...
```

#### 3b. Upload via CLI

```bash
# First time: Authenticate
quantgrid login

# Upload your adapter
quantgrid push quantgrid_submission_1704321600.zip

# Check status
quantgrid status your_submission_id
```

**What Happens Next:**
1. **Validation**: Your adapter runs through our Proof of Loss benchmark
2. **Standard Quality Check**: Must meet minimum performance threshold
3. **Weekly Merge**: If approved, merged with others every Sunday
4. **Auto-Deploy**: New version (YYYY.WW) goes live automatically

---

## What Gets Shared?

| Item | Shared? | Notes |
|------|---------|-------|
| Raw training data | No Never | Stays on your machine |
| Trained LoRA weights | Yes | Only 50MB of adapter parameters |
| Base model | No Never | Everyone uses the same frozen base |
| Your name/handle | Yes | For contributor credit |

---

## Quality Standards

Your adapter must pass the **Proof of Loss** evaluation:

- **Benchmark**: 500 curated financial Q&A pairs
- **Metric**: Cross-entropy loss
- **Threshold**: Must match or beat baseline performance
- **Purpose**: Prevents harmful/low-quality submissions

**If your adapter degrades overall performance, it will be auto-rejected.**

---

## Contributor Leaderboard

Top contributors are ranked by:
1. Number of accepted adapters
2. Impact on model performance
3. Community upvotes

View the leaderboard:
```bash
quantgrid leaderboard
```

---

## Advanced: Google Colab Training

Don't have a GPU? Use Colab:

```python
# In Colab notebook:
!pip install quantgrid[ml]

from quantgrid.ml.trainer import QuantGridTrainer

trainer = QuantGridTrainer()
trainer.train("my_data.json", output_dir="./adapter")

# Download the adapter to your machine
from google.colab import files
!zip -r adapter.zip ./adapter
files.download('adapter.zip')
```

---

## Best Practices

### Data Quality
- **Domain-specific is better than generic**: A focused dataset on earnings calls beats random financial tweets
- **Accuracy matters**: Wrong information degrades the Hive Mind
- **Diversity helps**: Mix different financial topics

### Training Tips
- **Start small**: Test on 100 examples first
- **Monitor loss**: Should decrease steadily
- **Don't overfit**: 3 epochs is usually enough

### Specialized Niches
The most valuable contributions are **specialized knowledge**:
- Sector-specific analysis (biotech, energy, crypto)
- Alternative data interpretation (satellite imagery, credit card data)
- Regulatory filings (SEC, FDA, patent applications)
- International markets (ASX, LSE, TSE)

---

## FAQ

**Q: Can I keep my adapter private?**  
A: No - QuantGrid Hub is for collective intelligence. For private models, train locally without submitting.

**Q: Will I see others' raw data?**  
A: No - only trained weights are shared, never raw data.

**Q: How often are new versions released?**  
A: Every Sunday at 3 AM UTC (CalVer: YYYY.WW)

**Q: Can I submit multiple adapters?**  
A: Yes! The more the better. Each trains on different data.

**Q: What if my adapter is rejected?**  
A: Check the evaluation report. Common issues: too small dataset, overfitting, low quality data.

**Q: Do I need to retrain when a new version is released?**  
A: No - adapters are cumulative. Your contribution lives forever.

---

## Join the Hive Mind

Every contribution makes QuantGrid smarter. Your expertise in pharmaceutical earnings calls, European equities, or crypto fundamentals fills gaps that generic models miss.

**Ready to contribute?**

```bash
# Install ML dependencies
pip install quantgrid[ml]

# Authenticate with Hub
quantgrid login

# Train and push your first adapter
python my_training_script.py
quantgrid push my_adapter.zip
```

**Questions?** Open an issue on GitHub or join our Discord.

---

*"Individually we are smart. Together we are genius."*
