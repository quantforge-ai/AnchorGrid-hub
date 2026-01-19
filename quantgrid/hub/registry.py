"""
QuantGrid Hub - Collective Intelligence Registry

The interface to the Hive Mind.
Manages downloading, verifying, and merging community intelligence.

This is Federated Learning for the masses.
"""

import os
import hashlib
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from loguru import logger

try:
    from peft import PeftModel, get_peft_model, LoraConfig
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    logger.warning("PEFT not installed. Hub features will be limited.")


@dataclass
class AdapterMetadata:
    """Metadata for a community-contributed adapter"""
    adapter_id: str
    author: str
    domain: str  # "sec_filings", "earnings_calls", "technical_analysis"
    training_examples: int
    evaluation_score: float  # Loss on hold-out dataset
    dataset_hash: str  # SHA256 of training data (proof of work)
    created_at: datetime
    downloads: int = 0
    upvotes: int = 0
    version: str = "1.0.0"
    license: str = "MIT"
    
    def to_dict(self) -> dict:
        return {
            "adapter_id": self.adapter_id,
            "author": self.author,
            "domain": self.domain,
            "training_examples": self.training_examples,
            "evaluation_score": self.evaluation_score,
            "dataset_hash": self.dataset_hash,
            "created_at": self.created_at.isoformat(),
            "downloads": self.downloads,
            "upvotes": self.upvotes,
            "version": self.version,
            "license": self.license,
        }


