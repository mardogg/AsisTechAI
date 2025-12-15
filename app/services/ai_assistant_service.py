# app/services/ai_assistant_service.py
"""
AI Assistant Service

Orchestrates AI operations, manages conversations, and coordinates between
the OpenAI client, repositories, and strategies.

Design Patterns:
- Facade: Simplifies complex AI interactions
- Service Layer: Encapsulates business logic
- Repository: Data access abstraction

SOLID Principles:
- Single Responsibility: Manages AI assistant operations
- Dependency Inversion: Depends on abstractions (repositories, strategies)
- Open/Closed: Extensible through strategies
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message, MessageRole, ConversationStatus
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.ai_strategies import AIStrategyFactory, OpenAIClientError
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AIAssistantService:
    """
    Service for managing AI assistant operations.
    
    Coordinates between:
    - AI strategies (chat, search, analysis)
    - Conversation management
    - Message storage
    - Token tracking
    """
    
    def __init__(self, db: Session):
        """
        Initialize AI assistant service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.strategy_factory = AIStrategyFactory()
    
    def chat(
        self,
        user_id: UUID,
        message_content: str,
        conversation_id: Optional[UUID] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Handle a chat message from the user.
        
        Args:
            user_id: User UUID
            message_content: User's message
            conversation_id: Existing conversation ID (optional)
            model: OpenAI model to use (optional)
            temperature: Sampling temperature (optional)
            max_tokens: Max response tokens (optional)
            
        Returns:
            Dict with conversation, user message, and AI response
        """
        logger.info(f"Processing chat for user {user_id}")
        
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(user_id, conversation_id)
            
            # Create user message
            user_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=message_content
            )
            self.db.add(user_message)
            conversation.increment_message_count()
            
            # Get conversation context
            context = self.message_repo.get_conversation_context(
                conversation.id,
                max_messages=settings.MAX_CONVERSATION_HISTORY
            )
            
            # Add current message to context
            context.append({"role": "user", "content": message_content})
            
            # Execute chat strategy
            chat_strategy = self.strategy_factory.create("chat")
            response = chat_strategy.execute(
                messages=context,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if not response.get("success"):
                raise Exception(response.get("error", "Unknown error"))
            
            # Create assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=response["content"],
                token_count=response.get("tokens_used"),
                extra_data={
                    "model": response["model"],
                    "finish_reason": response.get("finish_reason")
                }
            )
            self.db.add(assistant_message)
            conversation.increment_message_count()
            
            # Auto-generate conversation title if it's the first exchange
            if conversation.message_count == 2 and conversation.title == "New Conversation":
                conversation.title = self._generate_conversation_title(message_content)
            
            self.db.commit()
            self.db.refresh(user_message)
            self.db.refresh(assistant_message)
            self.db.refresh(conversation)
            
            logger.info(f"Chat completed: {response.get('tokens_used', 0)} tokens")
            
            return {
                "conversation_id": conversation.id,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "tokens_used": response.get("tokens_used"),
                "model": response["model"]
            }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            self.db.rollback()
            raise Exception(f"Chat failed: {e}")
    
    def web_search(
        self,
        user_id: UUID,
        query: str,
        conversation_id: Optional[UUID] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a web search and return results with AI summary.
        
        Args:
            user_id: User UUID
            query: Search query
            conversation_id: Existing conversation ID (optional)
            model: OpenAI model to use (optional)
            
        Returns:
            Dict with search results and summary
        """
        logger.info(f"Processing web search for user {user_id}")
        
        if not settings.ENABLE_WEB_SEARCH:
            raise Exception("Web search is disabled")
        
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(user_id, conversation_id)
            
            # Create user message
            user_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=f"[Web Search] {query}"
            )
            self.db.add(user_message)
            conversation.increment_message_count()
            
            # Get conversation context
            context = self.message_repo.get_conversation_context(
                conversation.id,
                max_messages=10  # Shorter context for searches
            )
            
            # Execute web search strategy
            search_strategy = self.strategy_factory.create("web_search")
            response = search_strategy.execute(
                query=query,
                messages=context,
                model=model or "gpt-4o-mini"
            )
            
            if not response.get("success"):
                raise Exception(response.get("error", "Search failed"))
            
            # Create assistant message with search results
            assistant_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=response["content"],
                token_count=response.get("tokens_used"),
                extra_data={
                    "search_query": query,
                    "search_results": response.get("search_results", []),
                    "model": response["model"]
                }
            )
            self.db.add(assistant_message)
            conversation.increment_message_count()
            
            self.db.commit()
            self.db.refresh(conversation)
            
            logger.info(f"Web search completed: {len(response.get('search_results', []))} sources")
            
            return {
                "conversation_id": conversation.id,
                "query": query,
                "results": response.get("search_results", []),
                "summary": response["content"],
                "tokens_used": response.get("tokens_used")
            }
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            self.db.rollback()
            raise Exception(f"Web search failed: {e}")
    
    def analyze_image(
        self,
        user_id: UUID,
        image_url: str,
        prompt: str = "Describe this image in detail",
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Analyze an image using vision AI.
        
        Args:
            user_id: User UUID
            image_url: URL of image to analyze
            prompt: Analysis prompt
            conversation_id: Existing conversation ID (optional)
            
        Returns:
            Dict with analysis results
        """
        logger.info(f"Processing image analysis for user {user_id}")
        
        if not settings.ENABLE_IMAGE_ANALYSIS:
            raise Exception("Image analysis is disabled")
        
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(user_id, conversation_id)
            
            # Create user message
            user_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=f"[Image Analysis] {prompt}",
                extra_data={"image_url": image_url}
            )
            self.db.add(user_message)
            conversation.increment_message_count()
            
            # Execute image analysis strategy
            analysis_strategy = self.strategy_factory.create("image_analysis")
            response = analysis_strategy.execute(
                image_url=image_url,
                prompt=prompt
            )
            
            if not response.get("success"):
                raise Exception(response.get("error", "Analysis failed"))
            
            # Create assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=response["analysis"],
                token_count=response.get("tokens_used"),
                extra_data={
                    "image_url": image_url,
                    "model": response["model"]
                }
            )
            self.db.add(assistant_message)
            conversation.increment_message_count()
            
            self.db.commit()
            self.db.refresh(conversation)
            
            logger.info("Image analysis completed")
            
            return {
                "conversation_id": conversation.id,
                "analysis": response["analysis"],
                "tokens_used": response.get("tokens_used"),
                "image_url": image_url
            }
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            self.db.rollback()
            raise Exception(f"Image analysis failed: {e}")
    
    def get_conversation(
        self,
        user_id: UUID,
        conversation_id: UUID,
        include_messages: bool = True
    ) -> Optional[Conversation]:
        """
        Get a conversation with optional messages.
        
        Args:
            user_id: User UUID
            conversation_id: Conversation UUID
            include_messages: Whether to include messages
            
        Returns:
            Conversation or None
        """
        return self.conversation_repo.get_by_user_and_id(user_id, conversation_id)
    
    def list_conversations(
        self,
        user_id: UUID,
        status: Optional[ConversationStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        """
        List user's conversations.
        
        Args:
            user_id: User UUID
            status: Filter by status (optional)
            skip: Pagination offset
            limit: Max results
            
        Returns:
            List of conversations
        """
        return self.conversation_repo.get_by_user(user_id, status, skip, limit)
    
    def delete_conversation(
        self,
        user_id: UUID,
        conversation_id: UUID
    ) -> bool:
        """
        Delete a conversation.
        
        Args:
            user_id: User UUID
            conversation_id: Conversation UUID
            
        Returns:
            True if deleted
        """
        return self.conversation_repo.delete_conversation(conversation_id, user_id)
    
    def _get_or_create_conversation(
        self,
        user_id: UUID,
        conversation_id: Optional[UUID]
    ) -> Conversation:
        """
        Get existing conversation or create new one.
        
        Args:
            user_id: User UUID
            conversation_id: Existing conversation ID (optional)
            
        Returns:
            Conversation instance
        """
        if conversation_id:
            conversation = self.conversation_repo.get_by_user_and_id(user_id, conversation_id)
            if conversation:
                return conversation
        
        # Create new conversation
        conversation = Conversation(
            user_id=user_id,
            title="New Conversation",
            status=ConversationStatus.ACTIVE
        )
        self.db.add(conversation)
        self.db.flush()  # Get ID without committing
        return conversation
    
    def _generate_conversation_title(self, first_message: str) -> str:
        """
        Generate a conversation title from the first message.
        
        Args:
            first_message: First user message
            
        Returns:
            Generated title
        """
        # Simple title generation - take first 50 chars
        title = first_message[:50]
        if len(first_message) > 50:
            title += "..."
        return title
