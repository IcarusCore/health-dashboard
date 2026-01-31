import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import toast from 'react-hot-toast';
import {
  HeartIcon,
  FireIcon,
  MoonIcon,
  ScaleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BoltIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { format, subDays } from 'date-fns';
import { formatHoursMinutes } from '../utils/formatters';

interface DashboardOverview {
  today: any;
  yesterday: any;
  steps_streak: number;
  exercise_streak: number;
  sleep_streak: number;
  week_avg_steps: number | null;
  week_avg_sleep_hours: number | null;
  week_avg_activity_score: number | null;
  unread_insights: number;
  last_sync_at: string | null;
}

function StatCard({
  title,
  value,
  unit,
  change,
  changeDirection,
  icon: Icon,
  iconBg,
  goal,
  goalPercent,
}: {
  title: string;
  value: string | number | null;
  unit?: string;
  change?: number | null;
  changeDirection?: 'up' | 'down' | 'stable';
  icon: any;
  iconBg: string;
  goal?: number;
  goalPercent?: number | null;
}) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className={`p-2 rounded-lg ${iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
        {change !== undefined && change !== null && (
          <div
            className={`flex items-center text-sm ${
              changeDirection === 'up'
                ? 'text-success'
                : changeDirection === 'down'
                ? 'text-error'
                : 'text-dark-400'
            }`}
          >
            {changeDirection === 'up' ? (
              <ArrowTrendingUpIcon className="w-4 h-4 mr-1" />
            ) : changeDirection === 'down' ? (
              <ArrowTrendingDownIcon className="w-4 h-4 mr-1" />
            ) : null}
            {Math.abs(change).toFixed(1)}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-dark-50">
          {value ?? '--'}
          {unit && <span className="text-lg font-normal text-dark-400 ml-1">{unit}</span>}
        </p>
        <p className="text-sm text-dark-400 mt-1">{title}</p>
      </div>
      {goalPercent !== undefined && goalPercent !== null && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-dark-400 mb-1">
            <span>Goal progress</span>
            <span>{Math.min(goalPercent, 100).toFixed(0)}%</span>
          </div>
          <div className="progress-bar">
            <div
              className={`progress-bar-fill ${
                goalPercent >= 100 ? 'bg-success' : 'bg-primary-500'
              }`}
              style={{ width: `${Math.min(goalPercent, 100)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function StreakCard({
  title,
  days,
  icon: Icon,
}: {
  title: string;
  days: number;
  icon: any;
}) {
  return (
    <div className="flex items-center gap-3 p-4 bg-dark-800 rounded-lg">
      <div className="p-2 bg-accent-500/20 rounded-lg">
        <Icon className="w-5 h-5 text-accent-400" />
      </div>
      <div>
        <p className="text-xl font-bold text-dark-50">{days} days</p>
        <p className="text-sm text-dark-400">{title}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [stepsData, setStepsData] = useState<any[]>([]);
  const [sleepData, setSleepData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [overviewData, stepsTimeseries, sleepTimeseries] = await Promise.all([
        api.getDashboardOverview(),
        api.getMeasurementTimeseries('steps', format(subDays(new Date(), 14), 'yyyy-MM-dd')),
        api.getSleepStages(format(subDays(new Date(), 14), 'yyyy-MM-dd')),
      ]);

      setOverview(overviewData);

      if (stepsTimeseries?.data) {
        setStepsData(
          stepsTimeseries.data.map((d: any) => ({
            date: format(new Date(d.timestamp), 'MM/dd'),
            steps: d.value ? Math.round(d.value) : 0,
          }))
        );
      }

      if (sleepTimeseries) {
        setSleepData(
          sleepTimeseries.map((s: any) => ({
            date: format(new Date(s.date), 'MM/dd'),
            hours: s.total_hours || 0,
            deep: s.deep_hours || 0,
            rem: s.rem_hours || 0,
            light: s.light_hours || 0,
          }))
        );
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
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

  const today = overview?.today;

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-dark-50">Dashboard</h1>
          <p className="text-dark-400">
            {format(new Date(), 'EEEE, MMMM d, yyyy')}
          </p>
        </div>
        {overview?.unread_insights !== undefined && overview.unread_insights > 0 && (
          <Link
            to="/insights"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500/20 text-primary-400 rounded-lg hover:bg-primary-500/30 transition-colors"
          >
            <span>{overview.unread_insights} new insights</span>
            <ArrowTrendingUpIcon className="w-4 h-4" />
          </Link>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Steps Today"
          value={today?.steps?.toLocaleString()}
          icon={FireIcon}
          iconBg="bg-success/20 text-success"
          goalPercent={today?.steps_goal_percent}
        />
        <StatCard
          title="Active Calories"
          value={today?.active_calories?.toLocaleString()}
          unit="kcal"
          icon={BoltIcon}
          iconBg="bg-warning/20 text-warning"
          goalPercent={today?.calories_goal_percent}
        />
        <StatCard
          title="Sleep"
          value={formatHoursMinutes(today?.sleep_duration_hours)}
          unit="hrs"
          icon={MoonIcon}
          iconBg="bg-info/20 text-info"
          goalPercent={today?.sleep_goal_percent}
        />
        <StatCard
          title="Resting HR"
          value={today?.resting_heart_rate}
          unit="bpm"
          icon={HeartIcon}
          iconBg="bg-error/20 text-error"
        />
      </div>

      {/* Streaks */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StreakCard title="Steps Streak" days={overview?.steps_streak || 0} icon={FireIcon} />
        <StreakCard title="Exercise Streak" days={overview?.exercise_streak || 0} icon={BoltIcon} />
        <StreakCard title="Sleep Streak" days={overview?.sleep_streak || 0} icon={MoonIcon} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Steps Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-dark-100 mb-4">Steps (Last 14 Days)</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stepsData}>
                <defs>
                  <linearGradient id="stepsGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="steps"
                  stroke="#10b981"
                  strokeWidth={2}
                  fill="url(#stepsGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sleep Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-dark-100 mb-4">Sleep (Last 14 Days)</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sleepData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number, name: string) => [formatHoursMinutes(value), name]}
                />
                <Bar dataKey="deep" stackId="sleep" fill="#1d4ed8" name="Deep" />
                <Bar dataKey="rem" stackId="sleep" fill="#7c3aed" name="REM" />
                <Bar dataKey="light" stackId="sleep" fill="#06b6d4" name="Light" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Weekly Averages */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Weekly Averages</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="text-center">
            <p className="text-3xl font-bold text-dark-50">
              {overview?.week_avg_steps?.toLocaleString() ?? '--'}
            </p>
            <p className="text-sm text-dark-400">Avg Daily Steps</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-dark-50">
              {formatHoursMinutes(overview?.week_avg_sleep_hours)}
              <span className="text-lg font-normal text-dark-400 ml-1">hrs</span>
            </p>
            <p className="text-sm text-dark-400">Avg Sleep</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-dark-50">
              {overview?.week_avg_activity_score ?? '--'}
            </p>
            <p className="text-sm text-dark-400">Avg Activity Score</p>
          </div>
        </div>
      </div>
    </div>
  );
}
