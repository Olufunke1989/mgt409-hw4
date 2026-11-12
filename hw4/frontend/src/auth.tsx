import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  name: string;
  email: string;
}

export interface SignupData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

/** Error from the server, with an overall message and optional per-field messages. */
export class AuthError extends Error {
  fields: Record<string, string>;
  constructor(message: string, fields: Record<string, string> = {}) {
    super(message);
    this.fields = fields;
  }
}

async function post(url: string, body?: unknown): Promise<User> {
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new AuthError("We couldn't reach the shop server. Please try again.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data?.detail ?? {};
    throw new AuthError(detail.message ?? "Something went wrong. Please try again.", detail.fields ?? {});
  }
  return data as User;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  signup: (data: SignupData) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On page load, ask the server whether this browser is already logged in.
  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((u) => setUser(u))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const u = await post("/api/auth/login", { email, password });
    setUser(u);
    return u;
  }, []);

  const signup = useCallback(async (data: SignupData) => {
    const u = await post("/api/auth/signup", data);
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" }).catch(() => null);
    setUser(null);
  }, []);

  return <AuthContext.Provider value={{ user, loading, login, signup, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
