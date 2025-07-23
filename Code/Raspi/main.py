import os 
import cv2
import time
import serial
import spidev
import RPi.GPIO as GPIO
from pymongo.mongo_client import MongoClient
from utils.record_data import collect_and_store_data
from config import DefaultConfig

DefaultConfig.initialise()
logger = DefaultConfig.logger
logger.info("Initializing MongoDB connection...")
client = MongoClient(DefaultConfig.URI)
db = client[DefaultConfig.db_name]
collection = db[DefaultConfig.collection_name]
rtsp_url = DefaultConfig.rtsp_url
try:
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB.")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    exit()

def write_sensor_data(num_cycles, rtsp_url):
    """
    Writes the sensor data document to MongoDB for a specified number of cycles.
    :param num_cycles: int - The number of data collection cycles to perform.
    """
    for cycle in range(num_cycles):
        try:
            sensor_document = collect_and_store_data(rtsp_url)
            collection.insert_one(sensor_document)
            logger.info(f"Cycle {cycle + 1}/{num_cycles}: Sensor data written to MongoDB: {sensor_document}")
        except Exception as e:
            logger.error(f"Cycle {cycle + 1}/{num_cycles}: Error writing sensor data to MongoDB: {e}")

if __name__ == "__main__":
    try:
        logger.info("Starting sensor data collection program...")
        # Get the number of readings from the user
        n_readings = int(input("Enter the number of sensor reading cycles to perform: "))
        logger.info(f"User requested {n_readings} sensor reading cycles")
        
        if n_readings <= 0:
            logger.warning("Number of cycles must be positive. Exiting program.")
            exit()
            
    except ValueError as e:
        logger.error(f"Invalid input received: {e}. Exiting program.")
        exit()
    except KeyboardInterrupt:
        logger.info("Program interrupted by user. Exiting gracefully.")
        exit()

    # Start the data collection process with the specified number of cycles
    logger.info(f"Starting data collection for {n_readings} cycles...")
    write_sensor_data(n_readings, rtsp_url)
    logger.info("Data collection completed successfully.")