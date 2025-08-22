import os
import base64

def retrieve_image(username):
    image_path = f"saved_faces/{username}.jpg"
    if not os.path.exists(image_path):
        return None

    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")
