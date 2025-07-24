import os
import time
import cv2
from utils.logger import CustomLogger

logger = CustomLogger()
def capture_image(rtsp_url, retries=3):
    """
    Captures an image from the RTSP stream and saves it with a timestamped filename.
    Ensures the image file is actually saved to disk and the directory exists.
    :param rtsp_url: str - The RTSP URL of the camera stream.
    :param retries: int - Number of retry attempts.
    :return: str - The filename of the saved image, or None if the capture failed.
    """
    image_dir = "images"
    os.makedirs(image_dir, exist_ok=True)  # Ensure 'images/' directory exists

    for attempt in range(retries):
        logger.info(f"Attempting to capture image from RTSP stream (Attempt {attempt + 1}/{retries})")
        video = cv2.VideoCapture(rtsp_url)
        video.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        time.sleep(0.5)  # Stabilize connection
        ret, frame = video.read()
        if ret:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            image_filename = os.path.join(image_dir, f"image_{timestamp}.jpg")
            success = cv2.imwrite(image_filename, frame)
            video.release()

            if success and os.path.exists(image_filename) and os.path.getsize(image_filename) > 0:
                logger.info(f"✅ Image successfully saved: {image_filename}")
                return image_filename
            else:
                logger.warning(f"⚠️ File write failed or image file invalid on attempt {attempt + 1}")
        else:
            logger.warning(f"⚠️ Frame not captured on attempt {attempt + 1}")
        video.release()
        time.sleep(1)

    logger.error("❌ Failed to capture and save image after multiple attempts.")
    return None