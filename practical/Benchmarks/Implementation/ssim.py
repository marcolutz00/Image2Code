import os
import sys
from skimage.metrics import structural_similarity as ssim
from skimage.io import imread

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Utils.utils as utils

def ssim_score(image1_path, image2_path):
    image1 = imread(image1_path)
    image2 = imread(image2_path)

    image1 = utils.cutColorChannels(image1)
    image2 = utils.cutColorChannels(image2)

    return ssim(image1, image2, win_size=7, channel_axis=-1)