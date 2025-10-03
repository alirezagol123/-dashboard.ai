"""
GraphQL Schema for Agriculture Semantic Layer
Provides GraphQL API for IrrigationEvent, EnvironmentControl, and PestDetection entities
"""

from graphene import ObjectType, String, Int, Float, Boolean, List, Field, Schema, DateTime
from graphene.types import Scalar
from typing import Dict, Any
import json
from datetime import datetime

# Custom DateTime scalar
class DateTime(Scalar):
    @staticmethod
    def serialize(dt):
        return dt.isoformat()

    @staticmethod
    def parse_literal(node):
        return datetime.fromisoformat(node.value)

    @staticmethod
    def parse_value(value):
        return datetime.fromisoformat(value)

# GraphQL Types
class IrrigationEventType(ObjectType):
    event_id = String()
    timestamp = DateTime()
    water_amount_liters = Float()
    irrigation_method = String()
    irrigation_duration_minutes = Int()
    status = String()

class EnvironmentControlType(ObjectType):
    control_id = String()
    timestamp = DateTime()
    temperature_celsius = Float()
    humidity_percent = Float()
    co2_ppm = Int()
    light_lux = Int()
    fan_status = Boolean()
    heater_status = Boolean()

class PestDetectionType(ObjectType):
    detection_id = String()
    timestamp = DateTime()
    pest_or_disease_type = String()
    severity_level = String()
    detected_by = String()
    recommended_action = String()

# Additional GraphQL Types for Complete Ontology Coverage
class SoilSensorType(ObjectType):
    sensor_id = String()
    timestamp = DateTime()
    soil_moisture_percent = Float()
    soil_ph_level = Float()
    soil_temperature_celsius = Float()

class PlantGrowthType(ObjectType):
    plant_id = String()
    timestamp = DateTime()
    plant_height_cm = Float()
    fruit_count = Int()
    fruit_size_cm = Float()
    leaf_count = Int()

class NutrientSensorType(ObjectType):
    sensor_id = String()
    timestamp = DateTime()
    nitrogen_level_ppm = Float()
    phosphorus_level_ppm = Float()
    potassium_level_ppm = Float()
    nutrient_uptake_mg_l = Float()

class EnvironmentalSensorType(ObjectType):
    sensor_id = String()
    timestamp = DateTime()
    pressure_hpa = Float()
    wind_speed_ms = Float()
    rainfall_mm = Float()
    motion_detected = Boolean()

class MarketDataType(ObjectType):
    market_id = String()
    timestamp = DateTime()
    tomato_price_per_kg = Float()
    lettuce_price_per_head = Float()
    pepper_price_per_kg = Float()
    demand_level_percent = Float()
    supply_level_percent = Float()
    cost_per_kg = Float()
    profit_margin_percent = Float()

class AnalyticsType(ObjectType):
    analytics_id = String()
    timestamp = DateTime()
    energy_usage_kwh = Float()
    water_efficiency_percent = Float()
    yield_prediction_kg = Float()
    yield_efficiency_percent = Float()
    fertilizer_usage_kg = Float()
    leaf_wetness_percent = Float()
    test_temperature_celsius = Float()

