import os
import json
import base64
import requests
import logging
from datetime import datetime

# Api keys needed for the image upload to imgbb
KEYS_PATH = os.path.join(os.path.dirname(__file__), '..', 'keys.json')
# Expiration time for the image on imgbb
EXPIRATION = 600 # 10 min

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
        with open(KEYS_PATH) as f:
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


    def upload_single_image(self, image_path):
        try:
            image_name = os.path.basename(image_path)

            with open(image_path, "rb") as file:
                encoded_image = base64.b64encode(file.read()).decode('utf-8')
            
            
            url = f"https://api.imgbb.com/1/upload?expiration={EXPIRATION}&key={self.imgbb_api_key}"

            data = {"image": encoded_image}
            links = {}
            self.get_imgbb_links(links, image_name, data, url)
            
            if image_name in links:
                return links
            
            return None
        except Exception as e:
            logger.error(f"Error uploading single image {image_path}: {str(e)}")
            return None


    def upload_images(self):
        input_folder = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Input')
        links = {}

        try:
            images = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
            # print(images)
            for image in images:
                image_path = os.path.join(input_folder, image)
                image_url = self.upload_single_image(image_path)

                if image_url:
                    links[image] = image_url

        except Exception as e:
            logger.error(f"Error with Images: {str(e)}")
            return {}
        
        return links
        

if __name__ == "__main__":
    imageUploader = ImageUploader()
    print(imageUploader.upload_image())
