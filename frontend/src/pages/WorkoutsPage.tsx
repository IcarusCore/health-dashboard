// WorkoutsPage.tsx
import { useEffect, useState } from 'react';
import api from '../services/api';
import { format } from 'date-fns';
import { BoltIcon, ClockIcon, FireIcon, HeartIcon } from '@heroicons/react/24/outline';

export default function WorkoutsPage() {
  const [workouts, setWorkouts] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [streak, setStreak] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [workoutsData, summaryData, streakData] = await Promise.all([
        api.getWorkouts({ page_size: 20 }),
        api.getWorkoutSummary(),
        api.getWorkoutStreak(),
      ]);
      setWorkouts(workoutsData);
      setSummary(summaryData);
      setStreak(streakData);
    } catch (error) {
      console.error('Failed to fetch workouts:', error);
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
      <h1 className="text-2xl font-bold text-dark-50">Workouts</h1>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-dark-50">{summary?.total_workouts || 0}</p>
          <p className="text-sm text-dark-400">Total Workouts</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-dark-50">{summary?.total_duration_minutes?.toFixed(0) || 0}</p>
          <p className="text-sm text-dark-400">Total Minutes</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-dark-50">{summary?.total_distance_km?.toFixed(1) || 0}</p>
          <p className="text-sm text-dark-400">Total km</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-dark-50">{streak?.current_streak_days || 0}</p>
          <p className="text-sm text-dark-400">Day Streak</p>
        </div>
      </div>

      {/* Workout List */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Recent Workouts</h3>
        <div className="space-y-4">
          {workouts.length === 0 ? (
            <p className="text-dark-400 text-center py-8">No workouts recorded yet</p>
          ) : (
            workouts.map((workout) => (
              <div
                key={workout.id}
                className="flex items-center gap-4 p-4 bg-dark-800 rounded-lg"
              >
                <div className="p-3 bg-success/20 rounded-lg">
                  <BoltIcon className="w-6 h-6 text-success" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-dark-100">
                    {workout.workout_type?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                  </p>
                  <p className="text-sm text-dark-400">
                    {format(new Date(workout.start_time), 'MMM d, yyyy • h:mm a')}
                  </p>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-center">
                    <p className="font-semibold text-dark-100">{workout.duration_minutes?.toFixed(0)}</p>
                    <p className="text-dark-400">min</p>
                  </div>
                  {workout.distance_km && (
                    <div className="text-center">
                      <p className="font-semibold text-dark-100">{workout.distance_km?.toFixed(2)}</p>
                      <p className="text-dark-400">km</p>
                    </div>
                  )}
                  {workout.total_calories && (
                    <div className="text-center">
                      <p className="font-semibold text-dark-100">{workout.total_calories?.toFixed(0)}</p>
                      <p className="text-dark-400">cal</p>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
