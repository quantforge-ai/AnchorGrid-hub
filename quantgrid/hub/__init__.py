"""
QuantGrid Hub - Collective Intelligence Network

The "Hive Mind" - Federated learning infrastructure for community-driven
model improvement.
"""

from quantgrid.hub.registry import QuantGridHub, AdapterMetadata
from quantgrid.hub.evaluation import ProofOfLoss, EvaluationBenchmark
from quantgrid.hub.merging import merge_adapters, ModelSoup
from quantgrid.hub.auth import KeyGenerator, get_current_user, create_api_key_for_user
from quantgrid.hub.submit import prepare_submission

__all__ = [
    # Registry Management
    "QuantGridHub",
    "AdapterMetadata",
    
    # Quality Control
    "ProofOfLoss",
    "EvaluationBenchmark",
    
    # Model Merging
    "merge_adapters",
    "ModelSoup",
    
    # Authentication
    "KeyGenerator",
    "get_current_user",
    "create_api_key_for_user",
    
    # Submission Packaging
    "prepare_submission",
]

__version__ = "0.2.0"
__status__ = "🟢 Hive Mind Active"
