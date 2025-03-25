from playwright.async_api import async_playwright
import os
import asyncio
import subprocess
import json
from pathlib import Path

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
    pa11y_command = ["pa11y", local_html, "--runner", "htmlcs", "--reporter", output_type] # in order to analyze output better --reporter json (or csv)

    output_cmd = subprocess.run(pa11y_command, capture_output=True, text=True)

    if output_cmd.stderr:
        print(output_cmd.stderr)
        return

    if output_type == "json":
        output_cmd_json = json.loads(output_cmd.stdout)
        return output_cmd_json
    
    return output_cmd.stdout


# 3. Google Lighthouse : https://www.npmjs.com/package/lighthouse
# Implementation: https://medium.com/@olimpiuseulean/use-python-to-automate-google-lighthouse-reports-and-keep-a-historical-record-of-these-65f378325d64
async def google_lighthouse(html_path):
    local_html = os.path.abspath(html_path)
    local_html_dir = Path(local_html).parent
    local_html_name = Path(local_html).name

    # Important lighthouse can't acccess local files, thus webserver
    server_process = await asyncio.create_subprocess_exec(
        "python",
        "-m",
        "http.server",
        "8000",
        "--bind",
        "127.0.0.1",
        cwd=str(local_html_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    await asyncio.sleep(1)

    localhost_url = f"http://127.0.0.1:8000/{local_html_name}"

    lighthouse_command = ["lighthouse", localhost_url, "--output=json", "--chrome-flags=--headless", "--quiet", "--output-path=stdout", "--only-categories=accessibility"]
    output_cmd = subprocess.run(lighthouse_command, capture_output=True, text=True)

    # kill server  
    server_process.terminate()

    if output_cmd.stderr:
        print(output_cmd.stderr)
        return
    
    # TODO: Further anlysis of output: .categories.accessibility.score, ...
    output_cmd_json = json.loads(output_cmd.stdout)

    # Important fields
    important_output = output_cmd_json["audits"]

    lighthouse_report = open(f"{DIR_PATH}/lighthouse_report.json", "w")
    json.dump(important_output, lighthouse_report)
    return important_output


async def getAccessibilityIssues(html_path):
    axe_core_results = await axe_core(html_path)
    pa11y_results = await pa11y(html_path)
    lighthouse_results = await google_lighthouse(html_path)

    return axe_core_results, pa11y_results, lighthouse_results




# Tests
asyncio.run(getAccessibilityIssues(f"{OUTPUT_DATA_PATH}/1.html"))
