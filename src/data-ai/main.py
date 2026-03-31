from services.course_information_service import extract_course_information

if __name__ == '__main__':
    print('Tecnológicas emergentes 🆕')
    print('\t Selecciona opción:')
    print('\t\t 1. Extraer información de un curso')
    print('\t\t 2. Generador de preguntas')
    opcion = input('\t\t > ')
    if opcion == '1':
        extract_course_information()
    elif opcion == '2':
        print('Generador de preguntas no implementado')
    else:
        print('Opción incorrecta ✖️✖')