import spidev  # For SPI communication
import RPi.GPIO as GPIO
import serial
import time
import threading
from time import sleep

# Flag to control thread execution
running = True

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
        percentage = int((raw_value / 1023.0) * 100)
        print(f"Moisture Sensor - Raw ADC Value: {raw_value}, Mapped Percentage: {percentage}%")
        return raw_value, percentage
    finally:
        spi.close()

def read_ph():
    """
    Reads and parses data from the pH sensor.
    """
    try:
        if ph_serial.in_waiting > 0:
            data = ph_serial.readline().decode('utf-8').strip()

            if data.startswith('PH:'):
                try:
                    parts = data.split(',')
                    ph_value = parts[0].split(':')[1].strip()
                    depth = parts[1].split(':')[1].strip()
                    light_value = parts[2].split(':')[1].strip()
                    temperature_value = parts[3].split(':')[1].strip()
                    print(f"pH Sensor - pH: {ph_value}, Depth: {depth}, Light: {light_value}, Temperature: {temperature_value}")
                except (IndexError, ValueError) as e:
                    print(f"Error parsing pH sensor data: {data}, Error: {e}")
    except Exception as e:
        print(f"pH sensor error: {e}")

def read_npk():
    """
    Reads and parses data from the NPK sensor.
    """
    try:
        npk_serial.write(npk_query)
        time.sleep(0.15)

        response = npk_serial.read(11)
        # Uncomment the line below for raw debugging purposes
        # print("NPK Sensor - Raw Response:", response.hex())

        if len(response) == 11 and response[0] == 0x01 and response[1] == 0x03 and response[2] == 0x06:
            nitrogen = (response[3] << 8) | response[4]
            phosphorus = (response[5] << 8) | response[6]
            potassium = (response[7] << 8) | response[8]
            print(f"NPK Sensor - Nitrogen (N): {nitrogen} mg/kg, Phosphorus (P): {phosphorus} mg/kg, Potassium (K): {potassium} mg/kg")
        else:
            print("Invalid or incomplete response from NPK sensor.")
    except Exception as e:
        print(f"NPK sensor error: {e}")

def reading():
    """
    Main function to handle sensor readings sequentially.
    """
    global running
    try:
        print("Starting sensor readings. Press Ctrl+C to exit.")

        while running:
            read_moisture_sensor(0)
            time.sleep(1)  # Allow time between readings

            read_ph()
            time.sleep(1)  # Allow time between readings

            read_npk()
            time.sleep(1)  # Allow time between readings

    except KeyboardInterrupt:
        print("Stopping sensor readings...")
        running = False

    # Cleanup GPIO
    GPIO.cleanup()
    print("Program terminated gracefully.")

if __name__ == "__main__":
    reading()
