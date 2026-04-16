import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
// 🔥 ADDED 'Mic' to the Lucide imports
import { Send, LogOut, MessageSquare, Loader2, Sparkles, Menu, X, Paperclip, Pin, Trash2, Mic } from 'lucide-react'; 
import { chatAPI } from '../api/axiosConfig';
import MessageBubble from './MessageBubble';

const ChatInterface = ({ onLogout }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [username, setUsername] = useState('');
  const [uploading, setUploading] = useState(false); 
  
  // 🔥 UPDATED: State for Server-Side Voice Recording
  const [isListening, setIsListening] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null); 

  useEffect(() => {
    const storedUsername = localStorage.getItem('username');
    setUsername(storedUsername || 'User');
    loadSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSessions = async () => {
    try {
      const data = await chatAPI.getHistory();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const data = await chatAPI.getSessionMessages(sessionId);
      setMessages(data.messages || []);
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error('Error loading session messages:', error);
    }
  };

  const handlePinToggle = async (e, sessionId) => {
    e.stopPropagation(); 
    try {
      await chatAPI.pinSession(sessionId);
      loadSessions(); 
    } catch (error) {
      console.error("Failed to pin session:", error);
    }
  };

  const handleDelete = async (e, sessionId) => {
    e.stopPropagation(); 
    try {
      await chatAPI.deleteSession(sessionId);
      loadSessions(); 
      if (currentSessionId === sessionId) {
        handleNewChat(); 
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const allowed = ['.pdf', '.docx', '.xlsx', '.xls', '.csv', '.txt'];
    const isAllowed = allowed.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!isAllowed) {
      alert("Format not supported yet, bro! Use PDF, Word, Excel, or Text.");
      return;
    }

    setUploading(true);
    try {
      const response = await chatAPI.uploadFile(file);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `📁 **Knowledge Acquired:** I've memorized the contents of **${file.name}**. You can now ask me questions about it!`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Is the Python server and Qdrant running?');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = ''; 
    }
  };

  const handleInput = (e) => {
    setInputMessage(e.target.value);
    const textarea = inputRef.current;
    if (textarea) {
      textarea.style.height = 'auto'; 
      textarea.style.height = `${textarea.scrollHeight}px`; 
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); 
      handleSendMessage(); 
    }
  };

  // ==========================================
  // 🔥 UPDATED: SERVER-SIDE VOICE TRANSCRIPTION 🔥
  // ==========================================
  const toggleListening = async () => {
    if (isListening) {
      // STOP RECORDING
      mediaRecorderRef.current?.stop();
      setIsListening(false);
    } else {
      // START RECORDING
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunksRef.current.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          const formData = new FormData();
          formData.append("file", audioBlob, "recording.wav");

          setLoading(true);
          try {
            // 🚀 Send raw audio to your Ubuntu Server's new endpoint
            // chatAPI.transcribe is a new method you'll add to axiosConfig
            const response = await chatAPI.transcribe(formData);
            const transcribedText = response.text;

            if (transcribedText) {
              setInputMessage(transcribedText);
              // Directly trigger answer for a seamless experience
              handleSendMessage(null, transcribedText);
            }
          } catch (error) {
            console.error("Transcription failed:", error);
          } finally {
            setLoading(false);
            // Stop the stream tracks
            stream.getTracks().forEach(track => track.stop());
          }
        };

        mediaRecorder.start();
        setIsListening(true);
      } catch (err) {
        console.error("Mic access denied:", err);
        alert("I can't hear you, bro! Check mic permissions (needs HTTPS).");
      }
    }
  };

  const handleSendMessage = async (e, directText = null) => {
    if (e) e.preventDefault(); 
    const messageToSend = directText || inputMessage.trim();
    
    if (!messageToSend || loading) return;

    const userMessage = {
      role: 'user',
      content: messageToSend,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
    
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(userMessage.content, currentSessionId);

      const aiMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.final_answer,
        reasoning_content: response.thought_process,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMessage]);

      if (!currentSessionId && response.session_id) {
        setCurrentSessionId(response.session_id);
        loadSessions(); 
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '❌ Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setCurrentSessionId(null);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    onLogout();
  };

  return (
    <div className="flex h-screen bg-cyber-darker overflow-hidden">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: 'spring', damping: 20 }}
            className="w-80 glass border-r border-cyber-purple/20 flex flex-col z-10"
          >
            {/* Sidebar Header */}
            <div className="p-6 border-b border-cyber-purple/20">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold gradient-text">Neo AI</h2>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="lg:hidden text-cyber-purple hover:text-cyber-pink transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-sm text-slate-400">Welcome, {username}!</p>
            </div>

            {/* New Chat Button */}
            <div className="p-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleNewChat}
                className="w-full py-3 bg-gradient-to-r from-cyber-purple to-cyber-blue rounded-lg 
                            text-white font-semibold flex items-center justify-center space-x-2
                            hover:shadow-lg hover:shadow-cyber-purple/50 transition-all"
              >
                <Sparkles className="w-5 h-5" />
                <span>New Chat</span>
              </motion.button>
            </div>

            {/* Session History */}
            <div className="flex-1 overflow-y-auto p-4">
              <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                Session History
              </h3>
              <div className="space-y-2">
                {sessions.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-4">
                    No sessions yet. Start a new chat!
                  </p>
                ) : (
                  sessions.map((session) => (
                    <motion.div
                      key={session.id}
                      whileHover={{ scale: 1.02 }}
                      onClick={() => loadSessionMessages(session.id)}
                      className={`w-full p-3 rounded-lg text-left transition-all cursor-pointer group flex items-center justify-between ${
                        currentSessionId === session.id
                          ? 'glass border-cyber-purple'
                          : 'glass-hover'
                      }`}
                    >
                      <div className="flex items-start space-x-2 min-w-0 flex-1">
                        {session.is_pinned ? (
                          <Pin className="w-4 h-4 text-cyber-pink mt-1 flex-shrink-0" />
                        ) : (
                          <MessageSquare className="w-4 h-4 text-cyber-purple mt-1 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0 pr-2">
                          <p className="text-sm text-white truncate">{session.name}</p>
                          <p className="text-xs text-slate-500">
                            {new Date(session.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>

                      <div className="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                        <button
                          onClick={(e) => handlePinToggle(e, session.id)}
                          className="p-1 text-slate-400 hover:text-cyber-pink transition-colors rounded"
                          title={session.is_pinned ? "Unpin chat" : "Pin chat"}
                        >
                          <Pin className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => handleDelete(e, session.id)}
                          className="p-1 text-slate-400 hover:text-red-400 transition-colors rounded"
                          title="Delete chat"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>

            {/* Logout Button */}
            <div className="p-4 border-t border-cyber-purple/20">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleLogout}
                className="w-full py-3 glass-hover rounded-lg text-red-400 font-semibold 
                            flex items-center justify-center space-x-2"
              >
                <LogOut className="w-5 h-5" />
                <span>Logout</span>
              </motion.button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <header className="glass border-b border-cyber-purple/20 p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="text-cyber-purple hover:text-cyber-pink transition-colors"
              >
                <Menu className="w-6 h-6" />
              </button>
            )}
            <h1 className="text-xl font-bold gradient-text">
              {currentSessionId ? 'Chat Session' : 'New Conversation'}
            </h1>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-slate-400">Connected</span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full text-center"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
              >
                <Sparkles className="w-20 h-20 text-cyber-purple mb-6" />
              </motion.div>
              <h2 className="text-3xl font-bold gradient-text mb-4">
                Welcome to Neo AI, Your Personal AI Assistant!
              </h2>
              <p className="text-slate-400 max-w-md">
                Start a conversation by typing your message below, or click the microphone to speak!
              </p>
            </motion.div>
          ) : (
            <AnimatePresence>
              {messages.map((message, index) => (
                <MessageBubble
                  key={index}
                  message={message}
                  isUser={message.role === 'user'}
                />
              ))}
            </AnimatePresence>
          )}

          {/* 🔥 UPDATED: CUSTOM AI THINKING TEXT 🔥 */}
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center space-x-3"
            >
              <div className="glass border-2 border-cyber-purple w-10 h-10 rounded-full flex items-center justify-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                >
                  <Loader2 className="w-5 h-5 text-cyber-purple" />
                </motion.div>
              </div>
              <div className="glass rounded-2xl p-4">
                <span className="text-cyber-purple italic font-medium animate-pulse">
                  The AI is Thinking...
                </span>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="glass border-t border-cyber-purple/20 p-4">
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-3">
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileUpload} 
                className="hidden" 
                accept=".pdf,.docx,.xlsx,.xls,.csv,.txt"
              />

              <motion.button
                type="button"
                onClick={() => fileInputRef.current.click()}
                disabled={loading || uploading}
                whileHover={{ scale: 1.1, rotate: -10 }}
                whileTap={{ scale: 0.9 }}
                className="p-3 mb-1 text-cyber-purple hover:text-cyber-pink transition-colors disabled:opacity-50"
                title="Upload Document"
              >
                {uploading ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                    <Loader2 className="w-6 h-6" />
                  </motion.div>
                ) : (
                  <Paperclip className="w-6 h-6 shadow-glow" />
                )}
              </motion.button>

              {/* 🔥 UPDATED: MICROPHONE BUTTON FOR SERVER-SIDE 🔥 */}
              <motion.button
                type="button"
                onClick={toggleListening}
                disabled={loading || uploading}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className={`p-3 mb-1 transition-all rounded-full ${
                  isListening 
                    ? 'text-red-400 bg-red-400/10 shadow-[0_0_15px_rgba(248,113,113,0.5)] animate-pulse' 
                    : 'text-cyber-purple hover:text-cyber-pink'
                }`}
                title={isListening ? "Stop listening" : "Start voice recording"}
              >
                <Mic className="w-6 h-6 shadow-glow" />
              </motion.button>

              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputMessage}
                  onChange={handleInput}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  placeholder={uploading ? "Analyzing document..." : isListening ? "I'm listening, bro..." : "Type your message..."}
                  disabled={loading || uploading}
                  className={`w-full px-6 py-4 bg-cyber-dark border rounded-3xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed resize-none overflow-y-auto max-h-48 ${
                    isListening ? 'border-red-400/50 focus:border-red-400 focus:ring-red-400/20' : 'border-cyber-purple/30 focus:border-cyber-purple focus:ring-cyber-purple/20'
                  }`}
                  style={{ minHeight: '56px' }}
                />
              </div>
              
              <motion.button
                type="submit"
                disabled={loading || !inputMessage.trim() || uploading}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-4 mb-1 bg-gradient-to-r from-cyber-purple to-cyber-blue rounded-full
                             text-white hover:shadow-lg hover:shadow-cyber-purple/50 transition-all
                             disabled:opacity-50 disabled:cursor-not-allowed glow flex-shrink-0"
              >
                {loading ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                    <Loader2 className="w-6 h-6" />
                  </motion.div>
                ) : (
                  <Send className="w-6 h-6" />
                )}
              </motion.button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;