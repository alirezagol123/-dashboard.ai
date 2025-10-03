import React from 'react'
import { Thermometer, Droplets, Gauge, Sun, Zap, TrendingUp, TrendingDown, Minus } from 'lucide-react'

const StatsCard = ({ sensorType, stats, rowIndex = 0, colIndex = 0 }) => {
  const sensorConfigs = {
    temperature: {
      icon: Thermometer,
      color: 'text-red-500',
      bgColor: 'bg-red-50',
      unit: '°C',
      name: 'Temperature'
    },
    humidity: {
      icon: Droplets,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
      unit: '%',
      name: 'Humidity'
    },
    pressure: {
      icon: Gauge,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50',
      unit: 'hPa',
      name: 'Pressure'
    },
    light: {
      icon: Sun,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-50',
      name: 'Light'
    },
    motion: {
      icon: Zap,
      color: 'text-green-500',
      bgColor: 'bg-green-50',
      name: 'Motion'
    }
  }

  const config = sensorConfigs[sensorType] || {
    icon: Minus,
    color: 'text-gray-500',
    bgColor: 'bg-gray-50',
    unit: '',
    name: sensorType
  }

  const Icon = config.icon

  if (!stats) {
    return (
      <div className="bg-white rounded-lg shadow-md p-3 flex-shrink-0" style={{ width: '300px', minWidth: '300px' }}>
        <div className="flex items-center mb-4">
          <div className={`p-2 rounded-lg ${config.bgColor}`}>
            <Icon className={`h-6 w-6 ${config.color}`} />
          </div>
          <h3 className="ml-3 text-lg font-semibold text-gray-800">
            {config.name}
          </h3>
        </div>
        <div className="text-center text-gray-500 py-8">
          No data available
        </div>
      </div>
    )
  }

  const formatValue = (value) => {
    if (value === null || value === undefined) return 'N/A'
    return `${value.toFixed(1)}${config.unit}`
  }

  const getTrendIcon = (current, average) => {
    if (current > average) {
      return <TrendingUp className="h-4 w-4 text-green-500" />
    } else if (current < average) {
      return <TrendingDown className="h-4 w-4 text-red-500" />
    } else {
      return <Minus className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-3 hover:shadow-lg transition-shadow flex-shrink-0" style={{ width: '300px', minWidth: '300px' }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className={`p-2 rounded-lg ${config.bgColor}`}>
            <Icon className={`h-6 w-6 ${config.color}`} />
          </div>
          <h3 className="ml-3 text-lg font-semibold text-gray-800">
            {config.name}
          </h3>
        </div>
        <div className="text-sm text-gray-500">
          {stats.count} readings
        </div>
      </div>

      <div className="space-y-3">
        {/* Current Value */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Current</span>
          <div className="flex items-center">
            <span className="text-lg font-semibold text-gray-800">
              {formatValue(stats.average)}
            </span>
            {getTrendIcon(stats.average, stats.average)}
          </div>
        </div>

        {/* Min Value */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Min</span>
          <span className="text-sm font-medium text-gray-800">
            {formatValue(stats.min_value)}
          </span>
        </div>

        {/* Max Value */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Max</span>
          <span className="text-sm font-medium text-gray-800">
            {formatValue(stats.max_value)}
          </span>
        </div>

        {/* Average */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Average</span>
          <span className="text-sm font-medium text-gray-800">
            {formatValue(stats.average)}
          </span>
        </div>

        {/* Last Update */}
        {stats.latest_timestamp && (
          <div className="pt-2 border-t border-gray-100">
            <div className="text-xs text-gray-500">
              Last: {new Date(stats.latest_timestamp).toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default StatsCard
