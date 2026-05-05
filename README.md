---
title: AIVerse Backend
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# FastAPI AI Backend

A production-ready FastAPI backend for AI applications with modular architecture.

## Features

- ✅ RESTful API design
- ✅ Automatic API documentation
- ✅ Environment-based configuration
- ✅ Modular router structure
- ✅ Service layer pattern
- ✅ Pydantic data validation
- ✅ CORS support
- 🔜 AI model integration (Ollama, GROQ)
- 🔜 Database integration
- 🔜 Authentication & authorization

## Project Structure
fastapi/ 
    ├── app/ # Main application package 
    │   ├── api/ # API routes 
    │   ├── core/ # Core functionality 
    │   ├── models/ # Pydantic models 
    │   ├── services/ # Business logic 
    │   └── utils/ # Utilities 
    ├── tests/ # Test files 
    ├── .env # Environment variables 
    ├── requirements.txt # Dependencies 
    └── main.py # Entry point
frontend/
docs/
commands.txt
widget-demo.html

## Setup

### 1. Clone and Navigate
```bash
cd fastapi
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Run the Application
```bash
# Method 1: Using uvicorn directly
uvicorn main:app --reload

# Method 2: Using Python
python main.py
```

## Frontend (React App) Setup

### 1. Clone and Navigate
```bash
cd frontend
```

### 3. Install Dependencies
```bash
npm install
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Run the Application
```bash
npm run dev

```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Health
- `GET /api/v1/health` - Health check

### Users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user
- `PATCH /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `GET /api/v1/users/stats/count` - User statistics

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DEBUG`: Enable debug mode
- `ENVIRONMENT`: Environment name (development/production)
- `API_V1_PREFIX`: API version prefix
- `ALLOWED_ORIGINS`: CORS allowed origins

## 🤖 Multi-Provider AI Support

AIVerse now supports multiple AI providers with a unified interface:

### Supported Providers

| Provider | Cost | Speed | Quality | Free Tier |
|----------|------|-------|---------|-----------|
| **Ollama** | Free | Fast* | Good | ✅ Unlimited |
| **Groq** | Very Low | Very Fast | Good | ✅ 30 req/min |

*With GPU

### Quick Start

```python
# Use Groq for fast inference
response = await ai_service.chat(
    provider="groq",
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Use Ollama for free unlimited usage
response = await ai_service.chat(
    provider="ollama",
    model="llama2",
    messages=[{"role": "user", "content": "Write a poem"}]
)
```

### Features

- ✅ **Unified Interface** - Same API for all providers
- ✅ **Cost Tracking** - Monitor spending across providers
- ✅ **Budget Limits** - Set monthly spending caps
- ✅ **Usage Dashboard** - Real-time usage statistics

### Get API Keys

1. **Groq:** https://console.groq.com/keys (Free tier available)

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Use type hints

## License

MIT