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



DATASET_HF = "HuggingFaceM4/WebSight"
CURR_PATH = os.path.dirname(os.path.abspath(__file__))

async def download_dataset():
    await utils_dataset.login_hugging_face()

    indices = [ 57, 60, 96, 102, 146, 210, 211, 234, 257, 258, 264, 265, 268, 269, 277 ]

    webcode2m = load_dataset(DATASET_HF, split="train", streaming=True)

    webcode2m_filtered = await utils_dataset.filter_entries(webcode2m, indices)

    for index, entry in enumerate(webcode2m_filtered):
        html_str = entry['text']
        img = entry['image']

        out_html = os.path.join(CURR_PATH, 'html', f"{index+1}.html")
        out_img  = os.path.join(CURR_PATH, 'images', f"{index+1}.png")
        os.makedirs(os.path.dirname(out_html), exist_ok=True)
        os.makedirs(os.path.dirname(out_img), exist_ok=True)

        with open(out_html, 'w', encoding='utf-8') as f:
            f.write(html_str)
        img.save(out_img)

async def main():
    model="gemini"
    prompt_strategy="naive"

    # await download_dataset()
    # print("Dataset downloaded and stored in 'html' and 'images' directories.")    

    strategy = utils_llms.get_model_strategy(model)

    # 2. Load prompt
    prompt = utils_prompt.get_prompt(prompt_strategy)

    # 3. Create LLM-Client for model strategy
    client = LLMClient(strategy)
    
    image_dir = os.path.join(CURR_PATH, 'images')

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


        output_html_path = os.path.join(CURR_PATH, 'html_generated', f"{model}_{image_information['name']}.html")
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(result_clean)



if __name__ == "__main__":
    asyncio.run(main())

