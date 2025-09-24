# Plan de Desarrollo del Backend - Nexus Communicator

**Objetivo:** Crear un backend robusto y escalable con Flask para dar soporte a todas las funcionalidades de la aplicación Nexus Communicator, preparándolo para su despliegue en Render.com.

## 1. Modelos de Base de Datos (SQLAlchemy)

- **`User`**: Almacenará la información del usuario, incluyendo:
  - `id`, `name`, `email` (único), `password_hash`.
  - `phone`, `company`.
  - API Keys: `whatsapp_api_key`, `gmail_api_key`, `gemini_api_key`.
  - Configuración de automatización: `gemini_auto_reply_enabled`, `gemini_knowledge_base`.
  - Configuración de notificaciones y privacidad.
  - Configuración del sistema: `language`, `timezone`, `theme`.

- **`Contact`**: Almacenará los contactos de cada usuario.
  - `id`, `name`, `phone`, `email`.
  - `tags`, `notes`, `status`.
  - `user_id` (Foreign Key a `User`).

- **`Campaign`**: Almacenará las campañas de mensajería.
  - `id`, `name`, `message`, `status`.
  - `scheduled_at`, `created_at`.
  - `user_id` (Foreign Key a `User`).

- **`CampaignContact`**: Tabla de asociación para la relación muchos a muchos entre campañas y contactos.

- **`MediaFile`**: Almacenará información sobre los archivos multimedia adjuntos a las campañas.
  - `id`, `filename`, `filepath`, `mimetype`.
  - `campaign_id` (Foreign Key a `Campaign`).

- **`ImportedFile`**: Registro de los archivos importados (Excel, Sheets).
  - `id`, `filename`, `status`, `imported_contacts_count`.
  - `user_id` (Foreign Key a `User`).

## 2. Rutas de la API (Endpoints Flask)

### Autenticación (`/api/auth`)
- `POST /register`: Registrar un nuevo usuario.
- `POST /login`: Iniciar sesión y crear una sesión.
- `POST /logout`: Cerrar la sesión del usuario.
- `GET /me`: Obtener la información del usuario actualmente autenticado.

### Perfil de Usuario (`/api/profile`)
- `GET /`: Obtener el perfil completo del usuario.
- `PUT /`: Actualizar el perfil del usuario (incluyendo todas las configuraciones).

### Contactos (`/api/contacts`)
- `GET /`: Obtener la lista de contactos del usuario (con paginación y filtros).
- `POST /`: Crear un nuevo contacto.
- `GET /<id>`: Obtener un contacto específico.
- `PUT /<id>`: Actualizar un contacto.
- `DELETE /<id>`: Eliminar un contacto.
- `POST /import/sheets`: Importar contactos desde Google Sheets.
- `POST /import/drive`: Importar contactos desde un archivo de Google Drive (Excel/CSV).

### Campañas (`/api/campaigns`)
- `GET /`: Obtener la lista de campañas del usuario.
- `POST /`: Crear una nueva campaña.
- `GET /<id>`: Obtener detalles de una campaña.
- `PUT /<id>`: Actualizar una campaña.
- `DELETE /<id>`: Eliminar una campaña.
- `POST /<id>/send`: Enviar una campaña inmediatamente.

### Automatización (`/api/automation`)
- `GET /status`: Obtener el estado del bot de IA.
- `GET /activity`: Obtener la actividad reciente del bot.

### Estadísticas (`/api/stats`)
- `GET /dashboard`: Obtener las métricas principales para el dashboard.

## 3. Lógica de Negocio

- **Autenticación**: Usar `werkzeug` para hashear contraseñas y `flask-login` o sesiones de Flask para gestionar la autenticación.
- **Validación**: Implementar validación de datos para todas las entradas de la API para asegurar la integridad.
- **Integraciones**: Crear módulos de servicio para interactuar con las APIs de WhatsApp, Gmail y Gemini.
- **Manejo de Archivos**: Configurar una carpeta `uploads` para almacenar los archivos multimedia y los archivos importados de forma segura.

## 4. Configuración para Despliegue en Render.com

- **`requirements.txt`**: Asegurarse de que todas las dependencias estén listadas, incluyendo `gunicorn` para producción.
- **`render.yaml` (o configuración en el dashboard)**:
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn src.main:app`
- **Base de Datos**: Configurar Render para usar una base de datos PostgreSQL en producción, actualizando `SQLALCHEMY_DATABASE_URI` a través de variables de entorno.
- **Variables de Entorno**: Configurar `SECRET_KEY`, `DATABASE_URL`, `FLASK_ENV=production`, y las API keys en el entorno de Render.
- **CORS**: Asegurarse de que el origen del frontend desplegado en Netlify esté en la lista blanca de CORS.


