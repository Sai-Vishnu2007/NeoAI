"""
Main FastAPI application - NEO AI MASTER BRANCH
"""
import re  
import uuid 
import PyPDF2 
import docx  
import pandas as pd  
import io
import asyncio
import sqlite3
from datetime import timedelta, datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# --- Web Search ---
from duckduckgo_search import DDGS 

# --- Google Auth Imports ---
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# --- BRAIN IMPORTS (Qdrant & Embeddings) ---
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

# --- Local Modules ---
from backend import auth, database, models
from backend.llm_engine import get_llm_client

# =================================================================
# 🚀 INITIALIZATION
# =================================================================
app = FastAPI(title="Neo AI Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== WEB SEARCH ====================
def search_web(query: str):
    """Hits DuckDuckGo for live internet search"""
    print(f"🌍 Neo AI is Searching the Web: {query}")
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
        
        if not results:
            print("⚠️ WEB SEARCH RETURNED NO RESULTS!")
            return ""
            
        web_text = "\n\n--- LIVE INTERNET SEARCH RESULTS ---\n\n"
        for item in results:
            web_text += f"Title: {item.get('title')}\nSnippet: {item.get('body')}\nLink: {item.get('href')}\n\n"
        
        print("✅ Successfully grabbed internet data!")
        return web_text
    except Exception as e:
        print(f"Web Search Error: {e}")
        return ""

# ==================== VECTOR DB ====================
qdrant = QdrantClient("http://localhost:6335")
embedder = SentenceTransformer("all-MiniLM-L6-v2") 
COLLECTION_NAME = "agent_documents"

# ==================== STARTUP EVENT ====================
@app.on_event("startup")
async def startup_event():
    async with database.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    print("✅ SQL Database initialized")

    try:
        qdrant.get_collection(collection_name=COLLECTION_NAME)
        print("✅ Qdrant Collection ready")
    except:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print("✅ Qdrant Collection created")

# ==================== HEALTH CHECK ====================
@app.get("/")
async def root():
    return {"status": "running", "message": "Neo AI Backend is operational"}

# ==================== PYDANTIC SCHEMAS ====================
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    message_id: int
    thought_process: str
    final_answer: str
    session_id: int

class GoogleToken(BaseModel):
    token: str

# =================================================================
# 🔐 AUTHENTICATION ENDPOINTS
# =================================================================
GOOGLE_CLIENT_ID = "468719421977-lo8btn40i88v5dhdvh9gra9qo65k2igh.apps.googleusercontent.com"

@app.post("/auth/google")
async def google_login(token_data: GoogleToken, db: AsyncSession = Depends(database.get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(token_data.token, google_requests.Request(), GOOGLE_CLIENT_ID)
        google_email = idinfo['email']
        base_username = google_email.split('@')[0] 

        result = await db.execute(select(models.User).where(models.User.username == base_username))
        db_user = result.scalar_one_or_none()

        if not db_user:
            random_password = uuid.uuid4().hex
            new_user = auth.UserCreate(username=base_username, password=random_password)
            db_user = await auth.create_user(db, new_user)

        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)
        
        return {"access_token": access_token, "token_type": "bearer", "username": db_user.username}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google authentication token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Login Error: {str(e)}")

@app.post("/register", response_model=auth.Token)
async def register(user: auth.UserCreate, db: AsyncSession = Depends(database.get_db)):
    try:
        db_user = await auth.create_user(db, user)
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e: raise e
    except Exception as e: raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/token", response_model=auth.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(database.get_db)):
    user = await auth.authenticate_user(db, form_data.username, form_data.password)
    if not user: raise HTTPException(status_code=401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=auth.UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# =================================================================
# 📂 DOCUMENT PROCESSING & TRANSCRIPTION
# =================================================================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user)):
    try:
        filename = file.filename.lower()
        content = await file.read()
        text = ""

        if filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages: text += page.extract_text() + "\n"
        elif filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
        elif filename.endswith(('.xlsx', '.xls', '.csv')):
            df = pd.read_csv(io.BytesIO(content)) if filename.endswith('.csv') else pd.read_excel(io.BytesIO(content))
            text = df.to_string() 
        elif filename.endswith('.txt'):
            text = content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format!")

        if not text.strip(): raise HTTPException(status_code=400, detail="Document appears to be empty.")

        chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 50]
        points = []
        for i, chunk in enumerate(chunks):
            vector = embedder.encode(chunk).tolist()
            points.append(PointStruct(id=str(uuid.uuid4()), vector=vector, payload={"user_id": current_user.id, "filename": file.filename, "text": chunk}))
        
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        return {"filename": file.filename, "status": "Knowledge acquired successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processor Error: {str(e)}")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user)):
    try:
        audio_content = await file.read()
        llm_client = get_llm_client()
        transcription_text = llm_client.speech_to_text(audio_content)
        return {"text": transcription_text}
    except Exception as e:
        print(f"Transcription Endpoint Error: {e}")
        raise HTTPException(status_code=500, detail="Server failed to process audio")