# Query Type
class Query(ObjectType):
    # Irrigation Events Queries
    irrigation_events = List(IrrigationEventType, limit=Int(), offset=Int())
    latest_irrigation_event = Field(IrrigationEventType)
    irrigation_events_today = List(IrrigationEventType)
    
    # Environment Controls Queries
    environment_controls = List(EnvironmentControlType, limit=Int(), offset=Int())
    latest_environment_control = Field(EnvironmentControlType)
    current_humidity = Float()
    current_temperature = Float()
    
    # Pest Detection Queries
    pest_detections = List(PestDetectionType, limit=Int(), offset=Int())
    pest_detections_today = List(PestDetectionType)
    high_severity_pest_detections = List(PestDetectionType)
    
    # Cross-entity queries
    farm_status = Field('FarmStatusType')
    
    # Soil Sensor Queries
    soil_sensors = List(SoilSensorType, limit=Int(), offset=Int())
    latest_soil_sensor = Field(SoilSensorType)
    current_soil_moisture = Float()
    current_soil_ph = Float()
    current_soil_temperature = Float()
    
    # Plant Growth Queries
    plant_growth_data = List(PlantGrowthType, limit=Int(), offset=Int())
    latest_plant_growth = Field(PlantGrowthType)
    current_plant_height = Float()
    current_fruit_count = Int()
    current_fruit_size = Float()
    current_leaf_count = Int()
    
    # Nutrient Sensor Queries
    nutrient_sensors = List(NutrientSensorType, limit=Int(), offset=Int())
    latest_nutrient_sensor = Field(NutrientSensorType)
    current_nitrogen_level = Float()
    current_phosphorus_level = Float()
    current_potassium_level = Float()
    current_nutrient_uptake = Float()
    
    # Environmental Sensor Queries
    environmental_sensors = List(EnvironmentalSensorType, limit=Int(), offset=Int())
    latest_environmental_sensor = Field(EnvironmentalSensorType)
    current_pressure = Float()
    current_wind_speed = Float()
    current_rainfall = Float()
    motion_detected = Boolean()
    
    # Market Data Queries
    market_data = List(MarketDataType, limit=Int(), offset=Int())
    latest_market_data = Field(MarketDataType)
    current_tomato_price = Float()
    current_lettuce_price = Float()
    current_pepper_price = Float()
    current_demand_level = Float()
    current_supply_level = Float()
    current_cost_per_kg = Float()
    current_profit_margin = Float()
    
    # Analytics Queries
    analytics_data = List(AnalyticsType, limit=Int(), offset=Int())
    latest_analytics = Field(AnalyticsType)
    current_energy_usage = Float()
    current_water_efficiency = Float()
    current_yield_prediction = Float()
    current_yield_efficiency = Float()
    current_fertilizer_usage = Float()
    current_leaf_wetness = Float()
    current_test_temperature = Float()
    
    def resolve_irrigation_events(self, info, limit=10, offset=0):
        """Get irrigation events with pagination"""
        # Mock data - replace with actual database query
        return [
            IrrigationEventType(
                event_id="irr_1",
                timestamp=datetime.now(),
                water_amount_liters=25.5,
                irrigation_method="drip",
                irrigation_duration_minutes=30,
                status="completed"
            ),
            IrrigationEventType(
                event_id="irr_2",
                timestamp=datetime.now(),
                water_amount_liters=15.0,
                irrigation_method="sprinkler",
                irrigation_duration_minutes=20,
                status="completed"
            )
        ][offset:offset + limit]
    
    def resolve_latest_irrigation_event(self, info):
        """Get the latest irrigation event"""
        return IrrigationEventType(
            event_id="irr_latest",
            timestamp=datetime.now(),
            water_amount_liters=25.5,
            irrigation_method="drip",
            irrigation_duration_minutes=30,
            status="completed"
        )
    
    def resolve_irrigation_events_today(self, info):
        """Get irrigation events from today"""
        return [
            IrrigationEventType(
                event_id="irr_today_1",
                timestamp=datetime.now(),
                water_amount_liters=25.5,
                irrigation_method="drip",
                irrigation_duration_minutes=30,
                status="completed"
            )
        ]
    
    def resolve_environment_controls(self, info, limit=10, offset=0):
        """Get environment control records with pagination"""
        return [
            EnvironmentControlType(
                control_id="env_1",
                timestamp=datetime.now(),
                temperature_celsius=24.5,
                humidity_percent=65.2,
                co2_ppm=420,
                light_lux=850,
                fan_status=True,
                heater_status=False
            ),
            EnvironmentControlType(
                control_id="env_2",
                timestamp=datetime.now(),
                temperature_celsius=25.1,
                humidity_percent=68.5,
                co2_ppm=435,
                light_lux=920,
                fan_status=True,
                heater_status=False
            )
        ][offset:offset + limit]
    
    def resolve_latest_environment_control(self, info):
        """Get the latest environment control record"""
        return EnvironmentControlType(
            control_id="env_latest",
            timestamp=datetime.now(),
            temperature_celsius=24.5,
            humidity_percent=65.2,
            co2_ppm=420,
            light_lux=850,
            fan_status=True,
            heater_status=False
        )
    
    def resolve_current_humidity(self, info):
        """Get current humidity level"""
        return 65.2
    
    def resolve_current_temperature(self, info):
        """Get current temperature"""
        return 24.5
    
    def resolve_pest_detections(self, info, limit=10, offset=0):
        """Get pest detection records with pagination"""
        return [
            PestDetectionType(
                detection_id="pest_1",
                timestamp=datetime.now(),
                pest_or_disease_type="Aphids",
                severity_level="high",
                detected_by="camera",
                recommended_action="Apply neem oil spray immediately"
            ),
            PestDetectionType(
                detection_id="pest_2",
                timestamp=datetime.now(),
                pest_or_disease_type="Leaf Spot",
                severity_level="medium",
                detected_by="sensor",
                recommended_action="Increase air circulation and reduce humidity"
            )
        ][offset:offset + limit]
    
    def resolve_pest_detections_today(self, info):
        """Get pest detections from today"""
        return [
            PestDetectionType(
                detection_id="pest_today_1",
                timestamp=datetime.now(),
                pest_or_disease_type="Aphids",
                severity_level="high",
                detected_by="camera",
                recommended_action="Apply neem oil spray immediately"
            )
        ]
    
    def resolve_high_severity_pest_detections(self, info):
        """Get high severity pest detections"""
        return [
            PestDetectionType(
                detection_id="pest_high_1",
                timestamp=datetime.now(),
                pest_or_disease_type="Aphids",
                severity_level="high",
                detected_by="camera",
                recommended_action="Apply neem oil spray immediately"
            )
        ]
    
    def resolve_farm_status(self, info):
        """Get overall farm status combining all entities"""
        return FarmStatusType(
            last_irrigation=datetime.now(),
            current_humidity=65.2,
            current_temperature=24.5,
            active_pests=1,
            system_status="healthy",
            # Additional fields to resolve ambiguous mappings
            current_soil_moisture=45.2,
            current_soil_ph=6.7,
            current_soil_temperature=22.3,
            current_plant_height=19.99,
            current_fruit_count=2,
            current_nitrogen_level=62.96,
            current_pressure=1004.81,
            current_wind_speed=10.26,
            current_rainfall=0.55,
            current_energy_usage=26.05,
            current_yield_prediction=105.50
        )
    
    # Soil Sensor Resolvers
    def resolve_soil_sensors(self, info, limit=10, offset=0):
        """Get soil sensor data with pagination"""
        return [
            SoilSensorType(
                sensor_id="soil_1",
                timestamp=datetime.now(),
                soil_moisture_percent=45.2,
                soil_ph_level=6.7,
                soil_temperature_celsius=22.3
            )
        ][offset:offset + limit]
    
    def resolve_latest_soil_sensor(self, info):
        """Get latest soil sensor reading"""
        return SoilSensorType(
            sensor_id="soil_latest",
            timestamp=datetime.now(),
            soil_moisture_percent=45.2,
            soil_ph_level=6.7,
            soil_temperature_celsius=22.3
        )
    
    def resolve_current_soil_moisture(self, info):
        """Get current soil moisture"""
        return 45.2
    
    def resolve_current_soil_ph(self, info):
        """Get current soil pH"""
        return 6.7
    
    def resolve_current_soil_temperature(self, info):
        """Get current soil temperature"""
        return 22.3
    
    # Plant Growth Resolvers
    def resolve_plant_growth_data(self, info, limit=10, offset=0):
        """Get plant growth data with pagination"""
        return [
            PlantGrowthType(
                plant_id="plant_1",
                timestamp=datetime.now(),
                plant_height_cm=19.99,
                fruit_count=2,
                fruit_size_cm=1.21,
                leaf_count=25
            )
        ][offset:offset + limit]
    
    def resolve_latest_plant_growth(self, info):
        """Get latest plant growth data"""
        return PlantGrowthType(
            plant_id="plant_latest",
            timestamp=datetime.now(),
            plant_height_cm=19.99,
            fruit_count=2,
            fruit_size_cm=1.21,
            leaf_count=25
        )
    
    def resolve_current_plant_height(self, info):
        """Get current plant height"""
        return 19.99
    
    def resolve_current_fruit_count(self, info):
        """Get current fruit count"""
        return 2
    
    def resolve_current_fruit_size(self, info):
        """Get current fruit size"""
        return 1.21
    
    def resolve_current_leaf_count(self, info):
        """Get current leaf count"""
        return 25
    
    # Nutrient Sensor Resolvers
    def resolve_nutrient_sensors(self, info, limit=10, offset=0):
        """Get nutrient sensor data with pagination"""
        return [
            NutrientSensorType(
                sensor_id="nutrient_1",
                timestamp=datetime.now(),
                nitrogen_level_ppm=62.96,
                phosphorus_level_ppm=34.97,
                potassium_level_ppm=95.59,
                nutrient_uptake_mg_l=50.0
            )
        ][offset:offset + limit]
    
    def resolve_latest_nutrient_sensor(self, info):
        """Get latest nutrient sensor reading"""
        return NutrientSensorType(
            sensor_id="nutrient_latest",
            timestamp=datetime.now(),
            nitrogen_level_ppm=62.96,
            phosphorus_level_ppm=34.97,
            potassium_level_ppm=95.59,
            nutrient_uptake_mg_l=50.0
        )
    
    def resolve_current_nitrogen_level(self, info):
        """Get current nitrogen level"""
        return 62.96
    
    def resolve_current_phosphorus_level(self, info):
        """Get current phosphorus level"""
        return 34.97
    
    def resolve_current_potassium_level(self, info):
        """Get current potassium level"""
        return 95.59
    
    def resolve_current_nutrient_uptake(self, info):
        """Get current nutrient uptake"""
        return 50.0
    
    # Environmental Sensor Resolvers
    def resolve_environmental_sensors(self, info, limit=10, offset=0):
        """Get environmental sensor data with pagination"""
        return [
            EnvironmentalSensorType(
                sensor_id="env_1",
                timestamp=datetime.now(),
                pressure_hpa=1004.81,
                wind_speed_ms=10.26,
                rainfall_mm=0.55,
                motion_detected=False
            )
        ][offset:offset + limit]
    
    def resolve_latest_environmental_sensor(self, info):
        """Get latest environmental sensor reading"""
        return EnvironmentalSensorType(
            sensor_id="env_latest",
            timestamp=datetime.now(),
            pressure_hpa=1004.81,
            wind_speed_ms=10.26,
            rainfall_mm=0.55,
            motion_detected=False
        )
    
    def resolve_current_pressure(self, info):
        """Get current atmospheric pressure"""
        return 1004.81
    
    def resolve_current_wind_speed(self, info):
        """Get current wind speed"""
        return 10.26
    
    def resolve_current_rainfall(self, info):
        """Get current rainfall"""
        return 0.55
    
    def resolve_motion_detected(self, info):
        """Get motion detection status"""
        return False
    
    # Market Data Resolvers
    def resolve_market_data(self, info, limit=10, offset=0):
        """Get market data with pagination"""
        return [
            MarketDataType(
                market_id="market_1",
                timestamp=datetime.now(),
                tomato_price_per_kg=2.71,
                lettuce_price_per_head=1.59,
                pepper_price_per_kg=3.40,
                demand_level_percent=75.0,
                supply_level_percent=80.0,
                cost_per_kg=2.50,
                profit_margin_percent=25.0
            )
        ][offset:offset + limit]
    
    def resolve_latest_market_data(self, info):
        """Get latest market data"""
        return MarketDataType(
            market_id="market_latest",
            timestamp=datetime.now(),
            tomato_price_per_kg=2.71,
            lettuce_price_per_head=1.59,
            pepper_price_per_kg=3.40,
            demand_level_percent=75.0,
            supply_level_percent=80.0,
            cost_per_kg=2.50,
            profit_margin_percent=25.0
        )
    
    def resolve_current_tomato_price(self, info):
        """Get current tomato price"""
        return 2.71
    
    def resolve_current_lettuce_price(self, info):
        """Get current lettuce price"""
        return 1.59
    
    def resolve_current_pepper_price(self, info):
        """Get current pepper price"""
        return 3.40
    
    def resolve_current_demand_level(self, info):
        """Get current demand level"""
        return 75.0
    
    def resolve_current_supply_level(self, info):
        """Get current supply level"""
        return 80.0
    
    def resolve_current_cost_per_kg(self, info):
        """Get current cost per kg"""
        return 2.50
    
    def resolve_current_profit_margin(self, info):
        """Get current profit margin"""
        return 25.0
    
    # Analytics Resolvers
    def resolve_analytics_data(self, info, limit=10, offset=0):
        """Get analytics data with pagination"""
        return [
            AnalyticsType(
                analytics_id="analytics_1",
                timestamp=datetime.now(),
                energy_usage_kwh=26.05,
                water_efficiency_percent=81.15,
                yield_prediction_kg=105.50,
                yield_efficiency_percent=86.40,
                fertilizer_usage_kg=0.38,
                leaf_wetness_percent=45.0,
                test_temperature_celsius=25.0
            )
        ][offset:offset + limit]
    
    def resolve_latest_analytics(self, info):
        """Get latest analytics data"""
        return AnalyticsType(
            analytics_id="analytics_latest",
            timestamp=datetime.now(),
            energy_usage_kwh=26.05,
            water_efficiency_percent=81.15,
            yield_prediction_kg=105.50,
            yield_efficiency_percent=86.40,
            fertilizer_usage_kg=0.38,
            leaf_wetness_percent=45.0,
            test_temperature_celsius=25.0
        )
    
    def resolve_current_energy_usage(self, info):
        """Get current energy usage"""
        return 26.05
    
    def resolve_current_water_efficiency(self, info):
        """Get current water efficiency"""
        return 81.15
    
    def resolve_current_yield_prediction(self, info):
        """Get current yield prediction"""
        return 105.50
    
    def resolve_current_yield_efficiency(self, info):
        """Get current yield efficiency"""
        return 86.40
    
    def resolve_current_fertilizer_usage(self, info):
        """Get current fertilizer usage"""
        return 0.38
    
    def resolve_current_leaf_wetness(self, info):
        """Get current leaf wetness"""
        return 45.0
    
    def resolve_current_test_temperature(self, info):
        """Get current test temperature"""
        return 25.0

