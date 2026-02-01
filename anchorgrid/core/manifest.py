"""
AnchorGrid Core - Universal Model Manifest

Domain-agnostic metadata system for AI models.
Works for finance, legal, code, medical, or any domain.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class GridManifest(BaseModel):
    """
    Universal manifest for any AI model.
    
    The domain is just metadata - the LoRA weights work for anything.
    """
    
    # Identity
    name: str = Field(..., description="Model name (e.g., 'django-expert')")
    version: str = Field(..., description="Semantic version (e.g., '1.0.0')")
    author: str = Field(..., description="Creator username")
    
    # 🌍 THE AGNOSTIC LAYER
    # This is what makes it work for ANY industry
    domain: str = Field(..., description="Primary domain: finance, legal, code, medical, science, general")
    sub_domain: str = Field(..., description="Specific subdomain (e.g., 'crypto', 'tax', 'react')")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    
    # Technical specs
    base_model: str = Field(..., description="Base model used (e.g., 'mistralai/Mistral-7B-v0.1')")
    lora_rank: int = Field(default=16, description="LoRA rank")
    lora_alpha: int = Field(default=32, description="LoRA alpha")
    
    # Description
    description: str = Field(..., description="What this model does")
    intended_use: str = Field(..., description="Example use case")
    limitations: Optional[str] = Field(None, description="Known limitations")
    
    # Quality metrics
    dataset_size: int = Field(..., description="Number of training examples")
    dataset_hash: str = Field(..., description="SHA256 hash of dataset for verification")
    training_loss: Optional[float] = Field(None, description="Final training loss")
    
    # Metadata
    license: str = Field(default="MIT", description="License")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    huggingface_repo: Optional[str] = Field(None, description="HF repo ID if uploaded")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "sec-filings-expert",
                "version": "1.0.0",
                "author": "tanishq",
                "domain": "finance",
                "sub_domain": "regulatory",
                "tags": ["sec", "10k", "filings"],
                "base_model": "mistralai/Mistral-7B-v0.1",
                "description": "Analyzes SEC 10-K filings",
                "intended_use": "Extract key financial metrics from regulatory documents",
                "dataset_size": 1000,
                "dataset_hash": "a1b2c3..."
            }
        }


# Domain registry - can be extended easily
SUPPORTED_DOMAINS = [
    "finance",     # Stocks, crypto, trading, accounting
    "legal",       # Law, contracts, compliance
    "code",        # Programming, debugging, code generation
    "medical",     # Healthcare, diagnosis, research
    "science",     # Research, papers, analysis
    "general",     # Multi-purpose
]


def create_manifest(
    name: str,
    author: str,
    domain: str,
    sub_domain: str,
    description: str,
    dataset_size: int,
    dataset_hash: str,
    **kwargs
) -> GridManifest:
    """Helper to create a manifest"""
    
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(f"Domain '{domain}' not supported. Choose from: {SUPPORTED_DOMAINS}")
    
    return GridManifest(
        name=name,
        author=author,
        domain=domain,
        sub_domain=sub_domain,
        description=description,
        dataset_size=dataset_size,
        dataset_hash=dataset_hash,
        version=kwargs.get('version', '1.0.0'),
        base_model=kwargs.get('base_model', 'mistralai/Mistral-7B-v0.1'),
        tags=kwargs.get('tags', []),
        intended_use=kwargs.get('intended_use', ''),
        limitations=kwargs.get('limitations', None),
        **kwargs
    )
