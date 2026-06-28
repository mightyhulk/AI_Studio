import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import './LoginPage.css';

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields.');
      return;
    }

    setIsLoading(true);

    try {
      const baseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
      const response = await fetch(`${baseUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      onLogin(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setIsLoading(true);
      try {
        const baseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
        const response = await fetch(`${baseUrl}/auth/google`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: tokenResponse.access_token }),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Google sign-in failed');
        }

        onLogin(data.user);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    },
    onError: () => setError('Google sign-in failed')
  });

  return (
    <div className="login-page">
      {/* Left: branding panel */}
      <div className="login-brand-panel">
        <div className="login-brand-content">
          <div className="login-brand-badge">
            <span className="login-brand-icon">✦</span>
          </div>
          <h2 className="login-brand-tagline">The Digital Curator.</h2>
          <p className="login-brand-description">
            Dense information made effortless through scholarly authority and intelligent archival.
          </p>
          <div className="login-brand-features">
            <div className="login-brand-feature">
              <span className="feature-icon">✍</span>
              <span>Text Generation & Summarization</span>
            </div>
            <div className="login-brand-feature">
              <span className="feature-icon">🎨</span>
              <span>AI Image Creation & Editing</span>
            </div>
            <div className="login-brand-feature">
              <span className="feature-icon">🔊</span>
              <span>Speech & Music Generation</span>
            </div>
          </div>
        </div>
        <div className="login-brand-decoration">
          <div className="deco-circle deco-circle-1"></div>
          <div className="deco-circle deco-circle-2"></div>
          <div className="deco-circle deco-circle-3"></div>
        </div>
      </div>

      {/* Right: sign in form */}
      <div className="login-form-panel">
        <div className="login-form-container">
          <div className="login-form-header">
            <h1 className="login-title">Alexandria AI</h1>
            <div className="login-divider"></div>
            <h2 className="login-subtitle">Welcome back</h2>
            <p className="login-hint">Please enter your details to access the archives.</p>
          </div>

          {error && (
            <div className="login-error animate-fade-in">
              <span className="error-icon">⚠</span>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-form">
            <div className="input-group">
              <label htmlFor="login-email">Email Address</label>
              <input
                id="login-email"
                type="email"
                className="input-field"
                placeholder="scholar@alexandria.ai"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>

            <div className="input-group">
              <label htmlFor="login-password">Password</label>
              <div className="password-wrapper">
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  className="input-field"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? '◉' : '◎'}
                </button>
              </div>
            </div>

            <div className="login-options">
              <label className="remember-me">
                <input type="checkbox" />
                <span>Remember me</span>
              </label>
              <a href="#" className="forgot-password">Forgot your password?</a>
            </div>

            <button
              type="submit"
              className="btn btn-primary login-submit-btn"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="btn-loading">
                  <span className="spinner"></span>
                  Authenticating…
                </span>
              ) : (
                'Sign In'
              )}
            </button>

            <div className="auth-separator">
              <span>Or continue with</span>
            </div>

            <button
              type="button"
              className="btn btn-secondary google-signin-btn"
              onClick={handleGoogleSignIn}
              disabled={isLoading}
            >
              <svg viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Sign in with Google
            </button>
          </form>

          <p className="login-footer">
            Don't have an account?{' '}
            <Link to="/signup" className="login-link">Request archival access</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
