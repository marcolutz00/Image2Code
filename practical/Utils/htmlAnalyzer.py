from PIL import Image
import os
import json
from playwright.async_api import async_playwright
import os 
import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from practical.Utils.utils import util_render_and_screenshot


DIR_PATH = os.path.dirname(os.path.realpath(__file__))



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


    return dom_html, bounding_boxes, accessibility_tree


async def create_data_entry(name, html_path, llm_output):
    # 1. Analyze HTML
    dom_html, bounding_boxes, accessibility_tree = await process_html_file(html_path)

    data = {
        "general": {
            "source": html_path,
            "date": datetime.datetime.now().isoformat()
        },
        "dom": dom_html,
        "bounding_boxes": bounding_boxes,
        "accessibility_tree": accessibility_tree
    }

    html_dir = os.path.dirname(html_path)

    json_dir = os.path.join(html_dir, '..', 'json')
    json_path = os.path.join(json_dir, f"{name}.json")

    with open(json_path, "w") as f:
        json.dump(data, f)

    # 2. Do screenshot -> only necessary if LLM-Output
    if llm_output:
        image_path = os.path.join(html_dir, '..', 'images', f"{name}.png")
        await util_render_and_screenshot(html_path, image_path)


    return data


