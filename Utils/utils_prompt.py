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

def _get_few_shot_prompt():
    """
        xxx
        
        examples from:
        https://www.w3.org/
    """

    base = _get_base_prompt()
    accessibility_reminder = _get_accessibility_reminder()

    few_shot_instructions = """
    Detailed accessibility rules with correct/incorrect examples for each rule.
    Each rule comes with [name, description, correct_example, counter_example]:

    [
    "Color Contrast",
    "WCAG 2.1 SC 1.4.3 Contrast (Minimum) – body text must present at least a 4.5 : 1 contrast ratio against its background.",
    "<p style=\"color:#000000;background:#ffffff;\">Readable text</p>",
    "<p style=\"color:#ffff99;background:#ffffff;\">Low-contrast text</p>"
    ],
    [
    "Alt-Text",
    "WCAG 2.1 SC 1.1.1 Non-text Content – every meaningful <img> needs a concise alt attribute.",
    "<img src=\"newsletter.gif\" alt=\"Free newsletter. Get free recipes, news, and more. Learn more.\">",
    "<img src=\"animal.jpg\">"
    ],
    [
    "Link Name",
    "WCAG 2.1 SC 2.4.4 Link Purpose (In Context) – link text must clearly describe its destination.",
    "<a href=\"routes.html\">Current routes at Boulders Climbing Gym</a>",
    "<a href=\"routes.html\">Click here</a>"
    ],
    [
    "FormLabel",
    "WCAG 2.1 SC 1.3.1 Info & Relationships – every form control needs a visible label bound programmatically.",
    "<input type=\"checkbox\" id=\"notification\" name=\"notify\" value=\"delays\">\n<label for=\"notification\">Notify me of delays</label>",
    "<input type=\"checkbox\" id=\"notification\" name=\"notify\" value=\"delays\">"
    ],
    [
    "Landmark Regions",
    "WCAG 2.1 SC 1.3.1 / 2.4.1 – page regions must be identified with ARIA or HTML5 landmarks so users can navigate by region.",
    "<nav aria-label=\"Primary\">\n  …\n</nav>\n<nav aria-label=\"Secondary\">\n  …\n</nav>",
    "<div id=\"primary-nav\">…</div><div id=\"secondary-nav\">…</div>"
    ],
    [
    "Table Headers",
    "WCAG 2.1 SC 1.3.1 Info & Relationships – data tables need <th> headers with proper scope so cell–header relationships are programmatically determinable.",
    "<table>\n  <tr><th scope=\"col\">Monday</th><th scope=\"col\">Tuesday</th></tr>\n  <tr><th scope=\"row\">9 am</th><td>Math</td><td>Art</td></tr>\n</table>",
    "<table>\n  <tr><td>Monday</td><td>Tuesday</td></tr>\n  <tr><td>9 am</td><td>Math</td><td>Art</td></tr>\n</table>"
    ],
    [
    "Heading Structure",
    "WCAG 2.1 SC 2.4.10 / 1.3.1 – headings must be used to convey document structure in a logical hierarchy.",
    "<h1>Cooking Techniques</h1>\n<h2>Cooking with Oil</h2>\n<h3>Deep-frying</h3>",
    "<h3>Cooking Techniques</h3>\n<h5>Cooking with Oil</h5>"
    ],
    [
    "Page Language",
    "WCAG 2.1 SC 3.1.1 Language of Page – the default language of the document must be set with the lang attribute on <html>.",
    "<!DOCTYPE html>\n<html lang=\"en\">\n  …\n</html>",
    "<!DOCTYPE html>\n<html>\n  …\n</html>"
    ]

    """

    return f"{base}\n\n{accessibility_reminder}\n\n{few_shot_instructions}\n\nThe image is attached to this prompt."



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

    The violations are provided in the following format:
    Violations:
    {
        "html": HTML/CSS which has to be fixed,
        "accessibility_violations": 
        [
            {
                "snippet": The code snippet with the issue, 
                "id": The Wcag issue ID, 
                "source": The source of the issue (e.g., axe, pa11y, lighthouse),
                "message": Message describing the issue, 
                "impact": impact level (critical, serious, moderate, minor)
            },
            { ... }
        ]
    }
    """

    return f"{accessibility_reminder}\n\n{refine_prompt}"



def _get_composite_prompt():
    """
        Composite Prompt:
        Combines iterative and color
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

    The violations are provided in the following format:
    Violations:
    {
        "html": HTML/CSS which has to be fixed,
        "accessibility_violations": 
        [
            {
                "snippet": The code snippet with the issue, 
                "id": The Wcag issue ID, 
                "source": The source of the issue (e.g., axe, pa11y, lighthouse),
                "message": Message describing the issue, 
                "impact": impact level (critical, serious, moderate, minor)
            },
            { ... }
        ]
    }
    """

    color_recommendation = """
        Color-Contrast Recommendations:
        Whenever a color-contrast violation is detected, we propose
        an accessible color alternative in the following format:

        Color Recommendations:
        [{
            "text_snippet": "Text that needs to be changed",
            "old_color": "#xxxxxx",
            "new_color": "#yyyyyy"
        }]

        Use these recommendations to update the HTML/CSS code.
        Do not change any other elements or attributes.
    """

    return f"{accessibility_reminder}\n\n{refine_prompt}\n\n{color_recommendation}"



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
        case "iterative":
            return _get_iterative_refine_prompt()
        case "composite":
            return _get_composite_prompt()
        case _:
            raise ValueError(f"Prompt Strategy {prompt_strategy} is not supported.")



def get_rewrite_text_prompt():
    return """
        Rewrite every visible text in the HTML below.
        • Keep meaning and approximate length (±20 %).
        • Do NOT add/remove elements or attributes.
        Return only HTML, no explanations.
    """