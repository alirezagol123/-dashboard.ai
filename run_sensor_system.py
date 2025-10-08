#!/usr/bin/env python3
"""
Run the complete integrated sensor system
This script runs the raw sensor generator + data pipeline automatically
"""

import asyncio
import sys
import os
import logging
import signal

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_sensor_system import IntegratedSensorSystem

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s")
logger = logging.getLogger("run_sensor_system")

async def main():
    """Main function to run the integrated sensor system"""
    logger.info("Smart Agriculture Sensor System")
    logger.info("Raw Data Generation -> Validation -> Normalization -> Clean Database")
    
    # Initialize the integrated system
    system = IntegratedSensorSystem()
    
    try:
        # Run the complete system
        await system.run_integrated_system()
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.exception("System error: %s", e)
    finally:
        # Graceful shutdown
        logger.info("Shutting down integrated sensor system...")
        try:
            # Stop the pipeline to flush remaining data
            if hasattr(system, 'pipeline') and hasattr(system.pipeline, 'stop'):
                system.pipeline.stop()
                logger.info("Pipeline stopped and data flushed")
        except Exception as e:
            logger.error("Error stopping pipeline: %s", e)
        
        # Show final statistics
        logger.info("Final System Statistics:")
        try:
            status = system.get_system_status()
            if status:
                logger.info("Raw data records: %s", status.get('raw_data_count', 0))
                logger.info("Processed records: %s", status.get('processed_data_count', 0))
                logger.info("Unprocessed records: %s", status.get('unprocessed_count', 0))
                
                pipeline_stats = status.get('pipeline_stats', {})
                logger.info("Pipeline success rate: %.1f%%", pipeline_stats.get('success_rate', 0))
                logger.info("Valid records: %s", pipeline_stats.get('processed', 0))
                logger.info("Rejected records: %s", pipeline_stats.get('rejected', 0))
        except Exception as e:
            logger.error("Error getting system status: %s", e)
        
        logger.info("Data saved to: smart_dashboard.db")
        logger.info("Your AI assistant will analyze the clean data from sensor_data table!")

def handle_signals(loop, system):
    """Handle shutdown signals gracefully"""
    def signal_handler():
        logger.info("Received shutdown signal, stopping system...")
        loop.create_task(system.stop() if hasattr(system, 'stop') else asyncio.sleep(0))
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except (NotImplementedError, OSError):
            # Windows doesn't support signal handlers the same way
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("Fatal error: %s", e)
