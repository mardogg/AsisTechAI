# app/repositories/message_repository.py
"""
Message Repository

Handles all database operations related to messages.
Follows Repository Pattern and Single Responsibility Principle.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from uuid import UUID
from app.models.conversation import Message, MessageRole
from app.repositories import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message entities.
    
    Provides specialized methods for message-related database operations.
    """
    
    def __init__(self, db: Session):
        """Initialize message repository."""
        super().__init__(db, Message)
    
    def get_by_conversation(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 100,
        ascending: bool = True
    ) -> List[Message]:
        """
        Get all messages for a specific conversation.
        
        Args:
            conversation_id: Conversation UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            ascending: Sort order (True = oldest first, False = newest first)
            
        Returns:
            List of messages in the conversation
        """
        query = self.db.query(Message).filter(Message.conversation_id == conversation_id)
        
        if ascending:
            query = query.order_by(asc(Message.created_at))
        else:
            query = query.order_by(desc(Message.created_at))
        
        return query.offset(skip).limit(limit).all()
    
    def get_latest_messages(
        self,
        conversation_id: UUID,
        limit: int = 10
    ) -> List[Message]:
        """
        Get the latest N messages from a conversation.
        
        Args:
            conversation_id: Conversation UUID
            limit: Number of messages to retrieve
            
        Returns:
            List of latest messages (ordered oldest to newest)
        """
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
            .all()
        )
        # Reverse to get chronological order
        return list(reversed(messages))
    
    def count_by_conversation(
        self,
        conversation_id: UUID
    ) -> int:
        """
        Count messages in a conversation.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Number of messages
        """
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .count()
        )
    
    def get_by_role(
        self,
        conversation_id: UUID,
        role: MessageRole,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """
        Get messages by role in a conversation.
        
        Args:
            conversation_id: Conversation UUID
            role: Message role (USER, ASSISTANT, SYSTEM)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of messages with the specified role
        """
        return (
            self.db.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.role == role
            )
            .order_by(asc(Message.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_conversation_context(
        self,
        conversation_id: UUID,
        max_messages: int = 20
    ) -> List[dict]:
        """
        Get conversation context in OpenAI format.
        
        Args:
            conversation_id: Conversation UUID
            max_messages: Maximum number of recent messages to include
            
        Returns:
            List of messages in OpenAI API format
        """
        messages = self.get_latest_messages(conversation_id, limit=max_messages)
        return [msg.to_openai_format() for msg in messages]
    
    def calculate_total_tokens(
        self,
        conversation_id: UUID
    ) -> int:
        """
        Calculate total tokens used in a conversation.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Total token count
        """
        messages = self.get_by_conversation(conversation_id)
        return sum(msg.token_count or 0 for msg in messages)
    
    def delete_messages_by_conversation(
        self,
        conversation_id: UUID
    ) -> int:
        """
        Delete all messages in a conversation.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Number of messages deleted
        """
        count = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .delete()
        )
        self.db.commit()
        return count