# Farm Status Type for cross-entity queries
class FarmStatusType(ObjectType):
    last_irrigation = DateTime()
    current_humidity = Float()
    current_temperature = Float()
    active_pests = Int()
    system_status = String()
    # Additional fields to resolve ambiguous mappings
    current_soil_moisture = Float()
    current_soil_ph = Float()
    current_soil_temperature = Float()
    current_plant_height = Float()
    current_fruit_count = Int()
    current_nitrogen_level = Float()
    current_pressure = Float()
    current_wind_speed = Float()
    current_rainfall = Float()
    current_energy_usage = Float()
    current_yield_prediction = Float()

# Mutation Type for creating records
class CreateIrrigationEvent(ObjectType):
    class Arguments:
        water_amount_liters = Float(required=True)
        irrigation_method = String(required=True)
        irrigation_duration_minutes = Int(required=True)
        status = String(required=True)
    
    irrigation_event = Field(IrrigationEventType)
    
    def mutate(self, info, water_amount_liters, irrigation_method, irrigation_duration_minutes, status):
        # Mock creation - replace with actual database operation
        irrigation_event = IrrigationEventType(
            event_id=f"irr_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            water_amount_liters=water_amount_liters,
            irrigation_method=irrigation_method,
            irrigation_duration_minutes=irrigation_duration_minutes,
            status=status
        )
        return CreateIrrigationEvent(irrigation_event=irrigation_event)

