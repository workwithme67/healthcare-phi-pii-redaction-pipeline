import axios from 'axios';

// Detect API host. In local docker / development it is proxied or uses specific URL.
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const healthService = {
  getHealth: async () => {
    const response = await apiClient.get('/app/health');
    return response.data;
  },
};

export const redactionService = {
  submitJob: async (text, filename = null) => {
    const response = await apiClient.post('/jobs', { text, filename });
    return response.data;
  },
  listJobs: async (page = 1, pageSize = 20, status = null) => {
    const params = { page, page_size: pageSize };
    if (status) params.status = status;
    const response = await apiClient.get('/jobs', { params });
    return response.data;
  },
  getJob: async (jobId) => {
    const response = await apiClient.get(`/jobs/${jobId}`);
    return response.data;
  },
  getStatistics: async () => {
    const response = await apiClient.get('/jobs/statistics');
    return response.data;
  },
};

export const auditService = {
  listLogs: async (page = 1, pageSize = 50, action = null) => {
    const params = { page, page_size: pageSize };
    if (action) params.action = action;
    const response = await apiClient.get('/audit', { params });
    return response.data;
  },
};

export default apiClient;
