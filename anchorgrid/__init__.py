"""
AnchorGrid - The Universal Intelligence Protocol

The world's first decentralized marketplace for AI models across domains.
Like Epic Games Store, but for Intelligence.

Basic Usage:
    # Browse the marketplace
    $ anchorgrid search medical
    
    # View plugin details  
    $ anchorgrid info @anchorgrid/finance-core
    
    # Download a plugin
    $ anchorgrid pull @anchorgrid/finance-core

Advanced Usage:
    # Use Finance Plugin (connectors & extractors)
    from anchorgrid.plugins.finance.connectors import yfinance_scraper
    from anchorgrid.plugins.finance.extractors import rsi
    
    # Database access
    from anchorgrid.db.session import get_async_session
    from anchorgrid.db.models import User, Portfolio
    
    # Services (requires Redis/PostgreSQL)
    from anchorgrid.services.quote_service import quote_service
    
Note: Heavy imports (LLM, ML, Services) are lazy-loaded to keep CLI fast.
"""

__version__ = "1.0.0"
__author__ = "AnchorGrid Team"

# No eager imports - keeps CLI fast and prevents dependency cascades
# Users import what they need explicitly

__all__ = [
    "__version__",
    "__author__",
]
