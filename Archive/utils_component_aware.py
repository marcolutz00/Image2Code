import torch
import numpy as np
from PIL import Image
import clip
from sam2.sam2_image_predictor import SAM2ImagePredictor
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
import matplotlib.pyplot as plt
import os
import sys

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Output", "openai", "images", "naive", "2025-06-08-15-35")

"""
    Idea:
    Combination of SAM (Segement Anything Model) to detect component in the image and then use CLIP-Model 
    to classify the components.
    After classification, the LLM gets the image and accessibility information to the classified components.
    -> Similar to RAG

    SAM: https://segment-anything.com
    Clip Model: https://github.com/openai/CLIP

    Information to Implementation:
    https://huggingface.co/facebook/sam2-hiera-tiny

"""

class ComponentAwarePredictor:
    def __init__(self):
        # Set seed for reproduce.
        np.random.seed(3)

        # device
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        self.dtype  = torch.bfloat16 if self.device=="cuda" else torch.float32

        self.predictor = SAM2ImagePredictor.from_pretrained("facebook/sam2-hiera-tiny", device=self.device.type)

        sam2_model = self.predictor.model
        self.mask_generator = SAM2AutomaticMaskGenerator(sam2_model, device=self.device.type)

        self.clip_model, self.clip_preprocess = clip.load("ViT-B/32", device=self.device)
        self.clip_model.eval()

        # Classes for Clip
        self.component_classes = [
            "button", "input field", "checkbox", "radio button", "dropdown menu",
            "text area", "link", "image", "navigation bar", "footer", "header", "sidebar", "card",
            "table", "form", "modal", "tooltip"
        ]


    def predict_component_names(self, image_path):
        # Start with SAM2 to get masks
        image = Image.open(image_path)
        image = np.array(image.convert("RGB"))  

        # self.show_masks(image_path, None)

        # Information here: https://github.com/facebookresearch/sam2/blob/main/notebooks/automatic_mask_generator_example.ipynb
        masks = self.mask_generator.generate(image)

        # Test show masks
        self.show_masks(image, masks)

        # Predict names of components with CLIP
        # Tokenize classes
        text = clip.tokenize(self.component_classes).to(self.device)

        with torch.no_grad():
            text_features = self.clip_model.encode_text(text)

        results = []
        # Crop iamges accoridng to masks and predict with CLIP
        for i, mask in enumerate(masks):
            bbox = mask["bbox"]
            x1, y1, x2, y2 = bbox.astype(int)

            image_cropped = image.crop((x1, y1, x2, y2))
            image_cropped_tensor = self.clip_preprocess(image_cropped).unsqueeze(0).to(self.device)

            # Get image features
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_cropped_tensor)

            # Calculate similarity
            similarity = (image_features @ text_features.T).squeeze(0)
            predicted_class_index = similarity.argmax().item()
            predicted_class_name = self.component_classes[predicted_class_index]



    
    def show_masks(self, image, masks):
        """
            Show masks on image.
        """
        plt.figure(figsize=(20, 20))
        self.show_anns(masks)
        plt.imshow(image)
        plt.axis('off')
        plt.show() 



if __name__ == "__main__":
    predictor = ComponentAwarePredictor()
    image_path = os.path.join(OUTPUT_PATH, "6.png")
    predictor.predict_component_names(image_path)