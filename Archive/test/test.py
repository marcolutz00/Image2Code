#!/usr/bin/env python3
import os
import sys
from playwright.async_api import async_playwright
import json 

UTILS_PATH = os.path.join(os.path.dirname(__file__), '..', 'Utils')
AXE_CORE_PATH = os.path.join(UTILS_PATH, "axe-core/axe.min.js")
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data')





def main():
    total_sum_checked = 0
    total_array_failed = []


    list_to_check = [
        # os.path.join(DATA_PATH, 'Output', 'gemini', 'insights', "naive", "2025-06-18-10-18"),
        # os.path.join(DATA_PATH, 'Output', 'gemini', 'insights', "naive", "2025-06-18-11-24"),
        # os.path.join(DATA_PATH, 'Output', 'gemini', 'insights', "naive", "2025-06-18-11-53"),
        os.path.join(DATA_PATH, 'Output', 'openai', 'insights', "naive", "2025-06-19-15-41"),
        os.path.join(DATA_PATH, 'Output', 'openai', 'insights', "naive", "2025-06-19-16-53"),
        os.path.join(DATA_PATH, 'Output', 'openai', 'insights', "naive", "2025-06-19-19-05"),
    ]

    for list in list_to_check:
        for file in os.listdir(list):
            if file.endswith('.json') and file.startswith('overview_'):
                # read json file
                with open(os.path.join(list, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    automatic_checks = data.get('automatic_checks', {})
                    count_failed = automatic_checks.get('total_nodes_failed', 0)
                    count_checked = automatic_checks.get('total_nodes_checked', 0)

                    total_sum_checked += count_checked
                    total_array_failed.append(count_failed)

                    # print(f"File: {file}, AXE Nodes Count: {count}")

                # print(f"File: {file}, AXE Nodes Count: {count}")
        print(f"Total AXE Nodes Count: {total_sum_checked}")
        print(f"Average AXE Nodes Count: {total_sum_checked / 53}")
        total_sum_checked = 0

    print(total_array_failed)
    print(len(total_array_failed))
    pass



if __name__ == "__main__":
    main()
