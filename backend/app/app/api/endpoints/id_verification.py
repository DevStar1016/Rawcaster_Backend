import cv2
import numpy as np

def skin_detection(image_path):
    # Load the image
    img = cv2.imread(image_path)

    # Convert image to YCrCb color space
    img_ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)

    # Define skin color range in YCrCb
    lower_skin = np.array([0, 133, 77], dtype=np.uint8)
    upper_skin = np.array([255, 173, 127], dtype=np.uint8)

    # Masking the image to detect skin color within the defined range
    skin_mask = cv2.inRange(img_ycrcb, lower_skin, upper_skin)
    result = cv2.bitwise_and(img, img, mask=skin_mask)

    # Checking the percentage of skin color in the image
    total_pixels = np.prod(img.shape[:2])
    skin_pixels = cv2.countNonZero(skin_mask)
    skin_percentage = (skin_pixels / total_pixels) * 100

    return skin_percentage

# Example usage
image_path = 'path/to/your/image.jpg'
percentage_skin = skin_detection(image_path)

# Define a threshold for skin percentage to determine abusive content
threshold = 1.0  # Set your preferred threshold

if percentage_skin > threshold:
    print("Abusive content (skin detected).")
else:
    print("No abusive content detected.")
