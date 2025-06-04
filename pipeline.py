import sys
import os
import json
import asyncio
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Benchmarks.visual_score as visual_score
from Benchmarks.accessibilityBenchmarks import AccessibilityBenchmarks
from LLMs.LLMClient import LLMClient
import Utils.utils_html as utils_html
import Utils.utils_dataset as utils_dataset
import Utils.utils_general as utils_general
import Utils.utils_prompt as utils_prompt
import Utils.utils_iterative_prompt as utils_iterative_prompt
import Data.Analysis.datasetAnalyze as datasetAnalyze
import Accessibility.accessibilityIssues as accessibilityIssues

KEYS_PATH = os.path.join(os.path.dirname(__file__), 'keys.json')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'Data')
INPUT_PATH = os.path.join(DATA_PATH, 'Input')
OUTPUT_PATH = os.path.join(DATA_PATH, 'Output')

DATE = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
# Test
# DATE = "2025-06-04-14-20"


async def _process_image(client, image_information, prompt, model, prompt_strategy):
    '''
        Sends API-Call to LLM and lets it create output.
        The Output is then stored to the Output Directory
    '''
    result_raw, tokens_used = await client.generate_frontend_code(prompt, image_information)

    # Print token information
    if tokens_used != None:
        print(tokens_used)

    result_clean = utils_html.clean_html_result(result_raw)
    
    output_dir = os.path.join(OUTPUT_PATH, model, 'html', prompt_strategy, DATE)
    
    output_html_path = os.path.join(output_dir, f"{image_information["name"]}.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(result_clean)
    
    # print(f"Result for {image_information["name"]}.html stored here: {output_html_path}")
    
    return result_clean


def _process_image_iterative(client, model, html_generated, accessibility_data):
    '''
        Gets generated HTML and Accessibility Data
        Grabs the Code with Issues and sends it to LLM.
        Afterwards, the LLM will return fixed code and it will be stored in file.
    '''

    number_iterations = 5
    for i in range(number_iterations):
        # get code snippets with violations (important +-3 lines around the file)
        html_snippets = utils_iterative_prompt.get_html_snippets(html_generated, accessibility_data)



async def _analyze_outputs(image, model, prompt_strategy):
    ''''
        Analyze outputs: 
        1. Structural Similarity. Create Accessibility-Tree, Bounding-Boxes, DOM-Similarity, Code-Quality
        2. Visual Similarity: Create Screenshots 
    '''
    # get basename
    image_name = os.path.splitext(image)[0]

    # 1. Define paths
    input_html_path = os.path.join(INPUT_PATH, 'html', f"{image_name}.html")
    input_accessibility_path = os.path.join(INPUT_PATH, 'accessibility', f"{image_name}.json")
    input_images_path = os.path.join(INPUT_PATH, 'images', f"{image_name}.png")
    input_insight_path = os.path.join(INPUT_PATH, 'insights', f"overview_{image_name}.json")
    output_html_path = os.path.join(OUTPUT_PATH, model, 'html', prompt_strategy, DATE, f"{image_name}.html")
    output_accessibility_path = os.path.join(OUTPUT_PATH, model, 'accessibility', prompt_strategy, DATE, f"{image_name}.json")
    output_images_path = os.path.join(OUTPUT_PATH, model, 'images', prompt_strategy, DATE, f"{image_name}.png")
    output_insight_path = os.path.join(OUTPUT_PATH, model, 'insights', prompt_strategy, DATE, f"overview_{image_name}.json")
    output_benchmark_path = os.path.join(OUTPUT_PATH, model, 'insights', prompt_strategy, DATE, f"benchmark_{image_name}.json")


    # 2. Calculate visual and structural Benchmarks
    # 2.1 get benchmarks
    input_list = [input_html_path, output_html_path, input_images_path, output_images_path]
    benchmark_score = visual_score.visual_eval_v3_multi(input_list)


    # # 2.2 Write Benchmarks to file
    utils_general.util_save_json(benchmark_score, output_benchmark_path)


    # 3. Analyze Accessibility Issues
    # await accessibilityIssues.enrich_with_accessibility_issues(image_name, input_html_path, input_accessibility_path, input_insight_path)
    await accessibilityIssues.enrich_with_accessibility_issues(image_name, output_html_path, output_accessibility_path, output_insight_path)


def _overwrite_insights(accessibility_dir, insight_dir, model, prompt_strategy, date=DATE):
    '''
       Calculates Insights:
       Accessibility Violation Ranking and benchmarks are calculated
       Place for the final insight overview: [*dir_accessibility*]/analysisAccessibilityIssues.json
    '''
    datasetAnalyze.overwrite_insights(accessibility_dir, insight_dir, model, prompt_strategy, date)


async def main():
    model = "gemini" # option openai, gemini, qwen_local, qwen_hf, llama_local, llama_hf, hf-finetuned
    model_dir = model.split("_")[0]
    prompt_strategy = "zero-shot" # option naive, zero-shot

    # 1. Load API-Key and define model strategy
    strategy = utils_general.get_model_strategy(model)

    # 2. Load prompt
    prompt = utils_prompt.get_prompt(prompt_strategy)

    # 3. Create LLM-Client for model strategy
    client = LLMClient(strategy)
    
    image_dir = os.path.join(INPUT_PATH, 'images')

    # Create output directory if it does not exist
    output_html_path, output_accessibility_path, output_images_path, output_insights_path = utils_general.util_create_directories(OUTPUT_PATH, model, prompt_strategy, DATE)

    for image in utils_dataset.sorted_alphanumeric(os.listdir(image_dir)):
        image_path = os.path.join(image_dir, image)

        if os.path.isfile(image_path) and image.endswith('.png'):
            print("Start processing: ", image)

            if int(image.split(".")[0]) < 22:
                continue

            image_information = {
                "name": os.path.splitext(image)[0],
                "path": image_path
            }
            
            # 4. Start the API Call and store information locally
            result = await _process_image(client, image_information, prompt, model_dir, prompt_strategy)

            # 5. Analyze outputs for Input & Output
            await _analyze_outputs(image, model_dir, prompt_strategy)


            print("----------- Done -----------\n")

    # 6. Overwrite insights
    # _overwrite_insights(
    #     os.path.join(INPUT_PATH, 'accessibility'),
    #     os.path.join(INPUT_PATH, 'insights'),
    #     None,
    #     None
    # )
    _overwrite_insights(
        output_accessibility_path,
        output_insights_path,
        model,
        prompt_strategy
    )




if __name__ == "__main__":
     asyncio.run(main())