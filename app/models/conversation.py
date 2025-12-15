# app/models/conversation.py
"""
Conversation Model Module

This module defines the Conversation and Message models for the AI Assistant.
It demonstrates:
1. One-to-Many relationships (Conversation has many Messages)
2. JSON storage for flexible metadata
3. Proper indexing for performance
4. Timezone-aware timestamps

Design Pattern: Active Record - Models encapsulate both data and behavior
SOLID Principle: Single Responsibility - Each model handles its own domain
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


def utcnow():
    """
    Helper function to get current UTC datetime with timezone information.
    
    Returns:
        datetime: Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)


class MessageRole(enum.Enum):
    """
    Enumeration of message roles in a conversation.
    
    Using Enum provides:
    - Type safety
    - Clear documentation of valid values
    - Prevention of typos
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(enum.Enum):
    """
    Enumeration of conversation statuses.
    
    Allows for conversation lifecycle management:
    - ACTIVE: Currently in use
    - ARCHIVED: Completed but preserved
    - DELETED: Soft-deleted (can be restored)
    """
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(Base):
    """
    Conversation model representing a chat session with the AI assistant.
    
    Features:
    - Tracks conversation metadata
    - Links to user and messages
    - Supports categorization and search
    - Maintains conversation state
    
    Relationships:
    - Many-to-One with User (a user can have many conversations)
    - One-to-Many with Message (a conversation has many messages)
    """
    
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True
    )
    
    # Foreign key to user
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Conversation metadata
    title = Column(
        String(200),
        nullable=False,
        default="New Conversation"
    )
    
    status = Column(
        SQLEnum(ConversationStatus),
        nullable=False,
        default=ConversationStatus.ACTIVE,
        index=True
    )
    
    # Summary of the conversation (can be AI-generated)
    summary = Column(
        Text,
        nullable=True
    )
    
    # Additional information storage (renamed from metadata to avoid conflict)
    extra_data = Column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Message count for quick reference
    message_count = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False
    )
    
    last_message_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    def __repr__(self):
        """String representation for debugging."""
        return f"<Conversation(id={self.id}, title={self.title}, messages={self.message_count})>"
    
    def update_extra_data(self, **kwargs):
        """
        Update conversation extra data.
        
        Args:
            **kwargs: Key-value pairs to add to extra data
        """
        if self.extra_data is None:
            self.extra_data = {}
        self.extra_data.update(kwargs)
        self.updated_at = utcnow()
    
    def increment_message_count(self):
        """Increment the message count and update last_message_at."""
        self.message_count += 1
        self.last_message_at = utcnow()
        self.updated_at = utcnow()
    
    def archive(self):
        """Archive the conversation."""
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = utcnow()
    
    def delete(self):
        """Soft delete the conversation."""
        self.status = ConversationStatus.DELETED
        self.updated_at = utcnow()


class Message(Base):
    """
    Message model representing a single message in a conversation.
    
    Features:
    - Stores message content and metadata
    - Tracks message role (user, assistant, system)
    - Records token usage for cost tracking
    - Supports rich content types (text, images, code)
    
    Relationships:
    - Many-to-One with Conversation
    """
    
    __tablename__ = "messages"
    
    # Primary key
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True
    )
    
    # Foreign key to conversation
    conversation_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('conversations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Message data
    role = Column(
        SQLEnum(MessageRole),
        nullable=False,
        index=True
    )
    
    content = Column(
        Text,
        nullable=False
    )
    
    # Token usage tracking for cost management
    token_count = Column(
        Integer,
        nullable=True
    )
    
    # Additional data (model used, temperature, etc.)
    extra_data = Column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
        index=True
    )
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        """String representation for debugging."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(role={self.role.value}, content={content_preview})>"
    
    def to_openai_format(self) -> dict:
        """
        Convert message to OpenAI API format.
        
        Returns:
            dict: Message in OpenAI API format
        """
        return {
            "role": self.role.value,
            "content": self.content
        }
