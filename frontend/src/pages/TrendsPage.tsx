// TrendsPage.tsx
import { useEffect, useState } from 'react';
import api from '../services/api';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon, MinusIcon } from '@heroicons/react/24/outline';

export default function TrendsPage() {
  const [trends, setTrends] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const metricsToTrack = ['steps', 'resting_heart_rate', 'heart_rate_variability', 'weight', 'sleep_duration'];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [reportData, ...trendData] = await Promise.all([
        api.getHealthReport(),
        ...metricsToTrack.map(m => api.getTrend(m, 30)),
      ]);
      setReport(reportData);
      setTrends(trendData);
    } catch (error) {
      console.error('Failed to fetch trends:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">
      <h1 className="text-2xl font-bold text-dark-50">Trends & Analysis</h1>

      {/* Health Report Summary */}
      {report && (
        <div className="card">
          <h3 className="text-lg font-semibold text-dark-100 mb-4">30-Day Health Report</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-dark-50">{report.overall_health_score || '--'}</p>
              <p className="text-sm text-dark-400">Overall Score</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-dark-50">{report.activity_score || '--'}</p>
              <p className="text-sm text-dark-400">Activity Score</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-dark-50">{report.sleep_score || '--'}</p>
              <p className="text-sm text-dark-400">Sleep Score</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-dark-50">{report.recovery_score || '--'}</p>
              <p className="text-sm text-dark-400">Recovery Score</p>
            </div>
          </div>
          <div className="text-sm text-dark-400">
            Data from {report.days_with_data} of {report.total_days} days ({report.data_completeness_percent}% complete)
          </div>
        </div>
      )}

      {/* Metric Trends */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Metric Trends (30 Days)</h3>
        <div className="space-y-4">
          {trends.map((trend, i) => (
            <div key={metricsToTrack[i]} className="flex items-center justify-between p-4 bg-dark-800 rounded-lg">
              <div className="flex items-center gap-4">
                <div className={`p-2 rounded-lg ${
                  trend.direction === 'increasing' ? 'bg-success/20' : 
                  trend.direction === 'decreasing' ? 'bg-error/20' : 'bg-dark-700'
                }`}>
                  {trend.direction === 'increasing' ? (
                    <ArrowTrendingUpIcon className="w-5 h-5 text-success" />
                  ) : trend.direction === 'decreasing' ? (
                    <ArrowTrendingDownIcon className="w-5 h-5 text-error" />
                  ) : (
                    <MinusIcon className="w-5 h-5 text-dark-400" />
                  )}
                </div>
                <div>
                  <p className="font-semibold text-dark-100">{trend.display_name}</p>
                  <p className="text-sm text-dark-400">
                    {trend.start_value?.toFixed(1)} → {trend.end_value?.toFixed(1)}
                  </p>
                </div>
              </div>
              <div className={`text-lg font-semibold ${
                trend.direction === 'increasing' ? 'text-success' :
                trend.direction === 'decreasing' ? 'text-error' : 'text-dark-400'
              }`}>
                {trend.change_percent > 0 ? '+' : ''}{trend.change_percent?.toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {report?.recommendations && report.recommendations.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-dark-100 mb-4">Recommendations</h3>
          <ul className="space-y-2">
            {report.recommendations.map((rec: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-dark-300">
                <span className="text-primary-400">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
