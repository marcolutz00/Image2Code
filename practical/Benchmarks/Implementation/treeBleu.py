from bs4 import BeautifulSoup
import os

DIR_PATH = os.path.join(os.path.dirname(__file__))

# Info BS4: https://www.twilio.com/de-de/blog/web-scraping-und-parsen-von-html-python-mit-beautiful-soup , https://www.crummy.com/software/BeautifulSoup/bs4/doc/


def rec_get_tree_height1(bs4_obj, storage_subtrees):
    unnecessary_elements = ["meta", "script", "style", "link"]

    elements = bs4_obj.find_all(recursive=False)
    # only names of html elements
    names = []
    for element in elements:
        if element.name not in unnecessary_elements:
            names.append(element.name)

    if names:
        subtree_height1 = f"{bs4_obj.name} -> {', '.join(names)}"
        storage_subtrees.append(subtree_height1)
        # print(subtree_height1)
    
    for element in elements:
        if element.name not in unnecessary_elements:
            rec_get_tree_height1(element, storage_subtrees)


'''
    Treebleu-Score according to paper: https://arxiv.org/pdf/2404.06369
'''

# Important Code1 is Input (Reference) and Code2 is Output (Generated)
def treeBleu_score(code1, code2):
    bs4_obj1 = BeautifulSoup(code1, 'html.parser')
    bs4_obj2 = BeautifulSoup(code2, 'html.parser')

    # Storage for found 1-height subtrees
    storage_subtrees1 = []
    storage_subtrees2 = []
    
    # Get 1-height subtrees
    rec_get_tree_height1(bs4_obj1, storage_subtrees1)
    rec_get_tree_height1(bs4_obj2, storage_subtrees2)

    # Avoid division by zero
    if len(storage_subtrees1) == 0:
        return 0

    # Compare
    amount_intersection = len(storage_subtrees1.intersection(storage_subtrees2))
    treebleu_score = amount_intersection / len(storage_subtrees1)

    return treebleu_score



# Tests 
with open (f"{DIR_PATH}/1.html", "r", encoding="utf-8") as f:
    example_html = f.read()

treeBleu_score(example_html, "g")