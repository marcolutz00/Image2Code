from .LLMStrategy import LLMStrategy
from . import tokenCounter as tc
from openai import OpenAI
from pathlib import Path
import os
import base64

# ToDo: Define Model
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o"

class OpenAIStrategy(LLMStrategy):
    def __init__(self):
        self.used_model = MODEL

    async def api_call(self, prompt, image_data):

        b64_img = base64.b64encode(image_data).decode("utf-8")

        amount_of_token = tc.count_tokens(b64_img, self.used_model)
        print(f"Amount of token {amount_of_token}")

        response = client.chat.completions.create(
            model=self.used_model,

            messages=[
                {"role": "system", "content": f"Imagine that you are a frontend developper focusing on implementing HTML/CSS from UI-Images. You are only answering the code without any explanation."},
                {"role": "user", "content": f"{prompt}. This is the image: {b64_img}"}
                #{"role": "user", "content": f"{prompt}. This is the image: test"}
            ]
        )
        return response.choices[0].message.content