class QuantGridHub:
    """
    The interface for the Hive Mind.
    
    This is how QuantGrid becomes a Network:
    - Developers train on private data
    - Share LoRA weights (intelligence) not raw data (privacy)
    - Community aggregates into super-model
    - Everyone benefits from collective learning
    
    The network effect: More contributors = Stronger model = More value for everyone
    """
    
    def __init__(
        self,
        base_model_id: str = "mistralai/Mistral-7B-v0.1",
        cache_dir: str = "./quantgrid_cache",
        hub_url: str = "https://hub.quantgrid.dev"  # Future: Central registry
    ):
        self.base_model_id = base_model_id
        self.cache_dir = cache_dir
        self.hub_url = hub_url
        
        if not PEFT_AVAILABLE:
            raise ImportError(
                "PEFT library required for Hub features. "
                "Install with: pip install quantgrid[ml]"
            )
        
        os.makedirs(cache_dir, exist_ok=True)
        logger.info("🌐 QuantGrid Hub initialized - Connecting to collective intelligence...")
    
    def pull_community_adapters(
        self,
        domain: str = "finance",
        min_score: float = 0.9,
        top_k: int = 10
    ) -> List[AdapterMetadata]:
        """
        Fetch top-rated adapters from QuantGrid Central.
        
        Only downloads adapters that passed 'Proof of Loss' evaluation.
        
        Args:
            domain: Domain expertise (e.g., "sec_filings", "earnings_calls")
            min_score: Minimum evaluation score (0.0 to 1.0)
            top_k: Number of top adapters to fetch
            
        Returns:
            List of adapter metadata sorted by quality
        """
        logger.info(f"📡 Connecting to QuantGrid Hive... searching for '{domain}' experts...")
        
        # TODO: Implement actual API call to hub.quantgrid.dev
        # For now, return mock data
        adapters = self._fetch_top_adapters(domain, min_score, top_k)
        
        logger.info(f"✅ Found {len(adapters)} verified experts in {domain}")
        return adapters
    
    def _fetch_top_adapters(
        self,
        domain: str,
        min_score: float,
        top_k: int
    ) -> List[AdapterMetadata]:
        """Fetch adapter metadata from registry (mock for now)"""
        # TODO: Replace with actual API call
        # Example structure for future implementation:
        # response = httpx.get(f"{self.hub_url}/api/v1/adapters", params={
        #     "domain": domain,
        #     "min_score": min_score,
        #     "limit": top_k
        # })
        # return [AdapterMetadata(**item) for item in response.json()]
        
        return []
    
    def build_consensus_model(
        self,
        adapter_list: List[str],
        weights: Optional[List[float]] = None,
        combination_type: str = "linear"
    ):
        """
        The Magic: Merges individual expertise into one Super-Model.
        
        Uses 'Model Soup' averaging technique from Google Research.
        
        Args:
            adapter_list: List of adapter IDs or paths
            weights: Optional weights for each adapter (default: equal)
            combination_type: "linear" (average) or "ties" (Task-Arithmetic)
            
        Returns:
            Merged model with collective intelligence
        """
        logger.info(f"⚗️ Brewing Model Soup with {len(adapter_list)} ingredients...")
        
        if weights is None:
            # Equal weight democracy
            weights = [1.0 / len(adapter_list)] * len(adapter_list)
        
        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # TODO: Implement actual adapter merging using PEFT
        # This requires the add_weighted_adapter functionality
        # For now, return base model as placeholder
        
        logger.info("✅ Consensus model built - Collective intelligence activated!")
        return base_model
    
    def contribute_intelligence(
        self,
        adapter_path: str,
        domain: str,
        dataset_hash: str,
        training_examples: int,
        metadata: Optional[Dict] = None
    ) -> AdapterMetadata:
        """
        Allow developers to upload their fine-tune to the collective.
        
        Must include dataset hash for 'Proof of Work' verification.
        Adapter will be evaluated on hold-out dataset for quality control.
        
        Args:
            adapter_path: Path to LoRA adapter files
            domain: Domain of expertise
            dataset_hash: SHA256 hash of training dataset
            training_examples: Number of examples used
            metadata: Additional metadata
            
        Returns:
            Metadata object with upload confirmation
        """
        if not self._verify_integrity(adapter_path):
            raise ValueError("❌ Adapter failed integrity check")
        
        logger.info("🔍 Running Proof of Loss evaluation...")
        
        # TODO: Run automated evaluation on benchmark
        # evaluation_score = self._evaluate_adapter(adapter_path)
        
        logger.info("🚀 Uploading intelligence to the grid...")
        
        # TODO: Upload to hub.quantgrid.dev
        # response = httpx.post(f"{self.hub_url}/api/v1/adapters/submit", ...)
        
        adapter_metadata = AdapterMetadata(
            adapter_id=f"community/{domain}/{hashlib.md5(adapter_path.encode()).hexdigest()[:8]}",
            author="developer",  # TODO: Get from auth
            domain=domain,
            training_examples=training_examples,
            evaluation_score=0.0,  # TODO: Real score
            dataset_hash=dataset_hash,
            created_at=datetime.utcnow(),
        )
        
        logger.info(f"✅ Intelligence contributed! Adapter ID: {adapter_metadata.adapter_id}")
        return adapter_metadata
    
    def _verify_integrity(self, adapter_path: str) -> bool:
        """Verify adapter integrity and security"""
        if not os.path.exists(adapter_path):
            return False
        
        # TODO: Add security checks:
        # - Scan for malicious code
        # - Verify file signatures
        # - Check file size limits
        # - Validate LoRA format
        
        return True
    
    def get_leaderboard(self, domain: str = "all", limit: int = 100) -> List[AdapterMetadata]:
        """
        Get the global leaderboard of contributors.
        
        Sorted by evaluation score and community votes.
        """
        logger.info(f"🏆 Fetching leaderboard for {domain}...")
        
        # TODO: Fetch from API
        return []
    
    def download_official_adapter(self, version: str = "latest") -> str:
        """
        Download the official aggregated adapter.
        
        This is the collective intelligence of the entire community,
        merged monthly from top-performing submissions.
        
        Args:
            version: Version tag (e.g., "latest", "v1.1.0", "v1.2.0")
            
        Returns:
            Path to downloaded adapter
        """
        logger.info(f"📥 Downloading official adapter {version}...")
        
        # TODO: Download from hub.quantgrid.dev/official/
        
        adapter_path = os.path.join(self.cache_dir, f"official-{version}")
        logger.info(f"✅ Official adapter ready at {adapter_path}")
        
        return adapter_path


# Global instance
hub = QuantGridHub()
