from .LLMStrategy import LLMStrategy
import ollama


# ToDo: Define Model
MODEL = "qwen2.5vl:3b"

class QwenStrategy(LLMStrategy):
    def __init__(self):
        self.used_model = MODEL


    async def llm_frontend_generation(self, prompt, image_information):
        with open(image_information["path"], "rb") as image_file:
            image_data = image_file.read()
            
        response = ollama.chat(
            model=self.used_model,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_data]
            }]
        )

        return response["message"]["content"], None


    async def llm_frontend_refinement(self, prompt):
        response = ollama.chat(
            model=self.used_model,
            messages=[{
                'role': 'user',
                'content': prompt
            }]
        )

        return response["message"]["content"], None