import os
import json
import matplotlib.pyplot as plt

'''
    Analysis of .json files which contain the accessibility issues of html files
'''

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_JSON_DIR = os.path.join(CURR_DIR, '..', 'Input', 'json', 'manual')


def json_analyzer(path):
    # dictionary which contains all accessibility issues & amounts across all files
    issues_dict = {}

    for file in os.listdir(path):
        with open(os.path.join(INPUT_JSON_DIR, file)) as f:
            # print(file)
            data = json.load(f)
            curr_dict = rank_issues(data)

            for key, values in curr_dict.items():
                
                # if key[1] == "https://dequeuniversity.com/rules/axe/4.10/meta-viewport":
                #     print("stop")

                temp = issues_dict.get(key)
                if(temp == None):
                    issues_dict[key] = values
                else:
                    assert values['impact'] == temp['impact']

                    old_amount = temp['amount']
                    issues_dict.pop(key)
                    issues_dict[key] = {
                        "impact": temp['impact'],
                        "amount": old_amount + values['amount']
                    }
    
    create_rankings(issues_dict)

    print("stop")
                


def rank_issues(data):
    curr_dict = {}
    for issue in data:
        wcag_id = issue.get('wcag_id')
        url = issue.get('url')
        impact = issue.get('impact')
        amount = issue.get('amount')

        curr_dict[(wcag_id, url)] = {
            "impact": impact,
            "amount": amount
        }

    return curr_dict


def create_rankings(issues_dict):
    # sort issues_dict by amount
    sorted_issues = sorted(issues_dict.items(), key=lambda x: x[1]['amount'], reverse=True)

    for i in range(len(sorted_issues)):
        key, values = sorted_issues[i]
        print(f"{i+1}. {key[0]} - {key[1]} - {values['impact']} - {values['amount']}")





json_analyzer(INPUT_JSON_DIR)