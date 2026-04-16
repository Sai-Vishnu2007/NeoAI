# NEO VOICE — MASTER IMPLEMENTATION PROMPT
## For AI Coding Agents / Cursor / Windsurf / Claude Code

---

## ROLE & CONSTRAINTS

You are a senior Python backend and systems engineer implementing the **Neo Voice** system.
You write production-quality, working code only. You do NOT:
- Invent library names, function signatures, or API parameters that are not in the official docs
- Use placeholder comments like `# TODO` or `# implement this`
- Stub out functions without full implementation unless explicitly asked
- Use deprecated APIs (e.g., no `asyncio.get_event_loop()`, use `asyncio.get_running_loop()`)
- Mix sync and async code incorrectly

When you are unsure of an exact API parameter, you write a comment flagged `# VERIFY:` followed by the specific thing to check. You never silently guess.

---

## SYSTEM CONTEXT (READ BEFORE WRITING ANY CODE)

- The backend is an **existing FastAPI server** already running on Ubuntu. You are ADDING to it. You NEVER rewrite `main.py` from scratch — you only append `app.include_router(...)` and `app.add_event_handler(...)` calls.
- Python version: **3.11**
- All async database calls use **SQLAlchemy 2.x async sessions** (`async with AsyncSession() as session`)
- WebSocket implementation uses **Starlette's native WebSocket** (`from starlette.websockets import WebSocket`) — NOT the `websockets` library directly
- JWT library: **`python-jose`** with `from jose import jwt, JWTError`
- Encryption library: **`cryptography.fernet.Fernet`** — symmetric, no asymmetric confusion
- All environment variables accessed via `os.environ.get("KEY")` or a `pydantic BaseSettings` config class — never hardcoded

---

## PHASE 1 — IMPLEMENT IN THIS EXACT ORDER

### TASK 1.1 — Create `app/auth/jwt_handler.py`

Write a module with exactly one async function:

```
async def validate_ws_token(websocket: WebSocket) -> str
```

- Extract the token from the `Authorization` header of the WebSocket upgrade request using `websocket.headers.get("authorization")`
- Strip the `"Bearer "` prefix
- Decode using `jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])`
- PUBLIC_KEY loaded from `os.environ["JWT_PUBLIC_KEY"]`
- Validate claims: `exp` not expired, `scope == "voice_client"`
- On any failure, call `await websocket.close(code=4001)` with the correct code from this table:
  - Missing/malformed token → 4001
  - Expired → 4002
  - Wrong scope → 4003
- Return `payload["sub"]` as `user_id` string on success
- Do NOT return None. Either return a valid string or close the socket and raise an exception to stop the caller.

---

### TASK 1.2 — Create `app/routers/ws_voice.py`

Create an APIRouter with one WebSocket route: `@router.websocket("/ws/voice")`

The handler must follow this **exact execution order**:

```
1. Call validate_ws_token(websocket) → get user_id
2. Call await websocket.accept()
3. Call await manager.connect(websocket, user_id)
4. Enter try/finally block
5. In the try: run the main receive loop (see below)
6. In the finally: call await manager.disconnect(user_id)
```

The receive loop:
- `data = await websocket.receive()` returns a dict with key `"bytes"` or `"text"`
- If `"bytes"`: pass raw bytes to `await stt_service.push_audio_chunk(user_id, data["bytes"])`
- If `"text"`: parse JSON, route by `payload["type"]`:
  - `"context"` → store `payload["active_window"]` in a per-user context dict
  - `"screenshot"` → call `await tool_executor.handle_screenshot(user_id, payload["data"])`
  - `"command"` → call `await pipeline.run(user_id, payload["text"])`
- Handle `WebSocketDisconnect` by breaking the loop cleanly

---

### TASK 1.3 — Create `app/services/connection_manager.py`

Implement `ConnectionManager` class with these methods. No shortcuts:

