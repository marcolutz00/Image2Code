import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import practical.Utils.utils_general as utils_general
import Benchmarks.Implementation.clipScore as clipScore 
import Benchmarks.Implementation.ssim as ssim


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Input', 'images')

class VisualBenchmarks:
    '''
        SSIM: Structural Similarity Index
        Compares images based on luminance, contrast and structure (see Wiki)
        https://scikit-image.org/docs/0.24.x/auto_examples/transform/plot_ssim.html

        Important: The images need to have the same size !!
    '''
    def ssim(self, image1_path, image2_path):
        return ssim.ssim_score(image1_path, image2_path)


    '''
        CLIP-Score is based on a transformer model which maps the images (or text) to a shared 
        vector space. At the end, we can compare the cosine similarity between the two images. 
    '''
    def clipValue(self, image1_path, image2_path):
        return clipScore.clip_score(image1_path, image2_path)

    

# Tests
# obj = VisualBenchmarks()
# image1_path = os.path.join(DATA_PATH, 'test_w3.png')
# image2_path = os.path.join(DATA_PATH, 'test_w3.png')
# image3_path = os.path.join(DATA_PATH, 'test_youtube.png')


# ssim_val = obj.ssim(image1_path, image2_path)
# print(ssim_val)