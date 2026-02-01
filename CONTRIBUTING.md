# Contributing to AnchorGrid

Thank you for your interest in contributing to AnchorGrid! This document provides guidelines for contributing to the project.

## 🎯 Project Vision

AnchorGrid is building the **secure infrastructure for agentic AI in regulated industries**. Our unique value proposition is **Proof-of-Integrity Discovery** - the first agent network where compliance is verified before agents can join.

---

## 🚀 Ways to Contribute

### 1. **New Domain Plugins**

We're expanding beyond Finance into Medical, Legal, and Code domains.

**What we need:**
- Domain-specific connectors (data sources)
- Domain-specific extractors (feature engineering)
- Domain-specific agents (AI reasoning logic)

**Example structure:**
```
anchorgrid/plugins/medical/
├── agent.py              # MedicalAgent class
├── manifest.json         # Plugin metadata
├── connectors/
│   └── dicom_reader.py   # Medical imaging data
└── extractors/
    └── tumor_detector.py # Feature extraction
```

**How to start:**
1. Copy `plugins/finance/` as a template
2. Replace Finance logic with your domain
3. Test with `anchorgrid run --plugin <domain> <task>`
4. Submit PR

### 2. **Security / Red-Teaming**

Help us make the Verification Layer bulletproof.

**Attack vectors to test:**
- Can you bypass Anchor certificate validation?
- Can you register a malicious agent?
- Can you fake a trust score?
- Can you inject code through the discovery protocol?

**How to contribute:**
1. Fork the repo
2. Try to break `anchorgrid/core/discovery.py`
3. Document the exploit
4. Submit security issue (private disclosure)

### 3. **Performance Optimization**

**Areas needing optimization:**
- Discovery protocol (can we handle 10,000+ agents?)
- Universal Engine (reduce latency)
- P2P distribution (faster downloads)

**Benchmarking:**
```bash
# Run performance tests
python -m pytest tests/perf/ -v

# Profile discovery
python -m cProfile demo_discovery.py
```

### 4. **Policy Integrations**

**What we need:**
- FINOS policy parser (YAML → Anchor checks)
- OWASP Agentic Top 10 ruleset
- Custom policy templates

**Example:**
```python
# anchorgrid/policies/finos.py

def parse_finos_threat_model(yaml_file):
    """Convert FINOS YAML to Anchor policy"""
    threats = load_yaml(yaml_file)
    policy = AnchorPolicy()
    
    for threat in threats:
        if threat.type == "BIAS":
            policy.add_check(BiasCheck(threshold=0.05))
    
    return policy
```

### 5. **Documentation**

**Always valuable:**
- Improve README clarity
- Add code examples
- Create tutorials
- Write blog posts

---

## 📝 Contribution Process

### Step 1: Fork & Clone

```bash
git clone https://github.com/YourUsername/anchorgrid-core.git
cd anchorgrid-core
```

### Step 2: Create Branch

```bash
git checkout -b feature/your-feature-name
```

**Branch naming:**
- `feature/medical-plugin` (new features)
- `fix/discovery-memory-leak` (bug fixes)
- `docs/cli-tutorial` (documentation)
- `perf/engine-optimization` (performance)

### Step 3: Make Changes

**Code style:**
- Use type hints (`def func(x: int) -> str:`)
- Add docstrings (Google style)
- Format with `black` (line length: 88)
- Lint with `ruff`

**Example:**
```python
def register_agent(
    agent_id: str,
    capabilities: List[str],
    anchor_cert: dict,
    policy: str
) -> AgentInfo:
    """
    Register agent with Anchor verification.
    
    Args:
        agent_id: Unique identifier for agent
        capabilities: List of capabilities (e.g., ["finance", "analysis"])
        anchor_cert: Anchor compliance certificate
        policy: Policy name (e.g., "finos-financial")
    
    Returns:
        AgentInfo object with registration details
    
    Raises:
        RegistrationError: If verification fails
    """
    # Implementation
```

### Step 4: Test

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_discovery.py

# Check coverage
pytest --cov=anchorgrid --cov-report=html
```

### Step 5: Commit

```bash
git add .
git commit -m "feat: Add medical plugin with DICOM support"
```

**Commit message format:**
- `feat: Add new feature`
- `fix: Fix bug in discovery protocol`
- `docs: Update README`
- `perf: Optimize engine latency`
- `test: Add discovery tests`
- `refactor: Simplify verification logic`

### Step 6: Push & PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

**PR checklist:**
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or clearly marked)
- [ ] Follows code style
- [ ] Security reviewed (if applicable)

---

## 🏗️ Project Structure

```
anchorgrid-core/
├── anchorgrid/
│   ├── core/              # Discovery, engine, security
│   ├── plugins/           # Domain-specific agents
│   ├── cli.py             # Main CLI
│   └── db/                # Database models
│
├── tests/                 # Test suite
├── docs/                  # Documentation
├── demo_discovery.py      # Demo scripts
└── README.md
```

---

## 🧪 Testing Guidelines

### Unit Tests

```python
# tests/test_discovery.py

def test_register_valid_agent():
    """Test successful registration with valid cert"""
    cert = {"score": 98, "hash": "0xabc", "expires": future_date}
    
    agent = discovery.register_agent(
        agent_id="TestBot",
        capabilities=["test"],
        anchor_cert=cert,
        policy="test-policy"
    )
    
    assert agent.agent_id == "TestBot"
    assert agent.anchor_score == 98
```

### Integration Tests

```python
# tests/test_integration.py

def test_full_discovery_flow():
    """Test register → discover → verify flow"""
    # 1. Register agent
    discovery.register_agent(...)
    
    # 2. Discover agents
    agents = discovery.discover(capability="finance")
    
    # 3. Verify trust scores
    assert all(a.anchor_score >= 95 for a in agents)
```

---

## 🛡️ Security Guidelines

### Reporting Vulnerabilities

**DO NOT** open public issues for security vulnerabilities.

**Instead:**
1. Email: [your-security-email]
2. Use GitHub Security Advisories (private disclosure)
3. Wait for response before public disclosure

### Security Checklist

When contributing security-sensitive code:

- [ ] Input validation (no SQL injection)
- [ ] Cryptographic signatures verified
- [ ] No hardcoded secrets
- [ ] Audit trail for sensitive operations
- [ ] Rate limiting (prevent DoS)

---

## 📚 Resources

### Learn More

- [Architecture Vision](docs/architecture.md)
- [Phase 4 Plan](docs/phase4_poid_plan.md)
- [GSoC Proposal](docs/gsoc_proposal.md)

### Communication

- **GitHub Issues:** Bug reports, feature requests
- **GitHub Discussions:** Questions, ideas
- **OWASP Slack:** #anchorgrid (coming soon)

---

## 🎓 For GSoC Contributors

### Getting Started

1. Read the [GSoC proposal](docs/gsoc_proposal.md)
2. Pick a Phase 5 task (Medical/Legal/Code plugins)
3. Check existing issues labeled `gsoc-2026`
4. Introduce yourself in GitHub Discussions

### Mentorship

Mentors available for:
- Architecture questions
- Code reviews
- Governance policy questions
- Career advice

---

## 🏆 Recognition

All contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Eligible for swag (coming soon)

**Top contributors:**
- Co-author credit in papers
- Speaker opportunities at conferences
- Direct collaboration with Anchor/FINOS teams

---

## ❤️ Thank You!

Every contribution matters - from fixing typos to building entire plugins. Together, we're building the secure foundation for agentic AI.

**Let's make regulated agentic AI a reality.** 🚀🔐
