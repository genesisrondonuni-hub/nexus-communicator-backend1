from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Contact, Campaign, BotActivity
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

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

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Obtener estadísticas principales para el dashboard"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Estadísticas básicas
        total_contacts = Contact.query.filter_by(user_id=user.id).count()
        total_campaigns = Campaign.query.filter_by(user_id=user.id).count()
        active_campaigns = Campaign.query.filter_by(user_id=user.id, status='active').count()
        
        # Mensajes enviados (suma de sent_count de todas las campañas)
        total_messages_sent = db.session.query(func.sum(Campaign.sent_count))\
                                       .filter_by(user_id=user.id).scalar() or 0
        
        # Actividad del bot en los últimos 30 días
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        bot_activities = BotActivity.query.filter(
            BotActivity.user_id == user.id,
            BotActivity.created_at >= thirty_days_ago
        ).count()
        
        # Contactos agregados en los últimos 7 días
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        new_contacts = Contact.query.filter(
            Contact.user_id == user.id,
            Contact.created_at >= seven_days_ago
        ).count()
        
        # Campañas completadas en los últimos 30 días
        completed_campaigns = Campaign.query.filter(
            Campaign.user_id == user.id,
            Campaign.status == 'completed',
            Campaign.sent_at >= thirty_days_ago
        ).count()
        
        return jsonify({
            'stats': {
                'total_contacts': total_contacts,
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'total_messages_sent': total_messages_sent,
                'bot_activities': bot_activities,
                'new_contacts': new_contacts,
                'completed_campaigns': completed_campaigns,
                'automation_enabled': user.gemini_auto_reply_enabled
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@dashboard_bp.route('/charts/contacts', methods=['GET'])
def get_contacts_chart_data():
    """Obtener datos para gráfico de contactos por mes"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Obtener contactos de los últimos 12 meses agrupados por mes
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        contacts_by_month = db.session.query(
            func.strftime('%Y-%m', Contact.created_at).label('month'),
            func.count(Contact.id).label('count')
        ).filter(
            Contact.user_id == user.id,
            Contact.created_at >= twelve_months_ago
        ).group_by(
            func.strftime('%Y-%m', Contact.created_at)
        ).order_by('month').all()
        
        # Formatear datos para el gráfico
        chart_data = []
        for month, count in contacts_by_month:
            try:
                month_date = datetime.strptime(month, '%Y-%m')
                chart_data.append({
                    'month': month_date.strftime('%b %Y'),
                    'contacts': count
                })
            except:
                continue
        
        return jsonify({
            'chart_data': chart_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@dashboard_bp.route('/charts/campaigns', methods=['GET'])
def get_campaigns_chart_data():
    """Obtener datos para gráfico de campañas"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Estadísticas de campañas por estado
        campaign_stats = db.session.query(
            Campaign.status,
            func.count(Campaign.id).label('count')
        ).filter_by(user_id=user.id).group_by(Campaign.status).all()
        
        # Formatear datos para gráfico de dona
        chart_data = []
        status_labels = {
            'draft': 'Borradores',
            'scheduled': 'Programadas',
            'active': 'Activas',
            'completed': 'Completadas',
            'paused': 'Pausadas'
        }
        
        for status, count in campaign_stats:
            chart_data.append({
                'status': status_labels.get(status, status),
                'count': count
            })
        
        return jsonify({
            'chart_data': chart_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@dashboard_bp.route('/charts/messages', methods=['GET'])
def get_messages_chart_data():
    """Obtener datos para gráfico de mensajes enviados por día"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Obtener mensajes de los últimos 30 días
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        messages_by_day = db.session.query(
            func.date(Campaign.sent_at).label('date'),
            func.sum(Campaign.sent_count).label('messages')
        ).filter(
            Campaign.user_id == user.id,
            Campaign.sent_at >= thirty_days_ago,
            Campaign.sent_count > 0
        ).group_by(
            func.date(Campaign.sent_at)
        ).order_by('date').all()
        
        # Formatear datos para el gráfico
        chart_data = []
        for date, messages in messages_by_day:
            if date:
                chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'messages': messages or 0
                })
        
        return jsonify({
            'chart_data': chart_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@dashboard_bp.route('/recent-activity', methods=['GET'])
def get_recent_activity():
    """Obtener actividad reciente para el dashboard"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Actividad reciente del bot (últimas 10)
        recent_bot_activities = BotActivity.query.filter_by(user_id=user.id)\
                                                 .order_by(BotActivity.created_at.desc())\
                                                 .limit(10).all()
        
        # Contactos recientes (últimos 5)
        recent_contacts = Contact.query.filter_by(user_id=user.id)\
                                      .order_by(Contact.created_at.desc())\
                                      .limit(5).all()
        
        # Campañas recientes (últimas 5)
        recent_campaigns = Campaign.query.filter_by(user_id=user.id)\
                                        .order_by(Campaign.created_at.desc())\
                                        .limit(5).all()
        
        return jsonify({
            'recent_activity': {
                'bot_activities': [activity.to_dict() for activity in recent_bot_activities],
                'contacts': [contact.to_dict() for contact in recent_contacts],
                'campaigns': [campaign.to_dict() for campaign in recent_campaigns]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@dashboard_bp.route('/performance', methods=['GET'])
def get_performance_metrics():
    """Obtener métricas de rendimiento"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Métricas de los últimos 30 días
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Tasa de apertura promedio
        campaigns_with_stats = Campaign.query.filter(
            Campaign.user_id == user.id,
            Campaign.sent_count > 0,
            Campaign.sent_at >= thirty_days_ago
        ).all()
        
        total_sent = sum(c.sent_count for c in campaigns_with_stats)
        total_opened = sum(c.opened_count for c in campaigns_with_stats)
        open_rate = round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2)
        
        # Actividad del bot
        successful_bot_activities = BotActivity.query.filter(
            BotActivity.user_id == user.id,
            BotActivity.status == 'success',
            BotActivity.created_at >= thirty_days_ago
        ).count()
        
        total_bot_activities = BotActivity.query.filter(
            BotActivity.user_id == user.id,
            BotActivity.created_at >= thirty_days_ago
        ).count()
        
        bot_success_rate = round((successful_bot_activities / total_bot_activities * 100) if total_bot_activities > 0 else 0, 2)
        
        # Crecimiento de contactos
        contacts_this_month = Contact.query.filter(
            Contact.user_id == user.id,
            Contact.created_at >= thirty_days_ago
        ).count()
        
        sixty_days_ago = datetime.utcnow() - timedelta(days=60)
        contacts_last_month = Contact.query.filter(
            Contact.user_id == user.id,
            Contact.created_at >= sixty_days_ago,
            Contact.created_at < thirty_days_ago
        ).count()
        
        contact_growth = round(((contacts_this_month - contacts_last_month) / contacts_last_month * 100) if contacts_last_month > 0 else 0, 2)
        
        return jsonify({
            'performance': {
                'open_rate': open_rate,
                'bot_success_rate': bot_success_rate,
                'contact_growth': contact_growth,
                'total_sent_30_days': total_sent,
                'total_opened_30_days': total_opened,
                'bot_activities_30_days': total_bot_activities,
                'new_contacts_30_days': contacts_this_month
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@dashboard_bp.route('/quick-actions', methods=['GET'])
def get_quick_actions():
    """Obtener acciones rápidas sugeridas para el usuario"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        suggestions = []
        
        # Verificar configuraciones pendientes
        if not user.whatsapp_api_key:
            suggestions.append({
                'type': 'config',
                'title': 'Configurar WhatsApp API',
                'description': 'Conecta tu cuenta de WhatsApp Business para enviar mensajes',
                'action': 'configure_whatsapp',
                'priority': 'high'
            })
        
        if not user.gemini_api_key:
            suggestions.append({
                'type': 'config',
                'title': 'Configurar Gemini IA',
                'description': 'Activa respuestas automáticas inteligentes',
                'action': 'configure_gemini',
                'priority': 'medium'
            })
        
        # Verificar si hay contactos
        total_contacts = Contact.query.filter_by(user_id=user.id).count()
        if total_contacts == 0:
            suggestions.append({
                'type': 'action',
                'title': 'Agregar Contactos',
                'description': 'Importa o agrega tus primeros contactos',
                'action': 'add_contacts',
                'priority': 'high'
            })
        
        # Verificar campañas en borrador
        draft_campaigns = Campaign.query.filter_by(user_id=user.id, status='draft').count()
        if draft_campaigns > 0:
            suggestions.append({
                'type': 'action',
                'title': f'Completar {draft_campaigns} Campaña(s)',
                'description': 'Tienes campañas en borrador listas para enviar',
                'action': 'complete_campaigns',
                'priority': 'medium'
            })
        
        # Sugerir configurar base de conocimiento si la automatización está activada pero no configurada
        if user.gemini_auto_reply_enabled and not user.gemini_knowledge_base:
            suggestions.append({
                'type': 'config',
                'title': 'Configurar Base de Conocimiento',
                'description': 'Mejora las respuestas automáticas con información de tu negocio',
                'action': 'configure_knowledge_base',
                'priority': 'high'
            })
        
        return jsonify({
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

