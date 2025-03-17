from skimage.metrics import structural_similarity as ssim
from skimage.io import imread
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Input')

class VisualBenchmarks:
    # https://scikit-image.org/docs/0.24.x/auto_examples/transform/plot_ssim.html
    def ssim(self, image1, image2):
        return ssim(image1, image2, win_size=7, channel_axis=-1)
    
    def boundingBoxes(self, code1, code2):
        print("test")

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