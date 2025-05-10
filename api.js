import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
});

export const login = async (username) => {
  const response = await API.post('/login', { username });
  return response.data;
};

export const getProtectedData = async (token) => {
  const response = await API.get('/protected', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};