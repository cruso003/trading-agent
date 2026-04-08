import { useEffect, useRef, useState, useCallback } from 'react';

export interface SSEEvent {
  type: string;
  data: Record<string, unknown>;
  timestamp?: string;
}

interface UseSSEOptions {
  url: string;
  onEvent?: (event: SSEEvent) => void;
}

export function useSSE({ url, onEvent }: UseSSEOptions) {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [agentStatus, setAgentStatus] = useState<Record<string, unknown>>({});
  const [recentEvents, setRecentEvents] = useState<SSEEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => {
      setConnected(false);
      es.close();
      setTimeout(connect, 3000);
    };

    const eventTypes = [
      'agent_status', 'window_open', 'window_closed',
      'prefilter_pass', 'prefilter_fail', 'news_alert',
      'analysis_done', 'gpt_confirm', 'gpt_challenge',
      'trade_placed', 'trade_closed', 'tp1_hit',
      'risk_blocked', 'b_alert', 'skip_logged', 'heartbeat',
    ];

    eventTypes.forEach(type => {
      es.addEventListener(type, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data) as Record<string, unknown>;
          const event: SSEEvent = {
            type,
            data,
            timestamp: new Date().toISOString(),
          };
          setLastEvent(event);
          setRecentEvents(prev => [event, ...prev].slice(0, 100));

          if (type === 'agent_status') {
            setAgentStatus(data);
          }

          onEventRef.current?.(event);
        } catch {
          // Ignore parse errors
        }
      });
    });
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      eventSourceRef.current?.close();
    };
  }, [connect]);

  return { connected, lastEvent, agentStatus, recentEvents };
}
