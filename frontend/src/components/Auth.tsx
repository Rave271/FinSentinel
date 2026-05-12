import { useState } from "react";
import type { useAuth } from "../lib/useAuth";
import { Insignia } from "./Insignia";
import { GridWire } from "./GridWire";

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
    <div className="app-shell auth-shell">
      <GridWire title="Neon gridwire" />
      <header className="topbar auth-topbar">
        <div className="brand-lockup">
          <div className="brand-mark">
            <Insignia title="FinSentinel" />
          </div>
          <div className="brand-copy">
            <strong>Secure access</strong>
            <span>sessions + guest mode</span>
          </div>
        </div>
        <div className="topbar-actions">
          <div className="status-indicator live">Secure Sessions</div>
          <div className="auth-topbar-note">Bcrypt login with HttpOnly sessions</div>
        </div>
      </header>

      <section className="hero-layout auth-layout">
        <section className="hero-intro auth-intro">
          <div className="page-header">
            <div>
              <span className="eyebrow">Access Control</span>
              <h1>Sign in to your market desk.</h1>
              <p>
                Use your account to keep a private session, or enter guest mode to explore the
                dashboard with the built-in demo token.
              </p>
            </div>
          </div>

          <div className="hero-stat-grid auth-stat-grid">
            <div className="hero-stat-card">
              <span>Session mode</span>
              <strong>HttpOnly</strong>
              <small>Cookies, not local storage</small>
            </div>
            <div className="hero-stat-card">
              <span>Hashing</span>
              <strong>Bcrypt</strong>
              <small>Password protection on the backend</small>
            </div>
            <div className="hero-stat-card">
              <span>Guest mode</span>
              <strong>Demo token</strong>
              <small>Browse without creating an account</small>
            </div>
          </div>
        </section>

        <section className="glass-card auth-card">
          <div className="auth-header">
            <h2>{isLogin ? "Sign in" : "Create your account"}</h2>
            <p>{isLogin ? "Return to your signal workspace." : "Create a secure session to save your state."}</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <label className="auth-field">
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </label>

            <label className="auth-field">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete={isLogin ? "current-password" : "new-password"}
                minLength={8}
                required
              />
            </label>

            {!isLogin ? (
              <label className="auth-field">
                <span>Confirm password</span>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </label>
            ) : null}

            {onAuth.error ? <div className="auth-error">{onAuth.error}</div> : null}

            <div className="auth-actions">
              <button type="submit" className="primary-button auth-button" disabled={onAuth.loading}>
                {onAuth.loading ? "Working..." : isLogin ? "Sign in" : "Create account"}
              </button>
              <button
                type="button"
                className="secondary-button auth-button"
                onClick={async () => {
                  await onAuth.guestLogin();
                }}
                disabled={onAuth.loading}
              >
                Continue as guest
              </button>
            </div>
          </form>

          <div className="auth-footer">
            <span>
              {isLogin ? "Need an account?" : "Already have an account?"}
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
                {isLogin ? "Register" : "Sign in"}
              </button>
            </span>
          </div>
        </section>
      </section>
    </div>
  );
}
