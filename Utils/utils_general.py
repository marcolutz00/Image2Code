from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from pathlib import Path
import json
import base64
import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LLMs.Strategies.openaiApiStrategy import OpenAIStrategy
from LLMs.Strategies.geminiApiStrategy import GeminiStrategy
from LLMs.Strategies.llamaLocalStrategy import LlamaStrategy
from LLMs.Strategies.qwenLocalStrategy import QwenStrategy
from LLMs.Strategies.hfFinetunedStrategy import HfFinetunedStrategy
from LLMs.Strategies.hfEndpointStrategy import HfEndpointStrategy



def read_html(html_path: str) -> str:
    """
    Reads HTML file and returns content
    """
    with open(html_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def read_json(json_path: str) -> dict:
    """
    Reads JSON file and returns content
    """
    with open(json_path, 'r', encoding='utf-8') as file:
        return json.load(file)


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


def util_save_json(data_json, file_path):
    '''
        Store json in file path
    '''
    with open(file_path, "w") as f:
        json.dump(data_json, f, ensure_ascii=False, indent=2)




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



def get_model_strategy(name):
    '''
        Returns strategy of the model and right parameter which can be used later
        TODO Add other models
    '''
    
    match name:
        case "openai":
            strategy = OpenAIStrategy(api_key=util_load_keys("openai"))
            return strategy
        case "gemini":
            strategy = GeminiStrategy(api_key=util_load_keys("gemini"))
            return strategy
        case "llama_local":
            strategy = LlamaStrategy()
            return strategy
        case "llama_hf":
            endpoint_llama = None
            strategy = HfEndpointStrategy(endpoint_llama)
            return strategy
        case "qwen_local":
            strategy = QwenStrategy()
            return strategy
        case "qwen_hf":
            with open(Path(__file__).resolve().parent.parent / "keys.json", "r", encoding="utf-8") as f:
                endpoint_qwen = json.load(f)["huggingface"]["endpoint_qwen"]
            strategy = HfEndpointStrategy(endpoint_qwen)
            return strategy
        case "finetuned_hf":
            strategy = HfFinetunedStrategy()
            return strategy
        case _:
            raise ValueError(f"Model {name} not supported.")


def util_create_dir_structure():
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

def util_create_directories(output_path, model, prompt_strategy, date):
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






if __name__ == "__main__":
    # Example usage
    # util_create_dir_structure()
    pass