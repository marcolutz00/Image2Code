import os
import json
import base64
import requests

keys_path = os.path.join(os.path.dirname(__file__), '..', 'keys.json')

with open(keys_path) as f:
    keys = json.load(f)
    imgbb_api_key = keys["imgbb"]["api_key"]

print(imgbb_api_key)

# Load images from data folder
input_folder = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Input')
images = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]

print(images)

# Encode images to base64
encoded_images = {}
for image in images:
    with open(os.path.join(input_folder, image), "rb") as img_file:
        encoded_images[image] = base64.b64encode(img_file.read()).decode('utf-8')

# print(encoded_images["test_youtube.png"])

# Upload images to imgbb
expiration = 600 # 10 min

url = f"https://api.imgbb.com/1/upload?expiration={expiration}&key={imgbb_api_key}"


data = {"image": encoded_images["test_youtube.png"]}
response = requests.post(url, data=data)

print(response.json())
