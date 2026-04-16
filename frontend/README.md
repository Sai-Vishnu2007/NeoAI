# 🚀 AI Agent Frontend - Cyberpunk Glassmorphism UI

A stunning, modern React frontend for the Local AI Agent with cyberpunk-themed glassmorphism design, built with React + Vite, Tailwind CSS, and Framer Motion.

## ✨ Features

- **🎨 Cyberpunk Glassmorphism Design**: Deep dark backgrounds with neon gradients and translucent glass cards
- **🔐 JWT Authentication**: Secure login/register with OAuth2 token management
- **💬 Real-time Chat Interface**: Beautiful message bubbles with auto-scrolling
- **🧠 Brain Process Accordion**: Collapsible reasoning display for AI thought processes
- **📝 Markdown Support**: Rich text rendering with syntax highlighting (Dracula theme)
- **🎭 Smooth Animations**: Framer Motion animations for all interactions
- **📱 Responsive Design**: Mobile-friendly with collapsible sidebar
- **💾 Session Management**: Browse and restore previous chat sessions

## 🛠️ Tech Stack

- **React 18+** (via Vite)
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **Axios** - API requests with interceptors
- **React Markdown** - Markdown rendering
- **React Syntax Highlighter** - Code syntax highlighting
- **Lucide React** - Beautiful icons

## 📋 Prerequisites

You need to install Node.js and npm. Download from: https://nodejs.org/

**Verify installation:**
```bash
node --version
npm --version
```

## 🚀 Installation & Setup

### 1️⃣ Navigate to Frontend Directory

```bash
cd frontend
```

### 2️⃣ Install Dependencies

```bash
npm install
```

This will install all required packages:
- React & React DOM
- Vite & plugins
- Tailwind CSS
- Framer Motion
- Axios
- React Markdown
- React Syntax Highlighter
- Lucide React icons

### 3️⃣ Start Development Server

```bash
npm run dev
```

The frontend will start on **http://localhost:5173**

### 4️⃣ Ensure Backend is Running

Make sure your FastAPI backend is running on **http://localhost:8000**

```bash
# In the parent directory
python start_server.py
```

## 🎯 Usage

1. **Register/Login**: Create a new account or sign in with existing credentials
2. **Start Chatting**: Type your message and click send
3. **View Brain Process**: Click the "Brain Process" accordion to see AI reasoning
4. **Session History**: Access previous chats from the sidebar
5. **New Chat**: Click "New Chat" to start a fresh conversation
6. **Logout**: Use the logout button in the sidebar

## 📁 Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── api/
│   │   └── axiosConfig.js  # API configuration & JWT interceptor
│   ├── components/
│   │   ├── Login.jsx       # Login/Register component
│   │   ├── ChatInterface.jsx  # Main chat UI
│   │   └── MessageBubble.jsx  # Message display with markdown
│   ├── App.jsx            # Main app component
│   ├── main.jsx           # React entry point
│   └── index.css          # Global styles & Tailwind
├── index.html             # HTML template
├── package.json           # Dependencies
├── vite.config.js         # Vite configuration
├── tailwind.config.js     # Tailwind configuration
└── postcss.config.js      # PostCSS configuration
```

## 🎨 Design System

### Colors
- **Deep Dark**: `#0f172a` (cyber-dark)
- **Darker**: `#020617` (cyber-darker)
- **Purple**: `#a855f7` (cyber-purple)
- **Blue**: `#3b82f6` (cyber-blue)
- **Pink**: `#ec4899` (cyber-pink)

### Components
- **Glass Cards**: Translucent backgrounds with blur effect
- **Gradient Buttons**: Purple-to-blue gradients with glow effects
- **Message Bubbles**: User (gradient) vs AI (glass) styling
- **Brain Process**: Collapsible accordion with pink accent

## 🔧 Configuration

### API Proxy
The Vite dev server proxies API requests from `/api` to `http://localhost:8000`. 

**Configure in `vite.config.js`:**
```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

### Backend API Endpoints

The frontend connects to these backend endpoints:

- `POST /token` - Login (OAuth2)
- `POST /register` - Register new user
- `POST /chat` - Send message
- `GET /sessions` - Get chat sessions
- `GET /sessions/{id}/messages` - Get session messages

## 📦 Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## 🐛 Troubleshooting

### CORS Errors
Ensure FastAPI backend has CORS middleware configured:
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

### 401 Unauthorized
- Token might be expired or invalid
- Check localStorage for `access_token`
- Try logging out and logging back in

### Connection Issues
- Verify backend is running on port 8000
- Check Vite proxy configuration
- Ensure no firewall blocking localhost connections

## 🎬 Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## 📸 Screenshots

### Login Screen
Beautiful glassmorphic login card with animated background elements.

### Chat Interface
- Left sidebar with session history
- Center chat area with message bubbles
- Bottom input bar with floating design
- Brain Process accordions for AI reasoning

### Features
- Smooth message animations (slide up + fade in)
- Auto-scrolling to latest message
- Loading indicators with pulse animations
- Markdown rendering with code syntax highlighting
- Responsive design for mobile devices

## 🔐 Security

- JWT tokens stored in localStorage
- Automatic token injection via Axios interceptors
- Token expiration handling (auto-logout on 401)
- Secure password input fields
- HTTPS recommended for production

## 📝 License

This project is part of the AI Agent system.

---

Built with ❤️ using React, Vite, Tailwind CSS, and Framer Motion
