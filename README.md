# AsisTechAI - Enterprise AI Technical Assistant

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.120.1-009688.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-316192.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

An enterprise-grade AI Technical Assistant built with FastAPI, PostgreSQL, and OpenAI's GPT-4. Features conversational AI, web search capabilities, image analysis, and code assistance - all following SOLID principles and industry-standard design patterns.

## 🌟 Features

### AI Capabilities
- **💬 Conversational AI**: Natural language conversations with context awareness
- **🔍 Web Search Integration**: Real-time web search with AI-powered summaries
- **🖼️ Image Analysis**: Vision API for analyzing images with detailed descriptions
- **💻 Code Assistant**: Specialized programming help with lower temperature for accuracy
- **📝 Conversation Management**: Full CRUD operations for conversation history

### Enterprise Features
- **🔐 JWT Authentication**: Secure OAuth2 password bearer authentication
- **🗄️ PostgreSQL Database**: Robust data persistence with SQLAlchemy ORM
- **🔄 Retry Logic**: Exponential backoff for API failures
- **📊 Token Tracking**: Monitor and optimize OpenAI API usage
- **🎯 Rate Limiting**: Configurable request and token limits
- **📝 Comprehensive Logging**: Full audit trail for debugging

## 🏗️ Architecture

### Design Patterns

#### 1. **Strategy Pattern** (`app/services/ai_strategies.py`)
Enables interchangeable AI operations without modifying existing code.
```python
- AIServiceStrategy (Abstract Base)
  ├── ChatStrategy
  ├── WebSearchStrategy
  ├── ImageAnalysisStrategy
  └── CodeAssistantStrategy
```

#### 2. **Repository Pattern** (`app/repositories/`)
Abstracts data access for testability and maintainability.
```python
- BaseRepository[T]
  ├── UserRepository
  ├── ConversationRepository
  └── MessageRepository
```

#### 3. **Factory Pattern** (`AIStrategyFactory`)
Dynamically creates and registers strategy instances.
```python
factory = AIStrategyFactory()
strategy = factory.create("chat")
```

#### 4. **Singleton Pattern** (`OpenAIClient`)
Ensures single OpenAI client instance for rate limit management.
```python
client = OpenAIClient()  # Always returns same instance
```

#### 5. **Facade Pattern** (`AIAssistantService`)
Simplifies complex AI operations with a unified interface.
```python
service = AIAssistantService(db)
result = service.chat(user_id, message)
```

### SOLID Principles

- ✅ **Single Responsibility**: Each class has one reason to change
- ✅ **Open/Closed**: Extensible through strategies without modification
- ✅ **Liskov Substitution**: All strategies/repositories are interchangeable
- ✅ **Interface Segregation**: Separate schemas for Create/Update/Response
- ✅ **Dependency Inversion**: High-level modules depend on abstractions

### Project Structure

```
AsisTechAI/
├── app/
│   ├── core/
│   │   ├── config.py              # Settings management
│   │   ├── database.py            # Database connection
│   │   └── security.py            # JWT & password hashing
│   ├── models/
│   │   ├── user.py                # User model
│   │   └── conversation.py        # Conversation & Message models
│   ├── schemas/
│   │   ├── user.py                # User validation schemas
│   │   └── conversation.py        # AI operation schemas
│   ├── repositories/
│   │   ├── base.py                # BaseRepository[T]
│   │   ├── user_repository.py     # User data access
│   │   ├── conversation_repository.py
│   │   └── message_repository.py
│   ├── services/
│   │   ├── openai_client.py       # OpenAI API wrapper
│   │   ├── ai_strategies.py       # Strategy implementations
│   │   └── ai_assistant_service.py # Orchestration service
│   ├── dependencies/
│   │   └── auth.py                # Auth dependencies
│   └── main.py                    # FastAPI application
├── tests/
│   ├── unit/                      # Unit tests
│   └── integration/               # Integration tests
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
├── docker-compose.yml             # Development environment
└── README.md                      # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 17
- OpenAI API Key
- Docker & Docker Compose (optional)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/AsisTechAI.git
cd AsisTechAI
```

2. **Create virtual environment**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings:
# - DATABASE_URL
# - SECRET_KEY
# - OPENAI_API_KEY
```

5. **Initialize database**
```bash
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

6. **Run the application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **Access the application**
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Dashboard: http://localhost:8000/dashboard (after authentication)

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## 📚 API Usage

### Authentication

All AI endpoints require JWT authentication.

**Register a user:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "email": "demo@example.com",
    "password": "SecurePass123!"
  }'
```

**Login to get token:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo_user&password=SecurePass123!"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### AI Endpoints

#### Chat with AI

```bash
curl -X POST "http://localhost:8000/ai/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain the SOLID principles",
    "conversation_id": null,
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

Response:
```json
{
  "conversation_id": "uuid-here",
  "message": "Explain the SOLID principles",
  "assistant_response": "SOLID is an acronym for five design principles...",
  "tokens_used": 250,
  "model_used": "gpt-4o-mini",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

#### Web Search

```bash
curl -X POST "http://localhost:8000/ai/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest FastAPI features 2025",
    "conversation_id": null,
    "max_results": 5
  }'
