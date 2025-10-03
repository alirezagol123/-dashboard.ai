import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { Activity, Thermometer, Droplets, Gauge, Sun, Zap } from 'lucide-react'

const Chart = ({ data, isLoading }) => {
  const [chartData, setChartData] = useState([])

  // Sensor type configurations
  const sensorConfigs = {
    temperature: {
      color: '#ef4444',
      icon: Thermometer,
      unit: '°C',
      threshold: { min: 15, max: 35 }
    },
    humidity: {
      color: '#3b82f6',
      icon: Droplets,
      unit: '%',
      threshold: { min: 30, max: 80 }
    },
    pressure: {
      color: '#8b5cf6',
      icon: Gauge,
      unit: 'hPa',
      threshold: { min: 980, max: 1020 }
    },
    light: {
      color: '#f59e0b',
      icon: Sun,
      unit: 'lux',
      threshold: { min: 0, max: 1000 }
    },
    motion: {
      color: '#10b981',
      icon: Zap,
      unit: '',
      threshold: { min: 0, max: 1 }
    }
  }

  // Process data for chart
  useEffect(() => {
    if (!data || data.length === 0) {
      setChartData([])
      return
    }

    // Group data by timestamp
    const groupedData = {}
    
    data.forEach(item => {
      const timestamp = new Date(item.timestamp).toLocaleTimeString()
      if (!groupedData[timestamp]) {
        groupedData[timestamp] = { timestamp }
      }
      groupedData[timestamp][item.sensor_type] = item.value
    })

    // Convert to array and sort by timestamp
    const chartDataArray = Object.values(groupedData)
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      .slice(-20) // Keep only last 20 data points

    setChartData(chartDataArray)
  }, [data])

  // Get available sensor types from data
  const availableSensors = Object.keys(sensorConfigs).filter(sensorType =>
    chartData.some(item => item[sensorType] !== undefined)
  )

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <Activity className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>No data available</p>
            <p className="text-sm">Waiting for sensor data...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800 flex items-center">
          <Activity className="h-5 w-5 mr-2 text-blue-600" />
          Real-time Sensor Data
        </h2>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="timestamp" 
              stroke="#666"
              fontSize={12}
              tickFormatter={(value) => value.split(' ')[1] || value}
            />
            <YAxis stroke="#666" fontSize={12} />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              formatter={(value, name) => [
                `${value}${sensorConfigs[name]?.unit || ''}`,
                typeof name === 'string' ? name.charAt(0).toUpperCase() + name.slice(1) : String(name)
              ]}
            />
            <Legend />
            
            {availableSensors.map(sensorType => {
              const config = sensorConfigs[sensorType]
              const Icon = config.icon
              return (
                <Line
                  key={sensorType}
                  type="monotone"
                  dataKey={sensorType}
                  stroke={config.color}
                  strokeWidth={2}
                  dot={{ fill: config.color, strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: config.color, strokeWidth: 2 }}
                  name={
                    <div className="flex items-center">
                      <Icon className="h-4 w-4 mr-1" style={{ color: config.color }} />
                      {sensorType.charAt(0).toUpperCase() + sensorType.slice(1)}
                    </div>
                  }
                />
              )
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
        {availableSensors.map(sensorType => {
          const config = sensorConfigs[sensorType]
          const Icon = config.icon
          return (
            <div key={sensorType} className="flex items-center text-sm">
              <div 
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: config.color }}
              />
              <Icon className="h-4 w-4 mr-1 text-gray-600" />
              <span className="text-gray-600 capitalize">{sensorType}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Chart