# =================================================================
# 💬 SESSIONS & CORE CHAT
# =================================================================
@app.get("/sessions")
async def get_sessions(current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(
        select(models.ChatSession)
        .where(models.ChatSession.user_id == current_user.id, models.ChatSession.is_archived == False)
        .order_by(desc(models.ChatSession.is_pinned), desc(models.ChatSession.created_at))
    )
    sessions = result.scalars().all()
    return {"sessions": [{"id": s.id, "name": s.name, "created_at": s.created_at.isoformat() + "Z", "is_pinned": getattr(s, 'is_pinned', False)} for s in sessions]}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: int, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(database.get_db)):
    session_result = await db.execute(select(models.ChatSession).where(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id))
    session_to_delete = session_result.scalar_one_or_none()
    if not session_to_delete: raise HTTPException(status_code=404, detail="Session not found")
    
    session_to_delete.is_archived = True 
    await db.commit()
    return {"status": "success", "message": "Session moved to archive"}

@app.get("/sessions/{session_id}/messages")
async def get_session_messages_web(session_id: int, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(database.get_db)):
    session_result = await db.execute(select(models.ChatSession).where(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id))
    if not session_result.scalar_one_or_none(): raise HTTPException(status_code=404, detail="Session not found")
    messages_result = await db.execute(select(models.Message).where(models.Message.session_id == session_id).order_by(models.Message.timestamp))
    messages = messages_result.scalars().all()
    return {"messages": [{"id": m.id, "role": m.role, "content": m.content, "reasoning_content": m.reasoning_content, "timestamp": m.timestamp.isoformat() + "Z"} for m in messages]}

@app.get("/sessions/{session_id}")
async def get_session_messages_mobile(session_id: int, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(database.get_db)):
    return await get_session_messages_web(session_id, current_user, db)

