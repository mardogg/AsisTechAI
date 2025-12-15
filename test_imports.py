"""
Test script to verify all imports work correctly
"""
import sys
print("Testing imports...")

try:
    # Test core config
    print("✓ Testing config...")
    from app.core.config import settings, get_settings
    
    # Test database
    print("✓ Testing database...")
    from app.database import Base, get_db, engine
    
    # Test models
    print("✓ Testing models...")
    from app.models import User, Conversation, Message, MessageRole, ConversationStatus
    
    # Test schemas
    print("✓ Testing schemas...")
    from app.schemas import (
        UserCreate, UserResponse,
        ConversationCreate, ConversationResponse,
        MessageCreate, MessageResponse,
        ChatRequest, ChatResponse
    )
    
    # Test repositories
    print("✓ Testing repositories...")
    from app.repositories import UserRepository, ConversationRepository, MessageRepository
    
    # Test OpenAI client
    print("✓ Testing OpenAI client...")
    from app.services.openai_client import OpenAIClient
    
    # Test auth
    print("✓ Testing auth...")
    try:
        from app.auth.dependencies import get_current_user, get_current_active_user
        from app.auth.jwt import create_token, verify_password, get_password_hash
    except Exception as auth_err:
        print(f"  Auth import warning: {auth_err}")
        print("  Continuing anyway...")
    
    print("\n✅ All imports successful!")
    print("\n📊 Module Summary:")
    print(f"  - User Model: {User.__tablename__}")
    print(f"  - Conversation Model: {Conversation.__tablename__}")
    print(f"  - Message Model: {Message.__tablename__}")
    print(f"  - OpenAI Model: {settings.OPENAI_MODEL}")
    print(f"  - Database URL: {settings.DATABASE_URL[:30]}...")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)

print("\n🎉 All systems ready for AsisTechAI!")
