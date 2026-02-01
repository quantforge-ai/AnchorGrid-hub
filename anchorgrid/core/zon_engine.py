"""
ZON Engine
==========

Handles transition between JSON and ZON (Zero Overhead Notation).
Optimizes data payloads for token efficiency.
"""

import json
from typing import Any, Dict, List, Union
from loguru import logger


class ZONEngine:
    """
    Core engine for ZON-based data compression.
    
    Implements:
    - Tabular encoding for arrays of objects
    - Dot-notation flattening for nested objects
    - Token-efficient primitive mapping
    """
    
    def encode(self, data: Any) -> str:
        """
        Generic ZON encoder.
        
        Logic:
        - If List[Dict], use @table format.
        - If Dict, use flattened dot-notation.
        - Else, return string representation.
        """
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return self.encode_table(data)
        elif isinstance(data, dict):
            return self.encode_object(data)
        return str(data)

    def encode_quote(self, quote: Dict[str, Any]) -> str:
        """Specialized encoder for market quotes"""
        # Compact representation: ticker:price:change:time
        t = quote.get("ticker", "NULL")
        p = quote.get("price", 0)
        c = quote.get("change_percent", 0)
        return f"{t}:{p}:{c:.2f}%"

    def encode_signals(self, signals: Dict[str, Any]) -> str:
        """Specialized encoder for technical signals"""
        # Flattened format: rsi:X|macd:Y|regime:Z
        parts = []
        for key in ["rsi", "macd", "bollinger_position", "atr"]:
            if key in signals:
                parts.append(f"{key}:{signals[key]}")
        
        regime = signals.get("regime", {})
        if isinstance(regime, dict):
            for k, v in regime.items():
                parts.append(f"regime.{k}:{v}")
        
        return "|".join(parts)

    def encode_table(self, data: List[Dict[str, Any]]) -> str:
        """Encode a list of objects as a ZON table"""
        if not data:
            return ""
        
        headers = list(data[0].keys())
        header_str = ",".join(headers)
        
        rows = []
        for item in data:
            row = [str(item.get(h, "")) for h in headers]
            rows.append(",".join(row))
        
        return f"@count:{len(data)}\n{header_str}\n" + "\n".join(rows)

    def encode_object(self, data: Dict[str, Any], prefix: str = "") -> str:
        """Flatten nested object using dot notation"""
        parts = []
        for k, v in data.items():
            key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
            if isinstance(v, dict):
                parts.append(self.encode_object(v, key))
            else:
                # Use T/F for booleans to save tokens
                if isinstance(v, bool):
                    v = "T" if v else "F"
                parts.append(f"{key}:{v}")
        return "|".join(parts)

    def decode(self, zon_str: str) -> Any:
        """
        Generic ZON decoder (Basic implementation).
        In production, this would use a full parser.
        """
        # Implementation depends on response format needed
        # For now, we mainly use ZON for input (compression)
        return zon_str
