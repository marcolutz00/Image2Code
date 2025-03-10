import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.LLMs.apiCalls import LLMClient
from LLMs.Strategies.openaiStrategy import OpenAIStrategy
import asyncio


async def main():
    # ToDo: Prompt Engineering
    # PROMPT = "Please convert the following image into React Code. " \
    # "Please copy all elements, style, text and components. " \
    # "Return the generated Code without any further description or text. " \
    # # ToDo: Declare if Base64 encoded or externally hosten and applicable URL
    # "The image is externally hosted and can be found via the following URL."

    PROMPT = "Please describe the image of the URL below to me in a few words."

    # Load API key from keys.json
    keys_path = os.path.join(os.path.dirname(__file__), 'keys.json')
    with open(keys_path) as f:
        keys = json.load(f)
        openai_api_key = keys["openai"]["api_key"]
    STRATEGY = OpenAIStrategy(api_key=openai_api_key)

    # Important: The information for the image can be the path to the image or the URL to the web-based image
    IMAGE_INFORMATION = "https://i.ibb.co/Z6zJdhPR/Bildschirmfoto-2025-03-10-um-11-23-13.png"
    IMAGE_EXTERNALLY_HOSTED = True


    client = LLMClient(STRATEGY)

    result = await client.generate_code(PROMPT, IMAGE_INFORMATION, IMAGE_EXTERNALLY_HOSTED)
    print("Ergebnis: ", result)


if __name__ == "__main__":
    asyncio.run(main())