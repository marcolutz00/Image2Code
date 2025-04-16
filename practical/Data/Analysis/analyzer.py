import os
import json
import matplotlib.pyplot as plt

'''
    Analysis of .json files which contain the accessibility issues of html files
'''

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_JSON_DIR = os.path.join(CURR_DIR, '..', 'Input', 'json', 'manual')

ISSUES_DICT = {}

'''
    This function returns a map describing which accessibility issue has been found by which source.

    Therefore, we are looking into the details of each accessibility issue reported. The source (axe-core, lighthouse, pa11y)
    which has reported the most amount of details will get the amount.
    Only exception: If there is an entry with Manual-Inspection, then Manual-Inspection will get the amount.
'''
def find_source(issue_data):
    axe_core = 0
    pa11y = 0
    lighthouse = 0

    for issue in issue_data:
        source = issue.get("source")

        match source:
            case "Manual-Inspection":
                return "Manual-Inspection"
            case "axe-core":
                axe_core += 1
            case "pa11y":
                pa11y += 1
            case "lighthouse":
                lighthouse += 1
    
    # return String of highest value
    return "unknown" if max(axe_core, pa11y, lighthouse) == 0 else ["axe-core", "pa11y", "lighthouse"][[axe_core, pa11y, lighthouse].index(max(axe_core, pa11y, lighthouse))]

# Issues are going to be listed
def list_and_add_issues(data, sources):
    global ISSUES_DICT

    curr_dict = {}
    amount_total = 0

    for accessibility_issue in data:
        wcag_id = accessibility_issue.get('wcag_id')
        url = accessibility_issue.get('axe_url')
        impact = accessibility_issue.get('impact')
        amount = accessibility_issue.get('amount')
        name = accessibility_issue.get('name')
        issues = accessibility_issue.get('issues')


        source_of_issue = find_source(issues)

        assert source_of_issue != "unknown"

        old_amount = sources.get(source_of_issue)
        sources[source_of_issue] = old_amount + amount

        # if key[1] == "https://dequeuniversity.com/rules/axe/4.10/meta-viewport":
        #     print("stop")

        amount_total += amount
        temp = ISSUES_DICT.get(name)

        if(temp == None):
            ISSUES_DICT[name] = {
            "impact": impact,
            "amount": amount
        }
            
        else:
            assert impact == temp['impact']

            old_amount = temp['amount']
            ISSUES_DICT.pop(name)
            ISSUES_DICT[name] = {
                "impact": temp['impact'],
                "amount": old_amount + amount
            }

    return amount_total


# Ranking based on amount sorting
def create_rankings():
    global ISSUES_DICT
    # sort issues_dict by amount
    sorted_issues = sorted(ISSUES_DICT.items(), key=lambda x: x[1]['amount'], reverse=True)
    
    return sorted_issues




def json_analyzer(path):
    global ISSUES_DICT

    amount_total = 0
    sources = {
        "Manual-Inspection": 0,
        "pa11y": 0,
        "axe-core": 0,
        "lighthouse": 0
    }

    for file in os.listdir(path):
        with open(os.path.join(INPUT_JSON_DIR, file)) as f:
            # print("Analyzed: ", file)
            data = json.load(f)
        
        amount = list_and_add_issues(data, sources)
        amount_total += amount

    
    sorted_issues = create_rankings()

    for i in range(len(sorted_issues)):
        key, values = sorted_issues[i]
        print(f"{i+1}. {key} - {values['impact']} - {values['amount']}")
    
    print("Amount final: ", amount_total)
    print("Average per File: ", float(amount_total/53))

    print("stop")
                



json_analyzer(INPUT_JSON_DIR)