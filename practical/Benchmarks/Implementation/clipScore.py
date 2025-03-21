from sentence_transformers import SentenceTransformer, util
from PIL import Image
import os
DIR_PATH = os.path.join(os.path.dirname(__file__))
# For tests
DATA_PATH = os.path.join(DIR_PATH, '..', '..', 'Data')
INPUT_IMAGE_PATH = os.path.join(DATA_PATH, 'Input', 'images')
OUTPUT_IMAGE_PATH = os.path.join(DATA_PATH, 'Output', 'openai', 'images')

# All information here: https://huggingface.co/sentence-transformers/clip-ViT-B-32

''' 
    The following paper presents some possible benchmarks (incl. CLIP and some fine-grained benchmarks)
    Paper: https://arxiv.org/pdf/2403.03163

    CLIP-Score is based on a transformer model which maps the images (or text) to a shared 
    vector space. At the end, we can compare the cosine similarity between the two images.    
    
'''

def clip_score(image1_path, image2_path):
    # Load the CLIP
    model = SentenceTransformer('clip-ViT-B-32')

    image_input = Image.open(image1_path)
    image_output = Image.open(image2_path)

    # Image encoding
    image_input_emb = model.encode(image_input)
    image_output_emb = model.encode(image_output)

    # cosine similarity 
    cos_scores = util.cos_sim(image_input_emb, image_output_emb)
    # print(cos_scores)

    return cos_scores.item()


# Tests
# image1_path = f"{INPUT_IMAGE_PATH}/1.png"
# image2_path = f"{OUTPUT_IMAGE_PATH}/1.png"

# print(clip_score(image1_path, image2_path))