import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import practical.Utils.utils_general as utils_general
import Benchmarks.Implementation.treeBleu as treeBleu
import Benchmarks.Implementation.textSimilarity as textSimilarity

class StructuralBenchmarks:
    def __init__(self):
        self.structural_benchmark = {}

    def text_similarity(self, html1_path, html2_path):
        '''
            Text-Similarity:
            Is based on the SequenceMatcher from the difflib library    
        '''
        score = textSimilarity.text_similarity_score(html1_path, html2_path)
        self.structural_benchmark["text_similarity"] = score


    def tree_bleu(self, html1_path, html2_path):
        '''
            Treebleu:
            Treebleu was presented in the following paper: https://arxiv.org/pdf/2404.06369
            It compares the amount of common 1-height subtrees in input and output html
        '''
        score = treeBleu.treeBleu_score(html1_path, html2_path)
        self.structural_benchmark["tree_bleu"] = score

    def calculate_and_get_structural_benchmarks(self, html1_path, html2_path):
        '''
            Calculate all structural benchmarks
        '''
        # Calculate the benchmarks
        self.text_similarity(html1_path, html2_path)
        self.tree_bleu(html1_path, html2_path)

        return self.structural_benchmark
    