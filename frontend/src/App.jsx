import React, { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [sessionId, setSessionId] = useState('default')

  // Get session ID from URL or generate one
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

  const renderPage = () => {
    return <Dashboard />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Content */}
      <main>
        {renderPage()}
      </main>
    </div>
  )
}

export default App
