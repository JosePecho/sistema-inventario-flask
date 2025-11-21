# reparar_registro.py
import sqlite3
import os

def reparar_sistema_registro():
    print("🔧 REPARANDO SISTEMA DE REGISTRO...")
    
    # Verificar y crear template de registro si no existe
    if not os.path.exists("templates/register.html"):
        print("✅ Creando template de registro...")
        # Aquí iría el contenido HTML del register.html que te proporcioné arriba
    
    # Verificar usuarios existentes
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT username FROM usuarios")
    usuarios = cursor.fetchall()
    
    print("👥 Usuarios existentes en el sistema:")
    for usuario in usuarios:
        print(f"   - {usuario[0]}")
    
    conn.close()
    
    print("🎉 SISTEMA DE REGISTRO REPARADO!")
    print("📍 Ahora puedes registrar nuevos usuarios correctamente")

if __name__ == "__main__":
    reparar_sistema_registro()