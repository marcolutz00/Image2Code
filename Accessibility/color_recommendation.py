import cv2
import numpy as np
from PIL import ImageColor
import os
from pathlib import Path
import sys
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Accessibility.colors as colors
import Benchmarks.ocr_free_utils as ocr_free_utils



def draw_boxes_on_image(image_path, blocks, out_path="annotated.png", color=(0, 255, 0), thickness=2):
    """
        For test cases
        Just draws boxes in image
    """
    img = cv2.imread(image_path)
    height, width = img.shape[:2]

    for b in blocks:
        x_norm, y_norm, w_norm, h_norm = b["bbox"]
        # x1, y1 = int(x_norm * width), int(y_norm * height)
        # x2, y2 = int((x_norm + w_norm) * width), int((y_norm + h_norm) * height)
        x1 = int(round(x_norm *  width))
        y1 = int(round(y_norm *  height))
        x2 = int(round((x_norm + w_norm) * width))
        y2 = int(round((y_norm + h_norm) * height))

        x1 = max(0, min(x1, width - 1))
        x2 = max(0, min(x2, width - 1))
        y1 = max(0, min(y1, height - 1))
        y2 = max(0, min(y2, height - 1))

        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(img, b["text"][:20], (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    cv2.imwrite(out_path, img)
    # print(f"Image: {out_path}")



def _is_color_too_similar(color1, color2):
    """
        Sometimes color of text not equal, due to bounding of text or similar.
        This can lead to omitting the true background color.
        Solution: Check if color is too similar to font color with euclidean distance
    """
    threshold = 10

    distance = np.sqrt(sum((rgb1 - rgb2)**2 for rgb1, rgb2 in zip(color1, color2)))

    return distance < threshold

def get_background_color(image_path, blocks):
    """
        Just gets background color of each block
        How? By getting all pixel colors of bounding boxes and determining background color as max of found colors (except font color)
    """
    img = cv2.imread(image_path)
    height, width = img.shape[:2]

    background_colors = []

    for block in blocks:
        dict_colors_box = {}

        font_color = block["color"]

        x_norm, y_norm, w_norm, h_norm = block["bbox"]
        x1 = int(round(x_norm *  width))
        y1 = int(round(y_norm *  height))
        x2 = int(round((x_norm + w_norm) * width))
        y2 = int(round((y_norm + h_norm) * height))

        x1 = max(0, min(x1, width - 1))
        x2 = max(0, min(x2, width - 1))
        y1 = max(0, min(y1, height - 1))
        y2 = max(0, min(y2, height - 1))

        for w in range(x1, x2):
            for h in range(y1, y2):
                pixel_color = img[h, w]
                if not np.array_equal(pixel_color, font_color) and not _is_color_too_similar(pixel_color, font_color):
                    if not tuple(pixel_color) in dict_colors_box:
                        dict_colors_box[tuple(pixel_color)] = 1
                    else:
                        dict_colors_box[tuple(pixel_color)] += 1
        
        if len(dict_colors_box) > 0:
            # Third-party snippet (not my code)
            # Source: Stack Overflow – “Getting key with maximum value in dictionary?”
            # Author: ricafeal
            # Link: https://stackoverflow.com/questions/268272/getting-key-with-maximum-value-in-dictionary
            most_common_color = max(dict_colors_box, key=dict_colors_box.get)
            background_colors.append(most_common_color)
            blocks[blocks.index(block)]["background_color"] = most_common_color
        else:
            blocks[blocks.index(block)]["background_color"] = None
            
    

    return background_colors

def _check_large_text_bbox(bbox_height):
    """
        Simple chek if css corresponds to large text
    """

    return True if bbox_height >= 24 else False


def perceived_brightness_rgb(rgb):
    """
        Human Eye has different brightness understanding

    """

    # Third-party snippet (not my code)
    # Source: Stack Overflow – “Formula to determine perceived brightness of RGB color”
    # Author: robmerica
    # Link: https://stackoverflow.com/questions/596216/formula-to-determine-perceived-brightness-of-rgb-color

    g = [(c/255)/12.92 if c/255<=0.03928 else ((c/255+0.055)/1.055)**2.4 for c in rgb]
    # According to official W3C recommendation: https://www.w3.org/TR/WCAG20-TECHS/G18.html
    return 0.2126*g[0] + 0.7152*g[1] + 0.0722*g[2]


def _calculate_contrast_ratio(fg,bg):
    """
        Calculates current contrast ratio
    """
    if fg is None or bg is None:
        return None
    
    luminance1 = perceived_brightness_rgb(fg)
    luminance2 = perceived_brightness_rgb(bg)
    return (max(luminance1,luminance2)+0.05)/(min(luminance1,luminance2)+0.05)


def suggest_foreground_color(block_color, background_color, target):
    """
        Suggests a foreground color that meets the contrast ratio requirement with the background color.
        It uses a simple list of examplary colors and iterates them
    """
    if block_color is None or background_color is None:
        return None
    
    exchange_colors = colors.get_exchange_colors()

    for color in exchange_colors:
        foreground_color = ImageColor.getrgb(color)

        ratio = _calculate_contrast_ratio(foreground_color, background_color)
        if ratio is not None and ratio >= target:
            return color
    
    return None



def calculate_recommended_colors(blocks, image_path):
    """
        If Color Contrast issue exists, color recommendation 
    """
    is_large = False

    original_img = cv2.imread(image_path)
    height, width = original_img.shape[:2]

    for block in blocks:
        is_large = _check_large_text_bbox(block["bbox"][3] * height)
        ratio = _calculate_contrast_ratio(block["color"], block["background_color"])
        if ratio is None:
            block["suggest_color"] = None
            is_large = False
            continue

        limit = 3.0 if is_large else 4.5


        if ratio < limit:
            new_fg = suggest_foreground_color(block["color"], block["background_color"], target=limit)
            block["suggest_color"] = new_fg
            print(f"Updated color for text '{block['text']}' to {new_fg} to meet contrast ratio of {limit}.")

        else:
            block["suggest_color"] = None

            
        is_large = False

def _extract_html_snippet(html_path, text_snippet):
    """
        gets the html snippet based on text snippet
    """
    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")
    # finds all occurrences where the text matches exactly
    matches = soup.find_all(string=lambda s: s and s.strip().lower() ==text_snippet.lower())
    
    if not matches:
        return ""
    
    html_snippet = str(matches[0].parent)

    return html_snippet


def _structure_recommended_colors(blocks, html_path):
    """
        Structures the recommended colors for output
    """
    list_output = []
    for block in blocks:
        new_color = block["suggest_color"]

        if new_color is None:
            continue

        old_color = block["color"]
        old_color_hex =  '#%02x%02x%02x' % old_color
        text = block["text"]

        # Get html Snippet
        html_snippet = _extract_html_snippet(html_path, text)

        list_output.append({
            "text_snippet": text,
            "html_snippet": html_snippet,
            "old_color": old_color_hex,
            "new_color": new_color
        })
    
    return list_output



def get_recommended_colors(html_path, image_path, full_output=False):
    """
        Get recommended colors for the given HTML and image paths.
    """

    modified_image_path = image_path.replace(".png", "_mod.png")
    base_name = image_path.split("/")[-1].split(".")[0]

    os.system(f'python3 "{Path(__file__).parent}/screenshot_single.py" --html "{html_path}" --png "{modified_image_path}"')

    blocks = ocr_free_utils.get_blocks_ocr_free(modified_image_path, html_path)
    # blocks = get_blocks_ocr_free(mod_img, modified_html)

    # For Test
    # draw_boxes_on_image(modified_image_path, blocks, out_path=os.path.join(DIR_PATH, f"{base_name}_annotated.png"))

    background_colors = get_background_color(modified_image_path, blocks)

    calculate_recommended_colors(blocks, image_path)

    # Delete modified image
    os.system(f'rm "{modified_image_path}"')

    if full_output:
        return blocks

    output = _structure_recommended_colors(blocks, html_path)

    return output






# Test cases
if __name__ == "__main__":
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    INPUT_HTML_PATH = os.path.join(DIR_PATH, '..', 'Data', 'Input', 'html')
    INPUT_IMG_PATH = os.path.join(DIR_PATH, '..', 'Data', 'Input', 'images')
    original_html = os.path.join(DIR_PATH, '8.html')
    original_img = os.path.join(DIR_PATH, '8.png')
    mod_img = os.path.join(DIR_PATH, '6_mod.png')
    # modified_html = os.path.join(DIR_PATH, '2_noimg.html')
    # original_html = os.path.join(os.path.dirname(__file__), 'original.html')
    # predict_html_list = os.path.join(os.path.dirname(__file__), 'generated.html')

    output_list = get_recommended_colors(original_html, original_img)

    print(output_list)