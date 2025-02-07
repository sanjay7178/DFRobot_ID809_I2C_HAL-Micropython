#!/usr/bin/env python3

from dfrobot_id809 import ID809, LEDMode, LEDColor
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize sensor
        logger.info("Initializing sensor...")
        sensor = ID809()
        
        # Initial delay after initialization
        time.sleep(1)

        # Test connection
        logger.info("Testing connection...")
        if not sensor.is_connected():
            logger.error("Sensor not connected!")
            return

        logger.info("Sensor connected successfully")

        # Test LED sequence
        logger.info("Running LED test sequence...")
        
        # Test different LED colors
        colors = [
            (LEDColor.RED, "RED"),
            (LEDColor.GREEN, "GREEN"),
            (LEDColor.BLUE, "BLUE"),
            (LEDColor.YELLOW, "YELLOW")
        ]
        
        for color, name in colors:
            logger.info(f"Testing LED color: {name}")
            if sensor.control_led(LEDMode.KEEPS_ON, color):
                logger.info(f"Successfully set LED to {name}")
            else:
                logger.error(f"Failed to set LED to {name}")
            time.sleep(1)

        # Final state - breathing blue
        logger.info("Setting LED to breathing blue...")
        if sensor.control_led(LEDMode.BREATHING, LEDColor.BLUE):
            logger.info("Successfully set LED to breathing blue")
        else:
            logger.error("Failed to set LED to breathing blue")

        logger.info("Test complete")

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    main()
