import os
import json
from services.save_service import save_jsonl, save_json

def unificar_datasets(carpeta: str):
    dataset_final = []
    archivos = [f for f in os.listdir(carpeta) if f.endswith("_questions.json")]

    print(f"📂 Archivos encontrados: {len(archivos)}")

    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)

        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)

        topic = data["topic"]
        questions = data["questions"]

        for q in questions:
            dataset_final.append({
                "topic": topic,
                "pregunta": q["pregunta"],
                "respuesta": q["respuesta"]
            })

        print(f"   ✅ {topic}: {len(questions)} preguntas")

    output_folder = "dataset"
    json_path = save_json("dataset_final", {"total": len(dataset_final), "data": dataset_final}, output_folder)
    jsonl_path = save_jsonl("dataset_final", dataset_final, output_folder)

    print(f"\n✅ Total: {len(dataset_final)} pares pregunta-respuesta")
    print(f"📁 JSON  → {json_path}")
    print(f"📁 JSONL → {jsonl_path}")

def claude_to_openai():
    SYSTEM_PROMPT = """
        Eres un tutor virtual del curso de Programación Avanzada.
        Responde ÚNICAMENTE basándote en el contexto del curso.
        
        FORMATO DE RESPUESTA:
        - Responde SIEMPRE en formato Markdown
        - Usa ## para títulos de secciones
        - Usa **negrita** para conceptos importantes
        - Usa listas con - para enumerar puntos
        - Usa bloques de código con ```cpp o ```pseudocode para ejemplos de código
        
        IMPORTANTE:
        - NO entregues código completo listo para ejecutar
        - Puedes dar pseudocódigo o fragmentos parciales explicativos
        - Explica qué hacer pero no cómo hacerlo con código exacto
        - Si la pregunta está fuera del curso responde:
          'Esa pregunta está fuera del contenido del curso.'
        - Responde siempre en español de manera clara y didáctica
    """

    with open("dataset/dataset_final.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    RECHAZO = "Esa pregunta está fuera del contenido del curso."
    preguntas_fuera = [
        "¿Cómo hago una página web en HTML?",
        "¿Qué es Python?",
        "¿Cuánto es 2+2?",
        "¿Cómo instalo Windows?",
        "¿Qué es la inteligencia artificial?",
        "¿Cómo funciona una base de datos SQL?",
        "¿Qué es JavaScript?",
        "¿Cómo creo una app móvil?",
        "¿Qué es machine learning?",
        "¿Cómo funciona internet?",
        "¿Qué es un sistema operativo?",
        "¿Cómo se programa en Java?",
        "¿Qué es la nube (cloud computing)?",
        "¿Cómo instalo un servidor web?",
        "¿Qué es Docker?",
        "¿Cómo se hace un videojuego?",
        "¿Qué es Git?",
        "¿Cómo funciona el protocolo HTTP?",
        "¿Qué es una API REST?",
        "¿Cómo se hace scraping web?",
        "¿Qué lenguaje de programación debo aprender primero?",
        "¿Cuál es la capital de Francia?",
        "¿Quién fue Albert Einstein?",
        "¿Cómo funciona el motor de un auto?",
        "¿Cuál es la fórmula de la fotosíntesis?",
        "¿Qué es el calentamiento global?",
        "¿Cómo se calcula el área de un círculo?",
        "¿Qué es la economía?",
        "¿Cómo funciona una red neuronal?",
        "¿Qué es blockchain?",
        "¿Puedes escribirme un ensayo?",
        "¿Cómo aprendo inglés rápido?",
        "¿Qué películas me recomiendas?",
        "¿Cómo funciona Excel?",
        "¿Qué es un antivirus?",
        "¿Cómo hago un currículum?",
        "¿Qué es la ciberseguridad?",
        "¿Cómo funciona un compilador en general?",
        "¿Qué es TypeScript?",
        "¿Cómo se usa Linux?",
    ]

    with open("dataset/dataset_openai.jsonl", "w", encoding="utf-8") as f:
        for item in data["data"]:
            entry = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": item["pregunta"]},
                    {"role": "assistant", "content": item["respuesta"]}
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        for pregunta in preguntas_fuera:
            entry = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": pregunta},
                    {"role": "assistant", "content": RECHAZO}
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")