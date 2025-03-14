from datasets import load_dataset
from huggingface_hub import login
from PIL import Image
import os
import json
import asyncio
from playwright.async_api import async_playwright
import os 

'''
Important: 
SALt-NLP/Design2Code-hf -> 77.6 MB
xcodemind/webcode2m -> 1.1 TB
'''
DATASETS = ["SALT-NLP/Design2Code-hf", "biglab/webui-7k-elements", "xcodemind/webcode2m"]
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
IMAGE_PATH = f"{DIR_PATH}/Data/images"
HTML_PATH = f"{DIR_PATH}/Data/code"

async def process_html_file(html_path):
    # Browser Session
    async with async_playwright() as p:
        # TODO: Check if size of screen correct
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{os.path.abspath(html_path)}")

        # DOM
        dom_html = await page.content()

        # List Elemente
        elements = await page.query_selector_all("*")

        # TODO: CHeck again if correct
        bounding_boxes = []
        # for elem in elements:
        #     box = await elem.bounding_box()
        #     tag_name = await elem.evaluate("(el) => el.tagName")
        #     # ggf. aria-label, alt etc. abrufen
        #     aria_label = await elem.get_attribute("aria-label")
        #     bounding_boxes.append({
        #         "tag": tag_name,
        #         "bbox": box,
        #         "ariaLabel": aria_label,
        #     })

        # Accessibility-Snapshot
        a11y_snapshot = await page.accessibility.snapshot()

        # TODO: Here axe-core
        
        await browser.close()

    return dom_html, bounding_boxes, a11y_snapshot


async def main():
    # Api key for huggingface
    keys_path = os.path.join(DIR_PATH, '..', 'keys.json')
    with open(keys_path) as f:
        huggingface_token = json.load(f)["huggingface"]["api_key"]

    login(huggingface_token)

    dataset = load_dataset(DATASETS[0], split="train", streaming=True)

    # Counter as ID
    counter = 1

    for example in dataset:
        img = example["image"]
        # img.show()
        text = example["text"]

        # Save image and html
        path = f"{DIR_PATH}/{counter}"
        img.save(f"{path}.png")
        with open(f"{path}.html", "w") as f:
            f.write(text)

        dom_html, bounding_boxes, a11y_snapshot = await process_html_file(f"{path}.html")


        counter += 1
        # Break after first
        break


if __name__ == "__main__":
    asyncio.run(main())