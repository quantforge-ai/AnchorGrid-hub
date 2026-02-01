"""
LLM Router
==========

Intelligent routing with automatic fallback to ensure reliability.
"""

import os
import httpx
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from loguru import logger


class LLMUnavailableError(Exception):
    """Raised when no LLM providers are available"""
    pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Generate completion"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class OllamaProvider(LLMProvider):
    """Local Ollama provider (primary, free)"""
    
    def __init__(self, base_url: str, model: str = "mistral:7b-instruct"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        # Increase timeout for complex local inference
        self.client = httpx.AsyncClient(timeout=90.0)
    
    @property
    def name(self) -> str:
        return "Ollama (Local)"
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Call Ollama API"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                    "stream": False,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
        
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Ping Ollama server"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider (fallback, pay-as-you-go)"""
    
    def __init__(self, api_key: str, model: str = "mistralai/mistral-7b-instruct"):
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    @property
    def name(self) -> str:
        return "OpenRouter"
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Call OpenRouter API"""
        try:
            response = await self.client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check API key validity"""
        return bool(self.api_key)


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (emergency fallback)"""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    @property
    def name(self) -> str:
        return "Anthropic"
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Call Anthropic API"""
        try:
            response = await self.client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["content"][0]["text"]
        
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check API key validity"""
        return bool(self.api_key)


class LLMRouter:
    """
    Intelligent LLM routing with automatic fallback.
    
    Priority order:
    1. Local Ollama (free, private)
    2. OpenRouter (pay-as-you-go)
    3. Anthropic (emergency)
    """
    
    def __init__(self):
        self.providers: List[LLMProvider] = []
        self.current_provider_idx = 0
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers from environment"""
        
        # Primary: Local Ollama
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.providers.append(OllamaProvider(ollama_url))
        
        # Fallback 1: OpenRouter
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            self.providers.append(OpenRouterProvider(openrouter_key))
        
        # Fallback 2: Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.providers.append(AnthropicProvider(anthropic_key))
        
        logger.info(f"Initialized {len(self.providers)} LLM providers")
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Generate completion with automatic fallback"""
        last_error = None
        
        for i, provider in enumerate(self.providers):
            try:
                # Check availability (ping only for Ollama, others check key)
                if not await provider.is_available():
                    logger.warning(f"{provider.name} unavailable, skipping")
                    continue
                
                # Try completion
                logger.info(f"Using {provider.name} for completion")
                response = await provider.complete(
                    prompt, temperature, max_tokens, **kwargs
                )
                
                # Success → Track current provider if it changed
                self.current_provider_idx = i
                return response
            
            except Exception as e:
                last_error = e
                logger.warning(f"{provider.name} failed: {e}")
                
                # Try next provider
                continue
        
        # All providers failed
        raise LLMUnavailableError(
            f"All {len(self.providers)} LLM providers failed. Last error: {last_error}"
        )
