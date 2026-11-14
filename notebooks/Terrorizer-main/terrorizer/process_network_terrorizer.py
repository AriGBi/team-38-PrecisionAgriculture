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
from sklearn.metrics import precision_recall_fscore_support

#from stop_words import get_stop_words
#from nltk.corpus import stopwords


pandarallel.initialize(nb_workers=2, progress_bar=False)



class terrorizer_matching_stage:
    def __init__(
        self,
        data,
        vectors,
        weight_same_t, 
        weight_first_token, 
        weight_similarity,
        weight_in_domain=0,
        weight_token_text=0
    ):
        self.weight_same_t = weight_same_t
        self.weight_first_token = weight_first_token
        self.weight_in_domain = weight_in_domain
        self.weight_token_text = weight_token_text
        self.weight_similarity = weight_similarity

        # bisogna creare una cartella results
        if not os.path.exists("./results"):
            os.mkdir("./results")  
            

        normal = data
        normal.fillna("", inplace=True)
        normal.sort_index(inplace=True)


        self.normal_vectors = vectors

        
        normal.reset_index(inplace=True, drop=True)

        normal.to_csv("normal.csv")
        self.normal = normal.copy()

    def get_token_text(self, pivot1, confronto1, pivot2, confronto2):

        token_text = 0
        matches_pivot1 = pivot1.strip().split()
        matches_pivot2 = pivot2.strip().split()
        matches_pivot=len(list(set(matches_pivot1)&set(matches_pivot2)))
        matches_confronto1 = confronto1.strip().split()
        matches_confronto2 = confronto2.strip().split()
        matches_confronto=len(list(set(matches_confronto1)&set(matches_confronto2)))
        if matches_pivot > 0  and matches_confronto >0:
            #x=pivot2.strip().split() 
            #y=confronto2.strip().split()
            token_text=len(list(set(matches_pivot2) & set(matches_confronto2)))
            if token_text>0:
                token_text=1
        return token_text


    
    def compare(self, pivot, confronto):
        in_domain = 0
        token_text = 0 
        name_pivotlist = pivot.get("name_normalized").strip().split()
        name_confrontolist = confronto.get("name_normalized").strip().split()
        same_t = int(bool(set(name_pivotlist) & set(name_confrontolist)))
        first_token = int(name_pivotlist[0] == name_confrontolist[0] if name_pivotlist and name_confrontolist else False)

        if "Domain" in pivot and "Domain" in confronto:
            domain_pivot = str(pivot["Domain"]).strip()
            domain_confronto = str(confronto["Domain"]).strip()
            in_domain = int(bool(domain_pivot and domain_confronto and domain_pivot == domain_confronto))
            if not domain_pivot or not domain_confronto:
                url_pivot = pivot.get("url", "").strip()
                url_confronto = confronto.get("url", "").strip()
                in_domain = int(bool(url_pivot and url_confronto and url_pivot == url_confronto))

            else:
                in_domain=0
        else:
            in_domain=0

    # Token text comparison, proceed if 'text_normalized' column exists
        if "text_normalized" in pivot and "text_normalized" in confronto:
            token_text =self.get_token_text(pivot["name_normalized"],
                        confronto["name_normalized"],
                        pivot["text_normalized"],
                        confronto["text_normalized"])
        else:
            token_text=0
    
    # Sum the boolean results since they are already 0 or 1
        return (confronto.get('name', ''), sum((
            self.weight_same_t * same_t,
            self.weight_first_token * first_token,
            self.weight_in_domain * in_domain,
            self.weight_token_text * token_text
         )))




    def process_compare(self, n_pivot, indexes_list):
        #print(f"Lauch subrocess for index: {n_pivot}")
        return  [self.compare(a, b) for a, b in zip([self.normal.loc[n_pivot]]*len(self.normal),
                                                [self.normal.loc[i] for i in indexes_list])]
        #return [compare(normal.loc[n_pivot], normal.loc[n]) for n in indexes_list]


    def get_row_scores(self, n_pivot, thres=0.):

        # print(f"process element: {n_pivot}")
        cos_dis = util.cos_sim(self.normal_vectors[n_pivot], self.normal_vectors)
        pivot = self.normal.loc[n_pivot]
        scores = [self.compare(pivot, x) for _, x in self.normal.iterrows()]
        #list(normal.parallel_apply(lambda x: compare(pivot, x), axis=1))
        scores = [c[1] for c in scores]
        sum_scores = np.sum(np.array([self.weight_similarity*cos_dis.numpy()[0], scores]), axis=0)
        final = np.where(sum_scores>=0)[0]

        return (n_pivot, final, sum_scores[final])

    def task(self, list_, name=None):

        for i in atpbar(list_, name=name):
            results = self.get_row_scores(i)
            with open(f"./results/{i}.pickle","wb") as f:
                pickle.dump(results, f)

    def main(self):
        idx = self.normal.index.to_list()
        results_normal=[]

        # if len(self.normal) > 1000:
        # # Use parallel processing for large datasets
        #     print("Running processing on data")
        #     ss = np.array_split(idx, 8)
        #     with mantichora(nworkers=8) as mcore:
        #          for i, s in enumerate(ss):
        #             mcore.run(self.task, ss[i], name=f"process {i}")
        #             results = mcore.returns()
        #             with open(f"./results/{i}.pickle", "wb") as f:
        #                  pickle.dump(result, f)

        # else:
        # Use normal processing for smaller datasets
        for i in idx:
            result = self.get_row_scores(i)
            results_normal.append(result)
        return results_normal
            


