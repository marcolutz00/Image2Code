from .LLMStrategy import LLMStrategy
from google import genai
from google.genai import types

'''
    Find all API-Information here:
    https://ai.google.dev/gemini-api/docs/image-understanding?hl=de
'''

# Model for normal Image-to-Code - IMPORTANT: Multi-Agent Approach uses reasoning model
MODEL = 'gemini-2.0-flash'



class GeminiStrategy(LLMStrategy):
    def __init__(self, api_key):
        self.api_key = api_key
        self.used_model = MODEL
        self.client = genai.Client(api_key=api_key)

    # Image-to-Code 
    async def llm_frontend_generation(self, prompt, image_information):
        '''
            Important! 
            1. image_data as bytes, like this:
            with open('path/to/small-sample.jpg', 'rb') as f:
                image_data = f.read()
            2. Only png images
        '''
        with open(image_information["path"], "rb") as image_file:
            image_data = image_file.read()

        response =self.client.models.generate_content(
            model=self.used_model,
            contents=[
            types.Part.from_bytes(
                data=image_data,
                mime_type='image/jpeg',
            ),
            prompt
            ]
        )


        tokens_used = response.usage_metadata

        return response.text, tokens_used
    

    async def llm_frontend_refinement(self, prompt):
        '''
            Refinement of the HTML code.
            The prompt should contain the HTML code which should be refined.
        '''
        response = self.client.models.generate_content(
            model=self.used_model,
            contents=[prompt]
        )

        tokens_used = response.usage_metadata

        return response.text, tokens_used


    # Multi-Agent Approach
    async def agent_call(self, prompt):
        '''
            Detects, identifies and patches accessibility issues in HTML/CSS
        '''
        response = self.client.models.generate_content(
            model=self.used_model,
            # prompt contains prompt + html_code
            contents=[prompt],
        )

        tokens_used = response.usage_metadata

        return response.text, tokens_used






    # Old - Not necessary anymore
    async def llm_accessibility_matching(self, prompt, current_map, accessibility_data):
        message = f'Prompt: {prompt}, Current Map: {current_map}, New Data: {accessibility_data}'

        response = self.client.models.generate_content(
            model=self.used_model,
            contents=[message]
        )

        return response.text
    
    async def llm_text_rewrite(self, prompt, html_code):
        message = f'Prompt: {prompt}, Current HTML: {html_code}'
        
        response = self.client.models.generate_content(
            model=self.used_model,
            contents=[message]
        )

        return response.text
    
