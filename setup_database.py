#!/usr/bin/env python3
"""
Database Setup Script for Smart Data Dashboard
Creates PostgreSQL database and tables
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text

def setup_postgresql_database():
    """Setup PostgreSQL database and tables"""
    
    # Database configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_NAME = os.getenv("DB_NAME", "smart_dashboard")
    
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"✅ Database '{DB_NAME}' created successfully")
        else:
            print(f"✅ Database '{DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
        
        # Create tables using SQLAlchemy
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(DATABASE_URL)
        
        # Create sensor_data table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sensor_type VARCHAR(50) NOT NULL,
            value FLOAT NOT NULL
        );
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        
        print("✅ Table 'sensor_data' created successfully")
        
        # Insert sample data
        sample_data_sql = """
        INSERT INTO sensor_data (sensor_type, value) VALUES
        ('temperature', 23.5),
        ('humidity', 65.2),
        ('pressure', 1013.25),
        ('light', 450.0),
        ('temperature', 24.1),
        ('humidity', 63.8),
        ('pressure', 1012.8),
        ('light', 380.0)
        ON CONFLICT DO NOTHING;
        """
        
        with engine.connect() as conn:
            conn.execute(text(sample_data_sql))
            conn.commit()
        
        print("✅ Sample data inserted successfully")
        print(f"✅ Database setup complete! Connection string: {DATABASE_URL}")
        
        return DATABASE_URL
        
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        return None

if __name__ == "__main__":
    print("🚀 Setting up PostgreSQL database for Smart Data Dashboard...")
    setup_postgresql_database()
