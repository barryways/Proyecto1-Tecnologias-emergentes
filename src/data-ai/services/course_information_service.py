import os
import json
from services import extract_service, save_service
from pathlib import Path

def extract_course_information():
    directory_files = Path(__file__).parent.parent
    base_path = os.path.join(directory_files, 'doc', 'Programación Avanzada', 'IA')
    files = os.listdir(base_path)
    if len(files) == 0:
        raise Exception('No se encontraron archivos del curso que se desea extraer la información')

    for file in files:
        if file.startswith('~$'):
            continue

        file_path = os.path.join(base_path, file)
        save_information_json(file_path)
    print('Archivos extraídos correctamente')

def save_information_json(path_file: str) -> str:
    content = extract_service.extract(path_file)
    if len(content) == 0:
        return ''
    name = os.path.splitext(os.path.basename(path_file))[0]
    folder = 'course_information'
    return save_service.save_json(name, content, folder)