import sys
import os
import json
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.LLMs.LLMClient import LLMClient
from LLMs.Strategies.openaiStrategy import OpenAIStrategy
from LLMs.Strategies.geminiStrategy import GeminiStrategy
from ImageUpload.imageUploader import ImageUploader
import practical.Utils.utils_html as utils_html
import asyncio

KEYS_PATH = os.path.join(os.path.dirname(__file__), 'keys.json')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'Data')
INPUT_PATH = os.path.join(DATA_PATH, 'Input')
OUTPUT_PATH = os.path.join(DATA_PATH, 'Output')


def _get_prompt(externally_hosted):
    '''
        returns prompt
    '''

    # base = """Please convert the following image into HTML/CSS. 
    #         Please copy everything you see, including header, nav-bars, elements, style, text, color, components and more.
    #         Return the generated HTML/CSS without any further description or text. """
    base = """Please describe what you see on the image."""
    
    # Prompt for LLm
    if externally_hosted:
        return (base + "The image is externally hosted and can be found via the following URL.")
    else:
        return (base + "The image is encoded and is attached to this prompt.")


def _load_api_key(model):
    '''
        loads api_key
    '''
    # API-Key for model
    with open(KEYS_PATH) as f:
        keys = json.load(f)
        return keys[model]["api_key"]


def _upload_image(single_image=True, image_path=None):
    '''
        Upload either one image or all images in path to IMGBB 
    '''
    uploader = ImageUploader()
    
    if single_image and image_path:
        return uploader.upload_single_image(image_path)
    else:
        return uploader.upload_images()


async def _process_image(client, image_information, prompt, model):
    '''
        Sends API-CAll to LLM and lets it create output.
        The Output is then stored to the Output Directory
    '''
    result = await client.generate_frontend_code(prompt, image_information)
    
    output_dir = os.path.join(OUTPUT_PATH, model, 'html')
    
    output_html_path = os.path.join(output_dir, f"{image_information["name"]}.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(result)
    
    print(f"Result for {image_information["name"]}.html stored here: {output_html_path}")
    
    return result


async def _analyze_outputs(image_name, model):
    ''''
        Analyze outputs: 
        1. Structural Similarity. Create Accessibility-Tree, Bounding-Boxes, DOM-Similarity, Code-Quality
        2. Visual Similarity: Create Screenshots 
    '''
    # get basename
    image_name = os.path.splitext(image_name)[0]

    # 1. Structural Similarity
    input_html_path = os.path.join(INPUT_PATH, 'html', f"{image_name}.html")
    output_html_path = os.path.join(OUTPUT_PATH, model, 'html', f"{image_name}.html")

    # Create DOM, Bounding-Boxes, Accessibility-Tree, Accessibility Violations of Input and Output
    await utils_html.create_data_entry(image_name, input_html_path, False)
    await utils_html.create_data_entry(image_name, output_html_path, True)

    # TODO: Now use Benchmarks to compare the two outputs


def _get_model_strategy(name):
    '''
        Returns strategy of the model and right parameter which can be used later
        TODO Add other models

        externally_hosted:
        True: Image is externally hosted, e.g. https://de.imgbb.com or https://imgur.com -> Only link is given as input
        False: Image is stored locally and b64 encoded. It is attached to this prompt.
    '''
    
    match name:
        case "openai":
            strategy = OpenAIStrategy(api_key=_load_api_key("openai"))
            externally_hosted = True
            return strategy, externally_hosted
        case "gemini":
            strategy = GeminiStrategy(api_key=_load_api_key("gemini"))
            externally_hosted = False
            return strategy, externally_hosted
        case _:
            raise ValueError(f"Model {name} not supported.")


# TODO: Main optimieren
async def main():
    model = "gemini"

    # 1. Load API-Key and define model strategy
    strategy, images_externally_hosted = _get_model_strategy(model)

    # 2. Load prompt
    prompt = _get_prompt(images_externally_hosted)

    # 3. Create LLM-Client for model strategy
    client = LLMClient(strategy)
    
    image_dir = os.path.join(INPUT_PATH, 'images')
    
    for image in os.listdir(image_dir):
        if os.path.isfile(os.path.join(image_dir, image)) and image.endswith('.png'):
            image_information = {
                "name": os.path.splitext(image)[0],
                "link": None,
                "bytes": None
            }
            result = None

             # 4. Determine if 1. Upload image(s) necessary, or 2. Encoding of Images
            if images_externally_hosted:
                image_information = _upload_image(single_image=True, image_path=os.path.join(image_dir, image))

                # Sleep to avoid rate limits
                time.sleep(5)

                 # 4. Let LLMs create code out of image(s)
                for image_name, link in image_information.items():
                    image_information["link"] = link
                    result = await _process_image(client, image_information, prompt, model)

                    
            else:
                with open(os.path.join(image_dir, image), "rb") as image_file:
                    image_data = image_file.read()
                image_information["bytes"] = image_data

                # Encode the image data to Base64
                # b64_image_data = util_encode_image(image_data)
                
                result = await _process_image(client, image_information, prompt, model)
            

            print(f"Short summary: {result[:50]} ... (see more in path)")

        # 6. Analyze outputs for Input & Output
        # await _analyze_outputs(image_name)
    

    # Tests:
    # await _analyze_outputs('1.png')


if __name__ == "__main__":
    asyncio.run(main())