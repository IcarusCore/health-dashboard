// SettingsPage.tsx
import { useEffect, useState } from 'react';
import api from '../services/api';
import { useAuthStore } from '../hooks/useAuthStore';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const { user, updateUser } = useAuthStore();
  const [settings, setSettings] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const [profile, setProfile] = useState({
    email: user?.email || '',
    username: user?.username || '',
    full_name: user?.full_name || '',
    timezone: user?.timezone || 'UTC',
  });

  const [goals, setGoals] = useState({
    daily_steps_goal: 10000,
    daily_calories_goal: 2000,
    daily_active_minutes_goal: 30,
    sleep_hours_goal: 8,
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
      setGoals({
        daily_steps_goal: data.daily_steps_goal,
        daily_calories_goal: data.daily_calories_goal,
        daily_active_minutes_goal: data.daily_active_minutes_goal,
        sleep_hours_goal: data.sleep_hours_goal,
      });
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setIsSaving(true);
    try {
      const updated = await api.updateProfile(profile);
      updateUser(updated);
      toast.success('Profile updated');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveGoals = async () => {
    setIsSaving(true);
    try {
      await api.updateSettings(goals);
      toast.success('Goals updated');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update goals');
    } finally {
      setIsSaving(false);
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
    <div className="space-y-6 animate-in max-w-2xl">
      <h1 className="text-2xl font-bold text-dark-50">Settings</h1>

      {/* Profile Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Profile</h3>
        <div className="space-y-4">
          <div>
            <label className="label">Email</label>
            <input
              type="email"
              value={profile.email}
              onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              className="input"
            />
          </div>
          <div>
            <label className="label">Username</label>
            <input
              type="text"
              value={profile.username}
              onChange={(e) => setProfile({ ...profile, username: e.target.value })}
              className="input"
            />
          </div>
          <div>
            <label className="label">Full Name</label>
            <input
              type="text"
              value={profile.full_name}
              onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
              className="input"
            />
          </div>
          <div>
            <label className="label">Timezone</label>
            <select
              value={profile.timezone}
              onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
              className="input"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">Eastern Time</option>
              <option value="America/Chicago">Central Time</option>
              <option value="America/Denver">Mountain Time</option>
              <option value="America/Los_Angeles">Pacific Time</option>
              <option value="Europe/London">London</option>
              <option value="Europe/Paris">Paris</option>
              <option value="Asia/Tokyo">Tokyo</option>
            </select>
          </div>
          <button onClick={handleSaveProfile} disabled={isSaving} className="btn-primary">
            {isSaving ? 'Saving...' : 'Save Profile'}
          </button>
        </div>
      </div>

      {/* Health Goals */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Health Goals</h3>
        <div className="space-y-4">
          <div>
            <label className="label">Daily Steps Goal</label>
            <input
              type="number"
              value={goals.daily_steps_goal}
              onChange={(e) => setGoals({ ...goals, daily_steps_goal: parseInt(e.target.value) || 0 })}
              className="input"
              min="1000"
              max="100000"
            />
          </div>
          <div>
            <label className="label">Daily Active Calories Goal</label>
            <input
              type="number"
              value={goals.daily_calories_goal}
              onChange={(e) => setGoals({ ...goals, daily_calories_goal: parseInt(e.target.value) || 0 })}
              className="input"
              min="100"
              max="10000"
            />
          </div>
          <div>
            <label className="label">Daily Exercise Minutes Goal</label>
            <input
              type="number"
              value={goals.daily_active_minutes_goal}
              onChange={(e) => setGoals({ ...goals, daily_active_minutes_goal: parseInt(e.target.value) || 0 })}
              className="input"
              min="5"
              max="300"
            />
          </div>
          <div>
            <label className="label">Sleep Hours Goal</label>
            <input
              type="number"
              value={goals.sleep_hours_goal}
              onChange={(e) => setGoals({ ...goals, sleep_hours_goal: parseFloat(e.target.value) || 0 })}
              className="input"
              min="4"
              max="12"
              step="0.5"
            />
          </div>
          <button onClick={handleSaveGoals} disabled={isSaving} className="btn-primary">
            {isSaving ? 'Saving...' : 'Save Goals'}
          </button>
        </div>
      </div>

      {/* Data Management */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Data Management</h3>
        <div className="space-y-4">
          <button
            onClick={() => {
              api.exportData('json').then((blob) => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'health_export.json';
                a.click();
                toast.success('Export downloaded');
              }).catch(() => toast.error('Export failed'));
            }}
            className="btn-secondary w-full"
          >
            Export All Data (JSON)
          </button>
          <button
            onClick={() => {
              api.exportData('csv').then((blob) => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'health_export.csv';
                a.click();
                toast.success('Export downloaded');
              }).catch(() => toast.error('Export failed'));
            }}
            className="btn-secondary w-full"
          >
            Export Measurements (CSV)
          </button>
        </div>
      </div>
    </div>
  );
}
