from datasets import load_dataset
from huggingface_hub import login
from PIL import Image
import os
import json
import sys 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import practical.Utils.htmlAnalyzer as htmlAnalyzer

'''
Important: 
SALt-NLP/Design2Code-hf -> 77.6 MB -> https://huggingface.co/datasets/SALT-NLP/Design2Code-hf
xcodemind/webcode2m -> 1.1 TB
'''
DATASETS = ["SALT-NLP/Design2Code-hf", "biglab/webui-7k-elements", "xcodemind/webcode2m"]
CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
KEYS_PATH = os.path.join(CURRENT_DIR_PATH, '..', 'keys.json')
INPUT_PATH = os.path.join(CURRENT_DIR_PATH, '..', 'Data', 'Input')


async def login_hugging_face():
    with open(KEYS_PATH) as f:
        huggingface_token = json.load(f)["huggingface"]["api_key"]

    login(huggingface_token)



async def load_and_store_dataset(dataset_name="SALT-NLP/Design2Code-hf"):
    # login
    await login_hugging_face()

    dataset = load_dataset(dataset_name, split="train", streaming=True)

    # Counter as ID per data entry
    counter = 1

    for data_entry in dataset:
        # Image / Screenshots
        img = data_entry["image"]
        # img.show()
        
        # HTML/CSS
        html = data_entry["text"]

        # Save image and html
        image_path = os.path.join(INPUT_PATH, 'images', f"{counter}")
        html_dir = os.path.join(INPUT_PATH, 'html')
        html_path = os.path.join(html_dir, f"{counter}.html")

        img.save(f"{image_path}.png")

        with open(html_path, "w") as f:
            f.write(html)

        # Analyze HTML
        await htmlAnalyzer.create_data_entry(counter, html_dir)

        counter += 1

        # Test: Break after first
        break