```python
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._context: dict[str, dict] = {}  # stores active_window per user

    async def connect(self, websocket: WebSocket, user_id: str) -> None
    # If user_id already has a connection, close the old one with code 4008 first, then replace it.

    async def disconnect(self, user_id: str) -> None
    # Remove from dict. Do not raise if user_id not found.

    async def send_json(self, user_id: str, payload: dict) -> None
    # Acquire user lock. Send via websocket.send_json(). Release lock.
    # If WebSocketDisconnect raised, call disconnect(user_id) silently.

    async def send_bytes(self, user_id: str, data: bytes) -> None
    # Same lock pattern as send_json but websocket.send_bytes()

    def get_active_users(self) -> list[str]
    # Return list(self._connections.keys())

    def set_context(self, user_id: str, key: str, value: str) -> None
    def get_context(self, user_id: str, key: str, default: str = "") -> str
```

---

### TASK 1.4 — Register router and lifespan in existing `main.py`

Add ONLY these lines (do not touch anything else in main.py):

```python
# At top imports — add:
from app.routers.ws_voice import router as ws_router
from app.services.background_tasker import start_background_tasker

# Modify the existing lifespan or add one:
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(start_background_tasker(manager, db_session_factory))
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

# After app = FastAPI(...) — add:
app.include_router(ws_router)
```

---

## PHASE 2 — AUDIO PIPELINE

### TASK 2.1 — Create `app/services/stt_service.py`

- Maintain a per-user audio buffer: `dict[str, bytearray]`
- `push_audio_chunk(user_id, pcm_bytes)`: append to buffer
- On silence detection OR buffer reaching 3 seconds (3s × 16000hz × 2bytes = 96000 bytes), call `_transcribe(user_id)`
- `_transcribe(user_id)`:
  1. Convert buffer bytearray → WAV bytes (use `io.BytesIO` + `wave` stdlib module, 16kHz mono int16)
  2. Base64-encode the WAV bytes
  3. POST to Groq Whisper API:
     ```
     POST https://api.groq.com/openai/v1/audio/transcriptions
     Header: Authorization: Bearer {GROQ_API_KEY}
     Body: multipart/form-data
       file: <wav bytes, filename="audio.wav">
       model: "whisper-large-v3"
       response_format: "json"
     ```
  4. Use `httpx.AsyncClient` for the request. Timeout: 5 seconds.
  5. On success: return `response.json()["text"]`
  6. On timeout: log warning, return empty string
  7. Clear the user's buffer after transcription attempt regardless of success

- Silence detection: compute RMS of last 800ms of buffer. If RMS < 300 (int16 scale), trigger transcription. Formula: `rms = sqrt(mean(array('h', last_chunk)**2))`

---

### TASK 2.2 — Create `app/services/llm_router.py`

```python
async def route_completion(
    messages: list[dict],
    tools: list[dict],
    user_context: dict,
    stream: bool = True
) -> AsyncGenerator[str, None]
```

System prompt (inject as first message with role `"system"`):

```
You are Neo, a dedicated and highly respectful AI assistant. You address 
the user with loyalty and precision. The user's currently active window is: 
{active_window}. Use this context to infer intent where appropriate.
Always respond concisely. When calling tools, prefer minimal confirmation text.
Maintain a calm, professional tone at all times.
```

Replace `{active_window}` with `user_context.get("active_window", "Unknown")`.

**Gemini call** (primary):
```python
import google.generativeai as genai
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-preview-05-20",  # VERIFY: confirm latest flash preview model string
    tools=tools
)
response = await model.generate_content_async(messages, stream=True)
async for chunk in response:
    yield chunk.text
```

**Groq fallback** (on any `google.api_core.exceptions.ServiceUnavailable` or `Exception` from Gemini):
```python
from groq import AsyncGroq
client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
stream = await client.chat.completions.create(
    model="moonshotai/kimi-k2-5",  # VERIFY: confirm exact Groq model string for Kimi k2.5
    messages=messages,
    stream=True
)
async for chunk in stream:
    if chunk.choices[0].delta.content:
        yield chunk.choices[0].delta.content
```