class process_network:
    
    def __init__(
            self,
            results_normal,
            resolution,
            match_threshold,
            bridgeness_threshold,
          #  location_weigth
            
    ):

        self.resolution = resolution
        self.match_threshold = match_threshold
        self.bridgeness_threshold = bridgeness_threshold
        #self.location_weigth = location_weigth
        self.results_normal=results_normal
        
        #MAIN_RES_DIR = "./results/"
        #results_normal = os.listdir(MAIN_RES_DIR)
        tab_normal = pd.read_csv("normal.csv")
        #tab_normal['location_id'] = tab_normal['location_id'].apply(ast.literal_eval)

        #result_normal={}
        #for c in results_normal:
          #  if not os.path.isdir(os.path.join(MAIN_RES_DIR, c)):
           #     with open(os.path.join(MAIN_RES_DIR, c), "rb") as f:
            #        data = pickle.load(f)
             #   pivot, list_res, list_score = data
                
              #  list_res, list_score = list(list_res), list(list_score)
                
               # result_normal.update({
                #    pivot: [(a, b) for a, b in zip(list_res, list_score)]
                #})
                
        #with open('result_normal_oct23.pickle', 'wb') as handle:
         #   pickle.dump(result_normal, handle, protocol=pickle.HIGHEST_PROTOCOL)

        #with open("result_normal_oct23.pickle", "rb") as f:
         #   self.result_normal = pickle.load(f)

        self.result_normal = {}
        for item in results_normal:
            index, indices, scores = item
            filtered_indices_scores = [(indices[i], scores[i]) for i in range(len(scores)) if scores[i] >= self.match_threshold]
            self.result_normal[index] = filtered_indices_scores

        self.normals = {a: b for a, b in zip(tab_normal.index, tab_normal.name_normalized)}

        self.g = nx.Graph() 
        for n in self.result_normal.keys():
            self.g.add_node(n, name=self.normals.get(n))
        for k, v in self.result_normal.items():
            #print([(k, el[0], el[1]) for el in v])
            self.g.add_weighted_edges_from([(k, el[0], el[1]) for el in v])

        self.g.remove_edges_from(nx.selfloop_edges(self.g))#remove self loops

        #node_locations = {index: locations for index, locations in tab_normal['location_id'].items()} #check se c'è almeno una location in comune

        #for node1, node2 in self.g.edges():
            #locations1 = node_locations.get(node1, None)  # Returns 2
            #locations2 = node_locations.get(node2, None)
            #common_locations = set(locations1) & set(locations2)
            #if common_locations:
                #self.g[node1][node2]['weight'] += self.location_weigth

        bridges_cent = bridgeness_centrality(self.g)
        #values = sorted([(a, b) for a, b in bridges_cent.items()], key=lambda x: x[1], reverse=True)
        nodes_positive_bridge = [(a, b) for a, b in bridges_cent.items() if b>self.bridgeness_threshold] 
        for v in nodes_positive_bridge: 
            self.g.remove_edges_from(list(self.g.edges(v[0])))

        if nx.number_of_edges(self.g)>0:
            self.l_com = nx.community.louvain_communities(self.g, resolution=self.resolution)
        else:
            self.l_com = [set([node]) for node in self.g.nodes()]
        
        print("Communities detection started")

        print(self.l_com)
    
        #l_com_s = l_com#sorted(l_com, key= lambda x: len(x), reverse=True)
        #comm_names = [[normals.get(c) for c in comm] for comm in l_com_s]
        

    def refine_communities(self, comm):
        #metadata, communities = {}, []   
    
        
        subgraph = self.g.subgraph(comm)
        subgraph = nx.Graph(subgraph)

        if nx.number_of_nodes(subgraph)==1:
            return comm
            
        #bridges = [c for c in nx.bridges(subgraph)]
        bridgeness = bridgeness_centrality(subgraph)
        bridgeness_values = sorted([(a, b) for a, b in bridgeness.items()], 
                                    key=lambda x: x[1], reverse=True)
        positive_bcentrality = [c for c in bridgeness_values if c[1]>self.bridgeness_threshold]
            
        if positive_bcentrality and len(subgraph)>1: #and brigdes
            for v in positive_bcentrality: 
                subgraph.remove_edges_from(list(subgraph.edges(v[0])))
            
            comm = nx.community.louvain_communities(subgraph, resolution=self.resolution)
            #    communities.append(sub_comm)
        #else:
        #    communities.append(comm)

        #l= [c for comm in communities for c in comm]

        return comm



    def task(self, list_, name=None):
        # Check if the list of communities is large
        # if len(list_) >= 1000:
        #     # Use atpbar for large datasets
        #     for i in atpbar(list_, name=name):
        #         l = self.refine_communities(i)
        #         name = uuid.uuid4()
        #         with open(f"res_network/newl_{name}.pickle", "wb") as f:
        #             pickle.dump(l, f)
        # else:
            # Directly process for smaller datasets
        result_dict = {}
        id_counter = 0 
        for i in list_:
            l = self.refine_communities(i)
            result_dict[id_counter] = l  # Use the counter as a key
            id_counter += 1  # Increment the counter
        self.results_normal = result_dict
        return result_dict



    def main(self):
        #  if len(self.l_com) > 1000:
        # # For larger data, use parallel processing with mantichora
        #     ss = np.array_split(self.l_com, 8)
        #     with mantichora(nworkers=8) as mcore:
        #          for i, s in enumerate(ss):
        #             mcore.run(self.task, s, name=f"process {i}")
        #             results_network = mcore.returns()
        #  else:
        # For smaller data, use a simple for-loop
         results_network = self.task(self.l_com)
         return results_network

