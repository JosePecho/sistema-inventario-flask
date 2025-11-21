from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from database import SistemaInventario
import sqlite3

app = Flask(__name__)
app.secret_key = 'clave_secreta_inventario_2024_leo_sistema_multiusuario'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

sistema = SistemaInventario()

# Clase User para Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.nombre = user_data['nombre']
        self.es_admin = user_data['es_admin']

@login_manager.user_loader
def load_user(user_id):
    user_data = sistema.obtener_usuario_por_id(user_id)
    if user_data:
        return User(user_data)
    return None

# ================= REDIRECCIÓN FORZADA =================
@app.before_request
def force_login():
    # Forzar logout en cada inicio para asegurar que pida login
    if request.endpoint != 'login' and request.endpoint != 'register' and request.endpoint != 'static' and not current_user.is_authenticated:
        return redirect(url_for('login'))

@app.route('/')
def root():
    """Redirige siempre al login"""
    return redirect(url_for('login'))

# ================= AUTENTICACIÓN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Forzar cerrar cualquier sesión previa
    if not current_user.is_authenticated:
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
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validaciones
            if not nombre or not username or not password:
                flash('❌ Todos los campos obligatorios deben ser llenados', 'error')
            elif password != confirm_password:
                flash('❌ Las contraseñas no coinciden', 'error')
            elif len(password) < 6:
                flash('❌ La contraseña debe tener al menos 6 caracteres', 'error')
            else:
                # Crear nuevo usuario
                if sistema.agregar_usuario(username, password, nombre, email, es_admin=True):
                    flash('✅ ¡Cuenta creada exitosamente! Ahora puedes iniciar sesión', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('❌ El nombre de usuario ya existe', 'error')
                    
        except Exception as e:
            flash('❌ Error al crear la cuenta', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('👋 ¡Sesión cerrada correctamente!', 'info')
    return redirect(url_for('login'))

@app.route('/mi_cuenta')
@login_required
def mi_cuenta():
    """Página de gestión de cuenta del usuario"""
    return render_template('mi_cuenta.html', usuario=current_user)

# ================= RUTAS PRINCIPALES =================
@app.route('/dashboard')
@login_required
def dashboard():
    """Página principal del dashboard"""
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
    """Lista todos los productos"""
    try:
        productos_lista = sistema.obtener_productos(current_user.id)
        return render_template('productos.html', productos=productos_lista)
    except Exception as e:
        flash('Error al cargar los productos', 'error')
        return render_template('productos.html', productos=[])

@app.route('/agregar_producto', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    """Agregar nuevo producto"""
    if request.method == 'POST':
        try:
            codigo = request.form['codigo'].strip()
            nombre = request.form['nombre'].strip()
            descripcion = request.form.get('descripcion', '').strip()
            categoria = request.form.get('categoria', '').strip()
            precio_compra = float(request.form['precio_compra'])
            precio_venta = float(request.form['precio_venta'])
            stock_actual = int(request.form['stock_actual'])
            stock_minimo = int(request.form['stock_minimo'])
            
            # Validación básica
            if precio_venta <= precio_compra:
                flash('❌ El precio de venta debe ser mayor al precio de compra', 'error')
            elif stock_actual < 0 or stock_minimo < 0:
                flash('❌ El stock no puede ser negativo', 'error')
            elif sistema.agregar_producto(current_user.id, codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock_actual, stock_minimo):
                flash('✅ Producto agregado correctamente', 'success')
                return redirect(url_for('productos'))
            else:
                flash('❌ Error: El código del producto ya existe', 'error')
        except ValueError:
            flash('❌ Error: Verifica que los precios y stock sean números válidos', 'error')
        except Exception as e:
            flash('❌ Error al agregar producto', 'error')
    
    return render_template('agregar_producto.html')

@app.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    """Editar producto existente"""
    try:
        producto = sistema.obtener_producto_por_id(current_user.id, producto_id)
        
        if not producto:
            flash('❌ Producto no encontrado', 'error')
            return redirect(url_for('productos'))
        
        if request.method == 'POST':
            codigo = request.form['codigo'].strip()
            nombre = request.form['nombre'].strip()
            descripcion = request.form.get('descripcion', '').strip()
            categoria = request.form.get('categoria', '').strip()
            precio_compra = float(request.form['precio_compra'])
            precio_venta = float(request.form['precio_venta'])
            stock_actual = int(request.form['stock_actual'])
            stock_minimo = int(request.form['stock_minimo'])
            
            # Validación
            if precio_venta <= precio_compra:
                flash('❌ El precio de venta debe ser mayor al precio de compra', 'error')
            elif stock_actual < 0 or stock_minimo < 0:
                flash('❌ El stock no puede ser negativo', 'error')
            elif sistema.actualizar_producto(current_user.id, producto_id, codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock_actual, stock_minimo):
                flash('✅ Producto actualizado correctamente', 'success')
                return redirect(url_for('productos'))
            else:
                flash('❌ Error al actualizar producto', 'error')
        
        return render_template('editar_producto.html', producto=producto)
    
    except Exception as e:
        flash('❌ Error al cargar el producto', 'error')
        return redirect(url_for('productos'))

@app.route('/eliminar_producto/<int:producto_id>')
@login_required
def eliminar_producto(producto_id):
    """Eliminar producto"""
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
    """Mostrar movimientos de inventario"""
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
    """Agregar movimiento (entrada/salida)"""
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
    """Página de consultas y búsqueda"""
    try:
        query = request.args.get('q', '').strip()
        categoria = request.args.get('categoria', '')
        
        productos_lista = sistema.buscar_productos(current_user.id, query, categoria)
        categorias = sistema.obtener_categorias(current_user.id)
        
        return render_template('consultas.html', 
                             productos=productos_lista, 
                             categorias=categorias, 
                             query=query, 
                             categoria_seleccionada=categoria)
    except Exception as e:
        flash('Error al realizar la búsqueda', 'error')
        return render_template('consultas.html', productos=[], categorias=[], query='', categoria_seleccionada='')

@app.route('/reportes')
@login_required
def reportes():
    """Página de reportes"""
    try:
        reporte_stock = sistema.obtener_reporte_stock(current_user.id)
        reporte_movimientos = sistema.obtener_reporte_movimientos(current_user.id)
        return render_template('reportes.html', 
                             reporte_stock=reporte_stock, 
                             reporte_movimientos=reporte_movimientos)
    except Exception as e:
        flash('Error al generar reportes', 'error')
        return render_template('reportes.html', reporte_stock=[], reporte_movimientos=[])

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
    print("👥 Sistema: Cada usuario tiene su inventario privado")
    print("💡 Crea tu cuenta gratuita en el formulario de login")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )