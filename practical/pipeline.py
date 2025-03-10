import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.API.apiCalls import LLMClient
from API.Strategies.openaiStrategy import OpenAIStrategy
import asyncio


async def main():
    # ToDo: Prompt Engineering
    PROMPT = "Please convert the following image into React Code. " \
    "Please copy all elements, style, text and components. " \
    "Return the generated Code without any further description or text. " \
    # ToDo: Declare if Base64 encoded or externally hosten and applicable URL
    "The image is externally hosted and can be found via the following URL."

    # Load API key from keys.json
    keys_path = os.path.join(os.path.dirname(__file__), 'keys.json')
    with open(keys_path) as f:
        keys = json.load(f)
        openai_api_key = keys["openai"]["api_key"]
    STRATEGY = OpenAIStrategy(api_key=openai_api_key)

    # Important: The information for the image can be the path to the image or the URL to the web-based image
    IMAGE_INFORMATION = "https://ibb.co/MDwjyy4K"
    IMAGE_EXTERNALLY_HOSTED = True


    client = LLMClient(STRATEGY)

    result = await client.generate_code(PROMPT, IMAGE_INFORMATION, IMAGE_EXTERNALLY_HOSTED)
    print("Ergebnis: ", result)


if __name__ == "__main__":
    asyncio.run(main())