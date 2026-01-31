// InsightsPage.tsx
import { useEffect, useState } from 'react';
import api from '../services/api';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { LightBulbIcon, CheckCircleIcon, XMarkIcon, StarIcon } from '@heroicons/react/24/outline';

export default function InsightsPage() {
  const [insights, setInsights] = useState<any[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    try {
      const data = await api.getInsights({});
      setInsights(data.insights);
      setUnreadCount(data.unread_count);
    } catch (error) {
      console.error('Failed to fetch insights:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMarkRead = async (id: string) => {
    try {
      await api.markInsightRead(id);
      setInsights(insights.map(i => i.id === id ? { ...i, is_read: true } : i));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (error) {
      toast.error('Failed to mark as read');
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      await api.dismissInsight(id);
      setInsights(insights.filter(i => i.id !== id));
      toast.success('Insight dismissed');
    } catch (error) {
      toast.error('Failed to dismiss');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllInsightsRead();
      setInsights(insights.map(i => ({ ...i, is_read: true })));
      setUnreadCount(0);
      toast.success('All insights marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'positive': return 'border-success bg-success/10';
      case 'warning': return 'border-warning bg-warning/10';
      case 'alert': return 'border-error bg-error/10';
      default: return 'border-info bg-info/10';
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-50">Health Insights</h1>
          {unreadCount > 0 && (
            <p className="text-dark-400">{unreadCount} unread insights</p>
          )}
        </div>
        {unreadCount > 0 && (
          <button onClick={handleMarkAllRead} className="btn-secondary">
            Mark all read
          </button>
        )}
      </div>

      {insights.length === 0 ? (
        <div className="card text-center py-12">
          <LightBulbIcon className="w-12 h-12 text-dark-500 mx-auto mb-4" />
          <p className="text-dark-400">No insights yet. Import your health data to get started!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {insights.map((insight) => (
            <div
              key={insight.id}
              className={`card border-l-4 ${getSeverityColor(insight.severity)} ${
                !insight.is_read ? 'ring-2 ring-primary-500/30' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`badge badge-${insight.severity === 'positive' ? 'success' : insight.severity === 'warning' ? 'warning' : insight.severity === 'alert' ? 'error' : 'info'}`}>
                      {insight.insight_type}
                    </span>
                    <span className="badge badge-primary">{insight.category}</span>
                    {!insight.is_read && (
                      <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-dark-100 mb-1">{insight.title}</h3>
                  <p className="text-dark-300">{insight.description}</p>
                  <p className="text-xs text-dark-500 mt-2">
                    {format(new Date(insight.created_at), 'MMM d, yyyy • h:mm a')}
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  {!insight.is_read && (
                    <button
                      onClick={() => handleMarkRead(insight.id)}
                      className="p-2 text-dark-400 hover:text-success hover:bg-dark-800 rounded-lg"
                      title="Mark as read"
                    >
                      <CheckCircleIcon className="w-5 h-5" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDismiss(insight.id)}
                    className="p-2 text-dark-400 hover:text-error hover:bg-dark-800 rounded-lg"
                    title="Dismiss"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