```

#### Image Analysis

```bash
curl -X POST "http://localhost:8000/ai/analyze-image" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "prompt": "Describe this image in detail",
    "conversation_id": null
  }'
```

#### List Conversations

```bash
curl -X GET "http://localhost:8000/ai/conversations?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Conversation with Messages

```bash
curl -X GET "http://localhost:8000/ai/conversations/{conversation_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Delete Conversation

```bash
curl -X DELETE "http://localhost:8000/ai/conversations/{conversation_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-...                  # Your OpenAI API key
OPENAI_MODEL=gpt-4o-mini              # Default: gpt-4o-mini
OPENAI_MAX_TOKENS=1000                # Max tokens per request
OPENAI_TEMPERATURE=0.7                # Creativity (0.0-2.0)
OPENAI_TIMEOUT=30                     # API timeout seconds

# AI Features
MAX_CONVERSATION_HISTORY=50           # Messages to keep in context
ENABLE_WEB_SEARCH=true                # Enable web search
ENABLE_IMAGE_ANALYSIS=true            # Enable vision API
ENABLE_CODE_EXECUTION=false           # Enable code execution (unsafe)

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60            # Requests per minute per user
MAX_TOKENS_PER_REQUEST=4000           # Max tokens per request

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/asistechai

# JWT Authentication
SECRET_KEY=your-secret-key-here       # Change in production!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Model Selection Guide

| Model | Cost | Speed | Use Case |
|-------|------|-------|----------|
| gpt-4o-mini | $0.15/1M tokens | Fast | General conversations, cost-effective |
| gpt-4o | $5/1M tokens | Medium | Complex reasoning, better quality |
| gpt-4-turbo | $10/1M tokens | Medium | Latest features, highest quality |
| gpt-3.5-turbo | $0.50/1M tokens | Very Fast | Simple tasks, highest throughput |

## 🧪 Testing

### Import Validation
```bash
python test_imports.py
```

### Run Tests (coming soon)
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=app --cov-report=html
```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Use `.env.example` as template
2. **Rotate SECRET_KEY regularly** - Generate with `openssl rand -hex 32`
3. **Use strong passwords** - Minimum 8 characters with complexity
4. **Enable HTTPS in production** - Configure reverse proxy (nginx)
5. **Rate limit API endpoints** - Prevent abuse with rate limiting
6. **Validate all inputs** - Pydantic schemas enforce validation
7. **Monitor OpenAI usage** - Set billing limits in OpenAI dashboard

## 📈 Performance Optimization

### Database Indexes
```sql
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
```

### Caching Strategy
- Use Redis for session storage
- Cache OpenAI responses for identical queries
- Implement conversation context caching

### Token Optimization
- Set appropriate `max_tokens` per use case
- Use `gpt-4o-mini` for cost-effective operations
- Implement conversation pruning (MAX_CONVERSATION_HISTORY)

## 🐛 Troubleshooting

### Common Issues

**"duplicate base class TimeoutError" warning**
- **Cause**: Python 3.11 exception hierarchy change
- **Impact**: Non-critical, auth still works
- **Solution**: Ignore warning or update auth dependencies

**"OpenAI rate limit exceeded"**
- **Cause**: Too many requests in short time
- **Solution**: Implement exponential backoff (already included)
- **Check**: MAX_REQUESTS_PER_MINUTE setting

**"Database connection refused"**
- **Cause**: PostgreSQL not running or wrong credentials
- **Solution**: Check DATABASE_URL in .env
- **Docker**: Ensure `docker-compose up db` is running

**"Invalid OpenAI API key"**
- **Cause**: Missing or incorrect OPENAI_API_KEY
- **Solution**: Get key from https://platform.openai.com/api-keys
- **Verify**: Run `python -c "from app.services.openai_client import openai_client; print(openai_client.validate_api_key())"`

## 🛠️ Development Workflow

### Adding a New AI Strategy

1. Create strategy class in `app/services/ai_strategies.py`:
```python
class CustomStrategy(AIServiceStrategy):
    def execute(self, **kwargs) -> Dict[str, Any]:
        # Your implementation
        return {"success": True, "content": "..."}
    
    def get_name(self) -> str:
        return "custom"
```

2. Register in factory:
```python
factory = AIStrategyFactory()
factory.register_strategy("custom", CustomStrategy())
```

3. Use in service:
```python
strategy = self.strategy_factory.create("custom")
result = strategy.execute(...)
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add custom table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

- **Documentation**: This README and inline code comments
- **Issues**: GitHub Issues for bug reports and feature requests
- **API Docs**: http://localhost:8000/docs when running locally

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework for building APIs
- **OpenAI** - GPT models powering the AI capabilities
- **SQLAlchemy** - Powerful ORM for database operations
- **Pydantic** - Data validation using Python type annotations

---

Built with ❤️ using FastAPI, PostgreSQL, and OpenAI GPT-4
