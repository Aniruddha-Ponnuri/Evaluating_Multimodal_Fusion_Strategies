import serial

# Adjust the port and baud rate according to your setup
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            #print(f"Received: {data}")

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
finally:
    ser.close()
