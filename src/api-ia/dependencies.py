from services.rag_service import initialize_rag_service
import os
import logging

logging.basicConfig(level=logging.INFO)

_logger = logging.getLogger(__name__)
_collection = None

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data',
    'dataset_final.json'
)


def get_collection_tutor_advanced_programming():
    global _collection
    if _collection is None:
        _logger.info('⏰ Initializing RAG service...')
        _collection = initialize_rag_service(DATASET_PATH, 'advanced_programming')
        _logger.info('🆗 RAG service initialized.')
    return _collection