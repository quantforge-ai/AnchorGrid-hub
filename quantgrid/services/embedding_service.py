"""
QuantForge AI Engine - Embedding Service

Generate text embeddings using Ollama (local) or OpenAI (fallback).
Used for vectorizing market data, news, and analysis for RAG.
"""
import asyncio
import httpx
from typing import Optional

from loguru import logger

from quantgrid.core.config import settings


# =============================================================================
# CONFIGURATION
# =============================================================================

# Ollama embedding model (768 dimensions)
OLLAMA_EMBED_MODEL = "nomic-embed-text"
OLLAMA_EMBED_DIMS = 768

# OpenAI fallback (1536 dimensions)
OPENAI_EMBED_MODEL = "text-embedding-3-small"
OPENAI_EMBED_DIMS = 1536


# =============================================================================
# EMBEDDING SERVICE
# =============================================================================

class EmbeddingService:
    """
    Text embedding service for vector search.
    
    Uses Ollama locally (FREE) with OpenAI fallback.
    
    Usage:
        service = EmbeddingService()
        vector = await service.embed("What is NVIDIA's P/E ratio?")
    """
    
    def __init__(
        self,
        ollama_url: str = None,
        openai_api_key: str = None,
    ):
        self.ollama_url = ollama_url or getattr(settings, "OLLAMA_URL", "http://localhost:11434")
        self.openai_api_key = openai_api_key or getattr(settings, "OPENAI_API_KEY", "")
        self._http_client = None
        self._ollama_available = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client
    
    async def _check_ollama(self) -> bool:
        """Check if Ollama is available"""
        if self._ollama_available is not None:
            return self._ollama_available
        
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.ollama_url}/api/tags")
            self._ollama_available = resp.status_code == 200
            
            if self._ollama_available:
                # Check if embedding model is available
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if not any(OLLAMA_EMBED_MODEL in name for name in model_names):
                    logger.warning(f"Ollama model {OLLAMA_EMBED_MODEL} not found. Pull it with: ollama pull {OLLAMA_EMBED_MODEL}")
            
            return self._ollama_available
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            self._ollama_available = False
            return False
    
    # -------------------------------------------------------------------------
    # MAIN EMBEDDING METHODS
    # -------------------------------------------------------------------------
    
    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (768 or 1536 dims depending on model)
        """
        # Try Ollama first (FREE)
        if await self._check_ollama():
            try:
                return await self._embed_ollama(text)
            except Exception as e:
                logger.warning(f"Ollama embedding failed: {e}")
        
        # Fallback to OpenAI
        if self.openai_api_key:
            return await self._embed_openai(text)
        
        # Last resort: return zero vector (not recommended for production)
        logger.error("No embedding service available!")
        return [0.0] * OLLAMA_EMBED_DIMS
    
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # For Ollama, we need to embed one at a time (no batch API)
        if await self._check_ollama():
            results = []
            for text in texts:
                try:
                    vec = await self._embed_ollama(text)
                    results.append(vec)
                except Exception as e:
                    logger.error(f"Ollama batch embed failed: {e}")
                    results.append([0.0] * OLLAMA_EMBED_DIMS)
            return results
        
        # OpenAI supports batch
        if self.openai_api_key:
            return await self._embed_openai_batch(texts)
        
        return [[0.0] * OLLAMA_EMBED_DIMS for _ in texts]
    
    # -------------------------------------------------------------------------
    # OLLAMA IMPLEMENTATION
    # -------------------------------------------------------------------------
    
    async def _embed_ollama(self, text: str) -> list[float]:
        """Generate embedding using Ollama"""
        client = await self._get_client()
        
        resp = await client.post(
            f"{self.ollama_url}/api/embeddings",
            json={
                "model": OLLAMA_EMBED_MODEL,
                "prompt": text,
            },
        )
        resp.raise_for_status()
        
        data = resp.json()
        embedding = data.get("embedding", [])
        
        if not embedding:
            raise ValueError("Empty embedding returned from Ollama")
        
        logger.debug(f"Ollama embedding: {len(text)} chars → {len(embedding)} dims")
        return embedding
    
    # -------------------------------------------------------------------------
    # OPENAI IMPLEMENTATION
    # -------------------------------------------------------------------------
    
    async def _embed_openai(self, text: str) -> list[float]:
        """Generate embedding using OpenAI API"""
        client = await self._get_client()
        
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self.openai_api_key}"},
            json={
                "model": OPENAI_EMBED_MODEL,
                "input": text,
            },
        )
        resp.raise_for_status()
        
        data = resp.json()
        embedding = data["data"][0]["embedding"]
        
        logger.debug(f"OpenAI embedding: {len(text)} chars → {len(embedding)} dims")
        return embedding
    
    async def _embed_openai_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding using OpenAI API"""
        client = await self._get_client()
        
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self.openai_api_key}"},
            json={
                "model": OPENAI_EMBED_MODEL,
                "input": texts,
            },
        )
        resp.raise_for_status()
        
        data = resp.json()
        # Sort by index to maintain order
        embeddings = sorted(data["data"], key=lambda x: x["index"])
        return [e["embedding"] for e in embeddings]
    
    # -------------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------------
    
    def get_dimensions(self) -> int:
        """Get the embedding dimensions for the current model"""
        if self._ollama_available:
            return OLLAMA_EMBED_DIMS
        elif self.openai_api_key:
            return OPENAI_EMBED_DIMS
        return OLLAMA_EMBED_DIMS
    
    async def close(self):
        """Close the HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

embedding_service = EmbeddingService()
