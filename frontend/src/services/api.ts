import axios, { AxiosInstance, AxiosError } from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiService {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load token from localStorage
    this.token = localStorage.getItem('access_token');

    // Request interceptor
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.logout();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  logout() {
    this.token = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const response = await this.client.post('/auth/login', { username, password });
    this.setToken(response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    return response.data;
  }

  async register(email: string, username: string, password: string, fullName?: string) {
    const response = await this.client.post('/auth/register', {
      email,
      username,
      password,
      full_name: fullName,
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) throw new Error('No refresh token');
    const response = await this.client.post('/auth/refresh', { refresh_token: refreshToken });
    this.setToken(response.data.access_token);
    return response.data;
  }

  // User endpoints
  async getProfile() {
    const response = await this.client.get('/users/me');
    return response.data;
  }

  async updateProfile(data: any) {
    const response = await this.client.patch('/users/me', data);
    return response.data;
  }

  async getSettings() {
    const response = await this.client.get('/users/me/settings');
    return response.data;
  }

  async updateSettings(data: any) {
    const response = await this.client.patch('/users/me/settings', data);
    return response.data;
  }

  // Dashboard endpoints
  async getDashboardOverview() {
    const response = await this.client.get('/dashboard/overview');
    return response.data;
  }

  async getDailySummary(date: string) {
    const response = await this.client.get(`/dashboard/daily/${date}`);
    return response.data;
  }

  // Metrics endpoints
  async getMetrics(category?: string) {
    const params = category ? { category } : {};
    const response = await this.client.get('/metrics', { params });
    return response.data;
  }

  async getMetricCategories() {
    const response = await this.client.get('/metrics/categories');
    return response.data;
  }

  // Measurements endpoints
  async getMeasurements(params: {
    metric_key?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }) {
    const response = await this.client.get('/measurements', { params });
    return response.data;
  }

  async getLatestMeasurements(metricKeys?: string[]) {
    const params = metricKeys ? { metric_keys: metricKeys.join(',') } : {};
    const response = await this.client.get('/measurements/latest', { params });
    return response.data;
  }

  async getMeasurementStats(metricKey: string, startDate?: string, endDate?: string) {
    const params = { start_date: startDate, end_date: endDate };
    const response = await this.client.get(`/measurements/stats/${metricKey}`, { params });
    return response.data;
  }

  async getMeasurementTimeseries(
    metricKey: string,
    startDate?: string,
    endDate?: string,
    aggregation: string = 'daily'
  ) {
    const params = { start_date: startDate, end_date: endDate, aggregation };
    const response = await this.client.get(`/measurements/timeseries/${metricKey}`, { params });
    return response.data;
  }

  async createMeasurement(data: any) {
    const response = await this.client.post('/measurements', data);
    return response.data;
  }

  // Workouts endpoints
  async getWorkouts(params: {
    workout_type?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }) {
    const response = await this.client.get('/workouts', { params });
    return response.data;
  }

  async getWorkoutSummary(startDate?: string, endDate?: string) {
    const params = { start_date: startDate, end_date: endDate };
    const response = await this.client.get('/workouts/summary', { params });
    return response.data;
  }

  async getWorkoutTypes() {
    const response = await this.client.get('/workouts/types');
    return response.data;
  }

  async getWorkoutStreak() {
    const response = await this.client.get('/workouts/streak');
    return response.data;
  }

  // Sleep endpoints
  async getSleepSessions(params: {
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }) {
    const response = await this.client.get('/sleep', { params });
    return response.data;
  }

  async getLatestSleep() {
    const response = await this.client.get('/sleep/latest');
    return response.data;
  }

  async getSleepSummary(startDate?: string, endDate?: string) {
    const params = { start_date: startDate, end_date: endDate };
    const response = await this.client.get('/sleep/summary', { params });
    return response.data;
  }

  async getSleepStages(startDate?: string, endDate?: string) {
    const params = { start_date: startDate, end_date: endDate };
    const response = await this.client.get('/sleep/stages', { params });
    return response.data;
  }

  // Analytics endpoints
  async getTrend(metricKey: string, days: number = 30) {
    const response = await this.client.get(`/analytics/trends/${metricKey}`, { params: { days } });
    return response.data;
  }

  async getCorrelation(metricA: string, metricB: string, lagDays: number = 0) {
    const response = await this.client.post('/analytics/correlations', {
      metric_a: metricA,
      metric_b: metricB,
      lag_days: lagDays,
    });
    return response.data;
  }

  async getCorrelationMatrix(metrics: string[], days: number = 90) {
    const response = await this.client.get('/analytics/correlations/matrix', {
      params: { metrics: metrics.join(','), days },
    });
    return response.data;
  }

  async getHealthReport(startDate?: string, endDate?: string) {
    const params = { start_date: startDate, end_date: endDate };
    const response = await this.client.get('/analytics/report', { params });
    return response.data;
  }

  // Insights endpoints
  async getInsights(params: {
    insight_type?: string;
    category?: string;
    is_read?: boolean;
    page?: number;
    page_size?: number;
  }) {
    const response = await this.client.get('/insights', { params });
    return response.data;
  }

  async markInsightRead(insightId: string) {
    const response = await this.client.patch(`/insights/${insightId}`, { is_read: true });
    return response.data;
  }

  async dismissInsight(insightId: string) {
    const response = await this.client.delete(`/insights/${insightId}`);
    return response.data;
  }

  async markAllInsightsRead() {
    const response = await this.client.post('/insights/mark-all-read');
    return response.data;
  }

  // Alerts endpoints
  async getAlerts() {
    const response = await this.client.get('/alerts');
    return response.data;
  }

  async createAlert(data: any) {
    const response = await this.client.post('/alerts', data);
    return response.data;
  }

  async updateAlert(alertId: string, data: any) {
    const response = await this.client.patch(`/alerts/${alertId}`, data);
    return response.data;
  }

  async deleteAlert(alertId: string) {
    const response = await this.client.delete(`/alerts/${alertId}`);
    return response.data;
  }

  // Import endpoints
  async uploadAppleHealth(file: File, onProgress?: (progress: number) => void) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post('/imports/apple-health', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  }

  async getImportHistory() {
    const response = await this.client.get('/imports');
    return response.data;
  }

  async getImportProgress(importId: string) {
    const response = await this.client.get(`/imports/${importId}/progress`);
    return response.data;
  }

  async getImportSummary() {
    const response = await this.client.get('/imports/summary');
    return response.data;
  }

  // Export endpoints
  async exportData(format: string = 'json', startDate?: string, endDate?: string) {
    const response = await this.client.get(`/exports/download`, {
      params: { format, start_date: startDate, end_date: endDate },
      responseType: 'blob',
    });
    return response.data;
  }
}

export const api = new ApiService();
export default api;
