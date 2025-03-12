import os
import json
import base64
import requests
import logging
from datetime import datetime

# Api keys needed for the image upload to imgbb
keys_path = os.path.join(os.path.dirname(__file__), '..', 'keys.json')

# Log directory
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
log_file = os.path.join(log_dir, 'logs.log')

# Logger configure
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# FOrmat with timestamp
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(log_format)

logger.addHandler(file_handler)

class ImageUploader:
    def __init__(self):
        with open(keys_path) as f:
            keys = json.load(f)
            self.imgbb_api_key = keys["imgbb"]["api_key"]

    def get_imgbb_links(self, links, name, data, url):
        try:
            response = requests.post(url, data=data)
            response = response.json()
            success = response["success"]
            status = response["status"]

            if success:
                logger.info(f"Image {name} uploaded successfully")
                links[name] = response["data"]["url"]
            else:
                logger.error(f"Image {name} upload failed with status: {status}")
        except Exception as e:
            logger.error(f"Error uploading image {name}: {str(e)}")

    def upload_image(self):
        input_folder = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Input')
        images = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
        # print(images)

        # Encode images to base64
        encoded_images = {}
        for image in images:
            with open(os.path.join(input_folder, image), "rb") as img_file:
                encoded_images[image] = base64.b64encode(img_file.read()).decode('utf-8')

        expiration = 600 # 10 min

        url = f"https://api.imgbb.com/1/upload?expiration={expiration}&key={self.imgbb_api_key}"

        # Links for the images on imgbb
        links = {}
        for(image, encoded_image) in encoded_images.items():
            data = {"image": encoded_image}
            self.get_imgbb_links(links, image, data, url)

        # Return the links of the images which are now accessible for the LLMs
        return links
        

if __name__ == "__main__":
    imageUploader = ImageUploader()
    print(imageUploader.upload_image())
