# AI Agent with RAG and Memory

A powerful AI Agent powered by DeepSeek R1 with long-term memory using Qdrant vector database and RAG (Retrieval-Augmented Generation).

## Features

- **JWT Authentication**: Secure user registration and login
- **RAG Integration**: Retrieves relevant past conversations for context-aware responses
- **DeepSeek R1 LLM**: Advanced reasoning with `<think>` tags for thought process
- **Long-term Memory**: Vector-based memory storage using Qdrant
- **SQLite Database**: Persistent storage of users, sessions, and messages
- **Async FastAPI**: High-performance async web framework

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────┐
│ Auth │  │ Chat  │
└──────┘  └───┬───┘
              │
        ┌─────┴─────┐
        │           │
    ┌───▼───┐   ┌───▼───────┐
    │ SQLite│   │  Qdrant   │
    │  DB   │   │  Memory   │
    └───────┘   └───────────┘
                     │
                ┌────▼─────┐
                │ DeepSeek │
                │   R1     │
                └──────────┘
```

## Prerequisites

1. **Python 3.8+**
2. **Docker** (for Qdrant)
3. **Ollama** with DeepSeek R1 model

### Install Ollama and DeepSeek R1

```bash
# Install Ollama from https://ollama.ai/

# Pull DeepSeek R1 model
ollama pull deepseek-r1
```

## Installation

1. **Clone or navigate to the project directory**

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Start Qdrant using Docker Compose**
```bash
docker-compose up -d
```

4. **Configure environment variables** (optional)

Edit `.env` file:
```
SECRET_KEY=your-super-secret-jwt-key-change-in-production
QDRANT_HOST=localhost
QDRANT_PORT=6333
OLLAMA_BASE_URL=http://localhost:11434
```

## Running the Application

### Option 1: Using the startup script (Recommended)
```bash
python start_server.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Using Python module
```bash
python -m backend.main
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### 1. Health Check
```bash
GET /
```
Returns API status and version.

### 2. User Registration
```bash
POST /register
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepassword123"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. User Login
```bash
POST /token
Content-Type: application/x-www-form-urlencoded

username=john_doe&password=securepassword123
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 4. Chat (Main Feature) 🚀
```bash
POST /chat
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "message": "What is machine learning?",
  "session_id": null
}
```

**How it works:**
1. **Retrieves context** from Qdrant memory (similar past conversations)
2. **Constructs prompt** with retrieved context
3. **Generates response** using DeepSeek R1 LLM
4. **Saves to SQLite** (both user message and AI response)
5. **Stores in Qdrant** for future context retrieval
6. **Returns response** with answer and thought process

Response:
```json
{
  "session_id": 1,
  "message_id": 2,
  "final_answer": "Machine learning is a subset of AI...",
  "thought_process": "Let me break this down...",
  "context_used": [
    {
      "score": 0.87,
      "user_message": "Tell me about AI",
      "ai_response": "AI is the simulation..."
    }
  ]
}
```

### 5. Get All Sessions
```bash
GET /sessions
Authorization: Bearer <your_token>
```

### 6. Get Session Messages
```bash
GET /sessions/{session_id}/messages
Authorization: Bearer <your_token>
```

## Example Usage with cURL

### Register a new user
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### Login and get token
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

### Send a chat message
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing in simple terms"
  }'
```

## Example Usage with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Register
response = requests.post(f"{BASE_URL}/register", json={
    "username": "alice",
    "password": "alice123"
})
token = response.json()["access_token"]

# 2. Chat
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(f"{BASE_URL}/chat", 
    headers=headers,
    json={
        "message": "What is the capital of France?"
    }
)
result = response.json()
print(f"Answer: {result['final_answer']}")
print(f"Thought: {result['thought_process']}")

# 3. Continue conversation in same session
response = requests.post(f"{BASE_URL}/chat", 
    headers=headers,
    json={
        "message": "What about Germany?",
        "session_id": result['session_id']  # Continue in same session
    }
)
```

## Project Structure

```
.
├── backend/
│   ├── __init__.py           # Package initialization
│   ├── main.py              # 🔥 FastAPI application (glue code)
│   ├── database.py          # Database setup and session management
│   ├── models.py            # SQLAlchemy models (User, ChatSession, Message)
│   ├── auth.py              # JWT authentication and password hashing
│   ├── llm_engine.py        # DeepSeek R1 client
│   └── memory_system.py     # Qdrant RAG memory system
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Qdrant container setup
├── .env                     # Environment variables
├── start_server.py          # Startup script
└── README.md               # This file
```

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `hashed_password`: Bcrypt hashed password
- `is_admin`: Admin flag

### ChatSessions Table
- `id`: Primary key
- `user_id`: Foreign key to Users
- `name`: Session name
- `created_at`: Timestamp

### Messages Table
- `id`: Primary key
- `session_id`: Foreign key to ChatSessions
- `role`: "user" or "assistant"
- `content`: Message content (final answer)
- `reasoning_content`: Thought process from `<think>` tags
- `timestamp`: Message timestamp

## Qdrant Vector Storage

Each interaction is stored as a vector point with:
- **Vector**: Sentence embedding of user message
- **Payload**: 
  - `user_id`: User identifier
  - `user_message`: Original user message
  - `ai_response`: AI's response

## Troubleshooting

### Qdrant not connecting
```bash
# Check if Qdrant is running
docker ps

# Start Qdrant
docker-compose up -d

# Check Qdrant logs
docker-compose logs qdrant
```

### Ollama not responding
```bash
# Check if Ollama is running
ollama list

# Test DeepSeek R1
ollama run deepseek-r1 "Hello"
```

### Database issues
```bash
# Delete the database and restart
rm agent.db
python start_server.py
```

## Development

To run in development mode with auto-reload:
```bash
python start_server.py
```

## Testing

Use the interactive API documentation at `http://localhost:8000/docs` to test all endpoints with a built-in UI.

## Security Notes

- Change `SECRET_KEY` in `.env` for production
- Use HTTPS in production
- Implement rate limiting for production use
- Add input sanitization for user messages
- Consider adding session expiration

## License

MIT

## Contributing

Feel free to submit issues and enhancement requests!
