import cv2
import numpy as np
from PIL import Image, ImageColor
import os
from bs4 import BeautifulSoup, NavigableString, Tag, Comment
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import colors as colors


def rgb_to_hex(rgb):
    """Convert an RGB tuple to hexadecimal format."""
    return '{:02X}{:02X}{:02X}'.format(*rgb)


class ColorPool:
    def __init__(self, offset=0):

        color_values = list(range(10, 251, 16))
        color_list = [((r + offset) % 256, (g + offset) % 256, (b + offset) % 256) for r in color_values for g in color_values for b in color_values]
        self.color_pool = [rgb_to_hex(color) for color in color_list]

    def pop_color(self):
        if self.color_pool:
            return self.color_pool.pop()
        else:
            raise NotImplementedError


def process_html(input_file_path, output_file_path, offset=0):
    # Read the input HTML file
    with open(input_file_path, 'r') as file:
        soup = BeautifulSoup(file, 'html.parser')

    def update_style(element, property_name, value):
        # Update the element's style attribute with the given property and value
        # Adding !important to ensure the style overrides others
        important_value = f"{value} !important"
        styles = element.attrs.get('style', '').split(';')
        updated_styles = [s for s in styles if not s.strip().startswith(property_name) and len(s.strip()) > 0]
        updated_styles.append(f"{property_name}: {important_value}")
        element['style'] = '; '.join(updated_styles).strip()

    # Set the background color of all elements to white
    for element in soup.find_all(True):
        update_style(element, 'background-color', 'rgba(255, 255, 255, 0.0)')

    color_pool = ColorPool(offset)

    # Assign a unique color to text within each text-containing element
    text_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'a', 'b', 'li', 'table', 'td', 'th', 'button', 'footer', 'header', 'figcaption']  # Add more tags as needed
    for tag in soup.find_all(text_tags):
        color = f"#{color_pool.pop_color()}"
        update_style(tag, 'color', color)
        update_style(tag, 'opacity', 1.0)

    # Write the modified HTML to a new file
    with open(output_file_path, 'w') as file:
        file.write(str(soup))


def similar(n1, n2):
    if abs(n1 - n2) <= 8:
        return True
    else:
        return False


def find_different_pixels(image1_path, image2_path):
    # Open the images
    img1 = Image.open(image1_path)
    img2 = Image.open(image2_path)

    # Ensure both images are of the same size
    if img1.size != img2.size:
        print(f"[Warning] Images are not the same size, {image1_path}, {image2_path}")
        return None

    # Convert images to RGB if they are not
    img1 = img1.convert('RGB')
    img2 = img2.convert('RGB')

    # Get pixel data
    pixels1 = img1.load()
    pixels2 = img2.load()

    # List to store coordinates of different pixels
    different_pixels = []

    # Iterate through each pixel
    for x in range(img1.size[0]):
        for y in range(img1.size[1]):
            # Compare pixel colors
            r1, g1, b1 = pixels1[x, y]
            r2, g2, b2 = pixels2[x, y]
            if similar((r1 + 50) % 256, r2) and similar((g1 + 50) % 256, g2) and similar((b1 + 50) % 256, b2):
                different_pixels.append((y, x))

    if len(different_pixels) > 0:
        return np.stack(different_pixels)
    else:
        return None


def extract_text_with_color(html_file):
    def get_color(tag):
        if 'style' in tag.attrs:
            styles = tag['style'].split(';')
            color_style = [s for s in styles if 'color' in s and 'background-color' not in s]
            if color_style:
                color = color_style[-1].split(':')[1].strip().replace(" !important", "")
                if color[0] == "#":
                    return color
                else:
                    try:
                        if color.startswith('rgb'):
                            color = tuple(map(int, color[4:-1].split(',')))  # Extract the RGB values
                        else:
                            color = ImageColor.getrgb(color)  # Convert named color to RGB
                        return '#{:02x}{:02x}{:02x}'.format(*color)  # Convert RGB to hexadecimal
                    except ValueError:
                        print(f"Warning: unable to identify or convert color in {html_file}...", color)
                        return None
        return None

    def extract_text_recursive(element, parent_color='#000000'):
        if isinstance(element, Comment):
            return None
        elif isinstance(element, NavigableString):
            text = element.strip()
            return (text, parent_color) if text else None

        elif isinstance(element, Tag):
            current_color = get_color(element) or parent_color
            children_texts = filter(None, [extract_text_recursive(child, current_color) for child in element.children])
            return list(children_texts)

    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        body = soup.body
        return extract_text_recursive(body) if body else []


