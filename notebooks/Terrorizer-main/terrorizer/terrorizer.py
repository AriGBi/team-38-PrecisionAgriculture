from .main import Terrorizer


def terrorizer_disambiguator(data, column_name):
    terrorizer_instance = Terrorizer(
        data=data,
        knowledge_base_path='./knowledge_base_duckduck24v2.csv',  
        column_name=column_name,
        threshold=0.8
    )
    return terrorizer_instance.execute()