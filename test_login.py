# test_login.py
from database import SistemaInventario

def test_usuario():
    sistema = SistemaInventario()
    
    # Verificar que el usuario Leo existe
    usuario = sistema.obtener_usuario_por_username('Leo')
    if usuario:
        print("✅ Usuario Leo encontrado:")
        print(f"   ID: {usuario['id']}")
        print(f"   Nombre: {usuario['nombre']}")
        print(f"   Es admin: {usuario['es_admin']}")
    else:
        print("❌ Usuario Leo NO encontrado")
    
    # Probar login
    resultado = sistema.verificar_password('Leo', 'SISTEMAINVENTARIO')
    if resultado:
        print("✅ Login exitoso con Leo/SISTEMAINVENTARIO")
    else:
        print("❌ Login fallido")

if __name__ == "__main__":
    test_usuario()