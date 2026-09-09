import axios from "axios";

import { getToken, UNAUTHORIZED_EVENT } from "./auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

export const api = axios.create({ baseURL: `${API_URL}/api` });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    return Promise.reject(error);
  }
);

export function apiErrorMessage(error) {
  const data = error?.response?.data;
  if (!data) {
    return "Something went wrong talking to the ClauseGuard server. Check that the backend is running.";
  }
  if (data.detail) return data.detail;
  const firstFieldError = Object.values(data).find((v) => Array.isArray(v) && v.length);
  return firstFieldError?.[0] || "Something went wrong. Please try again.";
}
