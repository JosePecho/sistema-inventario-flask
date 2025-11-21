import sqlite3
import os

def reparar_todo():
    print("🔧 REPARANDO SISTEMA...")
    
    # 1. Eliminar base de datos vieja
    if os.path.exists("inventario.db"):
        os.remove("inventario.db")
        print("✅ Base de datos vieja eliminada")
    
    # 2. Crear nueva base de datos
    from database import SistemaInventario
    sistema = SistemaInventario()
    print("✅ Nueva base de datos creada")
    
    # 3. Crear usuario Leo
    if sistema.agregar_usuario("Leo", "SISTEMAINVENTARIO", "Leo", es_admin=True):
        print("✅ Usuario Leo creado")
    else:
        print("⚠️  Usuario Leo ya existe")
    
    # 4. Verificar que se crearon las tablas
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    
    # Verificar tablas de usuario 1
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'productos_%'")
    tablas_productos = cursor.fetchall()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'movimientos_%'")
    tablas_movimientos = cursor.fetchall()
    
    conn.close()
    
    print(f"✅ Tablas de productos creadas: {len(tablas_productos)}")
    print(f"✅ Tablas de movimientos creadas: {len(tablas_movimientos)}")
    print("🎉 SISTEMA REPARADO EXITOSAMENTE!")
    print("📍 Ahora ejecuta: python app.py")

if __name__ == "__main__":
    reparar_todo()