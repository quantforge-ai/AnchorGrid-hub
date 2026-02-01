"""
AnchorGrid Universal Registry - The Decentralized Marketplace

This is the interface to the future hub.anchorgrid.net marketplace.
For now, it mocks the network with hardcoded "Century-Scale" plugins.

The registry contains plugins from multiple domains:
- Finance: Trading, risk analysis, sentiment
- Medical: Tumor detection, diagnosis, drug discovery
- Legal: Contract audit, compliance, case law
- Code: Bug detection, security audit, optimization

ID Convention:
- Official plugins: Short single-word IDs (finance, medical, legal)
- Community plugins: user/package format (defi/sniper, med-ai/radiology)
"""

import time
from typing import List, Optional, Dict
from pydantic import BaseModel


class PluginMetadata(BaseModel):
    """
    Metadata for a plugin/model in the Universal Registry.
    
    This is what gets shown in the "Store" UI.
    """
    id: str              # Unique identifier (short: "finance" or namespaced: "user/package")
    full_name: str       # Display name for UI
    domain: str          # Domain category (finance, medical, legal, etc.)
    version: str         # Semantic version
    author: str          # Creator/organization
    description: str     # What it does
    downloads: int       # Popularity metric
    score: float         # Proof of Utility score (0.0 - 1.0)
    price: str           # "Free" or monthly subscription


# ============================================================================
# THE MOCK DATABASE (This will be replaced by hub.anchorgrid.net API)
# ============================================================================

MOCK_DATABASE = [
    # ========================================================================
    # OFFICIAL PLUGINS (Short IDs - Reserved)
    # ========================================================================
    
    PluginMetadata(
        id="finance",
        full_name="Wall St. Standard",
        domain="finance",
        version="1.2",
        author="AnchorGrid",
        description="Official connectors (Yahoo/SEC) & extractors (RSI/MACD). Zero-cost alternative to Bloomberg.",
        downloads=12500,
        score=0.98,
        price="Free"
    ),
    
    PluginMetadata(
        id="medical",
        full_name="OncoDetect Pro",
        domain="medical",
        version="4.1",
        author="Hospital_DAO",
        description="Tumor detection adapter trained on 50k private DICOM scans. 94% verified accuracy.",
        downloads=840,
        score=0.94,
        price="$500/mo"
    ),
    
    PluginMetadata(
        id="legal",
        full_name="NDA Killer",
        domain="legal",
        version="2.0",
        author="LegalTech",
        description="Detects loopholes in standard NDAs. Trained on 5k real cases. Saved clients $2M.",
        downloads=3100,
        score=0.89,
        price="$50/mo"
    ),
    
    PluginMetadata(
        id="code",
        full_name="Vuln Hunter",
        domain="code",
        version="3.0",
        author="WhiteHat",
        description="Smart contract vulnerability detection. Trained on all Ethereum exploits (2016-2025).",
        downloads=8900,
        score=0.96,
        price="$100/mo"
    ),
    
    # ========================================================================
    # COMMUNITY PLUGINS (Namespaced IDs - user/package)
    # ========================================================================
    
    PluginMetadata(
        id="defi/sniper",
        full_name="Degen Sentiment",
        domain="finance",
        version="0.9b",
        author="Satoshi_Ghost",
        description="High-frequency sentiment for meme coins. Twitter/Reddit scrapers + LoRA fine-tuned on 100k trades.",
        downloads=45000,
        score=0.72,
        price="Free"
    ),
    
    PluginMetadata(
        id="med-ai/radiology",
        full_name="X-Ray Vision",
        domain="medical",
        version="2.3",
        author="RadAI Collective",
        description="Federated chest X-ray analysis. Trained across 200 hospitals without sharing patient data.",
        downloads=1200,
        score=0.91,
        price="$200/mo"
    ),
    
    PluginMetadata(
        id="legal/gdpr",
        full_name="GDPR Guardian",
        domain="legal",
        version="1.5",
        author="PrivacyFirst",
        description="Scans codebases for GDPR violations. Trained on 10k privacy policies and 3k lawsuits.",
        downloads=5600,
        score=0.87,
        price="Free"
    ),
]


class Registry:
    """
    The interface to the Decentralized Marketplace.
    
    In production, this will make HTTP calls to hub.anchorgrid.net.
    For the demo/MVP, it returns hardcoded data to prove the vision.
    """
    
    @staticmethod
    def search(query: str = "") -> List[PluginMetadata]:
        """
        Search the registry for plugins.
        
        Args:
            query: Search term (filters by id, name, domain, or description)
        
        Returns:
            List of matching plugins
        """
        # Simulate network latency (adds realism to the demo!)
        time.sleep(0.3) 
        
        # Empty query = show all
        if not query:
            return MOCK_DATABASE
        
        # Filter by query (case-insensitive)
        query = query.lower()
        return [
            p for p in MOCK_DATABASE 
            if query in p.id.lower() 
            or query in p.full_name.lower() 
            or query in p.domain.lower()
            or query in p.description.lower()
        ]

    @staticmethod
    def get_info(plugin_id: str) -> Optional[PluginMetadata]:
        """
        Get detailed info about a specific plugin.
        
        Args:
            plugin_id: Unique plugin identifier (e.g., "finance" or "defi/sniper")
        
        Returns:
            Plugin metadata or None if not found
        """
        time.sleep(0.1)  # Simulate API call
        
        for p in MOCK_DATABASE:
            if p.id == plugin_id:
                return p
        return None
    
    @staticmethod
    def get_featured() -> List[PluginMetadata]:
        """
        Get featured/highest rated plugins (for homepage).
        """
        # Return top 3 by score
        sorted_plugins = sorted(MOCK_DATABASE, key=lambda x: x.score, reverse=True)
        return sorted_plugins[:3]
    
    @staticmethod
    def get_by_domain(domain: str) -> List[PluginMetadata]:
        """
        Get all plugins for a specific domain.
        """
        return [p for p in MOCK_DATABASE if p.domain.lower() == domain.lower()]
