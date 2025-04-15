import os
import json
import matplotlib.pyplot as plt

'''
    Analysis of .json files which contain the accessibility issues of html files
'''

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_JSON_DIR = os.path.join(CURR_DIR, '..', 'Input', 'json', 'manual')

AMOUNT = 0
ISSUES_DICT = {}

# Issues are going to be listed
def list_and_add_issues(data):
    global AMOUNT
    global ISSUES_DICT

    curr_dict = {}
    for issue in data:
        wcag_id = issue.get('wcag_id')
        url = issue.get('axe_url')
        impact = issue.get('impact')
        amount = issue.get('amount')
        name = issue.get('name')

        curr_dict[name] = {
            "impact": impact,
            "amount": amount
        }

        # Add to global amount
        AMOUNT += amount

                
        # if key[1] == "https://dequeuniversity.com/rules/axe/4.10/meta-viewport":
        #     print("stop")

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

    return curr_dict


# Ranking based on amount sorting
def create_rankings():
    global ISSUES_DICT
    # sort issues_dict by amount
    sorted_issues = sorted(ISSUES_DICT.items(), key=lambda x: x[1]['amount'], reverse=True)
    
    return sorted_issues






def json_analyzer(path):
    global AMOUNT
    global ISSUES_DICT

    for file in os.listdir(path):
        with open(os.path.join(INPUT_JSON_DIR, file)) as f:
            # print("Analyzed: ", file)

            data = json.load(f)
            curr_dict = list_and_add_issues(data)

    
    sorted_issues = create_rankings()

    for i in range(len(sorted_issues)):
        key, values = sorted_issues[i]
        print(f"{i+1}. {key} - {values['impact']} - {values['amount']}")
    
    print("Amount final: ", AMOUNT)
    print("Average per File: ", float(AMOUNT/53))

    print("stop")
                



json_analyzer(INPUT_JSON_DIR)