class CreateEnvironmentControl(ObjectType):
    class Arguments:
        temperature_celsius = Float(required=True)
        humidity_percent = Float(required=True)
        co2_ppm = Int(required=True)
        light_lux = Int(required=True)
        fan_status = Boolean()
        heater_status = Boolean()
    
    environment_control = Field(EnvironmentControlType)
    
    def mutate(self, info, temperature_celsius, humidity_percent, co2_ppm, light_lux, fan_status=False, heater_status=False):
        # Mock creation - replace with actual database operation
        environment_control = EnvironmentControlType(
            control_id=f"env_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            temperature_celsius=temperature_celsius,
            humidity_percent=humidity_percent,
            co2_ppm=co2_ppm,
            light_lux=light_lux,
            fan_status=fan_status,
            heater_status=heater_status
        )
        return CreateEnvironmentControl(environment_control=environment_control)

class CreatePestDetection(ObjectType):
    class Arguments:
        pest_or_disease_type = String(required=True)
        severity_level = String(required=True)
        detected_by = String(required=True)
        recommended_action = String(required=True)
    
    pest_detection = Field(PestDetectionType)
    
    def mutate(self, info, pest_or_disease_type, severity_level, detected_by, recommended_action):
        # Mock creation - replace with actual database operation
        pest_detection = PestDetectionType(
            detection_id=f"pest_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            pest_or_disease_type=pest_or_disease_type,
            severity_level=severity_level,
            detected_by=detected_by,
            recommended_action=recommended_action
        )
        return CreatePestDetection(pest_detection=pest_detection)

