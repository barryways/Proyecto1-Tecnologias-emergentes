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
    SYSTEM_PROMPT = """Eres un tutor virtual del curso de Programación Avanzada.
    IMPORTANTE:
    - NO entregues código completo listo para ejecutar
    - Puedes dar pseudocódigo o fragmentos parciales explicativos
    - Responde SIEMPRE en formato Markdown
    - Si la pregunta está fuera del curso responde:
      'Esa pregunta está fuera del contenido del curso.'
    - Responde en español de manera clara y didáctica"""

    with open("dataset/dataset_final.json", "r", encoding="utf-8") as f:
        data = json.load(f)

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