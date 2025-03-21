import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Utils.utils as utils
import Benchmarks.Implementation.treeBleu as treeBleu
import Benchmarks.Implementation.textSimilarity as textSimilarity

class StructuralBenchmarks:
    def __init__(self):
        obj_structuralBenchmark = {}


    
    '''
        Text-Similarity:
        Is based on the SequenceMatcher from the difflib library    
    '''
    def textSimilarity(self, code1_path, code2_path):
        score = textSimilarity.text_similarity_score(code1_path, code2_path)
        self.obj_structuralBenchmark["textSimilarity"] = score
    

    '''
        Treebleu:
        Treebleu was presented in the following paper: https://arxiv.org/pdf/2404.06369
        It compares the amount of common 1-height subtrees in input and output code
    '''
    def treebleu(self, code1, code2):
        score = treeBleu.treeBleu_score(code1, code2)
        self.obj_structuralBenchmark["treebleu"] = score
    