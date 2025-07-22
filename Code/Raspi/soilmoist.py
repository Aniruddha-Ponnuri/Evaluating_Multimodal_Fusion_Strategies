import spidev  # For SPI communication
from time import sleep  # For delay

def read_mcp3008(channel=0):
    """
    Reads the analog value from the specified channel on the MCP3008 and maps it to a percentage.
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
        # MCP3008 communication to read data
        adc = spi.xfer2([1, (8 + channel) << 4, 0])
        raw_value = ((adc[1] & 3) << 8) + adc[2]  # Combine the two bytes to form the 10-bit ADC value

        # Map raw value to percentage
        percentage = 100 - int((raw_value / 1023.0) * 100)
        return raw_value, percentage

    finally:
        spi.close()  # Ensure SPI connection is closed

# Continuously read values until KeyboardInterrupt
if __name__ == "__main__":
    try:
        print("Reading MCP3008 values. Press Ctrl+C to exit.")
        while True:
            raw, percent = read_mcp3008()
            print(f"Raw ADC Value: {raw}, Mapped Percentage: {percent}%")
            sleep(0.5)  # Delay for readability
    except KeyboardInterrupt:
        print("\nExiting on user request.")
    except Exception as e:
        print(f"Error: {e}")
