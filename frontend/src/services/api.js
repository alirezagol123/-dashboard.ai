import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// API endpoints
export const apiService = {
  // Get latest sensor data
  getLatestData: async (limit = 20, sensorType = null) => {
    try {
      const params = { limit }
      if (sensorType) params.sensor_type = sensorType
      
      const response = await api.get('/data/latest', { params })
      return response.data
    } catch (error) {
      console.error('Error fetching latest data:', error)
      throw error
    }
  },

  // Get statistics
  getStats: async () => {
    try {
      const response = await api.get('/data/stats')
      return response.data
    } catch (error) {
      console.error('Error fetching stats:', error)
      throw error
    }
  },

  // Get sensor types
  getSensorTypes: async () => {
    try {
      const response = await api.get('/data/types')
      return response.data
    } catch (error) {
      console.error('Error fetching sensor types:', error)
      throw error
    }
  },

  // Create sensor data (for testing)
  createSensorData: async (sensorType, value) => {
    try {
      const response = await api.post('/data', {
        sensor_type: sensorType,
        value: value
      })
      return response.data
    } catch (error) {
      console.error('Error creating sensor data:', error)
      throw error
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get('/health')
      return response.data
    } catch (error) {
      console.error('Health check failed:', error)
      throw error
    }
  }
}

export default apiService
