-- PostgreSQL Schema for Agriculture Semantic Layer
-- Three core entities: IrrigationEvent, EnvironmentControl, PestDetection

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Irrigation Events Table
CREATE TABLE irrigation_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    water_amount_liters DECIMAL(10,2) NOT NULL CHECK (water_amount_liters >= 0),
    irrigation_method VARCHAR(20) NOT NULL CHECK (irrigation_method IN ('drip', 'sprinkler', 'flood', 'manual')),
    irrigation_duration_minutes INTEGER NOT NULL CHECK (irrigation_duration_minutes > 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('scheduled', 'in_progress', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Environment Controls Table
CREATE TABLE environment_controls (
    control_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    temperature_celsius DECIMAL(5,2) NOT NULL CHECK (temperature_celsius BETWEEN -50 AND 100),
    humidity_percent DECIMAL(5,2) NOT NULL CHECK (humidity_percent BETWEEN 0 AND 100),
    co2_ppm INTEGER NOT NULL CHECK (co2_ppm BETWEEN 0 AND 10000),
    light_lux INTEGER NOT NULL CHECK (light_lux >= 0),
    fan_status BOOLEAN NOT NULL DEFAULT FALSE,
    heater_status BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pest Detections Table
CREATE TABLE pest_detections (
    detection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pest_or_disease_type VARCHAR(100) NOT NULL,
    severity_level VARCHAR(20) NOT NULL CHECK (severity_level IN ('low', 'medium', 'high', 'critical')),
    detected_by VARCHAR(20) NOT NULL CHECK (detected_by IN ('sensor', 'camera', 'manual', 'ai_analysis')),
    recommended_action TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_irrigation_timestamp ON irrigation_events(timestamp);
CREATE INDEX idx_irrigation_status ON irrigation_events(status);
CREATE INDEX idx_irrigation_method ON irrigation_events(irrigation_method);

CREATE INDEX idx_environment_timestamp ON environment_controls(timestamp);
CREATE INDEX idx_environment_temperature ON environment_controls(temperature_celsius);
CREATE INDEX idx_environment_humidity ON environment_controls(humidity_percent);

CREATE INDEX idx_pest_timestamp ON pest_detections(timestamp);
CREATE INDEX idx_pest_severity ON pest_detections(severity_level);
CREATE INDEX idx_pest_type ON pest_detections(pest_or_disease_type);

-- Views for common queries
CREATE VIEW latest_irrigation AS
SELECT * FROM irrigation_events 
ORDER BY timestamp DESC 
LIMIT 1;

CREATE VIEW latest_environment AS
SELECT * FROM environment_controls 
ORDER BY timestamp DESC 
LIMIT 1;

CREATE VIEW recent_pest_detections AS
SELECT * FROM pest_detections 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY timestamp DESC;

-- Sample data insertion functions
CREATE OR REPLACE FUNCTION insert_sample_irrigation_data()
RETURNS VOID AS $$
BEGIN
    INSERT INTO irrigation_events (water_amount_liters, irrigation_method, irrigation_duration_minutes, status) VALUES
    (25.5, 'drip', 30, 'completed'),
    (15.0, 'sprinkler', 20, 'completed'),
    (35.2, 'drip', 45, 'in_progress'),
    (20.0, 'manual', 15, 'scheduled');
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_sample_environment_data()
RETURNS VOID AS $$
BEGIN
    INSERT INTO environment_controls (temperature_celsius, humidity_percent, co2_ppm, light_lux, fan_status, heater_status) VALUES
    (24.5, 65.2, 420, 850, TRUE, FALSE),
    (25.1, 68.5, 435, 920, TRUE, FALSE),
    (23.8, 62.1, 410, 780, FALSE, TRUE),
    (26.2, 70.3, 450, 950, TRUE, FALSE);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_sample_pest_data()
RETURNS VOID AS $$
BEGIN
    INSERT INTO pest_detections (pest_or_disease_type, severity_level, detected_by, recommended_action) VALUES
    ('Aphids', 'high', 'camera', 'Apply neem oil spray immediately'),
    ('Leaf Spot', 'medium', 'sensor', 'Increase air circulation and reduce humidity'),
    ('Whiteflies', 'low', 'manual', 'Monitor closely and apply preventive treatment'),
    ('Powdery Mildew', 'critical', 'ai_analysis', 'Emergency treatment required - apply fungicide');
END;
$$ LANGUAGE plpgsql;

-- Trigger for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_irrigation_updated_at BEFORE UPDATE ON irrigation_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_environment_updated_at BEFORE UPDATE ON environment_controls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pest_updated_at BEFORE UPDATE ON pest_detections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample queries for testing
-- These match the natural language queries in the semantic layer

-- "When was the last irrigation?"
-- SELECT timestamp FROM irrigation_events ORDER BY timestamp DESC LIMIT 1;

-- "What is the current humidity?"
-- SELECT humidity_percent FROM environment_controls ORDER BY timestamp DESC LIMIT 1;

-- "What pests have been detected today?"
-- SELECT pest_or_disease_type, severity_level FROM pest_detections WHERE DATE(timestamp) = CURRENT_DATE;

-- "Show me irrigation events from last week"
-- SELECT * FROM irrigation_events WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days';

-- "What is the temperature now?"
-- SELECT temperature_celsius FROM environment_controls ORDER BY timestamp DESC LIMIT 1;

-- "How much water was used today?"
-- SELECT SUM(water_amount_liters) FROM irrigation_events WHERE DATE(timestamp) = CURRENT_DATE;

-- "Are the fans running?"
-- SELECT fan_status FROM environment_controls ORDER BY timestamp DESC LIMIT 1;

-- "Show me high severity pest detections"
-- SELECT * FROM pest_detections WHERE severity_level IN ('high', 'critical');

-- "What are the recommended actions for pests?"
-- SELECT recommended_action FROM pest_detections ORDER BY timestamp DESC LIMIT 5;

-- "What pest trends do we have?"
-- SELECT pest_or_disease_type, COUNT(*) FROM pest_detections GROUP BY pest_or_disease_type;
