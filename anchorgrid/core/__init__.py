"""
AnchorGrid Core - Universal Infrastructure

Contains domain-agnostic components:
- registry.py: Universal plugin marketplace
- engine.py: Universal LLM wrapper (coming in Phase 3)
- llm_router.py: Multi-provider LLM routing
- config.py: Settings and configuration
- downloader.py: Model downloading (requires huggingface_hub)

Import explicitly when needed:
    from anchorgrid.core.registry import Registry
    from anchorgrid.core.llm_router import LLMRouter
    from anchorgrid.core.config import settings  # Only if you need config
"""

# No eager imports - keeps package lightweight
# Users import what they need explicitly
# This prevents dependency cascades (e.g., downloader → huggingface_hub)

__all__ = [
    # Available modules (import explicitly):
    # - registry
    # - llm_router  
    # - config
    # - downloader
    # - verifier
]
