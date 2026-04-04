from services.rag_service import initialize_rag_service
import os

_collection = None

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data',
    'dataset_final.json'
)

def get_collection_tutor_advanced_programming():
    global _collection
    if _collection is None:
        _collection = initialize_rag_service(DATASET_PATH, 'advanced_programming')
    return _collection