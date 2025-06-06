from pathlib import Path


class LLMClient:
    # Central Interface for using different APIs

    def __init__(self, strategy):
        self.strategy = strategy

    async def generate_frontend_code(self, prompt, image_information):
        return await self.strategy.llm_frontend_generation(prompt, image_information)
    
    async def refine_frontend_code(self, prompt):
        return await self.strategy.llm_frontend_refinement(prompt)    

    async def generate_accessibility_matching(self, prompt, current_map, accessibility_data):
        return await self.strategy.llm_accessibility_matching(prompt, current_map, accessibility_data)
    
    async def generate_text_rewrite(self, prompt, html_code):
        return await self.strategy.llm_text_rewrite(prompt, html_code)

