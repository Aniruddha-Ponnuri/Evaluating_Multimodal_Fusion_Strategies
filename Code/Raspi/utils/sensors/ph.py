import RPi.GPIO as GPIO
import serial
from utils.logger import CustomLogger

logger = CustomLogger()

# Initialize serial communication for pH sensor
ph_serial = None

def initialize_ph_sensor():
    """
    Initialize the pH sensor serial connection.
    """
    global ph_serial
    try:
        if ph_serial is None or not ph_serial.is_open:
            ph_serial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
            logger.info("pH sensor serial connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize pH sensor: {e}")
        ph_serial = None

def read_ph():
    """
    Reads and parses data from the pH sensor.
    :return: tuple - (pH value, depth, light value, temperature value)
    """
    global ph_serial
    
    # Ensure sensor is initialized
    if ph_serial is None or not ph_serial.is_open:
        initialize_ph_sensor()
    
    if ph_serial is None:
        return None, None, None, None
    
    try:
        if ph_serial.in_waiting > 0:
            data = ph_serial.readline().decode('utf-8').strip()

            if data.startswith('PH:'):
                try:
                    parts = data.split(',')
                    ph_value = float(parts[0].split(':')[1].strip())
                    depth = float(parts[1].split(':')[1].strip())
                    light_value = float(parts[2].split(':')[1].strip())
                    temperature_value = float(parts[3].split(':')[1].strip())
                    logger.info(f"pH Sensor - pH: {ph_value}, Depth: {depth}, Light: {light_value}, Temperature: {temperature_value}")
                    return ph_value, depth, light_value, temperature_value
                except (IndexError, ValueError) as e:
                    logger.error(f"Error parsing pH sensor data: {data}, Error: {e}")
        return None, None, None, None
    except Exception as e:
        logger.error(f"pH sensor error: {e}")
        # Try to reinitialize on error
        try:
            if ph_serial and ph_serial.is_open:
                ph_serial.close()
        except:
            pass
        ph_serial = None
        return None, None, None, None

def close_ph_sensor():
    """
    Close the pH sensor serial connection.
    """
    global ph_serial
    try:
        if ph_serial and ph_serial.is_open:
            ph_serial.close()
            logger.info("pH sensor serial connection closed")
    except Exception as e:
        logger.error(f"Error closing pH sensor: {e}")
    finally:
        ph_serial = None