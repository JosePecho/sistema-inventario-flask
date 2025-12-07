import sqlite3
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

class SistemaInventario:
    def __init__(self, db_name="inventario.db"):
        self.db_name = db_name
        self.crear_tablas()
    
    def crear_tablas(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabla de usuarios (compartida) - AGREGADO CAMPO foto_perfil
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT,
                es_admin BOOLEAN DEFAULT 1,
                foto_perfil TEXT DEFAULT NULL,  -- NUEVO: campo para foto de perfil
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    # ========== NUEVOS MÉTODOS PARA FOTO DE PERFIL ==========
    
    def actualizar_foto_perfil(self, user_id, foto_path):
        """Actualizar la ruta de la foto de perfil del usuario"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE usuarios SET foto_perfil = ? WHERE id = ?',
                (foto_path, user_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error actualizando foto de perfil: {e}")
            return False
    
    def obtener_foto_perfil(self, user_id):
        """Obtener la ruta de la foto de perfil del usuario"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT foto_perfil FROM usuarios WHERE id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] else None
        except Exception as e:
            print(f"Error obteniendo foto de perfil: {e}")
            return None
    
    def guardar_foto_archivo(self, user_id, file):
        """Guardar archivo de foto en el sistema de archivos"""
        try:
            # Crear carpeta para fotos de perfil si no existe
            foto_dir = os.path.join('static', 'profile_photos')
            if not os.path.exists(foto_dir):
                os.makedirs(foto_dir)
            
            # Generar nombre único para la foto
            import uuid
            extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{extension}"
            filepath = os.path.join(foto_dir, filename)
            
            # Guardar archivo
            file.save(filepath)
            
            # Guardar ruta relativa en la base de datos
            ruta_relativa = f'profile_photos/{filename}'
            self.actualizar_foto_perfil(user_id, ruta_relativa)
            
            return ruta_relativa
            
        except Exception as e:
            print(f"Error al guardar foto: {e}")
            return None
    
    def eliminar_foto_antigua(self, user_id):
        """Eliminar la foto anterior del usuario del sistema de archivos"""
        try:
            foto_actual = self.obtener_foto_perfil(user_id)
            if foto_actual:
                foto_path = os.path.join('static', foto_actual)
                if os.path.exists(foto_path):
                    os.remove(foto_path)
                    print(f"✅ Foto anterior eliminada: {foto_path}")
            return True
        except Exception as e:
            print(f"Error eliminando foto anterior: {e}")
            return False

    # ========== MÉTODOS EXISTENTES (se mantienen igual) ==========
    
    def actualizar_estructura_tablas(self, user_id):
        """Actualizar la estructura de las tablas existentes con las nuevas columnas"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f'productos_{user_id}',))
            if not cursor.fetchone():
                conn.close()
                return False
                
            cursor.execute(f"PRAGMA table_info(productos_{user_id})")
            columnas_existentes = [col[1] for col in cursor.fetchall()]
            
            columnas_nuevas = [
                ('modelo', 'TEXT'),
                ('marca', 'TEXT'), 
                ('estado', 'TEXT'),
                ('año_adquisicion', 'INTEGER')
            ]
            
            for columna, tipo in columnas_nuevas:
                if columna not in columnas_existentes:
                    cursor.execute(f"ALTER TABLE productos_{user_id} ADD COLUMN {columna} {tipo}")
                    print(f"✅ Columna {columna} agregada a productos_{user_id}")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error actualizando estructura de tablas: {e}")
            return False

    # ========== MÉTODOS PARA USUARIOS ==========
    
    def obtener_usuario_por_username(self, username):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
            usuario = cursor.fetchone()
            conn.close()
            return dict(usuario) if usuario else None
        except Exception as e:
            print(f"Error obteniendo usuario por username: {e}")
            return None
    
    def obtener_usuario_por_id(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,))
            usuario = cursor.fetchone()
            conn.close()
            return dict(usuario) if usuario else None
        except Exception as e:
            print(f"Error obteniendo usuario por ID: {e}")
            return None
    
    def verificar_password(self, username, password):
        usuario = self.obtener_usuario_por_username(username)
        if usuario and check_password_hash(usuario['password'], password):
            return usuario
        return None
    
    def agregar_usuario(self, username, password, nombre, email=None, es_admin=True):
        try:
            if self.obtener_usuario_por_username(username):
                return False, "El nombre de usuario ya existe"
            
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO usuarios (username, password, nombre, email, es_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, nombre, email, 1 if es_admin else 0))
            
            user_id = cursor.lastrowid
            
            try:
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS productos_{user_id} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT UNIQUE NOT NULL,
                        nombre TEXT NOT NULL,
                        descripcion TEXT,
                        ubicacion TEXT,
                        modelo TEXT,
                        marca TEXT,
                        estado TEXT,
                        año_adquisicion INTEGER,
                        precio_compra REAL,
                        stock_actual INTEGER DEFAULT 0,
                        stock_minimo INTEGER DEFAULT 0,
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS movimientos_{user_id} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        producto_id INTEGER,
                        tipo TEXT NOT NULL,
                        cantidad INTEGER NOT NULL,
                        motivo TEXT,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (producto_id) REFERENCES productos_{user_id} (id)
                    )
                ''')
                
                print(f"✅ Usuario {username} (ID: {user_id}) creado con tablas exitosamente")
                
            except Exception as e:
                print(f"❌ Error creando tablas para usuario {user_id}: {e}")
                cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
                conn.commit()
                conn.close()
                return False, "Error creando las tablas del usuario. Intenta nuevamente."
            
            conn.commit()
            conn.close()
            return True, f"✅ Usuario {username} creado exitosamente"
            
        except sqlite3.IntegrityError:
            return False, "El nombre de usuario ya existe"
        except Exception as e:
            print(f"❌ Error crítico agregando usuario: {e}")
            return False, f"Error del sistema: {str(e)}"

    def asegurar_tablas_usuario(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS productos_{user_id} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    ubicacion TEXT,
                    modelo TEXT,
                    marca TEXT,
                    estado TEXT,
                    año_adquisicion INTEGER,
                    precio_compra REAL,
                    stock_actual INTEGER DEFAULT 0,
                    stock_minimo INTEGER DEFAULT 0,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS movimientos_{user_id} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        producto_id INTEGER,
                        tipo TEXT NOT NULL,
                        cantidad INTEGER NOT NULL,
                        motivo TEXT,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (producto_id) REFERENCES productos_{user_id} (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error asegurando tablas para usuario {user_id}: {e}")
            return False

    # ========== MÉTODOS PARA PRODUCTOS ==========
    
    def obtener_estadisticas(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT COUNT(*) FROM productos_{user_id}')
            total_productos = cursor.fetchone()[0]
            
            cursor.execute(f'SELECT COUNT(*) FROM movimientos_{user_id}')
            total_movimientos = cursor.fetchone()[0]
            
            cursor.execute(f'SELECT COUNT(*) FROM productos_{user_id} WHERE stock_actual < 30')
            productos_bajos = cursor.fetchone()[0]
            
            cursor.execute(f'SELECT SUM(precio_compra * stock_actual) FROM productos_{user_id}')
            valor_total = cursor.fetchone()[0] or 0
            
            cursor.execute(f'SELECT COUNT(*) FROM movimientos_{user_id} WHERE DATE(fecha) = DATE("now")')
            movimientos_hoy = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_productos': total_productos,
                'total_movimientos': total_movimientos,
                'productos_bajos': productos_bajos,
                'valor_total': round(valor_total, 2),
                'valor_inventario': round(valor_total, 2),
                'stock_bajo': productos_bajos,
                'movimientos_hoy': movimientos_hoy
            }
        except Exception as e:
            print(f"Error al obtener estadísticas del usuario {user_id}: {e}")
            return {
                'total_productos': 0,
                'total_movimientos': 0,
                'productos_bajos': 0,
                'valor_total': 0,
                'valor_inventario': 0,
                'stock_bajo': 0,
                'movimientos_hoy': 0
            }
    
    def obtener_productos_stock_bajo(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT * FROM productos_{user_id} 
                WHERE stock_actual < 30
                ORDER BY stock_actual ASC
            ''')
            productos = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return productos
        except Exception as e:
            print(f"Error al obtener productos bajos en stock del usuario {user_id}: {e}")
            return []
    
    def obtener_productos(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT * FROM productos_{user_id} ORDER BY nombre')
            productos = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return productos
        except Exception as e:
            print(f"Error al obtener productos del usuario {user_id}: {e}")
            return []
    
    def obtener_producto_por_id(self, user_id, producto_id):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT * FROM productos_{user_id} WHERE id = ?', (producto_id,))
            producto = cursor.fetchone()
            conn.close()
            return dict(producto) if producto else None
        except Exception as e:
            print(f"Error al obtener producto del usuario {user_id}: {e}")
            return None
    
    def agregar_producto(self, user_id, codigo, nombre, descripcion, ubicacion, modelo, marca, estado, año_adquisicion, precio_compra, stock_actual, stock_minimo):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT COUNT(*) FROM productos_{user_id} WHERE codigo = ?', (codigo,))
            existe = cursor.fetchone()[0] > 0
            
            if existe:
                conn.close()
                return False, f"El código '{codigo}' ya existe en tu inventario"
            
            cursor.execute(f'''
                INSERT INTO productos_{user_id} (codigo, nombre, descripcion, ubicacion, modelo, marca, estado, año_adquisicion, precio_compra, stock_actual, stock_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (codigo, nombre, descripcion, ubicacion, modelo, marca, estado, año_adquisicion, precio_compra, stock_actual, stock_minimo))
            
            conn.commit()
            conn.close()
            return True, "Producto agregado correctamente"
            
        except sqlite3.IntegrityError:
            return False, f"El código '{codigo}' ya existe en tu inventario"
        except Exception as e:
            print(f"Error agregando producto para usuario {user_id}: {e}")
            return False, f"Error del sistema: {str(e)}"
    
    def actualizar_producto(self, user_id, producto_id, codigo, nombre, descripcion, ubicacion, modelo, marca, estado, año_adquisicion, precio_compra, stock_actual, stock_minimo):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT COUNT(*) FROM productos_{user_id} WHERE codigo = ? AND id != ?', (codigo, producto_id))
            existe = cursor.fetchone()[0] > 0
            
            if existe:
                conn.close()
                return False, f"El código '{codigo}' ya existe para otro producto"
            
            cursor.execute(f'''
                UPDATE productos_{user_id} 
                SET codigo=?, nombre=?, descripcion=?, ubicacion=?, modelo=?, marca=?, estado=?, año_adquisicion=?, precio_compra=?, stock_actual=?, stock_minimo=?
                WHERE id=?
            ''', (codigo, nombre, descripcion, ubicacion, modelo, marca, estado, año_adquisicion, precio_compra, stock_actual, stock_minimo, producto_id))
            
            conn.commit()
            conn.close()
            
            if cursor.rowcount > 0:
                return True, "Producto actualizado correctamente"
            else:
                return False, "Producto no encontrado"
                
        except Exception as e:
            print(f"Error actualizando producto para usuario {user_id}: {e}")
            return False, f"Error al actualizar producto: {str(e)}"
    
    def eliminar_producto(self, user_id, producto_id):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(f'DELETE FROM movimientos_{user_id} WHERE producto_id = ?', (producto_id,))
            cursor.execute(f'DELETE FROM productos_{user_id} WHERE id = ?', (producto_id,))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error eliminando producto del usuario {user_id}: {e}")
            return False

    # ========== MÉTODOS PARA MOVIMIENTOS ==========
    
    def obtener_movimientos(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT m.*, p.codigo as producto_codigo, p.nombre as producto_nombre 
                FROM movimientos_{user_id} m 
                LEFT JOIN productos_{user_id} p ON m.producto_id = p.id 
                ORDER BY m.fecha DESC
            ''')
            movimientos = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return movimientos
        except Exception as e:
            print(f"Error al obtener movimientos del usuario {user_id}: {e}")
            return []
    
    def agregar_movimiento(self, user_id, producto_id, tipo, cantidad, motivo):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT stock_actual FROM productos_{user_id} WHERE id = ?', (producto_id,))
            producto = cursor.fetchone()
            
            if not producto:
                conn.close()
                return False
            
            if tipo == 'salida':
                stock_actual = producto[0]
                if stock_actual < cantidad:
                    conn.close()
                    return False
            
            cursor.execute(f'''
                INSERT INTO movimientos_{user_id} (producto_id, tipo, cantidad, motivo)
                VALUES (?, ?, ?, ?)
            ''', (producto_id, tipo, cantidad, motivo))
            
            if tipo == 'entrada':
                cursor.execute(f'UPDATE productos_{user_id} SET stock_actual = stock_actual + ? WHERE id = ?', (cantidad, producto_id))
            else:
                cursor.execute(f'UPDATE productos_{user_id} SET stock_actual = stock_actual - ? WHERE id = ?', (cantidad, producto_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error agregando movimiento para usuario {user_id}: {e}")
            return False

    # ========== MÉTODOS PARA BÚSQUEDA Y CONSULTAS ==========
    
    def buscar_productos(self, user_id, query='', ubicacion=''):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            sql = f'''
                SELECT * FROM productos_{user_id} 
                WHERE (codigo LIKE ? OR nombre LIKE ? OR descripcion LIKE ?)
            '''
            params = [f'%{query}%', f'%{query}%', f'%{query}%']
            
            if ubicacion:
                sql += ' AND ubicacion = ?'
                params.append(ubicacion)
            
            sql += ' ORDER BY nombre'
            
            cursor.execute(sql, params)
            productos = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return productos
        except Exception as e:
            print(f"Error buscando productos del usuario {user_id}: {e}")
            return []
    
    def obtener_ubicaciones(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT DISTINCT ubicacion FROM productos_{user_id} WHERE ubicacion IS NOT NULL AND ubicacion != "" ORDER BY ubicacion')
            ubicaciones = [row[0] for row in cursor.fetchall()]
            conn.close()
            return ubicaciones
        except Exception as e:
            print(f"Error obteniendo ubicaciones del usuario {user_id}: {e}")
            return []

    # ========== MÉTODOS PARA REPORTES ==========
    
    def obtener_reporte_stock(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT 
                    COALESCE(ubicacion, 'Sin ubicación') as ubicacion,
                    COUNT(*) as total_productos,
                    SUM(stock_actual) as total_stock,
                    ROUND(SUM(precio_compra * stock_actual), 2) as valor_total
                FROM productos_{user_id} 
                GROUP BY ubicacion
                ORDER BY valor_total DESC
            ''')
            reporte = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return reporte
        except Exception as e:
            print(f"Error generando reporte stock del usuario {user_id}: {e}")
            return []
    
    def obtener_reporte_movimientos(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT 
                    DATE(fecha) as fecha,
                    tipo,
                    COUNT(*) as total_movimientos,
                    SUM(cantidad) as total_cantidad
                FROM movimientos_{user_id} 
                GROUP BY DATE(fecha), tipo
                ORDER BY fecha DESC
                LIMIT 30
            ''')
            reporte = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return reporte
        except Exception as e:
            print(f"Error generando reporte movimientos del usuario {user_id}: {e}")
            return []