Wrap the entire Gemini block in `try/except Exception` and fall through to Groq. Log which engine is being used at INFO level.

---

### TASK 2.3 — Create `app/services/tts_service.py`

```python
async def synthesize_stream(text: str) -> AsyncGenerator[bytes, None]
```

**Primary — Google Cloud TTS:**
```python
from google.cloud import texttospeech_v1 as tts
client = tts.TextToSpeechAsyncClient()
request = tts.SynthesizeSpeechRequest(
    input=tts.SynthesisInput(text=text),
    voice=tts.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Neural2-D"
    ),
    audio_config=tts.AudioConfig(
        audio_encoding=tts.AudioEncoding.MP3,
        speaking_rate=1.0
    )
)
response = await client.synthesize_speech(request=request)
# Google Cloud TTS returns the full audio in one response, not streaming
# Chunk it manually: yield 4096-byte chunks
audio = response.audio_content
for i in range(0, len(audio), 4096):
    yield audio[i:i+4096]
```

**Fallback — `edge-tts`** (on any exception from Google TTS):
```python
import edge_tts
communicate = edge_tts.Communicate(text=text, voice="en-US-GuyNeural")
async for chunk in communicate.stream():
    if chunk["type"] == "audio":
        yield chunk["data"]
```

---

## PHASE 3 — TOOL EXECUTION

### TASK 3.1 — Create `app/services/tool_executor.py`

Implement exactly these functions. Each function signature is final:

```python
async def execute_tool(
    tool_name: str,
    tool_args: dict,
    user_id: str,
    manager: ConnectionManager,
    db: AsyncSession
) -> dict  # always returns {"result": <data>, "error": None} or {"result": None, "error": "<msg>"}
```

**`fetch_emails` implementation:**
```python
creds = await get_user_credentials(user_id, db)
if creds.email_host.endswith("gmail.com") or creds.email_host == "imap.gmail.com":
    # Use Gmail API with creds.gmail_token
    # VERIFY: use google-api-python-client service object, not imaplib, for Gmail
else:
    import imaplib
    mail = imaplib.IMAP4_SSL(creds.email_host, creds.email_port)
    mail.login(creds.email_username, decrypt(creds.email_password))
    mail.select("inbox")
    _, msg_ids = mail.search(None, "UNSEEN")
    # fetch up to tool_args.get("max_count", 5) messages
    # return list of {"subject": ..., "from": ..., "preview": first 200 chars of body}
```

**`get_streaming_stats` implementation:**
```python
platform = tool_args["platform"]
creds = await get_user_credentials(user_id, db)
if platform == "youtube":
    token = decrypt(creds.youtube_token)  # JSON string → parse to dict
    # VERIFY: use google-api-python-client with credentials.Credentials.from_authorized_user_info(token_dict)
    # Call: youtube.liveBroadcasts().list(part="snippet,statistics", broadcastStatus="active")
elif platform == "twitch":
    token = decrypt(creds.twitch_token)
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.twitch.tv/helix/streams",
            headers={"Authorization": f"Bearer {token}", "Client-Id": os.environ["TWITCH_CLIENT_ID"]},
            params={"user_login": creds.twitch_username}
        )
    data = r.json()["data"]
    return {"live": len(data) > 0, "viewers": data[0]["viewer_count"] if data else 0}
```

**`handle_screenshot` implementation:**
```python
async def handle_screenshot(user_id: str, base64_png: str, last_user_text: str) -> str:
    import base64
    image_bytes = base64.b64decode(base64_png)
    # Pass to Gemini Vision
    import google.generativeai as genai
    model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")  # VERIFY: same model string
    import PIL.Image, io
    img = PIL.Image.open(io.BytesIO(image_bytes))
    response = await model.generate_content_async([
        img,
        f"The user asked: '{last_user_text}'. Describe what is visible on this screen and extract any actionable context."
    ])
    return response.text
```

