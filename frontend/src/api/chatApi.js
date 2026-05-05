import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
})

export async function sendMessage(message, sessionId = 'default') {
  try {
    const { data } = await apiClient.post('/chat', {
      message,
      session_id: sessionId,
    })
    return data
  } catch (err) {
    // Surface a clear error message
    if (err.code === 'ERR_NETWORK' || err.code === 'ECONNREFUSED') {
      throw new Error('Cannot connect to backend. Make sure the server is running on port 8000.')
    }
    if (err.response?.data?.detail) {
      throw new Error(err.response.data.detail)
    }
    throw err
  }
}
