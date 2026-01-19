"""
QuantGrid ML - Prediction Models & Training Infrastructure

Phase 8: Custom ML models for financial prediction and community training.
"""

__all__ = []

# Optional: Heavy ML dependencies only loaded when needed
try:
    from quantgrid.ml.trainer import QuantGridTrainer
    __all__.append("QuantGridTrainer")
except ImportError:
    pass

try:
    from quantgrid.ml.financial_mistral import Financialистral
    __all__.append("FinancialMistral")
except ImportError:
    pass
