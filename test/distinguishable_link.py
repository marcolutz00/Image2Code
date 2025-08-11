from datasets import load_dataset
import os
from PIL import Image
import asyncio
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Utils.utils_dataset as utils_dataset
import Utils.utils_llms as utils_llms
import Utils.utils_prompt as utils_prompt
from LLMs.LLMClient import LLMClient
import Utils.utils_html as utils_html
import Utils.utils_image_processing as utils_image_processing
import Accessibility.accessibilityIssues as accessibilityIssues



CURR_PATH = os.path.dirname(os.path.abspath(__file__))

async def main():
    model="gemini"
    prompt_strategy="few-shot"

    # await download_dataset()
    # print("Dataset downloaded and stored in 'html' and 'images' directories.")    

    strategy = utils_llms.get_model_strategy(model)

    # 2. Load prompt
    prompt = utils_prompt.get_prompt(prompt_strategy)

    # 3. Create LLM-Client for model strategy
    client = LLMClient(strategy)

    image_dir = os.path.join(CURR_PATH, 'distinguishable_link', 'images')

    for image in utils_dataset.sorted_alphanumeric(os.listdir(image_dir)):

        # if os.path.splitext(image)[0] != "14":
        #     continue

        image_path = os.path.join(image_dir, image)

        image_information = {
                "name": os.path.splitext(image)[0],
                "path": image_path
            }

        result_raw, tokens_used = await client.generate_frontend_code(prompt, image_information)

        # Print token information
        if tokens_used != None:
            print(tokens_used)

        result_clean = utils_html.clean_html_result(result_raw)


        output_html_path = os.path.join(CURR_PATH, 'distinguishable_link', 'html_generated', f"{model}_{image_information['name']}.html")
        output_accessibility_path = os.path.join(CURR_PATH, 'distinguishable_link', 'accessibility', f"{model}_{image_information['name']}_accessibility.json")
        output_insight_path = os.path.join(CURR_PATH, 'distinguishable_link', 'insights', f"{model}_{image_information['name']}_insights.json")
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(result_clean)


        # 3. Analyze Accessibility Issues
        # await accessibilityIssues.enrich_with_accessibility_issues(image_name, input_html_path, input_accessibility_path, input_insight_path)
        accessibility_issues, accessibility_issues_overview = await accessibilityIssues.enrich_with_accessibility_issues(image, output_html_path, output_accessibility_path, output_insight_path)


if __name__ == "__main__":
    asyncio.run(main())

