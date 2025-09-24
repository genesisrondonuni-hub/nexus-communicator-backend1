from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, BotActivity
from datetime import datetime, timedelta

automation_bp = Blueprint('automation', __name__)

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

@automation_bp.route('/status', methods=['GET'])
def get_automation_status():
    """Obtener el estado del bot de automatización"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        return jsonify({
            'automation': {
                'enabled': user.gemini_auto_reply_enabled,
                'gemini_configured': bool(user.gemini_api_key),
                'knowledge_base_configured': bool(user.gemini_knowledge_base),
                'last_activity': None  # Se actualizará con actividad real
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@automation_bp.route('/toggle', methods=['POST'])
def toggle_automation():
    """Activar/desactivar respuestas automáticas"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if 'enabled' not in data:
            return jsonify({'error': 'Campo "enabled" requerido'}), 400
        
        # Verificar que las configuraciones necesarias estén presentes
        if data['enabled']:
            if not user.gemini_api_key:
                return jsonify({'error': 'Gemini API Key no configurada'}), 400
            if not user.gemini_knowledge_base:
                return jsonify({'error': 'Base de conocimiento no configurada'}), 400
        
        user.gemini_auto_reply_enabled = bool(data['enabled'])
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar actividad
        activity = BotActivity(
            user_id=user.id,
            activity_type='automation_toggled',
            message_content=f"Automatización {'activada' if user.gemini_auto_reply_enabled else 'desactivada'}",
            status='success'
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'message': f'Automatización {"activada" if user.gemini_auto_reply_enabled else "desactivada"} exitosamente',
            'enabled': user.gemini_auto_reply_enabled
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@automation_bp.route('/knowledge-base', methods=['GET'])
def get_knowledge_base():
    """Obtener la base de conocimiento del agente"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        return jsonify({
            'knowledge_base': user.gemini_knowledge_base or '',
            'last_updated': user.updated_at.isoformat() if user.updated_at else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@automation_bp.route('/knowledge-base', methods=['PUT'])
def update_knowledge_base():
    """Actualizar la base de conocimiento del agente"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if not data or 'knowledge_base' not in data:
            return jsonify({'error': 'Campo "knowledge_base" requerido'}), 400
        
        user.gemini_knowledge_base = data['knowledge_base']
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar actividad
        activity = BotActivity(
            user_id=user.id,
            activity_type='knowledge_base_updated',
            message_content='Base de conocimiento actualizada',
            status='success'
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'message': 'Base de conocimiento actualizada exitosamente',
            'knowledge_base': user.gemini_knowledge_base
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@automation_bp.route('/activity', methods=['GET'])
def get_bot_activity():
    """Obtener actividad reciente del bot"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        activity_type = request.args.get('type', '').strip()
        
        # Construir consulta
        query = BotActivity.query.filter_by(user_id=user.id)
        
        # Filtrar por tipo de actividad
        if activity_type:
            query = query.filter_by(activity_type=activity_type)
        
        # Ordenar por fecha (más recientes primero)
        query = query.order_by(BotActivity.created_at.desc())
        
        # Paginación
        activities = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'activities': [activity.to_dict() for activity in activities.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': activities.total,
                'pages': activities.pages,
                'has_next': activities.has_next,
                'has_prev': activities.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@automation_bp.route('/activity/stats', methods=['GET'])
def get_activity_stats():
    """Obtener estadísticas de actividad del bot"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Estadísticas de los últimos 30 días
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        total_activities = BotActivity.query.filter_by(user_id=user.id).count()
        recent_activities = BotActivity.query.filter(
            BotActivity.user_id == user.id,
            BotActivity.created_at >= thirty_days_ago
        ).count()
        
        # Actividades por tipo
        message_received = BotActivity.query.filter_by(
            user_id=user.id, 
            activity_type='message_received'
        ).count()
        
        auto_replies = BotActivity.query.filter_by(
            user_id=user.id, 
            activity_type='auto_reply_sent'
        ).count()
        
        successful_activities = BotActivity.query.filter_by(
            user_id=user.id, 
            status='success'
        ).count()
        
        failed_activities = BotActivity.query.filter_by(
            user_id=user.id, 
            status='failed'
        ).count()
        
        # Actividades de hoy
        today = datetime.utcnow().date()
        today_activities = BotActivity.query.filter(
            BotActivity.user_id == user.id,
            db.func.date(BotActivity.created_at) == today
        ).count()
        
        return jsonify({
            'stats': {
                'total_activities': total_activities,
                'recent_activities': recent_activities,
                'today_activities': today_activities,
                'message_received': message_received,
                'auto_replies': auto_replies,
                'successful_activities': successful_activities,
                'failed_activities': failed_activities,
                'success_rate': round((successful_activities / total_activities * 100) if total_activities > 0 else 0, 2)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@automation_bp.route('/test-response', methods=['POST'])
def test_auto_response():
    """Probar respuesta automática con un mensaje de ejemplo"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        if not user.gemini_api_key:
            return jsonify({'error': 'Gemini API Key no configurada'}), 400
        
        if not user.gemini_knowledge_base:
            return jsonify({'error': 'Base de conocimiento no configurada'}), 400
        
        data = request.get_json()
        if not data or not data.get('test_message'):
            return jsonify({'error': 'Mensaje de prueba requerido'}), 400
        
        test_message = data['test_message']
        
        # TODO: Implementar integración real con Gemini API
        # Por ahora, generar una respuesta de ejemplo
        sample_response = f"""Hola, gracias por tu mensaje: "{test_message}"

Basándome en la información de nuestro negocio, puedo ayudarte con:
- Información sobre nuestros productos y servicios
- Horarios de atención
- Preguntas frecuentes
- Soporte técnico

¿En qué más puedo asistirte?

---
Esta es una respuesta generada automáticamente por nuestro asistente IA."""
        
        # Registrar actividad de prueba
        activity = BotActivity(
            user_id=user.id,
            activity_type='test_response',
            contact_name='Usuario de Prueba',
            message_content=test_message,
            response_content=sample_response,
            status='success'
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'test_message': test_message,
            'generated_response': sample_response,
            'response_time': '1.2s',
            'confidence': 0.95
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@automation_bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Webhook para recibir mensajes de WhatsApp y generar respuestas automáticas"""
    try:
        # TODO: Implementar webhook real de WhatsApp
        # Este endpoint recibiría mensajes de WhatsApp y generaría respuestas automáticas
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        # Simular procesamiento de mensaje entrante
        return jsonify({
            'status': 'processed',
            'message': 'Webhook procesado exitosamente'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@automation_bp.route('/settings', methods=['GET'])
def get_automation_settings():
    """Obtener configuración completa de automatización"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        return jsonify({
            'settings': {
                'auto_reply_enabled': user.gemini_auto_reply_enabled,
                'gemini_api_configured': bool(user.gemini_api_key),
                'knowledge_base_configured': bool(user.gemini_knowledge_base),
                'knowledge_base_length': len(user.gemini_knowledge_base or ''),
                'last_updated': user.updated_at.isoformat() if user.updated_at else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@automation_bp.route('/clear-activity', methods=['DELETE'])
def clear_activity_history():
    """Limpiar historial de actividad del bot"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Eliminar todas las actividades del usuario
        deleted_count = BotActivity.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        return jsonify({
            'message': f'Historial de actividad limpiado: {deleted_count} registros eliminados',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

