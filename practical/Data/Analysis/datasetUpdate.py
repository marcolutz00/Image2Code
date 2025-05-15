import os
import re
import json
import copy
from selenium import webdriver 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import time
import pathlib
import base64
from PIL import Image
from io import BytesIO



DIR_PATH = os.path.dirname(os.path.realpath(__file__))
HTML_PATH= os.path.join(DIR_PATH, '..', 'Input', 'html')
JSON_PATH= os.path.join(DIR_PATH, '..', 'Input', 'json', 'manual')
IMAGE_PATH = os.path.join(DIR_PATH, '..', 'Input', 'images')


'''
    Due to the design of the Datasets which we are using, the <a> in each Data Entry
    does not contain a href attribute.
    This leads to problems concerning some Wcag Standards.
    In order to solve those issues by design, we are going to add an empty href="#" 
    for each <a>
'''

def add_empty_href(html):
    '''
      Regex whcich checks if already a href attribute exists or not.
      If not, add an empty attribute
    '''

    return re.sub(r'(<a\b)(?![^>]*\bhref\s*=)', r'\1 href="#"', html, flags=re.IGNORECASE)

def update_html_href():
    '''
        Reads an changes html files
    '''

    for file in os.listdir(HTML_PATH):
        if os.path.isdir(os.path.join(HTML_PATH, file)) or file.startswith("."):
            continue

        with open(os.path.join(HTML_PATH, file), 'r', encoding='utf-8') as f:
            html = f.read()
        
        adjusted_html = add_empty_href(html)

        with open(os.path.join(HTML_PATH, file), 'w', encoding='utf-8') as w:
            w.write(adjusted_html)
        




def update_json_manual_checks(json_file_path, amount_manual_checks):
    '''
        Within the generated accessibility json for each file, a user has to set check some of the issues 
        manually. 
        After checking them and using the corresponding values, this method sets the correct 
        values for 'total_checks' and 'failed_checks'. Those values are important in order to 
        correctly calculate the accessibility benchmark.

        Updates manual overview of checks (fields: 'total_SC' and 'failed_SC') per json file
    '''
    with open(json_file_path, 'r') as fr:
        original_data = json.load(fr)
        data = copy.deepcopy(original_data)

        amount_passed = 0
        amount_failed = 0

        if "manual" in data and "checks" in data["manual"]:
            for check_id, status in data["manual"]["checks"].items():
                if status.lower() == "pass":
                    amount_passed += 1
                elif status.lower() == "fail":
                    amount_failed += 1
                else: 
                    raise ValueError(f"Unknown status: {status} for check ID: {check_id}")
        
        # Check if amount correct
        assert amount_failed + amount_passed == amount_manual_checks

        data["manual"]["total_checks"] = amount_failed + amount_passed
        data["manual"]["failed_checks"] = amount_failed

    # check if structure and content remains the same, apart from manual
    original_data_without_manual = copy.deepcopy(original_data)
    if "manual" in original_data_without_manual:
        del original_data_without_manual["manual"]

    data_without_manual = copy.deepcopy(data)
    if "manual" in data_without_manual:
        del data_without_manual["manual"]

    assert original_data_without_manual == data_without_manual

    with open(json_file_path, 'w') as fw:
        json.dump(data, fw)



def _render_fullpage(driver, out_image_path, dpr=1):
    '''
        Private Helper function:
        Goal - get the full size of the website in order to take a correct screenshot
    '''
    WIDTH = 1280
    MAX_HEIGHT = 15000 # just random height
    SCROLL_COUNT = 4 

    driver.set_window_size(WIDTH, 1000)
    prev_height = 0

    # check dynamically if scroll necessary
    for i in range(SCROLL_COUNT):
        time.sleep(0.3)
        temp_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")

        # check if only little height difference
        if abs(temp_height - prev_height) < 5:
            break

        driver.set_window_size(WIDTH, min(temp_height, MAX_HEIGHT))
        prev_height = temp_height

    b64_encoded = driver.execute_cdp_cmd("Page.captureScreenshot", {"fromSurface": True, "captureBeyondViewport": True})["data"]

    img = base64.b64decode(b64_encoded)

    if dpr != 1:
        im = Image.open(BytesIO(img))
        if im.width != WIDTH:
            ratio = WIDTH / im.width
            im = im.resize((WIDTH, int(im.height * ratio)), Image.LANCZOS)
        im.save(out_image_path)
    else:
        pathlib.Path(out_image_path).write_bytes(img)


def update_images():
    '''
        Since some of the images do not reflect the html to 100%, it is neccessary to 
        take screenshots again.
        Example: Blue Boxes from design2code, instead of images
    '''
    new_image_dir = os.path.join(IMAGE_PATH)

    if not os.path.exists(new_image_dir):
        os.makedirs(new_image_dir)  

    for file in os.listdir(HTML_PATH):
        if os.path.isdir(os.path.join(HTML_PATH, file)) or file.startswith("."):
            continue

        basename = file.split(".")[0]

        print("Image for File: ", basename)

        options = Options()
        options.add_argument('--headless')  
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(pathlib.Path(os.path.join(HTML_PATH, file)).resolve().as_uri())

            WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")


            dp_ratio = driver.execute_script("return window.devicePixelRatio")
            _render_fullpage(driver, os.path.join(new_image_dir, f"{basename}.png"), dp_ratio)


        except Exception as e:
            print(f"Error for file {file}: {e}")

        finally:
            driver.quit()






def main():
    # manual_checks = 7

    # for file in os.listdir(JSON_PATH):
    #     update_json_manual_checks(os.path.join(JSON_PATH, file), manual_checks)

    update_images()


if __name__ == "__main__":
    main()