import React from 'react'
import { AlertTriangle, Thermometer, Droplets, Gauge, Sun, Zap, X } from 'lucide-react'

const AlertBox = ({ alerts, onDismiss }) => {
  const sensorConfigs = {
    temperature: {
      icon: Thermometer,
      color: 'text-red-500',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      unit: '°C',
      name: 'Temperature'
    },
    humidity: {
      icon: Droplets,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      unit: '%',
      name: 'Humidity'
    },
    pressure: {
      icon: Gauge,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      unit: 'hPa',
      name: 'Pressure'
    },
    light: {
      icon: Sun,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      name: 'Light'
    },
    motion: {
      icon: Zap,
      color: 'text-green-500',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      name: 'Motion'
    }
  }

  // Threshold configurations
  const thresholds = {
    temperature: { min: 15, max: 35 },
    humidity: { min: 30, max: 80 },
    pressure: { min: 980, max: 1020 },
    light: { min: 0, max: 1000 },
    motion: { min: 0, max: 1 }
  }

  // Generate alerts based on current data
  const generateAlerts = (data) => {
    const activeAlerts = []
    
    if (!data) return activeAlerts

    Object.entries(data).forEach(([sensorType, stats]) => {
      const threshold = thresholds[sensorType]
      const config = sensorConfigs[sensorType]
      
      if (!threshold || !stats) return

      const currentValue = stats.average
      const unit = config.unit

      if (currentValue < threshold.min) {
        activeAlerts.push({
          id: `${sensorType}-low-${Date.now()}`,
          sensorType,
          type: 'low',
          message: `${config.name} is below threshold (${currentValue.toFixed(1)}${unit} < ${threshold.min}${unit})`,
          severity: 'warning',
          timestamp: new Date().toISOString()
        })
      }

      if (currentValue > threshold.max) {
        activeAlerts.push({
          id: `${sensorType}-high-${Date.now()}`,
          sensorType,
          type: 'high',
          message: `${config.name} is above threshold (${currentValue.toFixed(1)}${unit} > ${threshold.max}${unit})`,
          severity: 'critical',
          timestamp: new Date().toISOString()
        })
      }
    })

    return activeAlerts
  }

  const activeAlerts = generateAlerts(alerts)

  if (activeAlerts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center mb-4">
          <div className="p-2 rounded-lg bg-green-50">
            <AlertTriangle className="h-6 w-6 text-green-500" />
          </div>
          <h3 className="ml-3 text-lg font-semibold text-gray-800">
            System Status
          </h3>
        </div>
        <div className="text-center py-4">
          <div className="text-green-600 font-medium mb-2">All systems normal</div>
          <div className="text-sm text-gray-500">No threshold alerts</div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className="p-2 rounded-lg bg-red-50">
            <AlertTriangle className="h-6 w-6 text-red-500" />
          </div>
          <h3 className="ml-3 text-lg font-semibold text-gray-800">
            Active Alerts
          </h3>
        </div>
        <div className="text-sm text-red-600 font-medium">
          {activeAlerts.length} alert{activeAlerts.length !== 1 ? 's' : ''}
        </div>
      </div>

      <div className="space-y-3">
        {activeAlerts.map((alert) => {
          const config = sensorConfigs[alert.sensorType]
          const Icon = config.icon
          
          return (
            <div
              key={alert.id}
              className={`p-4 rounded-lg border-l-4 ${
                alert.severity === 'critical' 
                  ? 'bg-red-50 border-red-500' 
                  : 'bg-yellow-50 border-yellow-500'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  <Icon className={`h-5 w-5 mt-0.5 mr-3 ${
                    alert.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'
                  }`} />
                  <div>
                    <div className={`font-medium ${
                      alert.severity === 'critical' ? 'text-red-800' : 'text-yellow-800'
                    }`}>
                      {alert.message}
                    </div>
                    <div className={`text-sm mt-1 ${
                      alert.severity === 'critical' ? 'text-red-600' : 'text-yellow-600'
                    }`}>
                      {new Date(alert.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
                {onDismiss && (
                  <button
                    onClick={() => onDismiss(alert.id)}
                    className={`ml-2 p-1 rounded-full hover:bg-white hover:bg-opacity-50 ${
                      alert.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'
                    }`}
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="text-xs text-gray-500">
          <div className="flex items-center justify-between">
            <span>Thresholds:</span>
            <div className="text-right">
              <div>Temp: 15-35°C</div>
              <div>Humidity: 30-80%</div>
              <div>Pressure: 980-1020 hPa</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AlertBox
