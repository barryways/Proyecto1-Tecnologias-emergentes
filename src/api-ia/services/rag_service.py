import os
import json
import chromadb
from chromadb.utils import embedding_functions

# Define models to convert text to vector
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def initialize_rag_service(path_dataset: str, collection_name: str) -> chromadb.Collection:
    """
        Carga el dataset en una colección
        de chromadb
    :param path_dataset:
    :param collection_name:
    :return:
    """

    client = chromadb.PersistentClient(path="data/chroma_db")
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    collections = [c.name for c in client.list_collections()]
    if collection_name in collections:
        print("ChromaDB: Colección ya esta cargada ✅")
        return client.get_collection(
            name=collection_name,
            embedding_function=embedding_function
        )

    with open(path_dataset, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["data"]
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_function
    )
    collection.add(
        ids=[
            str(i)
            for i in range(len(items))
        ],
        documents=[
            f'{item["pregunta"]} {item["respuesta"]}'
            for item in items
        ],
        metadatas=[
            {"topic": item["topic"], "pregunta": item["pregunta"], "respuesta": item["respuesta"]}
            for item in items
        ]
    )

    print("ChromaDB: Colección se ha cargado ✅")
    return collection

def search_context(collection: chromadb.Collection, question: str, n_results: int = 3) -> str:
    """
        Busca los contextos más relevantes
        para la pregunta
    :param collection:
    :param question:
    :param n_results:
    :return:
    """

    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )

    contexts = []
    for i, metadata in enumerate(results["metadatas"][0]):
        contexts.append(
            f'Tema: {metadata["topic"]}\n'
            f'Pregunta: {metadata["pregunta"]}\n'
            f'Respuesta: {metadata["respuesta"]}'
        )

    return '\n\n--\n\n'.join(contexts)