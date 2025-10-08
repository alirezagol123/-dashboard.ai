import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Wifi, WifiOff, RefreshCw, Activity, MessageSquare, BarChart3, Leaf, Bug, Droplets, Thermometer, Calendar, ShoppingCart, Users, TrendingUp, Menu, X, Database, ChevronUp, ChevronDown, Wrench, Bell } from 'lucide-react'
import Chart from '../components/Chart'
import StatsCard from '../components/StatsCard'
import AlertBox from '../components/AlertBox'
import LangChainChat from '../components/LangChainChat'
import DataVisualizer from '../components/DataVisualizer'
import AlertsManager from '../components/AlertsManager'

// Global WebSocket connection manager to prevent multiple connections
class WebSocketManager {
  constructor() {
    this.ws = null
    this.isConnecting = false
    this.isConnected = false
    this.listeners = new Set()
    this.retryCount = 0
    this.maxRetries = 10
    this.retryDelay = 2000
    this.retryTimeout = null
  }

  addListener(callback) {
    this.listeners.add(callback)
    console.log(`WebSocketManager: Added listener. Total: ${this.listeners.size}`)
  }

  removeListener(callback) {
    this.listeners.delete(callback)
    console.log(`WebSocketManager: Removed listener. Total: ${this.listeners.size}`)
  }

  notifyListeners(event, data) {
    this.listeners.forEach(callback => {
      try {
        callback(event, data)
      } catch (error) {
        console.error('WebSocketManager: Error in listener:', error)
      }
    })
  }

  connect() {
    if (this.isConnecting || this.isConnected) {
      console.log('WebSocketManager: Already connecting or connected, skipping...')
      return
    }

    this.isConnecting = true
    console.log(`WebSocketManager: Attempting connection (attempt ${this.retryCount + 1}/${this.maxRetries})`)

    try {
      this.ws = new WebSocket('ws://127.0.0.1:8000/ws/data')
      
      this.ws.onopen = () => {
        this.isConnecting = false
        this.isConnected = true
        this.retryCount = 0
        console.log('WebSocketManager: ✅ Connected successfully!')
        this.notifyListeners('open', null)
      }

      this.ws.onmessage = (event) => {
        this.notifyListeners('message', event.data)
      }

      this.ws.onclose = (event) => {
        this.isConnecting = false
        this.isConnected = false
        console.log(`WebSocketManager: ❌ Disconnected: ${event.code}`)
        this.notifyListeners('close', event)

        // Retry if we haven't exceeded max retries
        if (this.retryCount < this.maxRetries) {
          this.retryCount++
          console.log(`WebSocketManager: Retrying in ${this.retryDelay}ms...`)
          this.retryTimeout = setTimeout(() => this.connect(), this.retryDelay)
        } else {
          console.log('WebSocketManager: Max retries reached')
        }
      }

      this.ws.onerror = (error) => {
        this.isConnecting = false
        this.isConnected = false
        console.error('WebSocketManager: Error:', error)
        this.notifyListeners('error', error)
      }

    } catch (error) {
      this.isConnecting = false
      this.isConnected = false
      console.error('WebSocketManager: Connection error:', error)
      this.notifyListeners('error', error)
    }
  }

  disconnect() {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout)
      this.retryTimeout = null
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Component unmounting')
      this.ws = null
    }
    
    this.isConnecting = false
    this.isConnected = false
    console.log('WebSocketManager: Disconnected')
  }

  getConnectionState() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting
    }
  }
}

// Global instance
const wsManager = new WebSocketManager()

