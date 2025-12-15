"""
Repository Pattern Implementation

Separates data access logic from business logic.
Follows SOLID principles and provides a clean abstraction over database operations.
"""

from typing import Optional, List, Generic, TypeVar, Type
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from app.database import Base

# Generic type for models
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(ABC, Generic[ModelType]):
    """
    Abstract base repository class.
    
    Implements Repository Pattern and follows:
    - Single Responsibility: Only handles data access
    - Dependency Inversion: Depends on abstractions (Session, Base)
    - Open/Closed: Can be extended without modification
    """
    
    def __init__(self, db: Session, model: Type[ModelType]):
        """
        Initialize repository with database session and model class.
        
        Args:
            db: SQLAlchemy database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get a single entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found, None otherwise
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all entities with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of entities
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, **kwargs) -> ModelType:
        """
        Create a new entity.
        
        Args:
            **kwargs: Entity attributes
            
        Returns:
            Created entity
        """
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Update an entity.
        
        Args:
            id: Entity ID
            **kwargs: Attributes to update
            
        Returns:
            Updated entity if found, None otherwise
        """
        db_obj = self.get_by_id(id)
        if db_obj:
            for key, value in kwargs.items():
                if hasattr(db_obj, key) and value is not None:
                    setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> bool:
        """
        Delete an entity.
        
        Args:
            id: Entity ID
            
        Returns:
            True if deleted, False if not found
        """
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
    
    def count(self) -> int:
        """
        Count total number of entities.
        
        Returns:
            Total count
        """
        return self.db.query(self.model).count()


# Import specific repositories for easy access
from app.repositories.user_repository import UserRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ConversationRepository",
    "MessageRepository"
]
