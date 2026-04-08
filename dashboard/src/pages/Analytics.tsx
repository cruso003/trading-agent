import { useAnalytics } from '../hooks/useTrades';
import PerformanceCharts from '../components/PerformanceCharts';
import './Analytics.css';

export default function Analytics() {
  const { summary, daily, grades, loading } = useAnalytics();

  if (loading) {
    return (
      <div className="analytics-page">
        <div className="analytics-loading">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <div className="analytics-page-header">
        <div className="analytics-page-title">Performance Analytics</div>
        <div className="analytics-page-sub">XAUUSDm · All Time</div>
      </div>
      <PerformanceCharts summary={summary} daily={daily} grades={grades} />
    </div>
  );
}
