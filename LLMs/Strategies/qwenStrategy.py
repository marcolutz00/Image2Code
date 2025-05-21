from .LLMStrategy import LLMStrategy
from transformers import Qwen2_5_VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info
import torch

# ToDo: Define Model
MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"
MAX_TOKENS = 2048

class QwenStrategy(LLMStrategy):
    def __init__(self):
        self.used_model = MODEL
        self.max_tokens = MAX_TOKENS
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.used_model, torch_dtype="auto", device_map="auto", attn_implementation="eager"
        )
        self.processor = AutoProcessor.from_pretrained(self.used_model)


    async def api_frontend_generation(self, prompt, image_information):
        # Information here: https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct

        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": f"file://{image_information['path']}"},
                {"type": "text",  "text": prompt}
            ],
        }]

        # Prep for inference
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(text=[text], images=image_inputs, videos=video_inputs,
                                return_tensors="pt").to(self.model.device)
        
        # Inference
        prompt_length = inputs.input_ids.shape[-1]
        generation = self.model.generate(**inputs, max_new_tokens=self.max_tokens, return_dict_in_generate=True)

        response = self.processor.decode(generation.sequences[0][prompt_length:], skip_special_tokens=True)

        # generated_ids = self.model.generate(**inputs, max_new_tokens=self.max_tokens)
        # generated_ids_trimmed = [
        #     out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        # ]
        # response = self.processor.batch_decode(
        #     generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        # )

        return response, None