@app.put("/sessions/{session_id}/pin")
async def toggle_pin_session(session_id: int, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(database.get_db)):
    session_result = await db.execute(select(models.ChatSession).where(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id))
    session_to_pin = session_result.scalar_one_or_none()
    if not session_to_pin: raise HTTPException(status_code=404, detail="Session not found")
    
    session_to_pin.is_pinned = not getattr(session_to_pin, 'is_pinned', False)
    await db.commit()
    return {"status": "success", "is_pinned": session_to_pin.is_pinned}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(database.get_db)):
    print(f"\n🚀 [SERVER WAKE UP] I received the message: {request.message}")
    try:
        session_id = request.session_id
        if not session_id:
            session_name = request.message[:50] + "..." if len(request.message) > 50 else request.message
            new_session = models.ChatSession(user_id=current_user.id, name=session_name, created_at=datetime.utcnow())
            db.add(new_session); await db.flush(); session_id = new_session.id
        else:
            session_check = await db.execute(select(models.ChatSession).where(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id))
            if not session_check.scalar_one_or_none(): raise HTTPException(status_code=404, detail="Session not found")
        
        # 1. FETCH MEMORY
        history_result = await db.execute(select(models.Message).where(models.Message.session_id == session_id).order_by(models.Message.timestamp.desc()).limit(10))
        db_history = history_result.scalars().all()
        db_history.reverse()
        formatted_history = [{"role": msg.role, "content": msg.content} for msg in db_history]

        user_message = models.Message(session_id=session_id, role="user", content=request.message, timestamp=datetime.utcnow())
        db.add(user_message)
        
        # 🛡️ FORTRESS GUARDRAIL
        SECURITY_PATTERNS = {
            "API Key (Groq/OpenAI/Stripe)": r"(gsk_[a-zA-Z0-9]{24,}|sk-[a-zA-Z0-9]{24,}|sk_live_[a-zA-Z0-9]{24,})",
            "AWS Cloud Key": r"(AKIA[0-9A-Z]{16})",
            "Credit/Debit Card": r"\b(?:\d[ -]*?){13,16}\b", 
            "Bank IBAN Number": r"\b[A-Z]{2}[0-9]{2}(?:[ ]?[0-9a-zA-Z]{4}){3,7}\b", 
            "Social Security / National ID": r"\b\d{3}-\d{2}-\d{4}\b"
        }
        
        detected_threat = None
        for threat_type, pattern in SECURITY_PATTERNS.items():
            if re.search(pattern, request.message):
                detected_threat = threat_type; break 
                
        if detected_threat:
            warning_text = f"🛡️ **Security Alert:** I detected sensitive information (**{detected_threat}**) in your message! Request blocked for your safety."
            ai_message = models.Message(session_id=session_id, role="assistant", content=warning_text, reasoning_content=f"Blocked {detected_threat}", timestamp=datetime.utcnow())
            db.add(ai_message); await db.commit(); await db.refresh(ai_message)
            return {"message_id": ai_message.id, "thought_process": ai_message.reasoning_content, "final_answer": ai_message.content, "session_id": session_id}

        # 🧠 RAG BRAIN
        retrieved_context = ""
        try:
            query_vector = embedder.encode(request.message).tolist()
            search_response = qdrant.query_points(
                collection_name=COLLECTION_NAME, query=query_vector, limit=3, score_threshold=0.5,
                query_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=current_user.id))])
            )
            if search_response.points:
                retrieved_context = "\n\n---\n\n".join([hit.payload["text"] for hit in search_response.points])
                print(f"✅ Context found in files: {len(retrieved_context)} characters")
            else:
                print("🧠 No relevant documents found for this query. Skipping RAG.")
        except Exception as e: print(f"Qdrant query error: {e}")

        # 🚦 AI TRAFFIC COP
        llm_client = get_llm_client() 
        router_prompt = f"You are an intelligent routing system. Your only job is to decide if the user's message requires searching the live internet. Does the user need real-time data, current events, weather, live sports, latest news, or up-to-date facts? Reply with EXACTLY one word: YES or NO.\nUser message: \"{request.message}\""
        
        try:
            router_decision = llm_client.generate_response(prompt=router_prompt, history=[])
            if "YES" in router_decision.get("final_answer", "").strip().upper():
                print(f"🚦 AI Router: INTERNET NEEDED for '{request.message}'")
                live_web_data = search_web(request.message)
                if live_web_data: retrieved_context += f"\n\n[LIVE WEB DATA]:\n{live_web_data}"
            else: print("🚦 AI Router: NO INTERNET NEEDED.")
        except Exception as e: print(f"Router Error: {e}")

        # 🧠 PROMPT CONSTRUCTION & GENERATION
        final_prompt = request.message
        if retrieved_context:
            final_prompt = f"You are a helpful AI assistant. Use the following context to answer the user's question accurately. If the context contains code or technical details, refer to them specifically.\n\n--- CONTEXT START ---\n{retrieved_context}\n--- CONTEXT END ---\n\nUser Question: {request.message}"

        msg_lower = request.message.lower()
        if "draw" in msg_lower or ("image" in msg_lower and ("generate" in msg_lower or "create" in msg_lower)):
            img_b64 = llm_client.generate_image(request.message)
            llm_response = {"final_answer": f"![Generated Image]({img_b64})" if img_b64 else "Sorry, the image generation failed.", "thought_process": ""}
        else:
            llm_response = llm_client.generate_response(prompt=final_prompt, history=formatted_history)
        
        ai_message = models.Message(session_id=session_id, role="assistant", content=llm_response["final_answer"], reasoning_content=llm_response.get("thought_process", ""), timestamp=datetime.utcnow())
        db.add(ai_message); await db.commit(); await db.refresh(ai_message)
        
        return {"message_id": ai_message.id, "thought_process": ai_message.reasoning_content or "", "final_answer": ai_message.content, "session_id": session_id}
    except Exception as e: await db.rollback(); raise HTTPException(status_code=500, detail=str(e))

# =================================================================
# 🛡️ ADMIN DASHBOARD ENDPOINTS
# =================================================================
def get_db_connection():
    conn = sqlite3.connect("agent.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/admin/users")
async def get_admin_users():
    conn = get_db_connection()
    users = conn.cursor().execute("SELECT id, username, is_admin FROM users ORDER BY id").fetchall()
    conn.close()
    return {"users": [{"id": u["id"], "username": u["username"], "is_admin": bool(u["is_admin"]), "auth_type": "google" if "@" in u["username"] else "standard", "join_date": "Active"} for u in users]}

@app.get("/api/admin/chats/{user_id}")
async def get_admin_user_chats(user_id: int):
    conn = get_db_connection()
    messages = conn.cursor().execute("SELECT m.id, m.role, m.content, m.reasoning_content, m.timestamp, cs.name as session_name FROM messages m JOIN chat_sessions cs ON m.session_id = cs.id WHERE cs.user_id = ? ORDER BY m.timestamp ASC", (user_id,)).fetchall()
    conn.close()
    return {"messages": [dict(m) for m in messages]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)