---

### TASK 3.2 — Create `app/models/user_credentials.py`

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer
import uuid

class UserCredentials(Base):
    __tablename__ = "user_credentials"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    email_host: Mapped[str | None] = mapped_column(String(256))
    email_port: Mapped[int | None] = mapped_column(Integer)
    email_username: Mapped[str | None] = mapped_column(String(256))
    email_password: Mapped[str | None] = mapped_column(String)      # Fernet encrypted
    youtube_token: Mapped[str | None] = mapped_column(String)       # Fernet encrypted
    twitch_token: Mapped[str | None] = mapped_column(String)        # Fernet encrypted
    twitch_username: Mapped[str | None] = mapped_column(String(128))
    gcal_token: Mapped[str | None] = mapped_column(String)          # Fernet encrypted
```

Write two utility functions in the same file:

```python
def encrypt(value: str) -> str:
    f = Fernet(os.environ["CREDENTIAL_ENCRYPTION_KEY"].encode())
    return f.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    f = Fernet(os.environ["CREDENTIAL_ENCRYPTION_KEY"].encode())
    return f.decrypt(value.encode()).decode()
```

---

## PHASE 4 — BACKGROUND TASKER & PROACTIVE ALERTS

### TASK 4.1 — Create `app/services/background_tasker.py`

```python
async def start_background_tasker(
    manager: ConnectionManager,
    session_factory: async_sessionmaker
) -> None:
    poll_interval = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
    while True:
        try:
            async with session_factory() as db:
                active_users = manager.get_active_users()
                for user_id in active_users:
                    await _poll_user(user_id, db, manager)
        except Exception as e:
            logging.error(f"Background tasker error: {e}")
        await asyncio.sleep(poll_interval)
```

`_poll_user` must:
1. Load `UserCredentials` for the user from DB
2. If `gcal_token` is set: call Google Calendar API, fetch events starting within next 10 minutes that haven't been alerted yet (track alerted event IDs in a module-level `set`)
3. If `email_password` or gmail credentials set: check for new "important" emails since last poll (track via timestamp stored in module-level `dict[str, datetime]`)
4. For each triggered event, call:
   ```python
   audio_chunks = []
   async for chunk in tts_service.synthesize_stream(event.message):
       audio_chunks.append(chunk)
   full_audio = b"".join(audio_chunks)
   await manager.send_bytes(user_id, full_audio)
   await manager.send_json(user_id, {"type": "alert", "message": event.message, "source": event.source})
   ```
5. Never raise exceptions that escape `_poll_user` — catch all and log

---

## PC CLIENT — IMPLEMENT IN THIS EXACT ORDER

### TASK 5.1 — Create `neo_client/ws_client.py`

```python
class NeoWebSocketClient:
    def __init__(self, config: dict):
        self.url = config["server_url"]
        self.token = config["jwt_token"]
        self._ws = None
        self._receive_queue: asyncio.Queue = asyncio.Queue()
        self._send_queue: asyncio.Queue = asyncio.Queue()
        self._connected = asyncio.Event()

    async def connect(self) -> None:
        # Use websockets.connect() with extra_headers={"Authorization": f"Bearer {self.token}"}
        # On successful connect: set self._connected
        # Start two tasks: _sender_loop and _receiver_loop

    async def _sender_loop(self) -> None:
        # Drain self._send_queue and send each item
        # Items are either bytes (audio) or dict (JSON)
        # Use ws.send(bytes) for audio, ws.send(json.dumps(dict)) for JSON

    async def _receiver_loop(self) -> None:
        # Receive messages, put into self._receive_queue

    async def send_audio(self, pcm_bytes: bytes) -> None:
        await self._send_queue.put(pcm_bytes)

    async def send_json(self, payload: dict) -> None:
        await self._send_queue.put(payload)

    async def receive(self) -> dict | bytes:
        return await self._receive_queue.get()

    async def disconnect(self) -> None:
        if self._ws:
            await self._ws.close()
        self._connected.clear()
