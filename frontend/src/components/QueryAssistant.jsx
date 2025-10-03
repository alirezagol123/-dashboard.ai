import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { MessageSquare, Database, Zap, Globe, AlertCircle, CheckCircle, Clock } from 'lucide-react'

const QueryAssistant = ({ currentFeature = 'dashboard' }) => {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [queryHistory, setQueryHistory] = useState([])
  const [examples, setExamples] = useState([])

  // Load examples on component mount
  useEffect(() => {
    loadExamples()
  }, [currentFeature])

  const loadExamples = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/semantic/sample-queries')
      setExamples(response.data[currentFeature] || [])
    } catch (error) {
      console.error('Failed to load examples:', error)
    }
  }

  const executeQuery = async () => {
    if (!query.trim() || isLoading) return

    setIsLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await axios.post('http://127.0.0.1:8000/ask', {
        query: query,
        feature_context: currentFeature,
        session_id: 'default'
      })

      const result = response.data
      
      if (result.success) {
        setResults({
          summary: result.response,
          metrics: result.metrics,
          raw_data: result.data,
          sql: result.sql,
          language: result.detected_language,
          intent: result.detected_intent
        })
        // Add to history
        setQueryHistory(prev => [result, ...prev.slice(0, 9)]) // Keep last 10
      } else {
        setError(result.error || 'Query failed')
      }
    } catch (error) {
      console.error('Query execution error:', error)
      setError(error.response?.data?.detail || 'Failed to execute query')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      executeQuery()
    }
  }

  const handleExampleClick = (example) => {
    setQuery(example)
    setTimeout(() => executeQuery(), 100)
  }

  const formatRawData = (rawData) => {
    if (!rawData) return null
    
    const lines = rawData.split('\n').filter(line => line.trim())
    if (lines.length === 0) return null

    const headers = lines[0].split('|')
    const rows = lines.slice(1).map(line => line.split('|'))

    return { headers, rows }
  }

  const getFeatureIcon = () => {
    switch (currentFeature) {
      case 'irrigation': return '💧'
      case 'environment': return '🌡️'
      case 'pest-detection': return '🐛'
      default: return '📊'
    }
  }

  const getFeatureName = () => {
    switch (currentFeature) {
      case 'irrigation': return 'Irrigation'
      case 'environment': return 'Environment'
      case 'pest-detection': return 'Pest Detection'
      default: return 'Dashboard'
    }
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{getFeatureIcon()}</div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              Dynamic Query Assistant
            </h2>
            <p className="text-sm text-gray-600">
              Ask questions about {getFeatureName()} data in natural language
            </p>
          </div>
        </div>
      </div>

      {/* Query Input */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex space-x-3">
          <div className="flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Ask about ${getFeatureName().toLowerCase()} data... (e.g., "When was the last irrigation?")`}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
          </div>
          <button
            onClick={executeQuery}
            disabled={!query.trim() || isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                <span>Querying...</span>
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" />
                <span>Query</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Examples */}
      {examples.length > 0 && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Example Queries:</h3>
          <div className="flex flex-wrap gap-2">
            {examples.slice(0, 6).map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                className="px-3 py-1 text-xs bg-white border border-gray-300 rounded-full hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <h3 className="text-sm font-medium text-red-800">Query Error</h3>
            </div>
            <p className="mt-2 text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Success Results */}
        {results && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <h3 className="text-sm font-medium text-green-800">Query Result</h3>
              </div>
              <p className="mt-2 text-sm text-green-700">{results.summary}</p>
              {results.language === 'persian' && (
                <div className="mt-2 flex items-center space-x-1 text-xs text-green-600">
                  <Globe className="h-3 w-3" />
                  <span>Translated from Persian</span>
                </div>
              )}
            </div>

            {/* Metrics */}
            {results.metrics && Object.keys(results.metrics).length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-blue-800 mb-3">Key Metrics</h3>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(results.metrics).map(([key, value]) => (
                    <div key={key} className="bg-white rounded p-2">
                      <div className="text-xs text-gray-600 capitalize">{key.replace('_', ' ')}</div>
                      <div className="text-lg font-semibold text-blue-700">{value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Raw Data Table */}
            {results.raw_data && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-3">
                  <Database className="h-4 w-4 text-gray-600" />
                  <h3 className="text-sm font-medium text-gray-800">Raw Data</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-200">
                        {formatRawData(results.raw_data)?.headers.map((header, index) => (
                          <th key={index} className="px-2 py-1 text-left font-medium text-gray-600">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {formatRawData(results.raw_data)?.rows.map((row, rowIndex) => (
                        <tr key={rowIndex} className="border-b border-gray-100">
                          {row.map((cell, cellIndex) => (
                            <td key={cellIndex} className="px-2 py-1 text-gray-800">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* SQL Query */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-800 mb-2">Generated SQL</h3>
              <code className="text-xs text-gray-700 bg-white p-2 rounded block overflow-x-auto">
                {results.sql}
              </code>
            </div>
          </div>
        )}

        {/* Query History */}
        {queryHistory.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-800 mb-3">Recent Queries</h3>
            <div className="space-y-2">
              {queryHistory.slice(0, 5).map((historyItem, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-800">
                      {historyItem.original_question}
                    </div>
                    <div className="text-xs text-gray-600">
                      {historyItem.summary}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setQuery(historyItem.original_question)
                      setTimeout(() => executeQuery(), 100)
                    }}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Re-run
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!results && !error && !isLoading && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-800 mb-2">
                Ask a Question
              </h3>
              <p className="text-sm text-gray-600">
                Use natural language to query your {getFeatureName().toLowerCase()} data
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default QueryAssistant
