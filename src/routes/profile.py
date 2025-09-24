from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

def require_auth():
    """Middleware para verificar autenticación"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return None
    
    return user

@profile_bp.route('/', methods=['GET'])
def get_profile():
    """Obtener perfil completo del usuario"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@profile_bp.route('/', methods=['PUT'])
def update_profile():
    """Actualizar perfil del usuario"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        # Actualizar información personal
        if 'name' in data:
            user.name = data['name'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip()
        if 'company' in data:
            user.company = data['company'].strip()
        
        # Actualizar API Keys
        if 'whatsapp_api_key' in data:
            user.whatsapp_api_key = data['whatsapp_api_key']
        if 'gmail_api_key' in data:
            user.gmail_api_key = data['gmail_api_key']
        if 'gemini_api_key' in data:
            user.gemini_api_key = data['gemini_api_key']
        
        # Actualizar configuración de automatización
        if 'gemini_auto_reply_enabled' in data:
            user.gemini_auto_reply_enabled = bool(data['gemini_auto_reply_enabled'])
        if 'gemini_knowledge_base' in data:
            user.gemini_knowledge_base = data['gemini_knowledge_base']
        
        # Actualizar configuración de notificaciones
        if 'email_notifications' in data:
            user.email_notifications = bool(data['email_notifications'])
        if 'push_notifications' in data:
            user.push_notifications = bool(data['push_notifications'])
        if 'sms_notifications' in data:
            user.sms_notifications = bool(data['sms_notifications'])
        
        # Actualizar configuración de privacidad
        if 'profile_visible' in data:
            user.profile_visible = bool(data['profile_visible'])
        if 'data_sharing' in data:
            user.data_sharing = bool(data['data_sharing'])
        if 'analytics' in data:
            user.analytics = bool(data['analytics'])
        
        # Actualizar configuración del sistema
        if 'language' in data:
            user.language = data['language']
        if 'timezone' in data:
            user.timezone = data['timezone']
        if 'theme' in data:
            user.theme = data['theme']
        
        # Actualizar timestamp
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@profile_bp.route('/change-password', methods=['POST'])
def change_password():
    """Cambiar contraseña del usuario"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Contraseña actual y nueva contraseña son requeridas'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Verificar contraseña actual
        if not user.check_password(current_password):
            return jsonify({'error': 'Contraseña actual incorrecta'}), 400
        
        # Validar nueva contraseña
        if len(new_password) < 6:
            return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
        
        # Actualizar contraseña
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Contraseña actualizada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@profile_bp.route('/api-keys', methods=['GET'])
def get_api_keys():
    """Obtener estado de las API keys (sin mostrar las keys completas)"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        def mask_key(key):
            if not key:
                return None
            if len(key) <= 8:
                return '*' * len(key)
            return key[:4] + '*' * (len(key) - 8) + key[-4:]
        
        return jsonify({
            'api_keys': {
                'whatsapp_configured': bool(user.whatsapp_api_key),
                'whatsapp_masked': mask_key(user.whatsapp_api_key),
                'gmail_configured': bool(user.gmail_api_key),
                'gmail_masked': mask_key(user.gmail_api_key),
                'gemini_configured': bool(user.gemini_api_key),
                'gemini_masked': mask_key(user.gemini_api_key)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@profile_bp.route('/delete-account', methods=['DELETE'])
def delete_account():
    """Eliminar cuenta del usuario"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if not data or not data.get('password'):
            return jsonify({'error': 'Contraseña requerida para eliminar la cuenta'}), 400
        
        # Verificar contraseña
        if not user.check_password(data['password']):
            return jsonify({'error': 'Contraseña incorrecta'}), 400
        
        # Eliminar usuario (las relaciones se eliminan en cascada)
        db.session.delete(user)
        db.session.commit()
        
        # Limpiar sesión
        session.clear()
        
        return jsonify({
            'message': 'Cuenta eliminada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

