def _get_base_prompt():
    '''
        returns prompt
    '''

    base = """Your task is to meticulously replicate the provided UI image using HTML and CSS. 
    Pay close attention to every detail, including:  
    * **Layout:** Structure the HTML to match the image's arrangement of elements. 
    * **Styling:** Accurately reproduce colors, fonts, spacing, and other visual attributes using CSS. 
    * **Content:** Include all text, icons, and other visual elements present in the image. 
    * **Placeholders:** Treat any blue-filled boxes as image placeholders. 

    Important for images:
    Use the `<img>` tag with a empty src but appropriate `height` and `width` attributes to represent these.  
    The content of the image is not important, but only the fact, that it is marked as one in HTML/CSS
    You will provide the complete HTML and CSS code in one file required to render the image.

    Now, convert the following image into HTML/CSS code. 
    Remember to copy everything you see as precisely as possible. 
    Return only the complete HTML and CSS code, without any additional text or explanations."""
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
        WCAG url: {url_wcag}
        Memorization for you: {memory_wcag}
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

