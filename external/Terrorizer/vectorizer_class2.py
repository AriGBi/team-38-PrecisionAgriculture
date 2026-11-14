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

class NameVectorizer:
    def __init__(self):
        self.model = SentenceTransformer("Vsevolod/company-names-similarity-sentence-transformer")
        nltk.download('punkt')
        nltk.download('omw-1.4')
        nltk.download('stopwords')
        # Hardcoded rules for dealing with punctuation marks and other custom symbols
        self.punctuation_replacement_rules = {
    # old patterns: replacement pattern
         "[\u2022,\u2023,\u25E6,\u2043,\u2219]": ",",  # Convert bullet points to commas
        r"[-/\\]": " ",  # Convert colon, hyphens and forward and backward slashes to spaces
        r"[^a-zA-Z0-9,.; #(++)]": "",  # Preserve spaces, commas, full stops, semicollons for discerning noun chunks
       #r"[\(\)]": ""
}

        # Patterns for cleaning punctuation, for clean_punctuation()
        self.compiled_punct_patterns = [re.compile(p) for p in self.punctuation_replacement_rules.keys()]
        self.punct_replacement = list(self.punctuation_replacement_rules.values())
# Pattern for fixing a missing space between enumerations, for split_sentences()
        self.compiled_missing_space_pattern = re.compile("([a-z])([A-Z])([a-z])")

        self.compiled_nonalphabet_nonnumeric_pattern = re.compile(r"([^a-zA-Z0-9 #(++)+:])")
        self.compiled_padded_punctuation_pattern = re.compile(r"( )([^a-zA-Z0-9 #(++)+]:)")
        self.remove_symbols = re.compile(r"(?:\(|\))")


    def clean_punctuation(self, text):
        """Replaces punctuation according to the predefined patterns"""
        for j, pattern in enumerate(self.compiled_punct_patterns):
            text = pattern.sub(self.punct_replacement[j], text)
        return text

    def remove_punctuation(self, text):
        """Remove punctuation marks and replace with spaces (to facilitate lemmatisation)"""
        text = self.compiled_nonalphabet_nonnumeric_pattern.sub(r" ", text)
        text = self.remove_symbols.sub(r" ", text)
        return text

    def pad_punctuation(tself, text):
        """Pad punctuation marks with spaces (to facilitate lemmatisation)"""
        text = self.compiled_nonalphabet_nonnumeric_pattern.sub(r" \1 ", text)
        return text

    # Other methods would follow the same structure...
    def unpad_punctuation(self, text):

         text = self.compiled_padded_punctuation_pattern.sub(r"\2", text)
         return text

    def detect_sentences(self, text):
        """
        Splits a word written in camel-case into separate sentences.
        """
        text = self.compiled_missing_space_pattern.sub(r"\1. \2\3", text)
        return text

    def lowercase(self, text):
        """Converts all text to lowercase"""
        return text.lower()

    def lemmatize_paragraph(self, text):
        """Lemmatizes each word in a paragraph."""
        text = " ".join([lemmatise(token) for token in text.split(" ")])
        return text

    def join_num_text(self, text):
        """Joins numbers with adjacent text."""
        words = text.split()
        if len(words) > 1 and words[0].isnumeric():
            element = words[0] + words[1]
            words = [element] + words[2:]
        return " ".join(words)

        def remove_stopwords(self, text):

        # Code to remove stopwords from self
           stopwords = get_stopwords()

           stoplist = list(get_stop_words('en'))         #About 900 stopwords
           nltk_words_en = list(stopwords.words('english'))
           nltk_words_de = list(stopwords.words('german'))
           nltk_words_sp = list(stopwords.words('spanish'))
           nltk_words_fr = list(stopwords.words('french'))
           stoplist.extend(nltk_words_sp)
           stoplist.extend(nltk_words_de)
           stoplist.extend(nltk_words_sp)
           stoplist.extend(nltk_words_fr)
           text = " ".join(filter(lambda token: token not in stoplist, text.split(" ")))
    
           return text
  


    def remove_numbers(self, text):
        """Remove all numbers from the text"""
        text = " ".join([c for c in text.split() if not c.isdigit()])
        return text


    def clean_up(self,text):
        """Removes extra spaces between words"""
        self = " ".join([c for c in text.split() if len(c)>=2]).strip()
        return text

    def remove_cleanco(self,text):
        """Remove cleanco processing from the text"""
        return cleanco.basename(text)
        
    
    def _clean_text(self, text, keep_punct=False):
        if keep_punct is False:
            return pipe(
            text,
            self.detect_sentences,
            # remove_stopwords,
            self.lowercase,
            self.remove_cleanco,
            self.remove_punctuation,
            self.join_num_text
            # remove_stopwords,
            # remove_numbers,
            # lemmatize_paragraph,
            # clean_up,
            )
        elif keep_punct is True:
            return pipe(
            text,
            self.detect_sentences,
            self.lowercase,
            self.clean_punctuation,
            self.pad_punctuation,
            self.lemmatize_paragraph,
            # remove_stopwords,
            self.unpad_punctuation,
            self.clean_up,
            )
 
    
    
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
         
         for index, item in enumerate(l):
             name = self._clean_text(item)
             if name:
                 words = name.split()
             else:
                 name=item

             if not words:
                 vectors = np.zeros(384)
             else:
                 vectors = np.mean([self.model.encode(w, show_progress_bar=False) * weights.get(w, 1e-4) for w in words], axis=0)

             


         return vectors

    


