import os
import re
from pptx import Presentation

def extract(path_file: str) -> list:
    extension = os.path.splitext(path_file)[1]
    name = os.path.splitext(os.path.basename(path_file))[0]
    match extension:
        case '.pptx':
            return group_content_by_theme(content_in_pptx(path_file))
        case _:
            return []

def content_in_pptx(path_file: str) -> list:
    prs = Presentation(path_file)
    slides_content = []

    for i, slide in enumerate(prs.slides):
        content = []
        title = ''
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue

            text = clear_text(shape.text.strip())
            if not text:
                continue

            if re.search(r'^\d+$', text, re.IGNORECASE):
                continue

            try:
                if shape.is_placeholder:
                    idx = shape.placeholder_format.idx
                    if idx == 0:
                        title = text
                    else:
                        content.append(text)
                else:
                    content.append(text)
            except ValueError:
                content.append(text)

        if re.search(r'ejercicio|tarea', title, re.IGNORECASE):
            continue

        slides_content.append({
            'title': title,
            'content': content
        })
    return slides_content

def clear_text(text: str) -> str:
    return (text.replace('\x0b', ' ')
                .capitalize()
                .strip()
           )

def group_content_by_theme(slides_content: list) -> list:
    if len(slides_content) == 0:
        return []

    topic = slides_content[0]['title']
    topic_content = []
    topic_children = []

    for slide_content in slides_content[1:]:
        theme = slide_content['title']
        content = slide_content['content']
        if len(content) == 0:
            continue
        topic_children.append({
            'title': theme,
            'content': content
        })

    topic_content.append({
        'topic': topic,
        'content': topic_children
    })

    return topic_content

# TODO: Implement PDF extraction
def content_in_txt() -> list:
    raise NotImplementedError('PDF extraction not implemented yet')


# TODO: Implement PDF extraction
def content_in_pdf() -> list:
    raise NotImplementedError('PDF extraction not implemented yet')
