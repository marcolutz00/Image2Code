from .LLMStrategy import LLMStrategy
from openai import OpenAI
from pathlib import Path
import os
import base64

# ToDo: Define Model
MODEL = "gpt-4o" # gpt-4o, gpt-4.1

class OpenAIStrategy(LLMStrategy):
    def __init__(self, api_key):
        self.api_key = api_key
        self.used_model = MODEL
        self.client = OpenAI(api_key=api_key)

    def _upload_image(self, file_path):
        with open(file_path, "rb") as f:
            file = self.client.files.create(
                file=f,
                purpose="vision",
            )
        return file.id

    async def llm_frontend_generation(self, prompt, image_information):
        # B64 encoding
        # with open(image_information["path"], "rb") as image_file:
        #     image_data = base64.b64encode(image_file.read()).decode("utf-8")
        
        image_data = self._upload_image(image_information["path"])

        response = self.client.responses.create(
            model=self.used_model,
            input=[
                {
                    # "role": "system", "content": f"Imagine that you are a senior frontend developper focusing on implementing HTML/CSS from UI-Images. It is the goal to copy the image as precise as possible. Please only answer with the code, meaning without any explanation.",
                    "role": "user",
                    "content": [
                        { "type": "input_text", "text": prompt },
                        {
                            "type": "input_image",
                            "file_id": image_data,
                            # "image_url": f"data:image/png;base64,{image_data}",
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
    


    async def llm_frontend_refinement(self, prompt):
        response = self.client.responses.create(
            model=self.used_model,
            input=[
                {
                    "role": "system", "content": f"Imagine that you are a senior frontend developper focusing on implementing HTML/CSS from UI-Images. It is the goal to copy the image as precise as possible. Please only answer with the code, meaning without any explanation.",
                    "role": "user",
                    "content": [
                        { "type": "input_text", "text": prompt }
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
