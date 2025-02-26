import json
from pathlib import Path


class LLMClient:
    # Central Interface for using different APIs

    def __init__(self, strategy):
        self.strategy = strategy

    async def generate_code(self, prompt, image_path):
        # Read UI-Screenshots
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        return await self.strategy.api_call(prompt, image_data)
