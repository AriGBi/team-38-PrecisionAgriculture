from sklearn.metrics import precision_recall_fscore_support
import optuna, joblib
import uuid, glob
import pickle, os, ast
import pandas as pd
import numpy as np
import networkx as nx
from atpbar import atpbar
from mantichora import mantichora
from sentence_transformers import util
from pandarallel import pandarallel
import numpy as np
from .bridges import bridgeness_centrality
from polyfuzz import PolyFuzz
from polyfuzz.models import TFIDF
from itertools import chain
from tqdm.notebook import tqdm

def tokenize(name):
      return set(name.split())


class KnowledgeAugmentation:
    def __init__(self, data, knowledge_base='./knowledge_base_duckduck24v2.csv', column_name="name", threshold=0.8):
        self.data = data
        self.knowledge_base = pd.read_csv(knowledge_base)
        self.threshold = threshold
        self.column_name = column_name

    def token_in_common(self):
        self.data[self.column_name] = self.data[self.column_name].str.strip().str.upper()
        self.knowledge_base['original_name'] = self.knowledge_base['original_name'].str.strip().str.upper()
        l1 = list(set(self.data[self.column_name].tolist()))
        l2 = list(set(self.knowledge_base['original_name'].tolist()))
        name_matches = {name1: [] for name1 in l1}
        
        tokens_l1 = {name: tokenize(name) for name in l1}
        tokens_l2 = {name: tokenize(name) for name in l2}
        for name1, tokens1 in tokens_l1.items():
            len_tokens1 = len(tokens1)  
            if len_tokens1:  
                for name2, tokens2 in tokens_l2.items():
                    lun = len(tokens1.intersection(tokens2))
                    if lun >= 1:  
                        name_matches[name1].append(name2)
        return name_matches  
     
    def check_missing(self, mx):
        self.data[self.column_name] = self.data[self.column_name].str.strip().str.upper()
        mx['name'] = mx[self.column_name].str.strip().str.upper()
        merged_df = pd.merge(self.data, mx, on=self.column_name, how='outer')
        return merged_df
   
    def process_knowledge_retrieval(self, custom_threshold=None):
        with tqdm(total=1, desc="Processing Knowledge Retrieval") as pbar:  
            result_match = self.knowledge_matches(custom_threshold=custom_threshold)
            merged_df = self.check_missing(result_match)
        return merged_df

    def knowledge_matches(self, custom_threshold=None):
        threshold = custom_threshold if custom_threshold is not None else self.threshold
        my_dict = self.token_in_common()
        
        model = TFIDF()
        polyfuzz_model = PolyFuzz(model)
        
        from_list = self.data[self.column_name].dropna().astype(str).tolist()
        to_list = self.knowledge_base["original_name"].dropna().astype(str).tolist()
        
        polyfuzz_model.match(from_list, to_list)
        matches = polyfuzz_model.get_matches()
        matches = matches.loc[matches['Similarity'] >= threshold]
        matches['To'] = matches['To'].str.strip().str.upper()
        mx = pd.merge(matches, self.knowledge_base, how='left', left_on=['To'], right_on=['original_name'])
        mx = mx[['From', 'original_name', 'did_u_mean', 'url', 'Domain', 'text_normalized']]
        mx = mx.rename(columns={'From': self.column_name, 'original_name': 'knowledge_base_name'})
        
        return mx






