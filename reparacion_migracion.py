import sqlite3
import os

def migrar_base_datos():
    """Migra la base de datos de categoría a ubicación"""
    
    print("=" * 60)
    print("🔧 MIGRACIÓN DE BASE DE DATOS")
    print("📍 Cambiando 'categoría' por 'ubicación'")
    print("=" * 60)
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('inventario.db')
        cursor = conn.cursor()
        
        # 1. Obtener todos los usuarios
        cursor.execute("SELECT id FROM usuarios")
        usuarios = cursor.fetchall()
        
        print(f"📊 Usuarios encontrados: {len(usuarios)}")
        
        for (user_id,) in usuarios:
            print(f"\n🔄 Procesando usuario ID: {user_id}")
            
            # 2. Verificar si la tabla del usuario existe
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='productos_{user_id}'")
            if not cursor.fetchone():
                print(f"  ⚠️ Tabla productos_{user_id} no existe, saltando...")
                continue
            
            # 3. Verificar estructura de la tabla
            cursor.execute(f"PRAGMA table_info(productos_{user_id})")
            columnas = [col[1] for col in cursor.fetchall()]
            print(f"  📋 Columnas actuales: {columnas}")
            
            # 4. Si existe 'categoria' pero no 'ubicacion', renombrar
            if 'categoria' in columnas and 'ubicacion' not in columnas:
                print(f"  🔄 Renombrando 'categoria' a 'ubicacion'...")
                
                # SQLite no permite RENAME COLUMN directamente, necesitamos crear nueva tabla
                # Primero crear tabla temporal con la nueva estructura
                cursor.execute(f'''
                    CREATE TABLE productos_{user_id}_temp AS 
                    SELECT id, codigo, nombre, descripcion, 
                           categoria as ubicacion,  -- RENOMBRADO AQUÍ
                           modelo, marca, estado, año_adquisicion,
                           precio_compra, stock_actual, stock_minimo,
                           fecha_creacion
                    FROM productos_{user_id}
                ''')
                
                # Eliminar tabla original
                cursor.execute(f'DROP TABLE productos_{user_id}')
                
                # Renombrar tabla temporal
                cursor.execute(f'ALTER TABLE productos_{user_id}_temp RENAME TO productos_{user_id}')
                
                print(f"  ✅ Tabla migrada exitosamente")
            
            # 5. Si no existe ninguna, agregar columna ubicacion
            elif 'ubicacion' not in columnas and 'categoria' not in columnas:
                print(f"  ➕ Agregando columna 'ubicacion'...")
                cursor.execute(f'ALTER TABLE productos_{user_id} ADD COLUMN ubicacion TEXT')
                print(f"  ✅ Columna 'ubicacion' agregada")
            
            else:
                print(f"  ✅ Estructura ya actualizada")
        
        # Guardar cambios
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 60)
        print("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ Base de datos actualizada a la nueva estructura")
        print("📍 'categoría' → 'ubicación'")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA MIGRACIÓN: {e}")
        print("⚠️ Si hay problemas, restaura tu backup de inventario.db")
        return False

def verificar_estructura():
    """Verifica la estructura actual de la base de datos"""
    
    print("\n🔍 VERIFICANDO ESTRUCTURA ACTUAL")
    print("=" * 60)
    
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cursor.fetchall()
    
    for (tabla,) in tablas:
        if tabla.startswith('productos_'):
            cursor.execute(f"PRAGMA table_info({tabla})")
            columnas = cursor.fetchall()
            print(f"\n📊 Tabla: {tabla}")
            for col in columnas:
                print(f"  • {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 INICIANDO MIGRACIÓN DE BASE DE DATOS")
    print("⚠️ IMPORTANTE: HAZ UNA COPIA DE SEGURIDAD DE inventario.db ANTES DE CONTINUAR")
    print("¿Continuar? (s/n): ", end="")
    
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        # Primero verificar estructura actual
        verificar_estructura()
        
        # Solicitar confirmación final
        print("\n⚠️ ¿ESTÁS SEGURO DE EJECUTAR LA MIGRACIÓN? (s/n): ", end="")
        confirmacion = input().strip().lower()
        
        if confirmacion == 's':
            migrar_base_datos()
        else:
            print("❌ Migración cancelada por el usuario")
    else:
        print("❌ Migración cancelada")