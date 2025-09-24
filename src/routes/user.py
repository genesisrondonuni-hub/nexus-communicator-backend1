from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Contact, Campaign, ImportedFile
from datetime import datetime
import json

user_bp = Blueprint('user', __name__)

# Rutas de autenticación
@user_bp.route('/auth/register', methods=['POST'])
def register():
    """Registrar nuevo usuario"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'Email, contraseña y nombre son requeridos'}), 400
        
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'El usuario ya existe'}), 400
        
        # Crear nuevo usuario
        user = User(
            email=data['email'],
            name=data['name'],
            phone=data.get('phone'),
            company=data.get('company')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Iniciar sesión automáticamente
        session['user_id'] = user.id
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/auth/login', methods=['POST'])
def login():
    """Iniciar sesión"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email y contraseña son requeridos'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        # Actualizar último login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Iniciar sesión
        session['user_id'] = user.id
        
        return jsonify({
            'message': 'Inicio de sesión exitoso',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Cerrar sesión"""
    session.pop('user_id', None)
    return jsonify({'message': 'Sesión cerrada exitosamente'}), 200

@user_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """Obtener usuario actual"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

# Rutas de perfil de usuario
@user_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Actualizar perfil de usuario"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        # Actualizar campos básicos
        if 'name' in data:
            user.name = data['name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'company' in data:
            user.company = data['company']
        
        # Actualizar API Keys
        if 'whatsapp_api_key' in data:
            user.whatsapp_api_key = data['whatsapp_api_key']
        if 'gmail_api_key' in data:
            user.gmail_api_key = data['gmail_api_key']
        if 'gemini_api_key' in data:
            user.gemini_api_key = data['gemini_api_key']
        
        # Actualizar configuración de automatización
        if 'gemini_auto_reply_enabled' in data:
            user.gemini_auto_reply_enabled = data['gemini_auto_reply_enabled']
        if 'gemini_knowledge_base' in data:
            user.gemini_knowledge_base = data['gemini_knowledge_base']
        
        # Actualizar configuración de notificaciones
        if 'email_notifications' in data:
            user.email_notifications = data['email_notifications']
        if 'push_notifications' in data:
            user.push_notifications = data['push_notifications']
        if 'sms_notifications' in data:
            user.sms_notifications = data['sms_notifications']
        
        # Actualizar configuración de privacidad
        if 'profile_visible' in data:
            user.profile_visible = data['profile_visible']
        if 'data_sharing' in data:
            user.data_sharing = data['data_sharing']
        if 'analytics' in data:
            user.analytics = data['analytics']
        
        # Actualizar configuración del sistema
        if 'language' in data:
            user.language = data['language']
        if 'timezone' in data:
            user.timezone = data['timezone']
        if 'theme' in data:
            user.theme = data['theme']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Rutas de contactos
@user_bp.route('/contacts', methods=['GET'])
def get_contacts():
    """Obtener contactos del usuario"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        contacts = Contact.query.filter_by(user_id=session['user_id']).all()
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/contacts', methods=['POST'])
def create_contact():
    """Crear nuevo contacto"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('phone'):
            return jsonify({'error': 'Nombre y teléfono son requeridos'}), 400
        
        contact = Contact(
            user_id=session['user_id'],
            name=data['name'],
            email=data.get('email'),
            phone=data['phone'],
            status=data.get('status', 'activo'),
            tags=json.dumps(data.get('tags', [])),
            notes=data.get('notes')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'message': 'Contacto creado exitosamente',
            'contact': contact.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Actualizar contacto"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=session['user_id']).first()
        if not contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            contact.name = data['name']
        if 'email' in data:
            contact.email = data['email']
        if 'phone' in data:
            contact.phone = data['phone']
        if 'status' in data:
            contact.status = data['status']
        if 'tags' in data:
            contact.tags = json.dumps(data['tags'])
        if 'notes' in data:
            contact.notes = data['notes']
        
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Contacto actualizado exitosamente',
            'contact': contact.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Eliminar contacto"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=session['user_id']).first()
        if not contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({'message': 'Contacto eliminado exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Rutas de campañas
@user_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """Obtener campañas del usuario"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        campaigns = Campaign.query.filter_by(user_id=session['user_id']).all()
        return jsonify({
            'campaigns': [campaign.to_dict() for campaign in campaigns]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    """Crear nueva campaña"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('message'):
            return jsonify({'error': 'Nombre y mensaje son requeridos'}), 400
        
        campaign = Campaign(
            user_id=session['user_id'],
            name=data['name'],
            message=data['message'],
            status=data.get('status', 'draft'),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
            media_url=data.get('media_url'),
            media_type=data.get('media_type')
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({
            'message': 'Campaña creada exitosamente',
            'campaign': campaign.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/campaigns/<int:campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    """Actualizar campaña"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=session['user_id']).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            campaign.name = data['name']
        if 'message' in data:
            campaign.message = data['message']
        if 'status' in data:
            campaign.status = data['status']
        if 'scheduled_at' in data:
            campaign.scheduled_at = datetime.fromisoformat(data['scheduled_at']) if data['scheduled_at'] else None
        if 'media_url' in data:
            campaign.media_url = data['media_url']
        if 'media_type' in data:
            campaign.media_type = data['media_type']
        
        campaign.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Campaña actualizada exitosamente',
            'campaign': campaign.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/campaigns/<int:campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """Eliminar campaña"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=session['user_id']).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        db.session.delete(campaign)
        db.session.commit()
        
        return jsonify({'message': 'Campaña eliminada exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Rutas de estadísticas
@user_bp.route('/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas del usuario"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        user_id = session['user_id']
        
        # Contar contactos
        total_contacts = Contact.query.filter_by(user_id=user_id).count()
        active_contacts = Contact.query.filter_by(user_id=user_id, status='activo').count()
        
        # Contar campañas
        total_campaigns = Campaign.query.filter_by(user_id=user_id).count()
        active_campaigns = Campaign.query.filter_by(user_id=user_id, status='active').count()
        
        # Sumar mensajes enviados
        total_messages = db.session.query(db.func.sum(Campaign.sent_count)).filter_by(user_id=user_id).scalar() or 0
        
        # Calcular tasa de respuesta promedio
        campaigns_with_stats = Campaign.query.filter_by(user_id=user_id).filter(Campaign.sent_count > 0).all()
        if campaigns_with_stats:
            total_sent = sum(c.sent_count for c in campaigns_with_stats)
            total_opened = sum(c.opened_count for c in campaigns_with_stats)
            response_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        else:
            response_rate = 0
        
        return jsonify({
            'stats': {
                'total_contacts': total_contacts,
                'active_contacts': active_contacts,
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'total_messages': total_messages,
                'response_rate': round(response_rate, 1)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

