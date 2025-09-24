# Nexus Communicator - Backend

API REST construida con Flask para la plataforma de mensajería Nexus Communicator.

## 🚀 Características

- **API REST Completa**: Endpoints para autenticación, contactos, campañas y estadísticas
- **Base de Datos**: SQLite para desarrollo, PostgreSQL para producción
- **Autenticación**: Sistema de sesiones seguro con cookies
- **CORS**: Configurado para frontend React
- **Modelos Relacionales**: Usuario, Contactos, Campañas y Archivos Importados

## 📋 Requisitos Previos

- Python 3.8+
- pip (gestor de paquetes de Python)
- SQLite (incluido con Python)

## 🛠️ Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd nexus-communicator-backend
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicializar base de datos**
   ```bash
   python src/main.py
   ```

La base de datos se creará automáticamente en `src/database/app.db`.

## 🏃‍♂️ Ejecución

### Modo Desarrollo
```bash
source venv/bin/activate
python src/main.py
```

El servidor estará disponible en `http://localhost:5000`

### Modo Producción
Para producción, usa un servidor WSGI como Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
```

## 📡 API Endpoints

### Autenticación
- `POST /api/auth/register` - Registrar nuevo usuario
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/logout` - Cerrar sesión
- `GET /api/auth/me` - Obtener usuario actual

### Perfil de Usuario
- `PUT /api/profile` - Actualizar perfil y configuración

### Contactos
- `GET /api/contacts` - Obtener contactos del usuario
- `POST /api/contacts` - Crear nuevo contacto
- `PUT /api/contacts/{id}` - Actualizar contacto
- `DELETE /api/contacts/{id}` - Eliminar contacto

### Campañas
- `GET /api/campaigns` - Obtener campañas del usuario
- `POST /api/campaigns` - Crear nueva campaña
- `PUT /api/campaigns/{id}` - Actualizar campaña
- `DELETE /api/campaigns/{id}` - Eliminar campaña

### Estadísticas
- `GET /api/stats` - Obtener estadísticas del usuario

## 🗄️ Modelo de Base de Datos

### Usuario (users)
- Información personal y de contacto
- API Keys (WhatsApp, Gmail, Gemini)
- Configuración de automatización
- Preferencias de notificaciones y privacidad
- Configuración del sistema

### Contacto (contacts)
- Información de contacto
- Etiquetas y notas
- Estado (activo/inactivo)
- Timestamps de actividad

### Campaña (campaigns)
- Información de la campaña
- Mensaje y multimedia
- Estado y programación
- Estadísticas de envío

### Archivo Importado (imported_files)
- Historial de importaciones
- Tipo de archivo y contactos importados

## 🔧 Configuración

### Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu_clave_secreta_aqui
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
CORS_ORIGINS=http://localhost:5173,https://tu-frontend.netlify.app
```

### Base de Datos
Para usar PostgreSQL en producción:

```python
# En src/main.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/nexus_db'
```

## 🔐 Seguridad

### Autenticación
- Contraseñas hasheadas con Werkzeug
- Sesiones seguras con cookies
- Validación de entrada en todos los endpoints

### CORS
Configurado para permitir requests desde el frontend:
```python
CORS(app, supports_credentials=True)
```

### Validación
- Validación de datos de entrada
- Sanitización de parámetros
- Manejo seguro de errores

## 📁 Estructura del Proyecto

```
src/
├── models/
│   └── user.py         # Modelos de base de datos
├── routes/
│   └── user.py         # Rutas y endpoints
├── database/
│   └── app.db          # Base de datos SQLite
└── main.py             # Aplicación principal
```

## 🧪 Testing

Para ejecutar tests (cuando estén implementados):
```bash
python -m pytest tests/
```

## 🚀 Despliegue

### Heroku
1. Crear `Procfile`:
   ```
   web: gunicorn src.main:app
   ```

2. Configurar variables de entorno en Heroku
3. Deploy desde Git

### Railway/Render
1. Conectar repositorio
2. Configurar build command: `pip install -r requirements.txt`
3. Configurar start command: `python src/main.py`

### VPS/Servidor Propio
1. Instalar dependencias del sistema
2. Configurar Nginx como proxy reverso
3. Usar systemd para gestión de procesos

## 🔍 Monitoreo y Logs

### Logs de Desarrollo
Los logs se muestran en la consola durante el desarrollo.

### Logs de Producción
Para producción, configura logging a archivos:
```python
import logging
logging.basicConfig(filename='app.log', level=logging.INFO)
```

## 🐛 Solución de Problemas

### Error de Base de Datos
```bash
# Eliminar y recrear la base de datos
rm src/database/app.db
python src/main.py
```

### Error de CORS
Verifica que el frontend esté en la lista de orígenes permitidos:
```python
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
```

### Error de Dependencias
```bash
pip install --upgrade -r requirements.txt
```

## 📊 Performance

### Optimizaciones Implementadas
- Índices en campos de búsqueda frecuente
- Paginación en endpoints que retornan listas
- Compresión de respuestas JSON

### Recomendaciones para Producción
- Usar PostgreSQL en lugar de SQLite
- Implementar cache con Redis
- Configurar rate limiting
- Usar CDN para archivos estáticos

## 📞 Soporte

Para soporte técnico:
- Email: soporte@nexuscommunicator.com
- Issues: GitHub Issues
- Documentación: [Ver documentación completa](../docs/)

## 📄 Licencia

© 2024 Nexus Communicator. Todos los derechos reservados.

