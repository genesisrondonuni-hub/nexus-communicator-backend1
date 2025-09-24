from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Tabla de asociación para la relación muchos a muchos entre campañas y contactos
campaign_contacts = db.Table('campaign_contacts',
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaigns.id'), primary_key=True),
    db.Column('contact_id', db.Integer, db.ForeignKey('contacts.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    
    # API Keys
    whatsapp_api_key = db.Column(db.Text, nullable=True)
    gmail_api_key = db.Column(db.Text, nullable=True)
    gemini_api_key = db.Column(db.Text, nullable=True)
    
    # Configuración de automatización
    gemini_auto_reply_enabled = db.Column(db.Boolean, default=False)
    gemini_knowledge_base = db.Column(db.Text, nullable=True)
    
    # Configuración de notificaciones
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    
    # Configuración de privacidad
    profile_visible = db.Column(db.Boolean, default=True)
    data_sharing = db.Column(db.Boolean, default=False)
    analytics = db.Column(db.Boolean, default=True)
    
    # Configuración del sistema
    language = db.Column(db.String(10), default='es')
    timezone = db.Column(db.String(50), default='Europe/Madrid')
    theme = db.Column(db.String(10), default='light')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    contacts = db.relationship('Contact', backref='user', lazy=True, cascade='all, delete-orphan')
    campaigns = db.relationship('Campaign', backref='user', lazy=True, cascade='all, delete-orphan')
    imported_files = db.relationship('ImportedFile', backref='user', lazy=True, cascade='all, delete-orphan')
    bot_activities = db.relationship('BotActivity', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Establece la contraseña hasheada"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'company': self.company,
            'whatsapp_api_key': self.whatsapp_api_key,
            'gmail_api_key': self.gmail_api_key,
            'gemini_api_key': self.gemini_api_key,
            'gemini_auto_reply_enabled': self.gemini_auto_reply_enabled,
            'gemini_knowledge_base': self.gemini_knowledge_base,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'sms_notifications': self.sms_notifications,
            'profile_visible': self.profile_visible,
            'data_sharing': self.data_sharing,
            'analytics': self.analytics,
            'language': self.language,
            'timezone': self.timezone,
            'theme': self.theme,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='activo')  # activo, inactivo
    tags = db.Column(db.Text, nullable=True)  # JSON string de tags
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'tags': self.tags,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_message': self.last_message.isoformat() if self.last_message else None
        }

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, active, completed, paused
    
    # Estadísticas
    sent_count = db.Column(db.Integer, default=0)
    opened_count = db.Column(db.Integer, default=0)
    clicked_count = db.Column(db.Integer, default=0)
    total_recipients = db.Column(db.Integer, default=0)
    
    # Programación
    scheduled_at = db.Column(db.DateTime, nullable=True)
    
    # Multimedia
    media_url = db.Column(db.String(500), nullable=True)
    media_type = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    contacts = db.relationship('Contact', secondary=campaign_contacts, lazy='subquery',
                              backref=db.backref('campaigns', lazy=True))
    media_files = db.relationship('MediaFile', backref='campaign', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'message': self.message,
            'status': self.status,
            'sent_count': self.sent_count,
            'opened_count': self.opened_count,
            'clicked_count': self.clicked_count,
            'total_recipients': self.total_recipients,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'media_url': self.media_url,
            'media_type': self.media_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'contacts': [contact.to_dict() for contact in self.contacts],
            'media_files': [media.to_dict() for media in self.media_files]
        }

class MediaFile(db.Model):
    __tablename__ = 'media_files'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    mimetype = db.Column(db.String(100))
    file_size = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'filepath': self.filepath,
            'mimetype': self.mimetype,
            'file_size': self.file_size,
            'campaign_id': self.campaign_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ImportedFile(db.Model):
    __tablename__ = 'imported_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # excel, csv, google_sheets, google_drive
    file_url = db.Column(db.String(500), nullable=True)
    contacts_imported = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_url': self.file_url,
            'contacts_imported': self.contacts_imported,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class BotActivity(db.Model):
    __tablename__ = 'bot_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    activity_type = db.Column(db.String(50), nullable=False)  # message_received, auto_reply_sent, etc.
    contact_phone = db.Column(db.String(20))
    contact_name = db.Column(db.String(100))
    message_content = db.Column(db.Text)
    response_content = db.Column(db.Text)
    status = db.Column(db.String(20), default='success')  # success, failed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'activity_type': self.activity_type,
            'contact_phone': self.contact_phone,
            'contact_name': self.contact_name,
            'message_content': self.message_content,
            'response_content': self.response_content,
            'status': self.status,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

