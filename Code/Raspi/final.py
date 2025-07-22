import RPi.GPIO as GPIO
import serial
import time
import spidev
import cv2
from pymongo.mongo_client import MongoClient
import os 

# MongoDB setup
uri = "mongodb+srv://python:raspi123@sensors.g0oav.mongodb.net/?retryWrites=true&w=majority&appName=sensors"
client = MongoClient(uri)
db = client['sensor_data']  # Replace with your database name
sensor_collection = db['sensor_readings']  # Collection for all sensor data

# Check MongoDB connection before proceeding
try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit()

# Initialize serial communication for pH sensor
ph_serial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Adjust as necessary

# Initialize serial communication for NPK sensor
npk_serial = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
npk_query = bytearray([0x01, 0x03, 0x00, 0x1E, 0x00, 0x03, 0x65, 0xCD])  # MODBUS query

def read_moisture_sensor(channel=0):
    """
    Reads the analog value from the specified channel on the MCP3008 (Moisture Sensor) and maps it to a percentage.
    :param channel: int (0-7) - The ADC channel to read from (default is 0).
    :return: tuple - (raw ADC value, mapped percentage).
    """
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be an integer between 0 and 7.")

    # Initialize SPI connection
    spi = spidev.SpiDev()
    spi.open(0, 0)  # Open SPI port 0, device (CS) 0
    spi.max_speed_hz = 1350000  # Set SPI speed

    try:
        adc = spi.xfer2([1, (8 + channel) << 4, 0])
        raw_value = ((adc[1] & 3) << 8) + adc[2]  # Combine the two bytes to form the 10-bit ADC value
        percentage = 100 - int((raw_value / 1023.0) * 100)
        print(f"Moisture Sensor - Raw ADC Value: {raw_value}, Mapped Percentage: {percentage}%")
        return raw_value, percentage
    finally:
        spi.close()

def read_ph():
    """
    Reads and parses data from the pH sensor.
    :return: tuple - (pH value, depth, light value, temperature value)
    """
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
                    print(f"pH Sensor - pH: {ph_value}, Depth: {depth}, Light: {light_value}, Temperature: {temperature_value}")
                    return ph_value, depth, light_value, temperature_value
                except (IndexError, ValueError) as e:
                    print(f"Error parsing pH sensor data: {data}, Error: {e}")
        return None, None, None, None
    except Exception as e:
        print(f"pH sensor error: {e}")
        return None, None, None, None

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
            print(f"NPK Sensor - Nitrogen (N): {nitrogen} mg/kg, Phosphorus (P): {phosphorus} mg/kg, Potassium (K): {potassium} mg/kg")
            return nitrogen, phosphorus, potassium
        else:
            print("Invalid or incomplete response from NPK sensor.")
            return None, None, None
    except Exception as e:
        print(f"NPK sensor error: {e}")
        return None, None, None

def capture_image(retries=3):
    """
    Captures an image from the RTSP stream and saves it with a timestamped filename.
    Ensures the image file is actually saved to disk and the directory exists.
    :param retries: int - Number of retry attempts.
    :return: str - The filename of the saved image, or None if the capture failed.
    """
    image_dir = "images"
    os.makedirs(image_dir, exist_ok=True)  # Ensure 'images/' directory exists

    for attempt in range(retries):
        video = cv2.VideoCapture("rtsp://admin:VYMNOK@192.168.26.38:554/H.264")
        video.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        time.sleep(0.5)  # Stabilize connection
        ret, frame = video.read()
        if ret:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            image_filename = os.path.join(image_dir, f"image_{timestamp}.jpg")
            success = cv2.imwrite(image_filename, frame)
            video.release()

            if success and os.path.exists(image_filename) and os.path.getsize(image_filename) > 0:
                print(f"✅ Image successfully saved: {image_filename}")
                return image_filename
            else:
                print(f"⚠️ File write failed or image file invalid on attempt {attempt + 1}")
        else:
            print(f"⚠️ Frame not captured on attempt {attempt + 1}")
        video.release()
        time.sleep(1)

    print("❌ Failed to capture and save image after multiple attempts.")
    return None


def collect_and_store_data():
    """
    Gathers sensor data and stores it in MongoDB only after all sensors return data.
    """
    try:
        while True:
            # Initialize variables to ensure all sensors provide data
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
                    image_filename = capture_image()

                # Skip storing image if capture failed
                if image_filename is None:
                    print("Skipping image capture for this cycle.")
                    continue
                

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

            # Insert the combined document into MongoDB
            sensor_collection.insert_one(sensor_document)
            print("Sensor data written to MongoDB:", sensor_document)

            # Delay before the next reading cycle
            time.sleep(5)
    except KeyboardInterrupt:
        print("Data collection stopped by user.")
    finally:
        ph_serial.close()
        npk_serial.close()
        GPIO.cleanup()

# Start the data collection process
collect_and_store_data()
