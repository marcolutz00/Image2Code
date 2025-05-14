from .LLMStrategy import LLMStrategy
from google import genai
from google.genai import types

'''
    Find all API-Information here:
    https://ai.google.dev/gemini-api/docs/image-understanding?hl=de
'''

MODEL = 'gemini-2.0-flash'
SYSTEM_INSTRUCTION_MAPPING = 'You are an expert in understanding accessibility issues in HTML/CSS. ' \
'Therefore, you often use automatic tools like Google lighthouse, Axe-Core and Pa11y which help you ' \
'to automatically detect Accessibility Issues within the code'

class GeminiStrategy(LLMStrategy):
    def __init__(self, api_key):
        self.api_key = api_key
        self.used_model = MODEL
        self.client = genai.Client(api_key=api_key)

    async def api_frontend_generation(self, prompt, image_information):
        '''
            Important! 
            1. image_data as bytes, like this:
            with open('path/to/small-sample.jpg', 'rb') as f:
                image_data = f.read()
            2. Only png images
        '''
        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                types.Part.from_bytes(
                    data=image_information["bytes"],
                    mime_type='image/png',
                ),
                prompt
            ]
        )

        return response.text

    async def api_accessibility_matching(self, prompt, current_map, accessibility_data):
        message = f'Prompt: {prompt}, Current Map: {current_map}, New Data: {accessibility_data}'

        response = self.client.models.generate_content(
            model=self.used_model,
            contents=[message],
            config=types.GenerateContentConfig(
                # temperature can range between 0.0 - 2.0. Creative answers should have a higher score, but if exactness is more important, than smaller score
                temperature=0.1,
                system_instruction=SYSTEM_INSTRUCTION_MAPPING
            )
        )

        return response.text