"""
Automated Action Executor for Enhanced Alerting System
Handles execution of automated actions when alerts are triggered
"""
import logging
import smtplib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class ActionExecutor:
    """Executes automated actions for triggered alerts"""
    
    def __init__(self, db_path: str = "smart_dashboard.db"):
        self.db_path = db_path
        self._init_database()
        
        # Action types and their handlers
        self.action_handlers = {
            "email": self._execute_email_action,
            "sms": self._execute_sms_action,
            "notification": self._execute_notification_action,
            "auto": self._execute_auto_action,
            "log": self._execute_log_action
        }
    
    def _init_database(self):
        """Initialize action execution database tables"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create action_executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS action_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    action_parameters TEXT,
                    status TEXT DEFAULT 'pending',
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    result TEXT,
                    error_message TEXT,
                    FOREIGN KEY (alert_id) REFERENCES user_alerts (id)
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Action execution database initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing action execution database: {e}")
    
    def execute_alert_actions(self, triggered_alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute actions for triggered alerts"""
        execution_results = []
        
        for alert in triggered_alerts:
            try:
                alert_id = alert["alert_id"]
                action_type = alert.get("action_type")
                
                if not action_type:
                    logger.info(f"No action type specified for alert {alert_id}")
                    continue
                
                # Execute the action
                result = self._execute_action(alert_id, action_type, alert)
                
                execution_results.append({
                    "alert_id": alert_id,
                    "action_type": action_type,
                    "status": result["status"],
                    "result": result.get("result"),
                    "error": result.get("error")
                })
                
            except Exception as e:
                logger.error(f"❌ Error executing action for alert {alert_id}: {e}")
                execution_results.append({
                    "alert_id": alert_id,
                    "action_type": action_type,
                    "status": "failed",
                    "error": str(e)
                })
        
        return execution_results
    
    def _execute_action(self, alert_id: int, action_type: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific action type"""
        try:
            if action_type not in self.action_handlers:
                return {
                    "status": "failed",
                    "error": f"Unknown action type: {action_type}"
                }
            
            # Get action parameters
            action_params = self._get_action_parameters(alert_id, action_type)
            
            # Execute the action
            result = self.action_handlers[action_type](alert_data, action_params)
            
            # Log the execution
            self._log_action_execution(alert_id, action_type, action_params, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error executing {action_type} action: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _get_action_parameters(self, alert_id: int, action_type: str) -> Dict[str, Any]:
        """Get action parameters from database or defaults"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT action_parameters FROM user_alerts 
                WHERE id = ? AND action_type = ?
            """, (alert_id, action_type))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0]:
                return json.loads(row[0])
            else:
                return self._get_default_parameters(action_type)
                
        except Exception as e:
            logger.error(f"❌ Error getting action parameters: {e}")
            return self._get_default_parameters(action_type)
    
    def _get_default_parameters(self, action_type: str) -> Dict[str, Any]:
        """Get default parameters for action type"""
        defaults = {
            "email": {
                "recipient": "admin@farm.com",
                "subject_template": "Alert: {alert_name}",
                "body_template": "Alert triggered: {alert_name}\nSensor: {sensor_type}\nCurrent Value: {current_value}\nThreshold: {threshold}"
            },
            "sms": {
                "recipient": "+1234567890",
                "message_template": "Alert: {alert_name} - {sensor_type} is {current_value}"
            },
            "notification": {
                "title_template": "Alert: {alert_name}",
                "message_template": "{sensor_type} is {current_value} (threshold: {threshold})"
            },
            "auto": {
                "auto_response": "Automated response triggered",
                "auto_action": "log_and_notify"
            },
            "log": {
                "log_level": "WARNING",
                "log_message_template": "Alert triggered: {alert_name}"
            }
        }
        
        return defaults.get(action_type, {})
    
    def _execute_email_action(self, alert_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email action"""
        try:
            # For demo purposes, we'll just log the email
            # In production, you would use actual SMTP
            recipient = params.get("recipient", "admin@farm.com")
            subject = params.get("subject_template", "Alert: {alert_name}").format(**alert_data)
            body = params.get("body_template", "Alert triggered").format(**alert_data)
            
            logger.info(f"📧 EMAIL ACTION: To: {recipient}")
            logger.info(f"📧 Subject: {subject}")
            logger.info(f"📧 Body: {body}")
            
            return {
                "status": "success",
                "result": f"Email sent to {recipient}",
                "recipient": recipient,
                "subject": subject
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Email action failed: {str(e)}"
            }
    
    def _execute_sms_action(self, alert_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SMS action"""
        try:
            # For demo purposes, we'll just log the SMS
            # In production, you would use actual SMS service
            recipient = params.get("recipient", "+1234567890")
            message = params.get("message_template", "Alert triggered").format(**alert_data)
            
            logger.info(f"📱 SMS ACTION: To: {recipient}")
            logger.info(f"📱 Message: {message}")
            
            return {
                "status": "success",
                "result": f"SMS sent to {recipient}",
                "recipient": recipient,
                "message": message
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": f"SMS action failed: {str(e)}"
            }
    
    def _execute_notification_action(self, alert_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification action"""
        try:
            title = params.get("title_template", "Alert: {alert_name}").format(**alert_data)
            message = params.get("message_template", "Alert triggered").format(**alert_data)
            
            logger.info(f"🔔 NOTIFICATION ACTION: {title}")
            logger.info(f"🔔 Message: {message}")
            
            return {
                "status": "success",
                "result": "Notification sent",
                "title": title,
                "message": message
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Notification action failed: {str(e)}"
            }
    
    def _execute_auto_action(self, alert_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute automated action"""
        try:
            auto_response = params.get("auto_response", "Automated response triggered")
            auto_action = params.get("auto_action", "log_and_notify")
            
            logger.info(f"🤖 AUTO ACTION: {auto_response}")
            logger.info(f"🤖 Action Type: {auto_action}")
            
            # Execute the automated action
            if auto_action == "log_and_notify":
                # Log the alert and send notification
                self._execute_log_action(alert_data, {})
                self._execute_notification_action(alert_data, {})
            
            return {
                "status": "success",
                "result": auto_response,
                "action_type": auto_action
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Auto action failed: {str(e)}"
            }
    
    def _execute_log_action(self, alert_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute log action"""
        try:
            log_level = params.get("log_level", "WARNING")
            log_message = params.get("log_message_template", "Alert triggered: {alert_name}").format(**alert_data)
            
            logger.warning(f"📝 LOG ACTION [{log_level}]: {log_message}")
            
            return {
                "status": "success",
                "result": "Alert logged",
                "log_level": log_level,
                "log_message": log_message
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Log action failed: {str(e)}"
            }
    
    def _log_action_execution(self, alert_id: int, action_type: str, params: Dict[str, Any], result: Dict[str, Any]):
        """Log action execution to database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO action_executions (
                    alert_id, action_type, action_parameters, status, 
                    result, error_message, executed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_id,
                action_type,
                json.dumps(params),
                result["status"],
                result.get("result"),
                result.get("error"),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error logging action execution: {e}")
    
    def get_action_execution_history(self, alert_id: int = None) -> List[Dict[str, Any]]:
        """Get action execution history"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if alert_id:
                cursor.execute("""
                    SELECT * FROM action_executions 
                    WHERE alert_id = ? 
                    ORDER BY executed_at DESC
                """, (alert_id,))
            else:
                cursor.execute("""
                    SELECT * FROM action_executions 
                    ORDER BY executed_at DESC
                """)
            
            executions = []
            for row in cursor.fetchall():
                executions.append({
                    "id": row[0],
                    "alert_id": row[1],
                    "action_type": row[2],
                    "action_parameters": json.loads(row[3]) if row[3] else {},
                    "status": row[4],
                    "executed_at": row[5],
                    "result": row[6],
                    "error_message": row[7]
                })
            
            conn.close()
            return executions
            
        except Exception as e:
            logger.error(f"❌ Error getting action execution history: {e}")
            return []
