import RPi.GPIO as GPIO
import serial
import time
import threading

# Moisture sensor setup
moisture_channel = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(moisture_channel, GPIO.IN)

# pH sensor setup
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Adjust as necessary

# Flag to control thread execution
running = True

# Function to read moisture sensor
def read_moisture():
    try:
        while running:
            moisture_value = GPIO.input(moisture_channel)
            print(f"Moisture Value: {moisture_value}")  # Display the moisture value
            if moisture_value == 0:
                print("Moisture Detected!")
            elif moisture_value == 1:
                print("No Moisture Detected!")
            else:
                print("Error in reading moisture value!")
            time.sleep(1)
    except Exception as e:
        print(f"Moisture sensor error: {e}")

# Function to read pH sensor data
def read_ph():
    try:
        while running:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()
                
                # Check if the data starts with "PH:"
                if data.startswith('PH:'):
                    # Remove the labels and split the data by commas
                    try:
                        # Split by commas
                        parts = data.split(',')

                        # Extract each part by splitting at ':'
                        ph_value = parts[0].split(':')[1].strip()
                        depth = parts[1].split(':')[1].strip()
                        light_value = parts[2].split(':')[1].strip()
                        temperature_value = parts[3].split(':')[1].strip()

                        # Print the parsed values
                        print(f"pH: {ph_value}, Depth: {depth}, Light: {light_value}, Temperature: {temperature_value}")
                    except (IndexError, ValueError) as e:
                        print(f"Error parsing data: {data}, Error: {e}")
            time.sleep(1)
    except Exception as e:
        print(f"pH sensor error: {e}")
    finally:
        ser.close()

# Start threads for each sensor
moisture_thread = threading.Thread(target=read_moisture)
ph_thread = threading.Thread(target=read_ph)

# Start the threads
ph_thread.start()
time.sleep(3)
moisture_thread.start()


try:
    # Keep the main thread alive to handle keyboard interrupt
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping sensor readings...")
    running = False  # Stop both threads when keyboard interrupt is detected

# Wait for both threads to complete
moisture_thread.join()
ph_thread.join()

# Cleanup GPIO when finished
GPIO.cleanup()
print("Program terminated gracefully.")
