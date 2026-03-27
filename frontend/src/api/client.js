import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    // If the server returned 401 for an in-flight request, clear auth and
    // redirect to the login page — except when the request itself was the
    // login endpoint. Redirecting during a login attempt causes the login
    // page to reload and swallow the server-provided error message, so skip
    // the redirect for /auth/login and allow the caller to handle the error.
    if (err.response?.status === 401) {
      const reqUrl = err.config?.url || ''
      if (!reqUrl.endsWith('/auth/login')) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default client
