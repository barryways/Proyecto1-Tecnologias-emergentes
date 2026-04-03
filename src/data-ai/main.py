from services.course_information_service import extract_course_information
from services.generate_training_question_service import generate_questions
from services.dataset_service import unificar_datasets

if __name__ == '__main__':
    print('Tecnológicas emergentes 🆕')
    print('\t Selecciona opción:')
    print('\t\t 1. Extraer información de un curso')
    print('\t\t 2. Generador de preguntas')
    print('\t\t 3. Unificar preguntas')
    opcion = input('\t\t > ')
    if opcion == '1':
        extract_course_information()
    elif opcion == '2':
        generate_questions()
    elif opcion == '3':
        unificar_datasets('training_questions')
    else:
        print('Opción incorrecta ✖️✖')