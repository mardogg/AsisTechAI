"""
FastAPI Main Application Module - AsisTechAI

This module defines the main FastAPI application for the AI Tech Assistant, including:
- Application initialization and configuration
- API endpoints for user authentication
- API endpoints for AI assistant operations (chat, conversations, analysis)
- Web routes for HTML templates
- Database table creation on startup

The application follows a RESTful API design with proper separation of concerns:
- Routes handle HTTP requests and responses
- Models define database structure
- Schemas validate request/response data
- Dependencies handle authentication and database sessions
"""

from contextlib import asynccontextmanager  # Used for startup/shutdown events
from datetime import datetime, timezone, timedelta
from uuid import UUID  # For type validation of UUIDs in path parameters
from typing import List

# FastAPI imports
from fastapi import Body, FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles  # For serving static files (CSS, JS)
from fastapi.templating import Jinja2Templates  # For HTML templates

from sqlalchemy.orm import Session  # SQLAlchemy database session

import uvicorn  # ASGI server for running FastAPI apps

# Application imports
from app.auth.dependencies import get_current_active_user  # Authentication dependency
from app.models.user import User  # Database model for users
from app.models.conversation import Conversation, Message  # Database models for AI conversations
from app.schemas.token import TokenResponse  # API token schema
from app.schemas.user import UserCreate, UserResponse, UserLogin  # User schemas
from app.schemas.conversation import (
    ChatRequest, ChatResponse,
    ConversationResponse, ConversationWithMessages,
    WebSearchRequest, WebSearchResponse,
    ImageAnalysisRequest, ImageAnalysisResponse,
    MessageResponse
)
from app.database import Base, get_db, engine  # Database connection
from app.services.ai_assistant_service import AIAssistantService  # AI service


# ------------------------------------------------------------------------------
# Create tables on startup using the lifespan event
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    
    This runs when the application starts and creates all database tables
    defined in SQLAlchemy models. It's an alternative to using Alembic
    for simpler applications.
    
    Args:
        app: FastAPI application instance
    """
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    yield  # This is where application runs
    # Cleanup code would go here (after yield), but we don't need any

# Initialize the FastAPI application with metadata and lifespan
app = FastAPI(
    title="AsisTechAI - AI Tech Assistant API",
    description="AI-powered technical assistant with chat, web search, and analysis capabilities",
    version="1.0.0",
    lifespan=lifespan  # Pass our lifespan context manager
)

# ------------------------------------------------------------------------------
# Static Files and Templates Configuration
# ------------------------------------------------------------------------------
# Mount the static files directory for serving CSS, JS, and images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates directory for HTML rendering
templates = Jinja2Templates(directory="templates")


# ------------------------------------------------------------------------------
# Web (HTML) Routes
# ------------------------------------------------------------------------------
# Our web routes use HTML responses with Jinja2 templates
# These provide a user-friendly web interface alongside the API

@app.get("/", response_class=HTMLResponse, tags=["web"])
def read_index(request: Request):
    """
    Landing page.
    
    Displays the welcome page with links to register and login.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse, tags=["web"])
def login_page(request: Request):
    """
    Login page.
    
    Displays a form for users to enter credentials and log in.
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse, tags=["web"])
def register_page(request: Request):
    """
    Registration page.
    
    Displays a form for new users to create an account.
    """
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse, tags=["web"])
def dashboard_page(request: Request):
    """
    Dashboard page for AI Tech Assistant.
    
    This is the main interface after login, where users can:
    - Chat with the AI assistant
    - View conversation history
    - Access different AI features (chat, search, image analysis)
    
    JavaScript in this page calls the API endpoints to interact with the AI.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/chat/{conversation_id}", response_class=HTMLResponse, tags=["web"])
def chat_page(request: Request, conversation_id: str):
    """
    Chat page for a specific conversation.
    
    Args:
        request: The FastAPI request object (required by Jinja2)
        conversation_id: UUID of the conversation
        
    Returns:
        HTMLResponse: Rendered template with conversation ID passed to frontend
    """
    return templates.TemplateResponse("chat.html", {"request": request, "conversation_id": conversation_id})


# ------------------------------------------------------------------------------
# Health Endpoint
# ------------------------------------------------------------------------------
@app.get("/health", tags=["health"])
def read_health():
    """Health check."""
    return {"status": "ok"}


