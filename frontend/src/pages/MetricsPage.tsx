// MetricsPage.tsx
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { format, subDays } from 'date-fns';
import { formatHoursMinutes, kgToLbs, formatBodyFatPercent } from '../utils/formatters';


// Helper to format stat values based on metric type
const formatStatValue = (value: number | null | undefined, metricKey: string): string => {
  if (value === null || value === undefined) return '--';
  
  // Weight metrics - convert kg to lbs
  if (metricKey === 'weight' || metricKey === 'lean_body_mass') {
    const lbs = kgToLbs(value);
    return lbs ? lbs.toFixed(1) : '--';
  }
  
  // Body fat - convert decimal to percentage
  if (metricKey === 'body_fat') {
    return formatBodyFatPercent(value);
  }
  
  // Sleep duration - format as h:mm
  if (metricKey === 'sleep_duration') {
    return formatHoursMinutes(value);
  }
  
  // Default formatting
  return value < 1 ? value.toFixed(2) : value.toFixed(1);
};

export default function MetricsPage() {
  const { metricKey } = useParams();
  const [metrics, setMetrics] = useState<any[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>(metricKey || 'heart_rate');
  const [timeseriesData, setTimeseriesData] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
  }, []);

  useEffect(() => {
    if (selectedMetric) {
      fetchMetricData(selectedMetric);
    }
  }, [selectedMetric]);

  const fetchMetrics = async () => {
    try {
      const data = await api.getMetrics();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  const fetchMetricData = async (metric: string) => {
    setIsLoading(true);
    try {
      const [timeseries, metricStats] = await Promise.all([
        api.getMeasurementTimeseries(metric, format(subDays(new Date(), 30), 'yyyy-MM-dd')),
        api.getMeasurementStats(metric),
      ]);
      
      if (timeseries?.data) {
        setTimeseriesData(timeseries.data.map((d: any) => {
          let value = d.value;
          // Convert units based on metric
          if ((metric === 'weight' || metric === 'lean_body_mass') && value !== null) {
            value = value * 2.20462; // kg to lbs
          } else if (metric === 'body_fat' && value !== null) {
            value = value * 100; // decimal to percent
          }
          return {
            date: format(new Date(d.timestamp), 'MM/dd'),
            value: value,
          };
        }));
      }
      setStats(metricStats);
    } catch (error) {
      console.error('Failed to fetch metric data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const categories = [...new Set(metrics.map(m => m.category))];

  return (
    <div className="space-y-6 animate-in">
      <h1 className="text-2xl font-bold text-dark-50">Health Metrics</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Metric Selector */}
        <div className="card lg:col-span-1">
          <h3 className="text-lg font-semibold text-dark-100 mb-4">Select Metric</h3>
          <div className="space-y-4">
            {categories.map(category => (
              <div key={category}>
                <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">
                  {category}
                </p>
                <div className="space-y-1">
                  {metrics.filter(m => m.category === category).map(metric => (
                    <button
                      key={metric.metric_key}
                      onClick={() => setSelectedMetric(metric.metric_key)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        selectedMetric === metric.metric_key
                          ? 'bg-primary-500/20 text-primary-400'
                          : 'text-dark-300 hover:bg-dark-800'
                      }`}
                    >
                      {metric.display_name}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Chart and Stats */}
        <div className="lg:col-span-3 space-y-6">
          {/* Stats */}
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="card text-center">
                <p className="text-2xl font-bold text-dark-50">{formatStatValue(stats.current_value, selectedMetric)}</p>
                <p className="text-sm text-dark-400">Current</p>
              </div>
              <div className="card text-center">
                <p className="text-2xl font-bold text-dark-50">{formatStatValue(stats.average, selectedMetric)}</p>
                <p className="text-sm text-dark-400">Average</p>
              </div>
              <div className="card text-center">
                <p className="text-2xl font-bold text-dark-50">{formatStatValue(stats.minimum, selectedMetric)}</p>
                <p className="text-sm text-dark-400">Minimum</p>
              </div>
              <div className="card text-center">
                <p className="text-2xl font-bold text-dark-50">{formatStatValue(stats.maximum, selectedMetric)}</p>
                <p className="text-sm text-dark-400">Maximum</p>
              </div>
            </div>
          )}

          {/* Chart */}
          <div className="card">
            <h3 className="text-lg font-semibold text-dark-100 mb-4">
              {stats?.display_name || selectedMetric} (Last 30 Days){selectedMetric === 'weight' || selectedMetric === 'lean_body_mass' ? ' - lbs' : selectedMetric === 'body_fat' ? ' - %' : selectedMetric === 'sleep_duration' ? ' - hrs' : ''}
            </h3>
            <div className="h-80">
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeseriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                    <YAxis stroke="#64748b" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                      }}
                      formatter={(value: number) => {
                        if (selectedMetric === 'sleep_duration') {
                          return [formatHoursMinutes(value), 'Duration'];
                        }
                        return [value?.toFixed(1), 'Value'];
                      }}
                    />
                    <Line
                      connectNulls={true}
                      type="monotone"
                      dataKey="value"
                      stroke="#06b6d4"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
