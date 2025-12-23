import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const generateSql = async (question) => {
  const response = await api.post('/generate-sql', { question });
  return response.data;
};

export const executeSql = async (sql_query) => {
  const response = await api.post('/execute-sql', { sql_query });
  return response.data;
};

export const generateInsights = async (data) => {
  const response = await api.post('/generate-insights', { data });
  return response.data;
};