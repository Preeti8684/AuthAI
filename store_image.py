import os
import base64

def store_image(username, image_data):
    folder = "saved_faces"
    if not os.path.exists(folder):
        os.makedirs(folder)

    image_path = os.path.join(folder, f"{username}.jpg")

    with open(image_path, "wb") as img_file:
        img_file.write(base64.b64decode(image_data))

    return image_path