class CommunityNaming:
    def __init__(self, results=None, pickle_path=None):
        if results:
            self.all_results = results
        elif pickle_path and os.path.exists(pickle_path):
            self.all_results = self.load_results_from_pickles(pickle_path)
        else:
            raise ValueError("No results provided and pickle path is invalid or does not exist.")
    
    @staticmethod
    def extract_first_name(sublist):
        if isinstance(sublist, list) and len(sublist) > 0:
            sublist=sorted(sublist)
            return sublist[0]
        elif isinstance(sublist, str):
            return sublist
        return None
    

    def load_results_from_pickles(self, pickle_path):
        all_results = {}
        for pickle_file in os.listdir(pickle_path):
            with open(os.path.join(pickle_path, pickle_file), 'rb') as f:
                result = pickle.load(f)
                all_results.update(result)
        return all_results

    def process_communities(self):

        tab_normal = pd.read_csv("normal.csv")
        id_to_name_map = tab_normal[tab_normal.columns[1]].to_dict()
        communities_with_names = {k: {id_to_name_map[node_id] for node_id in v} for k, v in self.all_results.items()}
        df_communities = pd.DataFrame(list(communities_with_names.items()), columns=['Community_ID', 'original_name'])
        df_communities['original_name'] = df_communities['original_name'].apply(list)
        df_communities['normalized_label_terrorizer'] = df_communities['original_name'].apply(lambda x: self.extract_first_name(x) if isinstance(x, list) else x)
        df1 = df_communities.explode('original_name', ignore_index=True)
        return df1
   
    def main(self):
        if not hasattr(self, 'all_results'):
            self.load_results_from_pickles(self.pickle_path)
        return self.process_communities()

        

