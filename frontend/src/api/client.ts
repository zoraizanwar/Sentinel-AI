import axios, { AxiosError } from 'axios';

export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 600000, // 10 minutes timeout for heavy ML runs
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('sentinel_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface ApiError {
  errorCode: string;
  message: string;
  statusCode: number;
}

export function extractApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ error_code?: string; message?: string; detail?: string }>;
    const status = axiosErr.response?.status || 500;
    const data = axiosErr.response?.data;

    let code = data?.error_code || 'NETWORK_ERROR';
    let message = data?.message || data?.detail || axiosErr.message || 'An unexpected error occurred.';

    if (status === 501) {
      code = 'NOT_IMPLEMENTED';
      message = data?.detail || 'This service capability is scheduled for Phase 6.';
    }

    return {
      errorCode: code,
      message,
      statusCode: status,
    };
  }

  return {
    errorCode: 'UNKNOWN_ERROR',
    message: error instanceof Error ? error.message : 'An unknown error occurred.',
    statusCode: 500,
  };
}
