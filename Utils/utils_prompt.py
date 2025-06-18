def _get_base_prompt():
    '''
        base Image-to-Code prompt
    '''

    base = """
    You are an expert web developer who specializes in HTML and CSS.
    Your task is to replicate the provided UI screenshot of a webpage pixel-perfectly using HTML and CSS.
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
    Output **only** the complete HTML and CSS code in **one file** — no additional comments or explanations.


    Now convert the following image into HTML/CSS according to these requirements."""
    
    
    return base


def _get_accessibility_reminder():
    # Wcag 2.2
    url_wcag22 = "https://www.w3.org/TR/WCAG22/"

    reminder = f"""Accessibility-first Reminder
        --------------------
        It is *EXTREMELY* important that your HTML/CSS **complies with WCAG 2.2**.   

        Refer to the full spec if in doubt: {url_wcag22}

        Avoid any violations."""
    
    return reminder


def _get_naive_prompt():
    return f"{_get_base_prompt()}\n\nThe image is encoded and attached to this prompt."


def _get_zero_shot_prompt():
    '''
        Zero-Shot:
        Naive Approach but with reference to comply with WCAG standards as a kind of reminder.
        Central Idea: Since modern LLMs are a huge data compresser, it might be enough to give citation to the WCAG-standards

        Similar to Paper: Human or LLM? A Comparative Study on Accessible Code Generation Capability
    '''
    base = _get_base_prompt()
    accessibility_reminder = _get_accessibility_reminder()

    return f"{base}\n\n{accessibility_reminder}\n\nThe image is attached to this prompt."


def _get_iterative_start_prompt():
    """
        Self-and-Refine Approach
        Check here: https://arxiv.org/pdf/2303.17651

        3 Phases
        Build: Use prompt to copy Image as above
        Feedback: Use Accessibility Tools to find violations
        Refine: Use generated Code and found violations to refine the existing lines of code.

        Phase Build:
        This starting prompt for the build phase uses the naive approach
    """
    return _get_naive_prompt()


def _get_iterative_refine_prompt():
    """
        Self-and-Refine Approach
        Check here: https://arxiv.org/pdf/2303.17651

        Phase Refine:
        This prompt is used to refine the output -> solve accessibility violations.
    """

    accessibility_reminder = _get_accessibility_reminder()

    refine_prompt = """In this refinement step, you will:

    1. Analyze the listed accessibility violations below.
    2. Adjust the provided HTML/CSS code so that **all** violations are resolved.
    3. Prioritize accessibility issues with the highest impact.
    4. Preserve layout, structure (tags) and visible content exactly as they are, except for the specific fixes required.
    5. Return **only** the corrected HTML—no additional explanations, no comments, no markdown fences.

    Make sure to only change what is necessary to fix the violations.
    The HTML/CSS is provided below, along with the accessibility issues that need to be addressed.
    """

    return f"{accessibility_reminder}\n\n{refine_prompt}"


def _get_reasoning_prompt():
    '''
        Reasoning Prompt:
        This prompt is used to let the LLM reason about the image and then generate the HTML/CSS.
        It should also take possible accessibility violations into account.
        Use: https://arxiv.org/pdf/2404.02575
    '''

    accessibility_reminder = _get_accessibility_reminder()
    chain_of_thought = """
        Let’s think step by step.
    """

    output_format = """
        Output Format
        --------------------
        When you reply:
        1. Return ONE valid JSON object **and nothing else**.
        2. It MUST have exactly these keys:
        • "thoughts" – your internal reasoning  
        • "code" – a complete HTML/CSS document as described above
    """

    return f"{_get_base_prompt()}\n\n{accessibility_reminder}\n{chain_of_thought}\n\n{output_format}\n\nThe image is attached to this prompt."


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
        case "iterative":
            return _get_iterative_start_prompt()
        case "iterative_refine":
            return _get_iterative_refine_prompt()
        case "reason":
            return _get_reasoning_prompt()
        case _:
            raise ValueError(f"Prompt Strategy {prompt_strategy} is not supported.")



def get_rewrite_text_prompt():
    return """
        Rewrite every visible text in the HTML below.
        • Keep meaning and approximate length (±20 %).
        • Do NOT add/remove elements or attributes.
        Return only HTML, no explanations.
    """