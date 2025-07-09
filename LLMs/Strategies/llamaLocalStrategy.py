from .LLMStrategy import LLMStrategy
import base64
import ollama

# ToDo: Define Model
MODEL = "llama3.2-vision:latest"
MAX_TOKENS = 6144
CONTEXT_LENGTH = 32768 

class LlamaStrategy(LLMStrategy):
    def __init__(self):
        self.used_model = MODEL


    async def llm_frontend_generation(self, prompt, image_information):
        with open(image_information["path"], "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        response = ollama.chat(
            model=self.used_model,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_data]
            }],
            options={
                "num_predict": MAX_TOKENS,
                "num_ctx": CONTEXT_LENGTH
            }
        )

        return response["message"]["content"], None
    
    async def llm_frontend_refinement(self, prompt):
        response = ollama.chat(
            model=self.used_model,
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            options={
                "num_predict": MAX_TOKENS,
                "num_ctx": CONTEXT_LENGTH
            }
        )

        return response["message"]["content"], None
