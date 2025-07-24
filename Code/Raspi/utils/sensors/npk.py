import RPi.GPIO as GPIO
import serial
import time
from utils.logger import CustomLogger

logger = CustomLogger()
npk_serial = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
npk_query = bytearray([0x01, 0x03, 0x00, 0x1E, 0x00, 0x03, 0x65, 0xCD]) 

def read_npk():
    """
    Reads and parses data from the NPK sensor.
    :return: tuple - (Nitrogen, Phosphorus, Potassium)
    """
    try:
        npk_serial.write(npk_query)
        time.sleep(0.15)

        response = npk_serial.read(11)

        if len(response) == 11 and response[0] == 0x01 and response[1] == 0x03 and response[2] == 0x06:
            nitrogen = (response[3] << 8) | response[4]
            phosphorus = (response[5] << 8) | response[6]
            potassium = (response[7] << 8) | response[8]
            logger.info(f"NPK Sensor - Nitrogen (N): {nitrogen} mg/kg, Phosphorus (P): {phosphorus} mg/kg, Potassium (K): {potassium} mg/kg")
            return nitrogen, phosphorus, potassium
        else:
            logger.warning("Invalid or incomplete response from NPK sensor.")
            return None, None, None
    except Exception as e:
        logger.error(f"NPK sensor error: {e}")
        return None, None, None
