# ZON Format Guide - Zero Overhead Notation

> **Attribution**: ZON (Zero Overhead Notation) is developed by the creators at [zonformat.org](https://zonformat.org). AnchorGrid uses ZON for token-efficient financial data serialization.

**The most token-efficient format for financial data.**

---

## What is ZON?

ZON (Zero Overhead Notation) is a token-efficient serialization format designed for LLM workflows. It reduces token usage by **35-50%** compared to JSON while maintaining full readability and JSON compatibility.

### Why We Use ZON in AnchorGrid

**JSON Example** (124 tokens):
```json
{
  "instruction": "Analyze this SEC filing",
  "input": "Item 1. Business\n\nApple Inc. designs, manufactures...",
  "output": "Key findings: Revenue up 15% YoY to $394B, gross margin improved to 43.3%"
}
```

**ZON Example** (74 tokens - 40% savings!):
```zon
q:Analyze this SEC filing|i:Item 1. Business
Apple Inc. designs, manufactures...|o:Revenue ↑15% YoY $394B, margin 43.3%, cash $166B
```

### Savings at Scale

- **1,000 examples**: Save ~50,000 tokens
- **10,000 examples**: Save ~500,000 tokens  
- **100,000 examples**: Save ~5,000,000 tokens

**Why this matters:**
- Faster training (fewer tokens to process)
- Lower costs (less compute needed)
- Easier to share (smaller file sizes)

---

## ZON Syntax

### Basic Structure

```
q:QUESTION|i:INPUT|o:OUTPUT
```

- `q:` = Question/Instruction
- `i:` = Input/Context
- `o:` = Output/Response
- `|` = Field separator
- `---` = Example separator

### Full Example

```zon
q:Analyze AAPL|i:Price $258, RSI 25, MACD bullish|o:Oversold + momentum reversal = BUY
---
q:Summarize 10-K|i:Item 1. Business
Apple Inc...|o:Revenue ↑15% YoY, Services strong, iPhone growth 9%
---
q:Risk assessment|i:Portfolio: 60% stocks, 40% bonds, $1M|o:Moderate risk, well-diversified, age-appropriate
```

---

## Using ZON in Training

```python
from anchorgrid.core.zon_engine import ZONEngine

# Initialize
zon = ZONEngine()

# Option 1: Load from ZON file
dataset = zon.load_from_file("my_dataset.zon")

# Option 2: Parse ZON string
zon_data = """
q:What's the trend?|i:EMA20 > EMA50, bullish MACD|o:Strong uptrend confirmed
---
q:Position size?|i:Account $100k, risk 2%, ATR $5|o:Buy 400 shares, stop at $253
"""
dataset = zon.parse_training_data(zon_data)

# Option 3: Convert from JSON
import json
json_data = json.load(open("data.json"))
zon_string = zon.from_json(json_data)
```

---

## ZON Shortcuts

Use Unicode symbols to save even more tokens:

- `↑` = increase/up
- `↓` = decrease/down  
- `→` = leads to/results in
- `≈` = approximately
- `✓` = confirmed/yes
- `✗` = rejected/no

**Example:**
```
q:Earnings impact?|i:Beat EPS $1.52 vs $1.39|o:Stock ↑12% → new high. Buy signal ✓
```

---

## Converting Existing Datasets

### JSON to ZON

```python
from anchorgrid.core.zon_engine import ZONEngine

zon = ZONEngine()

# Load JSON dataset
import json
with open("dataset.json") as f:
    json_data = json.load(f)

# Convert to ZON
zon_string = zon.to_zon(json_data)

# Save
with open("dataset.zon", "w") as f:
    f.write(zon_string)

print(f"Saved {len(zon_string)} chars (was {len(json.dumps(json_data))} chars)")
```

### ZON to JSON

```python
# Load ZON
with open("dataset.zon") as f:
    zon_data = f.read()

# Convert to JSON
json_data = zon.to_json(zon_data)

# Save
with open("dataset.json", "w") as f:
    json.dump(json_data, f, indent=2)
```

---

## Best Practices

### ✅ DO:
- Use ZON for training datasets (huge token savings)
- Use Unicode shortcuts for common terms
- Keep fields concise but informative
- Separate examples with `---`

### ❌ DON'T:
- Use ZON for complex nested data (use JSON instead)
- Forget the field separators (`|`)
- Mix ZON and JSON in same file

---

## File Extension

Use **`.zon`** extension for ZON files:

```
my_dataset.zon
sec_filings.zon
earnings_calls.zon
```

> **Note**: There is a proposal to standardize `.zonf` as the official extension, but currently `.zon` is used in practice. See zonformat.org for updates.

---

## Official Resources

- **Specification**: [zonformat.org](https://zonformat.org)
- **CLI Tools**: Available via `zon-format` package
- **Libraries**: TypeScript, JavaScript, and Python implementations

---

## Why ZON Matters for AnchorGrid

When you submit adapters to the Hub, ZON format:
- **Reduces dataset size** by 35-50% (easier to share metadata)
- **Faster evaluation** (fewer tokens to process)
- **Lower training costs** (less compute needed)
- **Industry standard** (compatible with other LLM tools)

**Start using ZON today and save millions of tokens!**

---

**Note**: AnchorGrid uses ZON as a community standard. All credit for ZON format specification goes to the creators at zonformat.org.
