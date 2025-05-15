import sys
import os
import json
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.LLMs.LLMClient import LLMClient
import practical.Utils.utils_html as utils_html
import practical.Utils.utils_dataset as utils_dataset
import practical.Utils.utils_general as utils_general
import practical.Utils.utils_prompt as utils_prompt
import asyncio

KEYS_PATH = os.path.join(os.path.dirname(__file__), 'keys.json')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'Data')
INPUT_PATH = os.path.join(DATA_PATH, 'Input')
OUTPUT_PATH = os.path.join(DATA_PATH, 'Output')



async def _process_image(client, image_information, prompt, model):
    '''
        Sends API-CAll to LLM and lets it create output.
        The Output is then stored to the Output Directory
    '''
    result_raw, tokens_used = await client.generate_frontend_code(prompt, image_information)

    # Print token information
    if tokens_used != None:
        print(tokens_used)

    result_clean = utils_html.clean_html_result(result_raw)
    
    output_dir = os.path.join(OUTPUT_PATH, model, 'html')
    
    output_html_path = os.path.join(output_dir, f"{image_information["name"]}.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(result_clean)
    
    # print(f"Result for {image_information["name"]}.html stored here: {output_html_path}")
    
    return result_clean


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


async def main():
    model = "gemini"
    prompt_strategy = "naive"

    # 1. Load API-Key and define model strategy
    strategy = utils_general.get_model_strategy(model)

    # 2. Load prompt
    prompt = utils_prompt.get_prompt(prompt_strategy)

    # 3. Create LLM-Client for model strategy
    client = LLMClient(strategy)
    
    image_dir = os.path.join(INPUT_PATH, 'images')

    for image in utils_dataset.sorted_alphanumeric(os.listdir(image_dir)):
        image_path = os.path.join(image_dir, image)

        if os.path.isfile(image_path) and image.endswith('.png'):
            print("Start processing: ", image)

            image_information = {
                "name": os.path.splitext(image)[0],
                "path": image_path
            }
            
            result = await _process_image(client, image_information, prompt, model)

            print("----------- Done -----------\n")

        # 6. Analyze outputs for Input & Output
        # await _analyze_outputs(image_name)
    

    # Tests:
    # await _analyze_outputs('1.png')


if __name__ == "__main__":
    asyncio.run(main())