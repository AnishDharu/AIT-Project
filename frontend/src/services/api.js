import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bizflow_access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('bizflow_access')
      localStorage.removeItem('bizflow_refresh')
    }
    return Promise.reject(error)
  }
)

export async function login(username, password) {
  const { data } = await api.post('/auth/token/', { username, password })
  localStorage.setItem('bizflow_access', data.access)
  localStorage.setItem('bizflow_refresh', data.refresh)
  return data
}

export async function register(payload) {
  return (await api.post('/auth/register/', payload)).data
}

export function logout() {
  localStorage.removeItem('bizflow_access')
  localStorage.removeItem('bizflow_refresh')
}

export default api
