from pathlib import Path


class LLMClient:
    # Central Interface for using different APIs

    def __init__(self, strategy):
        self.strategy = strategy


    # Image-to-Code Approach
    async def generate_frontend_code(self, prompt, image_information):
        """
            Normal frontend code genaration based on image
        """
        return await self.strategy.llm_frontend_generation(prompt, image_information)
    
    async def refine_frontend_code(self, prompt):
        """
            Refinement of frontend code and accessibility violations
        """
        return await self.strategy.llm_frontend_refinement(prompt)    
    

    # Multi-Agent Approach
    async def agent_call(self, prompt):
        """
            Detect, identifies / classifies, patches accessibility issues in HTML
        """
        return await self.strategy.agent_call(prompt)
    


    # Old - Not necessary anymore
    async def generate_accessibility_matching(self, prompt, current_map, accessibility_data):
        """
            Idea: Generate accessibility matching automatically
        """
        return await self.strategy.llm_accessibility_matching(prompt, current_map, accessibility_data)
    
    async def generate_text_rewrite(self, prompt, html_code):
        """
            Rewrite text for data mutation
        """
        return await self.strategy.llm_text_rewrite(prompt, html_code)
    


