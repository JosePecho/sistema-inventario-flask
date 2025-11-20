from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from database import SistemaInventario
import sqlite3  # ← IMPORT AGREGADO

app = Flask(__name__)
app.secret_key = 'clave_secreta_inventario_2024_mas_segura'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'

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
    conn = sqlite3.connect(sistema.db_name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(dict(user_data))
    return None

# ================= RUTAS DE AUTENTICACIÓN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        usuario = sistema.verificar_password(username, password)
        if usuario:
            user_obj = User(usuario)
            login_user(user_obj)
            flash(f'✅ Bienvenido, {usuario["nombre"]}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('❌ Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('👋 Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

# ================= RUTAS PRINCIPALES PROTEGIDAS =================
@app.route('/')
@login_required
def dashboard():
    """Página principal del dashboard"""
    try:
        stats = sistema.obtener_estadisticas()
        productos_bajos = sistema.obtener_productos_stock_bajo()
        return render_template('dashboard.html', stats=stats, productos_bajos=productos_bajos)
    except Exception as e:
        flash('Error al cargar el dashboard', 'error')
        return render_template('dashboard.html', stats={}, productos_bajos=[])

@app.route('/productos')
@login_required
def productos():
    """Lista todos los productos"""
    try:
        productos_lista = sistema.obtener_productos()
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
            descripcion = request.form['descripcion'].strip()
            categoria = request.form['categoria'].strip()
            precio_compra = float(request.form['precio_compra'])
            precio_venta = float(request.form['precio_venta'])
            stock_actual = int(request.form['stock_actual'])
            stock_minimo = int(request.form['stock_minimo'])
            
            # Validación básica
            if precio_venta <= precio_compra:
                flash('❌ El precio de venta debe ser mayor al precio de compra', 'error')
            elif stock_actual < 0 or stock_minimo < 0:
                flash('❌ El stock no puede ser negativo', 'error')
            elif sistema.agregar_producto(codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock_actual, stock_minimo):
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
        producto = sistema.obtener_producto_por_id(producto_id)
        
        if not producto:
            flash('❌ Producto no encontrado', 'error')
            return redirect(url_for('productos'))
        
        if request.method == 'POST':
            codigo = request.form['codigo'].strip()
            nombre = request.form['nombre'].strip()
            descripcion = request.form['descripcion'].strip()
            categoria = request.form['categoria'].strip()
            precio_compra = float(request.form['precio_compra'])
            precio_venta = float(request.form['precio_venta'])
            stock_actual = int(request.form['stock_actual'])
            stock_minimo = int(request.form['stock_minimo'])
            
            # Validación
            if precio_venta <= precio_compra:
                flash('❌ El precio de venta debe ser mayor al precio de compra', 'error')
            elif stock_actual < 0 or stock_minimo < 0:
                flash('❌ El stock no puede ser negativo', 'error')
            elif sistema.actualizar_producto(producto_id, codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock_actual, stock_minimo):
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
        if sistema.eliminar_producto(producto_id):
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
        movimientos_lista = sistema.obtener_movimientos()
        productos_lista = sistema.obtener_productos()
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
        motivo = request.form['motivo'].strip()
        
        if cantidad <= 0:
            flash('❌ La cantidad debe ser mayor a 0', 'error')
        elif sistema.agregar_movimiento(producto_id, tipo, cantidad, motivo):
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
        
        productos_lista = sistema.buscar_productos(query, categoria)
        categorias = sistema.obtener_categorias()
        
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
        reporte_stock = sistema.obtener_reporte_stock()
        reporte_movimientos = sistema.obtener_reporte_movimientos()
        return render_template('reportes.html', 
                             reporte_stock=reporte_stock, 
                             reporte_movimientos=reporte_movimientos)
    except Exception as e:
        flash('Error al generar reportes', 'error')
        return render_template('reportes.html', reporte_stock=[], reporte_movimientos=[])

# ================= RUTA DE REGISTRO (OPCIONAL) =================
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registro de nuevos usuarios (solo para desarrollo)"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip()
        
        if sistema.agregar_usuario(username, password, nombre, email):
            flash('✅ Usuario registrado correctamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash('❌ Error: El nombre de usuario ya existe', 'error')
    
    return render_template('registro.html')

# ================= MANEJO DE ERRORES =================
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template('error.html', mensaje='Página no encontrada'), 404

@app.errorhandler(500)
def error_servidor(error):
    return render_template('error.html', mensaje='Error interno del servidor'), 500

# ================= INICIALIZACIÓN =================
if __name__ == '__main__':
    print("=" * 50)
    print("🔐 SISTEMA DE INVENTARIO CON LOGIN")
    print("📍 URL: http://localhost:5000")
    print("👤 Usuario: admin")
    print("🔑 Contraseña: admin123")
    print("=" * 50)
    
    # Configuración mejorada
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Cambiado a False para quitar advertencia
        threaded=True
    )