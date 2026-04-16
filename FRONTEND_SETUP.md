# 🎨 Frontend Installation Guide

## ⚠️ IMPORTANT: Install Node.js First!

Your system doesn't have Node.js installed. Follow these steps:

### Step 1: Download Node.js

1. Go to: **https://nodejs.org/**
2. Download the **LTS (Long Term Support)** version for Windows
3. Run the installer (node-vXX.X.X-x64.msi)
4. Follow the installation wizard (accept defaults)
5. **Restart your terminal/PowerShell** after installation

### Step 2: Verify Installation

Open a new PowerShell window and run:

```powershell
node --version
npm --version
```

You should see version numbers like:
```
v20.11.0
10.2.4
```

---

## 🚀 Quick Start (After Node.js is Installed)

### 1. Navigate to Frontend Directory

```powershell
cd "C:\Users\Manjunath\Dropbox\PC\Desktop\ai agent by claude\frontend"
```

### 2. Install Dependencies

```powershell
npm install
```

This will install:
- React 18.2.0
- Vite 5.0.8
- Tailwind CSS 3.4.0
- Framer Motion 10.16.16
- Axios 1.6.2
- React Markdown 9.0.1
- React Syntax Highlighter 15.5.0
- Lucide React 0.298.0
- And all dev dependencies

**Note:** Installation may take 2-5 minutes depending on internet speed.

### 3. Start the Backend First

In a separate terminal, start your FastAPI backend:

```powershell
cd "C:\Users\Manjunath\Dropbox\PC\Desktop\ai agent by claude"
python start_server.py
```

**Backend should be running on:** http://localhost:8000

### 4. Start the Frontend

Back in the frontend directory:

```powershell
npm run dev
```

**Frontend will start on:** http://localhost:5173

### 5. Open in Browser

Navigate to: **http://localhost:5173**

You should see the stunning cyberpunk login screen! 🎉

---

## 📋 Project Structure Created

```
frontend/
├── public/                          # Static assets
├── src/
│   ├── api/
│   │   └── axiosConfig.js          # ✅ API config with JWT interceptor
│   ├── components/
│   │   ├── Login.jsx               # ✅ Login/Register screen
│   │   ├── ChatInterface.jsx       # ✅ Main chat UI
│   │   └── MessageBubble.jsx       # ✅ Message bubbles with markdown
│   ├── App.jsx                     # ✅ Main app with routing
│   ├── main.jsx                    # ✅ React entry point
│   └── index.css                   # ✅ Tailwind + custom styles
├── index.html                       # ✅ HTML template
├── package.json                     # ✅ Dependencies
├── vite.config.js                  # ✅ Vite config with proxy
├── tailwind.config.js              # ✅ Tailwind config
├── postcss.config.js               # ✅ PostCSS config
├── .gitignore                      # ✅ Git ignore file
└── README.md                        # ✅ Documentation
```

---

## 🎨 Features Implemented

### 1. **Login Screen**
- Glass-morphic design with glowing borders
- Animated background elements
- Login/Register toggle
- Form validation
- Error handling
- Loading states

### 2. **Chat Interface**
- Collapsible sidebar with session history
- "New Chat" button
- Session switcher
- Auto-scrolling messages
- Beautiful message bubbles
- Loading indicators
- Logout functionality

### 3. **Message Bubbles**
- User messages: Gradient background (purple → blue)
- AI messages: Glass-morphic background
- **Brain Process Accordion**: Collapsible reasoning display
- Markdown rendering
- Code syntax highlighting (Dracula theme)
- Timestamps

### 4. **Animations (Framer Motion)**
- Message slide-up + fade-in
- Accordion expand/collapse
- Button hover effects
- Loading spinners
- Background gradient animations
- Smooth transitions

### 5. **API Integration**
- JWT token management
- Automatic token injection
- Token expiration handling
- Axios interceptors
- FormData for OAuth2 login
- Session management

---

## 🔧 Backend API Mapping

The frontend is configured to work with your **actual** backend API:

| Frontend Call | Backend Endpoint | Payload | Response |
|--------------|------------------|---------|----------|
| `authAPI.login()` | `POST /token` | `FormData(username, password)` | `{access_token, token_type}` |
| `authAPI.register()` | `POST /register` | `{username, password}` | `{access_token, token_type}` |
| `chatAPI.sendMessage()` | `POST /chat` | `{message, session_id?}` | `{session_id, message_id, final_answer, thought_process, context_used}` |
| `chatAPI.getHistory()` | `GET /sessions` | - | `{sessions: [...]}` |
| `chatAPI.getSessionMessages()` | `GET /sessions/{id}/messages` | - | `{messages: [...]}` |

---

## 🎯 How to Use

### First Time Setup
1. **Register**: Create a new account
2. **Login**: Sign in with your credentials
3. **Start Chatting**: Type a message and hit send
4. **View Reasoning**: Click "Brain Process" to see AI thinking
5. **Session History**: Click past sessions to view them

### Features to Test
- ✅ Login/Register
- ✅ Send messages
- ✅ View AI responses
- ✅ Expand/collapse brain process
- ✅ Code block rendering
- ✅ Markdown support
- ✅ New chat creation
- ✅ Session switching
- ✅ Logout

---

## 🐛 Troubleshooting

### Issue: `npm: command not found`
**Solution:** Node.js not installed. See Step 1 above.

### Issue: `CORS Error`
**Solution:** Add CORS middleware to FastAPI backend:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: `Cannot connect to backend`
**Solution:** 
1. Ensure backend is running on port 8000
2. Check `vite.config.js` proxy settings
3. Verify no firewall blocking localhost

### Issue: `401 Unauthorized after login`
**Solution:**
1. Check that token is being stored in localStorage
2. Verify backend JWT token generation
3. Check token expiration settings

---

## 📦 Production Build

When ready to deploy:

```powershell
npm run build
```

This creates optimized files in `dist/` directory.

### Preview Production Build

```powershell
npm run preview
```

---

## 🎨 Customization

### Change Colors
Edit `tailwind.config.js`:
```javascript
colors: {
  'cyber-dark': '#0f172a',
  'cyber-purple': '#a855f7',
  'cyber-blue': '#3b82f6',
  // Add your custom colors
}
```

### Change API URL
Edit `vite.config.js`:
```javascript
proxy: {
  '/api': {
    target: 'http://your-backend-url:port',
    // ...
  }
}
```

---

## 📚 Technologies Used

- **React 18** - UI library
- **Vite** - Build tool (faster than Create React App)
- **Tailwind CSS** - Utility-first CSS framework
- **Framer Motion** - Animation library
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering
- **React Syntax Highlighter** - Code highlighting
- **Lucide React** - Icon library

---

## 🎉 You're All Set!

The frontend is now ready to use. Once Node.js is installed and dependencies are downloaded, simply run:

```powershell
# Terminal 1 - Backend
python start_server.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Open **http://localhost:5173** and enjoy your cyberpunk AI agent! 🚀✨

---

**Need help?** Check the detailed README.md in the frontend/ directory.
