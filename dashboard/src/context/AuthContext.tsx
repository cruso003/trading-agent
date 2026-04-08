import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';

const API_BASE = 'http://localhost:8000/api';
const TOKEN_KEY = 'apexgold_token';

interface User {
  id: number;
  name: string;
  email: string;
  role: 'owner' | 'mentee' | 'trial';
  status: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  isOwner: boolean;
  isMentee: boolean;
}

interface JwtPayload {
  exp?: number;
  sub?: string;
}

const AuthContext = createContext<AuthContextType | null>(null);

function isTokenExpired(token: string): boolean {
  try {
    const decoded = jwtDecode<JwtPayload>(token);
    if (!decoded.exp) return false;
    return decoded.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const clearAuth = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setToken(null);
  }, []);

  const fetchMe = useCallback(async (t: string): Promise<User | null> => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${t}` },
      });
      if (!res.ok) return null;
      const data = await res.json() as User;
      return data;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    async function init() {
      const stored = localStorage.getItem(TOKEN_KEY);
      if (!stored || isTokenExpired(stored)) {
        clearAuth();
        setLoading(false);
        return;
      }
      const me = await fetchMe(stored);
      if (!me) {
        clearAuth();
      } else {
        setToken(stored);
        setUser(me);
      }
      setLoading(false);
    }
    init();
  }, [clearAuth, fetchMe]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' })) as { detail?: string };
      throw new Error(err.detail || 'Invalid credentials');
    }
    const data = await res.json() as { access_token: string };
    const t = data.access_token;
    localStorage.setItem(TOKEN_KEY, t);
    setToken(t);
    const me = await fetchMe(t);
    if (!me) {
      clearAuth();
      throw new Error('Failed to load user profile');
    }
    setUser(me);
    return me;
  }, [clearAuth, fetchMe]);

  const logout = useCallback(() => {
    clearAuth();
    navigate('/login');
  }, [clearAuth, navigate]);

  const isOwner = user?.role === 'owner';
  const isMentee = user?.role === 'mentee' || user?.role === 'trial';

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, isOwner, isMentee }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
