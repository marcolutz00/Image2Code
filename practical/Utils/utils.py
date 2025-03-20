from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from pathlib import Path
import json
import base64
import os
from . import tokenCounter as tc

'''
    Util-Functions for API-Calls
'''
# Load Keys
def util_load_keys(company):
    config_path = Path(__file__).resolve().parent.parent / "keys.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        keys_json = json.load(f)

    api_key = keys_json[company]

    return api_key


# API-Call and store code
def util_save_code(code, file_name="generated_code.html"):
    # Store as HTML
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Code gespeichert als {file_name}")


'''
    Util-Functions for HTML/CSS Analysis
'''
# Check first if any compiler errors
def util_validate_html(generatedHtml_path):
    # check if mistakes
    try:
        soup = BeautifulSoup(generatedHtml_path, "html.parser")
        return True
    except Exception as e:
        print("HTML error:", e)
        return False


'''
    Util-Functions for Images & Screenshots
'''
# Rendering the code and doing a screenshot of it afterwards (headless)
async def util_render_and_screenshot(generatedHtml_path, screenshot_path):
    async with async_playwright() as playwright:
        chromium = playwright.chromium # other: "firefox" oder "webkit".
        browser = await chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"file://{os.path.abspath(generatedHtml_path)}")
        await page.screenshot(path=screenshot_path, full_page=True)
        await browser.close()

    print(f"Screenshot saved in {screenshot_path}")


# Some improvements for the b64 encoding
def util_encode_image(self, image_data):
    b64_img = base64.b64encode(image_data).decode("utf-8")

    amount_of_token = tc.count_tokens(b64_img, self.used_model)
    print(f"Amount of token {amount_of_token}")
    
    return b64_img


# needed for SSIM - only 3 color channels necessary, 4th channel is alpha and can be deleted
def cutColorChannels(image):
    if(image.shape[2] == 4):
        return image[:, :, :3]


