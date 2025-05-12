from pathlib import Path
from practical.Utils.utils_general import util_encode_image


class LLMClient:
    # Central Interface for using different APIs

    def __init__(self, strategy):
        self.strategy = strategy

    async def generate_frontend_code(self, prompt, image_information):
        image_data = image_information
        return await self.strategy.api_frontend_generation(prompt, image_data)
            

    async def generate_accessibility_matching(self, prompt, current_map, accessibility_data):
        return await self.strategy.api_accessibility_matching(prompt, current_map, accessibility_data)

