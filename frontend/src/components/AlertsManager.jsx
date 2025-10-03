import React, { useState, useEffect } from 'react';
import { AlertCircle, Trash2, Bell, BellOff, Clock, Activity, RefreshCw } from 'lucide-react';

const AlertsManager = ({ sessionId = "default" }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [triggeredAlerts, setTriggeredAlerts] = useState([]);
  const [lastAlertCheck, setLastAlertCheck] = useState(null);
  const [alertActions, setAlertActions] = useState({}); // Track actions taken for each alert

  console.log('AlertsManager initialized with sessionId:', sessionId);

  // Fetch alerts from API
  const fetchAlerts = async (showRefreshIndicator = false) => {
    try {
      if (showRefreshIndicator) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      
      console.log('Fetching alerts for session:', sessionId);
      const response = await fetch(`http://127.0.0.1:8000/api/alerts?session_id=${sessionId}`);
      console.log('Alerts API Response Status:', response.status);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch alerts: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Alerts API Response Data:', data);
      
      if (data.success) {
        console.log('Alerts received:', data.alerts);
        setAlerts(data.alerts || []);
      } else {
        console.error('API returned error:', data.error);
        setError(data.error || 'Failed to fetch alerts');
      }
    } catch (err) {
      setError(err.message);
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Manual refresh function
  const handleRefresh = () => {
    fetchAlerts(true);
  };

  // Check for triggered alerts
  const checkTriggeredAlerts = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/alerts/monitor?session_id=${sessionId}`);
      if (!response.ok) return;
      
      const data = await response.json();
      if (data.success && data.triggered_alerts && data.triggered_alerts.length > 0) {
        console.log('🚨 Alerts triggered:', data.triggered_alerts);
        setTriggeredAlerts(data.triggered_alerts);
        
        // Play alert sound
        playAlertSound();
        
        // Show browser notification
        showBrowserNotification(data.triggered_alerts);
      }
    } catch (err) {
      console.error('Error checking triggered alerts:', err);
    }
  };

  // Play industrial WAV-style alert sound
  const playAlertSound = () => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      
      // Create industrial WAV-style tone with proper industrial characteristics
      const createIndustrialTone = (frequency, startTime, duration, volume = 0.8, waveType = 'square') => {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        const filter = audioContext.createBiquadFilter();
        const compressor = audioContext.createDynamicsCompressor();
        
        oscillator.connect(filter);
        filter.connect(compressor);
        compressor.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(frequency, startTime);
        oscillator.type = waveType; // Square wave for industrial sound
        
        // Industrial EQ filter - sharp cutoff
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(2000, startTime); // Industrial cutoff
        filter.Q.setValueAtTime(2, startTime); // Sharp Q for industrial sound
        
        // Industrial compressor settings
        compressor.threshold.setValueAtTime(-20, startTime);
        compressor.knee.setValueAtTime(30, startTime);
        compressor.ratio.setValueAtTime(12, startTime);
        compressor.attack.setValueAtTime(0.003, startTime);
        compressor.release.setValueAtTime(0.25, startTime);
        
        // Industrial envelope - sharp attack, quick decay
        gainNode.gain.setValueAtTime(0, startTime);
        gainNode.gain.linearRampToValueAtTime(volume, startTime + 0.01); // Sharp attack
        gainNode.gain.linearRampToValueAtTime(volume * 0.8, startTime + duration * 0.3);
        gainNode.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
        
        oscillator.start(startTime);
        oscillator.stop(startTime + duration);
      };
      
      const now = audioContext.currentTime;
      
      // Industrial WAV-style alert with fire department siren pattern - FASTER & LONGER
      
      // 1. High industrial tone (1200Hz square wave) - Fire department high pattern
      createIndustrialTone(1200, now, 0.3, 0.95, 'square');
      
      // 2. Faster industrial pause
      const pause1 = now + 0.35;
      
      // 3. Low industrial tone (600Hz square wave) - Fire department low pattern
      createIndustrialTone(600, pause1, 0.3, 0.95, 'square');
      
      // 4. Faster industrial pause
      const pause2 = pause1 + 0.35;
      
      // 5. High industrial tone again (1200Hz square wave)
      createIndustrialTone(1200, pause2, 0.3, 0.95, 'square');
      
      // 6. Faster industrial pause
      const pause3 = pause2 + 0.35;
      
      // 7. Low industrial tone again (600Hz square wave)
      createIndustrialTone(600, pause3, 0.3, 0.95, 'square');
      
      // 8. Faster industrial pause
      const pause4 = pause3 + 0.35;
      
      // 9. High industrial tone again (1200Hz square wave) - EXTRA CYCLE
      createIndustrialTone(1200, pause4, 0.3, 0.95, 'square');
      
      // 10. Faster industrial pause
      const pause5 = pause4 + 0.35;
      
      // 11. Low industrial tone again (600Hz square wave) - EXTRA CYCLE
      createIndustrialTone(600, pause5, 0.3, 0.95, 'square');
      
    } catch (err) {
      console.log('Audio not supported:', err);
    }
  };

  // Handle alert action (Act or Pass)
  const handleAlertAction = (alertId, action) => {
    setAlertActions(prev => ({
      ...prev,
      [alertId]: {
        action,
        timestamp: new Date().toISOString()
      }
    }));
    
    // If action is "pass", remove from triggered alerts after a delay
    if (action === 'pass') {
      setTimeout(() => {
        setTriggeredAlerts(prev => prev.filter(alert => alert.alert_id !== alertId));
      }, 2000);
    }
  };

  // Get recommended action for alert in Persian
  const getRecommendedAction = (alert) => {
    const sensorType = alert.sensor_type;
    const condition = alert.condition;
    const threshold = alert.threshold;
    const currentValue = alert.current_value;
    
    // Persian sensor names
    const persianSensorNames = {
      'temperature': 'دما',
      'humidity': 'رطوبت',
      'soil_moisture': 'رطوبت خاک',
      'pressure': 'فشار',
      'light': 'نور',
      'motion': 'حرکت',
      'co2_level': 'سطح CO2',
      'ph': 'پی اچ'
    };
    
    // Persian condition names
    const persianConditions = {
      'above': 'بیشتر از',
      'below': 'کمتر از',
      'equals': 'برابر با'
    };
    
    const persianSensorName = persianSensorNames[sensorType] || sensorType;
    const persianCondition = persianConditions[condition] || condition;
    
    // Generate recommended actions based on sensor type and condition
          if (sensorType === 'temperature') {
            if (condition === 'above' && currentValue > threshold) {
              return {
                title: "هشدار دمای بالا",
                description: `${persianSensorName} ${currentValue}°C است (${persianCondition} ${threshold}°C آستانه)`,
                recommendedActions: [
                  "سیستم‌های خنک‌کننده حتما بررسی شود",
                  "تهویه باید افزایش پیدا کند",
                  "وضعیت تجهیزات باید نظارت شود"
                ]
              };
            } else if (condition === 'below' && currentValue < threshold) {
              return {
                title: "هشدار دمای پایین", 
                description: `${persianSensorName} ${currentValue}°C است (${persianCondition} ${threshold}°C آستانه)`,
                recommendedActions: [
                  "سیستم‌های گرمایشی سریع بررسی شود",
                  "عایق‌بندی باید تأیید شود",
                  "شرایط یخ‌زدگی باید نظارت شود"
                ]
              };
            }
          } else if (sensorType === 'humidity') {
            if (condition === 'above' && currentValue > threshold) {
              return {
                title: "هشدار رطوبت بالا",
                description: `${persianSensorName} ${currentValue}% است (${persianCondition} ${threshold}% آستانه)`,
                recommendedActions: [
                  "تهویه باید افزایش پیدا کند",
                  "منابع رطوبت باید بررسی شود",
                  "رشد کپک باید نظارت شود"
                ]
              };
            } else if (condition === 'below' && currentValue < threshold) {
              return {
                title: "هشدار رطوبت پایین",
                description: `${persianSensorName} ${currentValue}% است (${persianCondition} ${threshold}% آستانه)`,
                recommendedActions: [
                  "منابع رطوبت حتما اضافه شود",
                  "سیستم‌های رطوبت‌ساز باید بررسی شود",
                  "سلامت گیاهان باید نظارت شود"
                ]
              };
            }
          } else if (sensorType === 'soil_moisture') {
            if (condition === 'below' && currentValue < threshold) {
              return {
                title: "هشدار رطوبت خاک پایین",
                description: `${persianSensorName} ${currentValue}% است (${persianCondition} ${threshold}% آستانه)`,
                recommendedActions: [
                  "گیاهان حتما آبیاری شود",
                  "سیستم‌های آبیاری باید بررسی شود",
                  "پژمردگی گیاهان باید نظارت شود"
                ]
              };
            } else if (condition === 'above' && currentValue > threshold) {
              return {
                title: "هشدار رطوبت خاک بالا",
                description: `${persianSensorName} ${currentValue}% است (${persianCondition} ${threshold}% آستانه)`,
                recommendedActions: [
                  "زهکشی سریعا بررسی شود",
                  "آبیاری باید کاهش پیدا کند",
                  "پوسیدگی ریشه باید نظارت شود"
                ]
              };
            }
          }
    
    // Default recommendation in Persian
    return {
      title: `هشدار ${persianSensorName}`,
      description: `${persianSensorName} ${persianCondition} ${threshold} است (فعلی: ${currentValue})`,
      recommendedActions: [
        "خوانش سنسورها باید بررسی شود",
        "وضعیت سیستم باید تأیید شود",
        "شرایط باید نظارت شود"
      ]
    };
  };

  // Show browser notification
  const showBrowserNotification = (alerts) => {
    if (Notification.permission === 'granted') {
      const alert = alerts[0]; // Show first alert
      new Notification(`🚨 Alert: ${alert.alert_name}`, {
        body: `${alert.sensor_type} is ${alert.condition} ${alert.threshold} (current: ${alert.current_value})`,
        icon: '/favicon.ico',
        tag: 'alert-notification'
      });
    }
  };

  // Request notification permission
  const requestNotificationPermission = () => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  };


  // Delete alert
  const deleteAlert = async (alertId) => {
    try {
      setDeletingId(alertId);
      const response = await fetch(`http://127.0.0.1:8000/api/alerts/${alertId}?session_id=${sessionId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete alert');
      }
      
      const data = await response.json();
      if (data.success) {
        fetchAlerts(); // Refresh the list
      } else {
        setError(data.error || 'Failed to delete alert');
      }
    } catch (err) {
      setError(err.message);
      console.error('Error deleting alert:', err);
    } finally {
      setDeletingId(null);
    }
  };

  // Load alerts on component mount
  useEffect(() => {
    fetchAlerts();
  }, [sessionId]);

  // Auto-refresh alerts every 10 seconds to catch new alerts created via AI
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAlerts();
    }, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [sessionId]);

  // Monitor for triggered alerts every 30 seconds
  useEffect(() => {
    // Request notification permission on component mount
    requestNotificationPermission();
    
    const interval = setInterval(() => {
      checkTriggeredAlerts();
    }, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [sessionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading alerts...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Clean Header with Controls Only - TOP */}
      <div className="flex items-center justify-end space-x-4 mb-6">
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
          title="Refresh alerts"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
        {triggeredAlerts.length > 0 && (
          <button
            onClick={() => setTriggeredAlerts([])}
            className="flex items-center px-3 py-2 text-sm font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
            title="Clear triggered alerts"
          >
            <AlertCircle className="h-4 w-4 mr-2" />
            Clear Alerts
          </button>
        )}
        <div className="text-sm text-gray-500">
          Session: {sessionId.substring(0, 20)}...
        </div>
      </div>

      {/* Priority Alert Actions */}
      {triggeredAlerts.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {triggeredAlerts.map((alert, index) => {
              const recommendation = getRecommendedAction(alert);
              const actionTaken = alertActions[alert.alert_id];
              
              return (
                <div key={index} className="bg-white border border-gray-200 rounded-xl p-4 shadow-lg hover:shadow-xl transition-all duration-300 border-l-4 border-l-red-500">
                  <div className="mb-3">
                    <div className="font-bold text-red-800 text-lg mb-2">{recommendation.title}</div>
                    <div className="text-sm text-red-600 mb-2 font-medium">{recommendation.description}</div>
                    <div className="text-xs text-red-500 font-medium flex items-center">
                      <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                      فعال شده: {new Date(alert.timestamp).toLocaleTimeString('fa-IR')}
                    </div>
                  </div>
                  
                    <div className="mb-3">
                      <div className="text-base font-bold text-gray-800 mb-2">اقدامات پیشنهادی:</div>
                      <div className="space-y-2">
                        {recommendation.recommendedActions.slice(0, 2).map((action, actionIndex) => (
                          <div key={actionIndex} className="flex items-center justify-between">
                            <span className="text-sm text-gray-700 font-medium">{action}</span>
                            {actionTaken ? (
                              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                                actionTaken.action === 'act' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {actionTaken.action === 'act' ? '✅' : '⏸️'}
                              </div>
                            ) : (
                              <div className="flex space-x-1">
                                <button
                                  onClick={() => handleAlertAction(alert.alert_id, 'act')}
                                  className="flex items-center px-2 py-1 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700 transition-colors"
                                  title="Act on this recommendation"
                                >
                                  Act
                                </button>
                                <button
                                  onClick={() => handleAlertAction(alert.alert_id, 'pass')}
                                  className="flex items-center px-2 py-1 bg-yellow-600 text-white rounded text-xs font-medium hover:bg-yellow-700 transition-colors"
                                  title="Pass on this recommendation"
                                >
                                  Pass
                                </button>
                              </div>
                            )}
                          </div>
                        ))}
                        {recommendation.recommendedActions.length > 2 && (
                          <div className="text-gray-500 text-sm">و {recommendation.recommendedActions.length - 2} مورد دیگر...</div>
                        )}
                      </div>
                    </div>
                  
                  {actionTaken && actionTaken.action === 'act' && (
                    <div className="bg-green-50 border border-green-200 rounded p-2 mt-2">
                      <div className="text-xs text-green-800 font-bold">اقدام مورد نیاز</div>
                    </div>
                  )}
                  
                  {actionTaken && actionTaken.action === 'pass' && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded p-2 mt-2">
                      <div className="text-xs text-yellow-800 font-bold">تأیید شد</div>
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      )}

      {/* Success Message */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <Bell className="h-5 w-5 text-green-500 mr-2" />
            <span className="text-green-700">{successMessage}</span>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Alert Creation Info - Only show when no triggered alerts */}
      {triggeredAlerts.length === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center mb-3">
            <Bell className="h-5 w-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-blue-800">Create Alerts with AI</h3>
          </div>
          <p className="text-blue-700 mb-3">
            To create new alerts, use the AI Assistant on the right sidebar. Simply ask the AI to create alerts for you!
          </p>
          <div className="text-sm text-blue-600">
            <p className="font-medium mb-2">Example commands:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>&quot;Alert me when temperature &gt; 25°C&quot;</li>
              <li>&quot;Notify me if humidity &lt; 40%&quot;</li>
              <li>&quot;Warn me when soil moisture &gt; 60%&quot;</li>
              <li>&quot;Alert me when CO2 level &gt; 1000&quot;</li>
            </ul>
          </div>
        </div>
      )}

      {/* Alerts List */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            Your Alerts ({alerts.length})
          </h2>
        </div>
        
        {alerts.length === 0 ? (
          <div className="p-8 text-center">
            <BellOff className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No alerts yet</h3>
            <p className="text-gray-500">Create your first alert to get started with smart monitoring.</p>
            <div className="mt-4 text-sm text-gray-400">
              Session ID: {sessionId}
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {alerts.map((alert) => (
              <div key={alert.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <Bell className="h-5 w-5 text-blue-600 mr-2" />
                      <h3 className="text-lg font-medium text-gray-900">{alert.alert_name}</h3>
                      <span className={`ml-3 px-2 py-1 text-xs font-medium rounded-full ${
                        alert.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {alert.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Sensor:</span> {alert.sensor_type.replace('_', ' ').toUpperCase()}
                      </div>
                      <div>
                        <span className="font-medium">Condition:</span> {alert.condition_type} {alert.threshold_value}
                      </div>
                      <div>
                        <span className="font-medium">Created:</span> {new Date(alert.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => deleteAlert(alert.id)}
                      disabled={deletingId === alert.id}
                      className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
                      title="Delete alert"
                    >
                      {deletingId === alert.id ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsManager;