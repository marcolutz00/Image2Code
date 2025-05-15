def _get_base_prompt():
    '''
        returns prompt
    '''

    base = """
    Your task is to replicate the provided UI mock-up pixel-perfectly using HTML and CSS.
    Pay close attention to every detail and follow these guidelines:  
    1. **Layout**  
    Structure the markup so the spatial arrangement of every element exactly matches the screenshot.
    
    2. **Styling**  
    Reproduce fonts, colors, spacing, sizes, borders, shadows, and any other visual details as closely as possible.

    3. **Content**  
    Include all visible text, icons, and graphic elements.

    4. **Image placeholders**  
    Blue boxes represent images. Use  
    `<img src="src/rick.jpg" width="…" height="…" alt="">`  
    to reserve space; the actual image content is irrelevant. 
    However, the appropriate height and width is very important.

    5. **Delivery format**  
    Output **only** the complete HTML and CSS code in **one file**—no additional comments or explanations.


    Now convert the following image into HTML/CSS according to these requirements."""
    # base = """Please describe what you see on the image."""
    
    # Prompt for LLm
    return base


def _get_naive_prompt():
    return f"{_get_base_prompt()}\n\nThe image is encoded and attached to this prompt."

def _get_zero_shot_prompt():
    '''
        Zero-Shot:
        Naive Approach but with reference to comply with WCAG standards as a kind of reminder.
        Central Idea: Since modern LLMs are a huge data compresser, it might be enough to give citation to the WCAG-standards
    '''
    base = _get_base_prompt()
    
    # Wcag 2.1
    url_wcag = "https://www.w3.org/TR/WCAG21/"
    # Just some citation of the wcag website above, to guide the LLM correctly
    memory_wcag = """
        Abstract

        Web Content Accessibility Guidelines (WCAG) 2.1 covers a wide range of recommendations for making web content more accessible. 
        Following these guidelines will make content more accessible to a wider range of people with disabilities, including accommodations 
        for blindness and low vision, deafness and hearing loss, limited movement, speech disabilities, photosensitivity, and combinations of these, 
        and some accommodation for learning disabilities and cognitive limitations; but will not address every user need for people with these disabilities. 
        These guidelines address accessibility of web content on any kind of device (including desktops, laptops, kiosks, and mobile devices). Following these 
        guidelines will also often make web content more usable to users in general.
    """

    zero_shot_prompt = f"""
        Accessibility add-on
        --------------------
        Apply the following WCAG 2.1 principles **even if this requires small visual deviations**:
        1. WCAG url: {url_wcag}
        2. Memorization for you: {memory_wcag}
    """

    return f"{base}\n\n{zero_shot_prompt}\n\nThe image is encoded and attached to this prompt."

def _get_few_shot_prompt():
    pass

def _get_reasoning_prompt():
    pass

def _get_own_prompt():
    pass


def get_prompt(prompt_strategy):
    '''
        Decision which prompt to take

        TODO: Define further strategies.
    '''
    match prompt_strategy:
        case "naive":
            return _get_naive_prompt()
        case "zero-shot":
            return _get_zero_shot_prompt()
        case "few-shot":
            return _get_few_shot_prompt()
        case "reason":
            return _get_reasoning_prompt()
        case _:
            raise ValueError(f"Prompt Strategy {prompt_strategy} is not supported.")



def get_system_instructions():
    return ('''
        You are a senior front-end engineer. 
        When asked, you output a single self-contained HTML5 document 
        with embedded CSS that reproduces the requested UI as faithfully as possible. 
        Return only raw code (no Markdown fences, no explanations). 
        Use semantic elements when obvious, keep the CSS concise and well-structured, 
        and never embed images as base64 unless explicitly instructed.
    ''')