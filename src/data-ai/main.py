from services.course_information_service import extract_course_information
from services.generate_training_question_service import generate_questions
from services.dataset_service import unificar_datasets, claude_to_openai
from services.fine_tuning_openai import init_fine_tuning, status_fine_tuning

if __name__ == '__main__':
    print('Tecnológicas emergentes 🆕')
    print('\t Selecciona opción:')
    print('\t\t 1. Extraer información de un curso')
    print('\t\t 2. Generador de preguntas')
    print('\t\t 3. Unificar preguntas')
    print('\t\t 4. OpenAI dataset')
    print('\t\t 5. Entrenar modelo')
    print('\t\t 6. Monitorear modelo')
    opcion = input('\t\t > ')
    if opcion == '1':
        extract_course_information()
    elif opcion == '2':
        generate_questions()
    elif opcion == '3':
        unificar_datasets('training_questions')
    elif opcion == '4':
        claude_to_openai()
    elif opcion == '5':
        init_fine_tuning()
    elif opcion == '6':
        '''
            - 1
            ✅ File uploaded successfully. [ID] = file-9rXPEKnzZ51ErSA7Tc1BSU
            ✅ Job created successfully. [ID] = ftjob-5gUEKMUsoR30vKzwITp08A7z
            
            - 2
            ✅ File uploaded successfully. [ID] = file-97zHjzG4mbaezu6HThiBHw
            ✅ Job created successfully. [ID] = ftjob-SiXHd3Y9UFvMkpKQ9ic6hleW
            
            - 3
            ✅ Job created successfully. [ID] = ftjob-VxXQpjtNCotKNpEZox6szbAw
        '''
        status_fine_tuning(job_id='ftjob-VxXQpjtNCotKNpEZox6szbAw')
    else:
        print('Opción incorrecta ✖️✖')