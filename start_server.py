"""
Startup script for the AI Agent API server.

This script runs the FastAPI application with uvicorn.
"""
import uvicorn
import sys

def main():
    """Start the FastAPI server"""
    print("=" * 60)
    print("Starting AI Agent API Server")
    print("=" * 60)
    print("\nMake sure you have:")
    print("  1. Qdrant running (docker-compose up -d)")
    print("  2. Ollama running with deepseek-r1 model")
    print("  3. All dependencies installed (pip install -r requirements.txt)")
    print("\n" + "=" * 60)
    print("Server will start at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    
    try:
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # Auto-reload on code changes
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
