from playwright.async_api import async_playwright
import os
import asyncio
import subprocess
import json
from pathlib import Path
import sys
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Accessibility import accessibilityMapping



DIR_PATH = os.path.dirname(os.path.realpath(__file__))

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data')
INPUT_DATA_PATH = os.path.join(DATA_PATH, 'Input', 'html')
OUTPUT_DATA_PATH = os.path.join(DATA_PATH, 'Output', 'openai', 'html')
UTILS_PATH = os.path.join(os.path.dirname(__file__), '..', 'Utils')

AXE_CORE_PATH = os.path.join(UTILS_PATH, "axe-core/axe.min.js")

'''
    In the following, we are going to use different automatic accessibility tools
'''

async def _axe_core(html_path):
    """
    1. axe-core (npm) infos here: https://hackmd.io/@gabalafou/ByvwfEC0j
    """
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

        # axe_violations = axe_results["violations"]

    # return axe_violations
    return axe_results


async def _pa11y(html_path):
    """
    2. Pa11y (npm) infos here: https://www.npmjs.com/package/pa11y
    Engine: HTML Code Sniffer
    """
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



async def _google_lighthouse(html_path):
    """
    3. Google Lighthouse : https://www.npmjs.com/package/lighthouse
    Implementation: https://medium.com/@olimpiuseulean/use-python-to-automate-google-lighthouse-reports-and-keep-a-historical-record-of-these-65f378325d64
    """
    local_html = os.path.abspath(html_path)
    local_html_dir = Path(local_html).parent
    local_html_name = Path(local_html).name

    # Important lighthouse can't acccess local files, thus webserver
    server_process = await asyncio.create_subprocess_exec(
        "python3",
        "-m",
        "http.server",
        "8001",
        "--bind",
        "127.0.0.1",
        cwd=str(local_html_dir), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        await asyncio.sleep(1)

        url = f"http://127.0.0.1:8001/{local_html_name}"

        # find lighthouse locally
        lighthouse_binary = shutil.which("lighthouse") or "/opt/homebrew/bin/lighthouse"

        cmd = [
            lighthouse_binary, url,
            "--output=json", "--output-path=stdout", "--chrome-flags=--headless","--quiet", "--only-categories=accessibility",
        ]

        process_lighthouse = await asyncio.create_subprocess_exec(
            *cmd, stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await process_lighthouse.communicate()

        if process_lighthouse.returncode != 0:
            raise RuntimeError(stderr_bytes.decode() or "lighthouse failed")

        data = json.loads(stdout_bytes.decode())
        return {
            "audits": data["audits"],
            "categories": data["categories"],
        }

    finally:
        if server_process.returncode is None:
            server_process.terminate()
            try:
                await server_process.wait()
            except ProcessLookupError:
                pass



async def _get_accessibility_issues(html_path):
    """
    collect accessibility violations from various tools
    """
    axe_core_results = await _axe_core(html_path)
    pa11y_results = await _pa11y(html_path)

    try:
        lighthouse_results = await _google_lighthouse(html_path)
    except Exception as e:
        print(f"Error with Lighthouse: {e}")
        lighthouse_results = None

    issues_automatic_json, issues_overview_json = accessibilityMapping.integrate_accessibility_tools_results(pa11y_results, axe_core_results, lighthouse_results)

    return issues_automatic_json, issues_overview_json


async def enrich_with_accessibility_issues(file, html_path, accessibility_path, insights_path):
    '''
        Enrich the dataset with accessibility issues from:
        1. axe-core
        2. pa11y
        3. google lighthouse

        At the end, the information is stores
    '''
    base_name = file.split(".")[0]

    print(f"Checking accessibility issues for {base_name} ...")

    # Accessibility Issues analyze
    issues_automatic_json, issues_overview_json = await _get_accessibility_issues(html_path)
    
    with open(accessibility_path, "w") as f:
        json.dump(issues_automatic_json, f, ensure_ascii=False, indent=2)

    with open(insights_path, "w") as f:
        json.dump(issues_overview_json, f, ensure_ascii=False, indent=2)

    print(f"Accessibility issues for {base_name} stored in {accessibility_path} and {insights_path}")

    return issues_automatic_json, issues_overview_json
    
    



# Tests
# asyncio.run(get_accessibility_issues(f"{OUTPUT_DATA_PATH}/1.html"))
