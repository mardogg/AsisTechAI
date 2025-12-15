"""
Unit tests for password validation in user registration.

Tests the password strength requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character
"""

import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate


class TestPasswordValidation:
    """Test suite for password validation requirements"""
    
    def test_valid_password(self):
        """Test that a valid password is accepted"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }
        user = UserCreate(**user_data)
        assert user.password == "SecurePass123!"
    
    def test_password_too_short(self):
        """Test that password less than 8 characters is rejected"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "password": "Pass1!",
            "confirm_password": "Pass1!"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "at least 8 characters" in str(exc_info.value)
    
    def test_password_no_uppercase(self):
        """Test that password without uppercase letter is rejected"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "password": "securepass123!",
            "confirm_password": "securepass123!"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "uppercase letter" in str(exc_info.value)
    
    def test_password_no_lowercase(self):
        """Test that password without lowercase letter is rejected"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "password": "SECUREPASS123!",
            "confirm_password": "SECUREPASS123!"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "lowercase letter" in str(exc_info.value)
    
    def test_password_no_digit(self):
        """Test that password without a digit is rejected"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "password": "SecurePass!",
            "confirm_password": "SecurePass!"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "number" in str(exc_info.value)
    
    def test_password_no_special_character(self):
        """Test that password without special character is rejected"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "password": "SecurePass123",
            "confirm_password": "SecurePass123"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "special character" in str(exc_info.value)
    
    def test_password_mismatch(self):
        """Test that mismatched passwords are rejected"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "password": "SecurePass123!",
            "confirm_password": "DifferentPass123!"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        assert "do not match" in str(exc_info.value)
    
    def test_various_special_characters(self):
        """Test that various special characters are accepted"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        for char in special_chars:
            user_data = {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "username": "johndoe",
                "password": f"SecurePass123{char}",
                "confirm_password": f"SecurePass123{char}"
            }
            user = UserCreate(**user_data)
            assert user.password == f"SecurePass123{char}"
    
    def test_complex_password(self):
        """Test that a complex password with all requirements is accepted"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "password": "MyC0mpl3x!P@ssw0rd#2024",
            "confirm_password": "MyC0mpl3x!P@ssw0rd#2024"
        }
        user = UserCreate(**user_data)
        assert user.password == "MyC0mpl3x!P@ssw0rd#2024"
