import os
import sys
from datetime import timedelta

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, session
from flask_cors import CORS
from src.models.user import db

# Importar todas las rutas
from src.routes.auth import auth_bp
from src.routes.profile import profile_bp
from src.routes.contacts import contacts_bp
from src.routes.campaigns import campaigns_bp
from src.routes.automation import automation_bp
from src.routes.dashboard import dashboard_bp

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configuración de la aplicación
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexus-communicator-secret-key-2024-production')
    
    # Configuración de sesiones
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Configuración de CORS para permitir requests desde el frontend
    CORS(app, 
         supports_credentials=True,
         origins=[
             "http://localhost:5173",
             "http://localhost:3000",
             "https://*.netlify.app",
             "https://*.vercel.app",
             os.environ.get('FRONTEND_URL', '')
         ])
    
    # Configuración de la base de datos
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Para PostgreSQL en producción (Render)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # SQLite para desarrollo local
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(contacts_bp, url_prefix='/api/contacts')
    app.register_blueprint(campaigns_bp, url_prefix='/api/campaigns')
    app.register_blueprint(automation_bp, url_prefix='/api/automation')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    # Crear las tablas de la base de datos
    with app.app_context():
        try:
            db.create_all()
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error al inicializar la base de datos: {e}")
    
    # Ruta de salud para verificar que el servidor está funcionando
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'message': 'Nexus Communicator Backend está funcionando correctamente',
            'version': '1.0.0'
        }, 200
    
    # Ruta para servir archivos estáticos del frontend (si están presentes)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Servir archivos del frontend si están disponibles"""
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return {
                'message': 'Nexus Communicator API',
                'version': '1.0.0',
                'endpoints': {
                    'auth': '/api/auth',
                    'profile': '/api/profile',
                    'contacts': '/api/contacts',
                    'campaigns': '/api/campaigns',
                    'automation': '/api/automation',
                    'dashboard': '/api/dashboard',
                    'health': '/health'
                }
            }, 200

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return {
                    'message': 'Nexus Communicator API',
                    'version': '1.0.0',
                    'endpoints': {
                        'auth': '/api/auth',
                        'profile': '/api/profile',
                        'contacts': '/api/contacts',
                        'campaigns': '/api/campaigns',
                        'automation': '/api/automation',
                        'dashboard': '/api/dashboard',
                        'health': '/health'
                    }
                }, 200
    
    # Manejo de errores
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Endpoint no encontrado'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Error interno del servidor'}, 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Acceso prohibido'}, 403
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'No autorizado'}, 401
    
    return app

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"🚀 Iniciando Nexus Communicator Backend...")
    print(f"📍 Puerto: {port}")
    print(f"🔧 Modo debug: {debug}")
    print(f"🗄️ Base de datos: {'PostgreSQL (Producción)' if os.environ.get('DATABASE_URL') else 'SQLite (Desarrollo)'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

