from skimage.metrics import structural_similarity as ssim
from skimage.io import imread
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Input')

class VisualBenchmarks:
    '''
        SSIM: Structural Similarity Index
        Compares images based on luminance, contrast and structure (see Wiki)
        https://scikit-image.org/docs/0.24.x/auto_examples/transform/plot_ssim.html
    '''
    def ssim(self, image1, image2):
        return ssim(image1, image2, win_size=7, channel_axis=-1)
    
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
        tbd 
        DOM-Similarity:
        Compares two images based on the DOM-Tree
        Similar problems as with bounding boxes - how to compare?
        Maybe try this: https://www.geeksforgeeks.org/html-dom-comparedocumentposition-method/

    '''
    def domSimilarity(self, image1, image2):
        print("test")
    

    def codeQuality(self, code1, code2):
        print("test")

    

    def cutColorChannels(self, image):
        if(image.shape[2] == 4):
            return image[:, :, :3]
    


obj = VisualBenchmarks()
image1_path = os.path.join(DATA_PATH, 'test_w3.png')
image2_path = os.path.join(DATA_PATH, 'test_w3.png')
image3_path = os.path.join(DATA_PATH, 'test_youtube.png')

image1 = imread(image1_path)
image2 = imread(image2_path)
image3 = imread(image3_path)

# We only need 3 color channels, so we can ignore the 4th channel
image1 = obj.cutColorChannels(image1)
image2 = obj.cutColorChannels(image2)
image3 = obj.cutColorChannels(image3)

ssim_val = obj.ssim(image1, image2)
print(ssim_val)