class Mutation(ObjectType):
    create_irrigation_event = CreateIrrigationEvent.Field()
    create_environment_control = CreateEnvironmentControl.Field()
    create_pest_detection = CreatePestDetection.Field()

# Create GraphQL Schema
schema = Schema(query=Query, mutation=Mutation)

# Sample GraphQL Queries
SAMPLE_QUERIES = {
    "irrigation": [
        """
        query GetLatestIrrigation {
            latestIrrigationEvent {
                eventId
                timestamp
                waterAmountLiters
                irrigationMethod
                status
            }
        }
        """,
        """
        query GetIrrigationToday {
            irrigationEventsToday {
                eventId
                timestamp
                waterAmountLiters
                irrigationMethod
                irrigationDurationMinutes
            }
        }
        """,
        """
        query GetIrrigationEvents($limit: Int, $offset: Int) {
            irrigationEvents(limit: $limit, offset: $offset) {
                eventId
                timestamp
                waterAmountLiters
                irrigationMethod
                status
            }
        }
        """
    ],
    "environment": [
        """
        query GetCurrentHumidity {
            currentHumidity
        }
        """,
        """
        query GetCurrentTemperature {
            currentTemperature
        }
        """,
        """
        query GetLatestEnvironment {
            latestEnvironmentControl {
                controlId
                timestamp
                temperatureCelsius
                humidityPercent
                co2Ppm
                lightLux
                fanStatus
                heaterStatus
            }
        }
        """
    ],
    "pest": [
        """
        query GetPestDetectionsToday {
            pestDetectionsToday {
                detectionId
                timestamp
                pestOrDiseaseType
                severityLevel
                detectedBy
                recommendedAction
            }
        }
        """,
        """
        query GetHighSeverityPests {
            highSeverityPestDetections {
                detectionId
                timestamp
                pestOrDiseaseType
                severityLevel
                recommendedAction
            }
        }
        """,
        """
        query GetPestDetections($limit: Int, $offset: Int) {
            pestDetections(limit: $limit, offset: $offset) {
                detectionId
                timestamp
                pestOrDiseaseType
                severityLevel
                detectedBy
            }
        }
        """
    ],
    "cross_entity": [
        """
        query GetFarmStatus {
            farmStatus {
                lastIrrigation
                currentHumidity
                currentTemperature
                activePests
                systemStatus
            }
        }
        """,
        """
        query GetCompleteFarmData {
            latestIrrigationEvent {
                eventId
                timestamp
                waterAmountLiters
                status
            }
            latestEnvironmentControl {
                controlId
                timestamp
                temperatureCelsius
                humidityPercent
                fanStatus
            }
            pestDetectionsToday {
                detectionId
                pestOrDiseaseType
                severityLevel
            }
        }
        """
    ]
}

