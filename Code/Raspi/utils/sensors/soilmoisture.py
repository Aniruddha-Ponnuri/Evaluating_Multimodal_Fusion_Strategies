import RPi.GPIO as GPIO
import spidev
from logger import CustomLogger

logger = CustomLogger()
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
        logger.info(f"Moisture Sensor - Raw ADC Value: {raw_value}, Mapped Percentage: {percentage}%")
        return raw_value, percentage
    except Exception as e:
        logger.error(f"Error reading moisture sensor on channel {channel}: {e}")
        raise
    finally:
        spi.close()