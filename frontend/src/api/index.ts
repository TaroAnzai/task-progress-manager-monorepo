import axios from 'axios';

// .envファイルに VITE_API_BASE_URL を定義しておく
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/';

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Cookie認証が必要な場合は true
});