# Natural Language to GraphQL Mapping
NATURAL_LANGUAGE_MAPPING = {
    "When was the last irrigation?": """
        query GetLatestIrrigation {
            latestIrrigationEvent {
                timestamp
                waterAmountLiters
                irrigationMethod
            }
        }
    """,
    "What is the current humidity?": """
        query GetCurrentHumidity {
            currentHumidity
        }
    """,
    "What pests have been detected today?": """
        query GetPestDetectionsToday {
            pestDetectionsToday {
                pestOrDiseaseType
                severityLevel
                recommendedAction
            }
        }
    """,
    "Show me irrigation events from last week": """
        query GetIrrigationEvents {
            irrigationEvents(limit: 10) {
                eventId
                timestamp
                waterAmountLiters
                irrigationMethod
            }
        }
    """,
    "What is the temperature now?": """
        query GetCurrentTemperature {
            currentTemperature
        }
    """,
    "Are the fans running?": """
        query GetLatestEnvironment {
            latestEnvironmentControl {
                fanStatus
                heaterStatus
            }
        }
    """,
    "Show me high severity pest detections": """
        query GetHighSeverityPests {
            highSeverityPestDetections {
                detectionId
                pestOrDiseaseType
                severityLevel
                recommendedAction
            }
        }
    """
}

if __name__ == "__main__":
    # Test the schema
    print("GraphQL Schema created successfully!")
    print("\nSample Queries:")
    for category, queries in SAMPLE_QUERIES.items():
        print(f"\n{category.upper()}:")
        for query in queries:
            print(f"  {query.strip()}")
    
    print("\nNatural Language Mapping:")
    for nl_query, graphql_query in NATURAL_LANGUAGE_MAPPING.items():
        print(f"\nNL: {nl_query}")
        print(f"GraphQL: {graphql_query.strip()}")
