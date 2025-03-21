from playwright.async_api import async_playwright
import os
import asyncio
import subprocess
import json

AXE_CORE_PATH = "/usr/local/lib/node_modules/axe-core/axe.min.js"
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data')
INPUT_DATA_PATH = os.path.join(DATA_PATH, 'Input', 'html')
OUTPUT_DATA_PATH = os.path.join(DATA_PATH, 'Output', 'openai', 'html')

'''
    In the following, we are going to use different automatic accessibility tools
'''

# 1. axe-core (npm) infos here: https://hackmd.io/@gabalafou/ByvwfEC0j
async def axe_core(html_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(f"file://{os.path.abspath(html_path)}")

        await page.add_script_tag(path=AXE_CORE_PATH)

        axe_results = await page.evaluate("""
            async () => {
                return await axe.run();
            }
        """)

        axe_violations = axe_results["violations"]

    return axe_violations


# 2. Pa11y (npm) infos here: https://www.npmjs.com/package/pa11y
# Uses HTML_CodeSniffer under the hood
async def pa11y(html_path):
    output_type = "json"

    local_html = f"file://{os.path.abspath(html_path)}"
    pa11y_command = ["pa11y", local_html, "--reporter", output_type] # in order to analyze output better --reporter json (or csv)

    output_cmd = subprocess.run(pa11y_command, capture_output=True, text=True)

    if output_cmd.stderr:
        print(output_cmd.stderr)
        return

    if output_type == "json":
        output_cmd_json = json.loads(output_cmd.stdout)
        return output_cmd_json
    
    return output_cmd.stdout



async def getAccessibilityIssues(html_path):
    axe_core_results = await axe_core(html_path)
    pa11y_results = await pa11y(html_path)

    return axe_core_results, pa11y_results




# Tests
# asyncio.run(getAccessibilityIssues(f"{OUTPUT_DATA_PATH}/1.html"))
