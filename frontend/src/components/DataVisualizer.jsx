import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Plot from 'react-plotly.js'

const DataVisualizer = () => {
  const [chartData, setChartData] = useState(null)
  const [chartType, setChartType] = useState('line')
  const [xColumn, setXColumn] = useState('timestamp')
  const [yColumn, setYColumn] = useState('value')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [availableColumns, setAvailableColumns] = useState([])

  useEffect(() => {
    // Load available columns from data summary with retry logic
    const loadColumns = async () => {
      let attempts = 0
      const maxAttempts = 3
      const delay = 1000

      while (attempts < maxAttempts) {
        try {
          const response = await axios.get('http://localhost:8000/data/summary')
          setAvailableColumns(response.data.columns || [])
          return // Success, exit retry loop
        } catch (error) {
          attempts++
          if (attempts < maxAttempts) {
            console.log(`🔄 Visualizer: Backend not ready, retrying... (${attempts}/${maxAttempts})`)
            await new Promise(resolve => setTimeout(resolve, delay))
          } else {
            console.error('❌ Visualizer: Failed to load columns:', error)
            setAvailableColumns(['timestamp', 'sensor_type', 'value']) // Fallback columns
          }
        }
      }
    }

    loadColumns()
  }, [])

  const createVisualization = async () => {
    if (!xColumn || !yColumn) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await axios.post('http://localhost:8000/visualize', {
        chart_type: chartType,
        columns: [xColumn, yColumn]
      })

      if (response.data.success) {
        const chartConfig = JSON.parse(response.data.chart)
        setChartData(chartConfig)
      } else {
        setError(response.data.error || 'Failed to create visualization')
      }
    } catch (error) {
      setError(error.response?.data?.detail || error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const chartTypes = [
    { value: 'line', label: 'Line Chart' },
    { value: 'bar', label: 'Bar Chart' },
    { value: 'scatter', label: 'Scatter Plot' },
    { value: 'histogram', label: 'Histogram' }
  ]

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        📊 Data Visualizer
      </h2>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Chart Type
          </label>
          <select
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {chartTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            X Axis
          </label>
          <select
            value={xColumn}
            onChange={(e) => setXColumn(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {availableColumns.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Y Axis
          </label>
          <select
            value={yColumn}
            onChange={(e) => setYColumn(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {availableColumns.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={createVisualization}
            disabled={isLoading}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Creating...' : 'Create Chart'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Chart Display */}
      <div className="border border-gray-200 rounded-lg p-4 min-h-96">
        {chartData ? (
          <Plot
            data={chartData.data}
            layout={chartData.layout}
            config={{ responsive: true }}
            style={{ width: '100%', height: '400px' }}
          />
        ) : (
          <div className="flex items-center justify-center h-96 text-gray-500">
            <div className="text-center">
              <div className="text-4xl mb-2">📈</div>
              <p>Select chart type and columns, then click "Create Chart"</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DataVisualizer