def flatten_tree(tree):
    flat_list = []

    # Helper function to recursively flatten the tree
    def flatten(node):
        if isinstance(node, list):
            for item in node:
                flatten(item)
        else:
            flat_list.append(node)

    # Flatten the tree
    flatten(tree)
    return flat_list


def average_color(image_path, coordinates):
    """
    Calculates the average color of the specified coordinates in the given image.

    :param image: A PIL Image object.
    :param coordinates: A 2D numpy array of coordinates, where each row represents [x, y].
    :return: A tuple representing the average color (R, G, B).
    """
    # Convert image to numpy array
    image_array = np.array(Image.open(image_path).convert('RGB'))

    # Extract colors at the specified coordinates
    colors = [image_array[x, y] for x, y in coordinates]

    # Calculate the average color
    avg_color = np.mean(colors, axis=0)

    return tuple(avg_color.astype(int))


def get_blocks_from_image_diff_pixels(image_path, html_text_color_tree, different_pixels):
    image = cv2.imread(image_path)
    x_w = image.shape[0]
    y_w = image.shape[1]

    def hex_to_bgr(hex_color):
        """
        Converts a hex color string to a BGR color tuple.
        """
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return rgb[::-1]


    def get_intersect(arr1, arr2):
        # Reshape the arrays to 1D
        arr1_reshaped = arr1.view([('', arr1.dtype)] * arr1.shape[1])
        arr2_reshaped = arr2.view([('', arr2.dtype)] * arr2.shape[1])

        # Find the intersection
        common_rows = np.intersect1d(arr1_reshaped, arr2_reshaped)

        # Reshape the result back to 2D, if needed
        common_rows = common_rows.view(arr1.dtype).reshape(-1, arr1.shape[1])
        return common_rows


    blocks = []
    for item in html_text_color_tree:
        try:
            color = np.array(hex_to_bgr(item[1]), dtype="uint8")
        except:
            continue
        
        lower = color - 4
        upper = color + 4

        mask = cv2.inRange(image, lower, upper)

        coords = np.column_stack(np.where(mask > 0))

        coords = get_intersect(coords, different_pixels)

        if coords.size == 0:
            continue

        x_min, y_min = np.min(coords, axis=0)
        x_max, y_max = np.max(coords, axis=0)
        color = average_color(image_path.replace("_p.png", ".png"), coords)

        blocks.append({'text': item[0].lower(), 'bbox': (y_min / y_w, x_min / x_w, (y_max - y_min + 1) / y_w, (x_max - x_min + 1) / x_w), 'color': color})
    return blocks


def get_itermediate_names(image_path, html_path):
    return html_path, html_path.replace(".html", "_p.html"), html_path.replace(".html", "_p_1.html"), image_path.replace(".png", "_p.png"), image_path.replace(".png", "_p_1.png")

def get_blocks_ocr_free(image_path, html_path):
    html, p_html, p_html_1, p_png, p_png_1 = get_itermediate_names(image_path, html_path)
    process_html(html, p_html)
    process_html(html, p_html_1, offset=50)


    os.system(f'python3 "{Path(__file__).parent}/screenshot_single.py" --html "{p_html}" --png "{p_png}"')
    os.system(f'python3 "{Path(__file__).parent}/screenshot_single.py" --html "{p_html_1}" --png "{p_png_1}"')

    different_pixels = find_different_pixels(p_png, p_png_1)

    if different_pixels is None:
        print(f"[Warning] Unable to get pixels with different colors from {p_png}, {p_png_1}...")
        os.system(f'rm "{p_html}" "{p_png}" "{p_html_1}" "{p_png_1}"')
        return []
    #
    html_text_color_tree = flatten_tree(extract_text_with_color(p_html))
    try:
        blocks = get_blocks_from_image_diff_pixels(p_png, html_text_color_tree, different_pixels)
    except:
        print(f"[Warning] Unable to get blocks from {p_png}...")
        os.system(f'rm "{p_html}" "{p_png}" "{p_html_1}" "{p_png_1}"')
        return []

    os.system(f'rm "{p_html}" "{p_png}" "{p_html_1}" "{p_png_1}"')
    return blocks


