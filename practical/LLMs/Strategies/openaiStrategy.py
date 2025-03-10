from .LLMStrategy import LLMStrategy
from openai import OpenAI
from pathlib import Path
import os

# ToDo: Define Model
MODEL = "gpt-4o"

class OpenAIStrategy(LLMStrategy):
    def __init__(self, api_key):
        self.api_key = api_key
        self.used_model = MODEL
        self.client = OpenAI(api_key=api_key)

    async def api_call(self, prompt, image_data):

        response = self.client.chat.completions.create(
            model=self.used_model,

            messages=[
                {"role": "system", "content": f"Imagine that you are a senior frontend developper focusing on implementing React Code from UI-Images. Please only answer with the code, meaning without any explanation."},
                # {"role": "system", "content": f"Imagine that you are a are trying to explain the image to someone. Please describe the image in a few words."},

                {"role": "user", "content": 
                    [
                        {"type": "text", "text": f"{prompt}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"{image_data}",
                            },
                        },
                    ],
                }
            ]
        )
        return response.choices[0].message.content
