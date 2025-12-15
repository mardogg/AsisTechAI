# app/repositories/conversation_repository.py
"""
Conversation Repository

Handles all database operations related to conversations.
Follows Repository Pattern and Single Responsibility Principle.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from app.models.conversation import Conversation, ConversationStatus
from app.repositories import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation entities.
    
    Provides specialized methods for conversation-related database operations.
    Follows Repository Pattern for data access abstraction.
    """
    
    def __init__(self, db: Session):
        """Initialize conversation repository."""
        super().__init__(db, Conversation)
    
    def get_by_user(
        self, 
        user_id: UUID, 
        status: Optional[ConversationStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Conversation]:
        """
        Get all conversations for a specific user.
        
        Args:
            user_id: User UUID
            status: Filter by conversation status (optional)
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of conversations for the user
        """
        query = self.db.query(Conversation).filter(Conversation.user_id == user_id)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        return (
            query
            .order_by(desc(Conversation.last_message_at), desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_active_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        """
        Get active conversations for a user.
        
        Args:
            user_id: User UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active conversations
        """
        return self.get_by_user(
            user_id=user_id,
            status=ConversationStatus.ACTIVE,
            skip=skip,
            limit=limit
        )
    
    def get_by_user_and_id(
        self,
        user_id: UUID,
        conversation_id: UUID
    ) -> Optional[Conversation]:
        """
        Get a specific conversation by ID, ensuring it belongs to the user.
        
        Args:
            user_id: User UUID
            conversation_id: Conversation UUID
            
        Returns:
            Conversation if found and belongs to user, None otherwise
        """
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            .first()
        )
    
    def count_by_user(
        self,
        user_id: UUID,
        status: Optional[ConversationStatus] = None
    ) -> int:
        """
        Count conversations for a specific user.
        
        Args:
            user_id: User UUID
            status: Filter by status (optional)
            
        Returns:
            Number of conversations
        """
        query = self.db.query(Conversation).filter(Conversation.user_id == user_id)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        return query.count()
    
    def archive_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> Optional[Conversation]:
        """
        Archive a conversation.
        
        Args:
            conversation_id: Conversation UUID
            user_id: User UUID (for verification)
            
        Returns:
            Updated conversation if found, None otherwise
        """
        conversation = self.get_by_user_and_id(user_id, conversation_id)
        if conversation:
            conversation.archive()
            self.db.commit()
            self.db.refresh(conversation)
        return conversation
    
    def delete_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Soft delete a conversation.
        
        Args:
            conversation_id: Conversation UUID
            user_id: User UUID (for verification)
            
        Returns:
            True if deleted, False if not found
        """
        conversation = self.get_by_user_and_id(user_id, conversation_id)
        if conversation:
            conversation.delete()
            self.db.commit()
            return True
        return False
    
    def search_conversations(
        self,
        user_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        """
        Search conversations by title or summary.
        
        Args:
            user_id: User UUID
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching conversations
        """
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.user_id == user_id,
                (Conversation.title.ilike(f"%{search_term}%") |
                 Conversation.summary.ilike(f"%{search_term}%"))
            )
            .order_by(desc(Conversation.last_message_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
