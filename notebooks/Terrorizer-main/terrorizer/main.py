import pandas as pd
from polyfuzz import PolyFuzz
from polyfuzz.models import TFIDF
from itertools import chain
from tqdm.notebook import tqdm
import re
import numpy as np
from cleanco import basename
from .text_utils import _clean_text
from .knowledge_augementation_class import KnowledgeAugmentation
from .preprocessing_class_terrorizer import NamesPreprocessing  
from .vectorizer_class2 import NameVectorizer
from .process_network_terrorizer import terrorizer_matching_stage
from .process_network_terrorizer import process_network
from .process_network_terrorizer import CommunityNaming
from tqdm.notebook import tqdm



class Terrorizer:
    def __init__(self, data, knowledge_base_path='./knowledge_base_duckduck24v2.csv', column_name="name", threshold=0.8):
        self.data=data
        self.knowledge_base_path = knowledge_base_path
        self.column_name = column_name
        self.threshold = threshold
        self.preprocessed_data = None
        self.augmented_data = None
        self.vectors = None
        self.matching_results = None
        self.network_results = None
        self.community_names = None

    def execute(self):
        
        # Step 1: Names Preprocessing
        total_steps = 3  # Total number of steps in the execute method
        progress_bar = tqdm(total=total_steps, desc='Overall Progress')
    
    # Step 1: Names Preprocessing
        progress_bar.set_description("Step 1: Names Preprocessing")

        names_preprocessor = NamesPreprocessing()
        self.preprocessed_data = names_preprocessor.preprocess(self.data, default_column=self.column_name)
        progress_bar.update(1)
        # Step 2: Knowledge Augmentation
        progress_bar.set_description("Step 2: Knowledge Augmentation")
        knowledge_augmenter = KnowledgeAugmentation(self.preprocessed_data, knowledge_base=self.knowledge_base_path, column_name=self.column_name, threshold=self.threshold)
        self.augmented_data = knowledge_augmenter.process_knowledge_retrieval()
        progress_bar.update(1)

        # Step 3: Name Vectorization
        name_vectorizer = NameVectorizer()
        names_to_vectorize = self.augmented_data['name_normalized'].tolist()
        weights = name_vectorizer.total_score(names_to_vectorize)
        self.vectors = [name_vectorizer.get_vector([name], weights) for name in names_to_vectorize]

        # Step 4: Matching Stage
        progress_bar.set_description("Step 3: Disambiguation")
        matching_stage = terrorizer_matching_stage(self.augmented_data, self.vectors, weight_same_t=1, weight_first_token=1, weight_similarity=1)
        self.matching_results = matching_stage.main()

        # Step 5: Process Network
        network_processor = process_network(self.matching_results, resolution=1.0, match_threshold=0.5, bridgeness_threshold=0.5)
        self.network_results = network_processor.main()
        progress_bar.update(1)

        # Step 6: Community Naming
        community_namer = CommunityNaming(results=self.network_results)
        self.community_names = community_namer.main()
        progress_bar.set_description("Disambiguation completed")
        progress_bar.close()
        return self.community_names

        ###Cose da fare:
        #1- Far ritornare invece che quella roba, quella cosa che avevo previsto io in naming, ossia un dataframe con i nomi vecchi e per ogni nome vecchio il nome pulito
        #2- magari la threshold di knowledge base chiamarla threshold_knowledge
        #3- mettere un tqdm fatto meglio su tutto il processo se possibile
        #4- creare un po' di error handling generico
        #5- mettere la possibilità di NON usare la knowledge base quindi di fare process senza le extra features