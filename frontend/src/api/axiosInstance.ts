import type { AxiosRequestConfig } from 'axios';
import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL;

const axiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // ← これが必須
});

// ✅ 認証トークン付与などはここで一元管理
axiosInstance.interceptors.request.use((config) => {
  // ここで認証トークンを付与
  config.headers = config.headers ?? {};
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ✅ orvalが要求する「mutator形式」の関数をexport
export const customInstance = async<T = unknown>(config: AxiosRequestConfig ) => {
  const responsee = await axiosInstance.request<T>(config);
  return responsee.data;
};