```

Reconnection: on any `ConnectionClosed` exception in `_receiver_loop`, wait 5 seconds, then call `connect()` again. Maximum 3 retries before giving up and calling `overlay.dismiss()`.

---

### TASK 5.2 — Create `neo_client/wake_word.py`

**Porcupine path (default):**

```python
import pvporcupine
import sounddevice as sd
import numpy as np

class WakeWordListener:
    def __init__(self, config: dict, on_trigger: callable):
        self.on_trigger = on_trigger  # sync callback, no args
        self.porcupine = pvporcupine.create(
            access_key=config["porcupine_access_key"],  # VERIFY: Porcupine requires access_key
            keyword_paths=[config["porcupine_model_path"]]
        )
        self.frame_length = self.porcupine.frame_length  # typically 512
        self._cooldown = False

    def start(self) -> None:
        # Run in a separate thread using threading.Thread(target=self._listen, daemon=True)
        pass

    def _listen(self) -> None:
        with sd.InputStream(
            samplerate=self.porcupine.sample_rate,  # 16000
            channels=1,
            dtype="int16",
            blocksize=self.frame_length
        ) as stream:
            while True:
                frame, _ = stream.read(self.frame_length)
                pcm = frame.flatten().tolist()
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0 and not self._cooldown:
                    self._cooldown = True
                    self.on_trigger()
                    threading.Timer(3.0, self._reset_cooldown).start()

    def _reset_cooldown(self):
        self._cooldown = False
```

**Vosk fallback path:**
```python
# If config["wake_word_engine"] == "vosk":
from vosk import Model, KaldiRecognizer
import json
model = Model(lang="en-us")  # downloads small model on first run
rec = KaldiRecognizer(model, 16000)
# In the listen loop: feed audio → rec.AcceptWaveform(bytes) → parse JSON result
# Match if "rise and shine" in result["text"].lower()
```

---

### TASK 5.3 — Create `neo_client/overlay_ui.py`

```python
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QVBoxLayout, QProgressBar
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QObject
from PyQt6.QtGui import QPalette, QColor

class OverlaySignals(QObject):
    set_status = pyqtSignal(str)
    set_text = pyqtSignal(str)
    set_mic_level = pyqtSignal(float)
    reveal = pyqtSignal()
    dismiss = pyqtSignal()

class OverlayWindow(QMainWindow):
    def __init__(self, monitor_index: int = 0):
        super().__init__()
        self.signals = OverlaySignals()
        self._setup_window()
        self._setup_ui()
        self._connect_signals()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setWindowOpacity(0.92)
        self.setFixedSize(360, 120)
        # Position: top-right of primary screen
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 380, 40)
        # Background color
        self.setStyleSheet("background-color: #0a0a0f;")
        self.hide()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 12)

        self.status_label = QLabel("Listening...")
        self.status_label.setStyleSheet("color: #00e5ff; font-size: 12px; font-weight: 500;")

        self.text_label = QLabel("")
        self.text_label.setStyleSheet("color: #ffffff; font-size: 13px;")
        self.text_label.setWordWrap(True)
        self.text_label.setMaximumHeight(40)

        self.mic_bar = QProgressBar()
        self.mic_bar.setRange(0, 100)
        self.mic_bar.setFixedHeight(4)
        self.mic_bar.setTextVisible(False)
        self.mic_bar.setStyleSheet(
            "QProgressBar { background: #1a1a2e; border-radius: 2px; }"
            "QProgressBar::chunk { background: #00e5ff; border-radius: 2px; }"
        )
        layout.addWidget(self.status_label)
        layout.addWidget(self.text_label)
        layout.addWidget(self.mic_bar)

    def _connect_signals(self):
        self.signals.set_status.connect(self.status_label.setText)
        self.signals.set_text.connect(self.text_label.setText)
        self.signals.set_mic_level.connect(lambda v: self.mic_bar.setValue(int(v * 100)))
        self.signals.reveal.connect(self._reveal)
        self.signals.dismiss.connect(self._dismiss)

    def _reveal(self):
        self.show()
        self.raise_()

    def _dismiss(self):
        self.hide()
