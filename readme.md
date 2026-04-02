## Diagrama
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