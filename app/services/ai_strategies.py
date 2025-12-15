# app/services/ai_strategies.py
"""
AI Service Strategies

Implements the Strategy Pattern for different AI operations.
Each strategy encapsulates a specific AI capability.

Design Patterns:
- Strategy: Different algorithms for different AI tasks
- Dependency Inversion: Strategies depend on abstractions (OpenAI client)

SOLID Principles:
- Single Responsibility: Each strategy does one thing
- Open/Closed: Easy to add new strategies without modifying existing code
- Liskov Substitution: All strategies are interchangeable
- Interface Segregation: Clean, focused interfaces
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.services.openai_client import openai_client, OpenAIClientError

logger = logging.getLogger(__name__)


class AIServiceStrategy(ABC):
    """
    Abstract base class for AI service strategies.
    
    Defines the interface that all AI strategies must implement.
    This follows the Strategy Pattern and enables easy extension.
    """
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the AI service strategy.
        
        Args:
            **kwargs: Strategy-specific parameters
            
        Returns:
            Dict containing strategy results
            
        Raises:
            OpenAIClientError: If the operation fails
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the strategy name."""
        pass


class ChatStrategy(AIServiceStrategy):
    """
    Strategy for tech support chat interactions.
    
    Prompts users for device info and provides intelligent tech support.
    """
    
    def execute(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a tech support chat completion.
        
        Args:
            messages: Conversation history in OpenAI format
            model: Model to use (optional)
            temperature: Sampling temperature (optional)
            max_tokens: Maximum response tokens (optional)
            **kwargs: Additional parameters
            
        Returns:
            Dict with response content and metadata
        """
        logger.info(f"Executing tech support chat strategy with {len(messages)} messages")
        
        # Add system message for tech support context
        tech_support_system = {
            "role": "system",
            "content": """You are AsisTech AI, an expert technical support assistant. 

When a user first describes a problem:
1. Ask for the device make and model (e.g., "HP LaserJet Pro M404", "iPhone 14 Pro", "Dell XPS 15", "PlayStation 5")
2. Ask for the operating system/firmware version if relevant
3. Ask specific clarifying questions about the issue

Provide solutions in this order:
1. Quick fixes and common solutions
2. Diagnostic steps the user can perform
3. Advanced troubleshooting
4. When to seek professional help

Always be friendly, clear, and patient. Use simple language and step-by-step instructions."""
        }
        
        # Prepend system message if not already there
        if not messages or messages[0].get("role") != "system":
            messages = [tech_support_system] + messages
        
        try:
            response = openai_client.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            logger.info(f"Tech support chat completed: {response['tokens_used']} tokens used")
            return {
                "success": True,
                "content": response["content"],
                "role": response["role"],
                "model": response["model"],
                "tokens_used": response["tokens_used"],
                "finish_reason": response["finish_reason"]
            }
            
        except OpenAIClientError as e:
            logger.error(f"Chat strategy failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "I encountered an error processing your request. Please try again."
            }
    
    def get_name(self) -> str:
        return "chat"


class WebSearchStrategy(AIServiceStrategy):
    """
    Strategy for web search-enabled chat.
    
    Uses OpenAI's web search capability to fetch current information.
    """
    
    def execute(
        self,
        query: str,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a web search query.
        
        Args:
            query: Search query
            messages: Optional conversation context
            model: Model to use (must support web search)
            **kwargs: Additional parameters
            
        Returns:
            Dict with search results and AI summary
        """
        logger.info(f"Executing web search strategy for: {query[:50]}...")
        
        try:
            # Build messages for web search
            if messages is None:
                messages = []
            
            # Add the search query as the latest message
            search_messages = messages + [
                {"role": "user", "content": f"Search the web for: {query}"}
            ]
            
            response = openai_client.chat_with_web_search(
                messages=search_messages,
                model=model,
                **kwargs
            )
            
            logger.info(f"Web search completed: {len(response.get('search_results', []))} sources found")
            return {
                "success": True,
                "query": query,
                "content": response["content"],
                "search_results": response.get("search_results", []),
                "model": response["model"],
                "tokens_used": response["tokens_used"]
            }
            
        except OpenAIClientError as e:
            logger.error(f"Web search strategy failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "content": "I couldn't complete the web search. Please try again."
            }
    
    def get_name(self) -> str:
        return "web_search"


class ImageAnalysisStrategy(AIServiceStrategy):
    """
    Strategy for image analysis using vision capabilities.
    
    Analyzes images and generates descriptions or answers questions about them.
    """
    
    def execute(
        self,
        image_url: str,
        prompt: str = "Describe this image in detail",
        model: str = "gpt-4o-mini",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute image analysis.
        
        Args:
            image_url: URL of the image to analyze
            prompt: Analysis prompt
            model: Model to use (must support vision)
            **kwargs: Additional parameters
            
        Returns:
            Dict with analysis results
        """
        logger.info(f"Executing image analysis strategy")
        
        try:
            response = openai_client.analyze_image(
                image_url=image_url,
                prompt=prompt,
                model=model
            )
            
            logger.info("Image analysis completed")
            return {
                "success": True,
                "analysis": response["analysis"],
                "model": response["model"],
                "tokens_used": response["tokens_used"],
                "image_url": image_url
            }
            
        except OpenAIClientError as e:
            logger.error(f"Image analysis strategy failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis": "I couldn't analyze the image. Please check the URL and try again."
            }
    
    def get_name(self) -> str:
        return "image_analysis"


class CodeAssistantStrategy(AIServiceStrategy):
    """
    Strategy for code-related assistance.
    
    Specialized for programming questions, code review, and debugging.
    """
    
    def execute(
        self,
        code_query: str,
        code_context: Optional[str] = None,
        language: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute code assistance.
        
        Args:
            code_query: The coding question or request
            code_context: Optional code snippet for context
            language: Programming language (optional)
            messages: Optional conversation history
            **kwargs: Additional parameters
            
        Returns:
            Dict with code assistance response
        """
        logger.info("Executing code assistant strategy")
        
        try:
            # Build specialized prompt for code assistance
            system_message = {
                "role": "system",
                "content": "You are an expert programming assistant. Provide clear, accurate code help with explanations."
            }
            
            user_content = code_query
            if code_context:
                user_content = f"{code_query}\n\nCode context:\n```{language or ''}\n{code_context}\n```"
            
            # Build message list
            if messages is None:
                messages = [system_message]
            else:
                messages = [system_message] + messages
            
            messages.append({"role": "user", "content": user_content})
            
            response = openai_client.chat(
                messages=messages,
                temperature=0.2,  # Lower temperature for more precise code
                **kwargs
            )
            
            logger.info("Code assistance completed")
            return {
                "success": True,
                "content": response["content"],
                "model": response["model"],
                "tokens_used": response["tokens_used"],
                "language": language
            }
            
        except OpenAIClientError as e:
            logger.error(f"Code assistant strategy failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "I couldn't assist with the code. Please try again."
            }
    
    def get_name(self) -> str:
        return "code_assistant"


class YouTubeSearchStrategy(AIServiceStrategy):
    """
    Strategy for searching YouTube for tech solutions.
    
    Searches YouTube and provides video recommendations for tech problems.
    """
    
    def execute(
        self,
        problem_description: str,
        device_info: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search YouTube for tech solution videos.
        
        Args:
            problem_description: Description of the tech problem
            device_info: Make and model of device
            **kwargs: Additional parameters
            
        Returns:
            Dict with YouTube search results and AI summary
        """
        logger.info(f"Executing YouTube search strategy for: {problem_description}")
        
        try:
            from app.core.config import settings
            import requests
            import urllib.parse
            
            # Build search query
            search_query = problem_description
            if device_info:
                search_query = f"{device_info} {problem_description} fix tutorial"
            
            videos = []
            
            # If YouTube API key is available, fetch actual videos
            if settings.YOUTUBE_API_KEY and settings.YOUTUBE_API_KEY != "YOUR_YOUTUBE_API_KEY_HERE":
                try:
                    # Call YouTube Data API
                    youtube_api_url = "https://www.googleapis.com/youtube/v3/search"
                    params = {
                        "part": "snippet",
                        "q": search_query,
                        "type": "video",
                        "maxResults": 5,
                        "order": "relevance",
                        "key": settings.YOUTUBE_API_KEY,
                        "videoDuration": "medium",  # 4-20 minutes
                        "videoDefinition": "any"
                    }
                    
                    response = requests.get(youtube_api_url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract video info
                    if "items" in data:
                        for item in data["items"]:
                            video_id = item["id"]["videoId"]
                            snippet = item["snippet"]
                            videos.append({
                                "title": snippet["title"],
                                "url": f"https://www.youtube.com/watch?v={video_id}",
                                "thumbnail": snippet["thumbnails"]["medium"]["url"],
                                "channel": snippet["channelTitle"],
                                "description": snippet["description"][:200] + "..."
                            })
                    
                except Exception as api_error:
                    logger.warning(f"YouTube API failed, falling back: {api_error}")
            
            # Use AI to analyze and recommend the best videos
            if videos:
                video_list = "\n".join([f"{i+1}. {v['title']} by {v['channel']}\n   URL: {v['url']}" for i, v in enumerate(videos)])
                
                messages = [
                    {
                        "role": "system",
                        "content": "You are a tech support assistant. Review these YouTube videos and recommend the most helpful ones for solving the user's problem. Be specific about which videos to watch first."
                    },
                    {
                        "role": "user",
                        "content": f"Device: {device_info or 'Not specified'}\nProblem: {problem_description}\n\nFound these YouTube videos:\n{video_list}\n\nWhich videos should the user watch? Provide a brief explanation."
                    }
                ]
                
                ai_response = openai_client.chat(messages=messages, temperature=0.5, **kwargs)
                
                # Format response with video links
                content = f"🎥 **YouTube Video Recommendations:**\n\n{ai_response['content']}\n\n**Videos Found:**\n"
                for i, video in enumerate(videos, 1):
                    content += f"\n{i}. **[{video['title']}]({video['url']})**\n   Channel: {video['channel']}\n"
                
                return {
                    "success": True,
                    "content": content,
                    "videos": videos,
                    "search_query": search_query,
                    "youtube_url": videos[0]["url"] if videos else None,
                    "tokens_used": ai_response.get("tokens_used")
                }
            else:
                # Fallback to search URL if API key not available
                youtube_search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(search_query)}"
                
                messages = [
                    {
                        "role": "system",
                        "content": "You are a tech support assistant helping users find YouTube tutorials. Provide guidance on what to search for and what to look for in videos."
                    },
                    {
                        "role": "user",
                        "content": f"Device: {device_info or 'Not specified'}\nProblem: {problem_description}\n\nProvide search guidance for finding YouTube tutorials."
                    }
                ]
                
                ai_response = openai_client.chat(messages=messages, **kwargs)
                
                return {
                    "success": True,
                    "content": f"{ai_response['content']}\n\n🔍 **[Click here to search YouTube]({youtube_search_url})**\n\nSearch Query: `{search_query}`",
                    "search_query": search_query,
                    "youtube_url": youtube_search_url,
                    "tokens_used": ai_response.get("tokens_used")
                }
            
        except OpenAIClientError as e:
            logger.error(f"YouTube search strategy failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "I couldn't generate YouTube search suggestions. Please try searching YouTube directly."
            }
    
    def get_name(self) -> str:
        return "youtube_search"


class DeviceDiagnosticStrategy(AIServiceStrategy):
    """
    Strategy for running local device diagnostics.
    
    Provides diagnostic commands and checks the user can run locally.
    """
    
    def execute(
        self,
        device_type: str,
        device_info: Optional[str] = None,
        operating_system: Optional[str] = None,
        problem_description: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate diagnostic steps for the device.
        
        Args:
            device_type: Type of device (printer, phone, pc, console, etc.)
            device_info: Make and model
            operating_system: OS/firmware version
            problem_description: What's wrong
            **kwargs: Additional parameters
            
        Returns:
            Dict with diagnostic steps and commands
        """
        logger.info(f"Executing device diagnostic strategy for {device_type}")
        
        try:
            diagnostic_prompt = f"""Generate comprehensive diagnostic steps for:
Device Type: {device_type}
Device: {device_info or 'Not specified'}
Operating System: {operating_system or 'Not specified'}
Problem: {problem_description or 'General diagnostics'}

Provide:
1. **Quick Checks** (things to verify immediately)
2. **Diagnostic Commands** (specific commands/tests to run)
3. **Built-in Diagnostic Tools** (how to access device's own diagnostics)
4. **What to Look For** (error messages, indicators, patterns)
5. **Safety Warnings** (if any)

Format the response with clear steps the user can follow."""

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert device diagnostics specialist. Provide clear, actionable diagnostic steps that users can perform themselves. Include specific commands, button combinations, and built-in diagnostic tools."
                },
                {
                    "role": "user",
                    "content": diagnostic_prompt
                }
            ]
            
            response = openai_client.chat(messages=messages, temperature=0.3, **kwargs)
            
            return {
                "success": True,
                "content": f"## 🔧 Diagnostic Steps for {device_info or device_type}\n\n{response['content']}",
                "device_type": device_type,
                "tokens_used": response["tokens_used"]
            }
            
        except OpenAIClientError as e:
            logger.error(f"Device diagnostic strategy failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "I couldn't generate diagnostic steps. Please check your device's manual for built-in diagnostic options."
            }
    
    def get_name(self) -> str:
        return "device_diagnostic"


# Factory for creating strategies
class AIStrategyFactory:
    """
    Factory for creating AI strategy instances.
    
    Implements Factory Pattern for strategy creation.
    """
    
    _strategies = {
        "chat": ChatStrategy,
        "web_search": WebSearchStrategy,
        "image_analysis": ImageAnalysisStrategy,
        "code_assistant": CodeAssistantStrategy,
        "youtube_search": YouTubeSearchStrategy,
        "device_diagnostic": DeviceDiagnosticStrategy
    }
    
    @classmethod
    def create(cls, strategy_name: str) -> AIServiceStrategy:
        """
        Create a strategy instance by name.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Strategy instance
            
        Raises:
            ValueError: If strategy name is unknown
        """
        strategy_class = cls._strategies.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        return strategy_class()
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: type):
        """
        Register a new strategy.
        
        This allows for runtime extension of available strategies.
        
        Args:
            name: Strategy name
            strategy_class: Strategy class
        """
        cls._strategies[name] = strategy_class
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """Get list of available strategy names."""
        return list(cls._strategies.keys())
