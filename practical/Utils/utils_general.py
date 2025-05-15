from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from pathlib import Path
import json
import base64
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from LLMs.Strategies.openaiStrategy import OpenAIStrategy
from LLMs.Strategies.geminiStrategy import GeminiStrategy
from LLMs.Strategies.llamaStrategy import LlamaStrategy
from LLMs.Strategies.qwenStrategy import QwenStrategy


def util_load_keys(source):
    '''
        Util-Functions for API-Calls
    '''
    config_path = Path(__file__).resolve().parent.parent / "keys.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        keys_json = json.load(f)

    api_key = keys_json[source]["api_key"]

    return api_key



def util_save_code(code, file_name="generated_code.html"):
    '''
        API-Call and store code
    '''
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Code stored as {file_name}")




def util_validate_html(generatedHtml_path):
    '''
        Util-Functions for HTML/CSS Analysis
        Check first if any compiler errors
    '''
    try:
        soup = BeautifulSoup(generatedHtml_path, "html.parser")
        return True
    except Exception as e:
        print("HTML error:", e)
        return False



async def util_render_and_screenshot(generatedHtml_path, screenshot_path):
    '''
        Util-Functions for Images & Screenshots
        Rendering the code and doing a screenshot of it afterwards (headless)

        other browsers: "firefox" oder "webkit".
    '''
    async with async_playwright() as playwright:
        chromium = playwright.chromium 
        browser = await chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"file://{os.path.abspath(generatedHtml_path)}")
        await page.screenshot(path=screenshot_path, full_page=True)
        await browser.close()

    print(f"Screenshot saved in {screenshot_path}")



def util_encode_image_b64(self, image_data):
    '''
        b64 encoding of images
    '''
    b64_img = base64.b64encode(image_data).decode("utf-8")
    
    return b64_img



def cutColorChannels(image):
    '''
        needed for SSIM - only 3 color channels necessary, 4th channel is alpha and can be deleted
    '''
    if(image.shape[2] == 4):
        return image[:, :, :3]


def get_model_strategy(name):
    '''
        Returns strategy of the model and right parameter which can be used later
        TODO Add other models

        externally_hosted:
        True: Image is externally hosted, e.g. https://de.imgbb.com or https://imgur.com -> Only link is given as input
        False: Image is stored locally and b64 encoded. It is attached to this prompt.
    '''
    
    match name:
        case "openai":
            strategy = OpenAIStrategy(api_key=util_load_keys("openai"))
            return strategy
        case "gemini":
            strategy = GeminiStrategy(api_key=util_load_keys("gemini"))
            return strategy
        case "llama":
            strategy = LlamaStrategy()
            return strategy
        case "qwen":
            strategy = QwenStrategy()
            return strategy
        case _:
            raise ValueError(f"Model {name} not supported.")



