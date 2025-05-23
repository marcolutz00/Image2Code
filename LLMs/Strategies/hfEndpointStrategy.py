import base64
from .LLMStrategy import LLMStrategy
import json
from openai import OpenAI
import os

KEYS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'keys.json')

class HfEndpointStrategy(LLMStrategy):
    def __init__(self, url):
        with open(KEYS_PATH) as f:
            self.token = json.load(f)["huggingface"]["reader_token"]

        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.client = OpenAI(
            base_url = url,
            api_key = self.token
        )



    async def api_frontend_generation(self, prompt, image_information):
        with open(image_information["path"], "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        response = self.client.chat.completions.create(
            model="tgi",                          
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        answer = response.choices[0].message.content
        return answer, None
