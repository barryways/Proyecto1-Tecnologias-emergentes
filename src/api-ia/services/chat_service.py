import os
import logging
from openai import OpenAI

_logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
fine_tuned_model = os.getenv("OPENAI_MODEL_ID")

def ask_tutor(question: str) -> str:
    if not question:
        raise ValueError("La pregunta no puede estar vacía")

    response = openai_client.chat.completions.create(
        model=fine_tuned_model,
        messages=[
            {
                "role": "system",
                "content":
                    """
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
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return response.choices[0].message.content