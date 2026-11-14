from cleanco import basename
from toolz import pipe
import pandas as pd
import numpy as np
import re
import nltk
import gensim
from functools import lru_cache
from collections import Counter
import pickle
import pandas as pd
import json
import numpy as np
from collections import Counter
import tldextract
import swifter



class NamesPreprocessing:
    def __init__(self):
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
        

    def clean_from_company(self, data, column=None):
        def clean_text(text):
            text = text.lower()
            text = text.replace(',', ' ')
            text = re.sub(r"\(.*\)", " ", text)
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)
            return basename(text)

        if isinstance(data, str):
             return clean_text(data)
        elif isinstance(data, list):
             return [clean_text(item) for item in data]
        elif isinstance(data, pd.DataFrame) and column:
             new_column = column + "_cleaned"
             data[new_column] = data[column].astype(str).apply(clean_text)
             return data
        else:
            raise TypeError("Input must be a string, list, or DataFrame with a specified column.")
    
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
 
    def preprocess(self, data, default_column='original_name'):
         def clean_text(text):
            text = text.lower()
            text = text.replace(',', ' ')
            text = re.sub(r"\(.*\)", " ", text)
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)
            return basename(text)

         if isinstance(data, str):
             data = pd.DataFrame({default_column: [data]})

    # Handle list input
         elif isinstance(data, list):
             data = pd.DataFrame({default_column: data})

   
    # Apply the cleaning function
         data['name_normalized'] = data[default_column].apply(clean_text)

         return data

