import sys
import os
import json
import argparse
import asyncio
import datetime
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLMs.LLMClient import LLMClient
import Utils.utils_dataset as utils_dataset
import Utils.utils_general as utils_general
import Utils.utils_prompt as utils_prompt
import Utils.utils_image_processing as utils_image_processing
import Utils.utils_llms as utils_llms
import Data.Analysis.analyzeAccessibility as analyzeAccessibility
import Data.Analysis.calculateBenchmarks as calculateBenchmarks


CURR_PATH = Path(__file__).resolve().parent
KEYS_PATH = CURR_PATH / "keys.json"
DATA_PATH = CURR_PATH / "Data"
INPUT_PATH = DATA_PATH / "Input"
OUTPUT_PATH = DATA_PATH / "Output"


# Arguments
DEFAULT_MODEL = "gemini"  # option: openai, gemini, qwen_local, qwen_hf, llama_local, llama_hf, hf-finetuned
DEFAULT_PROMPT_STRATEGY = "naive" # options: naive, zero-shot, few-shot, reason, iterative, composite
DATE = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
# Test
# DATE = "2025-06-30-20-08"


async def main(model, prompt_strategy, date):
    model_dir = model.split("_")[0]
    prompt_strategy = "composite" 
    max_attempts = 3

    # 1. Load API-Key and define model strategy
    strategy = utils_llms.get_model_strategy(model)

    # 2. Load prompt
    prompt = utils_prompt.get_prompt(prompt_strategy)

    # 3. Create LLM-Client for model strategy
    client = LLMClient(strategy)
    
    image_dir = os.path.join(INPUT_PATH, 'images')

    # Create output directory if it does not exist
    output_base_html_path, output_base_accessibility_path, output_base_images_path, output_base_insights_path = utils_general.create_directories(OUTPUT_PATH, model, prompt_strategy, DATE)

    for image in utils_dataset.sorted_alphanumeric(os.listdir(image_dir)):
        image_path = os.path.join(image_dir, image)

        if os.path.isfile(image_path) and image.endswith('.png'):
            print("Start processing: ", image)

            # if int(image.split(".")[0]) < 62:
            #     continue

            image_information = {
                "name": os.path.splitext(image)[0],
                "path": image_path
            }
            
            # 4. Start the API Call and store information locally
            # Sometimes the LLMs return errors messages (e.g. "I can't do this task ...")
            for i in range(max_attempts):
                try: 
                    generated_html = await utils_image_processing.process_image(client, image_information, prompt, model_dir, prompt_strategy, DATE)
                    break
                except Exception as e:
                    print(f"Failed at image {image} on attempt {i + 1}")
                    if i == max_attempts - 1:
                        raise e

            # 5. Analyze outputs for Input & Output
            _, accessibility_issues, _ = await utils_image_processing.analyze_outputs(image, model_dir, prompt_strategy, DATE)

            if prompt_strategy == "iterative":
                # 5.1 Process HTML iteratively
                await utils_image_processing.process_image_iterative(client, model_dir, prompt_strategy, generated_html, accessibility_issues, image, DATE)
            if prompt_strategy == "composite":
                # a
                await utils_image_processing.process_image_composite(client, model_dir, prompt_strategy, generated_html, accessibility_issues, image, DATE)
                

            print("----------- Done -----------\n")

    # 6. Overwrite insights
    # _overwrite_insights(
    #     os.path.join(INPUT_PATH, 'accessibility'),
    #     os.path.join(INPUT_PATH, 'insights'),
    #     None,
    #     None
    # )
    analyzeAccessibility.calculate_insights(
        output_base_accessibility_path,
        output_base_insights_path,
        model,
        prompt_strategy,
        DATE
    )

    calculateBenchmarks.start_process(
        model, 
        prompt_strategy, 
        DATE 
    )


def get_cli_arguments():
    parser = argparse.ArgumentParser(
        description="Process a batch of screenshots with different LLM back-ends."
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"LLM-Model (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--prompt_strategy", "-p",
        default=DEFAULT_PROMPT_STRATEGY,
        choices=["naive", "zero-shot", "few-shot", "reason",
                 "iterative", "composite"],
        help=f"Prompt-Strategy (default: {DEFAULT_PROMPT_STRATEGY})"
    )

    parser.add_argument(
        "--date", "-d",
        default=DATE,
        help=("Timestamp for this Run "
              f"(default is current date: {DATE})")
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_cli_arguments()
    asyncio.run(
        main(
            model           = args.model,
            prompt_strategy = args.prompt_strategy,
            date      = args.date,
        )
    )