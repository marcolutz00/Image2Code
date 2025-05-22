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
    Blue boxes represent images. Use `<img>` and as a source the placeholder file `src="src/placeholder.jpg"`
    to reserve space. However, the appropriate height and width is very important.

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

    zero_shot_prompt = f"""
        Accessibility-first Reminder
        --------------------
        It is *EXTREMELY* important that your HTML/CSS **complies with WCAG 2.1**.   
        If pixel accuracy ever clashes with accessibility, **accessibility takes priority**

        Remember the four WCAG Principles:
        * **Perceivable**  – Information must be detectable by every user.  
        * **Operable**     – Interface elements must be usable through any input method.  
        * **Understandable** – Content and interactions must be comprehensible and predictable.  
        * **Robust**       – Code must be reliable across current and future technologies, including assistive tools.

        Refer to the full spec if in doubt: {url_wcag}
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