import torch
import json 
import os
from ..LLMs.Strategies.LLMStrategy import LLMStrategy
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor

from transformers.image_utils import to_numpy_array, PILImageResampling, ChannelDimension
from transformers.image_transforms import resize, to_channel_dimension_format

MODEL = "HuggingFaceM4/VLM_WebSight_finetuned"
KEYS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'keys.json')

class HfFinetunedStrategy(LLMStrategy):
    def __init__(self):
        with open(KEYS_PATH) as f:
            huggingface_token = json.load(f)["huggingface"]["reader_token"]

        self.token = huggingface_token
        # get the right device
        self.device = (
                torch.device("cuda")
                if torch.cuda.is_available()
                else torch.device("mps" if torch.backends.mps.is_available() else "cpu")
            )
        self.used_model = MODEL

        self.processor = AutoProcessor.from_pretrained(self.used_model, token=self.token)
        self.model = AutoModelForCausalLM.from_pretrained(
            "HuggingFaceM4/VLM_WebSight_finetuned",
            token=self.token,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
        ).to(self.device)

        # helper, mentioned in docmentation - https://huggingface.co/HuggingFaceM4/VLM_WebSight_finetuned
        self.image_seq_len = self.model.config.perceiver_config.resampler_n_latents
        self.bos_token = self.processor.tokenizer.bos_token
        self.bad_words_ids = self.processor.tokenizer(["<image>", "<fake_token_around_image>"], add_special_tokens=False).input_ids



    async def llm_frontend_generation(self, prompt, image_information):
        pil_image = Image.open(image_information["path"])

        inputs = self.processor.tokenizer(
            f"{self.bos_token}<fake_token_around_image>{'<image>' * self.image_seq_len}<fake_token_around_image>",
            return_tensors="pt",
            add_special_tokens=False,
        )

        # inputs["pixel_values"] = self.processor.image_processor([pil_image], transform=self.custom_transform)
        inputs = self.create_input_with_prompt(pil_image, prompt, self.processor, self.device)
        generated_ids = self.model.generate(**inputs, bad_words_ids=self.bad_words_ids, max_length=4096)
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return generated_text


    async def llm_frontend_refinement(self, prompt):
        """
            Refinement of the HTML code.
            The prompt should contain the HTML code which should be refined.
        """
        inputs = self.processor.tokenizer(
            f"{self.bos_token}<fake_token_around_image>{'<image>' * self.image_seq_len}<fake_token_around_image>",
            return_tensors="pt",
            add_special_tokens=False,
        )

        inputs = self.create_input_with_prompt("", prompt, self.processor, self.device)
        generated_ids = self.model.generate(**inputs, bad_words_ids=self.bad_words_ids, max_length=4096)
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return generated_text
    

    # standard input is without prompt - with prompt helper
    def create_input_with_prompt(self, img, prompt, processor, device):
        prompts = [
            "User:",                          
            img,
            prompt,                          
            "\nAssistant:"                    
        ]

        inputs = processor(prompts, return_tensors="pt")
        return {k: v.to(device) for k, v in inputs.items()}
    


    # Helper Functions - from docu: https://huggingface.co/HuggingFaceM4/VLM_WebSight_finetuned

    def convert_to_rgb(self, image):
        # `image.convert("RGB")` would only work for .jpg images, as it creates a wrong background
        # for transparent images. The call to `alpha_composite` handles this case
        if image.mode == "RGB":
            return image

        image_rgba = image.convert("RGBA")
        background = Image.new("RGBA", image_rgba.size, (255, 255, 255))
        alpha_composite = Image.alpha_composite(background, image_rgba)
        alpha_composite = alpha_composite.convert("RGB")
        return alpha_composite

    # The processor is the same as the Idefics processor except for the BILINEAR interpolation,
    # so this is a hack in order to redefine ONLY the transform method
    def custom_transform(self, x):
        x = self.convert_to_rgb(x)
        x = to_numpy_array(x)
        x = resize(x, (960, 960), resample=PILImageResampling.BILINEAR)
        x = self.processor.image_processor.rescale(x, scale=1 / 255)
        x = self.processor.image_processor.normalize(
            x,
            mean=self.processor.image_processor.image_mean,
            std=self.processor.image_processor.image_std
        )
        x = to_channel_dimension_format(x, ChannelDimension.FIRST)
        x = torch.tensor(x)
        return x