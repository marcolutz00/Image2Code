import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Utils.utils as utils
import Benchmarks.Implementation.treeBleu as treeBleu

class StructuralBenchmarks:
    def domSimilarity(self, code1, code2):
        print("test")
    

    '''
        tbd
        Code-Quality:
        Is the created HTML/CSS of good quality and without errors?
    '''
    def codeQuality(self, code1, code2):
        print("test")

    '''
        Treebleu:
        Treebleu was presented in the following paper: https://arxiv.org/pdf/2404.06369
        It compares the amount of common 1-height subtrees in input and output code
    '''
    def treebleu(self, code1, code2):
        print("test")
    