"""
Alert Monitor Service for Smart Agriculture Platform
Monitors sensor data against user alerts and triggers notifications
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from app.services.alert_manager import AlertManager

logger = logging.getLogger(__name__)

class AlertMonitor:
    """Monitors sensor data against user alerts"""
    
    def __init__(self):
        self.alert_manager = AlertManager()
        self.last_checked = {}
    
    def monitor_sensor_data(self, sensor_data: List[Dict[str, Any]], user_id: str = "default") -> List[Dict[str, Any]]:
        """Monitor sensor data against all active alerts"""
        try:
            logger.info(f"🔍 Monitoring {len(sensor_data)} sensor data points for alerts")
            
            # Check alerts against current data
            triggered_alerts = self.alert_manager.check_alerts_against_data(sensor_data, user_id)
            
            # Filter out recently triggered alerts to avoid spam
            new_alerts = self._filter_new_alerts(triggered_alerts, user_id)
            
            if new_alerts:
                logger.info(f"🚨 {len(new_alerts)} new alerts triggered")
                for alert in new_alerts:
                    logger.info(f"   - {alert['alert_name']}: {alert['current_value']} {alert['condition']} {alert['threshold']}")
            
            return new_alerts
            
        except Exception as e:
            logger.error(f"❌ Error monitoring sensor data: {e}")
            return []
    
    def _filter_new_alerts(self, triggered_alerts: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """Filter out recently triggered alerts to avoid spam"""
        try:
            new_alerts = []
            current_time = datetime.now()
            
            for alert in triggered_alerts:
                alert_key = f"{user_id}_{alert['alert_id']}"
                last_triggered = self.last_checked.get(alert_key)
                
                # Only trigger if not triggered in the last 5 minutes
                if not last_triggered or (current_time - last_triggered).seconds > 300:
                    new_alerts.append(alert)
                    self.last_checked[alert_key] = current_time
            
            return new_alerts
            
        except Exception as e:
            logger.error(f"❌ Error filtering new alerts: {e}")
            return triggered_alerts
    
    def get_alert_summary(self, user_id: str = "default") -> Dict[str, Any]:
        """Get summary of user's alerts"""
        try:
            alerts = self.alert_manager.get_user_alerts(user_id)
            
            active_count = sum(1 for alert in alerts if alert["is_active"])
            inactive_count = len(alerts) - active_count
            
            return {
                "total_alerts": len(alerts),
                "active_alerts": active_count,
                "inactive_alerts": inactive_count,
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting alert summary: {e}")
            return {
                "total_alerts": 0,
                "active_alerts": 0,
                "inactive_alerts": 0,
                "alerts": []
            }