const Dashboard = () => {
  const [sensorData, setSensorData] = useState([])
  const [stats, setStats] = useState({})
  const [isLoading, setIsLoading] = useState(true)
  const [wsConnected, setWsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [aiSidebarOpen, setAiSidebarOpen] = useState(true) // Always open by default
  const [sidebarWidth, setSidebarWidth] = useState(320) // Default width in pixels
  const [isResizing, setIsResizing] = useState(false)
  const [leftSidebarWidth, setLeftSidebarWidth] = useState(256) // Default width for left sidebar
  const [isLeftResizing, setIsLeftResizing] = useState(false)
  const [isLeftSidebarCollapsed, setIsLeftSidebarCollapsed] = useState(false)
  const [sessionId, setSessionId] = useState('default')

  // Handle right sidebar resize
  const handleMouseDown = (e) => {
    setIsResizing(true)
    e.preventDefault()
  }

  // Handle left sidebar resize
  const handleLeftMouseDown = (e) => {
    setIsLeftResizing(true)
    e.preventDefault()
  }

  const handleMouseMove = useCallback((e) => {
    if (!isResizing) return
    
    const newWidth = window.innerWidth - e.clientX
    const minWidth = 250
    const maxWidth = 600
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      setSidebarWidth(newWidth)
    }
  }, [isResizing])

  const handleLeftMouseMove = useCallback((e) => {
    if (!isLeftResizing) return
    
    const newWidth = e.clientX
    const minWidth = 200
    const maxWidth = 400
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      setLeftSidebarWidth(newWidth)
    }
  }, [isLeftResizing])

  const handleMouseUp = useCallback(() => {
    setIsResizing(false)
    setIsLeftResizing(false)
  }, [])

  // Toggle left sidebar collapse
  const toggleLeftSidebar = () => {
    setIsLeftSidebarCollapsed(!isLeftSidebarCollapsed)
  }

  useEffect(() => {
    if (isResizing || isLeftResizing) {
      document.addEventListener('mousemove', isResizing ? handleMouseMove : handleLeftMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      
      return () => {
        document.removeEventListener('mousemove', isResizing ? handleMouseMove : handleLeftMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isResizing, isLeftResizing, handleMouseMove, handleLeftMouseMove, handleMouseUp])

  // Fetch data from API
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true)
      const response = await fetch('http://127.0.0.1:8000/data/latest?limit=20')
      if (!response.ok) {
        throw new Error('Failed to fetch data')
      }
      const data = await response.json()
      console.log('Fetched data via polling:', data.length, 'records')
      setSensorData(data)
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      setError(err.message)
      console.error('Error fetching data:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Fetch stats from API
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/data/stats')
      if (!response.ok) {
        throw new Error('Failed to fetch stats')
      }
      const data = await response.json()
      setStats(data)
    } catch (err) {
      console.error('Error fetching stats:', err)
    }
  }, [])

  // WebSocket connection using global manager
  useEffect(() => {
    const handleWebSocketEvent = (event, data) => {
      switch (event) {
        case 'open':
      setWsConnected(true)
          console.log('Dashboard: WebSocket connected')
          break
          
        case 'close':
          setWsConnected(false)
          console.log('Dashboard: WebSocket disconnected')
          break
          
        case 'error':
          setWsConnected(false)
          console.error('Dashboard: WebSocket error')
          break
          
        case 'message':
          try {
            const message = data
            console.log('Dashboard: WebSocket message received:', message)
            
            // Handle ping/pong messages
            if (message === 'ping') {
              if (wsManager.ws) {
                wsManager.ws.send('pong')
              }
              return
            }
            if (message === 'pong') {
              return
            }
            
            // Handle welcome message
            if (message === 'welcome') {
              console.log('Dashboard: Received welcome message from server')
              return
            }
            
            // Handle sensor data
            const sensorData = JSON.parse(message)
            console.log('Dashboard: Parsed sensor data:', sensorData)
            
            setSensorData(prev => {
              const newData = [sensorData, ...prev.slice(0, 19)]
              console.log('Dashboard: Updated sensorData length:', newData.length)
              return newData
            })
      setLastUpdate(new Date())
            
            // Update stats with new data
            setStats(prevStats => {
              try {
                const newStats = { ...prevStats }
                if (!newStats[sensorData.sensor_type]) {
                  newStats[sensorData.sensor_type] = { values: [], average: 0, trend: 'stable' }
                }
                
                // Ensure values array exists and add new value
                if (!newStats[sensorData.sensor_type].values) {
                  newStats[sensorData.sensor_type].values = []
                }
                newStats[sensorData.sensor_type].values.push(sensorData.value)
                
                // Keep only last 10 values for trend calculation
                if (newStats[sensorData.sensor_type].values.length > 10) {
                  newStats[sensorData.sensor_type].values = newStats[sensorData.sensor_type].values.slice(-10)
                }
                
                // Calculate average
                const values = newStats[sensorData.sensor_type].values
                newStats[sensorData.sensor_type].average = values.reduce((sum, val) => sum + val, 0) / values.length
                
                // Calculate trend
                if (values.length >= 2) {
                  const recent = values.slice(-3).reduce((sum, val) => sum + val, 0) / Math.min(3, values.length)
                  const older = values.slice(0, -3).reduce((sum, val) => sum + val, 0) / Math.max(1, values.length - 3)
                  newStats[sensorData.sensor_type].trend = recent > older ? 'up' : recent < older ? 'down' : 'stable'
                }
                
                console.log(`Dashboard: Updated stats for ${sensorData.sensor_type}:`, newStats[sensorData.sensor_type])
                return newStats
              } catch (error) {
                console.error('Dashboard: Error updating stats:', error)
                return prevStats
              }
            })
          } catch (err) {
            console.error('Dashboard: Error parsing WebSocket message:', err)
          }
          break
      }
    }

    // Add listener to global WebSocket manager
    wsManager.addListener(handleWebSocketEvent)
    
    // Connect if not already connected
    const connectionState = wsManager.getConnectionState()
    if (!connectionState.isConnected && !connectionState.isConnecting) {
      wsManager.connect()
    } else {
      // Update state if already connected
      setWsConnected(connectionState.isConnected)
    }

    return () => {
      console.log('Dashboard: Removing WebSocket listener')
      wsManager.removeListener(handleWebSocketEvent)
    }
  }, [])

  // Initial data fetch
  useEffect(() => {
    fetchData()
    fetchStats()
  }, [fetchData, fetchStats])

  // Initialize session ID
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const sessionFromUrl = urlParams.get('session_id')
    const sessionFromStorage = localStorage.getItem('session_id')
    
    if (sessionFromUrl) {
      setSessionId(sessionFromUrl)
      localStorage.setItem('session_id', sessionFromUrl)
    } else if (sessionFromStorage) {
      setSessionId(sessionFromStorage)
    } else {
      // Generate a new session ID
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      setSessionId(newSessionId)
      localStorage.setItem('session_id', newSessionId)
    }
  }, [])

  // Polling fallback when WebSocket is disconnected
  useEffect(() => {
    let interval = null
    
    if (!wsConnected) {
      console.log('WebSocket disconnected, starting polling fallback every 3 seconds')
      interval = setInterval(() => {
        console.log('Polling for new data...')
        fetchData()
        fetchStats()
      }, 3000) // More frequent polling
    } else {
      console.log('WebSocket connected, stopping polling')
    }
    
    return () => {
      if (interval) {
        clearInterval(interval)
        console.log('Polling stopped')
      }
    }
  }, [wsConnected, fetchData, fetchStats])

  // Get sensor types from stats
  const sensorTypes = Object.keys(stats)

  return (
    <div className="min-h-screen overflow-x-hidden" style={{ backgroundColor: 'transparent' }}>
      {/* Sidebar */}
      <div 
        className={`fixed top-6 left-0 z-30 transform transition-all duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 lg:fixed lg:top-2 lg:left-0 lg:h-[calc(100vh-0.5rem)] lg:z-50 ${isLeftResizing ? 'select-none' : ''} ${
          isLeftSidebarCollapsed ? 'lg:translate-x-0 lg:top-0 lg:left-0 lg:h-12 bg-transparent shadow-none' : 'bg-white shadow-lg'
        }`}
        style={{ 
          width: isLeftSidebarCollapsed ? '60px' : `${leftSidebarWidth}px`,
          height: isLeftSidebarCollapsed ? '48px' : 'calc(100vh - 0.5rem)'
        }}
      >
        {/* Resize Handle */}
        {!isLeftSidebarCollapsed && (
          <div
            className={`absolute right-0 top-0 w-1 h-full cursor-col-resize transition-colors duration-200 ${
              isLeftResizing ? 'bg-blue-500' : 'bg-gray-200 hover:bg-gray-300'
            }`}
            onMouseDown={handleLeftMouseDown}
            title="Drag to resize sidebar"
          />
        )}
        <div className={`flex items-center justify-between h-12 px-6 ${!isLeftSidebarCollapsed ? 'border-b border-gray-200' : ''}`}>
          <div className="flex items-center space-x-2">
            {!isLeftSidebarCollapsed && (
              <>
                <h2 className="text-lg font-semibold text-gray-800">Agriculture Tools</h2>
                {isLeftResizing && (
                  <span className="text-xs text-blue-600 font-medium">
                    {leftSidebarWidth}px
                  </span>
                )}
              </>
            )}
            {isLeftSidebarCollapsed && (
              <button
                onClick={toggleLeftSidebar}
                className="flex items-center justify-center w-8 h-8 bg-black rounded-full hover:bg-gray-800 transition-colors ml-0"
                title="Expand Agriculture Tools"
              >
                <Wrench className="h-4 w-4 text-white" />
              </button>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {!isLeftSidebarCollapsed && (
              <button
                onClick={toggleLeftSidebar}
                className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                title="Collapse sidebar"
              >
                <ChevronUp className="h-4 w-4" />
              </button>
            )}
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
        
        {!isLeftSidebarCollapsed && (
        <nav className="mt-6 px-3">
          <div className="space-y-1">
            <button
              onClick={() => setActiveTab('fertilization')}
              className={`w-full flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors border ${
                activeTab === 'fertilization'
                  ? 'bg-blue-50 text-blue-700 border-blue-300'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-gray-200'
              }`}
            >
              <Leaf className="h-5 w-5 mr-3" />
              Fertilization
            </button>
            
            <button
              onClick={() => setActiveTab('harvest')}
              className={`w-full flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors border ${
                activeTab === 'harvest'
                  ? 'bg-blue-50 text-blue-700 border-blue-300'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-gray-200'
              }`}
            >
              <Calendar className="h-5 w-5 mr-3" />
              Harvest
            </button>
            
            <button
              onClick={() => setActiveTab('marketplace')}
              className={`w-full flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors border ${
                activeTab === 'marketplace'
                  ? 'bg-blue-50 text-blue-700 border-blue-300'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-gray-200'
              }`}
            >
              <ShoppingCart className="h-5 w-5 mr-3" />
              Marketplace
            </button>
            
            <button
              onClick={() => setActiveTab('consultation')}
              className={`w-full flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors border ${
                activeTab === 'consultation'
                  ? 'bg-blue-50 text-blue-700 border-blue-300'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-gray-200'
              }`}
            >
              <Users className="h-5 w-5 mr-3" />
              Consultation
            </button>
            
            <button
              onClick={() => setActiveTab('analytics')}
              className={`w-full flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors border ${
                activeTab === 'analytics'
                  ? 'bg-blue-50 text-blue-700 border-blue-300'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-gray-200'
              }`}
            >
              <TrendingUp className="h-5 w-5 mr-3" />
              Analytics
            </button>
          </div>
        </nav>
        )}
      </div>

      {/* Main Content */}
      <div className={`flex flex-col min-h-screen ${isLeftSidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'}`}>
        {/* Top Bar */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 mr-3"
                >
                  <Menu className="h-6 w-6" />
                </button>
                <div className="flex items-center space-x-1 ml-0">
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'dashboard'
                      ? 'bg-blue-50 text-blue-700 border-blue-300'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  <Activity className="h-4 w-4 inline mr-2" />
                  Dashboard
                </button>
                
                <button
                  onClick={() => setActiveTab('irrigation')}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'irrigation'
                      ? 'bg-blue-50 text-blue-700 border-blue-300'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  <Droplets className="h-4 w-4 inline mr-2" />
                  Irrigation
                </button>
                
                <button
                  onClick={() => setActiveTab('environment')}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'environment'
                      ? 'bg-blue-50 text-blue-700 border-blue-300'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  <Thermometer className="h-4 w-4 inline mr-2" />
                  Environment
                </button>
                
                <button
                  onClick={() => setActiveTab('pest-detection')}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'pest-detection'
                      ? 'bg-blue-50 text-blue-700 border-blue-300'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  <Bug className="h-4 w-4 inline mr-2" />
                  Pest Detection
                </button>
                
                
                <button
                  onClick={() => setActiveTab('alerts')}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'alerts'
                      ? 'bg-blue-50 text-blue-700 border-blue-300'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  <Bell className="h-4 w-4 inline mr-2" />
                  Alerts
                </button>
                </div>
                
              </div>
              
              <div className="flex items-center space-x-4">
                {/* Session ID Display */}
                <div className="text-xs text-gray-400">
                  Session: {sessionId.substring(0, 20)}...
                </div>
                
                {/* AI Assistant Toggle - Always visible */}
                <button
                  onClick={() => setAiSidebarOpen(!aiSidebarOpen)}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    aiSidebarOpen
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <MessageSquare className="h-4 w-4 inline mr-2" />
                  AI Assistant
                </button>

                {/* Connection Status */}
                <div className="flex items-center">
                  {wsConnected ? (
                    <div className="flex items-center text-green-600">
                      <Wifi className="h-4 w-4 mr-1" />
                      <span className="text-sm font-medium">Connected</span>
                    </div>
                  ) : (
                    <div className="flex items-center text-red-600">
                      <WifiOff className="h-4 w-4 mr-1" />
                      <span className="text-sm font-medium">Disconnected</span>
                    </div>
                  )}
                </div>

                {/* Refresh Button */}
                <button
                  onClick={fetchData}
                  disabled={isLoading}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main 
          className={`transition-all duration-300 ${isResizing || isLeftResizing ? 'select-none' : ''}`}
          style={{ 
            padding: '0px',
            width: '100vw',
            marginLeft: '8px',
            marginRight: '0px',
            minWidth: '800px',
            backgroundColor: 'transparent',
            position: 'absolute',
            left: '0px',
            top: '72px'
          }}
        >
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <div className="mt-2 text-sm text-red-700">{error}</div>
                </div>
              </div>
            </div>
          )}

          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6" style={{ padding: '0px', backgroundColor: 'transparent' }}>
             {/* Stats Cards */}
             <div className="space-y-4" style={{ margin: '0px', padding: '0px' }}>
               {Array.from({ length: Math.ceil(sensorTypes.length / 6) }, (_, rowIndex) => (
                 <div 
                   key={rowIndex}
                   className="flex gap-2 overflow-x-auto"
                   style={{ 
                     scrollbarWidth: 'thin',
                     scrollbarColor: 'white transparent',
                     paddingBottom: '10px'
                   }}
                 >
                   {sensorTypes.slice(rowIndex * 6, (rowIndex + 1) * 6).map((type, colIndex) => (
                     <StatsCard
                       key={type}
                       sensorType={type}
                       stats={stats[type]}
                       rowIndex={rowIndex}
                       colIndex={colIndex}
                     />
                   ))}
                 </div>
               ))}
             </div>

              {/* Chart and Alerts */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <Chart data={sensorData} />
                </div>
                <div>
                  <AlertBox data={sensorData} />
                </div>
              </div>
            </div>
          )}

          {/* Fertilization Tab */}
          {activeTab === 'fertilization' && (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <Leaf className="h-6 w-6 mr-3 text-green-600" />
                  Intelligent Fertilization & Plant Nutrition
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Soil pH Analysis</h3>
                    <div className="text-3xl font-bold text-green-600 mb-2">
                      {stats.soil_ph?.average?.toFixed(1) || 'N/A'}
                    </div>
                    <p className="text-sm text-gray-600">Optimal range: 6.0-7.0</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          (stats.soil_ph?.average || 0) >= 6.0 && (stats.soil_ph?.average || 0) <= 7.0 
                            ? 'bg-green-500' : 'bg-red-500'
                        }`}
                        style={{width: `${Math.min(100, Math.max(0, ((stats.soil_ph?.average || 0) - 5.0) / 3.0 * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Nitrogen Level</h3>
                    <div className="text-3xl font-bold text-blue-600 mb-2">
                      {stats.nitrogen_level?.average?.toFixed(0) || 'N/A'} ppm
                    </div>
                    <p className="text-sm text-gray-600">Recommended: 40-60 ppm</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          (stats.nitrogen_level?.average || 0) >= 40 && (stats.nitrogen_level?.average || 0) <= 60 
                            ? 'bg-blue-500' : 'bg-yellow-500'
                        }`}
                        style={{width: `${Math.min(100, Math.max(0, ((stats.nitrogen_level?.average || 0) / 80) * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Phosphorus Level</h3>
                    <div className="text-3xl font-bold text-purple-600 mb-2">
                      {stats.phosphorus_level?.average?.toFixed(0) || 'N/A'} ppm
                    </div>
                    <p className="text-sm text-gray-600">Recommended: 25-35 ppm</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          (stats.phosphorus_level?.average || 0) >= 25 && (stats.phosphorus_level?.average || 0) <= 35 
                            ? 'bg-purple-500' : 'bg-yellow-500'
                        }`}
                        style={{width: `${Math.min(100, Math.max(0, ((stats.phosphorus_level?.average || 0) / 50) * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-800 mb-3">AI Recommendations</h3>
                  <ul className="space-y-2 text-blue-700">
                    {(stats.nitrogen_level?.average || 0) < 40 ? (
                    <li>• Apply nitrogen fertilizer (15-5-10) at 2 lbs per 100 sq ft</li>
                    ) : (
                      <li>• Nitrogen levels are optimal, no additional fertilizer needed</li>
                    )}
                    
                    {(stats.soil_ph?.average || 0) < 6.0 ? (
                      <li>• Apply lime to raise soil pH to optimal range</li>
                    ) : (stats.soil_ph?.average || 0) > 7.0 ? (
                      <li>• Apply sulfur to lower soil pH to optimal range</li>
                    ) : (
                      <li>• Soil pH is optimal, no adjustment needed</li>
                    )}
                    
                    <li>• Fertilizer usage: {stats.fertilizer_usage?.average?.toFixed(1) || '0'} kg applied</li>
                    <li>• Nutrient uptake efficiency: {stats.nutrient_uptake?.average?.toFixed(1) || '0'}%</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Pest Detection Tab */}
          {activeTab === 'pest-detection' && (
            <div className="space-y-4" style={{ padding: '0px', backgroundColor: 'transparent' }}>
              <div className="bg-white rounded-lg shadow-md p-4 max-w-6xl mx-auto">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <Bug className="h-6 w-6 mr-3 text-red-600" />
                  Pest & Disease Detection
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Current Status</h3>
                    <div className="space-y-3">
                      <div className={`flex items-center justify-between p-3 rounded-lg ${
                        stats.pest_count?.average > 2 ? 'bg-red-50 border border-red-200' : 
                        stats.pest_count?.average > 1 ? 'bg-yellow-50 border border-yellow-200' : 
                        'bg-green-50 border border-green-200'
                      }`}>
                        <div>
                          <div className={`font-medium ${
                            stats.pest_count?.average > 2 ? 'text-red-800' : 
                            stats.pest_count?.average > 1 ? 'text-yellow-800' : 
                            'text-green-800'
                          }`}>
                            Pest Count: {stats.pest_count?.average?.toFixed(1) || '0'}
                        </div>
                          <div className={`text-sm ${
                            stats.pest_count?.average > 2 ? 'text-red-600' : 
                            stats.pest_count?.average > 1 ? 'text-yellow-600' : 
                            'text-green-600'
                          }`}>
                            Severity: {stats.pest_count?.average > 2 ? 'High' : 
                                     stats.pest_count?.average > 1 ? 'Medium' : 'Low'}
                      </div>
                        </div>
                        <div className={`text-xs ${
                          stats.pest_count?.average > 2 ? 'text-red-500' : 
                          stats.pest_count?.average > 1 ? 'text-yellow-500' : 
                          'text-green-500'
                        }`}>
                          Live
                        </div>
                      </div>
                      
                      <div className={`flex items-center justify-between p-3 rounded-lg ${
                        stats.disease_risk?.average > 30 ? 'bg-red-50 border border-red-200' : 
                        stats.disease_risk?.average > 20 ? 'bg-yellow-50 border border-yellow-200' : 
                        'bg-green-50 border border-green-200'
                      }`}>
                        <div>
                          <div className={`font-medium ${
                            stats.disease_risk?.average > 30 ? 'text-red-800' : 
                            stats.disease_risk?.average > 20 ? 'text-yellow-800' : 
                            'text-green-800'
                          }`}>
                            Disease Risk: {stats.disease_risk?.average?.toFixed(1) || '0'}%
                        </div>
                          <div className={`text-sm ${
                            stats.disease_risk?.average > 30 ? 'text-red-600' : 
                            stats.disease_risk?.average > 20 ? 'text-yellow-600' : 
                            'text-green-600'
                          }`}>
                            Level: {stats.disease_risk?.average > 30 ? 'High' : 
                                   stats.disease_risk?.average > 20 ? 'Medium' : 'Low'}
                          </div>
                        </div>
                        <div className={`text-xs ${
                          stats.disease_risk?.average > 30 ? 'text-red-500' : 
                          stats.disease_risk?.average > 20 ? 'text-yellow-500' : 
                          'text-green-500'
                        }`}>
                          Live
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Environmental Factors</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Temperature</span>
                        <span className="font-medium">{stats.temperature?.average?.toFixed(1) || 'N/A'}°C</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Humidity</span>
                        <span className="font-medium">{stats.humidity?.average?.toFixed(1) || 'N/A'}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Leaf Wetness</span>
                        <span className="font-medium">{stats.leaf_wetness?.average?.toFixed(1) || '0'}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Risk Level</span>
                        <span className={`font-medium ${
                          stats.disease_risk?.average > 30 ? 'text-red-600' : 
                          stats.disease_risk?.average > 20 ? 'text-yellow-600' : 
                          'text-green-600'
                        }`}>
                          {stats.disease_risk?.average > 30 ? 'High' : 
                           stats.disease_risk?.average > 20 ? 'Medium' : 'Low'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-red-800 mb-3">AI Recommendations</h3>
                  <ul className="space-y-2 text-red-700">
                    {stats.pest_count?.average > 2 ? (
                      <>
                    <li>• Apply neem oil spray immediately to affected areas</li>
                    <li>• Increase air circulation to reduce humidity</li>
                    <li>• Monitor temperature and adjust greenhouse ventilation</li>
                    <li>• Schedule follow-up inspection in 24 hours</li>
                      </>
                    ) : stats.pest_count?.average > 1 ? (
                      <>
                        <li>• Apply preventive treatment with organic pesticides</li>
                        <li>• Monitor humidity levels closely</li>
                        <li>• Check for early signs of infestation</li>
                      </>
                    ) : (
                      <>
                        <li>• Continue regular monitoring</li>
                        <li>• Maintain optimal environmental conditions</li>
                        <li>• Apply preventive measures as scheduled</li>
                      </>
                    )}
                  </ul>
                </div>
              </div>
              
            </div>
          )}

          {/* Irrigation Tab */}
          {activeTab === 'irrigation' && (
            <div className="space-y-4" style={{ padding: '0px', backgroundColor: 'transparent' }}>
              <div className="bg-white rounded-lg shadow-md p-4 max-w-6xl mx-auto">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <Droplets className="h-6 w-6 mr-3 text-blue-600" />
                  Smart Irrigation Management
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Soil Moisture</h3>
                    <div className="text-3xl font-bold text-blue-600 mb-2">
                      {stats.soil_moisture?.average?.toFixed(1) || 'N/A'}%
                    </div>
                    <p className="text-sm text-gray-600">Optimal range: 60-80%</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, (stats.soil_moisture?.average || 0)))}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Water Usage Today</h3>
                    <div className="text-3xl font-bold text-green-600 mb-2">
                      {stats.water_usage?.average?.toFixed(1) || 'N/A'}L
                    </div>
                    <p className="text-sm text-gray-600">Target: 50L</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, ((stats.water_usage?.average || 0) / 50) * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Water Efficiency</h3>
                    <div className="text-3xl font-bold text-purple-600 mb-2">
                      {stats.water_efficiency?.average?.toFixed(1) || 'N/A'}%
                    </div>
                    <p className="text-sm text-gray-600">Target: &gt;80%</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, (stats.water_efficiency?.average || 0)))}%`}}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-800 mb-3">Irrigation Status</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium text-blue-700 mb-2">Auto Irrigation</h4>
                      <p className="text-sm text-blue-600">
                        Status: {stats.soil_moisture?.average < 60 ? 'ACTIVE' : 'STANDBY'} | 
                        Next: {stats.soil_moisture?.average < 60 ? 'Now' : '2h 15m'}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-blue-700 mb-2">Rainfall Today</h4>
                      <p className="text-sm text-blue-600">
                        Amount: {stats.rainfall?.average?.toFixed(2) || '0'}mm | 
                        Probability: 20%
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
            </div>
          )}

          {/* Environment Tab */}
          {activeTab === 'environment' && (
            <div className="space-y-4" style={{ padding: '0px', backgroundColor: 'transparent' }}>
              <div className="bg-white rounded-lg shadow-md p-4 max-w-6xl mx-auto">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <Thermometer className="h-6 w-6 mr-3 text-orange-600" />
                  Greenhouse Environment Control
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Temperature</h3>
                    <div className="text-3xl font-bold text-orange-600 mb-2">
                      {stats.temperature?.average?.toFixed(1) || 'N/A'}°C
                    </div>
                    <p className="text-sm text-gray-600">Target: 22-26°C</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-orange-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, ((stats.temperature?.average || 0) - 22) / 4 * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Humidity</h3>
                    <div className="text-3xl font-bold text-blue-600 mb-2">
                      {stats.humidity?.average?.toFixed(1) || 'N/A'}%
                    </div>
                    <p className="text-sm text-gray-600">Target: 60-70%</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, (stats.humidity?.average || 0)))}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">CO2 Level</h3>
                    <div className="text-3xl font-bold text-green-600 mb-2">
                      {stats.co2_level?.average?.toFixed(0) || 'N/A'} ppm
                    </div>
                    <p className="text-sm text-gray-600">Target: 400-500 ppm</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, ((stats.co2_level?.average || 0) - 400) / 100 * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Light Level</h3>
                    <div className="text-3xl font-bold text-yellow-600 mb-2">
                      {stats.light?.average?.toFixed(0) || 'N/A'} lux
                    </div>
                    <p className="text-sm text-gray-600">Target: 800-1000 lux</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-yellow-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, ((stats.light?.average || 0) - 800) / 200 * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-green-800 mb-3">System Status</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium text-green-700 mb-2">Ventilation</h4>
                      <p className="text-sm text-green-600">
                        Fans: {stats.temperature?.average > 25 ? 'ON' : 'OFF'} | 
                        Speed: {stats.temperature?.average > 25 ? '60%' : '0%'}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-green-700 mb-2">Heating</h4>
                      <p className="text-sm text-green-600">
                        Status: {stats.temperature?.average < 22 ? 'ON' : 'OFF'} | 
                        Setpoint: 25°C
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
            </div>
          )}

          {/* Harvest Tab */}
          {activeTab === 'harvest' && (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <Calendar className="h-6 w-6 mr-3 text-purple-600" />
                  Harvest Time Prediction
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Plant Height</h3>
                    <div className="text-3xl font-bold text-green-600 mb-2">
                      {stats.plant_height?.average?.toFixed(1) || 'N/A'} cm
                    </div>
                    <p className="text-sm text-gray-600">Growth Rate: {stats.plant_height?.trend || 'stable'}</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, ((stats.plant_height?.average || 0) / 30) * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Fruit Count</h3>
                    <div className="text-3xl font-bold text-red-600 mb-2">
                      {stats.fruit_count?.average?.toFixed(1) || 'N/A'}
                    </div>
                    <p className="text-sm text-gray-600">Per plant average</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-red-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, ((stats.fruit_count?.average || 0) / 5) * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Yield Prediction</h3>
                    <div className="text-3xl font-bold text-purple-600 mb-2">
                      {stats.yield_prediction?.average?.toFixed(0) || 'N/A'} kg
                    </div>
                    <p className="text-sm text-gray-600">Expected harvest</p>
                    <div className="mt-3 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full" 
                        style={{width: `${Math.min(100, Math.max(0, ((stats.yield_prediction?.average || 0) / 120) * 100))}%`}}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-purple-800 mb-3">Harvest Status</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-white border border-purple-200 rounded-lg">
                      <div>
                        <div className="font-medium text-purple-800">
                          Harvest Readiness: {stats.fruit_count?.average > 3 ? 'Ready' : 
                                           stats.fruit_count?.average > 1 ? 'Almost Ready' : 'Growing'}
                      </div>
                        <div className="text-sm text-purple-600">
                          Plants: {stats.plant_height?.average > 20 ? 'Mature' : 'Growing'} | 
                          Fruits: {stats.fruit_count?.average?.toFixed(1) || '0'} per plant
                    </div>
                      </div>
                      <div className={`text-sm font-medium ${
                        stats.fruit_count?.average > 3 ? 'text-green-600' : 
                        stats.fruit_count?.average > 1 ? 'text-yellow-600' : 
                        'text-blue-600'
                      }`}>
                        {stats.fruit_count?.average > 3 ? 'Ready Now' : 
                         stats.fruit_count?.average > 1 ? '1-2 weeks' : '3-4 weeks'}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 bg-white border border-purple-200 rounded-lg">
                      <div>
                        <div className="font-medium text-purple-800">Expected Yield</div>
                        <div className="text-sm text-purple-600">
                          Prediction: {stats.yield_prediction?.average?.toFixed(0) || '0'}kg | 
                          Efficiency: {stats.yield_efficiency?.average?.toFixed(1) || '0'}%
                      </div>
                      </div>
                      <div className="text-sm text-purple-500">
                        {stats.yield_prediction?.average > 100 ? 'High' : 
                         stats.yield_prediction?.average > 80 ? 'Medium' : 'Low'} Yield
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Marketplace Tab */}
          {activeTab === 'marketplace' && (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <ShoppingCart className="h-6 w-6 mr-3 text-green-600" />
                  Agricultural Marketplace
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Input Supplies</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-white border border-gray-200 rounded-lg">
                        <div>
                          <div className="font-medium">Organic Fertilizer</div>
                          <div className="text-sm text-gray-600">25kg bag</div>
                        </div>
                        <div className="text-green-600 font-bold">$45.99</div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-white border border-gray-200 rounded-lg">
                        <div>
                          <div className="font-medium">Seeds - Tomato</div>
                          <div className="text-sm text-gray-600">1000 seeds</div>
                        </div>
                        <div className="text-green-600 font-bold">$12.50</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Your Products</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-white border border-gray-200 rounded-lg">
                        <div>
                          <div className="font-medium">Fresh Tomatoes</div>
                          <div className="text-sm text-gray-600">15kg available</div>
                        </div>
                        <div className="text-blue-600 font-bold">$3.50/kg</div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-white border border-gray-200 rounded-lg">
                        <div>
                          <div className="font-medium">Organic Lettuce</div>
                          <div className="text-sm text-gray-600">25 heads available</div>
                        </div>
                        <div className="text-blue-600 font-bold">$2.00/head</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-green-800 mb-3">Market Trends</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <h4 className="font-medium text-green-700 mb-2">Tomato Price</h4>
                      <p className="text-sm text-green-600">↑ +5% this week</p>
                    </div>
                    <div>
                      <h4 className="font-medium text-green-700 mb-2">Lettuce Demand</h4>
                      <p className="text-sm text-green-600">↑ High demand</p>
                    </div>
                    <div>
                      <h4 className="font-medium text-green-700 mb-2">Pepper Supply</h4>
                      <p className="text-sm text-green-600">↓ Low supply</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Consultation Tab */}
          {activeTab === 'consultation' && (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <Users className="h-6 w-6 mr-3 text-indigo-600" />
                  Expert Consultation
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Available Experts</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg">
                        <div>
                          <div className="font-medium">Dr. Sarah Johnson</div>
                          <div className="text-sm text-gray-600">Plant Pathology Specialist</div>
                        </div>
                        <div className="text-green-600 text-sm">Online</div>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg">
                        <div>
                          <div className="font-medium">Mike Chen</div>
                          <div className="text-sm text-gray-600">Soil Science Expert</div>
                        </div>
                        <div className="text-yellow-600 text-sm">Busy</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Recent Consultations</h3>
                    <div className="space-y-3">
                      <div className="p-3 bg-white border border-gray-200 rounded-lg">
                        <div className="font-medium text-gray-800">Aphid Treatment</div>
                        <div className="text-sm text-gray-600">Resolved - Dr. Johnson</div>
                        <div className="text-xs text-gray-500">2 days ago</div>
                      </div>
                      <div className="p-3 bg-white border border-gray-200 rounded-lg">
                        <div className="font-medium text-gray-800">Soil pH Adjustment</div>
                        <div className="text-sm text-gray-600">In Progress - Mike Chen</div>
                        <div className="text-xs text-gray-500">1 week ago</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-indigo-800 mb-3">Schedule Consultation</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-indigo-700 mb-2">Select Expert</label>
                      <select className="w-full p-2 border border-indigo-300 rounded-md">
                        <option>Dr. Sarah Johnson - Plant Pathology</option>
                        <option>Mike Chen - Soil Science</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-indigo-700 mb-2">Issue Type</label>
                      <select className="w-full p-2 border border-indigo-300 rounded-md">
                        <option>Pest Control</option>
                        <option>Disease Management</option>
                        <option>Soil Health</option>
                        <option>Plant Nutrition</option>
                      </select>
                    </div>
                  </div>
                  <button className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                    Schedule Consultation
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <TrendingUp className="h-6 w-6 mr-3 text-blue-600" />
                  Data Analytics & Reporting
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Yield This Month</h3>
                    <div className="text-3xl font-bold text-green-600 mb-2">245 kg</div>
                    <p className="text-sm text-gray-600">↑ +12% vs last month</p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Water Efficiency</h3>
                    <div className="text-3xl font-bold text-blue-600 mb-2">87%</div>
                    <p className="text-sm text-gray-600">↑ +5% improvement</p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Energy Usage</h3>
                    <div className="text-3xl font-bold text-orange-600 mb-2">1,250 kWh</div>
                    <p className="text-sm text-gray-600">↓ -8% vs last month</p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Profit Margin</h3>
                    <div className="text-3xl font-bold text-purple-600 mb-2">23%</div>
                    <p className="text-sm text-gray-600">↑ +3% vs last month</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Performance Trends</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Temperature Stability</span>
                        <span className="text-green-600 font-bold">94%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Humidity Control</span>
                        <span className="text-green-600 font-bold">91%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Irrigation Accuracy</span>
                        <span className="text-green-600 font-bold">88%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Generate Report</h3>
                    <div className="space-y-3">
                      <button className="w-full p-3 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                        Monthly Performance Report
                      </button>
                      <button className="w-full p-3 bg-green-600 text-white rounded-md hover:bg-green-700">
                        Yield Analysis Report
                      </button>
                      <button className="w-full p-3 bg-purple-600 text-white rounded-md hover:bg-purple-700">
                        Cost-Benefit Analysis
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}


          {/* Alerts Tab */}
          {activeTab === 'alerts' && (
            <div className="space-y-4" style={{ padding: '0px', backgroundColor: 'transparent' }}>
              <div className="bg-white rounded-lg shadow-md p-4 max-w-6xl mx-auto">
                <AlertsManager sessionId={sessionId} />
              </div>
            </div>
          )}


          {/* Footer */}
          <footer className="mt-12 text-center text-sm text-gray-500">
            <p>Smart Agriculture Dashboard MVP - Real-time farm monitoring with AI analysis</p>
            <p className="mt-1">
              Backend: {wsConnected ? 'WebSocket' : 'Polling'} | 
              Data points: {sensorData.length} | 
              Sensors: {sensorTypes.length} |
              AI: {activeTab === 'alerts' ? 'Alert Management Active' : 'Available'}
            </p>
          </footer>
        </main>

        {/* AI Assistant Right Sidebar - Always visible */}
        {aiSidebarOpen && (
          <div 
            className={`fixed top-0 right-0 z-50 h-full bg-white shadow-lg transform transition-transform duration-300 ease-in-out ${isResizing ? 'select-none' : ''}`}
            style={{ width: `${sidebarWidth}px` }}
          >
            {/* Resize Handle */}
            <div
              className={`absolute left-0 top-0 w-1 h-full cursor-col-resize transition-colors duration-200 ${
                isResizing ? 'bg-blue-500' : 'bg-gray-200 hover:bg-gray-300'
              }`}
              onMouseDown={handleMouseDown}
              title="Drag to resize sidebar"
            />
            
            <div className="flex items-center justify-between h-12 px-6 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-semibold text-gray-800">
                  AI Assistant - {activeTab === 'irrigation' ? 'Irrigation' : 
                                 activeTab === 'environment' ? 'Environment' : 
                                 activeTab === 'pest-detection' ? 'Pest Detection' :
                                 activeTab === 'fertilization' ? 'Fertilization' :
                                 activeTab === 'harvest' ? 'Harvest' :
                                 activeTab === 'marketplace' ? 'Marketplace' :
                                 activeTab === 'consultation' ? 'Consultation' :
                                 activeTab === 'analytics' ? 'Analytics' :
                                 activeTab === 'alerts' ? 'Alerts' :
                                 'Dashboard'}
                </h2>
                {isResizing && (
                  <span className="text-xs text-blue-600 font-medium">
                    {sidebarWidth}px
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                {/* New Chat Button - Plus icon */}
                <button
                  onClick={() => {
                    // Trigger new chat in LangChainChat component
                    const event = new CustomEvent('newChat');
                    window.dispatchEvent(event);
                  }}
                  className="p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                  title="New Chat"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                </button>
                
                {/* Close Button */}
                <button
                  onClick={() => setAiSidebarOpen(false)}
                  className="p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
            
            <div className="h-[calc(100vh-3rem)] overflow-hidden" style={{ width: `${sidebarWidth}px` }}>
              <LangChainChat currentFeature={activeTab} sidebarWidth={sidebarWidth} sessionId={sessionId} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
