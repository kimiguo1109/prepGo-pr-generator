"""Gemini API client with connection pooling and retry logic for multi-user support."""
import asyncio
import logging
from typing import AsyncGenerator, Optional
from functools import lru_cache

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for Google Gemini API with support for concurrent requests.
    Uses a single client instance with retry logic for reliability.
    """
    
    _client: genai.Client = None
    _lock = asyncio.Lock()
    _request_semaphore: asyncio.Semaphore = None
    _max_concurrent_requests = 10  # Limit concurrent API calls
    
    # Retry configuration
    _max_retries = 3
    _retry_delay = 2  # seconds
    _retry_backoff = 2  # exponential backoff multiplier
    
    @classmethod
    async def _ensure_initialized(cls):
        """Initialize client and semaphore if needed."""
        if cls._request_semaphore is None:
            cls._request_semaphore = asyncio.Semaphore(cls._max_concurrent_requests)
    
    @classmethod
    def _get_client(cls) -> genai.Client:
        """Get or create Gemini client (thread-safe singleton)."""
        if cls._client is None:
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not configured")
            cls._client = genai.Client(api_key=settings.gemini_api_key)
            logger.info("Gemini client initialized")
        return cls._client
    
    @classmethod
    async def generate_content_stream(
        cls, 
        prompt: str,
        model: str = None,
        request_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate content with streaming response.
        Includes retry logic and rate limiting for multi-user support.
        """
        await cls._ensure_initialized()
        
        client = cls._get_client()
        model = model or settings.gemini_model
        
        # Acquire semaphore to limit concurrent requests
        async with cls._request_semaphore:
            logger.info(f"Starting generation for request {request_id or 'unknown'}")
            
            last_error = None
            
            for attempt in range(cls._max_retries):
                try:
                    # Run synchronous API call in thread pool
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.7,
                                max_output_tokens=65536,
                            )
                        )
                    )
                    
                    # Yield the response text in chunks for streaming effect
                    if response.text:
                        text = response.text
                        chunk_size = 200
                        total_len = len(text)
                        
                        for i in range(0, total_len, chunk_size):
                            yield text[i:i + chunk_size]
                            await asyncio.sleep(0.1)  # Smoother streaming
                        
                        logger.info(f"Completed generation for request {request_id or 'unknown'} ({total_len} chars)")
                        return
                    else:
                        logger.warning(f"Empty response for request {request_id}")
                        return
                        
                except Exception as e:
                    last_error = e
                    logger.error(f"Attempt {attempt + 1}/{cls._max_retries} failed: {e}")
                    
                    if attempt < cls._max_retries - 1:
                        delay = cls._retry_delay * (cls._retry_backoff ** attempt)
                        logger.info(f"Retrying in {delay}s...")
                        await asyncio.sleep(delay)
            
            # All retries failed
            raise Exception(f"Gemini API error after {cls._max_retries} attempts: {str(last_error)}")
    
    @classmethod
    async def generate_content(
        cls, 
        prompt: str, 
        model: str = None,
        request_id: str = None
    ) -> str:
        """Generate content (non-streaming) with retry logic."""
        await cls._ensure_initialized()
        
        client = cls._get_client()
        model = model or settings.gemini_model
        
        async with cls._request_semaphore:
            logger.info(f"Starting non-streaming generation for request {request_id or 'unknown'}")
            
            last_error = None
            
            for attempt in range(cls._max_retries):
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.7,
                                max_output_tokens=65536,
                            )
                        )
                    )
                    
                    result = response.text or ""
                    logger.info(f"Completed non-streaming generation ({len(result)} chars)")
                    return result
                    
                except Exception as e:
                    last_error = e
                    logger.error(f"Attempt {attempt + 1}/{cls._max_retries} failed: {e}")
                    
                    if attempt < cls._max_retries - 1:
                        delay = cls._retry_delay * (cls._retry_backoff ** attempt)
                        await asyncio.sleep(delay)
            
            raise Exception(f"Gemini API error after {cls._max_retries} attempts: {str(last_error)}")
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get client statistics for monitoring."""
        return {
            "initialized": cls._client is not None,
            "max_concurrent_requests": cls._max_concurrent_requests,
            "model": settings.gemini_model
        }
    
    @classmethod
    def set_max_concurrent(cls, max_concurrent: int):
        """Update maximum concurrent requests."""
        if max_concurrent >= 1:
            cls._max_concurrent_requests = max_concurrent
            cls._request_semaphore = asyncio.Semaphore(max_concurrent)
            logger.info(f"Max concurrent Gemini requests set to {max_concurrent}")
