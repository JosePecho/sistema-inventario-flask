import sqlite3
import datetime
from typing import List, Dict, Optional

class SistemaInventario:
    def __init__(self, db_name="inventario.db"):
        self.db_name = db_name
        self.crear_tablas()
    
    def crear_tablas(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                categoria TEXT,
                precio_compra REAL,
                precio_venta REAL,
                stock_actual INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 0,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                tipo TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                motivo TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def agregar_producto(self, codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock_actual, stock_minimo):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO productos (codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock_actual, stock_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock_actual, stock_minimo))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error al agregar producto: {e}")
            return False
    
    def obtener_productos(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM productos ORDER BY nombre')
        productos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return productos
    
    def obtener_producto_por_id(self, producto_id) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM productos WHERE id = ?', (producto_id,))
        producto = cursor.fetchone()
        conn.close()
        return dict(producto) if producto else None
    
    def actualizar_producto(self, producto_id, codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock_actual, stock_minimo):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE productos 
                SET codigo=?, nombre=?, descripcion=?, categoria=?, precio_compra=?, precio_venta=?, stock_actual=?, stock_minimo=?
                WHERE id=?
            ''', (codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock_actual, stock_minimo, producto_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al actualizar producto: {e}")
            return False
    
    def eliminar_producto(self, producto_id):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM productos WHERE id = ?', (producto_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al eliminar producto: {e}")
            return False
    
    def agregar_movimiento(self, producto_id, tipo, cantidad, motivo):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('INSERT INTO movimientos (producto_id, tipo, cantidad, motivo) VALUES (?, ?, ?, ?)', (producto_id, tipo, cantidad, motivo))
            
            if tipo == 'entrada':
                cursor.execute('UPDATE productos SET stock_actual = stock_actual + ? WHERE id = ?', (cantidad, producto_id))
            elif tipo == 'salida':
                cursor.execute('UPDATE productos SET stock_actual = stock_actual - ? WHERE id = ?', (cantidad, producto_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al agregar movimiento: {e}")
            return False
    
    def obtener_movimientos(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, p.nombre as producto_nombre, p.codigo as producto_codigo
            FROM movimientos m
            JOIN productos p ON m.producto_id = p.id
            ORDER BY m.fecha DESC
        ''')
        
        movimientos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return movimientos
    
    def obtener_estadisticas(self) -> Dict:
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Total productos
            cursor.execute('SELECT COUNT(*) FROM productos')
            total_result = cursor.fetchone()
            total_productos = total_result[0] if total_result else 0
            
            # ✅ SOLO stock menor o igual a 20
            cursor.execute('SELECT COUNT(*) FROM productos WHERE stock_actual <= 20')
            stock_bajo_result = cursor.fetchone()
            stock_bajo = stock_bajo_result[0] if stock_bajo_result else 0
            
            # Valor inventario
            cursor.execute('SELECT SUM(stock_actual * precio_compra) FROM productos')
            valor_result = cursor.fetchone()
            valor_inventario = valor_result[0] if valor_result and valor_result[0] else 0
            
            # Movimientos hoy
            cursor.execute("SELECT COUNT(*) FROM movimientos WHERE DATE(fecha) = DATE('now')")
            movimientos_result = cursor.fetchone()
            movimientos_hoy = movimientos_result[0] if movimientos_result else 0
            
            conn.close()
            
            return {
                'total_productos': total_productos,
                'stock_bajo': stock_bajo,
                'valor_inventario': round(valor_inventario, 2),
                'movimientos_hoy': movimientos_hoy
            }
        except Exception as e:
            print(f"Error en estadísticas: {e}")
            return {
                'total_productos': 0,
                'stock_bajo': 0,
                'valor_inventario': 0,
                'movimientos_hoy': 0
            }
    
    def obtener_productos_stock_bajo(self) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # ✅ SOLO productos con 20 unidades o menos
            cursor.execute('SELECT * FROM productos WHERE stock_actual <= 20 ORDER BY stock_actual ASC')
            productos = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return productos
        except Exception as e:
            print(f"Error en stock bajo: {e}")
            return []
    
    def buscar_productos(self, query="", categoria="") -> List[Dict]:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        sql = 'SELECT * FROM productos WHERE 1=1'
        params = []
        
        if query:
            sql += ' AND (nombre LIKE ? OR codigo LIKE ? OR descripcion LIKE ?)'
            params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
        
        if categoria:
            sql += ' AND categoria = ?'
            params.append(categoria)
        
        sql += ' ORDER BY nombre'
        cursor.execute(sql, params)
        productos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return productos
    
    def obtener_categorias(self) -> List[str]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL ORDER BY categoria')
        categorias = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categorias
    
    def obtener_reporte_stock(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT categoria, COUNT(*) as total_productos, SUM(stock_actual) as total_stock, 
                   SUM(stock_actual * precio_compra) as valor_total
            FROM productos 
            GROUP BY categoria
            ORDER BY categoria
        ''')
        
        reporte = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return reporte
    
    def obtener_reporte_movimientos(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DATE(fecha) as fecha, tipo, COUNT(*) as total_movimientos, SUM(cantidad) as total_cantidad
            FROM movimientos 
            GROUP BY DATE(fecha), tipo
            ORDER BY fecha DESC, tipo
        ''')
        
        reporte = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return reporte