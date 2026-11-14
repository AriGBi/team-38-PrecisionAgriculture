import re
import nltk
import cleanco
from toolz import pipe
from functools import lru_cache


nltk.download('punkt')
nltk.download('omw-1.4')
nltk.download('stopwords')
# Hardcoded rules for dealing with punctuation marks and other custom symbols
punctuation_replacement_rules = {
# old patterns: replacement pattern
    "[\u2022,\u2023,\u25E6,\u2043,\u2219]": ",",  # Convert bullet points to commas
r"[-/\\]": " ",  # Convert colon, hyphens and forward and backward slashes to spaces
r"[^a-zA-Z0-9,.; #(++)]": "",  # Preserve spaces, commas, full stops, semicollons for discerning noun chunks
#r"[\(\)]": ""
}
# Patterns for cleaning punctuation, for clean_punctuation()
compiled_punct_patterns = [re.compile(p) for p in punctuation_replacement_rules.keys()]
punct_replacement = list(punctuation_replacement_rules.values())
# Pattern for fixing a missing space between enumerations, for split_sentences()
compiled_missing_space_pattern = re.compile("([a-z])([A-Z])([a-z])")
compiled_nonalphabet_nonnumeric_pattern = re.compile(r"([^a-zA-Z0-9 #(++)+:])")
compiled_padded_punctuation_pattern = re.compile(r"( )([^a-zA-Z0-9 #(++)+]:)")
remove_symbols = re.compile(r"(?:\(|\))")


@lru_cache()
@staticmethod
def WordNetLemmatizer():
    nltk.download("wordnet")
    return nltk.WordNetLemmatizer()

@lru_cache()
@staticmethod
def get_stopwords():
    """Returns the set of English stopwords from nltk"""
    nltk.download("stopwords")
    from nltk.corpus import stopwords

    return list(set(stopwords.words("english"))) + ["also"]

def lemmatise(term):
    """Apply the NLTK WN Lemmatizer to the term"""
    lem = WordNetLemmatizer()
    return lem.lemmatize(term)

def clean_punctuation(text):
    """Replaces punctuation according to the predefined patterns"""
    for j, pattern in enumerate(compiled_punct_patterns):
        text = pattern.sub(punct_replacement[j], text)
    return text

def remove_punctuation(text):
    """Remove punctuation marks and replace with spaces (to facilitate lemmatisation)"""
    text = compiled_nonalphabet_nonnumeric_pattern.sub(r" ", text)
    text = remove_symbols.sub(r" ", text)
    return text

def pad_punctuation(text):
    """Pad punctuation marks with spaces (to facilitate lemmatisation)"""
    text = compiled_nonalphabet_nonnumeric_pattern.sub(r" \1 ", text)
    return text

def unpad_punctuation(text):

        text = compiled_padded_punctuation_pattern.sub(r"\2", text)
        return text

def detect_sentences(text):
    """
    Splits a word written in camel-case into separate sentences.
    """
    text = compiled_missing_space_pattern.sub(r"\1. \2\3", text)
    return text

def lowercase(text):
    """Converts all text to lowercase"""
    return text.lower()

def lemmatize_paragraph(text):
    """Lemmatizes each word in a paragraph."""
    text = " ".join([lemmatise(token) for token in text.split(" ")])
    return text

def join_num_text(text):
    """Joins numbers with adjacent text."""
    words = text.split()
    if len(words) > 1 and words[0].isnumeric():
        element = words[0] + words[1]
        words = [element] + words[2:]
    return " ".join(words)

def remove_numbers(text):
    """Remove all numbers from the text"""
    text = " ".join([c for c in text.split() if not c.isdigit()])
    return text


def clean_up(text):
    """Removes extra spaces between words"""
    self = " ".join([c for c in text.split() if len(c)>=2]).strip()
    return text

def remove_cleanco(text):
    """Remove cleanco processing from the text"""
    return cleanco.basename(text)
    
def _clean_text(text, keep_punct=False):
    if keep_punct is False:
        return pipe(
        text,
        detect_sentences,
        lowercase,
        remove_cleanco,
        remove_punctuation,
        join_num_text
        )
    elif keep_punct is True:
        return pipe(
        text,
        detect_sentences,
        lowercase,
        clean_punctuation,
        pad_punctuation,
        lemmatize_paragraph,
        unpad_punctuation,
        clean_up,
        )