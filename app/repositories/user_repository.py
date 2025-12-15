"""
User Repository

Handles all database operations related to users.
Follows Repository Pattern and Single Responsibility Principle.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User entities.
    
    Provides specialized methods for user-related database operations.
    """
    
    def __init__(self, db: Session):
        """Initialize user repository"""
        super().__init__(db, User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def username_exists(self, username: str) -> bool:
        """
        Check if username already exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if exists, False otherwise
        """
        return self.db.query(User).filter(User.username == username).count() > 0
    
    def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if exists, False otherwise
        """
        return self.db.query(User).filter(User.email == email).count() > 0
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active users
        """
        return (
            self.db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Deactivate a user (soft delete).
        
        Args:
            user_id: ID of user to deactivate
            
        Returns:
            Updated user if found, None otherwise
        """
        return self.update(user_id, is_active=False)
    
    def activate_user(self, user_id: int) -> Optional[User]:
        """
        Activate a user.
        
        Args:
            user_id: ID of user to activate
            
        Returns:
            Updated user if found, None otherwise
        """
        return self.update(user_id, is_active=True)
