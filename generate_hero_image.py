import cv2
import numpy as np

# Create a blank image with gradient background
width = 800
height = 600
image = np.zeros((height, width, 3), dtype=np.uint8)

# Create gradient background
for i in range(height):
    color = int(255 * (1 - i/height))  # Fade from white to blue
    image[i, :] = [color, color, 255]

# Add some decorative elements
cv2.circle(image, (width//2, height//2), 150, (255, 255, 255), 2)
cv2.circle(image, (width//2, height//2), 100, (255, 255, 255), 2)
cv2.circle(image, (width//2, height//2), 50, (255, 255, 255), 2)

# Add text
font = cv2.FONT_HERSHEY_SIMPLEX
cv2.putText(image, 'AuthAI', (width//2 - 100, height//2), font, 2, (255, 255, 255), 2)
cv2.putText(image, 'Face Recognition', (width//2 - 150, height//2 + 50), font, 1, (255, 255, 255), 2)

# Save the image
cv2.imwrite('static/images/hero-image.png', image)
print("Hero image generated successfully!") 