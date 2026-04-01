import os
import json
import anthropic
import shutil
from pathlib import Path
from dotenv import load_dotenv
from services.extract_service import extract
from services.save_service import save_json

load_dotenv()
anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def generate_questions():
    directory_files = Path(__file__).parent.parent
    base_path = os.path.join(directory_files, 'doc', 'Programación Avanzada', 'IA')
    files = os.listdir(base_path)
    if len(files) == 0:
        raise Exception('No se encontraron archivos del curso que se desea extraer la información')

    for file in files:
        if file.startswith('~$'):
            continue

        path_file = os.path.join(base_path, file)
        questions_for_course(path_file)
        print(f'Archivo procesado: {file}')

def questions_for_course(path_file: str):
    try:
        course_data = extract(path_file)
        if len(course_data) == 0:
            raise Exception(f'El archivo {path_file} no contiene información válida')

        questions_theme = {
            'topic': course_data['topic'],
            'questions': []
        }

        for tema in course_data['themes']:
            data = anthropic_create_question(tema['title'], tema['content'], 2)
            questions_theme['questions'].extend(data)

        folder = 'training_questions'
        save_json(f'{course_data['topic']}_questions', questions_theme, folder)
        move_file_process(path_file)
    except Exception as e:
        print(f'Error al procesar el archivo {path_file}: {e}')


def move_file_process(source_file: str):
    base_path = Path(__file__).parent.parent
    destination_directory = Path.joinpath(base_path, 'doc', 'Programación Avanzada', 'PROCESADOS')
    shutil.move(source_file, destination_directory)

def anthropic_create_question(titulo: str, contenido: str, numero_preguntas: int) -> list:
    prompt = f"""
       Eres un experto en educación. Dado el siguiente contenido de una clase de Programación Avanzada,
       genera {numero_preguntas} pares de pregunta-respuesta en español.

       Titulo: {titulo}
       Contenido: {contenido}
        
       Reglas:
       - Las preguntas deben ser claras y directas
       - Las respuestas deben ser completas pero concisas
       - Varía el tipo de preguntas: definición, ejemplo, ventajas, comparación
       - Responde SOLO con un JSON válido, sin texto adicional

       Formato exacto:
       [
           {{"pregunta": "...", "respuesta": "..."}},
           {{"pregunta": "...", "respuesta": "..."}},
           {{"pregunta": "...", "respuesta": "..."}}
       ]
       """

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = response.content[0].text.strip()

    # Limpia por si Claude agrega backticks
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)
