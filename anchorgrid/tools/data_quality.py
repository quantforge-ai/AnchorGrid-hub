"""
Data Quality Filter
===================

Utility to filter and validate training examples for the LLM fine-tuning dataset.
Ensures we don't train on hallucinations or low-information data.
"""

import re
from typing import List, Dict, Any
from loguru import logger


class DataQualityFilter:
    """
    Automated filters for financial instruction datasets.
    """
    
    def __init__(self):
        # Minimum lengths for meaningful training
        self.min_input_len = 50
        self.min_output_len = 100
        
        # Blacklisted patterns (e.g. "I don't know", "Error", etc.)
        self.blacklist = [
            r"unable to fetch",
            r"data not available",
            r"technical error",
            r"sorry, but i can't",
            r"i don't have access to real-time data", # Ironically, we want to filter this since we DO have it
        ]

    def is_high_quality(self, example: Dict[str, str]) -> bool:
        """
        Check if an instruction-following example is high quality.
        """
        instr = example.get("instruction", "")
        inp = example.get("input", "")
        out = example.get("output", "")
        
        # 1. Length Check
        if len(inp) < self.min_input_len or len(out) < self.min_output_len:
            return False
        
        # 2. Blacklist Check
        for pattern in self.blacklist:
            if re.search(pattern, out.lower()) or re.search(pattern, inp.lower()):
                return False
        
        # 3. Financial Content Check
        # Ensure it contains numbers or tickers
        ticker_match = re.search(r'\b[A-Z]{1,5}\b', inp)
        price_match = re.search(r'\d+\.\d+', out)
        
        if not (ticker_match and price_match):
            return False
            
        return True

    def filter_dataset(self, examples: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Filter a list of examples"""
        before_count = len(examples)
        filtered = [ex for ex in examples if self.is_high_quality(ex)]
        after_count = len(filtered)
        
        logger.info(f"Quality Filter: Processed {before_count} examples. {after_count} kept ({after_count/before_count:.1%}).")
        return filtered
