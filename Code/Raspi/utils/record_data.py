import os
import cv2
import time
import serial
import spidev
import RPi.GPIO as GPIO
from sensors.ph import read_ph
from sensors.npk import read_npk
from sensors.soilmoisture import read_moisture_sensor
from sensors.camera import capture_image
from logger import CustomLogger
logger = CustomLogger()


def collect_and_store_data(rtsp_url):
    """
    Gathers sensor data and stores it in MongoDB only after all sensors return data.
    """
    try:
        logger.info(f"\nStarting data collection")
        
        moisture_data = None
        ph_data = None
        npk_data = None
        image_filename = None

        # Loop until all sensors return valid data
        while moisture_data is None or ph_data is None or npk_data is None or image_filename is None:
            # Read moisture data
            if moisture_data is None:
                moisture_value, moisture_percentage = read_moisture_sensor()
                if moisture_value is not None:
                    moisture_data = (moisture_value, moisture_percentage)

            # Read pH sensor data
            if ph_data is None:
                ph_value, depth, light_value, temperature_value = read_ph()
                if ph_value is not None:
                    ph_data = (ph_value, depth, light_value, temperature_value)

            # Read NPK sensor data
            if npk_data is None:
                nitrogen, phosphorus, potassium = read_npk()
                if nitrogen is not None:
                    npk_data = (nitrogen, phosphorus, potassium)

            # Capture image
            if image_filename is None:
                image_filename = capture_image(rtsp_url)

            # In case image capture fails repeatedly, you can decide whether to break
            if image_filename is None:
                logger.warning("Skipping image capture for this cycle temporarily. Retrying...")

        # Create a combined document with all sensor data
        sensor_document = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),

            # Moisture
            "moisture_value": moisture_data[0],
            "moisture_percentage": moisture_data[1],

            # pH sensor
            "ph_value": ph_data[0],
            "depth": ph_data[1],
            "light": ph_data[2],
            "temperature": ph_data[3],

            # NPK
            "nitrogen": npk_data[0],
            "phosphorus": npk_data[1],
            "potassium": npk_data[2],

            # Image
            "image_filename": image_filename
        }
        logger.info(f"Sensor data written to MongoDB: {sensor_document}")
        return sensor_document

    except KeyboardInterrupt:
        logger.warning("Data collection stopped by user.")
    finally:
        GPIO.cleanup()
