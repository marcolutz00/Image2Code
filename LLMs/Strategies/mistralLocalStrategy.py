from .LLMStrategy import LLMStrategy
import base64
from vllm import LLM, SamplingParams
import os

GGUF_PATH = os.path.join(os.environ["CONDA_PREFIX"], "models", "pixtral-12b-Q6_K_L.gguf")
MAX_TOKENS = 8192
CONTEXT_LENGTH = 32768


class PixtralStrategy(LLMStrategy):
    def __init__(self):
        self.llm = LLM(
            model = GGUF_PATH,
            tokenizer = "mistralai/Pixtral-12B-2409",
            trust_remote_code = True,
            max_model_len= CONTEXT_LENGTH,
        )
        self.sampler = SamplingParams(max_tokens=MAX_TOKENS)

    def file_to_data_url(path: str):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        file_type = "png"
        return f"data:image/{file_type};base64,{b64}"

    async def llm_frontend_generation(self, prompt, image_information):
        img_url = self.file_to_data_url(image_information["path"])

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": img_url}}
            ]
        }]

        response = self.llm.chat(messages, sampling_params=self.sampler)
        return response[0].outputs[0].text, None

    async def llm_frontend_refinement(self, prompt):
        response = self.llm.chat([{"role":"user","content":prompt}],
                            sampling_params=self.sampler)
        return response[0].outputs[0].text, None
