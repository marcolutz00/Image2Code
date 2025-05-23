from .LLMStrategy import LLMStrategy
from openai import OpenAI
from pathlib import Path
import os
import base64

# ToDo: Define Model
MODEL = "gpt-4o"

class OpenAIStrategy(LLMStrategy):
    def __init__(self, api_key):
        self.api_key = api_key
        self.used_model = MODEL
        self.client = OpenAI(api_key=api_key)


    async def api_frontend_generation(self, prompt, image_information):
        with open(image_information["path"], "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        response = self.client.responses.create(
            model=self.used_model,
            input=[
                {
                    "role": "system", "content": f"Imagine that you are a senior frontend developper focusing on implementing HTML/CSS from UI-Images. It is the goal to copy the image as precise as possible. Please only answer with the code, meaning without any explanation.",
                    "role": "user",
                    "content": [
                        { "type": "input_text", "text": prompt },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{image_data}",
                            # "image_url": f"data:image/jpeg;base64,{image_data}",
                        },
                    ],
                }
            ],
        )

        tokens_used = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens
        }
        return response.output_text, tokens_used
