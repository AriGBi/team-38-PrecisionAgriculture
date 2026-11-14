import pandas as pd
import numpy as np
import re
import nltk
import gensim
from toolz import pipe
from functools import lru_cache
from collections import Counter
import cleanco
import pickle
from sentence_transformers import SentenceTransformer, util
from .text_utils import _clean_text

class NameVectorizer:
    def __init__(self):
        self.model = SentenceTransformer("Vsevolod/company-names-similarity-sentence-transformer")
    
    def get_idf(self, docs):
        idf= {}
        for doc in docs:
            if doc is np.nan: continue
            words=list(set([c.lower() for c in doc.split()]))
            for w in words:
                if w not in idf.keys():
                    idf.update({w:0}) #update del dizionario
                    idf[w]= idf[w] + 1
            for k, v in idf.items():
                idf[k]= np.log(len(docs)/v)
        return idf
    
    def scale(val, src, dst):
        return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]

    def total_score(self, docs):
        idf_dict= self.get_idf(docs)
        elements = [a for c in docs if c is not np.nan for a in c.split() ]
        total_len = len(set(elements))
        count = Counter(elements)
    #la frequenza totale la uso come counter (il k quindi)
        terms= sorted([(k, np.log(v)*(idf_dict.get(k.lower()))) for k, v in count.items()], key=lambda x:x[1], reverse=True)
        values = [c for _, c in terms]
        _min, _max = min(values), max(values)-1e-4
        term={k: abs(1-(v-_min)/(_max-_min)) for k,v in terms}
        return term
    
    def get_vector(self, l, weights):
         words = None
         for item in l:
             name = _clean_text(item)
             if name:
                 words = name.split()
             else:
                 name = item
             if not words:
                 vectors = np.zeros(384)
             else:
                 vectors = np.mean([self.model.encode(w, show_progress_bar=False) * weights.get(w, 1e-4) for w in words], axis=0)

             


         return vectors

    


