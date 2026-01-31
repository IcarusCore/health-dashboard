// SleepPage.tsx
import { useEffect, useState } from 'react';
import api from '../services/api';
import { format } from 'date-fns';
import { formatHoursMinutes } from '../utils/formatters';
import { MoonIcon } from '@heroicons/react/24/outline';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function SleepPage() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [stages, setStages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [sessionsData, summaryData, stagesData] = await Promise.all([
        api.getSleepSessions({ page_size: 14 }),
        api.getSleepSummary(),
        api.getSleepStages(),
      ]);
      setSessions(sessionsData);
      setSummary(summaryData);
      setStages(stagesData.map((s: any) => ({
        date: format(new Date(s.date), 'MM/dd'),
        deep: s.deep_hours || 0,
        light: s.light_hours || 0,
        rem: s.rem_hours || 0,
        awake: s.awake_hours || 0,
      })));
    } catch (error) {
      console.error('Failed to fetch sleep data:', error);
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
      <h1 className="text-2xl font-bold text-dark-50">Sleep</h1>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-dark-50">{formatHoursMinutes(summary?.avg_duration_hours)}</p>
          <p className="text-sm text-dark-400">Avg Duration (hrs)</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-dark-50">{summary?.avg_efficiency?.toFixed(0) || '--'}%</p>
          <p className="text-sm text-dark-400">Avg Efficiency</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-dark-50">{summary?.avg_sleep_score?.toFixed(0) || '--'}</p>
          <p className="text-sm text-dark-400">Avg Sleep Score</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-dark-50">{summary?.consistency_score?.toFixed(0) || '--'}</p>
          <p className="text-sm text-dark-400">Consistency</p>
        </div>
      </div>

      {/* Sleep Stages Chart */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Sleep Stages (Last 14 Days)</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stages}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                formatter={(value: number, name: string) => [formatHoursMinutes(value), name]}
              />
              <Legend />
              <Bar dataKey="deep" stackId="a" fill="#1d4ed8" name="Deep" />
              <Bar dataKey="light" stackId="a" fill="#06b6d4" name="Light" />
              <Bar dataKey="rem" stackId="a" fill="#8b5cf6" name="REM" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Recent Sleep Sessions</h3>
        <div className="space-y-3">
          {sessions.map((session) => (
            <div key={session.id} className="flex items-center gap-4 p-4 bg-dark-800 rounded-lg">
              <div className="p-3 bg-info/20 rounded-lg">
                <MoonIcon className="w-6 h-6 text-info" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-dark-100">{session.duration_hours?.toFixed(1)} hours</p>
                <p className="text-sm text-dark-400">{format(new Date(session.start_time), 'MMM d, yyyy')}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-dark-100">Score: {session.sleep_score || '--'}</p>
                <p className="text-sm text-dark-400">{session.sleep_efficiency?.toFixed(0)}% efficiency</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
