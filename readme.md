# StudyBot

Proyecto con backend en FastAPI y frontend en React para autenticación y chat estudiantil.

## Configuración rápida

### Backend

1. Edita `src/api-ia/.env` con los datos reales de tu instancia MySQL en AWS.
2. Instala dependencias con `python -m pip install -r src/api-ia/requirements.txt`.
3. Asegúrate de haber ejecutado el script SQL de creación de `studybot_db` en tu base de datos.
4. Inicia el backend desde `src/api-ia` con `uvicorn main:app --reload`.

Variables importantes del backend:

- `DATABASE_URL`: URL completa de conexión si prefieres una sola variable.
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: alternativa para armar la conexión.
- `DB_SSL_ENABLED`, `DB_SSL_CA`: opciones para conexión TLS a AWS/RDS.
- `JWT_SECRET`: firma de tokens.
- `CORS_ORIGINS`: orígenes permitidos para el frontend.

### Frontend

1. Edita `src-ui/Frontend/.env` con la URL del backend.
2. Instala dependencias con `npm install`.
3. Inicia Vite con `npm run dev`.

## Persistencia

El backend ya no usa los archivos CSV para autenticación ni conversaciones. Ahora guarda:

- Usuarios en la tabla `usuario`
- Conversaciones en la tabla `conversacion`
- Mensajes en la tabla `mensaje`

Durante el arranque, el backend también verifica que existan:

- Roles `admin` y `student`
- Tipos de mensaje `user`, `assistant` y `system`
- Un usuario administrador por defecto usando las variables `AUTH_DEFAULT_ADMIN_*`

## Diagrama

```mermaid
erDiagram
    ROL_USUARIO {
        INT id_rol PK
        VARCHAR descripcion
        TIMESTAMP fec_creacion
    }

    USUARIO {
        BIGINT id_usuario PK
        VARCHAR nombre
        VARCHAR apellido
        VARCHAR no_carnet
        VARCHAR correo
        VARCHAR clave_hash
        INT id_rol FK
        TIMESTAMP fec_creacion
    }

    CONVERSACION {
        UUID id_conversacion PK
        BIGINT id_usuario FK
        VARCHAR titulo
        TIMESTAMP fec_creacion
        TIMESTAMP fec_actualizacion
    }

    TIPO_MENSAJE {
        INT id_tipo_mensaje PK
        VARCHAR descripcion
    }

    MENSAJE {
        BIGINT id_mensaje PK
        UUID id_conversacion FK
        INT id_tipo_mensaje FK
        TEXT contenido
        TIMESTAMP fecha_hora
        INT orden_mensaje
    }

    ROL_USUARIO ||--o{ USUARIO : tiene
    USUARIO ||--o{ CONVERSACION : crea
    CONVERSACION ||--o{ MENSAJE : contiene
    TIPO_MENSAJE ||--o{ MENSAJE : clasifica
```
