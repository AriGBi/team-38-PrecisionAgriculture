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
        pass

    def clean_text(self, text):
        text = text.lower()
        text = text.replace(',', ' ')
        text = re.sub(r"\(.*\)", " ", text)
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return basename(text)
    def clean_from_company(self, data, column=None):
        if isinstance(data, str):
             return self.clean_text(data)
        elif isinstance(data, list):
             return [self.clean_text(item) for item in data]
        elif isinstance(data, pd.DataFrame) and column:
             new_column = column + "_cleaned"
             data[new_column] = data[column].astype(str).apply(self.clean_text)
             return data
        else:
            raise TypeError("Input must be a string, list, or DataFrame with a specified column.")
    
  

    def preprocess(self, data, default_column='original_name'):
         if isinstance(data, str):
             data = pd.DataFrame({default_column: [data]})

    # Handle list input
         elif isinstance(data, list):
             data = pd.DataFrame({default_column: data})

   
    # Apply the cleaning function
         data['name_normalized'] = data[default_column].apply(self.clean_text)

         return data

