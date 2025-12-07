from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from database import SistemaInventario
import sqlite3
import datetime
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_inventario_2024_leo_sistema_multiusuario'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

sistema = SistemaInventario()

# Clase User para Flask-Login - AGREGADO CAMPO foto_perfil
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.nombre = user_data['nombre']
        self.es_admin = user_data['es_admin']
        self.foto_perfil = user_data.get('foto_perfil')  # Nuevo campo

@login_manager.user_loader
def load_user(user_id):
    user_data = sistema.obtener_usuario_por_id(user_id)
    if user_data:
        return User(user_data)
    return None

# ================= MIDDLEWARE SIMPLIFICADO =================
@app.before_request
def asegurar_tablas_usuario():
    if current_user.is_authenticated and request.endpoint not in ['login', 'register', 'static', 'logout']:
        sistema.asegurar_tablas_usuario(current_user.id)
        sistema.actualizar_estructura_tablas(current_user.id)

# ================= REDIRECCIÓN FORZADA =================
@app.before_request
def force_login():
    if request.endpoint != 'login' and request.endpoint != 'register' and request.endpoint != 'static' and not current_user.is_authenticated:
        return redirect(url_for('login'))

@app.route('/')
def root():
    return redirect(url_for('login'))

# ================= AUTENTICACIÓN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        logout_user()
        session.clear()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            usuario = sistema.verificar_password(username, password)
            if usuario:
                user_obj = User(usuario)
                login_user(user_obj)
                flash('✅ ¡Inicio de sesión exitoso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('❌ Usuario o contraseña incorrectos', 'error')
        else:
            flash('❌ Por favor ingresa usuario y contraseña', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        logout_user()
        session.clear()
    
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not nombre or not username or not password:
                flash('❌ Todos los campos obligatorios deben ser llenados', 'error')
            elif password != confirm_password:
                flash('❌ Las contraseñas no coinciden', 'error')
            elif len(password) < 6:
                flash('❌ La contraseña debe tener al menos 6 caracteres', 'error')
            else:
                exito, mensaje = sistema.agregar_usuario(username, password, nombre, email, es_admin=True)
                
                if exito:
                    flash(f'✅ {mensaje}', 'success')
                    return redirect(url_for('login'))
                else:
                    flash(f'❌ {mensaje}', 'error')
                    
        except Exception as e:
            flash(f'❌ Error al crear la cuenta: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('👋 ¡Sesión cerrada correctamente!', 'info')
    return redirect(url_for('login'))

# ================= NUEVA RUTA PARA SUBIR FOTO DE PERFIL =================
@app.route('/actualizar_foto_perfil', methods=['POST'])
@login_required
def actualizar_foto_perfil():
    """Actualizar la foto de perfil del usuario"""
    try:
        if 'foto_perfil' not in request.files:
            flash('❌ No se seleccionó ninguna foto', 'error')
            return redirect(url_for('mi_cuenta'))
        
        foto = request.files['foto_perfil']
        
        # Verificar que se subió un archivo
        if foto.filename == '':
            flash('❌ No se seleccionó ningún archivo', 'error')
            return redirect(url_for('mi_cuenta'))
        
        # Verificar extensión del archivo
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if '.' in foto.filename:
            extension = foto.filename.rsplit('.', 1)[1].lower()
            if extension not in allowed_extensions:
                flash('❌ Formato no permitido. Use PNG, JPG o GIF', 'error')
                return redirect(url_for('mi_cuenta'))
        
        # Eliminar foto anterior si existe
        sistema.eliminar_foto_antigua(current_user.id)
        
        # Guardar nueva foto
        ruta_foto = sistema.guardar_foto_archivo(current_user.id, foto)
        
        if ruta_foto:
            flash('✅ Foto de perfil actualizada correctamente', 'success')
        else:
            flash('❌ Error al guardar la foto', 'error')
        
        return redirect(url_for('mi_cuenta'))
        
    except Exception as e:
        print(f"Error en actualizar_foto_perfil: {e}")
        flash('❌ Error al actualizar la foto de perfil', 'error')
        return redirect(url_for('mi_cuenta'))

@app.route('/eliminar_foto_perfil', methods=['POST'])
@login_required
def eliminar_foto_perfil():
    """Eliminar la foto de perfil del usuario"""
    try:
        # Eliminar foto del sistema de archivos
        sistema.eliminar_foto_antigua(current_user.id)
        
        # Limpiar campo en la base de datos
        sistema.actualizar_foto_perfil(current_user.id, None)
        
        flash('✅ Foto de perfil eliminada correctamente', 'success')
        return redirect(url_for('mi_cuenta'))
        
    except Exception as e:
        print(f"Error en eliminar_foto_perfil: {e}")
        flash('❌ Error al eliminar la foto de perfil', 'error')
        return redirect(url_for('mi_cuenta'))

# ================= RUTA MI CUENTA MODIFICADA =================
@app.route('/mi_cuenta')
@login_required
def mi_cuenta():
    """Página de gestión de cuenta del usuario - AHORA CON FOTO"""
    try:
        # Obtener datos actualizados del usuario
        usuario_data = sistema.obtener_usuario_por_id(current_user.id)
        if usuario_data:
            # Actualizar el objeto current_user con la foto de perfil
            current_user.foto_perfil = usuario_data.get('foto_perfil')
        
        return render_template('mi_cuenta.html', usuario=current_user)
    except Exception as e:
        print(f"Error en mi_cuenta: {e}")
        flash('❌ Error al cargar información de la cuenta', 'error')
        return redirect(url_for('dashboard'))

# ================= RUTAS PRINCIPALES =================
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        stats = sistema.obtener_estadisticas(current_user.id)
        productos_bajos = sistema.obtener_productos_stock_bajo(current_user.id)
        return render_template('dashboard.html', stats=stats, productos_bajos=productos_bajos)
    except Exception as e:
        flash('Error al cargar el dashboard', 'error')
        stats_default = {
            'total_productos': 0,
            'total_movimientos': 0,
            'productos_bajos': 0,
            'valor_total': 0,
            'valor_inventario': 0,
            'stock_bajo': 0,
            'movimientos_hoy': 0
        }
        return render_template('dashboard.html', stats=stats_default, productos_bajos=[])

@app.route('/productos')
@login_required
def productos():
    try:
        productos_lista = sistema.obtener_productos(current_user.id)
        return render_template('productos.html', productos=productos_lista)
    except Exception as e:
        flash('Error al cargar los productos', 'error')
        return render_template('productos.html', productos=[])

@app.route('/agregar_producto', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    if request.method == 'POST':
        try:
            codigo = request.form['codigo'].strip()
            nombre = request.form['nombre'].strip()
            descripcion = request.form.get('descripcion', '').strip()
            ubicacion = request.form.get('ubicacion', '').strip()
            modelo = request.form.get('modelo', '').strip()
            marca = request.form.get('marca', '').strip()
            estado = request.form.get('estado', '').strip()
            año_adquisicion = request.form.get('año_adquisicion', '').strip()
            precio_compra = float(request.form['precio_compra'])
            stock_actual = int(request.form['stock_actual'])
            stock_minimo = int(request.form['stock_minimo'])
            
            año_int = int(año_adquisicion) if año_adquisicion and año_adquisicion.isdigit() else None
            
            if stock_actual < 0 or stock_minimo < 0:
                flash('❌ El stock no puede ser negativo', 'error')
            elif not codigo or not nombre:
                flash('❌ Código y nombre son obligatorios', 'error')
            else:
                exito, mensaje = sistema.agregar_producto(
                    current_user.id, codigo, nombre, descripcion, ubicacion, 
                    modelo, marca, estado, año_int, precio_compra, stock_actual, stock_minimo
                )
                
                if exito:
                    flash(f'✅ {mensaje}', 'success')
                    return redirect(url_for('productos'))
                else:
                    flash(f'❌ {mensaje}', 'error')
                
        except ValueError:
            flash('❌ Error: Verifica que los precios y stock sean números válidos', 'error')
        except Exception as e:
            flash(f'❌ Error al agregar producto: {str(e)}', 'error')
    
    return render_template('agregar_producto.html')

@app.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    try:
        producto = sistema.obtener_producto_por_id(current_user.id, producto_id)
        
        if not producto:
            flash('❌ Producto no encontrado', 'error')
            return redirect(url_for('productos'))
        
        if request.method == 'POST':
            codigo = request.form['codigo'].strip()
            nombre = request.form['nombre'].strip()
            descripcion = request.form.get('descripcion', '').strip()
            ubicacion = request.form.get('ubicacion', '').strip()
            modelo = request.form.get('modelo', '').strip()
            marca = request.form.get('marca', '').strip()
            estado = request.form.get('estado', '').strip()
            año_adquisicion = request.form.get('año_adquisicion', '').strip()
            precio_compra = float(request.form['precio_compra'])
            stock_actual = int(request.form['stock_actual'])
            stock_minimo = int(request.form['stock_minimo'])
            
            año_int = int(año_adquisicion) if año_adquisicion and año_adquisicion.isdigit() else None
            
            if stock_actual < 0 or stock_minimo < 0:
                flash('❌ El stock no puede ser negativo', 'error')
            else:
                exito, mensaje = sistema.actualizar_producto(
                    current_user.id, producto_id, codigo, nombre, descripcion, 
                    ubicacion, modelo, marca, estado, año_int, precio_compra, 
                    stock_actual, stock_minimo
                )
                
                if exito:
                    flash(f'✅ {mensaje}', 'success')
                    return redirect(url_for('productos'))
                else:
                    flash(f'❌ {mensaje}', 'error')
        
        return render_template('editar_producto.html', producto=producto)
    
    except Exception as e:
        flash('❌ Error al cargar el producto', 'error')
        return redirect(url_for('productos'))

@app.route('/eliminar_producto/<int:producto_id>')
@login_required
def eliminar_producto(producto_id):
    try:
        if sistema.eliminar_producto(current_user.id, producto_id):
            flash('✅ Producto eliminado correctamente', 'success')
        else:
            flash('❌ Error al eliminar producto', 'error')
    except Exception as e:
        flash('❌ Error al eliminar producto', 'error')
    
    return redirect(url_for('productos'))

@app.route('/movimientos')
@login_required
def movimientos():
    try:
        movimientos_lista = sistema.obtener_movimientos(current_user.id)
        productos_lista = sistema.obtener_productos(current_user.id)
        return render_template('movimientos.html', movimientos=movimientos_lista, productos=productos_lista)
    except Exception as e:
        flash('Error al cargar movimientos', 'error')
        return render_template('movimientos.html', movimientos=[], productos=[])

@app.route('/agregar_movimiento', methods=['POST'])
@login_required
def agregar_movimiento():
    try:
        producto_id = int(request.form['producto_id'])
        tipo = request.form['tipo']
        cantidad = int(request.form['cantidad'])
        motivo = request.form.get('motivo', '').strip()
        
        if cantidad <= 0:
            flash('❌ La cantidad debe ser mayor a 0', 'error')
        elif sistema.agregar_movimiento(current_user.id, producto_id, tipo, cantidad, motivo):
            flash('✅ Movimiento registrado correctamente', 'success')
        else:
            flash('❌ Error al registrar movimiento', 'error')
    
    except ValueError:
        flash('❌ Error: Verifica que los datos sean válidos', 'error')
    except Exception as e:
        flash('❌ Error al registrar movimiento', 'error')
    
    return redirect(url_for('movimientos'))

@app.route('/consultas')
@login_required
def consultas():
    try:
        query = request.args.get('q', '').strip()
        ubicacion = request.args.get('ubicacion', '')
        
        productos_lista = sistema.buscar_productos(current_user.id, query, ubicacion)
        ubicaciones = sistema.obtener_ubicaciones(current_user.id)
        
        return render_template('consultas.html', 
                             productos=productos_lista, 
                             ubicaciones=ubicaciones,
                             query=query, 
                             ubicacion_seleccionada=ubicacion)
    except Exception as e:
        flash('Error al realizar la búsqueda', 'error')
        return render_template('consultas.html', productos=[], ubicaciones=[], query='', ubicacion_seleccionada='')

@app.route('/reportes')
@login_required
def reportes():
    try:
        reporte_stock = sistema.obtener_reporte_stock(current_user.id)
        reporte_movimientos = sistema.obtener_reporte_movimientos(current_user.id)
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        return render_template('reportes.html', 
                             reporte_stock=reporte_stock, 
                             reporte_movimientos=reporte_movimientos,
                             fecha_actual=fecha_actual)
    except Exception as e:
        flash('Error al generar reportes', 'error')
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template('reportes.html', 
                             reporte_stock=[], 
                             reporte_movimientos=[],
                             fecha_actual=fecha_actual)

# ================= MANEJO DE ERRORES =================
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template('error.html', mensaje='Página no encontrada'), 404

@app.errorhandler(500)
def error_servidor(error):
    return render_template('error.html', mensaje='Error interno del servidor'), 500

# ================= INICIALIZACIÓN =================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SISTEMA DE INVENTARIO MULTIUSUARIO INICIADO")
    print("📍 URL: http://localhost:5000/login")
    print("👤 Ahora con: Foto de perfil personalizable")
    print("📸 Sube tu foto en: Mi Cuenta → Subir Foto")
    print("=" * 60)
    
    # Crear carpeta para fotos de perfil si no existe
    if not os.path.exists('static/profile_photos'):
        os.makedirs('static/profile_photos')
        print("📁 Carpeta para fotos de perfil creada")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,  # Cambia a False en producción
        threaded=True
    )