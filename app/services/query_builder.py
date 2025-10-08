"""
Query Builder Module for Smart Agriculture Platform
Converts semantic JSON into valid SQL templates using ontology mappings
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class QueryBuilder:
    """Converts semantic JSON into SQL templates using flexible templates"""
    
    def __init__(self, ontology: Dict[str, Any]):
        self.ontology = ontology
        self.sql_templates = self._build_sql_templates()
        
    def _build_sql_templates(self) -> Dict[str, str]:
        """Build SQL templates for different query patterns"""
        return {
            "current_value": """
                SELECT * FROM sensor_data 
                WHERE sensor_type = '{entity}' 
                ORDER BY timestamp DESC 
                LIMIT 1
            """,
            
            "average_value": """
                SELECT AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points
                FROM sensor_data 
                WHERE sensor_type = '{entity}'
            """,
            
            "time_aware_day": """
                SELECT DATE(timestamp) as time_period, 
                       AVG(value) as avg_value, 
                       MIN(value) as min_value, 
                       MAX(value) as max_value, 
                       COUNT(*) as data_points
                FROM sensor_data 
                WHERE sensor_type = '{entity}' 
                AND timestamp >= datetime('now', '-{time_range} days')
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp) ASC
            """,
            
            "time_aware_hour": """
                SELECT strftime('%Y-%m-%d %H:00', timestamp) as time_period, 
                       AVG(value) as avg_value, 
                       MIN(value) as min_value, 
                       MAX(value) as max_value, 
                       COUNT(*) as data_points
                FROM sensor_data 
                WHERE sensor_type = '{entity}' 
                AND timestamp >= datetime('now', '-{time_range} hours')
                GROUP BY strftime('%Y-%m-%d %H:00', timestamp)
                ORDER BY strftime('%Y-%m-%d %H:00', timestamp) ASC
            """,
            
            "time_aware_minute": """
                SELECT strftime('%Y-%m-%d %H:%M', timestamp) as time_period, 
                       AVG(value) as avg_value, 
                       MIN(value) as min_value, 
                       MAX(value) as max_value, 
                       COUNT(*) as data_points
                FROM sensor_data 
                WHERE sensor_type = '{entity}' 
                AND timestamp >= datetime('now', '-{time_range} minutes')
                GROUP BY strftime('%Y-%m-%d %H:%M', timestamp)
                ORDER BY strftime('%Y-%m-%d %H:%M', timestamp) ASC
            """,
            
            "time_aware_week": """
                SELECT strftime('%Y-%W', timestamp) as time_period, 
                       AVG(value) as avg_value, 
                       MIN(value) as min_value, 
                       MAX(value) as max_value, 
                       COUNT(*) as data_points
                FROM sensor_data 
                WHERE sensor_type = '{entity}' 
                AND timestamp >= datetime('now', '-{time_range} days')
                GROUP BY strftime('%Y-%W', timestamp)
                ORDER BY strftime('%Y-%W', timestamp) ASC
            """,
            
            "compound_current": """
                SELECT * FROM sensor_data 
                WHERE sensor_type IN ({entities}) 
                ORDER BY timestamp DESC 
                LIMIT {limit}
            """,
            
            "compound_time_aware": """
                SELECT {time_period_select}, sensor_type, 
                       AVG(value) as avg_value, 
                       MIN(value) as min_value, 
                       MAX(value) as max_value, 
                       COUNT(*) as data_points
                FROM sensor_data 
                WHERE sensor_type IN ({entities}) 
                AND {time_condition}
                GROUP BY {time_period_group}, sensor_type
                ORDER BY {time_period_group} ASC, sensor_type ASC
            """,
            
            "trend_analysis": """
                SELECT timestamp, value 
                FROM sensor_data 
                WHERE sensor_type = '{entity}' 
                ORDER BY timestamp DESC 
                LIMIT 10
            """,
            
            "comparison": """
                SELECT sensor_type, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value
                FROM sensor_data 
                WHERE sensor_type IN ({entities}) 
                GROUP BY sensor_type
            """
        }
    
    def build_time_based_query(self, sensor_type, time_context, aggregation="AVG"):
        """Build time-based query using dynamic time_context"""
        start = time_context["start_time"]
        end = time_context["end_time"]
        granularity = time_context["interval"]

        if granularity.startswith("hour"):
            time_group = "strftime('%Y-%m-%d %H:00', timestamp)"
        elif granularity.startswith("day"):
            time_group = "date(timestamp)"
        elif granularity.startswith("week"):
            time_group = "strftime('%Y-%W', timestamp)"
        elif granularity.startswith("month"):
            time_group = "strftime('%Y-%m', timestamp)"
        else:
            time_group = "strftime('%Y-%m-%d %H:00', timestamp)"

        return f"""
        SELECT {time_group} AS time_period,
               sensor_type,
               {aggregation}(value) AS avg_value,
               MIN(value) AS min_value,
               MAX(value) AS max_value,
               COUNT(*) AS data_points
        FROM sensor_data
        WHERE sensor_type = '{sensor_type}'
          AND timestamp BETWEEN '{start}' AND '{end}'
        GROUP BY {time_group}, sensor_type
        ORDER BY time_period;
        """

    def build_sql_from_semantic_json(self, semantic_json: Dict[str, Any]) -> str:
        """Convert semantic JSON to SQL query"""
        try:
            logger.info(f"🔧 Building SQL from semantic JSON: {semantic_json}")
            
            # Extract semantic components
            entity = semantic_json.get("entity", "temperature")
            aggregation = semantic_json.get("aggregation", "current")
            time_range = semantic_json.get("time_range", "last_24_hours")
            grouping = semantic_json.get("grouping", "none")
            format_type = semantic_json.get("format", "value")
            comparison = semantic_json.get("comparison", False)
            
            # Check if time_context is available for dynamic query generation
            time_context = semantic_json.get("time_context")
            if time_context:
                logger.info(f"🔧 Using dynamic time_context: {time_context}")
                # Use dynamic time-based query generation
                if isinstance(entity, list):
                    # Handle multiple entities
                    sensor_types = "', '".join(entity)
                    start = time_context["start_time"]
                    end = time_context["end_time"]
                    granularity = time_context["interval"]
                    
                    if granularity.startswith("hour"):
                        time_group = "strftime('%Y-%m-%d %H:00', timestamp)"
                    elif granularity.startswith("day"):
                        time_group = "date(timestamp)"
                    elif granularity.startswith("week"):
                        time_group = "strftime('%Y-%W', timestamp)"
                    elif granularity.startswith("month"):
                        time_group = "strftime('%Y-%m', timestamp)"
                    else:
                        time_group = "strftime('%Y-%m-%d %H:00', timestamp)"
                    
                    return f"""
                    SELECT {time_group} AS time_period,
                           sensor_type,
                           AVG(value) AS avg_value,
                           MIN(value) AS min_value,
                           MAX(value) AS max_value,
                           COUNT(*) AS data_points
                    FROM sensor_data
                    WHERE sensor_type IN ('{sensor_types}')
                      AND timestamp BETWEEN '{start}' AND '{end}'
                    GROUP BY {time_group}, sensor_type
                    ORDER BY time_period ASC, sensor_type ASC;
                    """
                else:
                    # Single entity with dynamic time context
                    return self.build_time_based_query(entity, time_context, "AVG")
            
            # Handle comparison queries
            if comparison:
                # Check if this is time range comparison (multiple time periods) - PRIORITY
                if isinstance(time_range, list) and len(time_range) > 1:
                    return self._build_time_comparison_sql(entity, time_range, aggregation, grouping)
                # Check if this is entity comparison (multiple sensors)
                elif isinstance(entity, list) and len(entity) > 1:
                    return self._build_entity_comparison_sql(entity, aggregation, time_range)
                else:
                    # Single entity + single time range but comparison requested
                    # Use dynamic time_context if available, otherwise fallback to static logic
                    if time_context:
                        return self.build_time_based_query(entity, time_context, "AVG")
                    else:
                        # Fallback to static time range logic
                        if isinstance(time_range, str) and any(keyword in time_range.lower() for keyword in ["days", "hours", "weeks", "months", "last_", "past_", "ago"]):
                            return self._build_daily_breakdown_sql(entity, time_range, aggregation, grouping)
                        else:
                            if isinstance(time_range, list):
                                comparison_ranges = time_range
                            else:
                                comparison_ranges = [time_range, self._get_previous_time_range(time_range)]
                            return self._build_time_comparison_sql(entity, comparison_ranges, aggregation, grouping)
            
            # Handle compound entities (multiple sensors)
            if isinstance(entity, list):
                return self._build_compound_sql(entity, semantic_json)
            
            # Handle single entity queries - use dynamic time_context if available
            if time_context:
                return self.build_time_based_query(entity, time_context, "AVG")
            else:
                # Fallback to static logic
                return self._build_single_entity_sql(entity, aggregation, time_range, grouping, format_type)
            
        except Exception as e:
            logger.error(f"❌ Error building SQL from semantic JSON: {e}")
            return self._get_fallback_sql(entity if isinstance(entity, str) else "temperature")
    
    def _build_single_entity_sql(self, entity: str, aggregation: str, time_range: str, grouping: str, format_type: str) -> str:
        """Build SQL for single entity queries - now uses dynamic time_context"""
        try:
            # For current/latest values, use simple template
            if aggregation == "current" or aggregation == "latest":
                template = self.sql_templates["current_value"]
                return template.format(entity=entity)
            
            # For average values without grouping, use simple template
            elif aggregation == "average" and grouping == "none":
                template = self.sql_templates["average_value"]
                return template.format(entity=entity)
            
            # For grouped queries, use dynamic time_context approach
            # This method is now primarily a fallback when time_context is not available
            # The main logic should use build_time_based_query with time_context
            else:
                # Fallback to static time range parsing (legacy support)
                time_window = self._parse_time_range(time_range)
                
                if aggregation == "average" and grouping in ["by_day", "daily"]:
                    template = self.sql_templates["time_aware_day"]
                    return template.format(entity=entity, time_range=time_window["days"])
                
                elif aggregation == "average" and grouping in ["by_hour", "hourly"]:
                    template = self.sql_templates["time_aware_hour"]
                    return template.format(entity=entity, time_range=time_window["hours"])
                
                elif aggregation == "average" and grouping in ["by_minute", "minutely"]:
                    template = self.sql_templates["time_aware_minute"]
                    return template.format(entity=entity, time_range=time_window["minutes"])
            
                elif aggregation == "average" and grouping in ["by_week", "weekly"]:
                    template = self.sql_templates["time_aware_week"]
                    return template.format(entity=entity, time_range=time_window["days"])
            
                elif format_type == "trend":
                    template = self.sql_templates["trend_analysis"]
                    return template.format(entity=entity)
            
                else:
                # Default fallback
                     return self._get_fallback_sql(entity)
                
        except Exception as e:
            logger.error(f"❌ Error building single entity SQL: {e}")
            return self._get_fallback_sql(entity)
    
    def _build_compound_sql(self, entities: List[str], semantic_json: Dict[str, Any]) -> str:
        """Build SQL for compound queries (multiple sensors)"""
        try:
            aggregation = semantic_json.get("aggregation", "current")
            time_range = semantic_json.get("time_range", "last_24_hours")
            grouping = semantic_json.get("grouping", "none")
            
            # Create entities list for SQL IN clause
            entities_str = "', '".join(entities)
            
            # Map time range to SQL time window
            time_window = self._parse_time_range(time_range)
            
            if aggregation == "current" or aggregation == "latest":
                template = self.sql_templates["compound_current"]
                return template.format(entities=f"'{entities_str}'", limit=len(entities))
            
            elif aggregation == "average" and grouping != "none":
                # Build time-aware compound query
                time_period_select, time_period_group, time_condition = self._build_time_aware_components(grouping, time_window)
                
                template = self.sql_templates["compound_time_aware"]
                return template.format(
                    entities=f"'{entities_str}'",
                    time_period_select=time_period_select,
                    time_period_group=time_period_group,
                    time_condition=time_condition
                )
            
            else:
                # Default compound query
                template = self.sql_templates["comparison"]
                return template.format(entities=f"'{entities_str}'")
                
        except Exception as e:
            logger.error(f"❌ Error building compound SQL: {e}")
            return self._get_fallback_sql(entities[0] if entities else "temperature")
    
    def _parse_time_range(self, time_range: str) -> Dict[str, int]:
        """Parse time range string to SQL time window"""
        time_range_lower = time_range.lower()
        
        # Parse different time range formats
        if "last_3_days" in time_range_lower or "three_days" in time_range_lower:
            return {"days": 3, "hours": 72, "minutes": 4320}
        elif "last_7_days" in time_range_lower or "one_week" in time_range_lower:
            return {"days": 7, "hours": 168, "minutes": 10080}
        elif "last_2_days" in time_range_lower or "two_days" in time_range_lower:
            return {"days": 2, "hours": 48, "minutes": 2880}
        elif "last_24_hours" in time_range_lower or "one_day" in time_range_lower:
            return {"days": 1, "hours": 24, "minutes": 1440}
        elif "last_4_hours" in time_range_lower or "four_hours" in time_range_lower:
            return {"days": 0, "hours": 4, "minutes": 240}
        elif "last_6_hours" in time_range_lower or "six_hours" in time_range_lower:
            return {"days": 0, "hours": 6, "minutes": 360}
        elif "last_8_hours" in time_range_lower or "eight_hours" in time_range_lower:
            return {"days": 0, "hours": 8, "minutes": 480}
        elif "last_12_hours" in time_range_lower or "twelve_hours" in time_range_lower:
            return {"days": 0, "hours": 12, "minutes": 720}
        elif "last_2_hours" in time_range_lower or "two_hours" in time_range_lower:
            return {"days": 0, "hours": 2, "minutes": 120}
        elif "last_hour" in time_range_lower or "one_hour" in time_range_lower:
            return {"days": 0, "hours": 1, "minutes": 60}
        elif "last_30_minutes" in time_range_lower:
            return {"days": 0, "hours": 0, "minutes": 30}
        elif "last_4_weeks" in time_range_lower or "four_weeks" in time_range_lower:
            return {"days": 28, "hours": 672, "minutes": 40320}
        elif "last_2_weeks" in time_range_lower or "two_weeks" in time_range_lower:
            return {"days": 14, "hours": 336, "minutes": 20160}
        elif "last_week" in time_range_lower or "one_week" in time_range_lower:
            return {"days": 7, "hours": 168, "minutes": 10080}
        else:
            # Default to last 24 hours
            return {"days": 1, "hours": 24, "minutes": 1440}
    
    def _build_time_aware_components(self, grouping: str, time_window: Dict[str, int]) -> tuple:
        """Build time-aware SQL components for compound queries"""
        if grouping in ["by_day", "daily"]:
            time_period_select = "DATE(timestamp) as time_period"
            time_period_group = "DATE(timestamp)"
            time_condition = f"timestamp >= datetime('now', '-{time_window['days']} days')"
        elif grouping in ["by_hour", "hourly"]:
            time_period_select = "strftime('%Y-%m-%d %H:00', timestamp) as time_period"
            time_period_group = "strftime('%Y-%m-%d %H:00', timestamp)"
            time_condition = f"timestamp >= datetime('now', '-{time_window['hours']} hours')"
        elif grouping in ["by_minute", "minutely"]:
            time_period_select = "strftime('%Y-%m-%d %H:%M', timestamp) as time_period"
            time_period_group = "strftime('%Y-%m-%d %H:%M', timestamp)"
            time_condition = f"timestamp >= datetime('now', '-{time_window['minutes']} minutes')"
        elif grouping in ["by_week", "weekly"]:
            time_period_select = "strftime('%Y-%W', timestamp) as time_period"
            time_period_group = "strftime('%Y-%W', timestamp)"
            time_condition = f"timestamp >= datetime('now', '-{time_window['days']} days')"
        else:
            # Default to daily
            time_period_select = "DATE(timestamp) as time_period"
            time_period_group = "DATE(timestamp)"
            time_condition = f"timestamp >= datetime('now', '-{time_window['days']} days')"
        
        return time_period_select, time_period_group, time_condition
    
    def _build_entity_comparison_sql(self, entities: List[str], aggregation: str, time_range: str) -> str:
        """Build SQL for comparing multiple entities (sensors)"""
        try:
            # Convert to single time range if needed
            if isinstance(time_range, str):
                time_window = self._parse_time_range(time_range)
                time_condition = f"timestamp >= datetime('now', '-{time_window['days']} days')"
            else:
                time_condition = "timestamp >= datetime('now', '-7 days')"  # fallback
            
            entities_str = "', '".join(entities)
            
            sql = f"""
                SELECT sensor_type,
                       AVG(value) as avg_value,
                       MIN(value) as min_value,
                       MAX(value) as max_value,
                       COUNT(*) as data_points
                FROM sensor_data
                WHERE sensor_type IN ('{entities_str}')
                AND {time_condition}
                GROUP BY sensor_type
                ORDER BY sensor_type ASC
            """
            
            logger.info(f"🔧 Built entity comparison SQL for entities: {entities}")
            return sql.strip()
            
        except Exception as e:
            logger.error(f"❌ Error building entity comparison SQL: {e}")
            return self._get_fallback_sql(entities[0] if entities else "temperature")
    
    def _build_time_comparison_sql(self, entity: str, time_ranges: List[str], aggregation: str, grouping: str) -> str:
        """Build SQL for comparing time ranges with proper aggregation"""
        try:
            # Handle multiple entities
            if isinstance(entity, list):
                entities = entity
            else:
                entities = [entity]
            
            # Build UNION query for multiple time ranges with proper aggregation
            union_queries = []
            
            for time_range in time_ranges:
                # Get time filter from the unified service
                from app.services.unified_semantic_service import UnifiedSemanticQueryService
                service = UnifiedSemanticQueryService()
                label, start_iso, end_iso, condition = service._time_range_to_sql_filter(time_range)
                
                # Build aggregation based on grouping
                if grouping == "by_week":
                    group_by = "strftime('%Y-%W', timestamp)"
                    time_period_select = f"strftime('%Y-%W', timestamp) as time_period"
                elif grouping == "by_month":
                    group_by = "strftime('%Y-%m', timestamp)"
                    time_period_select = f"strftime('%Y-%m', timestamp) as time_period"
                elif grouping == "by_day":
                    group_by = "DATE(timestamp)"
                    time_period_select = f"DATE(timestamp) as time_period"
                else:
                    # Default to single aggregated value for the entire range
                    group_by = "1"  # Group all rows together
                    time_period_select = f"'{label}' as time_period"
                
                # Handle multiple entities for each time range
                for entity_name in entities:
                    union_queries.append(f"""
                        SELECT '{label}' as time_period,
                               '{entity_name}' as sensor_type,
                               AVG(value) as avg_value,
                               MIN(value) as min_value,
                               MAX(value) as max_value,
                               COUNT(*) as data_points
                        FROM sensor_data
                        WHERE sensor_type = '{entity_name}'
                        AND {condition}
                        GROUP BY {group_by}
                    """)
            
            if not union_queries:
                # IMPROVED FALLBACK: Use granularity-based logic instead of hardcoded today/yesterday
                # Check if we have explicit ranges from semantic_json
                if isinstance(time_ranges, list) and len(time_ranges) > 0:
                    # Use the provided ranges
                    for time_range in time_ranges:
                        if time_range.startswith("past_"):
                            # Build dynamic condition for past_n_hours/days
                            for entity_name in entities:
                                union_queries.append(self._build_dynamic_time_condition(entity_name, time_range, aggregation, grouping))
                        else:
                            # Use existing logic for standard ranges
                            from app.services.unified_semantic_service import UnifiedSemanticQueryService
                            service = UnifiedSemanticQueryService()
                            label, start_iso, end_iso, condition = service._time_range_to_sql_filter(time_range)
                            for entity_name in entities:
                                union_queries.append(f"""
                                    SELECT '{label}' as time_period,
                                           '{entity_name}' as sensor_type,
                                           AVG(value) as avg_value,
                                           MIN(value) as min_value,
                                           MAX(value) as max_value,
                                           COUNT(*) as data_points
                                    FROM sensor_data
                                    WHERE sensor_type = '{entity_name}'
                                    AND {condition}
                                """)
                else:
                    # GRANULARITY-BASED FALLBACK: Use granularity to determine appropriate comparison
                    # This replaces the hardcoded today/yesterday fallback
                    if hasattr(self, 'current_granularity'):
                        granularity = self.current_granularity
                    else:
                        granularity = "day"  # default
                    
                    if granularity == "hour":
                        # Compare last hour vs previous hour
                        union_queries = [
                            f"""
                                SELECT 'last_hour' as time_period,
                                       '{entity}' as sensor_type,
                                       AVG(value) as avg_value,
                                       MIN(value) as min_value,
                                       MAX(value) as max_value,
                                       COUNT(*) as data_points
                                FROM sensor_data
                                WHERE sensor_type = '{entity}'
                                AND timestamp >= datetime('now', '-1 hour')
                            """,
                            f"""
                                SELECT 'previous_hour' as time_period,
                                       '{entity}' as sensor_type,
                                       AVG(value) as avg_value,
                                       MIN(value) as min_value,
                                       MAX(value) as max_value,
                                       COUNT(*) as data_points
                                FROM sensor_data
                                WHERE sensor_type = '{entity}'
                                AND timestamp >= datetime('now', '-2 hour') AND timestamp < datetime('now', '-1 hour')
                            """
                        ]
                    elif granularity == "day":
                        # Compare today vs yesterday
                        union_queries = [
                            f"""
                                SELECT 'today' as time_period,
                                       '{entity}' as sensor_type,
                                       AVG(value) as avg_value,
                                       MIN(value) as min_value,
                                       MAX(value) as max_value,
                                       COUNT(*) as data_points
                                FROM sensor_data
                                WHERE sensor_type = '{entity}'
                                AND DATE(timestamp) = DATE('now')
                            """,
                            f"""
                                SELECT 'yesterday' as time_period,
                                       '{entity}' as sensor_type,
                                       AVG(value) as avg_value,
                                       MIN(value) as min_value,
                                       MAX(value) as max_value,
                                       COUNT(*) as data_points
                                FROM sensor_data
                                WHERE sensor_type = '{entity}'
                                AND DATE(timestamp) = DATE('now', '-1 day')
                            """
                        ]
                    elif granularity == "week":
                        # Compare this week vs last week
                        union_queries = [
                            f"""
                                SELECT 'this_week' as time_period,
                                       '{entity}' as sensor_type,
                                       AVG(value) as avg_value,
                                       MIN(value) as min_value,
                                       MAX(value) as max_value,
                                       COUNT(*) as data_points
                                FROM sensor_data
                                WHERE sensor_type = '{entity}'
                                AND strftime('%Y-%W', timestamp) = strftime('%Y-%W', 'now')
                            """,
                            f"""
                                SELECT 'last_week' as time_period,
                                       '{entity}' as sensor_type,
                                       AVG(value) as avg_value,
                                       MIN(value) as min_value,
                                       MAX(value) as max_value,
                                       COUNT(*) as data_points
                                FROM sensor_data
                                WHERE sensor_type = '{entity}'
                                AND strftime('%Y-%W', timestamp) = strftime('%Y-%W', 'now', '-7 days')
                            """
                        ]
                    else:
                        # Default to today vs yesterday
                        union_queries = [
                            f"""
                                SELECT 'today' as time_period,
                                       '{entity}' as sensor_type,
                                       AVG(value) as avg_value,
                                       MIN(value) as min_value,
                                       MAX(value) as max_value,
                                       COUNT(*) as data_points
                                FROM sensor_data
                                WHERE sensor_type = '{entity}'
                                AND DATE(timestamp) = DATE('now')
                            """,
                            f"""
                                SELECT 'yesterday' as time_period,
                                       '{entity}' as sensor_type,
                                       AVG(value) as avg_value,
                                       MIN(value) as min_value,
                                       MAX(value) as max_value,
                                       COUNT(*) as data_points
                                FROM sensor_data
                                WHERE sensor_type = '{entity}'
                                AND DATE(timestamp) = DATE('now', '-1 day')
                            """
                        ]
            
            sql = " UNION ALL ".join(union_queries) + " ORDER BY time_period ASC"
            
            logger.info(f"🔧 Built time comparison SQL for entity '{entity}' across ranges: {time_ranges}")
            return sql.strip()
            
        except Exception as e:
            logger.error(f"❌ Error building time comparison SQL: {e}")
            return self._get_fallback_sql(entity if isinstance(entity, str) else "temperature")
    
    def _build_dynamic_time_condition(self, entity: str, time_range: str, aggregation: str, grouping: str) -> str:
        """Build dynamic time condition for past_n_hours/days expressions"""
        try:
            import re
            
            # Extract number and unit from past_n_hours or past_n_days
            hour_match = re.search(r'past_(\d+)_hours', time_range)
            day_match = re.search(r'past_(\d+)_days', time_range)
            
            if hour_match:
                hours = int(hour_match.group(1))
                return f"""
                    SELECT '{time_range}' as time_period,
                           '{entity}' as sensor_type,
                           AVG(value) as avg_value,
                           MIN(value) as min_value,
                           MAX(value) as max_value,
                           COUNT(*) as data_points
                    FROM sensor_data
                    WHERE sensor_type = '{entity}'
                    AND timestamp >= datetime('now', '-{hours} hours')
                """
            elif day_match:
                days = int(day_match.group(1))
                return f"""
                    SELECT '{time_range}' as time_period,
                           '{entity}' as sensor_type,
                           AVG(value) as avg_value,
                           MIN(value) as min_value,
                           MAX(value) as max_value,
                           COUNT(*) as data_points
                    FROM sensor_data
                    WHERE sensor_type = '{entity}'
                    AND timestamp >= datetime('now', '-{days} days')
                """
            else:
                # Fallback to generic past condition
                return f"""
                    SELECT '{time_range}' as time_period,
                           '{entity}' as sensor_type,
                           AVG(value) as avg_value,
                           MIN(value) as min_value,
                           MAX(value) as max_value,
                           COUNT(*) as data_points
                    FROM sensor_data
                    WHERE sensor_type = '{entity}'
                    AND timestamp >= datetime('now', '-1 day')
                """
        except Exception as e:
            logger.error(f"Error building dynamic time condition: {e}")
            return f"""
                SELECT '{time_range}' as time_period,
                       '{entity}' as sensor_type,
                       AVG(value) as avg_value,
                       MIN(value) as min_value,
                       MAX(value) as max_value,
                       COUNT(*) as data_points
                FROM sensor_data
                WHERE sensor_type = '{entity}'
                AND timestamp >= datetime('now', '-1 day')
            """
    
    def _build_comparison_sql(self, entity: str, time_ranges: List[str], aggregation: str, grouping: str) -> str:
        """Build SQL for comparison queries with multiple time ranges"""
        try:
            # Handle multiple entities
            if isinstance(entity, list):
                entities_str = "', '".join(entity)
                entity_condition = f"sensor_type IN ('{entities_str}')"
            else:
                entity_condition = f"sensor_type = '{entity}'"
            
            # Build time conditions for each range
            time_conditions = []
            for time_range in time_ranges:
                condition = self._build_time_condition_for_range(time_range)
                if condition:
                    time_conditions.append(condition)
            
            if not time_conditions:
                # Fallback to last 2 days
                time_conditions = ["timestamp >= datetime('now', '-2 days')"]
            
            # Build the complete SQL
            if grouping in ["by_day", "daily"]:
                time_period_select = "DATE(timestamp) as time_period"
                time_period_group = "DATE(timestamp)"
            elif grouping in ["by_hour", "hourly"]:
                time_period_select = "strftime('%Y-%m-%d %H:00', timestamp) as time_period"
                time_period_group = "strftime('%Y-%m-%d %H:00', timestamp)"
            elif grouping in ["by_week", "weekly"]:
                time_period_select = "strftime('%Y-%W', timestamp) as time_period"
                time_period_group = "strftime('%Y-%W', timestamp)"
            else:
                # Default to daily
                time_period_select = "DATE(timestamp) as time_period"
                time_period_group = "DATE(timestamp)"
            
            # Combine time conditions with OR
            combined_time_condition = " OR ".join([f"({cond})" for cond in time_conditions])
            
            sql = f"""
                SELECT {time_period_select}, sensor_type,
                       AVG(value) as avg_value,
                       MIN(value) as min_value,
                       MAX(value) as max_value,
                       COUNT(*) as data_points
                FROM sensor_data
                WHERE {entity_condition}
                AND ({combined_time_condition})
                GROUP BY {time_period_group}, sensor_type
                ORDER BY {time_period_group} ASC, sensor_type ASC
            """
            
            logger.info(f"🔧 Built comparison SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f"❌ Error building comparison SQL: {e}")
            return self._get_fallback_sql(entity if isinstance(entity, str) else "temperature")
    
    def _build_time_condition_for_range(self, time_range: str) -> str:
        """Build SQL time condition for a specific time range"""
        time_range_lower = time_range.lower()
        
        # Handle expanded time ranges (e.g., "4_hours_ago", "2_days_ago")
        if "_hours_ago" in time_range_lower:
            import re
            match = re.search(r'(\d+)_hours_ago', time_range_lower)
            if match:
                hours = int(match.group(1))
                return f"timestamp >= datetime('now', '-{hours} hours')"
        
        elif "_days_ago" in time_range_lower:
            import re
            match = re.search(r'(\d+)_days_ago', time_range_lower)
            if match:
                days = int(match.group(1))
                return f"timestamp >= datetime('now', '-{days} days')"
        
        elif "_weeks_ago" in time_range_lower:
            import re
            match = re.search(r'(\d+)_weeks_ago', time_range_lower)
            if match:
                weeks = int(match.group(1))
                days = weeks * 7
                return f"timestamp >= datetime('now', '-{days} days')"
        
        # Handle past_n_hours/days patterns
        elif time_range_lower.startswith("past_") and "_hours" in time_range_lower:
            import re
            match = re.search(r'past_(\d+)_hours', time_range_lower)
            if match:
                hours = int(match.group(1))
                return f"timestamp >= datetime('now', '-{hours} hours')"
        
        elif time_range_lower.startswith("past_") and "_days" in time_range_lower:
            import re
            match = re.search(r'past_(\d+)_days', time_range_lower)
            if match:
                days = int(match.group(1))
                return f"timestamp >= datetime('now', '-{days} days')"
        
        # Handle standard time ranges
        elif time_range_lower == "today":
            return "DATE(timestamp) = DATE('now')"
        elif time_range_lower == "yesterday":
            return "DATE(timestamp) = DATE('now', '-1 day')"
        elif time_range_lower == "this_week":
            return "timestamp >= datetime('now', 'weekday 0', '-6 days')"
        elif time_range_lower == "last_week":
            return "timestamp BETWEEN datetime('now', 'weekday 0', '-13 days') AND datetime('now', 'weekday 0', '-7 days')"
        elif time_range_lower == "this_month":
            return "timestamp >= datetime('now', 'start of month')"
        elif time_range_lower == "last_month":
            return "timestamp BETWEEN datetime('now', 'start of month', '-1 month') AND datetime('now', 'start of month')"
        elif time_range_lower == "this_year":
            return "timestamp >= datetime('now', 'start of year')"
        elif time_range_lower == "last_year":
            return "timestamp BETWEEN datetime('now', 'start of year', '-1 year') AND datetime('now', 'start of year')"
        else:
            return None
    
    def _get_fallback_sql(self, entity: str) -> str:
        """Get fallback SQL query"""
        return f"SELECT * FROM sensor_data WHERE sensor_type = '{entity}' ORDER BY timestamp DESC LIMIT 5"
    
    def _get_previous_time_range(self, time_range: str) -> str:
        """Get the previous time range for comparison"""
        if "hours_ago" in time_range:
            import re
            match = re.search(r'(\d+)_hours_ago', time_range)
            if match:
                hours = int(match.group(1))
                return f"{hours * 2}_hours_ago"
        elif "days_ago" in time_range:
            import re
            match = re.search(r'(\d+)_days_ago', time_range)
            if match:
                days = int(match.group(1))
                return f"{days * 2}_days_ago"
        elif "weeks_ago" in time_range:
            import re
            match = re.search(r'(\d+)_weeks_ago', time_range)
            if match:
                weeks = int(match.group(1))
                return f"{weeks * 2}_weeks_ago"
        else:
            # Default fallback
            return "yesterday"
    
    def _build_daily_breakdown_sql(self, entity: str, time_range: str, aggregation: str, grouping: str) -> str:
        """Build SQL for time-based breakdown of time ranges (e.g., last 3 days -> daily data, last 6 hours -> hourly data)"""
        try:
            # Get time filter from the unified service
            from app.services.unified_semantic_service import UnifiedSemanticQueryService
            service = UnifiedSemanticQueryService()
            label, start_iso, end_iso, condition = service._time_range_to_sql_filter(time_range)
            
            # Determine appropriate grouping based on time range and granularity
            if "hour" in time_range or "ساعت" in time_range:
                # Hourly breakdown for hour-based queries
                time_period_select = "strftime('%Y-%m-%d %H:00', timestamp) as time_period"
                group_by = "strftime('%Y-%m-%d %H:00', timestamp)"
                period_label = "hour"
            elif "week" in time_range or "هفته" in time_range:
                # Weekly breakdown for week-based queries
                time_period_select = "strftime('%Y-%W', timestamp) as time_period"
                group_by = "strftime('%Y-%W', timestamp)"
                period_label = "week"
            elif "month" in time_range or "ماه" in time_range:
                # Monthly breakdown for month-based queries
                time_period_select = "strftime('%Y-%m', timestamp) as time_period"
                group_by = "strftime('%Y-%m', timestamp)"
                period_label = "month"
            else:
                # Default to daily breakdown
                time_period_select = "DATE(timestamp) as time_period"
                group_by = "DATE(timestamp)"
                period_label = "day"
            
            # Build time-based breakdown with trend analysis
            sql = f"""
                SELECT 
                    {time_period_select},
                    sensor_type,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    COUNT(*) as data_points,
                    ROUND(AVG(value), 2) as period_avg,
                    ROUND(MAX(value) - MIN(value), 2) as period_range
                FROM sensor_data
                WHERE sensor_type = '{entity}'
                AND {condition}
                GROUP BY {group_by}, sensor_type
                ORDER BY time_period ASC
            """
            
            logger.info(f"🔧 Built {period_label} breakdown SQL for entity '{entity}' over range '{time_range}'")
            return sql.strip()
            
        except Exception as e:
            logger.error(f"❌ Error building {period_label} breakdown SQL: {e}")
            return self._get_fallback_sql(entity)
    
    def validate_semantic_json(self, semantic_json: Dict[str, Any]) -> Dict[str, Any]:
        """Validate semantic JSON structure"""
        try:
            required_fields = ["entity"]
            optional_fields = ["aggregation", "time_range", "grouping", "format"]
            
            # Check required fields
            for field in required_fields:
                if field not in semantic_json:
                    return {
                        "valid": False,
                        "error": f"Missing required field: {field}",
                        "suggestions": [f"Add {field} field to semantic JSON"]
                    }
            
            # Validate entity
            entity = semantic_json["entity"]
            if isinstance(entity, list):
                # Compound entity
                if not entity or len(entity) == 0:
                    return {
                        "valid": False,
                        "error": "Entity list cannot be empty",
                        "suggestions": ["Provide at least one sensor type in entity list"]
                    }
            elif isinstance(entity, str):
                # Single entity
                if not entity or entity.strip() == "":
                    return {
                        "valid": False,
                        "error": "Entity cannot be empty",
                        "suggestions": ["Provide a valid sensor type"]
                    }
            else:
                return {
                    "valid": False,
                    "error": "Entity must be string or list",
                    "suggestions": ["Use string for single sensor or list for multiple sensors"]
                }
            
            # Validate aggregation
            valid_aggregations = ["current", "latest", "average", "min", "max", "count"]
            aggregation = semantic_json.get("aggregation", "current")
            if aggregation not in valid_aggregations:
                return {
                    "valid": False,
                    "error": f"Invalid aggregation: {aggregation}",
                    "suggestions": [f"Use one of: {', '.join(valid_aggregations)}"]
                }
            
            # Validate grouping
            valid_groupings = ["none", "by_day", "daily", "by_hour", "hourly", "by_minute", "minutely", "by_week", "weekly"]
            grouping = semantic_json.get("grouping", "none")
            if grouping not in valid_groupings:
                return {
                    "valid": False,
                    "error": f"Invalid grouping: {grouping}",
                    "suggestions": [f"Use one of: {', '.join(valid_groupings)}"]
                }
            
            return {
                "valid": True,
                "message": "Semantic JSON is valid",
                "suggestions": []
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "suggestions": ["Check semantic JSON structure"]
            }
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported sensor entities from ontology"""
        try:
            sensor_mappings = self.ontology.get("sensor_mappings", {})
            return list(sensor_mappings.keys())
        except Exception as e:
            logger.error(f"❌ Error getting supported entities: {e}")
            return ["temperature", "humidity", "soil_moisture", "water_usage", "pest_count"]
    
    def get_supported_aggregations(self) -> List[str]:
        """Get list of supported aggregations"""
        return ["current", "latest", "average", "min", "max", "count"]
    
    def get_supported_groupings(self) -> List[str]:
        """Get list of supported groupings"""
        return ["none", "by_day", "daily", "by_hour", "hourly", "by_minute", "minutely", "by_week", "weekly"]
    
    def get_supported_time_ranges(self) -> List[str]:
        """Get list of supported time ranges"""
        return [
            "last_30_minutes", "last_hour", "last_2_hours", "last_24_hours", 
            "last_3_days", "last_7_days", "last_30_days"
        ]
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported formats"""
        return ["value", "trend", "comparison", "distribution"]
    
    def create_semantic_json_example(self) -> Dict[str, Any]:
        """Create example semantic JSON structure"""
        return {
            "entity": "temperature",
            "aggregation": "average",
            "time_range": "last_3_days",
            "grouping": "by_day",
            "format": "trend"
        }
    
    def create_compound_semantic_json_example(self) -> Dict[str, Any]:
        """Create example compound semantic JSON structure"""
        return {
            "entity": ["soil_moisture", "water_usage", "humidity"],
            "aggregation": "average",
            "time_range": "last_7_days",
            "grouping": "by_day",
            "format": "comparison"
        }
