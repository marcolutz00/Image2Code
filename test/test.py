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
NODE_MODULES_PATH = f"/usr/local/lib/node_modules"

# Use axe-core, infos here: https://hackmd.io/@gabalafou/ByvwfEC0j
AXE_CORE_PATH = "/usr/local/lib/node_modules/axe-core/axe.min.js"


async def process_html_file(html_path):
    # Browser Session
    async with async_playwright() as p:
        # TODO: Check if size of screen correct
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{os.path.abspath(html_path)}")

        # 1. DOM
        dom_html = await page.content()

        # List Elemente
        elements = await page.query_selector_all("*")

        # 2. Bounding-Boxes
        bounding_boxes = []
        for element in elements:
            # get bounding box, tag name and aria-label for each element
            bounding_box = await element.bounding_box()
            tag_name = await element.evaluate("(elem) => elem.tagName")
            aria_label = await element.get_attribute("aria-label")

            # All information into dict
            bounding_boxes.append({
                "tag": tag_name,
                "bbox": bounding_box,
                "ariaLabel": aria_label,
            })

        # 3. Accessibility Tree
        # Accessibility-Snapshot - Infos here: https://ambient.digital/wissen/blog/a11y-was-ist-das/
        accessibility_tree = await page.accessibility.snapshot()

        # 4. Violations
        # 4.1 Axe-Core
        # axe-core inject
        await page.add_script_tag(path=AXE_CORE_PATH)
        axe_results = await page.evaluate("""
            async () => {
                return await axe.run();
            }
        """)

        axe_violations = axe_results["violations"]

        # 4.2 TODO: Other violations: Add them manually or semi-manually (WAVE, ...)
        # Alternatively: Some Tools (e.g. WAVE) need webserver -> Use Ngrok for short-term hosting
        
        await browser.close()

    return dom_html, bounding_boxes, accessibility_tree, axe_violations


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

        dom_html, bounding_boxes, accessibility_tree, axe_violations = await process_html_file(f"{path}.html")


        counter += 1
        # Break after first
        break


if __name__ == "__main__":
    asyncio.run(main())