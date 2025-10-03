from http.server import BaseHTTPRequestHandler
import json
import sqlite3
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # Mock data for now - replace with actual database connection
            mock_data = [
                {
                    "id": 1,
                    "sensor_type": "temperature",
                    "value": 25.5,
                    "timestamp": "2024-01-01T12:00:00Z",
                    "unit": "°C"
                },
                {
                    "id": 2,
                    "sensor_type": "humidity",
                    "value": 60.2,
                    "timestamp": "2024-01-01T12:00:00Z",
                    "unit": "%"
                }
            ]
            
            response = {
                "success": True,
                "data": mock_data,
                "count": len(mock_data)
            }
            
        except Exception as e:
            response = {
                "success": False,
                "error": str(e),
                "data": []
            }
        
        self.wfile.write(json.dumps(response).encode())
        return
