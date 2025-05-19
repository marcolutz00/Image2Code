from bs4 import BeautifulSoup
# Info BS4: https://www.twilio.com/de-de/blog/web-scraping-und-parsen-von-html-python-mit-beautiful-soup , https://www.crummy.com/software/BeautifulSoup/bs4/doc/


def rec_get_tree_height1(bs4_obj, storage_subtrees):
    '''
        Recursive function to seee the 1-height subtrees of the html tree
    '''
    unnecessary_elements = ["meta", "script", "style", "link"]

    elements = bs4_obj.find_all(recursive=False)

    # only names of html elements
    names = []
    for element in elements:
        if element.name not in unnecessary_elements:
            names.append(element.name)

    if names:
        subtree_height1 = f"{bs4_obj.name} -> {', '.join(names)}"
        storage_subtrees.add(subtree_height1)
        # print(subtree_height1)
    
    for element in elements:
        if element.name not in unnecessary_elements:
            rec_get_tree_height1(element, storage_subtrees)



def treeBleu_score(html1_path, html2_path):
    '''
        Treebleu-Score according to paper: https://arxiv.org/pdf/2404.06369
    '''

    # Read HTML files
    with open(html1_path, "r", encoding="utf-8") as f:
        html1 = f.read()
    with open(html2_path, "r", encoding="utf-8") as f:
        html2 = f.read()

    bs4_obj1 = BeautifulSoup(html1, 'html.parser')
    bs4_obj2 = BeautifulSoup(html2, 'html.parser')

    # Storage for found 1-height subtrees -> important set, to use .intersection()
    storage_subtrees1 = set()
    storage_subtrees2 = set()
    
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
