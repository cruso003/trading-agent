import { useSSE } from '../hooks/useSSE';
import { useTrades, useDecisions } from '../hooks/useTrades';
import AgentStatus from '../components/AgentStatus';
import TradeCard from '../components/TradeCard';
import AnalysisPanel from '../components/AnalysisPanel';
import Controls from '../components/Controls';
import './Dashboard.css';

export default function Dashboard() {
  const { connected, agentStatus } = useSSE({
    url: 'http://localhost:8000/api/stream',
  });
  const { trades } = useTrades(10);
  const { decisions } = useDecisions(8);

  return (
    <div className="dashboard">
      <div className="dashboard-grid">
        {/* Top: Status + Controls */}
        <div className="grid-status">
          <AgentStatus status={agentStatus} connected={connected} />
        </div>
        <div className="grid-controls">
          <Controls />
        </div>

        {/* Middle: Trades + Analysis */}
        <div className="grid-trades">
          <TradeCard trades={trades} />
        </div>
        <div className="grid-analysis">
          <AnalysisPanel decisions={decisions} />
        </div>
      </div>
    </div>
  );
}