```

**Cross-thread rule:** ALL UI updates MUST go through `self.signals.<signal>.emit(value)` — never call Qt methods directly from non-main threads.

---

### TASK 5.4 — Create `neo_client/audio_handler.py`

```python
import sounddevice as sd
import numpy as np
import asyncio
import re

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 320  # 20ms
DTYPE = "int16"

FOCUS_APP_PATTERNS = [
    "fullscreen",
    re.compile(r"(valorant|fortnite|cs2|csgo|cyberpunk|elden ring|minecraft)", re.I)
]

class AudioHandler:
    def __init__(self, ws_client, overlay, window_monitor, device_index=None):
        self.ws = ws_client
        self.overlay = overlay
        self.window_monitor = window_monitor
        self.device_index = device_index
        self._playback_queue: asyncio.Queue = asyncio.Queue()
        self._streaming = False

    def start_capture(self) -> None:
        # Run in thread: open sd.InputStream, callback puts chunks in send queue
        def callback(indata, frames, time, status):
            if self._streaming:
                pcm = indata.flatten().tobytes()
                asyncio.run_coroutine_threadsafe(
                    self.ws.send_audio(pcm),
                    self._loop
                )
                rms = float(np.sqrt(np.mean(indata.astype(np.float32)**2)))
                self.overlay.signals.set_mic_level.emit(min(rms / 3000.0, 1.0))
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype=DTYPE,
            blocksize=CHUNK_SAMPLES, callback=callback,
            device=self.device_index
        )
        self._stream.start()

    async def playback_loop(self) -> None:
        while True:
            audio_bytes = await self._playback_queue.get()
            active_win = self.window_monitor.get_title()
            if self._should_mute(active_win):
                # Re-queue with lower priority — simple: put back after 5s delay
                await asyncio.sleep(5)
                await self._playback_queue.put(audio_bytes)
                continue
            # Play via pyaudio
            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE,
                            output=True)
            stream.write(audio_bytes)
            stream.stop_stream()
            stream.close()
            p.terminate()

    def _should_mute(self, title: str) -> bool:
        title_lower = title.lower()
        for pattern in FOCUS_APP_PATTERNS:
            if isinstance(pattern, str) and pattern in title_lower:
                return True
            if hasattr(pattern, "search") and pattern.search(title):
                return True
        return False

    def push_tts_audio(self, audio_bytes: bytes) -> None:
        asyncio.run_coroutine_threadsafe(
            self._playback_queue.put(audio_bytes),
            self._loop
        )
```

---

### TASK 5.5 — Create `neo_client/window_monitor.py`

```python
import platform
import subprocess
import threading

class WindowMonitor:
    def __init__(self):
        self._title = "Unknown"
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def get_title(self) -> str:
        with self._lock:
            return self._title

    def _poll(self) -> None:
        import time
        while True:
            title = self._fetch_title()
            with self._lock:
                self._title = title
            time.sleep(1.0)

    def _fetch_title(self) -> str:
        try:
            if platform.system() == "Windows":
                import pygetwindow as gw
                win = gw.getActiveWindow()
                return win.title if win else "Unknown"
            else:
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True, timeout=1
                )
                return result.stdout.strip() or "Unknown"
        except Exception:
            return "Unknown"
```

---

### TASK 5.6 — Create `neo_client/execution_engine.py`

```python
import webbrowser, os, subprocess, platform, base64, asyncio
import mss, mss.tools

