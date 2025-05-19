import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import practical.Utils.utils_general as utils_general
import Benchmarks.Implementation.clipScore as clipScore 
import Benchmarks.Implementation.ssim as ssim


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Input', 'images')

class VisualBenchmarks:
    def __init__(self):
        self.visual_benchmark = {}

    def ssim(self, image1_path, image2_path):
        '''
            SSIM: Structural Similarity Index
            Compares images based on luminance, contrast and structure (see Wiki)
            https://scikit-image.org/docs/0.24.x/auto_examples/transform/plot_ssim.html

            Important: The images need to have the same size !!
        '''
        self.visual_benchmark["ssim"] = ssim.ssim_score(image1_path, image2_path).item()


    def clipValue(self, image1_path, image2_path):
        '''
            CLIP-Score is based on a transformer model which maps the images (or text) to a shared 
            vector space. At the end, we can compare the cosine similarity between the two images. 
        '''
        self.visual_benchmark["clip"] =  clipScore.clip_score(image1_path, image2_path)

    
    def calculate_and_get_visual_benchmarks(self, image_input_path, image_input_ss_path, image_output_path, image_output_ss_path):
        '''
            Calculate all visual benchmarks
        '''
        self.ssim(image_input_ss_path, image_output_ss_path)
        self.clipValue(image_input_path, image_output_path)

        return self.visual_benchmark