import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.LLMs.LLMClient import LLMClient
from LLMs.Strategies.openaiStrategy import OpenAIStrategy
from ImageUpload.imageUploader import ImageUploader
import practical.Utils.utils_html as utils_html
import asyncio

KEYS_PATH = os.path.join(os.path.dirname(__file__), 'keys.json')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'Data')
INPUT_PATH = os.path.join(DATA_PATH, 'Input')
OUTPUT_PATH = os.path.join(DATA_PATH, 'Output')
MODEL = "openai"


def get_prompt():
    # Prompt for LLm
    return ("Please convert the following image into HTML/CSS. "
            "Please copy everything you see, including header, nav-bars, elements, style, text, color, components and more. "
            "Return the generated HTML/CSS without any further description or text. "
            "The image is externally hosted and can be found via the following URL.")


def load_api_key(model):
    # API-Key for model
    with open(KEYS_PATH) as f:
        keys = json.load(f)
        return keys[model]["api_key"]


def upload_image(single_image=True, image_path=None):
    # Upload either one image or all images in path
    uploader = ImageUploader()
    
    if single_image and image_path:
        return uploader.upload_single_image(image_path)
    else:
        return uploader.upload_images()


async def process_image(client, image_name, link, prompt, externally_hosted=True):
    # LLM processes iamge and generates code 

    # Generate code
    result = await client.generate_frontend_code(prompt, link, externally_hosted)
    
    base_name = os.path.splitext(image_name)[0]
    output_dir = os.path.join(OUTPUT_PATH, MODEL, 'html')
    
    # Store result
    output_html_path = os.path.join(output_dir, f"{base_name}.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(result)
    
    print(f"Result for {image_name} stored here: {output_html_path}")
    
    return result


async def analyze_outputs(image_name):
    ''''
        Analyze outputs: 
        1. Structural Similarity. Create Accessibility-Tree, Bounding-Boxes, DOM-Similarity, Code-Quality
        2. Visual Similarity: Create Screenshots 
    '''
    # get basename
    image_name = os.path.splitext(image_name)[0]

    # 1. Structural Similarity
    input_html_path = os.path.join(INPUT_PATH, 'html', f"{image_name}.html")
    output_html_path = os.path.join(OUTPUT_PATH, MODEL, 'html', f"{image_name}.html")

    # Create DOM, Bounding-Boxes, Accessibility-Tree, Accessibility Violations of Input and Output
    await utils_html.create_data_entry(image_name, input_html_path, False)
    await utils_html.create_data_entry(image_name, output_html_path, True)

    # TODO: Now use Benchmarks to compare the two outputs



async def main():
    # 1. Load prompt
    prompt = get_prompt()
    
    # 2. Load API-Key and define model strategy
    api_key = load_api_key(MODEL)
    strategy = OpenAIStrategy(api_key=api_key)
    
    # 3. Upload image(s)
    image_externally_hosted = True

    image_dir = os.path.join(INPUT_PATH, 'images')
    test_image = os.path.join(image_dir, '1.png')

    # image_information = upload_image(single_image=True, image_path=test_image)
    
    # 4. Create LLM-Client for model strategy
    client = LLMClient(strategy)
    
    # 5. Let LLMs create code out of image(s)
    # for image_name, link in image_information.items():
    #     result = await process_image(client, image_name, link, prompt, image_externally_hosted)
    #     print(f"Short summary: {result[:50]} ... (see more in path)")

    #     # 6. Analyze outputs for Input & Output
    #     await analyze_outputs(image_name)
    

    # Tests:
    await analyze_outputs('1.png')


if __name__ == "__main__":
    asyncio.run(main())