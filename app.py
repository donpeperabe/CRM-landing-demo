from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
from datetime import datetime
import sqlite3
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'clave_secreta_terra_zen_2024'

# ========== CONFIGURACIÓN DE UPLOADS==========
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_images(files):
    """Guarda imágenes subidas y retorna sus rutas"""
    saved_paths = []
    
    for file in files:
        if file and file.filename != '' and allowed_file(file.filename):
            if file.content_length > MAX_FILE_SIZE:
                continue  # Saltar archivos muy grandes
                
            # Generar nombre único para evitar colisiones
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Guardar archivo
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Guardar ruta relativa para la base de datos
            saved_paths.append(f"uploads/{unique_filename}")
    
    return saved_paths

# Ruta para subir imágenes via AJAX (NUEVA RUTA)
@app.route('/upload_images', methods=['POST'])
def upload_images():
    """Endpoint para subir imágenes"""
    if not session.get('crm_logged_in'):
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        if 'images[]' not in request.files:
            return jsonify({'success': False, 'error': 'No hay archivos'})
        
        files = request.files.getlist('images[]')
        saved_paths = save_uploaded_images(files)
        
        if saved_paths:
            return jsonify({
                'success': True, 
                'paths': saved_paths,
                'message': f'{len(saved_paths)} imagen(es) subida(s) correctamente'
            })
        else:
            return jsonify({'success': False, 'error': 'No se pudieron subir las imágenes'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== CONFIGURACIÓN ==========
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ========== BASE DE DATOS ==========
def get_db_path():
    return 'terrazen.db'

def init_db():
    """Inicializa todas las tablas de la base de datos"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Tabla de propietarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS propietarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT,
                telefono TEXT,
                fecha_registro TEXT NOT NULL,
                activo INTEGER DEFAULT 1
            )
        ''')
        
        # Tabla de propiedades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS propiedades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                propietario_id INTEGER,
                titulo_es TEXT NOT NULL,
                descripcion_es TEXT,
                titulo_en TEXT NOT NULL,
                descripcion_en TEXT,
                precio TEXT,
                ubicacion TEXT,
                tipo TEXT,
                estado TEXT DEFAULT 'disponible',
                imagenes TEXT,
                whatsapp TEXT,
                fecha_creacion TEXT NOT NULL,
                activo INTEGER DEFAULT 1,
                FOREIGN KEY (propietario_id) REFERENCES propietarios (id)
            )
        ''')
        
        # Tabla de prospectos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT,
                telefono TEXT NOT NULL,
                fuente TEXT,
                fecha TEXT NOT NULL,
                propiedad TEXT,
                propiedad_id INTEGER,
                idioma TEXT
            )
        ''')
        
        # Tabla de usuarios CRM
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios_crm (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre TEXT NOT NULL,
                fecha_registro TEXT NOT NULL,
                activo INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"❌ Error inicializando BD: {e}")

def create_default_crm_user():
    """Crea usuario por defecto si no existe"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM usuarios_crm")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute('''
                INSERT INTO usuarios_crm (username, password_hash, nombre, fecha_registro)
                VALUES (?, ?, ?, ?)
            ''', (
                'admin',
                'admin123',
                'Administrador Principal',
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            print("✅ Usuario CRM por defecto creado: admin/admin123")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error creando usuario por defecto: {e}")

# ========== FUNCIONES DE BASE DE DATOS ==========
def get_all_propietarios():
    """Obtiene todos los propietarios activos"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM propietarios WHERE activo = 1 ORDER BY nombre')
        rows = cursor.fetchall()
        
        propietarios = []
        for row in rows:
            propietarios.append({
                'id': row[0],
                'nombre': row[1],
                'email': row[2],
                'telefono': row[3],
                'fecha_registro': row[4]
            })
        
        conn.close()
        return propietarios
    except Exception as e:
        print(f"Error obteniendo propietarios: {e}")
        return []

def get_all_propiedades():
    """Obtiene todas las propiedades activas"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, pr.nombre as propietario_nombre 
            FROM propiedades p 
            LEFT JOIN propietarios pr ON p.propietario_id = pr.id 
            WHERE p.activo = 1
            ORDER BY p.fecha_creacion DESC
        ''')
        rows = cursor.fetchall()
        
        propiedades = []
        for row in rows:
            imagenes = json.loads(row[10]) if row[10] else []
            
            propiedades.append({
                'id': row[0],
                'propietario_id': row[1],
                'titulo_es': row[2],
                'descripcion_es': row[3],
                'titulo_en': row[4],
                'descripcion_en': row[5],
                'precio': row[6],
                'ubicacion': row[7],
                'tipo': row[8],
                'estado': row[9],
                'imagenes': imagenes,
                'whatsapp': row[11],
                'fecha_creacion': row[12],
                'propietario_nombre': row[14]
            })
        
        conn.close()
        return propiedades
    except Exception as e:
        print(f"Error obteniendo propiedades: {e}")
        return []

def get_propiedad_by_id(propiedad_id):
    """Obtiene una propiedad específica por ID"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, pr.nombre as propietario_nombre 
            FROM propiedades p 
            LEFT JOIN propietarios pr ON p.propietario_id = pr.id 
            WHERE p.id = ? AND p.activo = 1
        ''', (propiedad_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        imagenes = json.loads(row[10]) if row[10] else []
        
        propiedad = {
            'id': row[0],
            'propietario_id': row[1],
            'titulo_es': row[2],
            'descripcion_es': row[3],
            'titulo_en': row[4],
            'descripcion_en': row[5],
            'precio': row[6],
            'ubicacion': row[7],
            'tipo': row[8],
            'estado': row[9],
            'imagenes': imagenes,
            'whatsapp': row[11],
            'fecha_creacion': row[12],
            'propietario_nombre': row[14]
        }
        
        conn.close()
        return propiedad
    except Exception as e:
        print(f"Error obteniendo propiedad: {e}")
        return None

def get_propiedades_by_propietario(propietario_id):
    """Obtiene todas las propiedades de un propietario específico"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM propiedades 
            WHERE propietario_id = ? AND activo = 1
            ORDER BY fecha_creacion DESC
        ''', (propietario_id,))
        rows = cursor.fetchall()
        
        propiedades = []
        for row in rows:
            imagenes = json.loads(row[10]) if row[10] else []
            
            propiedades.append({
                'id': row[0],
                'propietario_id': row[1],
                'titulo_es': row[2],
                'descripcion_es': row[3],
                'titulo_en': row[4],
                'descripcion_en': row[5],
                'precio': row[6],
                'ubicacion': row[7],
                'tipo': row[8],
                'estado': row[9],
                'imagenes': imagenes,
                'whatsapp': row[11],
                'fecha_creacion': row[12]
            })
        
        conn.close()
        return propiedades
    except Exception as e:
        print(f"Error obteniendo propiedades del propietario: {e}")
        return []

def save_propietario(propietario):
    """Guarda un nuevo propietario"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO propietarios (nombre, email, telefono, fecha_registro)
            VALUES (?, ?, ?, ?)
        ''', (
            propietario['nombre'],
            propietario.get('email', ''),
            propietario.get('telefono', ''),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        propietario_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return propietario_id
    except Exception as e:
        print(f"Error guardando propietario: {e}")
        return None

def save_propiedad(propiedad):
    """Guarda una nueva propiedad"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO propiedades (propietario_id, titulo_es, descripcion_es, titulo_en, descripcion_en, 
                                   precio, ubicacion, tipo, estado, imagenes, whatsapp, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            propiedad['propietario_id'],
            propiedad['titulo_es'],
            propiedad.get('descripcion_es', ''),
            propiedad['titulo_en'],
            propiedad.get('descripcion_en', ''),
            propiedad.get('precio', ''),
            propiedad.get('ubicacion', ''),
            propiedad.get('tipo', 'terreno'),
            propiedad.get('estado', 'disponible'),
            json.dumps(propiedad.get('imagenes', [])),
            propiedad.get('whatsapp', ''),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        propiedad_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return propiedad_id
    except Exception as e:
        print(f"Error guardando propiedad: {e}")
        return None

def update_propietario(propietario_id, datos):
    """Actualiza un propietario existente"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE propietarios 
            SET nombre = ?, email = ?, telefono = ?
            WHERE id = ? AND activo = 1
        ''', (
            datos['nombre'],
            datos.get('email', ''),
            datos.get('telefono', ''),
            propietario_id
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error actualizando propietario: {e}")
        return False

def update_propiedad(propiedad_id, datos):
    """Actualiza una propiedad existente"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE propiedades 
            SET titulo_es = ?, descripcion_es = ?, titulo_en = ?, descripcion_en = ?,
                precio = ?, ubicacion = ?, tipo = ?, estado = ?, imagenes = ?, whatsapp = ?
            WHERE id = ? AND activo = 1
        ''', (
            datos['titulo_es'],
            datos.get('descripcion_es', ''),
            datos['titulo_en'],
            datos.get('descripcion_en', ''),
            datos.get('precio', ''),
            datos.get('ubicacion', ''),
            datos.get('tipo', 'terreno'),
            datos.get('estado', 'disponible'),
            json.dumps(datos.get('imagenes', [])),
            datos.get('whatsapp', ''),
            propiedad_id
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error actualizando propiedad: {e}")
        return False

def delete_propietario(propietario_id):
    """Elimina (desactiva) un propietario"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('UPDATE propietarios SET activo = 0 WHERE id = ?', (propietario_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error eliminando propietario: {e}")
        return False

def delete_propiedad(propiedad_id):
    """Elimina (desactiva) una propiedad"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('UPDATE propiedades SET activo = 0 WHERE id = ?', (propiedad_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error eliminando propiedad: {e}")
        return False

def verify_crm_user(username, password):
    """Verifica credenciales de usuario CRM"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios_crm WHERE username = ? AND activo = 1', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[2] == password:
            return {'id': user[0], 'username': user[1], 'nombre': user[3]}
        return None
    except Exception as e:
        print(f"Error verificando usuario: {e}")
        return None

def load_prospects():
    """Carga todos los prospectos"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM prospects ORDER BY fecha DESC')
        
        prospects = []
        for row in cursor.fetchall():
            prospects.append({
                'id': row[0],
                'nombre': row[1],
                'email': row[2],
                'telefono': row[3],
                'fuente': row[4],
                'fecha': row[5],
                'propiedad': row[6],
                'propiedad_id': row[7],
                'idioma': row[8]
            })
        
        conn.close()
        return prospects
    except Exception as e:
        print(f"Error cargando prospectos: {e}")
        return []

def save_prospect(prospect):
    """Guarda un nuevo prospecto"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prospects (nombre, email, telefono, fuente, fecha, propiedad, propiedad_id, idioma)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prospect['nombre'],
            prospect.get('email', ''),
            prospect['telefono'],
            prospect.get('fuente', 'direct'),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            prospect.get('propiedad', ''),
            prospect.get('propiedad_id', ''),
            prospect.get('idioma', 'espanol')
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error guardando prospecto: {e}")
        return False

# ========== RUTAS PÚBLICAS ==========
@app.route('/')
def home():
    """Página principal - Redirige según autenticación"""
    if session.get('crm_logged_in'):
        return redirect(url_for('crm_dashboard'))
    else:
        return redirect(url_for('propiedades_list'))

@app.route('/propiedades')
def propiedades_list():
    """Página principal con listado de todas las propiedades"""
    propiedades = get_all_propiedades()
    return render_template('propiedades_list.html', propiedades=propiedades)

# SOLO UNA DEFINICIÓN DE propiedad_detalle
@app.route('/propiedad/<int:propiedad_id>')
def propiedad_detalle(propiedad_id):
    """Landing page individual dinámica para cada propiedad"""
    propiedad = get_propiedad_by_id(propiedad_id)
    if not propiedad:
        return "Propiedad no encontrada", 404
    
    # Detectar idioma del navegador
    if 'language' not in session:
        browser_lang = request.accept_languages.best_match(['es', 'en'])
        session['language'] = 'espanol' if browser_lang == 'es' else 'ingles'
    
    return render_template('propiedad_landing.html', propiedad=propiedad)

@app.route('/set_language/<language>')
def set_language(language):
    if language in ['espanol', 'ingles']:
        session['language'] = language
    return redirect(request.referrer or url_for('propiedades_list'))

@app.route('/prospecto', methods=['GET', 'POST'])
def prospect_form():
    """Formulario para capturar prospectos"""
    language = session.get('language', 'espanol')
    phone = request.args.get('phone', '')
    source = request.args.get('source', 'direct')
    propiedad_id = request.args.get('propiedad_id', '')
    
    if request.method == 'POST':
        try:
            nombre = request.form['nombre']
            email = request.form.get('email', '')
            telefono = request.form['telefono']
            fuente = request.form.get('fuente', 'direct')
            propiedad_id = request.form.get('propiedad_id', '')
            
            # Obtener información de la propiedad si existe
            propiedad_info = ''
            if propiedad_id:
                propiedad_obj = get_propiedad_by_id(propiedad_id)
                if propiedad_obj:
                    propiedad_info = f"{propiedad_obj['titulo_es']} (ID: {propiedad_id})"
            
            prospecto = {
                'nombre': nombre,
                'email': email,
                'telefono': telefono,
                'fuente': fuente,
                'propiedad': propiedad_info or 'Interés general',
                'propiedad_id': propiedad_id,
                'idioma': language
            }
            
            if save_prospect(prospecto):
                return redirect(url_for('thank_you'))
            else:
                return "Error al guardar el prospecto", 500
                
        except Exception as e:
            print(f"Error procesando formulario: {e}")
            return "Error interno del servidor", 500
    
    return render_template('prospect_form.html', 
                         phone=phone, 
                         source=source, 
                         language=language,
                         propiedad_id=propiedad_id)

@app.route('/gracias')
def thank_you():
    language = session.get('language', 'espanol')
    return render_template('thank_you.html', language=language)

# ========== RUTAS CRM ==========
@app.route('/crm/login', methods=['GET', 'POST'])
def crm_login():
    """Login para el sistema CRM"""
    if session.get('crm_logged_in'):
        return redirect(url_for('crm_dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = verify_crm_user(username, password)
        if user:
            session['crm_logged_in'] = True
            session['crm_user'] = user
            return redirect(url_for('crm_dashboard'))
        else:
            return render_template('crm_login.html', error=True)
    
    return render_template('crm_login.html')

@app.route('/crm/dashboard')
def crm_dashboard():
    """Dashboard principal del CRM"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    propietarios = get_all_propietarios()
    return render_template('crm_dashboard.html', 
                         propietarios=propietarios, 
                         user=session.get('crm_user'))

@app.route('/crm/propietarios', methods=['GET', 'POST'])
def crm_propietarios():
    """Gestión de propietarios en el CRM"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    if request.method == 'POST':
        propietario = {
            'nombre': request.form['nombre'],
            'email': request.form.get('email', ''),
            'telefono': request.form.get('telefono', '')
        }
        
        propietario_id = save_propietario(propietario)
        if propietario_id:
            return redirect(url_for('crm_propietarios'))
        else:
            return "Error al guardar propietario", 500
    
    propietarios = get_all_propietarios()
    propiedades = get_all_propiedades()  
    return render_template('crm_propietarios.html', 
                         propietarios=propietarios,
                         propiedades=propiedades) 

@app.route('/crm/propietarios/nuevo', methods=['GET', 'POST'])
def crm_nuevo_propietario():
    """Formulario para agregar nuevo propietario"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    if request.method == 'POST':
        propietario = {
            'nombre': request.form['nombre'],
            'email': request.form.get('email', ''),
            'telefono': request.form.get('telefono', '')
        }
        
        propietario_id = save_propietario(propietario)
        if propietario_id:
            return redirect(url_for('crm_propietarios'))
        else:
            return "Error al guardar propietario", 500
    
    return render_template('crm_nuevo_propietario.html')

@app.route('/crm/propietarios/editar/<int:propietario_id>', methods=['GET', 'POST'])
def crm_editar_propietario(propietario_id):
    """Editar propietario existente"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    if request.method == 'POST':
        datos = {
            'nombre': request.form['nombre'],
            'email': request.form.get('email', ''),
            'telefono': request.form.get('telefono', '')
        }
        
        if update_propietario(propietario_id, datos):
            return redirect(url_for('crm_propietarios'))
        else:
            return "Error al actualizar propietario", 500
    
    propietarios = get_all_propietarios()
    propietario_actual = next((p for p in propietarios if p['id'] == propietario_id), None)
    
    if not propietario_actual:
        return "Propietario no encontrado", 404
    
    return render_template('crm_editar_propietario.html', propietario=propietario_actual)

@app.route('/crm/propietarios/eliminar/<int:propietario_id>')
def crm_eliminar_propietario(propietario_id):
    """Eliminar propietario"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    if delete_propietario(propietario_id):
        return redirect(url_for('crm_propietarios'))
    else:
        return "Error al eliminar propietario", 500

@app.route('/crm/propietarios/<int:propietario_id>')
def crm_detalle_propietario(propietario_id):
    """Ver detalle de propietario y sus propiedades"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    propietarios = get_all_propietarios()
    propietario_actual = next((p for p in propietarios if p['id'] == propietario_id), None)
    
    if not propietario_actual:
        return "Propietario no encontrado", 404
    
    propiedades_propietario = get_propiedades_by_propietario(propietario_id)
    
    return render_template('crm_detalle_propietario.html',
                         propietario=propietario_actual,
                         propiedades=propiedades_propietario)

@app.route('/crm/propiedades', methods=['GET', 'POST'])
def crm_propiedades():
    """Gestión de propiedades en el CRM"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    if request.method == 'POST':
        propiedad = {
            'propietario_id': request.form['propietario_id'],
            'titulo_es': request.form['titulo_es'],
            'descripcion_es': request.form.get('descripcion_es', ''),
            'titulo_en': request.form['titulo_en'],
            'descripcion_en': request.form.get('descripcion_en', ''),
            'precio': request.form.get('precio', ''),
            'ubicacion': request.form.get('ubicacion', ''),
            'tipo': request.form.get('tipo', 'terreno'),
            'estado': request.form.get('estado', 'disponible'),
            'whatsapp': request.form.get('whatsapp', ''),
            'imagenes': request.form.get('imagenes', '').split(',')
        }
        
        propiedad_id = save_propiedad(propiedad)
        if propiedad_id:
            return redirect(url_for('crm_propiedades'))
        else:
            return "Error al guardar propiedad", 500
    
    propietarios = get_all_propietarios()
    propiedades = get_all_propiedades()
    return render_template('crm_propiedades.html', 
                         propietarios=propietarios, 
                         propiedades=propiedades)

@app.route('/crm/propiedades/nueva', methods=['GET', 'POST'])
def crm_nueva_propiedad():
    """Formulario para agregar nueva propiedad"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    propietarios = get_all_propietarios()

    # 🔒 Bloquea acceso si no hay propietarios registrados
    if not propietarios:
        # Opción 1: Redirigir con mensaje
        session['no_owner_warning'] = "Debes registrar al menos un propietario antes de agregar propiedades."
        return redirect(url_for('crm_propietarios'))
    
    if request.method == 'POST':
        propiedad = {
            'propietario_id': request.form['propietario_id'],
            'titulo_es': request.form['titulo_es'],
            'descripcion_es': request.form.get('descripcion_es', ''),
            'titulo_en': request.form['titulo_en'],
            'descripcion_en': request.form.get('descripcion_en', ''),
            'precio': request.form.get('precio', ''),
            'ubicacion': request.form.get('ubicacion', ''),
            'tipo': request.form.get('tipo', 'terreno'),
            'estado': request.form.get('estado', 'disponible'),
            'whatsapp': request.form.get('whatsapp', ''),
            'imagenes': request.form.get('imagenes', '').split(',')
        }
        
        propiedad_id = save_propiedad(propiedad)
        if propiedad_id:
            return redirect(url_for('crm_propiedades'))
        else:
            return "Error al guardar propiedad", 500
    
    return render_template('crm_nueva_propiedad.html', propietarios=propietarios)


@app.route('/crm/propiedades/editar/<int:propiedad_id>', methods=['GET', 'POST'])
def crm_editar_propiedad(propiedad_id):
    """Editar propiedad existente"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    if request.method == 'POST':
        datos = {
            'propietario_id': request.form['propietario_id'],
            'titulo_es': request.form['titulo_es'],
            'descripcion_es': request.form.get('descripcion_es', ''),
            'titulo_en': request.form['titulo_en'],
            'descripcion_en': request.form.get('descripcion_en', ''),
            'precio': request.form.get('precio', ''),
            'ubicacion': request.form.get('ubicacion', ''),
            'tipo': request.form.get('tipo', 'terreno'),
            'estado': request.form.get('estado', 'disponible'),
            'whatsapp': request.form.get('whatsapp', ''),
            'imagenes': request.form.get('imagenes', '').split(',')
        }
        
        if update_propiedad(propiedad_id, datos):
            return redirect(url_for('crm_propiedades'))
        else:
            return "Error al actualizar propiedad", 500
    
    propiedades = get_all_propiedades()
    propiedad_actual = next((p for p in propiedades if p['id'] == propiedad_id), None)
    
    if not propiedad_actual:
        return "Propiedad no encontrada", 404
    
    propietarios = get_all_propietarios()
    return render_template('crm_editar_propiedad.html', 
                         propiedad=propiedad_actual,
                         propietarios=propietarios)

@app.route('/crm/propiedades/eliminar/<int:propiedad_id>')
def crm_eliminar_propiedad(propiedad_id):
    """Eliminar propiedad"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    if delete_propiedad(propiedad_id):
        return redirect(url_for('crm_propiedades'))
    else:
        return "Error al eliminar propiedad", 500

@app.route('/crm/logout')
def crm_logout():
    """Logout del CRM"""
    session.pop('crm_logged_in', None)
    session.pop('crm_user', None)
    return redirect(url_for('home'))

# ========== RUTAS DE PROSPECTOS (SIMPLIFICADO) ==========
@app.route('/prospectos')
def admin_prospectos():
    """Vista de prospectos - solo para usuarios CRM logueados"""
    if not session.get('crm_logged_in'):
        return redirect(url_for('crm_login'))
    
    prospects = load_prospects()
    return render_template('admin_prospectos.html', prospects=prospects)

# ========== INICIALIZACIÓN ==========
init_db()
create_default_crm_user()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
