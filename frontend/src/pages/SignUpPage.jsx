import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import './SignUpPage.css';

export default function SignUpPage({ onSignUp }) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!fullName.trim() || !email.trim() || !password.trim()) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setIsLoading(true);

    try {
      const baseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
      const response = await fetch(`${baseUrl}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: fullName, email, password }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Sign up failed');
      }

      // Redirect to login page upon successful account creation
      navigate('/login');
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
          throw new Error(data.detail || 'Google sign-up failed');
        }

        onSignUp(data.user);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    },
    onError: () => setError('Google sign-up failed')
  });

  return (
    <div className="signup-page">
      {/* Left: branding */}
      <div className="signup-brand-panel">
        <div className="signup-brand-content">
          <div className="signup-brand-badge">
            <span className="signup-brand-icon">✦</span>
          </div>
          <h1 className="signup-brand-title">Alexandria AI</h1>
          <p className="signup-brand-subtitle">The Digital Curator</p>
          <div className="signup-brand-quote">
            <blockquote>
              "The only true wisdom is in knowing you know nothing."
            </blockquote>
            <cite>— Socrates</cite>
          </div>
        </div>
        <div className="signup-brand-decoration">
          <div className="deco-line deco-line-1"></div>
          <div className="deco-line deco-line-2"></div>
          <div className="deco-line deco-line-3"></div>
        </div>
      </div>

      {/* Right: sign up form */}
      <div className="signup-form-panel">
        <div className="signup-form-container">
          <div className="signup-form-header">
            <h2 className="signup-title">Join the Collective</h2>
            <div className="signup-divider"></div>
            <p className="signup-hint">Create your account to begin exploring the archives.</p>
          </div>

          {error && (
            <div className="signup-error animate-fade-in">
              <span className="error-icon">⚠</span>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="signup-form">
            <div className="input-group">
              <label htmlFor="signup-name">Full Name</label>
              <input
                id="signup-name"
                type="text"
                className="input-field"
                placeholder="Eleanor Scholar"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                autoComplete="name"
              />
            </div>

            <div className="input-group">
              <label htmlFor="signup-email">Email Address</label>
              <input
                id="signup-email"
                type="email"
                className="input-field"
                placeholder="scholar@alexandria.ai"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>

            <div className="signup-form-row">
              <div className="input-group">
                <label htmlFor="signup-password">Password</label>
                <div className="password-wrapper">
                  <input
                    id="signup-password"
                    type={showPassword ? 'text' : 'password'}
                    className="input-field"
                    placeholder="Min. 6 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="new-password"
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

              <div className="input-group">
                <label htmlFor="signup-confirm">Confirm Password</label>
                <input
                  id="signup-confirm"
                  type={showPassword ? 'text' : 'password'}
                  className="input-field"
                  placeholder="Repeat password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                />
              </div>
            </div>

            <div className="signup-terms">
              <label className="terms-checkbox">
                <input type="checkbox" required />
                <span>
                  I agree to the{' '}
                  <a href="#" className="terms-link">Terms of Service</a>{' '}
                  and{' '}
                  <a href="#" className="terms-link">Privacy Policy</a>
                </span>
              </label>
            </div>

            <button
              type="submit"
              className="btn btn-primary signup-submit-btn"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="btn-loading">
                  <span className="spinner"></span>
                  Creating Account…
                </span>
              ) : (
                'Create Account'
              )}
            </button>

            <div className="auth-separator">
              <span>Or join with</span>
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
              Sign up with Google
            </button>
          </form>

          <p className="signup-footer">
            Already a member?{' '}
            <Link to="/login" className="signup-link">Authenticate here</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
