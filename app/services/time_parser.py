# time_parser.py
from datetime import datetime, timedelta
import re

def parse_time_context(query: str):
    query_lower = query.lower()
    # Use local time instead of UTC to match database timestamps
    now = datetime.now()
    time_context = {}

    # English patterns
    patterns = [
        (r'last (\d+)\s*hour', 'hour'),
        (r'last (\d+)\s*day', 'day'),
        (r'last (\d+)\s*week', 'week'),
        (r'last (\d+)\s*month', 'month'),
    ]

    for pattern, unit in patterns:
        match = re.search(pattern, query_lower)
        if match:
            value = int(match.group(1))
            delta = {
                "hour": timedelta(hours=value),
                "day": timedelta(days=value),
                "week": timedelta(weeks=value),
                "month": timedelta(days=value * 30)
            }[unit]
            # Fix interval naming
            interval_map = {
                "hour": "hourly",
                "day": "daily", 
                "week": "weekly",
                "month": "monthly"
            }
            
            time_context = {
                "unit": unit,
                "value": value,
                "interval": interval_map.get(unit, unit + "ly"),
                "start_time": (now - delta).isoformat(),
                "end_time": now.isoformat()
            }
            return time_context

    # Default: last 24 hours
    return {
        "unit": "hour",
        "value": 24,
        "interval": "hourly",
        "start_time": (now - timedelta(hours=24)).isoformat(),
        "end_time": now.isoformat()
    }