async def dispatch(payload: dict, ws_client) -> None:
    tool = payload.get("tool")
    handlers = {
        "open_website":       _open_website,
        "launch_application": _launch_application,
        "open_file":          _open_file,
        "screenshot_request": lambda p: _screenshot(p, ws_client),
        "search_local_files": _search_files,
    }
    handler = handlers.get(tool)
    if handler:
        await handler(payload)
    else:
        import logging
        logging.warning(f"Unknown action received: {tool}")
        await ws_client.send_json({"type": "error", "message": f"Unknown action: {tool}"})

async def _open_website(p): webbrowser.open(p["url"])
async def _launch_application(p): subprocess.Popen(p["app"], shell=True)

async def _open_file(p):
    path = p["path"]
    if platform.system() == "Windows":
        os.startfile(path)
    else:
        subprocess.Popen(["xdg-open", path])

async def _screenshot(p, ws_client):
    with mss.mss() as sct:
        img = sct.grab(sct.monitors[1])
        png_bytes = mss.tools.to_png(img.rgb, img.size)
    b64 = base64.b64encode(png_bytes).decode()
    await ws_client.send_json({"type": "screenshot", "data": b64})

async def _search_files(p):
    query = p["query"]
    paths = []
    if platform.system() == "Windows":
        result = subprocess.run(
            ["es.exe", "-n", "5", query],
            capture_output=True, text=True, timeout=3
        )
        paths = result.stdout.strip().splitlines()
    else:
        result = subprocess.run(
            ["fd", "--max-results", "5", query, os.path.expanduser("~")],
            capture_output=True, text=True, timeout=5
        )
        paths = result.stdout.strip().splitlines()

    if paths:
        top = paths[0]
        if platform.system() == "Windows":
            os.startfile(top)
        else:
            subprocess.Popen(["xdg-open", top])
    # Return result for spoken confirmation upstream
    return paths
```

---

### TASK 5.7 — Create `neo_client/main.py`

```python
import asyncio, sys, threading, json
from PyQt6.QtWidgets import QApplication

from neo_client.wake_word import WakeWordListener
from neo_client.overlay_ui import OverlayWindow
from neo_client.ws_client import NeoWebSocketClient
from neo_client.audio_handler import AudioHandler
from neo_client.window_monitor import WindowMonitor
from neo_client.execution_engine import dispatch

def load_config() -> dict:
    with open("config.json") as f:
        return json.load(f)

def main():
    config = load_config()

    app = QApplication(sys.argv)  # Must be created before any QWidget
    overlay = OverlayWindow(monitor_index=config.get("overlay_monitor", 0))

    ws_client = NeoWebSocketClient(config)
    window_monitor = WindowMonitor()
    window_monitor.start()
    audio = AudioHandler(ws_client, overlay, window_monitor,
                         device_index=config.get("audio_device_index"))

    async def on_ws_message():
        while True:
            msg = await ws_client.receive()
            if isinstance(msg, bytes):
                audio.push_tts_audio(msg)
                overlay.signals.set_status.emit("Speaking...")
            elif isinstance(msg, dict):
                if msg.get("type") == "action":
                    await dispatch(msg, ws_client)
                elif msg.get("type") == "transcript":
                    overlay.signals.set_text.emit(msg.get("text", ""))
                elif msg.get("type") == "alert":
                    overlay.signals.set_status.emit(f"Alert: {msg.get('message','')}")

    def on_wake_word():
        import subprocess as sp
        # Play "Greetings Supreme" audio (blocking in thread is fine)
        greeting_path = "assets/greetings_supreme.wav"
        if sys.platform == "win32":
            import winsound
            winsound.PlaySound(greeting_path, winsound.SND_FILENAME)
        else:
            sp.run(["aplay", greeting_path])

        overlay.signals.reveal.emit()

        # Start WS + audio in the asyncio thread
        loop = asyncio.new_event_loop()
        audio._loop = loop

        def run_async():
            loop.run_until_complete(asyncio.gather(
                ws_client.connect(),
                audio.playback_loop(),
                on_ws_message()
            ))

        threading.Thread(target=run_async, daemon=True).start()
        audio.start_capture()
        overlay.signals.set_status.emit("Listening...")

    wake_listener = WakeWordListener(config, on_trigger=on_wake_word)
    wake_listener.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## ACTIVE WINDOW CONTEXT INJECTION — EXACT WIRE FORMAT

