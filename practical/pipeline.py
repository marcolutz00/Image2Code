import Utils.utils as utils
from API.apiCalls import LLMClient
from API.Strategies.openaiStrategy import OpenAIStrategy
import asyncio


async def main():
    # ToDo: Prompt Engineering
    PROMPT = "Please convert the following image into HTML/CSS. Return the HTML with included CSS without any further description or text. The image is base64 encoded."
    COMPANY = "openai"
    STRATEGY = OpenAIStrategy()
    IMAGE_PATH = "practical/Data/Input/test_w3.png"


    client = LLMClient(STRATEGY)

    result = await client.generate_code(PROMPT, IMAGE_PATH)
    print("Ergebnis:", result)


if __name__ == "__main__":
    asyncio.run(main())