import os
import json
from playwright.async_api import async_playwright
import datetime
import sys
import re
import time
import pathlib
import base64
from PIL import Image
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils.utils_general import util_render_and_screenshot


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


def clean_html_result(result):
    '''
        Output of LLMs can contain other stuff. Everything is deleted except <html> and everything between...
        If no final </html> is found, than just tkae the string
    '''
    pattern = re.compile(r"<!DOCTYPE html.*?(?:</html>|$)", re.DOTALL | re.IGNORECASE)
    try:
        clean_result = pattern.search(result).group(0)
        unescaped_html = clean_result.encode('utf-8').decode('unicode_escape')

        # Only remove backslashes before <, > and whitespaces
        cleaned_html = re.sub(r'\\(?=[<>\s])', '', unescaped_html)
    except Exception as e:
        print(f"Try again with this image. Error: {e}")
        cleaned_html = None

    return cleaned_html.strip()


def _get_page_size(driver, width=1280, max_height=15_000):
    """
        Gets the page size (height, width)
    """
    driver.set_window_size(width, 1000)

    # load page
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    height = driver.execute_script(
        "return Math.max(document.body.scrollHeight, "
        "document.documentElement.scrollHeight)"
    )
    return width, min(height, max_height)


def _determine_size(html1_path, html2_path):
    '''
        Determines the max size of the 2 HTMLs 
        Important to get a screenshot which has the same size
    '''

    options = Options()  
    options.add_argument("--headless")

    sizes = []
    for html in (html1_path, html2_path):
        d = webdriver.Chrome(options=options)
        try:
            d.get(pathlib.Path(html).resolve().as_uri())
            sizes.append(_get_page_size(d))
        finally:
            d.quit()
    
    max_w = max(w for w, h in sizes)
    max_h = max(h for w , h in sizes)
    return max_w, max_h



def _render_fullpage_with_screenshot(driver, image_path, dpr=1, target_width=1280, target_height=None):
    '''
        Private Helper function:
        Goal - get the full size of the website in order to take a correct screenshot
    '''
    driver.set_window_size(target_width, target_height or 1000)
    # sometimes scrolling is necessary to see full webpage
    scroll_count = 4

    # check dynamically if scroll necessar<
    prev_height = 0
    for i in range(scroll_count):
        time.sleep(0.2)
        temp_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")

        # if no furhter scroll necessary -> break
        if abs(temp_height - prev_height) < 5:
            break

        prev_height = temp_height
        
        desired_height = min(temp_height, target_height) if target_height else temp_height
        # check if height difference
        if desired_height > driver.get_window_size()["height"]:
            driver.set_window_size(target_width, desired_height )

    
    if target_height is None:
        options = {
            "fromSurface": True,
            "captureBeyondViewport": True
        }
    else:
        options = {
            "fromSurface": True,
            "captureBeyondViewport": False,
            "clip": {
                "x": 0, "y": 0,
                "width":  target_width  * dpr,
                "height": target_height * dpr,
                "scale": 1
            }
        }

    b64_encoded = driver.execute_cdp_cmd("Page.captureScreenshot", options)["data"]

    img = base64.b64decode(b64_encoded)

    if dpr != 1:
        im = Image.open(BytesIO(img))
        if im.width != target_width:
            ratio = target_width / im.width
            im = im.resize((target_width, int(im.height * ratio)), Image.LANCZOS)
        im.save(image_path)
    else:
        pathlib.Path(image_path).write_bytes(img)


def _take_screenshots(html_path, image_path, max_width, max_height):
    '''
        creates driver, loads html and then calls _render_fullpage_with_screenshot in order to 
        take a screenshot
    '''
    options = Options()
    options.add_argument('--headless')  
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(pathlib.Path(html_path).resolve().as_uri())
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")


        dp_ratio = driver.execute_script("return window.devicePixelRatio")
        _render_fullpage_with_screenshot(driver, image_path, dp_ratio, max_width, max_height)
    except Exception as e:
        print(f"Error for file {html_path.split("/")[-1]}: {e}")

    finally:
        driver.quit()


def save_screenshots(html_path, image_path, html2_path = None, image2_path = None):
    '''
        Take a screenshot of the *full* page.
    '''
    max_width=1280 
    max_height=None

    if(html2_path != None):
        max_width, max_height = _determine_size(html_path, html2_path)
        print("Pair Screenshot for File: ", html_path.split("/")[-1])
        _take_screenshots(html_path, image_path, max_width, max_height)
        _take_screenshots(html2_path, image2_path, max_width, max_height)
    else:
        print("Single Screenshot for File: ", html_path.split("/")[-1])
        _take_screenshots(html_path, image_path, max_width, max_height)


def _get_css(url: str, soup: BeautifulSoup):
    """
        Extracts CSS from the website and stores it in file
        Combines all CSS
    """
    combined_css = []

    for link in soup.find_all('link', rel='stylesheet'):
        link_url = link.get('href')
        if link_url:
            # do some join: https://stackoverflow.com/questions/10893374/python-confusions-with-urljoin
            css_url = urljoin(url, link_url)
            print(css_url)
            response_css = requests.get(css_url, timeout=10)
            if response_css.status_code == 200:
                combined_css.append(response_css.text)
            else:
                print(f"Error loading CSS from {css_url}")

            # delete link 
            link.decompose()
    
    # combined css into file
    if combined_css:
        style = soup.new_tag('style')
        style.string = "\n".join(combined_css)
        soup.head.insert(0, style)


def extract_html_css_from_website(url: str, output_html_path: pathlib.Path, store_html: bool = True):
    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        print ("""\n !!! Error: Unable to fetch the website !!!\n""")
    
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    _get_css(url, soup)

    if store_html:
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

    return str(soup)



def change_links_and_img(html: str) -> str:
    """
        Changes all the existing Link amd image src to a default value
        -> Links: href="#"
        -> Image: src="/src/placeholder.jpg"
    """
    # Alternative values
    image_src = "src/placeholder.jpg"
    href_src = "#"

    soup = BeautifulSoup(html, "html.parser")

    # image
    for image in soup.find_all("img", src=True):
        image["src"] = image_src
    
    # Links
    for link in soup.find_all("a", href=True):
        link["href"] = href_src
    
    return str(soup)


# Tests
if __name__ == "__main__":
    htmls_path = os.path.join(DIR_PATH, "..", "Data", "Input", "html")
    images_path = os.path.join(DIR_PATH, "..", "Data", "Input", "images")

    # for html_file in os.listdir(htmls_path):
    #     if html_file.endswith(".html"):
    #         html_path = os.path.join(htmls_path, html_file)
    #         image_path = os.path.join(images_path, f"{os.path.splitext(html_file)[0]}.png")
    #         save_screenshots(html_path, image_path)
    #         print(f"Screenshot saved for {html_file} at {image_path}")



    

    



