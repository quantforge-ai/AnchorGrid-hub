"""
AnchorGrid Universal Engine - The Cortex

This is the "Intel Chip" of the Universal Intelligence Protocol.
It doesn't know about stocks, cancer, or contracts - it just knows how to REASON.

Any plugin can use this engine to process data and generate insights.

Privacy First:
- Runs 100% locally via Ollama (no API calls)
- Your data never leaves your machine
- No usage tracking, no centralized logging
"""

import os
from typing import Optional, List, Dict, Any
from loguru import logger

try:
    from langchain_community.chat_models import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.callbacks import BaseCallbackHandler
    
    class StreamingPrinter(BaseCallbackHandler):
        """
        Makes the terminal feel alive by printing tokens as they arrive.
        Creates the "ChatGPT streaming" effect for local models.
        """
        def on_llm_new_token(self, token: str, **kwargs) -> None:
            print(token, end="", flush=True)
    
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseCallbackHandler = object  # Dummy for type hints
    logger.warning("LangChain not installed. Engine will be limited.")


class UniversalEngine:
    """
    The Cortex - Universal Reasoning Engine
    
    Wraps a local LLM (Ollama) to provide reasoning capabilities to ANY plugin.
    - Finance Plugin: Analyzes stock data
    - Medical Plugin: Interprets DICOM scans
    - Legal Plugin: Reviews contracts
    - Code Plugin: Audits smart contracts
    
    All using the same underlying "brain" - just different data contexts.
    """
    
    def __init__(self, model_name: str = "phi"):
        """
        Initialize the Universal Engine.
        
        Args:
            model_name: Ollama model to use (phi, llama3, mistral, etc.)
                       phi = 2.7B params, fast, low RAM (~3GB)
                       llama3 = 8B params, smarter, high RAM (~8GB)
        """
        self.model_name = model_name
        self.available = False
        
        if not LANGCHAIN_AVAILABLE:
            logger.error("❌ LangChain not installed. Engine disabled.")
            logger.info("Install with: pip install langchain langchain-community")
            return
        
        try:
            self.llm = ChatOllama(
                model=model_name,
                temperature=0.2,  # Keep it factual (not creative)
                callbacks=[StreamingPrinter()]
            )
            self.available = True
            logger.info(f"🧠 Universal Engine initialized: {model_name} (Local/Private)")
        except Exception as e:
            logger.error(f"❌ Engine initialization failed: {e}")
            logger.info("Make sure Ollama is running: ollama serve")
            logger.info(f"And you have the model: ollama pull {model_name}")

    def think(self, prompt: str, context: str = "", domain: str = "general") -> str:
        """
        Pure reasoning with domain-specific data.
        
        This is domain-agnostic - the engine doesn't know if it's analyzing
        stocks, medical scans, or legal documents. It just reasons over data.
        
        Args:
            prompt: The user's question
            context: Real-time data from the plugin (e.g., stock prices, scan results)
            domain: Plugin domain for logging (finance, medical, legal, etc.)
        
        Returns:
            Reasoned response from the local LLM
        """
        if not self.available:
            return "❌ Engine offline. Install LangChain and start Ollama."
        
        # Build the system prompt
        system_prompt = (
            f"You are a specialized AnchorGrid Agent running 100% locally on the user's hardware. "
            f"You are analyzing data from the '{domain}' domain plugin.\n\n"
            "You have access to the following real-time data:\n\n"
            f"{context}\n\n"
            "Analyze this data and answer the user's request. "
            "Be precise, professional, and cite specific numbers from the data. "
            "If the data is insufficient, say so honestly."
        )
        
        try:
            logger.info(f"🧠 Engine processing {domain} query...")
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Stream the response token-by-token (ChatGPT effect)
            response = self.llm.invoke(messages)
            print("\n")  # Newline after streaming completes
            
            return response.content
            
        except Exception as e:
            error_msg = f"❌ Engine Error: {str(e)}"
            logger.error(error_msg)
            
            # Helpful error messages
            if "connection" in str(e).lower():
                return f"{error_msg}\n\n💡 Is Ollama running? Start with: ollama serve"
            elif "not found" in str(e).lower():
                return f"{error_msg}\n\n💡 Model not installed? Run: ollama pull {self.model_name}"
            else:
                return error_msg

    def is_available(self) -> bool:
        """Check if the engine is ready to use"""
        return self.available


# ============================================================================
# Singleton Instance - "The CPU is Always On"
# ============================================================================

# Create one global engine instance that all plugins share
# This is efficient - no need to reload the model for each query

try:
    engine = UniversalEngine()
    if engine.is_available():
        logger.info("✅ Global Engine ready for all plugins")
    else:
        logger.warning("⚠️  Engine created but not available (check dependencies)")
except Exception as e:
    logger.error(f"❌ Failed to create global engine: {e}")
    # Create a dummy engine that explains the error
    class DummyEngine:
        def think(self, prompt, context="", domain="general"):
            return "❌ Engine not available. Install dependencies: pip install langchain langchain-community"
        def is_available(self):
            return False
    
    engine = DummyEngine()