Every time a mic audio chunk is sent, also send the following JSON frame on the same WebSocket:

```python
await ws_client.send_json({
    "type": "context",
    "active_window": window_monitor.get_title()
})
```

Send this ONCE per transcription cycle (not per 20ms chunk) — specifically, send it immediately before the `_transcribe()` call is triggered server-side.

---

## ERROR HANDLING — MANDATORY PATTERNS

Every function that calls an external API MUST follow this pattern. No bare `except:` blocks:

```python
try:
    result = await external_api_call()
except httpx.TimeoutException:
    logging.warning("API call timed out: <service_name>")
    return {"error": "timeout"}
except httpx.HTTPStatusError as e:
    logging.error(f"HTTP {e.response.status_code} from <service>: {e.response.text}")
    return {"error": f"http_{e.response.status_code}"}
except Exception as e:
    logging.exception(f"Unexpected error in <function_name>")
    return {"error": "unexpected"}
```

Replace `<service_name>` and `<function_name>` with the actual names. Never swallow exceptions silently.

---

## THINGS YOU MUST NEVER DO

1. **Never** call `asyncio.run()` inside an already-running event loop — use `asyncio.create_task()` or `loop.run_until_complete()` from a non-async thread only
2. **Never** import `pvporcupine` without checking `config["wake_word_engine"] == "porcupine"` first
3. **Never** store raw credentials (passwords, tokens) in logs — mask with `***` in log messages
4. **Never** use `shell=True` in `subprocess.Popen` for paths containing user-supplied data — only for known, hardcoded app names
5. **Never** block the PyQt6 main thread — all WS/audio/file operations run in threads or the asyncio loop thread
6. **Never** call Google TTS and edge-tts simultaneously — edge-tts is fallback only, inside `except`
7. **Never** send credentials over the WebSocket — JWT token goes in the HTTP upgrade header only

---

## VERIFICATION CHECKLIST (run before marking any phase complete)

### Phase 1
- [ ] `GET /ws/voice` with no token → receives close code 4001
- [ ] `GET /ws/voice` with expired token → receives close code 4002
- [ ] Two clients connect with different user_ids → both receive only their own messages
- [ ] "RISE AND SHINE" spoken → overlay appears, "Greetings Supreme" plays within 500ms

### Phase 2
- [ ] Speak 5 seconds of audio → server log shows transcription text
- [ ] Active window title appears in every server-side LLM request log
- [ ] First TTS audio byte arrives at PC client within 2000ms of finishing speaking
- [ ] Open a fullscreen window → speak a command → TTS audio is deferred, not played

### Phase 3
- [ ] Say "open YouTube" → browser opens `https://youtube.com` within 1s
- [ ] Say "open VS Code" → VS Code launches within 2s
- [ ] Say "find my resume" → correct file opens within 3s
- [ ] Say "what's on my screen" → spoken description returned within 5s

### Phase 4
- [ ] Create a calendar event 8 minutes from now → alert spoken within 60s
- [ ] `fetch_emails` with user A credentials → returns only user A's emails, never user B's
- [ ] Kill Gemini API (block the domain in `/etc/hosts`) → Groq fallback responds correctly
- [ ] Restart server → background tasker resumes automatically

---

*End of Master Implementation Prompt — Neo Voice v1.0*