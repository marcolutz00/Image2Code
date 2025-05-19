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



async def _process_image(client, image_information, prompt, model, prompt_strategy):
    '''
        Sends API-CAll to LLM and lets it create output.
        The Output is then stored to the Output Directory
    '''
    result_raw, tokens_used = await client.generate_frontend_code(prompt, image_information)

    # Print token information
    if tokens_used != None:
        print(tokens_used)

    result_clean = utils_html.clean_html_result(result_raw)
    
    output_dir = os.path.join(OUTPUT_PATH, model, 'html', prompt_strategy)
    
    output_html_path = os.path.join(output_dir, f"{image_information["name"]}.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(result_clean)
    
    # print(f"Result for {image_information["name"]}.html stored here: {output_html_path}")
    
    return result_clean


async def _analyze_outputs(image, model, prompt_strategy):
    ''''
        Analyze outputs: 
        1. Structural Similarity. Create Accessibility-Tree, Bounding-Boxes, DOM-Similarity, Code-Quality
        2. Visual Similarity: Create Screenshots 
    '''
    # get basename
    image_name = os.path.splitext(image)[0]

    input_html_path = os.path.join(INPUT_PATH, 'html', f"{image_name}.html")
    input_accessibility_path = os.path.join(INPUT_PATH, 'accessibility', f"{image_name}.json")
    input_images_path = os.path.join(INPUT_PATH, 'images', f"{image_name}.png")
    input_insight_path = os.path.join(INPUT_PATH, 'insights', f"overview_{image_name}.json")
    output_html_path = os.path.join(OUTPUT_PATH, model, 'html', prompt_strategy, f"{image_name}.html")
    output_accessibility_path = os.path.join(OUTPUT_PATH, model, 'accessibility', prompt_strategy, f"{image_name}.json")
    output_images_path = os.path.join(OUTPUT_PATH, model, 'images', prompt_strategy, f"{image_name}.png")
    output_insight_path = os.path.join(OUTPUT_PATH, model, 'insights', prompt_strategy, f"overview_{image_name}.json")

    # Temp file for original html, but will be deleted afterwards
    output_original_images_path = os.path.join(OUTPUT_PATH, model, 'images', prompt_strategy, f"original_{image_name}.png")


    # 1. Take Screenshots
    utils_html.save_screenshots(output_html_path, output_images_path, input_html_path, output_original_images_path)

    # 2. Calculate Benchmarks
    # 2.1 Visual Benchmarks
    obj_visual_benchmarks = VisualBenchmarks()
    # Important: SSIM need same size images, clip value does not care
    ssim_score = obj_visual_benchmarks.ssim(output_original_images_path, output_images_path)
    clip_value = obj_visual_benchmarks.clipValue(input_images_path, output_images_path)

    # 2.2 Structural Benchmarks
    obj_structural_benchmarks = StructuralBenchmarks()
    text_similarity_score = obj_structural_benchmarks.textSimilarity(input_html_path, output_html_path)
    tree_bleu_score = obj_structural_benchmarks.treebleu(input_html_path, output_html_path)

    # 3. Delete temp Screenshot
    os.remove(output_original_images_path)

    # 4. Analyze Accessibility Issues
    # await accessibilityIssues.enrich_with_accessibility_issues(image_name, input_html_path, input_accessibility_path, input_insight_path)
    await accessibilityIssues.enrich_with_accessibility_issues(image_name, output_html_path, output_accessibility_path, output_insight_path)

async def main():
    model = "gemini"
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

            # if int(image.split(".")[0]) < 23:
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