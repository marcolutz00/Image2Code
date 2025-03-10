from pathlib import Path
from practical.Utils.utils import util_encode_image


class LLMClient:
    # Central Interface for using different APIs

    def __init__(self, strategy):
        self.strategy = strategy

    async def generate_code(self, prompt, image_information, externally_hosted):
        # Read UI-Screenshots
        # 1. Image is externally hosted, e.g. https://de.imgbb.com or https://imgur.com
        if externally_hosted:
            image_data = image_information

            return await self.strategy.api_call(prompt, image_data)
        
        # 2. Image is stored locally, input is the path to the image
        else:
            with open(image_information, "rb") as image_file:
                image_data = image_file.read()

            # Encode the image data to Base64
            b64_image_data = util_encode_image(image_data)
            
            return await self.strategy.api_call(prompt, b64_image_data)



