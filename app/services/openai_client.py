# app/services/openai_client.py
"""
OpenAI Client Wrapper

This module provides a wrapper around the OpenAI API client with:
- Error handling and retries
- Rate limiting
- Token counting
- Logging
- Configuration management

Design Patterns:
- Singleton: One client instance per application
- Facade: Simplifies OpenAI API interactions
- Strategy: Different methods for different AI operations

SOLID Principles:
- Single Responsibility: Handles only OpenAI API communication
- Open/Closed: Extensible for new OpenAI features
- Dependency Inversion: Depends on abstractions (config)
"""

import logging
from typing import List, Dict, Optional, Any
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import get_settings

# Configure logger
logger = logging.getLogger(__name__)

settings = get_settings()


class OpenAIClientError(Exception):
    """Base exception for OpenAI client errors."""
    pass


class OpenAIRateLimitError(OpenAIClientError):
    """Raised when rate limit is exceeded."""
    pass


class OpenAIConnectionError(OpenAIClientError):
    """Raised when connection to OpenAI fails."""
    pass


class OpenAIClient:
    """
    Wrapper for OpenAI API client with error handling and retries.
    
    Features:
    - Automatic retries with exponential backoff
    - Rate limiting protection
    - Error handling and logging
    - Token usage tracking
    - Support for chat, vision, and search
    
    Usage:
        client = OpenAIClient()
        response = client.chat(messages=[{"role": "user", "content": "Hello!"}])
    """
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """
        Implement Singleton pattern.
        Only one instance of OpenAIClient exists per application.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize OpenAI client if not already initialized."""
        if self._initialized:
            return
        
        try:
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.OPENAI_TIMEOUT
            )
            self.default_model = settings.OPENAI_MODEL
            self.default_max_tokens = settings.OPENAI_MAX_TOKENS
            self.default_temperature = settings.OPENAI_TEMPERATURE
            self._initialized = True
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise OpenAIClientError(f"Client initialization failed: {e}")
    
    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to config setting)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters for the API
            
        Returns:
            Dict containing response and metadata
            
        Raises:
            OpenAIRateLimitError: When rate limit is exceeded
            OpenAIConnectionError: When connection fails
            OpenAIClientError: For other API errors
        """
        try:
            logger.info(f"Sending chat request with {len(messages)} messages")
            
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                **kwargs
            )
            
            result = {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "model": response.model,
                "tokens_used": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
            
            logger.info(f"Chat response received: {result['tokens_used']} tokens used")
            return result
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise OpenAIRateLimitError("Rate limit exceeded. Please try again later.")
        except APIConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise OpenAIConnectionError("Failed to connect to OpenAI API.")
        except APIError as e:
            logger.error(f"API error: {e}")
            raise OpenAIClientError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise OpenAIClientError(f"Unexpected error: {e}")
    
    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def chat_with_web_search(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat request with web search enabled.
        
        Uses OpenAI's web search tool to fetch current information.
        
        Args:
            messages: List of message dicts
            model: Model to use (must support tools)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing response with web search results
        """
        try:
            logger.info("Sending chat request with web search enabled")
            
            # Use a model that supports web search (gpt-4o or later)
            search_model = model or "gpt-4o-mini"
            
            response = self.client.chat.completions.create(
                model=search_model,
                messages=messages,
                tools=[{"type": "web_search"}],
                **kwargs
            )
            
            # Process web search results if present
            search_results = []
            for choice in response.choices:
                if choice.message.tool_calls:
                    for tool_call in choice.message.tool_calls:
                        if tool_call.type == "web_search":
                            search_results.append(tool_call.function)
            
            result = {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "model": response.model,
                "tokens_used": response.usage.total_tokens,
                "search_results": search_results,
                "finish_reason": response.choices[0].finish_reason
            }
            
            logger.info(f"Web search response received: {len(search_results)} sources found")
            return result
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            # Fallback to regular chat if web search fails
            return self.chat(messages, model, **kwargs)
    
    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def analyze_image(
        self,
        image_url: str,
        prompt: str = "Describe this image in detail",
        model: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Analyze an image using OpenAI's vision capabilities.
        
        Args:
            image_url: URL of the image to analyze
            prompt: Analysis prompt
            model: Model to use (must support vision)
            
        Returns:
            Dict containing analysis and metadata
        """
        try:
            logger.info(f"Analyzing image: {image_url[:50]}...")
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500
            )
            
            result = {
                "analysis": response.choices[0].message.content,
                "model": response.model,
                "tokens_used": response.usage.total_tokens
            }
            
            logger.info("Image analysis complete")
            return result
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            raise OpenAIClientError(f"Image analysis failed: {e}")
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Estimate token count for a text string.
        
        Note: This is an approximation. Actual token count may vary.
        
        Args:
            text: Text to count tokens for
            model: Model name (affects token counting)
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters for English
        # For production, use tiktoken library for accurate counting
        return len(text) // 4
    
    def validate_api_key(self) -> bool:
        """
        Validate that the API key is working.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Make a minimal API call to test the key
            self.client.models.list()
            logger.info("API key validated successfully")
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False


# Create a global instance for easy import
openai_client = OpenAIClient()
