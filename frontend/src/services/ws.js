class WebSocketService {
  constructor() {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 5000
    this.listeners = new Set()
    this.isConnected = false
    this.url = 'ws://localhost:8000/ws/data'
  }

  connect() {
    try {
      // Add a small delay to ensure backend is ready
      setTimeout(() => {
        this.ws = new WebSocket(this.url)
      
        this.ws.onopen = () => {
          console.log('✅ WebSocket connected to backend')
          this.isConnected = true
          this.reconnectAttempts = 0
          this.notifyListeners('connected')
        }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.notifyListeners('message', data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

        this.ws.onclose = () => {
          console.log('❌ WebSocket disconnected')
          this.isConnected = false
          this.notifyListeners('disconnected')
          this.handleReconnect()
        }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.notifyListeners('error', error)
      }
      }, 2000) // 2 second delay
    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
      this.handleReconnect()
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`🔄 Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      setTimeout(() => {
        this.connect()
      }, this.reconnectInterval)
    } else {
      console.error('Max reconnection attempts reached')
      this.notifyListeners('maxReconnectAttemptsReached')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  addListener(callback) {
    this.listeners.add(callback)
  }

  removeListener(callback) {
    this.listeners.delete(callback)
  }

  notifyListeners(event, data = null) {
    this.listeners.forEach(callback => {
      try {
        callback(event, data)
      } catch (error) {
        console.error('Error in WebSocket listener:', error)
      }
    })
  }

  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts
    }
  }
}

// Create singleton instance
const wsService = new WebSocketService()

export default wsService
