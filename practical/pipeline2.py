import sys
import os
import json
import time
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.Benchmarks.visualBenchmarks import VisualBenchmarks
from practical.Benchmarks.structuralBenchmarks import StructuralBenchmarks
from practical.Benchmarks.accessibilityBenchmarks import AccessibilityBenchmarks
from practical.LLMs.LLMClient import LLMClient
import practical.Utils.utils_html as utils_html
import practical.Utils.utils_dataset as utils_dataset
import practical.Utils.utils_general as utils_general
import practical.Utils.utils_prompt as utils_prompt
import practical.Accessibility.accessibilityIssues as accessibilityIssues

KEYS_PATH = os.path.join(os.path.dirname(__file__), 'keys.json')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'Data')
INPUT_PATH = os.path.join(DATA_PATH, 'Input')
OUTPUT_PATH = os.path.join(DATA_PATH, 'Output')

'''
    Second pipeline after manual evaluation of the generated code.
    In this pipeline, we are going to analyze the accessibility outputs and Accessibility Benchmarks
'''


async def main():
    model = "openai"
    prompt_strategy = "naive" # option naive, zero-shot

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

            # if int(image.split(".")[0]) < 37:
            #     continue

            image_information = {
                "name": os.path.splitext(image)[0],
                "path": image_path
            }
            
            # 4. Start the API Call and store information locally
            # result = await _process_image(client, image_information, prompt, model, prompt_strategy)

            # 5. Analyze outputs for Input & Output
            await _analyze_outputs(image, model, prompt_strategy)


            print("----------- Done -----------\n")



if __name__ == "__main__":
    asyncio.run(main())