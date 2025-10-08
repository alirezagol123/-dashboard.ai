#!/usr/bin/env python3
"""
Initialize PostgreSQL database tables for Liara deployment
"""

import os
import psycopg2
from urllib.parse import urlparse

def init_postgresql_database():
    """Initialize PostgreSQL database with required tables"""
    try:
        # Get database URL from environment
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print("❌ DATABASE_URL environment variable not set")
            return False
        
        # Parse database URL
        parsed = urlparse(db_url)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        
        # Create sensor_data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                sensor_type VARCHAR(255) NOT NULL,
                value REAL NOT NULL,
                unit VARCHAR(50),
                source VARCHAR(255),
                raw_json TEXT
            )
        ''')
        
        # Create session_storage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_storage (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                sql_query TEXT,
                semantic_json TEXT,
                metrics TEXT,
                chart_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user_alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_alerts (
                id SERIAL PRIMARY KEY,
                alert_id VARCHAR(255) UNIQUE NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                sensor_type VARCHAR(255) NOT NULL,
                condition VARCHAR(255) NOT NULL,
                threshold REAL NOT NULL,
                operator VARCHAR(10) NOT NULL,
                severity VARCHAR(20) DEFAULT 'warning',
                time_window INTEGER DEFAULT 0,
                action_type VARCHAR(50),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create action_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_logs (
                id VARCHAR(255) PRIMARY KEY,
                alert_id VARCHAR(255) NOT NULL,
                action_type VARCHAR(255) NOT NULL,
                status VARCHAR(255) NOT NULL,
                message TEXT,
                timestamp VARCHAR(255) NOT NULL,
                completed_at VARCHAR(255),
                session_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_type_timestamp ON sensor_data(sensor_type, timestamp);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_data(timestamp);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON session_storage(session_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_session ON user_alerts(session_id);')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ PostgreSQL database initialized successfully!")
        print("✅ Tables created: sensor_data, session_storage, user_alerts, action_logs")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing PostgreSQL database: {e}")
        return False

if __name__ == "__main__":
    init_postgresql_database()
