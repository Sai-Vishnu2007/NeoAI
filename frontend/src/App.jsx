import { useState, useEffect } from 'react';
import Login from './components/Login';
import ChatInterface from './components/ChatInterface';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const neoToken = localStorage.getItem('neo_auth_token');
    
    if (token || neoToken) {
      setIsAuthenticated(true);
    }
    setIsLoading(false);
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('neo_auth_token');
    localStorage.removeItem('username');
    setIsAuthenticated(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-cyber-darker flex items-center justify-center">
        <div className="animate-pulse text-cyber-purple text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="App h-screen w-screen overflow-hidden">
      {!isAuthenticated ? (
        <Login onLoginSuccess={handleLoginSuccess} />
      ) : (
        <ChatInterface onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;