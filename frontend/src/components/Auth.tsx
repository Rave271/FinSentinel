import { useState } from "react";
import type { useAuth } from "../lib/useAuth";

interface AuthProps {
  onAuth: ReturnType<typeof useAuth>;
}

export function AuthPage({ onAuth }: AuthProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isLogin) {
      await onAuth.login(email, password);
    } else {
      if (password !== confirmPassword) {
        return;
      }
      await onAuth.register(email, password);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card glass-card">
        <div className="auth-header">
          <div className="brand-mark">FS</div>
          <h1>{isLogin ? "Sign In" : "Create Account"}</h1>
          <p>FinSentinel - NIFTY 50 signal intelligence</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </label>

          <label>
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              minLength={8}
              required
            />
          </label>

          {!isLogin && (
            <label>
              <span>Confirm Password</span>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                minLength={8}
                required
              />
            </label>
          )}

          {onAuth.error && (
            <div className="auth-error">
              <strong>Error:</strong> {onAuth.error}
            </div>
          )}

          <button
            type="submit"
            className="primary-button auth-button"
            disabled={onAuth.loading}
          >
            {onAuth.loading ? "Loading..." : isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {isLogin ? "Don't have an account?" : "Already have an account?"}
            <button
              type="button"
              className="link-button"
              onClick={() => {
                setIsLogin(!isLogin);
                setEmail("");
                setPassword("");
                setConfirmPassword("");
              }}
            >
              {isLogin ? "Sign up" : "Sign in"}
            </button>
          </p>
        </div>

        <div className="auth-divider">
          <span>or continue without account</span>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() => window.location.reload()}
        >
          Continue as Guest
        </button>
      </div>
    </div>
  );
}
