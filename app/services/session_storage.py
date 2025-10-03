import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SessionStorage:
    """Database-based session storage for queries, responses, SQL, and semantic JSON"""
    
    def __init__(self, db_path: str = "smart_dashboard.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Initialize session storage tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create session storage table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_storage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    sql_query TEXT,
                    semantic_json TEXT,
                    metrics TEXT,
                    chart_data TEXT,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create session metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    total_queries INTEGER DEFAULT 0
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON session_storage(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_metadata_id ON session_metadata(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_activity ON session_metadata(last_activity)')
            
            conn.commit()
            conn.close()
            logger.info("Session storage tables initialized")
            
        except Exception as e:
            logger.error(f"Error initializing session storage tables: {e}")
    
    def save_session_data(self, session_id: str, query: str, response: str, 
                         sql_query: str = None, semantic_json: Dict = None, 
                         metrics: Dict = None, chart_data: Dict = None) -> bool:
        """Save session data to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Save session data
            cursor.execute('''
                INSERT INTO session_storage 
                (session_id, query, response, sql_query, semantic_json, metrics, chart_data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                query,
                response,
                sql_query,
                json.dumps(semantic_json) if semantic_json else None,
                json.dumps(metrics) if metrics else None,
                json.dumps(chart_data) if chart_data else None,
                datetime.utcnow().isoformat()
            ))
            
            # Update session metadata
            cursor.execute('''
                INSERT OR REPLACE INTO session_metadata 
                (session_id, last_activity, total_queries)
                VALUES (?, ?, COALESCE((SELECT total_queries FROM session_metadata WHERE session_id = ?), 0) + 1)
            ''', (session_id, datetime.utcnow().isoformat(), session_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Session data saved for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session data: {e}")
            return False
    
    def get_session_context(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve past context for follow-up queries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT query, response, sql_query, semantic_json, metrics, timestamp
                FROM session_storage 
                WHERE session_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (session_id, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            context = []
            for row in results:
                context.append({
                    'query': row[0],
                    'response': row[1],
                    'sql_query': row[2],
                    'semantic_json': json.loads(row[3]) if row[3] else None,
                    'metrics': json.loads(row[4]) if row[4] else None,
                    'timestamp': row[5]
                })
            
            logger.info(f"Retrieved {len(context)} context items for session: {session_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving session context: {e}")
            return []
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session summary with key metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session metadata
            cursor.execute('''
                SELECT created_at, last_activity, total_queries, is_active
                FROM session_metadata 
                WHERE session_id = ?
            ''', (session_id,))
            
            metadata = cursor.fetchone()
            if not metadata:
                conn.close()
                return None
            
            # Get recent queries
            cursor.execute('''
                SELECT COUNT(*) as total_queries,
                       COUNT(CASE WHEN sql_query IS NOT NULL THEN 1 END) as sql_queries,
                       COUNT(CASE WHEN semantic_json IS NOT NULL THEN 1 END) as semantic_queries
                FROM session_storage 
                WHERE session_id = ?
            ''', (session_id,))
            
            stats = cursor.fetchone()
            conn.close()
            
            return {
                'session_id': session_id,
                'created_at': metadata[0],
                'last_activity': metadata[1],
                'total_queries': metadata[2],
                'is_active': bool(metadata[3]),
                'sql_queries': stats[1] if stats else 0,
                'semantic_queries': stats[2] if stats else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return None
    
    def expire_sessions(self, timeout_minutes: int = 30) -> int:
        """Expire sessions after timeout"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            cutoff_iso = cutoff_time.isoformat()
            
            # Update expired sessions
            cursor.execute('''
                UPDATE session_metadata 
                SET is_active = 0 
                WHERE last_activity < ? AND is_active = 1
            ''', (cutoff_iso,))
            
            expired_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Expired {expired_count} sessions after {timeout_minutes} minutes timeout")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error expiring sessions: {e}")
            return 0
    
    def cleanup_expired_sessions(self, days_to_keep: int = 7) -> int:
        """Clean up expired session data older than specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
            cutoff_iso = cutoff_time.isoformat()
            
            # Delete expired session data
            cursor.execute('''
                DELETE FROM session_storage 
                WHERE created_at < ?
            ''', (cutoff_iso,))
            
            deleted_count = cursor.rowcount
            
            # Delete expired metadata
            cursor.execute('''
                DELETE FROM session_metadata 
                WHERE created_at < ? AND is_active = 0
            ''', (cutoff_iso,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} expired session records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active sessions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id, created_at, last_activity, total_queries
                FROM session_metadata 
                WHERE is_active = 1 
                ORDER BY last_activity DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in results:
                sessions.append({
                    'session_id': row[0],
                    'created_at': row[1],
                    'last_activity': row[2],
                    'total_queries': row[3]
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []

