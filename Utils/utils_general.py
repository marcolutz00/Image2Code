from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from pathlib import Path
import json
import base64
import os
import sys
import shutil
import re
import pandas as pd


    
def read_json(json_path: str) -> dict:
    """
    Reads JSON file and returns content
    """
    with open(json_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    

def save_json(data_json, file_path):
    '''
        Store json in file path
    '''
    with open(file_path, "w") as f:
        json.dump(data_json, f, ensure_ascii=False, indent=2)


def clean_json_result(result):
    '''
        Finds the json array inside a string and returns it.
    '''
    pattern = re.compile(r"\[\s*\{.*?\}\s*\]", re.DOTALL)

    json_pattern = pattern.search(result)
    if json_pattern:
        json_result_raw = json_pattern.group(0)
        try:
            json_result_clean = json.loads(json_result_raw)
            return json_result_clean

        except Exception as e:
            print(f"Error cleaning JSON result : {e}")

    return None


def load_keys(source):
    '''
        Util-Functions for API-Calls
    '''
    config_path = Path(__file__).resolve().parent.parent / "keys.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        keys_json = json.load(f)

    api_key = keys_json[source]["api_key"]

    return api_key



def save_code(code, file_name="generated_code.html"):
    '''
        API-Call and store code
    '''
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Code stored as {file_name}")




async def render_and_screenshot(generatedHtml_path, screenshot_path):
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



def encode_image_b64(self, image_data):
    '''
        b64 encoding of images
    '''
    b64_img = base64.b64encode(image_data).decode("utf-8")
    
    return b64_img



def create_dir_structure():
    '''
        Creates the necessary folder structures for the project
    '''
    base = Path(__file__).resolve().parent.parent
    data_path = base / "Data"
    input_path = data_path / "Input"
    output_path = data_path / "Output"

    # placeholder.jpg
    placeholder_path = base / "Utils" /"placeholder.jpg"

    # Create if not exist
    input_path.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)

    (input_path / "images").mkdir(parents=True, exist_ok=True)
    (input_path / "html" / "src").mkdir(parents=True, exist_ok=True)
    shutil.copy(placeholder_path, input_path / "html" / "src" / "placeholder.jpg")

    models = ["openai", "gemini", "llama", "qwen"]
    sub_folders = ["accessibility", "html", "images", "insights"]
    prompt_strategies = ["naive", "zero-shot", "few-shot", "reason"]

    for model in models:
        for sub_folder in sub_folders:
            (output_path / model / sub_folder).mkdir(parents=True, exist_ok=True)
            for prompt_strategy in prompt_strategies:
                (output_path / model / sub_folder / prompt_strategy).mkdir(parents=True, exist_ok=True)
                if sub_folder == "html":
                    (output_path / model / sub_folder / prompt_strategy / "src").mkdir(parents=True, exist_ok=True)
                    shutil.copy(placeholder_path, output_path / model / sub_folder / prompt_strategy / "src" / "placeholder.jpg")

    print("Directory structure created successfully!")


def create_directories(output_path, model, prompt_strategy, date):
    '''
        Create the necessary directories for the output
    '''

    output_base_html_path = os.path.join(output_path, model, 'html')
    output_base_accessibility_path = os.path.join(output_path, model, 'accessibility')
    output_base_images_path = os.path.join(output_path, model, 'images')
    output_base_insights_path = os.path.join(output_path, model, 'insights')

    output_html_path = os.path.join(output_base_html_path, prompt_strategy, date)
    output_accessibility_path = os.path.join(output_base_accessibility_path, prompt_strategy, date)
    output_images_path = os.path.join(output_base_images_path, prompt_strategy, date)
    output_insights_path = os.path.join(output_base_insights_path, prompt_strategy, date)

    # Create directories if they do not exist
    os.makedirs(output_html_path, exist_ok=True)
    os.makedirs(output_accessibility_path, exist_ok=True)
    os.makedirs(output_images_path, exist_ok=True)
    os.makedirs(output_insights_path, exist_ok=True)

    # move placeholder.jpt to html folder
    placeholder_path = os.path.join(os.path.dirname(__file__), 'placeholder.jpg')
    placeholder_src_path = os.path.join(output_html_path, 'src')
    os.makedirs(placeholder_src_path, exist_ok=True)
    shutil.copy(placeholder_path, placeholder_src_path)

    return output_base_html_path, output_base_accessibility_path, output_base_images_path, output_base_insights_path

def _flatten_dict(dictionary, parent_key=""):
    """
    Helper to flatten dictionary
    """
    seperator = '.'
    flat_dict = {}

    for key, value in dictionary.items():
        new_key = f"{parent_key}{seperator}{key}" if parent_key else str(key)
        # if dict, then it could be further nested
        if isinstance(value, dict):
            flat_dict.update(_flatten_dict(value, new_key))
        else:
            flat_dict[new_key] = value
    return flat_dict


def export_dict_to_excel(dictionary, name, out_path):
    """
        Saves dictionary in excel
    """

    with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
        # 1) Landmarks ─ ein eindimensionales Dict: als Serie speichern
        flat_dict = _flatten_dict(dictionary)
        pd.Series(flat_dict, name="value").to_excel(writer, sheet_name=name)

    print(f"Wrote to excel file: {out_path}")





if __name__ == "__main__":
    # Example usage
    # util_create_dir_structure()
    pass