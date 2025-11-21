# cambiar_usuario.py
from database import SistemaInventario
from werkzeug.security import generate_password_hash

def cambiar_credenciales():
    sistema = SistemaInventario()
    
    # Cambiar usuario admin existente
    nuevo_usuario = "Leo"
    nueva_password = "SISTEMAINVENTARIO"
    
    try:
        # Conectar a la base de datos
        import sqlite3
        conn = sqlite3.connect("inventario.db")
        cursor = conn.cursor()
        
        # Generar hash de la nueva contraseña
        password_hash = generate_password_hash(nueva_password)
        
        # Actualizar el usuario admin
        cursor.execute('''
            UPDATE usuarios 
            SET username = ?, password = ?, nombre = ?
            WHERE username = 'admin'
        ''', (nuevo_usuario, password_hash, "Leo"))
        
        conn.commit()
        conn.close()
        
        print("✅ Credenciales actualizadas exitosamente!")
        print(f"👤 Nuevo usuario: {nuevo_usuario}")
        print(f"🔑 Nueva contraseña: {nueva_password}")
        
    except Exception as e:
        print(f"❌ Error al cambiar credenciales: {e}")

if __name__ == "__main__":
    cambiar_credenciales()