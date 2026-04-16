import axios from 'axios';

// 1. REVERTED back to the working proxy path to fix Registration/Login
const api = axios.create({
  baseURL: '/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('username');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    // 2. REVERTED to original path to fix "Registration failed"
    const response = await axios.post('/api/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
  
  register: async (username, password) => {
    // 3. REVERTED to original path
    const response = await axios.post('/api/register', {
      username,
      password,
    });
    return response.data;
  },

  // 🔥 ADDED THIS: Google Login Route 🔥
  googleLogin: async (token) => {
    // Matches your working /api/ pattern perfectly
    const response = await axios.post('/api/auth/google', { token });
    return response.data;
  },
};

export const chatAPI = {
  sendMessage: async (message, sessionId = null) => {
    const response = await api.post('/chat', {
      message,
      session_id: sessionId,
    });
    return response.data;
  },
  
  // 4. KEEPING the fixed upload method
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }); 
    return response.data;
  },

  // ==========================================
  // 🔥 NEW: SERVER-SIDE TRANSCRIPTION CALL 🔥
  // ==========================================
  transcribe: async (formData) => {
    // Uses the 'api' instance to automatically include your Bearer token
    const response = await api.post('/transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  getHistory: async () => {
    const response = await api.get('/sessions');
    return response.data;
  },
  
  getSessionMessages: async (sessionId) => {
    const response = await api.get(`/sessions/${sessionId}/messages`);
    return response.data;
  },

  // ==========================================
  // 🔥 NEW: PIN AND DELETE API CALLS 🔥
  // ==========================================
  pinSession: async (sessionId) => {
    // Uses 'api' so it gets the token and '/api' base URL automatically
    const response = await api.patch(`/sessions/${sessionId}/pin`);
    return response.data;
  },
  
  deleteSession: async (sessionId) => {
    const response = await api.delete(`/sessions/${sessionId}`);
    return response.data;
  }
};

export default api;