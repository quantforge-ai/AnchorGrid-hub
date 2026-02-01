# AnchorGrid API & Routes Guide

The `anchorgrid.api` and `anchorgrid.routes` packages define the interaction layer for external applications and the Grid Terminal.

## Platform API (`anchorgrid.api`)

Standard REST endpoints for the AnchorGrid Intelligence Platform. These routes use versioning (defaulting to `/api/v1/`).

### Version 1 Endpoints
- `/auth/`: User registration and JWT management.
- `/ai/`: Interface for the Agent Orchestrator.
- `/market/`: High-level market data and signals.
- `/vector/`: Semantic search and document retrieval.
- `/health`: System diagnostics.

## Terminal Routes (`anchorgrid.routes`)

Internal endpoints optimized for the AnchorGrid Terminal dashboard.
- Live data streaming over WebSockets.
- Dashboard-specific data structures.
- User preference persistence.

## Security & Versioning

### Authentication
All routes (except health) require a valid JWT or API Key provided in the `Authorization` header.

### Versioning Strategy
We use URL-based versioning to ensure zero breaking changes for integrations.
- Current: `/api/v1/`
- Deprecated: `/api/v0/` (Internal beta)

## Usage Example

```bash
# Get AI analysis via curl
curl -X POST "http://localhost:8000/api/v1/ai/analyze" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"query": "Analyze BTC trend"}'

# Check market signals
curl "http://localhost:8000/api/v1/market/signals/AAPL"
```

---

## Deployment
The API layer is powered by FastAPI and Uvicorn. It is designed to be horizontally scalable and can be deployed in containers across multiple regions.
