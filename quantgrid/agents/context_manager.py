"""
Conversation Context Manager
=============================

Maintains conversation state across multiple turns.
Enables follow-up questions and symbol tracking.
"""

import re
from typing import List, Dict, Set, Optional
from datetime import datetime
from collections import deque


class ConversationContext:
    """
    Tracks conversation history and extracted entities.
    
    Enables:
    - Multi-turn conversations
    - Follow-up questions
    - Symbol reference tracking
    - Analysis caching
    """
    
    def __init__(self, max_history: int = 5):
        """
        Args:
            max_history: Maximum number of exchanges to remember
        """
        self.history: deque = deque(maxlen=max_history * 2)
        self.symbols_mentioned: Set[str] = set()
        self.last_analysis: Optional[Dict] = None
        self.session_start: datetime = datetime.now()
    
    def add_turn(self, user_query: str, assistant_response: str):
        """
        Store a conversation turn.
        
        Args:
            user_query: User's input
            assistant_response: Agent's response
        """
        self.history.append({
            "role": "user",
            "content": user_query,
            "timestamp": datetime.now()
        })
        self.history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.now()
        })
    
    def extract_symbols(self, text: str) -> List[str]:
        """
        Extract ticker symbols from text.
        
        Args:
            text: Natural language text
        
        Returns:
            List of extracted symbols
        """
        # Match 1-5 uppercase letters, optionally followed by exchange suffix
        pattern = r'\b[A-Z]{1,5}(?:\.[A-Z]{1,3})?\b'
        symbols = re.findall(pattern, text)
        
        # Filter out common words
        stopwords = {
            "I", "A", "US", "AM", "PM", "CEO", "CFO", "CTO",
            "USD", "INR", "EUR", "GBP", "AI", "ML", "API"
        }
        symbols = [s for s in symbols if s not in stopwords]
        
        # Update tracker
        self.symbols_mentioned.update(symbols)
        
        return symbols
    
    def get_context_for_llm(self, max_turns: int = 3) -> str:
        """
        Format conversation history for LLM prompt.
        
        Args:
            max_turns: Maximum number of previous turns to include
        
        Returns:
            Formatted conversation context
        """
        if not self.history:
            return ""
        
        # Get last N exchanges (each exchange = user + assistant)
        recent_history = list(self.history)[-(max_turns * 2):]
        
        lines = ["=== Previous Conversation ==="]
        for turn in recent_history:
            role = turn["role"].capitalize()
            content = turn["content"][:200]  # Truncate long responses
            lines.append(f"{role}: {content}")
        
        # Add symbol context
        if self.symbols_mentioned:
            recent_symbols = list(self.symbols_mentioned)[-5:]
            lines.append(f"\nSymbols discussed: {', '.join(recent_symbols)}")
        
        return "\n".join(lines)
    
    def get_last_symbol(self) -> Optional[str]:
        """Get most recently mentioned symbol"""
        if self.symbols_mentioned:
            # Note: Set is unordered, so this might not literally be the "last" in order of time.
            # But the extract_symbols method updates the set. 
            # In a more robust version we'd use an OrderedSet or a List.
            return list(self.symbols_mentioned)[-1]
        return None
    
    def clear(self):
        """Reset conversation context"""
        self.history.clear()
        self.symbols_mentioned.clear()
        self.last_analysis = None