def draw_boxes_on_image(image_path, blocks, out_path="annotated.png", color=(0, 255, 0), thickness=2):
    """
        Test boxes 
    """
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    for b in blocks:
        x_norm, y_norm, w_norm, h_norm = b["bbox"]
        # x1, y1 = int(x_norm * w), int(y_norm * h)
        # x2, y2 = int((x_norm + w_norm) * w), int((y_norm + h_norm) * h)
        x1 = int(round(x_norm *  w))
        y1 = int(round(y_norm *  h))
        x2 = int(round((x_norm + w_norm) * w))
        y2 = int(round((y_norm + h_norm) * h))

        x1 = max(0, min(x1, w - 1))
        x2 = max(0, min(x2, w - 1))
        y1 = max(0, min(y1, h - 1))
        y2 = max(0, min(y2, h - 1))

        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(img, b["text"][:20], (x1, max(15, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    cv2.imwrite(out_path, img)
    print(f"✓ Annotiertes Bild gespeichert unter  {out_path}")



def get_background_color(image_path, blocks):
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
                if not np.array_equal(pixel_color, font_color):
                    if not tuple(pixel_color) in dict_colors_box:
                        dict_colors_box[tuple(pixel_color)] = 1
                    else:
                        dict_colors_box[tuple(pixel_color)] += 1
        
        if len(dict_colors_box) > 0:
            # https://stackoverflow.com/questions/268272/getting-key-with-maximum-value-in-dictionary
            most_common_color = max(dict_colors_box, key=dict_colors_box.get)
            background_colors.append(most_common_color)
            blocks[blocks.index(block)]["background_color"] = most_common_color
        else:
            blocks[blocks.index(block)]["background_color"] = None
            
    

    return background_colors

def is_large_text_bbox(bbox_h_img, dpr, is_bold=False):
    css_h = bbox_h_img / dpr
    return (css_h >= 24) or (is_bold and css_h >= 18.66)

def rel_lum(rgb):
    g = [(c/255)/12.92 if c/255<=0.03928 else ((c/255+0.055)/1.055)**2.4 for c in rgb]
    return 0.2126*g[0] + 0.7152*g[1] + 0.0722*g[2]


def contrast_ratio(fg,bg):
    """
    """
    if fg is None or bg is None:
        return None
    L1,L2 = rel_lum(fg), rel_lum(bg)
    return (max(L1,L2)+0.05)/(min(L1,L2)+0.05)


def suggest_foreground_color(block_color, background_color, target):
    """
    Suggests a foreground color that meets the contrast ratio requirement with the background color.
    """
    if block_color is None or background_color is None:
        return None
    
    exchange_colors = colors.get_exchange_colors()

    for color in exchange_colors:
        foreground_color = ImageColor.getrgb(color)

        ratio = contrast_ratio(foreground_color, background_color)
        if ratio is not None and ratio >= target:
            return color
    
    return None



def calculate_recommended_colors(blocks, target_contrast=4.5):
    """
    a
    """
    is_large = False
    dpr = 1.0 
    for block in blocks:
        is_large = is_large_text_bbox(block["bbox"][3], dpr, is_bold=False)
        ratio = contrast_ratio(block["color"], block["background_color"])
        if ratio is None:
            block["suggest_color"] = None
            continue
        limit = 3.0 if is_large else 4.5  

        # 5% tolerance
        tolerance = 0.95

        if ratio * tolerance < target_contrast:
            new_fg = suggest_foreground_color(block["color"], block["background_color"], target=limit)
            block["suggest_color"] = new_fg
            print(f"Updated color for text '{block['text']}' to {new_fg} to meet contrast ratio of {limit}.")

        else:
            block["suggest_color"] = None
            continue

            
        is_large = False

def delete_images(html_path):
    """
    
    """
    html_path_str = str(html_path)
    output_path = Path(html_path_str.replace(".html", "_noimg.html"))
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    for img in soup.find_all("img"):
        img.decompose()

    # write in modified html
    output_path.write_text(str(soup), encoding="utf-8")



if __name__ == "__main__":
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    INPUT_HTML_PATH = os.path.join(DIR_PATH, '..', 'Data', 'Input', 'html')
    INPUT_IMG_PATH = os.path.join(DIR_PATH, '..', 'Data', 'Input', 'images')
    original_html = os.path.join(DIR_PATH, '9.html')
    original_img = os.path.join(DIR_PATH, '9.png')
    mod_img = os.path.join(DIR_PATH, '9_mod.png')
    modified_html = os.path.join(DIR_PATH, '2_noimg.html')
    # original_html = os.path.join(os.path.dirname(__file__), 'original.html')
    # predict_html_list = os.path.join(os.path.dirname(__file__), 'generated.html')

    os.system(f'python3 "{Path(__file__).parent}/screenshot_single.py" --html "{original_html}" --png "{mod_img}"')


    # delete_images(Path(original_html))

    # Predicted html (generated is a list), while original is a single html
    blocks = get_blocks_ocr_free(original_img, original_html)
    # blocks = get_blocks_ocr_free(mod_img, modified_html)

    # Für Test
    draw_boxes_on_image(mod_img, blocks, out_path=os.path.join(DIR_PATH, "9annotated.png"))

    background_colors = get_background_color(mod_img, blocks)

    calculate_recommended_colors(blocks)

    print(blocks)