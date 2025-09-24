from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Contact, ImportedFile
from datetime import datetime
import json
import csv
import io
import openpyxl
from werkzeug.utils import secure_filename
import os

contacts_bp = Blueprint('contacts', __name__)

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

@contacts_bp.route('/', methods=['GET'])
def get_contacts():
    """Obtener lista de contactos del usuario con filtros y paginación"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        # Parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        tags = request.args.get('tags', '').strip()
        
        # Construir consulta
        query = Contact.query.filter_by(user_id=user.id)
        
        # Filtrar por búsqueda
        if search:
            query = query.filter(
                db.or_(
                    Contact.name.ilike(f'%{search}%'),
                    Contact.phone.ilike(f'%{search}%'),
                    Contact.email.ilike(f'%{search}%')
                )
            )
        
        # Filtrar por estado
        if status:
            query = query.filter_by(status=status)
        
        # Filtrar por etiquetas
        if tags:
            query = query.filter(Contact.tags.ilike(f'%{tags}%'))
        
        # Ordenar por fecha de creación (más recientes primero)
        query = query.order_by(Contact.created_at.desc())
        
        # Paginación
        contacts = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': contacts.total,
                'pages': contacts.pages,
                'has_next': contacts.has_next,
                'has_prev': contacts.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/', methods=['POST'])
def create_contact():
    """Crear un nuevo contacto"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        # Validar datos requeridos
        if not data.get('name') or not data.get('phone'):
            return jsonify({'error': 'Nombre y teléfono son requeridos'}), 400
        
        # Verificar si ya existe un contacto con el mismo teléfono
        existing_contact = Contact.query.filter_by(
            user_id=user.id, 
            phone=data['phone'].strip()
        ).first()
        
        if existing_contact:
            return jsonify({'error': 'Ya existe un contacto con este teléfono'}), 409
        
        # Crear nuevo contacto
        contact = Contact(
            user_id=user.id,
            name=data['name'].strip(),
            phone=data['phone'].strip(),
            email=data.get('email', '').strip() or None,
            tags=json.dumps(data.get('tags', [])) if data.get('tags') else None,
            notes=data.get('notes', '').strip() or None,
            status=data.get('status', 'activo')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'message': 'Contacto creado exitosamente',
            'contact': contact.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Obtener un contacto específico"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        contact = Contact.query.filter_by(id=contact_id, user_id=user.id).first()
        if not contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        return jsonify({
            'contact': contact.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Actualizar un contacto"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        contact = Contact.query.filter_by(id=contact_id, user_id=user.id).first()
        if not contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        # Actualizar campos
        if 'name' in data:
            contact.name = data['name'].strip()
        if 'phone' in data:
            # Verificar si el nuevo teléfono ya existe en otro contacto
            if data['phone'].strip() != contact.phone:
                existing_contact = Contact.query.filter_by(
                    user_id=user.id, 
                    phone=data['phone'].strip()
                ).first()
                if existing_contact:
                    return jsonify({'error': 'Ya existe un contacto con este teléfono'}), 409
            contact.phone = data['phone'].strip()
        
        if 'email' in data:
            contact.email = data['email'].strip() or None
        if 'tags' in data:
            contact.tags = json.dumps(data['tags']) if data['tags'] else None
        if 'notes' in data:
            contact.notes = data['notes'].strip() or None
        if 'status' in data:
            contact.status = data['status']
        
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Contacto actualizado exitosamente',
            'contact': contact.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Eliminar un contacto"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        contact = Contact.query.filter_by(id=contact_id, user_id=user.id).first()
        if not contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({
            'message': 'Contacto eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/bulk-delete', methods=['POST'])
def bulk_delete_contacts():
    """Eliminar múltiples contactos"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if not data or not data.get('contact_ids'):
            return jsonify({'error': 'IDs de contactos requeridos'}), 400
        
        contact_ids = data['contact_ids']
        if not isinstance(contact_ids, list):
            return jsonify({'error': 'contact_ids debe ser una lista'}), 400
        
        # Eliminar contactos
        deleted_count = Contact.query.filter(
            Contact.id.in_(contact_ids),
            Contact.user_id == user.id
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{deleted_count} contactos eliminados exitosamente',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/import/csv', methods=['POST'])
def import_csv():
    """Importar contactos desde archivo CSV"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        if 'file' not in request.files:
            return jsonify({'error': 'No se proporcionó archivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Solo se permiten archivos CSV'}), 400
        
        # Leer archivo CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_input, start=2):
            try:
                name = row.get('name', '').strip()
                phone = row.get('phone', '').strip()
                email = row.get('email', '').strip()
                tags = row.get('tags', '').strip()
                
                if not name or not phone:
                    errors.append(f'Fila {row_num}: Nombre y teléfono son requeridos')
                    continue
                
                # Verificar si ya existe
                existing_contact = Contact.query.filter_by(
                    user_id=user.id, 
                    phone=phone
                ).first()
                
                if existing_contact:
                    errors.append(f'Fila {row_num}: Ya existe contacto con teléfono {phone}')
                    continue
                
                # Crear contacto
                contact = Contact(
                    user_id=user.id,
                    name=name,
                    phone=phone,
                    email=email or None,
                    tags=json.dumps(tags.split(',')) if tags else None
                )
                
                db.session.add(contact)
                imported_count += 1
                
            except Exception as e:
                errors.append(f'Fila {row_num}: {str(e)}')
        
        # Registrar importación
        imported_file = ImportedFile(
            user_id=user.id,
            filename=secure_filename(file.filename),
            file_type='csv',
            contacts_imported=imported_count,
            status='completed' if imported_count > 0 else 'failed',
            error_message='; '.join(errors) if errors else None,
            completed_at=datetime.utcnow()
        )
        
        db.session.add(imported_file)
        db.session.commit()
        
        return jsonify({
            'message': f'Importación completada: {imported_count} contactos importados',
            'imported_count': imported_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/import/excel', methods=['POST'])
def import_excel():
    """Importar contactos desde archivo Excel"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        if 'file' not in request.files:
            return jsonify({'error': 'No se proporcionó archivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Solo se permiten archivos Excel (.xlsx, .xls)'}), 400
        
        # Leer archivo Excel
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        
        imported_count = 0
        errors = []
        
        # Obtener headers de la primera fila
        headers = [cell.value for cell in sheet[1]]
        
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            try:
                row_dict = dict(zip(headers, row))
                
                name = str(row_dict.get('name', '') or row_dict.get('nombre', '')).strip()
                phone = str(row_dict.get('phone', '') or row_dict.get('telefono', '')).strip()
                email = str(row_dict.get('email', '') or row_dict.get('correo', '')).strip()
                tags = str(row_dict.get('tags', '') or row_dict.get('etiquetas', '')).strip()
                
                if not name or not phone:
                    errors.append(f'Fila {row_num}: Nombre y teléfono son requeridos')
                    continue
                
                # Verificar si ya existe
                existing_contact = Contact.query.filter_by(
                    user_id=user.id, 
                    phone=phone
                ).first()
                
                if existing_contact:
                    errors.append(f'Fila {row_num}: Ya existe contacto con teléfono {phone}')
                    continue
                
                # Crear contacto
                contact = Contact(
                    user_id=user.id,
                    name=name,
                    phone=phone,
                    email=email or None,
                    tags=json.dumps(tags.split(',')) if tags else None
                )
                
                db.session.add(contact)
                imported_count += 1
                
            except Exception as e:
                errors.append(f'Fila {row_num}: {str(e)}')
        
        # Registrar importación
        imported_file = ImportedFile(
            user_id=user.id,
            filename=secure_filename(file.filename),
            file_type='excel',
            contacts_imported=imported_count,
            status='completed' if imported_count > 0 else 'failed',
            error_message='; '.join(errors) if errors else None,
            completed_at=datetime.utcnow()
        )
        
        db.session.add(imported_file)
        db.session.commit()
        
        return jsonify({
            'message': f'Importación completada: {imported_count} contactos importados',
            'imported_count': imported_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/import/sheets', methods=['POST'])
def import_google_sheets():
    """Importar contactos desde Google Sheets"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if not data or not data.get('sheet_url'):
            return jsonify({'error': 'URL de Google Sheets requerida'}), 400
        
        # Registrar intento de importación
        imported_file = ImportedFile(
            user_id=user.id,
            filename='Google Sheets Import',
            file_type='google_sheets',
            file_url=data['sheet_url'],
            status='processing'
        )
        
        db.session.add(imported_file)
        db.session.commit()
        
        # TODO: Implementar integración real con Google Sheets API
        # Por ahora, simular la importación
        
        return jsonify({
            'message': 'Importación de Google Sheets iniciada',
            'import_id': imported_file.id,
            'status': 'processing'
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/import/drive', methods=['POST'])
def import_google_drive():
    """Importar contactos desde Google Drive"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        if not data or not data.get('file_id'):
            return jsonify({'error': 'ID de archivo de Google Drive requerido'}), 400
        
        # Registrar intento de importación
        imported_file = ImportedFile(
            user_id=user.id,
            filename='Google Drive Import',
            file_type='google_drive',
            file_url=f"https://drive.google.com/file/d/{data['file_id']}",
            status='processing'
        )
        
        db.session.add(imported_file)
        db.session.commit()
        
        # TODO: Implementar integración real con Google Drive API
        # Por ahora, simular la importación
        
        return jsonify({
            'message': 'Importación de Google Drive iniciada',
            'import_id': imported_file.id,
            'status': 'processing'
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/import/history', methods=['GET'])
def get_import_history():
    """Obtener historial de importaciones"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        imports = ImportedFile.query.filter_by(user_id=user.id)\
                                   .order_by(ImportedFile.created_at.desc())\
                                   .limit(20).all()
        
        return jsonify({
            'imports': [imported_file.to_dict() for imported_file in imports]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@contacts_bp.route('/stats', methods=['GET'])
def get_contacts_stats():
    """Obtener estadísticas de contactos"""
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'No autorizado'}), 401
        
        total_contacts = Contact.query.filter_by(user_id=user.id).count()
        active_contacts = Contact.query.filter_by(user_id=user.id, status='activo').count()
        inactive_contacts = Contact.query.filter_by(user_id=user.id, status='inactivo').count()
        
        # Contactos agregados en los últimos 30 días
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_contacts = Contact.query.filter(
            Contact.user_id == user.id,
            Contact.created_at >= thirty_days_ago
        ).count()
        
        return jsonify({
            'stats': {
                'total_contacts': total_contacts,
                'active_contacts': active_contacts,
                'inactive_contacts': inactive_contacts,
                'recent_contacts': recent_contacts
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

