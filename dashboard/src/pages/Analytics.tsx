import { useAnalytics } from '../hooks/useTrades';
import PerformanceCharts from '../components/PerformanceCharts';
import './Analytics.css';

export default function Analytics() {
  const { summary, daily, grades, loading } = useAnalytics();

  if (loading) {
    return (
      <div className="analytics-page">
        <div className="loading-state">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <PerformanceCharts summary={summary} daily={daily} grades={grades} />
    </div>
  );
}
