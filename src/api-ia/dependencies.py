from services.rag_service import initialize_rag_service

_collection = None

def get_collection_tutor_advanced_programming():
    global _collection
    if _collection is None:
        _collection = initialize_rag_service('data/dataset_final.json', 'advanced_programming')
    return _collection