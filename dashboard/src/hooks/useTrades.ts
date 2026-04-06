import { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000/api';

export function useTrades(limit = 50) {
  const [trades, setTrades] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/trades?limit=${limit}`);
      const data = await res.json();
      setTrades(data);
    } catch {
      console.error('Failed to fetch trades');
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [refresh]);

  return { trades, loading, refresh };
}

export function useDecisions(limit = 50) {
  const [decisions, setDecisions] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/decisions?limit=${limit}`);
      const data = await res.json();
      setDecisions(data);
    } catch {
      console.error('Failed to fetch decisions');
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, [refresh]);

  return { decisions, loading, refresh };
}

export function useAnalytics() {
  const [summary, setSummary] = useState<Record<string, unknown>>({});
  const [daily, setDaily] = useState<Record<string, unknown>[]>([]);
  const [grades, setGrades] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [sumRes, dailyRes, gradeRes] = await Promise.all([
        fetch(`${API_BASE}/analytics/summary`),
        fetch(`${API_BASE}/analytics/daily`),
        fetch(`${API_BASE}/analytics/grades`),
      ]);
      setSummary(await sumRes.json());
      setDaily(await dailyRes.json());
      setGrades(await gradeRes.json());
    } catch {
      console.error('Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 60000);
    return () => clearInterval(interval);
  }, [refresh]);

  return { summary, daily, grades, loading, refresh };
}
