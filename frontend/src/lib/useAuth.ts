import { useEffect, useState } from "react";
import * as authService from "./auth";

export interface User {
  email: string;
  role: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function checkAuth() {
      try {
        const response = await authService.me();
        setUser({
          email: response.sub,
          role: response.role,
        });
        setError(null);
      } catch (err) {
        setUser(null);
        // Not logged in is not an error
      } finally {
        setLoading(false);
      }
    }

    checkAuth();
  }, []);

  const register = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      await authService.register(email, password);
      const response = await authService.login(email, password);
      setUser({
        email: response.email,
        role: response.role,
      });
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed";
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authService.login(email, password);
      setUser({
        email: response.email,
        role: response.role,
      });
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const guestLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await authService.guestLogin();
      setUser({
        email: response.email,
        role: response.role,
      });
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Guest login failed";
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
      setUser(null);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Logout failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return { user, loading, error, register, login, guestLogin, logout };
}
