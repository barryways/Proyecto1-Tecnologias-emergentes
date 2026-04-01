import os
import json

def save_json(file_name: str, content: dict, folder: str) -> str:
    output_path = build_output_path(file_name, folder)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    return output_path

def save_jsonl(file_name: str, content: list, folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    output_path = os.path.join(folder, f"{file_name}.jsonl")
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in content:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return output_path

def build_output_path(file_name: str, folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{file_name}.json")