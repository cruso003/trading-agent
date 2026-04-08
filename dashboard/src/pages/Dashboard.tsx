import { useSSE } from '../hooks/useSSE';
import { useTrades, useDecisions } from '../hooks/useTrades';
import LeftPanel from '../components/LeftPanel';
import TradesTable from '../components/TradesTable';
import ActivityFeed from '../components/ActivityFeed';
import './Dashboard.css';

export default function Dashboard() {
  const { connected, agentStatus, recentEvents } = useSSE({ url: 'http://localhost:8000/api/stream' });
  const { trades } = useTrades(20);
  const { decisions } = useDecisions(30);

  return (
    <div className="dashboard">
      <div className="left-panel">
        <LeftPanel status={agentStatus} connected={connected} />
      </div>
      <div className="center-panel">
        <TradesTable trades={trades} />
      </div>
      <div className="right-panel">
        <ActivityFeed decisions={decisions} recentEvents={recentEvents} />
      </div>
    </div>
  );
}
