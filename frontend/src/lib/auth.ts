export interface User {
  id: number;
  email: string;
  role: string;
}

export interface RegisterResponse {
  id: number;
  email: string;
  role: string;
}

export interface LoginResponse {
  id: number;
  email: string;
  role: string;
}

export interface MeResponse {
  sub: string;
  role: string;
}

export interface GuestAuthResponse {
  access_token: string;
  token_type: string;
}

const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function authRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Ignore JSON parse failures
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export async function register(email: string, password: string): Promise<RegisterResponse> {
  return authRequest<RegisterResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return authRequest<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function logout(): Promise<{ status: string }> {
  return authRequest<{ status: string }>("/api/auth/logout", {
    method: "POST",
  });
}

export async function me(): Promise<MeResponse> {
  return authRequest<MeResponse>("/api/auth/me");
}

export async function guestLogin(): Promise<GuestAuthResponse> {
  return authRequest<GuestAuthResponse>("/api/auth/dev-token?subject=frontend-demo&role=guest");
}