# ------------------------------------------------------------------------------
# User Registration Endpoint
# ------------------------------------------------------------------------------
@app.post(
    "/auth/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=["auth"]
)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    """
    user_data = user_create.dict(exclude={"confirm_password"})
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ------------------------------------------------------------------------------
# User Login Endpoints
# ------------------------------------------------------------------------------
@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Login with JSON payload (username & password).
    Returns an access token, refresh token, and user info.
    """
    auth_result = User.authenticate(db, user_login.username, user_login.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_result["user"]
    db.commit()  # commit the last_login update

    # Ensure expires_at is timezone-aware
    expires_at = auth_result.get("expires_at")
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    return TokenResponse(
        access_token=auth_result["access_token"],
        refresh_token=auth_result["refresh_token"],
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified
    )

@app.post("/auth/token", tags=["auth"])
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login with form data (Swagger/UI).
    Returns an access token.
    """
    auth_result = User.authenticate(db, form_data.username, form_data.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": auth_result["access_token"],
        "token_type": "bearer"
    }


# ------------------------------------------------------------------------------
# AI Assistant Endpoints
# ------------------------------------------------------------------------------

@app.post("/ai/chat", response_model=ChatResponse, tags=["ai"])
def ai_chat(
    request: ChatRequest,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Chat with the AI assistant.
    
    This endpoint handles conversational AI interactions.
    It can create a new conversation or continue an existing one.
    """
    try:
        service = AIAssistantService(db)
        result = service.chat(
            user_id=current_user.id,
            message_content=request.message,
            conversation_id=request.conversation_id,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return ChatResponse(
            conversation_id=result["conversation_id"],
            message=MessageResponse.model_validate(result["user_message"]),
            assistant_response=MessageResponse.model_validate(result["assistant_message"]),
            tokens_used=result.get("tokens_used"),
            model_used=result["model"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/ai/search", response_model=WebSearchResponse, tags=["ai"])
def ai_web_search(
    request: WebSearchRequest,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Perform a web search using AI.
    
    Searches the web and provides an AI-generated summary of results.
    """
    try:
        service = AIAssistantService(db)
        result = service.web_search(
            user_id=current_user.id,
            query=request.query,
            conversation_id=request.conversation_id
        )
        
        return WebSearchResponse(
            query=result["query"],
            results=result["results"],
            summary=result["summary"],
            conversation_id=result["conversation_id"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/ai/analyze-image", response_model=ImageAnalysisResponse, tags=["ai"])
def ai_analyze_image(
    request: ImageAnalysisRequest,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze an image using AI vision capabilities.
    
    Provide an image URL and get an AI-generated analysis.
    """
    if not request.image_url and not request.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either image_url or image_base64 must be provided"
        )
    
    try:
        service = AIAssistantService(db)
        result = service.analyze_image(
            user_id=current_user.id,
            image_url=request.image_url or request.image_base64,
            prompt=request.prompt or "Describe this image in detail",
            conversation_id=request.conversation_id
        )
        
        return ImageAnalysisResponse(
            analysis=result["analysis"],
            conversation_id=result["conversation_id"],
            tokens_used=result.get("tokens_used")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/ai/conversations", response_model=List[ConversationResponse], tags=["ai"])
def list_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all conversations for the authenticated user.
    """
    service = AIAssistantService(db)
    conversations = service.list_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return conversations


@app.get("/ai/conversations/{conversation_id}", response_model=ConversationWithMessages, tags=["ai"])
def get_conversation(
    conversation_id: UUID,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation with all messages.
    """
    service = AIAssistantService(db)
    conversation = service.get_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation


@app.delete("/ai/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["ai"])
def delete_conversation(
    conversation_id: UUID,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation.
    """
    service = AIAssistantService(db)
    success = service.delete_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return None


@app.post("/ai/youtube-search", tags=["ai"])
def youtube_search(
    request: dict,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search YouTube for tech support videos.
    
    Body parameters:
    - problem_description: The technical problem
    - device_info: (optional) Make and model of device
    - conversation_id: (optional) Existing conversation ID
    """
    from app.services.ai_strategies import YouTubeSearchStrategy
    
    try:
        strategy = YouTubeSearchStrategy()
        result = strategy.execute(
            problem_description=request.get("problem_description", ""),
            device_info=request.get("device_info")
        )
        
        # Optionally save to conversation
        if request.get("conversation_id"):
            service = AIAssistantService(db)
            # Add user message and AI response to conversation
            # (Implementation depends on your service layer)
        
        return {
            "success": result["success"],
            "content": result["content"],
            "youtube_url": result.get("youtube_url"),
            "search_query": result.get("search_query")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/ai/device-diagnostic", tags=["ai"])
def device_diagnostic(
    request: dict,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Run device diagnostics.
    
    Body parameters:
    - device_type: Type of device (printer, phone, pc, console, etc.)
    - device_info: (optional) Make and model
    - operating_system: (optional) OS version
    - problem_description: (optional) What's wrong
    - conversation_id: (optional) Existing conversation ID
    """
    from app.services.ai_strategies import DeviceDiagnosticStrategy
    
    try:
        strategy = DeviceDiagnosticStrategy()
        result = strategy.execute(
            device_type=request.get("device_type", "generic"),
            device_info=request.get("device_info"),
            operating_system=request.get("operating_system"),
            problem_description=request.get("problem_description")
        )
        
        return {
            "success": result["success"],
            "content": result["content"],
            "device_type": result.get("device_type")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ------------------------------------------------------------------------------
# Main Block to Run the Server
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="info")
