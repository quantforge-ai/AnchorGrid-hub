# API Versioning Guide

QuantGrid uses URL-based versioning for its REST APIs to ensure backward compatibility.

## Structure

```
quantgrid/api/
├── v1/              # Current stable API (v0.2.0+)
│   ├── auth.py      # Authentication endpoints
│   ├── ai.py        # AI analysis endpoints
│   ├── market.py    # Market data endpoints
│   ├── vector.py    # Vector search endpoints
│   ├── feeds.py     # Data feed endpoints
│   └── health.py    # Health check
└── v2/              # Reserved for future breaking changes
```

## Mounting Routes

### In Your FastAPI Application

```python
from fastapi import FastAPI
from quantgrid.api import v1

app = FastAPI()

# Mount v1 routes with /api/v1 prefix
app.include_router(v1.auth.router, prefix="/api/v1/auth", tags=["Auth v1"])
app.include_router(v1.ai.router, prefix="/api/v1/ai", tags=["AI v1"])
app.include_router(v1.market.router, prefix="/api/v1/market", tags=["Market v1"])
app.include_router(v1.vector.router, prefix="/api/v1/vector", tags=["Vector v1"])
app.include_router(v1.feeds.router, prefix="/api/v1/feeds", tags=["Feeds v1"])
app.include_router(v1.health.router, prefix="/api/v1/health", tags=["Health"])
```

### Available Endpoints

**v1 API** (Current):
- `POST /api/v1/auth/token` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/register` - Register user
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/ai/analyze` - AI analysis
- `GET /api/v1/market/quote/{symbol}` - Get quote
- `GET /api/v1/market/signals/{symbol}` - Get signals
- `POST /api/v1/vector/search` - Vector search
- `POST /api/v1/feeds/trigger` - Trigger data ingestion
- `GET /api/v1/health` - Health check

## Version Migration Strategy

When introducing breaking changes:

1. **Create v2 routes**: Add new endpoints in `quantgrid/api/v2/`
2. **Deprecation warnings**: Add deprecation warnings to v1 endpoints
3. **Grace period**: Maintain both v1 and v2 for 6 months minimum
4. **Documentation**: Update docs with migration guide
5. **Sunset v1**: Remove v1 after grace period

## Best Practices

### For Package Users

```python
# ✅ GOOD: Explicit version in URL
response = httpx.get("http://localhost:8000/api/v1/market/quote/AAPL")

# ❌ BAD: No version - will break on updates
response = httpx.get("http://localhost:8000/market/quote/AAPL")
```

### For API Developers

```python
# ✅ GOOD: Version-specific imports
from quantgrid.api.v1 import market

app.include_router(market.router, prefix="/api/v1/market")

# ❌ BAD: Generic imports (no version control)
from quantgrid.api import market  # Which version?
```

## Semantic Versioning

- **v1.x.x**: Backward-compatible additions (new endpoints, optional parameters)
- **v2.x.x**: Breaking changes (removed endpoints, changed response formats, required parameters)

## Terminal Routes (No Versioning)

Terminal routes in `quantgrid/routes/` are NOT versioned as they're internal to the terminal application:

```python
# These don't use versioning
app.include_router(quotes.router, tags=["Quotes"])
app.include_router(paper_trading.router, prefix="/paper-trading")
```

---

**Related Documentation:**
- [API Reference](https://quantgrid.dev/docs/api)
- [Migration Guide](https://quantgrid.dev/docs/migration)
- [Breaking Changes Log](https://quantgrid.dev/docs/changelog)
