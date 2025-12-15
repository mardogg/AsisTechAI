# app/schemas/conversation.py
"""
Conversation and Message Schemas Module

This module defines Pydantic schemas for conversation and message data validation.
Follows Interface Segregation Principle with separate schemas for different operations.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class MessageRoleEnum(str, Enum):
    """Message role enumeration for validation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatusEnum(str, Enum):
    """Conversation status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ------------------------------------------------------------------------------
# Message Schemas
# ------------------------------------------------------------------------------

class MessageBase(BaseModel):
    """Base schema for message data."""
    role: MessageRoleEnum = Field(
        ...,
        description="Role of the message sender"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Message content"
    )
    
    model_config = ConfigDict(from_attributes=True)


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    conversation_id: Optional[UUID] = Field(
        None,
        description="Conversation ID (optional for first message)"
    )


class MessageResponse(MessageBase):
    """Schema for message responses."""
    id: UUID
    conversation_id: UUID
    token_count: Optional[int] = None
    extra_data: Optional[dict] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Conversation Schemas
# ------------------------------------------------------------------------------

class ConversationBase(BaseModel):
    """Base schema for conversation data."""
    title: Optional[str] = Field(
        "New Conversation",
        max_length=200,
        description="Conversation title"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="New conversation title"
    )
    status: Optional[ConversationStatusEnum] = Field(
        None,
        description="Conversation status"
    )
    summary: Optional[str] = Field(
        None,
        description="Conversation summary"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(ConversationBase):
    """Schema for conversation responses."""
    id: UUID
    user_id: UUID
    status: ConversationStatusEnum
    summary: Optional[str] = None
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    extra_data: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(ConversationResponse):
    """Schema for conversation with all messages."""
    messages: List[MessageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# AI Chat Schemas
# ------------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Schema for chat requests."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message to the AI assistant"
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Existing conversation ID (optional)"
    )
    model: Optional[str] = Field(
        None,
        description="OpenAI model to use (optional, uses default if not specified)"
    )
    temperature: Optional[float] = Field(
        None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 to 2.0)"
    )
    max_tokens: Optional[int] = Field(
        None,
        ge=1,
        le=4000,
        description="Maximum tokens in response"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Explain quantum computing in simple terms",
                "conversation_id": None,
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
    )


class ChatResponse(BaseModel):
    """Schema for chat responses."""
    conversation_id: UUID
    message: MessageResponse
    assistant_response: MessageResponse
    tokens_used: Optional[int] = None
    model_used: str
    
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Web Search Schemas
# ------------------------------------------------------------------------------

class WebSearchRequest(BaseModel):
    """Schema for web search requests."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query"
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Conversation to add results to"
    )
    max_results: Optional[int] = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of search results"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "latest developments in AI technology 2025",
                "max_results": 5
            }
        }
    )


class WebSearchResult(BaseModel):
    """Schema for individual search result."""
    title: str
    url: str
    snippet: str
    
    model_config = ConfigDict(from_attributes=True)


class WebSearchResponse(BaseModel):
    """Schema for web search responses."""
    query: str
    results: List[WebSearchResult]
    summary: str
    conversation_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Image Analysis Schemas
# ------------------------------------------------------------------------------

class ImageAnalysisRequest(BaseModel):
    """Schema for image analysis requests."""
    image_url: Optional[str] = Field(
        None,
        description="URL of the image to analyze"
    )
    image_base64: Optional[str] = Field(
        None,
        description="Base64-encoded image data"
    )
    prompt: Optional[str] = Field(
        "Describe this image in detail",
        description="Analysis prompt"
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Conversation to add analysis to"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_url": "https://example.com/image.jpg",
                "prompt": "What programming concepts are shown in this diagram?"
            }
        }
    )


class ImageAnalysisResponse(BaseModel):
    """Schema for image analysis responses."""
    analysis: str
    conversation_id: Optional[UUID] = None
    tokens_used: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)
