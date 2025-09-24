from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Campaign, Contact, MediaFile, campaign_contacts
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import os

campaigns_bp = Blueprint('campaigns', __name__)

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

@campaigns_bp.route('/', methods=['GET'])
def get_campaigns():
    """Obtener lista de campañas del usuario"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status', '').strip()
        
        # Construir consulta
        query = Campaign.query.filter_by(user_id=user.id)
        
        # Filtrar por estado
        if status:
            query = query.filter_by(status=status)
        
        # Ordenar por fecha de creación (más recientes primero)
        query = query.order_by(Campaign.created_at.desc())
        
        # Paginación
        campaigns = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'campaigns': [campaign.to_dict() for campaign in campaigns.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': campaigns.total,
                'pages': campaigns.pages,
                'has_next': campaigns.has_next,
                'has_prev': campaigns.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/', methods=['POST'])
def create_campaign():
    """Crear una nueva campaña"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        # Validar datos requeridos
        if not data.get('name') or not data.get('message'):
            return jsonify({'error': 'Nombre y mensaje son requeridos'}), 400
        
        # Crear nueva campaña
        campaign = Campaign(
            user_id=user.id,
            name=data['name'].strip(),
            message=data['message'].strip(),
            status=data.get('status', 'draft'),
            scheduled_at=datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00')) if data.get('scheduled_at') else None
        )
        
        db.session.add(campaign)
        db.session.flush()  # Para obtener el ID de la campaña
        
        # Agregar contactos si se proporcionaron
        if data.get('contact_ids'):
            contacts = Contact.query.filter(
                Contact.id.in_(data['contact_ids']),
                Contact.user_id == user.id
            ).all()
            
            campaign.contacts = contacts
            campaign.total_recipients = len(contacts)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Campaña creada exitosamente',
            'campaign': campaign.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Obtener una campaña específica"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user.id).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        return jsonify({
            'campaign': campaign.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/<int:campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    """Actualizar una campaña"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user.id).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        # No permitir editar campañas ya enviadas
        if campaign.status in ['completed', 'active']:
            return jsonify({'error': 'No se puede editar una campaña ya enviada o activa'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        # Actualizar campos
        if 'name' in data:
            campaign.name = data['name'].strip()
        if 'message' in data:
            campaign.message = data['message'].strip()
        if 'status' in data:
            campaign.status = data['status']
        if 'scheduled_at' in data:
            campaign.scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00')) if data['scheduled_at'] else None
        
        # Actualizar contactos
        if 'contact_ids' in data:
            contacts = Contact.query.filter(
                Contact.id.in_(data['contact_ids']),
                Contact.user_id == user.id
            ).all()
            
            campaign.contacts = contacts
            campaign.total_recipients = len(contacts)
        
        campaign.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Campaña actualizada exitosamente',
            'campaign': campaign.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/<int:campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """Eliminar una campaña"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user.id).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        # No permitir eliminar campañas activas
        if campaign.status == 'active':
            return jsonify({'error': 'No se puede eliminar una campaña activa'}), 400
        
        db.session.delete(campaign)
        db.session.commit()
        
        return jsonify({
            'message': 'Campaña eliminada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/<int:campaign_id>/send', methods=['POST'])
def send_campaign(campaign_id):
    """Enviar una campaña inmediatamente"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user.id).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        # Verificar que la campaña esté en estado draft o scheduled
        if campaign.status not in ['draft', 'scheduled']:
            return jsonify({'error': 'La campaña ya fue enviada o está en proceso'}), 400
        
        # Verificar que tenga contactos
        if not campaign.contacts:
            return jsonify({'error': 'La campaña no tiene contactos asignados'}), 400
        
        # Verificar que el usuario tenga API keys configuradas
        if not user.whatsapp_api_key:
            return jsonify({'error': 'WhatsApp API Key no configurada'}), 400
        
        # Actualizar estado de la campaña
        campaign.status = 'active'
        campaign.sent_at = datetime.utcnow()
        
        # TODO: Implementar lógica real de envío de mensajes
        # Por ahora, simular el envío exitoso
        campaign.sent_count = len(campaign.contacts)
        campaign.status = 'completed'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Campaña enviada exitosamente',
            'campaign': campaign.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/<int:campaign_id>/preview', methods=['GET'])
def preview_campaign(campaign_id):
    """Obtener vista previa de una campaña"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user.id).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        # Obtener un contacto de ejemplo para la vista previa
        sample_contact = campaign.contacts[0] if campaign.contacts else None
        
        # Personalizar mensaje con datos del contacto de ejemplo
        preview_message = campaign.message
        if sample_contact:
            preview_message = preview_message.replace('{nombre}', sample_contact.name)
            preview_message = preview_message.replace('{telefono}', sample_contact.phone)
            if sample_contact.email:
                preview_message = preview_message.replace('{email}', sample_contact.email)
        
        return jsonify({
            'preview': {
                'message': preview_message,
                'sample_contact': sample_contact.to_dict() if sample_contact else None,
                'total_recipients': len(campaign.contacts),
                'media_files': [media.to_dict() for media in campaign.media_files]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/<int:campaign_id>/media', methods=['POST'])
def upload_campaign_media(campaign_id):
    """Subir archivo multimedia a una campaña"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user.id).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'No se proporcionó archivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        # Validar tipo de archivo
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.pdf', '.doc', '.docx'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': 'Tipo de archivo no permitido'}), 400
        
        # Crear directorio de uploads si no existe
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'campaigns')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        filename = secure_filename(file.filename)
        unique_filename = f"{campaign_id}_{datetime.utcnow().timestamp()}_{filename}"
        filepath = os.path.join(upload_dir, unique_filename)
        
        # Guardar archivo
        file.save(filepath)
        
        # Crear registro en la base de datos
        media_file = MediaFile(
            campaign_id=campaign.id,
            filename=unique_filename,
            original_filename=filename,
            filepath=filepath,
            mimetype=file.mimetype,
            file_size=os.path.getsize(filepath)
        )
        
        db.session.add(media_file)
        db.session.commit()
        
        return jsonify({
            'message': 'Archivo subido exitosamente',
            'media_file': media_file.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/<int:campaign_id>/media/<int:media_id>', methods=['DELETE'])
def delete_campaign_media(campaign_id, media_id):
    """Eliminar archivo multimedia de una campaña"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user.id).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        media_file = MediaFile.query.filter_by(id=media_id, campaign_id=campaign.id).first()
        if not media_file:
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        # Eliminar archivo físico
        try:
            if os.path.exists(media_file.filepath):
                os.remove(media_file.filepath)
        except Exception:
            pass  # Continuar aunque no se pueda eliminar el archivo físico
        
        # Eliminar registro de la base de datos
        db.session.delete(media_file)
        db.session.commit()
        
        return jsonify({
            'message': 'Archivo eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/<int:campaign_id>/generate-message', methods=['POST'])
def generate_message_with_ai(campaign_id):
    """Generar mensaje de campaña usando IA (Gemini)"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user.id).first()
        if not campaign:
            return jsonify({'error': 'Campaña no encontrada'}), 404
        
        if not user.gemini_api_key:
            return jsonify({'error': 'Gemini API Key no configurada'}), 400
        
        data = request.get_json()
        if not data or not data.get('prompt'):
            return jsonify({'error': 'Prompt requerido'}), 400
        
        prompt = data['prompt']
        tone = data.get('tone', 'profesional')
        
        # TODO: Implementar integración real con Gemini API
        # Por ahora, generar un mensaje de ejemplo
        generated_message = f"""¡Hola {{nombre}}!
        
Esperamos que te encuentres muy bien. Te escribimos para compartir contigo una oportunidad especial que no querrás perderte.

{prompt}

Si tienes alguna pregunta, no dudes en contactarnos. Estamos aquí para ayudarte.

¡Saludos cordiales!
{user.company or 'Nuestro equipo'}"""
        
        return jsonify({
            'generated_message': generated_message,
            'tone': tone,
            'prompt_used': prompt
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@campaigns_bp.route('/stats', methods=['GET'])
def get_campaigns_stats():
    """Obtener estadísticas de campañas"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        total_campaigns = Campaign.query.filter_by(user_id=user.id).count()
        draft_campaigns = Campaign.query.filter_by(user_id=user.id, status='draft').count()
        active_campaigns = Campaign.query.filter_by(user_id=user.id, status='active').count()
        completed_campaigns = Campaign.query.filter_by(user_id=user.id, status='completed').count()
        
        # Estadísticas de envío
        total_sent = db.session.query(db.func.sum(Campaign.sent_count))\
                              .filter_by(user_id=user.id).scalar() or 0
        total_opened = db.session.query(db.func.sum(Campaign.opened_count))\
                                .filter_by(user_id=user.id).scalar() or 0
        
        return jsonify({
            'stats': {
                'total_campaigns': total_campaigns,
                'draft_campaigns': draft_campaigns,
                'active_campaigns': active_campaigns,
                'completed_campaigns': completed_campaigns,
                'total_sent': total_sent,
                'total_opened': total_opened,
                'open_rate': round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

