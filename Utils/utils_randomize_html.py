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

random.seed(11)

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



def _mutate_declaration(name, value):
    name = name.lower()
    if name in ("font-family",):
        return random.choice(FONT_ALTERNATIVES)
    if name in ("color", "background", "background-color", "border-color"):
        return change_color(value)
    
    # no cchange
    return value 

def _mutate_css(css_text):
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

def _strip_styles(soup: BeautifulSoup):
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

def _reattach_styles(rewritten_html: str, styles, inline_map):
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



async def randomize_html_low(path: pathlib.Path, client, out_dir="out"):
    """
        Radnomizes HTML content:
        - Rewrite text content
        - change colors
        - change font families

        -> low, because not many changes
    """
    print(f"Start of {path.name}...")

    soup = BeautifulSoup(path.read_text("utf-8"), "html.parser")
    soup_no_style, styles, inline_map = _strip_styles(soup)

    prompt = utils_prompt.get_rewrite_text_prompt()
    
    raw_html = await client.get_rewrite_text_prompt(prompt, str(soup_no_style))
    clean_html = utils_html.clean_html_result(raw_html)

    final_html = _reattach_styles(clean_html, styles, inline_map)


    soup = BeautifulSoup(final_html, "html.parser")

    # randomize css
    for tag in soup.find_all("style"):
        tag.string = _mutate_css(tag.string or "")


    for tag in soup.find_all("style"):
        tag.string = _mutate_css(tag.string or "")
    for tag in soup.find_all(style=True):
        style = cssutils.parseStyle(tag["style"])
        for decl in list(style):
            new_val = _mutate_declaration(decl.name, decl.value)
            if new_val != decl.value:
                style[decl.name] = new_val
        tag["style"] = style.cssText

    # Store
    out_path = pathlib.Path(out_dir, path.name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(str(soup), encoding="utf-8")
    print(f"{path.name} {out_path}")







def _swap_header_footer(soup: BeautifulSoup):
    """
        Swap header and footers
    """
    header = soup.find("header")
    footer = soup.find("footer")

    if header and footer:
        header.replace_with(footer.extract())
        soup.body.insert(0, header)


def _swap_between_files(files: list, output_path: pathlib.Path):
    """
        Randomly swaps headers and footers between files
    """
    # get all files as soups
    soups = []
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            html = f.read()
        soups.append(BeautifulSoup(html, "html.parser"))
    
    # get all headers and footers
    headers = [soup.header.extract() if soup.header else None for soup in soups]
    footers = [soup.footer.extract() if soup.footer else None for soup in soups]

    # Mix up everthing
    random.shuffle(headers)
    random.shuffle(footers)

    # Combine back
    for i, soup in enumerate(soups):
        if headers[i]:
            soup.body.insert(0, headers[i])
        if footers[i]:
            soup.body.append(footers[i])

        # Store the modified soup back to the file
        with open(output_path / f"2_{os.path.basename(files[i])}", "w", encoding="utf-8") as f:
            f.write(str(soup))


def randomize_html_high(input_path: pathlib.Path, output_path: pathlib.Path):
    """
        Randomizes HTML content:
        - Change Layout: Exchange header, footer, ...
        - Exchange layouts within different files
        -> high, because changes more visible
    """

    # get 10 random numbers
    random_numbers = random.sample(range(1, 54), 10)

    for random_number in random_numbers:
        html_file = input_path / f"{random_number}.html"
        if not html_file.exists():
            print(f"{html_file} not found")
            continue
        
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")


        # do internal randomization within files
        _swap_header_footer(soup)

        with open(output_path / f"{random_number}.html", "w", encoding="utf-8") as f:
            f.write(str(soup))


    # do external randomization between files
    _swap_between_files([os.path.join(input_path, f"{i}.html") for i in random_numbers], output_path)






async def main():
    # Test in order to randomize html files (low)
    # strategy = utils_general.get_model_strategy("gemini")
    # client = LLMClient(strategy)
    
    # html_files = list(INPUT_HTML_DIR.glob("*.html"))
    # tasks = [
    #     randomize_html_low(file, client)
    #     for file in utils_dataset.sorted_alphanumeric(html_files)
    # ]
    # await asyncio.gather(*tasks)

    # Test in order to randomize html files (high) (not working yet, can be deleted)
    # input_path = INPUT_HTML_DIR
    # output_path = CURR_DIR.parent / "test"
    # randomize_html_high(input_path, output_path)

    # Do it manually
    # list of random numbers
    random_numbers = random.sample(range(1, 54), 10)
    random_numbers_shuffle_header = random.sample(random_numbers, len(random_numbers))
    random.seed(13)
    random_numbers_shuffle_footer = random.sample(random_numbers, len(random_numbers))
    zip_random_numbers = list(zip(random_numbers, random_numbers_shuffle_header, random_numbers_shuffle_footer))
    print(f"Random numbers: {random_numbers}")
    print(f"Random numbers zip : {zip_random_numbers}")

# Start
if __name__ == "__main__":
    asyncio.run(main())