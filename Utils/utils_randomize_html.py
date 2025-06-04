import pathlib
import random
import re
from bs4 import BeautifulSoup
import cssutils
import webcolors
from colorsys import rgb_to_hls, hls_to_rgb
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LLMs.LLMClient import LLMClient
import Utils.utils_prompt as utils_prompt
import Utils.utils_general as utils_general
import Utils.utils_dataset as utils_dataset
import Utils.utils_html as utils_html

CURR_DIR = pathlib.Path(__file__).parent
INPUT_HTML_DIR = pathlib.Path(__file__).parent.parent / "Data" / "Input" / "html"

# Change Parameter
FONT_ALTERNATIVES    = [
    "Inter, sans-serif",
    "Poppins, sans-serif",
    "'Open Sans', sans-serif",
    "'Roboto Slab', serif",
    "'Fira Sans', sans-serif"
]
# 20 degrees
HUE_SHIFT = 20
# 10 percent
SAT_LUM_SHIFT = 0.1 

LENGTH_RE = re.compile(r"(-?\d*\.?\d+)(px|rem|em|%)")


def change_color(c):
    '''
        Take color and return slightly shift
        -> still similar to original
    '''
    try:
        rgb = webcolors.name_to_rgb(c)
    except ValueError:
        try:
            rgb = webcolors.hex_to_rgb(c)
        except ValueError:
            return c  
    
    # Change to hls
    hue, lightness, saturation = rgb_to_hls(*(v/255 for v in rgb))

    # Shift hue, saturation and lightness
    hue = (hue + HUE_SHIFT/360 * random.choice([-1, 1])) % 1
    saturation = min(max(saturation + random.uniform(-SAT_LUM_SHIFT, SAT_LUM_SHIFT), 0), 1)
    lightness = min(max(lightness + random.uniform(-SAT_LUM_SHIFT, SAT_LUM_SHIFT), 0), 1)

    # Convert back to RGB and then to hex
    r, g, b = [round(x*255) for x in hls_to_rgb(hue, lightness, saturation)]
    return webcolors.rgb_to_hex((r, g, b))



def mutate_declaration(name, value):
    name = name.lower()
    if name in ("font-family",):
        return random.choice(FONT_ALTERNATIVES)
    if name in ("color", "background", "background-color", "border-color"):
        return change_color(value)
    
    # no cchange
    return value 

def mutate_css(css_text):
    """
        Randomizes CSS 
    """
    sheet = cssutils.parseString(css_text)

    for rule in sheet:
        if rule.type == rule.STYLE_RULE:
            for decl in list(rule.style):
                # Mutate each declaration
                new_val = mutate_declaration(decl.name, decl.value)

                # If the value has changed -> update 
                if new_val != decl.value:
                    rule.style[decl.name] = new_val

    return sheet.cssText.decode()

def strip_styles(soup: BeautifulSoup):
    """
        deletes <style> & style=""
        -> necessary in order to rewrite text
    """
    # get style blocks
    styles = [tag.extract() for tag in soup.find_all('style')]

    # store inline styles in mpa
    inline_map = {}
    for idx, tag in enumerate(soup.find_all(style=True)):
        key = f"data-style-{idx}"
        inline_map[key] = tag['style']
        tag[key] = tag['style']
        del tag['style']

    return soup, styles, inline_map

def reattach_styles(rewritten_html: str, styles, inline_map):
    """
        Reattaches styles to the new HTML
    """
    soup = BeautifulSoup(rewritten_html, "html.parser")

    # add style blocks back to head
    head = soup.head or soup
    for s in styles:
        head.append(s)

    # add inline styles back to tags
    for tag in soup.find_all():
        for k in list(tag.attrs):
            if k.startswith("data-style-") and k in inline_map:
                tag['style'] = inline_map[k]
                del tag[k]

    return str(soup)



async def process_html(path: pathlib.Path, client, out_dir="out"):
    print(f"Start of {path.name}...")

    soup = BeautifulSoup(path.read_text("utf-8"), "html.parser")
    soup_no_style, styles, inline_map = strip_styles(soup)

    prompt = utils_prompt.get_rewrite_text_prompt()
    
    raw_html = await client.generate_text_rewrite(prompt, str(soup_no_style))
    clean_html = utils_html.clean_html_result(raw_html)

    final_html = reattach_styles(clean_html, styles, inline_map)


    soup = BeautifulSoup(final_html, "html.parser")

    # randomize css
    for tag in soup.find_all("style"):
        tag.string = mutate_css(tag.string or "")


    for tag in soup.find_all("style"):
        tag.string = mutate_css(tag.string or "")
    for tag in soup.find_all(style=True):
        style = cssutils.parseStyle(tag["style"])
        for decl in list(style):
            new_val = mutate_declaration(decl.name, decl.value)
            if new_val != decl.value:
                style[decl.name] = new_val
        tag["style"] = style.cssText

    # Store
    out_path = pathlib.Path(out_dir, path.name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(str(soup), encoding="utf-8")
    print(f"{path.name} {out_path}")


async def main():
    strategy = utils_general.get_model_strategy("gemini")
    client = LLMClient(strategy)
    
    html_files = list(INPUT_HTML_DIR.glob("*.html"))
    tasks = [
        process_html(file, client)
        for file in utils_dataset.sorted_alphanumeric(html_files)
    ]
    await asyncio.gather(*tasks)

# Start
if __name__ == "__main__":
    asyncio.run(main())