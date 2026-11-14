from .main import Terrorizer


def terrorizer_disambiguator(
    data,
    column_name,
    knowledge_base_path='./knowledge_base_duckduck24v2.csv',
    # Optimized hyperparameters (NBER Assignee, F1 = 0.71)
    weight_first_token=0.49,
    weight_same_t=0.17,          # "Token in common"
    weight_in_domain=0.81,
    weight_similarity=0.70,      # cosine similarity
    weight_token_text=0.52,      # text in first url
    match_thresh=1.80,
    resolution=0.50,
    bridge_thresh=1.80,
):
    terrorizer_instance = Terrorizer(
        data=data,
        knowledge_base_path=knowledge_base_path,
        column_name=column_name,
        threshold=0.8,
        weight_first_token=weight_first_token,
        weight_same_t=weight_same_t,
        weight_in_domain=weight_in_domain,
        weight_similarity=weight_similarity,
        weight_token_text=weight_token_text,
        resolution=resolution,
    )
    return terrorizer_instance.execute(match_thresh, bridge_thresh)
