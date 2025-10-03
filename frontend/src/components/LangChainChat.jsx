import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js'
import { Line, Bar, Doughnut } from 'react-chartjs-2'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

// FormattedMessage component for rendering structured content
const FormattedMessage = ({ content, chart, chartType, sidebarWidth = 320 }) => {
  if (!content || !Array.isArray(content)) {
    return <span>{content}</span>
  }

  const renderChart = (chartData, type) => {
    try {
      if (!chartData || !chartData.labels || !chartData.datasets) return null;
    
    // Enhanced chart options with professional styling
    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 25,
            font: {
              size: 14,
              weight: '500'
            }
          }
        },
        title: {
          display: true,
          text: type === 'line' ? '📈 Trend Analysis' : 
                type === 'bar' ? '📊 Comparison Chart' : 
                type === 'histogram' ? '📈 Distribution Analysis' : 
                type === 'pie' ? '🥧 Percentage Breakdown' : '📊 Data Visualization',
          font: {
            size: 18,
            weight: 'bold',
            family: 'Inter, system-ui, sans-serif'
          },
          color: '#374151',
          padding: {
            top: 15,
            bottom: 25
          }
        },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: true,
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 13
          },
          padding: 12,
          callbacks: {
            title: function(context) {
              if (type === 'line') {
                return `📅 ${context[0].label}`;
              } else if (type === 'pie') {
                return `📊 ${context[0].label}`;
              }
              return `📈 ${context[0].label}`;
            },
            label: function(context) {
              const value = context.parsed.y || context.parsed;
              const unit = type === 'pie' ? '%' : '';
              return `${context.dataset.label}: ${value.toFixed(2)}${unit}`;
            }
          }
        }
      },
      scales: type === 'pie' ? {} : {
        x: {
          display: true,
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.1)',
            drawBorder: false
          },
          ticks: {
            font: {
              size: 13,
              family: 'Inter, system-ui, sans-serif'
            },
            color: '#6b7280',
            maxRotation: type === 'line' ? 45 : 0,
            maxTicksLimit: 8,
            padding: 8,
            callback: function(value, index, ticks) {
              const label = this.getLabelForValue(value);
              // For time-based labels, show every nth label to avoid crowding
              if (type === 'line' && ticks.length > 6) {
                const step = Math.ceil(ticks.length / 6);
                return index % step === 0 ? label : '';
              }
              return label;
            }
          },
          title: {
            display: true,
            text: type === 'line' ? '⏰ Time Period' : '📋 Categories',
            font: {
              size: 14,
              weight: '600',
              family: 'Inter, system-ui, sans-serif'
            },
            color: '#374151',
            padding: {
              top: 15
            }
          }
        },
        y: {
          display: true,
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.1)',
            drawBorder: false
          },
          ticks: {
            font: {
              size: 13,
              family: 'Inter, system-ui, sans-serif'
            },
            color: '#6b7280',
            padding: 8,
            callback: function(value) {
              return value.toFixed(1);
            }
          },
          title: {
            display: true,
            text: '📊 Value',
            font: {
              size: 14,
              weight: '600',
              family: 'Inter, system-ui, sans-serif'
            },
            color: '#374151',
            padding: {
              bottom: 15
            }
          }
        }
      },
      elements: {
        point: {
          radius: 6,
          hoverRadius: 8,
          borderWidth: 3
        },
        line: {
          tension: 0.4,
          borderWidth: 2
        },
        bar: {
          borderRadius: 4,
          borderSkipped: false
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeInOutQuart',
        delay: (context) => {
          let delay = 0;
          if (context.type === 'data' && context.mode === 'default') {
            delay = context.dataIndex * 100 + context.datasetIndex * 100;
          }
          return delay;
        }
      },
      responsive: true,
      maintainAspectRatio: false,
      onHover: (event, activeElements) => {
        event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
      }
    };

    // Enhanced chart data with better colors and styling
    const enhancedChartData = {
      ...chartData,
      datasets: chartData.datasets.map((dataset, index) => {
        const colorPalette = [
          {
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderColor: 'rgba(59, 130, 246, 1)',
            pointBackgroundColor: 'rgba(59, 130, 246, 1)',
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: 'rgba(59, 130, 246, 1)'
          },
          {
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderColor: 'rgba(16, 185, 129, 1)',
            pointBackgroundColor: 'rgba(16, 185, 129, 1)',
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: 'rgba(16, 185, 129, 1)'
          },
          {
            backgroundColor: 'rgba(245, 101, 101, 0.1)',
            borderColor: 'rgba(245, 101, 101, 1)',
            pointBackgroundColor: 'rgba(245, 101, 101, 1)',
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: 'rgba(245, 101, 101, 1)'
          },
          {
            backgroundColor: 'rgba(251, 191, 36, 0.1)',
            borderColor: 'rgba(251, 191, 36, 1)',
            pointBackgroundColor: 'rgba(251, 191, 36, 1)',
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: 'rgba(251, 191, 36, 1)'
          }
        ];
        
        const pieColors = [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 101, 101, 0.8)',
          'rgba(251, 191, 36, 0.8)',
          'rgba(139, 92, 246, 0.8)',
          'rgba(236, 72, 153, 0.8)'
        ];

        if (type === 'pie') {
          return {
            ...dataset,
            backgroundColor: pieColors.slice(0, dataset.data.length),
            borderColor: '#ffffff',
            borderWidth: 2,
            hoverBorderWidth: 3
          };
        }

        const colors = colorPalette[index % colorPalette.length];
        return {
          ...dataset,
          ...colors,
          fill: type === 'line' ? true : false,
          tension: type === 'line' ? 0.4 : 0
        };
      })
    };

    // Render different chart types
    const renderChartComponent = () => {
      switch (type) {
        case 'line':
          return <Line data={enhancedChartData} options={chartOptions} />;
        case 'bar':
          return <Bar data={enhancedChartData} options={chartOptions} />;
        case 'histogram':
          return <Bar data={enhancedChartData} options={chartOptions} />;
        case 'pie':
          return <Doughnut data={enhancedChartData} options={chartOptions} />;
        default:
          return <Bar data={enhancedChartData} options={chartOptions} />;
      }
    };
    
    return (
      <div 
        className="bg-white rounded-lg border border-gray-100 shadow-inner overflow-hidden"
        style={{ 
          height: `${Math.max(384, Math.min(512, sidebarWidth * 0.8))}px`,
          width: `${Math.max(280, sidebarWidth - 40)}px`
        }}
      >
        <div className="w-full h-full">
          {renderChartComponent()}
        </div>
      </div>
    );
    } catch (error) {
      console.error('Chart rendering error:', error);
      return (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-red-600 text-sm">Chart rendering failed. Please try again.</p>
        </div>
      );
    }
  };

  return (
    <div className="space-y-1">
      {content.map((item, index) => {
        try {
        switch (item.type) {
          case 'header':
            const HeaderTag = `h${Math.min(item.level, 6)}`
            const headerClasses = {
              1: 'text-lg font-bold text-gray-900 mb-2',
              2: 'text-base font-semibold text-gray-800 mb-1',
              3: 'text-sm font-medium text-gray-700 mb-1',
              4: 'text-sm font-medium text-gray-600 mb-1',
              5: 'text-xs font-medium text-gray-600 mb-1',
              6: 'text-xs font-medium text-gray-500 mb-1'
            }
            return (
              <HeaderTag key={index} className={headerClasses[item.level] || headerClasses[6]}>
                {item.content}
              </HeaderTag>
            )
          
          case 'bullet':
            return (
              <div key={index} className="flex items-start space-x-2 space-x-reverse mr-4">
                <span className="text-gray-500 text-lg font-bold flex-shrink-0" style={{ lineHeight: '1.25rem' }}>•</span>
                <span className="text-sm leading-relaxed">{item.content}</span>
              </div>
            )
          
          case 'numbered':
            return (
              <div key={index} className="flex items-start space-x-2 space-x-reverse mr-4">
                <span className="text-gray-500 mt-1 text-sm font-medium">{index + 1}.</span>
                <span className="text-sm">{item.content}</span>
              </div>
            )
          
          case 'bold':
            // Parse bold text (**text**)
            const boldText = item.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            return (
              <div 
                key={index} 
                className="text-sm font-semibold"
                dangerouslySetInnerHTML={{ __html: boldText }}
              />
            )
          
          case 'code-start':
            return (
              <div key={index} className="bg-gray-100 p-2 rounded text-xs font-mono text-gray-800">
                <code>{item.content.replace(/```/g, '')}</code>
              </div>
            )
          
          case 'empty':
            return <div key={index} className="h-2" />
          
          case 'text':
          default:
            return (
              <div key={index} className="text-sm leading-relaxed">
                {item.content}
              </div>
            )
        }
        } catch (error) {
          console.error('Content rendering error:', error);
          return (
            <div key={index} className="p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
              Content rendering failed
            </div>
          );
        }
      })}
      {chart && (() => {
        try {
          return renderChart(chart, chartType);
        } catch (error) {
          console.error('Chart rendering error:', error);
          return (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl">
              <p className="text-red-600 text-sm">Chart rendering failed. Please try again.</p>
            </div>
          );
        }
      })()}
    </div>
  )
}

const LangChainChat = ({ currentFeature = 'dashboard', sidebarWidth = 320, sessionId = 'default' }) => {
  console.log('🚀 COMPONENT DEBUG: LangChainChat component initialized')
  console.log('🚀 COMPONENT DEBUG: currentFeature:', currentFeature)
  console.log('🚀 COMPONENT DEBUG: sessionId:', sessionId)
  console.log('🚀 COMPONENT DEBUG: Component render timestamp:', new Date().toISOString())
  
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingText, setLoadingText] = useState('')
  const [loadingStep, setLoadingStep] = useState(0)
  const [semanticMode, setSemanticMode] = useState(true) // Set Semantic Layer as default
  const [semanticQueries, setSemanticQueries] = useState([])
  const [ontology, setOntology] = useState(null)
  const [aiAssistantMode, setAiAssistantMode] = useState(false)
  const [availableFeatures, setAvailableFeatures] = useState([])
  const [featureInfo, setFeatureInfo] = useState(null)
  const [sampleQueries, setSampleQueries] = useState([])
  // sessionId is now passed as a prop from Dashboard
  const [activeTab, setActiveTab] = useState('data') // 'data' or 'chat'
  const messagesEndRef = useRef(null)

  // Load AI Assistant data
  useEffect(() => {
    console.log('🔄 EFFECT DEBUG: useEffect for loading data triggered')
    loadAIAssistantData()
    loadSemanticData()
  }, [])

  // Load feature-specific data when currentFeature changes
  useEffect(() => {
    if (aiAssistantMode && currentFeature) {
      const featureName = getFeatureName(currentFeature)
      loadFeatureData(featureName)
    }
  }, [currentFeature, aiAssistantMode])

  const loadAIAssistantData = async () => {
    try {
      console.log('🔄 DEBUG: Loading AI Assistant data...')
      const [featuresResponse, healthResponse] = await Promise.all([
        axios.get('http://127.0.0.1:8000/api/ai/features'),
        axios.get('http://127.0.0.1:8000/api/ai/health')
      ])
      
      setAvailableFeatures(featuresResponse.data)
      console.log('✅ AI Assistant: Features loaded:', featuresResponse.data)
      console.log('✅ AI Assistant: Health status:', healthResponse.data)
        } catch (error) {
      console.error('❌ AI Assistant: Failed to load features:', error)
    }
  }

  const loadFeatureData = async (feature) => {
    try {
      const [infoResponse, queriesResponse] = await Promise.all([
        axios.get(`http://127.0.0.1:8000/api/ai/features/${feature}`),
        axios.get(`http://127.0.0.1:8000/api/ai/features/${feature}/sample-queries`)
      ])
      
      setFeatureInfo(infoResponse.data)
      setSampleQueries(queriesResponse.data)
      console.log(`✅ AI Assistant: ${feature} data loaded`)
    } catch (error) {
      console.error(`❌ AI Assistant: Failed to load ${feature} data:`, error)
    }
  }

  const loadSemanticData = async () => {
    try {
      console.log('🔄 DEBUG: Loading Semantic Layer data...')
      const [queriesResponse, ontologyResponse] = await Promise.all([
        axios.get('http://127.0.0.1:8000/semantic/sample-queries'),
        axios.get('http://127.0.0.1:8000/semantic/ontology')
      ])
      
      setSemanticQueries(queriesResponse.data)
      setOntology(ontologyResponse.data)
      console.log('✅ Semantic Layer: Data loaded successfully')
      console.log('✅ Semantic Layer: Sample queries:', queriesResponse.data)
      console.log('✅ Semantic Layer: Ontology entities:', Object.keys(ontologyResponse.data?.entities || {}))
    } catch (error) {
      console.error('❌ Semantic Layer: Failed to load data:', error)
    }
  }

  // Format text with bullet points, numbered lists, and better readability
  const formatMessageContent = (content) => {
    if (!content) return content
    
    // Split content into lines
    const lines = content.split('\n')
    const formattedLines = []
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      
      if (!line) {
        formattedLines.push({ type: 'empty', content: '' })
        continue
      }
      
      // Check for headers (lines starting with #)
      if (line.startsWith('#')) {
        const level = line.match(/^#+/)[0].length
        const text = line.replace(/^#+\s*/, '')
        formattedLines.push({ type: 'header', level, content: text })
        continue
      }
      
      // Check for bullet points (-, *, •)
      if (line.match(/^[-*•]\s+/)) {
        const text = line.replace(/^[-*•]\s+/, '')
        formattedLines.push({ type: 'bullet', content: text })
        continue
      }
      
      // Check for numbered lists (1., 2., etc.)
      if (line.match(/^\d+\.\s+/)) {
        const text = line.replace(/^\d+\.\s+/, '')
        formattedLines.push({ type: 'numbered', content: text })
        continue
      }
      
      // Check for bold text (**text**)
      if (line.includes('**')) {
        formattedLines.push({ type: 'bold', content: line })
        continue
      }
      
      // Check for code blocks (```code```)
      if (line.startsWith('```')) {
        formattedLines.push({ type: 'code-start', content: line })
        continue
      }
      
      // Regular text
      formattedLines.push({ type: 'text', content: line })
    }
    
    return formattedLines
  }

  // Simple message addition - no streaming
  const addBotMessage = (content, chart = null, chartType = null) => {
    console.log('🤖 DEBUG: Adding bot message with content:', content)
    console.log('🤖 DEBUG: Content type:', typeof content)
    console.log('🤖 DEBUG: Content length:', content?.length || 0)
    console.log('🤖 DEBUG: Content preview:', content?.substring(0, 100) + '...')
    console.log('🤖 DEBUG: Chart data:', chart)
    console.log('🤖 DEBUG: Chart type:', chartType)
    
    const formattedContent = formatMessageContent(content)
    
        const botMessage = {
      id: Date.now(),
          type: 'bot',
      content: content, // Keep original content
      formattedContent: formattedContent, // Add formatted content
      chart: chart, // Add chart data
      chartType: chartType, // Add chart type
          timestamp: new Date().toLocaleTimeString()
        }
        
    console.log('🤖 DEBUG: Bot message object:', botMessage)
    setMessages(prev => {
      const newMessages = [...prev, botMessage]
      console.log('🤖 DEBUG: Messages after adding bot:', newMessages.length)
      console.log('🤖 DEBUG: Last message:', newMessages[newMessages.length - 1])
      return newMessages
    })
  }

  // Streaming loading text with actual backend processing steps
  const streamingLoadingEffect = () => {
    const step1 = "🔍 تشخیص زبان و ترجمه سوال..."
    const step2 = "🎯 شناسایی نوع درخواست (داده، گفتگو، یا ترکیبی)..."
    const step3 = "📊 اجرای کوئری SQL و دریافت داده‌های واقعی..."
    const step4 = "🤖 تولید پاسخ هوشمند بر اساس داده‌های سنسور..."
    const step5 = "🔄 ترجمه پاسخ به فارسی و آماده‌سازی نهایی..."
    
    let currentStep = 0
    let currentText = ""
    let index = 0
    
    setLoadingStep(0)
    setLoadingText("")
    
    const processStep = (text) => {
      return new Promise((resolve) => {
        const timer = setInterval(() => {
          if (index < text.length) {
            currentText += text[index]
            setLoadingText(currentText)
            index++
          } else {
            clearInterval(timer)
            resolve()
          }
        }, 10) // Maximum speed for loading
      })
    }
    
    const runSteps = async () => {
      const steps = [step1, step2, step3, step4, step5]
      
      for (let i = 0; i < steps.length; i++) {
        setLoadingStep(i + 1)
      currentText = ""
      index = 0
        await processStep(steps[i])
        
        // Wait between steps (shorter for better UX)
        await new Promise(resolve => setTimeout(resolve, 600))
      }
    }
    
    runSteps()
  }

  const sendMessage = async () => {
    console.log('🚀 DEBUG: sendMessage called with input:', inputMessage)
    console.log('🚀 DEBUG: Current feature:', currentFeature)
    console.log('🚀 DEBUG: Session ID:', sessionId)
    console.log('🚀 DEBUG: Active tab:', activeTab)
    
    if (!inputMessage.trim() || isLoading) {
      console.log('⚠️ DEBUG: Message empty or loading, returning')
      return
    }

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    }

    console.log('📤 DEBUG: Adding user message:', userMessage)
    setMessages(prev => {
      const newMessages = [...prev, userMessage]
      console.log('📤 DEBUG: Messages after adding user:', newMessages.length)
      return newMessages
    })
    setInputMessage('')
    setIsLoading(true)
    
    // Start loading effect based on active tab
    if (activeTab === 'data') {
      // Data Query mode - use streaming loading effect with backend steps
    streamingLoadingEffect()
    } else {
      // Chat mode - simple loading without backend steps
      setLoadingText('💬 در حال پاسخ...')
      setLoadingStep(0)
    }

    try {
      console.log('🌐 DEBUG: Sending request with payload:', { 
        feature: currentFeature, 
        query: inputMessage,
        session_id: sessionId,
        active_tab: activeTab
      })
      console.log('🌐 DEBUG: Session ID being sent to API:', sessionId)
      
      let response
      let responseText = ''
      
      if (activeTab === 'data') {
        console.log('📊 DEBUG: Using DATA QUERY mode (semantic layer)')
        
        // Use streaming endpoint for real-time responses
        const response = await fetch('http://127.0.0.1:8000/ask/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
          query: inputMessage,
          session_id: sessionId,
          feature_context: currentFeature
        })
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let finalResult = null
        let streamingResponse = '' // Accumulate streaming tokens

        try {
          while (true) {
            const { done, value } = await reader.read()
            
            if (done) {
              console.log('🧠 DEBUG: Streaming completed')
              break
            }

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || '' // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6) // Remove 'data: ' prefix
                
                if (data === '[DONE]') {
                  console.log('🧠 DEBUG: Stream finished')
                  break
                }

                try {
                  const parsed = JSON.parse(data)
                  console.log('🧠 DEBUG: Received streaming data:', parsed)

                  if (parsed.step && parsed.message) {
                    // Update loading message with real backend progress
                    setLoadingText(parsed.message)
                    setLoadingStep(parsed.step)
                  }

                  // Handle token streaming
                  if (parsed.step === 4 && parsed.token) {
                    streamingResponse += parsed.token
                    // Update the loading text with the streaming response
                    setLoadingText(`🤖 تولید پاسخ هوشمند... ${streamingResponse}`)
                    console.log('🧠 DEBUG: Received token:', parsed.token)
                    console.log('🧠 DEBUG: Accumulated response:', streamingResponse)
                  }

                  if (parsed.step === 'complete' && parsed.result) {
                    finalResult = parsed.result
                    console.log('🧠 DEBUG: Final result received:', finalResult)
                  }

                  if (parsed.error) {
                    console.log('🧠 DEBUG: Error in stream:', parsed.error)
                    responseText = `❌ خطا: ${parsed.error}`
                  }
                } catch (e) {
                  console.log('🧠 DEBUG: Failed to parse streaming data:', data)
                }
              }
            }
          }
        } finally {
          reader.releaseLock()
        }

        if (finalResult) {
          console.log('🧠 DEBUG: Processing final result:', finalResult)
          console.log('🧠 DEBUG: Response field:', finalResult.response)
          console.log('🧠 DEBUG: Success field:', finalResult.success)
          console.log('🧠 DEBUG: Detected language:', finalResult.detected_language)
          console.log('🧠 DEBUG: Detected intent:', finalResult.detected_intent)
          console.log('🧠 DEBUG: Data points:', finalResult.data?.length || 0)
          console.log('🧠 DEBUG: SQL generated:', finalResult.sql ? 'Yes' : 'No')
          console.log('🧠 DEBUG: Chart data:', finalResult.chart)
          console.log('🧠 DEBUG: Chart type:', finalResult.chart_type)
        
        // Check if the response indicates an error
          if (!finalResult.success && finalResult.error) {
            responseText = `❌ خطا: ${finalResult.error}`
            console.log('🧠 DEBUG: Error response detected:', finalResult.error)
            console.log('🧠 DEBUG: SQL that failed:', finalResult.sql)
            console.log('🧠 DEBUG: Validation details:', finalResult.validation)
          } else if (streamingResponse) {
            // Use the streaming response if available
            responseText = streamingResponse
            console.log('🧠 DEBUG: Using streaming response:', responseText.substring(0, 100) + '...')
          } else if (finalResult.response) {
            responseText = finalResult.response
          console.log('🧠 DEBUG: Using response field:', responseText.substring(0, 100) + '...')
          } else if (finalResult.summary) {
            responseText = finalResult.summary
          console.log('🧠 DEBUG: Using summary field:', responseText.substring(0, 100) + '...')
          } else if (finalResult.output) {
            responseText = finalResult.output
          console.log('🧠 DEBUG: Using output field:', responseText.substring(0, 100) + '...')
        } else {
          responseText = 'No response generated'
          console.log('🧠 DEBUG: No response field found, using fallback')
        }
      } else {
          responseText = 'No response received from streaming endpoint'
        }
        
        // Extract chart data from final result
        const chartData = finalResult?.chart || null
        const chartType = finalResult?.chart_type || null
        
        // Add bot message with chart data for streaming
        addBotMessage(responseText, chartData, chartType)
        
      } else if (activeTab === 'chat') {
        console.log('💬 DEBUG: Using CHAT mode (pure AI conversation)')
        
        // Pure AI chat mode - use regular AI endpoint
        response = await axios.post('http://127.0.0.1:8000/ai/query', {
          query: inputMessage,
          feature_context: currentFeature
      })
      
        console.log('💬 DEBUG: Chat response:', response.data)
        if (typeof response.data.output === 'object') {
          responseText = JSON.stringify(response.data.output, null, 2)
        } else {
          responseText = response.data.output || response.data.answer || 'پاسخ دریافت نشد'
        }
      }
      
      console.log('✅ DEBUG: Response received successfully')
      console.log('✅ DEBUG: Response text length:', responseText.length)
      console.log('✅ DEBUG: Response text preview:', responseText.substring(0, 200) + '...')
      
      // Add bot message with chart data (only for chat mode, streaming mode already handled above)
      if (activeTab === 'chat') {
        const chartData = response?.data?.chart || null
        const chartType = response?.data?.chart_type || null
        addBotMessage(responseText, chartData, chartType)
      }
      
    } catch (error) {
      console.error('❌ DEBUG: Error sending message:', error)
      console.error('❌ DEBUG: Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        config: error.config
      })
      
      addBotMessage(`خطا در دریافت پاسخ: ${error.message || 'خطای نامشخص'}`, null, null)
    } finally {
      console.log('🏁 DEBUG: Setting loading to false')
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleQuickQuestion = (question) => {
    setInputMessage(question)
    // Auto-send the question
    setTimeout(() => {
      sendMessage()
    }, 100)
  }

  const quickQuestions = [
    "میانگین دما چقدر است؟",
    "روند رطوبت چگونه است؟",
    "بالاترین فشار ثبت شده چقدر است؟",
    "آمار کلی سنسورها را نشان دهید"
  ]

  const semanticQuickQuestions = [
    "When was the last irrigation?",
    "What is the current humidity?",
    "What pests have been detected today?",
    "Show me irrigation events from last week"
  ]




  // Map frontend tab names to AI Assistant feature names
  const getFeatureName = (currentFeature) => {
    const featureMap = {
      'irrigation': 'irrigation',
      'environment': 'environment', 
      'pest-detection': 'pest',
      'dashboard': 'dashboard',
      'chat': 'dashboard',
      'semantic': 'dashboard'
    }
    return featureMap[currentFeature] || 'dashboard'
  }

  const getModeTitle = () => {
    return 'Smart AI Assistant' // Updated to reflect intent routing
  }

  const getPlaceholder = () => {
    if (activeTab === 'data') {
      return "سوال خود را بنویسید... (داده‌های سنسور، آبیاری، آفات) - Data Query Mode"
    } else {
      return "سوال خود را بنویسید... (گفتگو، راهنمایی، توضیحات) - Chat Mode"
    }
  }

  const getQuickQuestions = () => {
    return [
      "امروز میشه سم پاشی کرد یا نه؟",
      "خاک چطوره؟ باید کود بدیم؟", 
      "وضعیت آفات و بیماری‌ها چطوره؟",
      "Should I water the plants today?",
      "What is the current soil moisture?",
      "Can we spray pesticides now?"
    ]
  }

  return (
    <div className="flex flex-col h-full" style={{ width: `${sidebarWidth}px` }}>
      
      
      {/* Mode Toggle - Hidden since we only use Semantic Layer */}
      {/* <div className="px-4 pb-2 pt-2">
        <div className="flex justify-center mb-2">
          <div className="bg-gray-100 rounded-lg p-1 flex">
            <button
              onClick={() => {
                setAiAssistantMode(false)
                setSemanticMode(false)
              }}
              className={`px-3 py-1 text-xs rounded-md transition-colors duration-200 ${
                !aiAssistantMode && !semanticMode
                  ? 'bg-white text-gray-800 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              AI Chat
            </button>
            <button
              onClick={() => {
                setAiAssistantMode(true)
                setSemanticMode(false)
              }}
              className={`px-3 py-1 text-xs rounded-md transition-colors duration-200 ${
                aiAssistantMode
                  ? 'bg-white text-gray-800 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              AI Assistant
            </button>
            <button
              onClick={() => {
                setAiAssistantMode(false)
                setSemanticMode(true)
              }}
              className={`px-3 py-1 text-xs rounded-md transition-colors duration-200 ${
                semanticMode
                  ? 'bg-white text-gray-800 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Semantic Layer
            </button>
          </div>
        </div>
        
        {/* Feature Info for AI Assistant - commented out since we only use Semantic Layer */}
        {/* {aiAssistantMode && featureInfo && (
          <div className="text-center mb-2">
            <h3 className="text-sm font-medium text-gray-700">{featureInfo.name}</h3>
            <p className="text-xs text-gray-500">{featureInfo.description}</p>
          </div>
        )} */}

      {/* Messages Container */}
      <div className={`flex-1 space-y-4 overflow-y-auto ${messages.length > 0 ? 'px-4 py-4' : 'px-4'}`} style={{ width: `${sidebarWidth}px` }}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-start' : 'justify-end'}`}
          >
            <div
              className={`${message.type === 'user' ? 'max-w-xs' : 'max-w-lg'} px-3 py-2 rounded-2xl text-sm ${
                message.type === 'user'
                  ? 'bg-transparent text-gray-800 border border-gray-200 rounded-bl-lg'
                  : 'bg-transparent text-gray-800 rounded-br-lg'
              }`}
              style={{ maxWidth: `${Math.max(200, sidebarWidth * 0.95)}px` }}
            >
              <div className="font-medium leading-relaxed" dir="rtl">
                {message.type === 'bot' && message.formattedContent ? (
                  <FormattedMessage 
                    content={message.formattedContent} 
                    chart={message.chart}
                    chartType={message.chartType}
                    sidebarWidth={sidebarWidth}
                  />
                ) : (
                  message.content
                )}
              </div>
              <div className={`text-xs mt-1 ${
                message.type === 'user' ? 'text-gray-500' : 'text-gray-500'
              }`}>
                {message.timestamp}
              </div>
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />

        {/* Loading State with Streaming Text */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-xs px-3 py-2 bg-transparent text-gray-800 border border-gray-200 rounded-2xl rounded-bl-lg">
              <div className="flex items-center space-x-2 space-x-reverse">
                <div className="animate-spin rounded-full h-3 w-3 border-2 border-gray-300 border-t-blue-500"></div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-600" dir="rtl">
                    {loadingText}
                    <span className="animate-pulse">|</span>
                  </div>
                  {loadingStep > 0 && activeTab === 'data' && (
                    <div className="mt-1">
                      <div className="text-xs text-gray-500 mb-1">
                        مرحله {loadingStep} از 5
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1">
                        <div 
                          className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                          style={{ width: `${(loadingStep / 5) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                  {activeTab === 'chat' && (
                    <div className="mt-1">
                      <div className="w-full bg-gray-200 rounded-full h-1">
                        <div className="bg-green-500 h-1 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />

        {/* Welcome State - Centered Input */}
        {messages.length === 0 && (
          <div className="flex-1 flex items-center justify-center px-4" style={{ width: `${sidebarWidth}px` }}>
            <div className="w-full" style={{ maxWidth: `${Math.max(280, sidebarWidth - 40)}px` }}>
              <div className="text-center mb-4">
                <h2 className="text-lg font-bold text-gray-800 mb-2">
                  {activeTab === 'data' ? '📊 Data Query Assistant' : '💬 Chat Assistant'}
                </h2>
                <p className="text-sm text-gray-600">
                  {activeTab === 'data' 
                    ? 'Ask about sensor data, irrigation, pests, environment - gets real database information'
                    : 'General conversation about agriculture, farming tips, explanations - pure AI chat'
                  }
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Session: {sessionId.substring(0, 20)}...
                </p>
              </div>
              <div className="relative">
                {/* Main Input Container */}
                <div className="relative bg-white border border-gray-300 rounded-xl shadow-sm focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 transition-all duration-200" style={{ width: `${Math.max(280, sidebarWidth - 40)}px` }}>
                  {/* Placeholder at top-right */}
                  <div className="absolute top-3 right-4 text-xs text-gray-400 pointer-events-none">
                    Just ask something...
                  </div>
                  
                  {/* Input Field */}
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                    placeholder=""
                    className="w-full px-4 py-8 pr-16 pl-4 bg-transparent border-0 rounded-xl focus:outline-none text-sm pt-10"
                  dir="rtl"
                  disabled={isLoading}
                />
                  
                  {/* Send Button (Absolute bottom) */}
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                    className="absolute bottom-2 right-2 w-8 h-8 bg-black text-white rounded-full hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
                >
                  {isLoading ? (
                      <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></div>
                  ) : (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  )}
                </button>
                  
                  {/* Tab Buttons (Bottom left) */}
                  <div className="absolute bottom-2 left-2 flex space-x-1">
                    <button
                      onClick={() => setActiveTab('data')}
                      className={`px-2 py-1 text-xs rounded-md transition-colors duration-200 ${
                        activeTab === 'data'
                          ? 'bg-gray-200 text-gray-800 font-medium' 
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      Agent
                    </button>
                    <button
                      onClick={() => setActiveTab('chat')}
                      className={`px-2 py-1 text-xs rounded-md transition-colors duration-200 ${
                        activeTab === 'chat'
                          ? 'bg-gray-200 text-gray-800 font-medium' 
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      Chat
                </button>
                  </div>
                </div>
                
                {/* Tab Description */}
                <div className="text-center mt-2">
                  <p className="text-xs text-gray-500">
                    {activeTab === 'data' 
                      ? '📊 Data Query - Gets real sensor data from database'
                      : '💬 Chat - General conversation about agriculture'
                    }
                  </p>
              </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Questions */}
      {messages.length === 0 && (
        <div className="px-4 pb-2">
          <p className="text-xs text-gray-600 mb-2 text-center">
            Sample Queries:
          </p>
          <div className="flex flex-wrap gap-1 justify-center">
            {getQuickQuestions().slice(0, 3).map((question, index) => (
              <button
                key={index}
                onClick={() => handleQuickQuestion(question)}
                className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-full transition-colors duration-200"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Fixed Bottom Input Area */}
      <div className="border-t border-gray-200 px-4 py-3 bg-gray-50" style={{ width: `${sidebarWidth}px` }}>
        <div className="relative">
          {/* Main Input Container */}
          <div className="relative bg-white border border-gray-300 rounded-xl shadow-sm focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 transition-all duration-200" style={{ width: `${Math.max(280, sidebarWidth - 40)}px` }}>
            {/* Placeholder at top-right */}
            <div className="absolute top-3 right-4 text-xs text-gray-400 pointer-events-none">
              Just ask something...
            </div>
            
            {/* Input Field */}
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
              placeholder=""
              className="w-full px-4 py-8 pr-16 pl-4 bg-transparent border-0 rounded-xl focus:outline-none text-sm pt-10"
                  dir="rtl"
                  disabled={isLoading}
                />
            
            {/* Send Button (Absolute bottom) */}
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
              className="absolute bottom-2 right-2 w-8 h-8 bg-black text-white rounded-full hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
                >
                  {isLoading ? (
                <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></div>
                  ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
                    </svg>
                  )}
                </button>
            
            {/* Tab Buttons (Bottom left) */}
            <div className="absolute bottom-2 left-2 flex space-x-1">
              <button
                onClick={() => setActiveTab('data')}
                className={`px-2 py-1 text-xs rounded-md transition-colors duration-200 ${
                  activeTab === 'data'
                    ? 'bg-gray-200 text-gray-800 font-medium' 
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                Agent
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`px-2 py-1 text-xs rounded-md transition-colors duration-200 ${
                  activeTab === 'chat'
                    ? 'bg-gray-200 text-gray-800 font-medium' 
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                Chat
                </button>
            </div>
          </div>
          
          {/* Tab Description */}
          <div className="text-center mt-2">
            <p className="text-xs text-gray-500">
              {activeTab === 'data' 
                ? '📊 Data Query - Gets real sensor data from database'
                : '💬 Chat - General conversation about agriculture'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LangChainChat