from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database import SistemaInventario

app = Flask(__name__)
app.secret_key = 'clave_secreta_inventario_2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True

sistema = SistemaInventario()

# ================= RUTAS PRINCIPALES =================
@app.route('/')
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
def productos():
    """Lista todos los productos"""
    try:
        productos_lista = sistema.obtener_productos()
        return render_template('productos.html', productos=productos_lista)
    except Exception as e:
        flash('Error al cargar los productos', 'error')
        return render_template('productos.html', productos=[])

@app.route('/agregar_producto', methods=['GET', 'POST'])
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
    print("🚀 SISTEMA DE INVENTARIO INICIADO")
    print("📍 URL: http://localhost:5000")
    print("⚠️  Este servidor es solo para DESARROLLO")
    print("=" * 50)
    
    # Configuración mejorada
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Cambiado a False para quitar advertencia
        threaded=True
    )