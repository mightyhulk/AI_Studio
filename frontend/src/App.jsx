import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import ChatPage from './pages/ChatPage';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('alexandria_auth') === 'true';
  });

  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('alexandria_user');
    return saved ? JSON.parse(saved) : null;
  });

  const handleLogin = (userData) => {
    setIsAuthenticated(true);
    setUser(userData);
    localStorage.setItem('alexandria_auth', 'true');
    localStorage.setItem('alexandria_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('alexandria_auth');
    localStorage.removeItem('alexandria_user');
  };

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated
            ? <Navigate to="/chat" replace />
            : <LoginPage onLogin={handleLogin} />
        }
      />
      <Route
        path="/signup"
        element={
          isAuthenticated
            ? <Navigate to="/chat" replace />
            : <SignUpPage onSignUp={handleLogin} />
        }
      />
      <Route
        path="/chat"
        element={
          isAuthenticated
            ? <ChatPage user={user} onLogout={handleLogout} />
            : <Navigate to="/login" replace />
        }
      />
      <Route path="*" element={<Navigate to={isAuthenticated ? "/chat" : "/login"} replace />} />
    </Routes>
  );
}

export default App;
