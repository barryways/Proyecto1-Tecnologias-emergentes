import os
import anthropic
from services.rag_service import search_context

anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def ask_tutor(question: str, collection) -> str:
    if not question:
        raise ValueError("La pregunta no puede estar vacía")

    context = search_context(collection, question)

    if context is None:
        return "Pregunta está fuera del contenido"

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=f"""
            Eres un tutor virtual del curso de Programación Avanzada en C++.
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

        """,
        messages=[
            {"role": "user", "content": f"Contexto: {context}\n\nPregunta: {question}"}
        ]
    )

    return response.content[0].text