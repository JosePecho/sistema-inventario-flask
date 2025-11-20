import sqlite3
import datetime
from typing import List, Dict, Optional
from werkzeug.security import generate_password_hash, check_password_hash

class SistemaInventario:
    def __init__(self, db_name="inventario.db"):
        self.db_name = db_name
        self.crear_tablas()
        self.crear_usuario_admin()  # Crear usuario admin por defecto
    
    def crear_tablas(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabla de productos (existente)
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
        
        # Tabla de movimientos (existente)
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
        
        # NUEVA TABLA: Usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT,
                es_admin BOOLEAN DEFAULT 0,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def crear_usuario_admin(self):
        """Crear usuario administrador por defecto"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Verificar si ya existe el usuario admin
            cursor.execute('SELECT id FROM usuarios WHERE username = ?', ('admin',))
            if not cursor.fetchone():
                password_hash = generate_password_hash('admin123')
                cursor.execute('''
                    INSERT INTO usuarios (username, password, nombre, email, es_admin)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', password_hash, 'Administrador', 'admin@inventario.com', 1))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error creando usuario admin: {e}")
    
    # ========== MÉTODOS PARA USUARIOS ==========
    
    def obtener_usuario_por_username(self, username):
        """Obtener usuario por nombre de usuario"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
        usuario = cursor.fetchone()
        conn.close()
        return dict(usuario) if usuario else None
    
    def verificar_password(self, username, password):
        """Verificar contraseña del usuario"""
        usuario = self.obtener_usuario_por_username(username)
        if usuario and check_password_hash(usuario['password'], password):
            return usuario
        return None
    
    def agregar_usuario(self, username, password, nombre, email=None, es_admin=False):
        """Agregar nuevo usuario"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO usuarios (username, password, nombre, email, es_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, nombre, email, 1 if es_admin else 0))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False  # Usuario ya existe
        except Exception as e:
            print(f"Error agregando usuario: {e}")
            return False

    # ... (el resto de tus métodos existentes se mantienen igual)