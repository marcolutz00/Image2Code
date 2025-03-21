import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Utils.utils as utils
import Benchmarks.Implementation.clipScore as clipScore 
import Benchmarks.Implementation.ssim as ssim


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Input', 'images')

class VisualBenchmarks:
    '''
        SSIM: Structural Similarity Index
        Compares images based on luminance, contrast and structure (see Wiki)
        https://scikit-image.org/docs/0.24.x/auto_examples/transform/plot_ssim.html

        Important: The images need to have the same size !!

        TODO: How to handle different sizes?
    '''
    def ssim(self, image1_path, image2_path):
        return ssim.ssim_score(image1_path, image2_path)
    
    '''
        tbd.
        Bounding-Boxes: 
        Compares two images based on the bounding boxes of the elements
        Problems: Different amount of elements in input and generated code
        How to compare? Maybe matching of elements first - but how to match?
    '''
    def boundingBoxes(self, code1, code2):
        print("test")


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