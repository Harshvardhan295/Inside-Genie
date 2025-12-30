import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

console.log('DEBUG: API_URL is configured as:', API_URL);

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add an interceptor to log every request details
api.interceptors.request.use((config) => {
  console.log(`DEBUG: Making POST request to: ${config.baseURL}/${config.url}`);
  console.log('DEBUG: Payload:', config.data);
  return config;
}, (error) => {
  console.error('DEBUG: Request Setup Error:', error);
  return Promise.reject(error);
});

// Add an interceptor to log every response or error
api.interceptors.response.use((response) => {
  console.log('DEBUG: Response Received:', response.status, response.data);
  return response;
}, (error) => {
  console.error('DEBUG: API Error Detail:');
  if (error.response) {
    // The server responded with a status code outside the 2xx range
    console.error('- Status:', error.response.status);
    console.error('- Data:', error.response.data);
    console.error('- Headers:', error.response.headers);
  } else if (error.request) {
    // The request was made but no response was received
    console.error('- No response received. Request object:', error.request);
  } else {
    // Something happened in setting up the request
    console.error('- Error Message:', error.message);
  }
  return Promise.reject(error);
});

export const generateSql = async (question) => {
  console.log('DEBUG: Calling generateSql with question:', question);
  const response = await api.post('generate-sql', { question }); 
  return response.data;
};

export const executeSql = async (sql_query) => {
  console.log('DEBUG: Calling executeSql with query:', sql_query);
  const response = await api.post('execute-sql', { sql_query });
  return response.data;
};

export const generateInsights = async (data) => {
  console.log('DEBUG: Calling generateInsights with data length:', data?.length);
  const response = await api.post('generate-insights', { data });
  return response.data;
};