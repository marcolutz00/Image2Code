import torch
import numpy as np
from PIL import Image
import clip
from sam2.sam2_image_predictor import SAM2ImagePredictor
import matplotlib.pyplot as plt

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
    def __init__(self, sam_model_path, clip_model_name="ViT-B/32"):
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

        self.predictor = SAM2ImagePredictor.from_pretrained("facebook/sam2-hiera-tiny")

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
        image = Image.open(image_path).convert("RGB")
        # self.predictor.set_image(torch.from_numpy(np.array(image)))
        self.predictor.set_image(np.array(image))


        masks, _, _ = self.predictor.predict(multimask_output=True)

        # Test show masks
        self.show_masks(image_path, masks)

        # Predict names of components with CLIP
        # Tokenize classes
        text = clip.tokenize(self.component_classes).to(self.device)

        with torch.no_grad():
            text_features = self.clip_model.encode_text(text)

        results = []
        # Crop iamges accoridng to masks and predict with CLIP
        for i, bbox in enumerate(bboxes):
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
        plt.figure(figsize=(10, 10))
        plt.imshow(image)
        # show_points(plt.gca())
        plt.axis('on')
        plt.show()  

