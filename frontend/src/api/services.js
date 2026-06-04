import axios from 'axios';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const dashboardService = {
  getDashboard: async () => {
    const response = await apiClient.get('/dashboard');
    return response.data;
  },
};

export const metricsService = {
  getMetrics: async () => {
    const response = await apiClient.get('/metrics');
    return response.data;
  },
};

export const funnelService = {
  getFunnel: async () => {
    const response = await apiClient.get('/funnel');
    return response.data;
  },
};

export const diagnosticsService = {
  getDiagnostics: async () => {
    const response = await apiClient.get('/diagnostics');
    return response.data;
  },
};
export const fetchAllDashboardData = async () => {
  const dashboard = await dashboardService.getDashboard();

  return {
    dashboard
  };
};

export default apiClient;
