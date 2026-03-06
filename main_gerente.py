# main_gerente.py
#
# Punto de entrada para el flujo GERENTE: reponer stock a partir de proveedores.
# No es el flujo cliente (main.py): aquí se usa la caja y el gestor de proveedores
# para comprar mercadería y actualizar inventario.
#
# Uso: python main_gerente.py

from database.init_db import init_database
from inventario_sqlite import InventarioSQLite
from caja import Caja
from gestor_proveedor import GestorProveedor
from servicio_compra import ServicioCompra


def main():
    # Inicializar BD (crea tablas y datos semilla si no existen)
    init_database()

    # Configuración de sucursal
    BRANCH_ID = 1
    CASH_REGISTER_ID = 1

    inventario = InventarioSQLite(branch_id=BRANCH_ID)
    caja = Caja(cash_register_id=CASH_REGISTER_ID)
    gestor_proveedor = GestorProveedor(inventario)
    servicio_compra = ServicioCompra(gestor_proveedor, caja, inventario)

    print("=== Reposición de stock (gerente) ===\n")
    print("Saldo en caja:", caja.obtener_saldo())
    

    while True:
        nombre = input("Nombre del producto a reponer (vacío para salir): ").strip()
        if not nombre:
            break
        producto = inventario.obtener_producto(nombre)
        if not producto:
            print("Producto no encontrado. Use el nombre exacto del inventario.\n")
            continue
        try:
            cantidad = int(input("Cantidad a reponer: "))
            if cantidad <= 0:
                print("Cantidad debe ser positiva.\n")
                continue
        except ValueError:
            print("Ingrese un número válido.\n")
            continue
        try:
            costo = servicio_compra.reponer_producto(producto, cantidad)
            gestor_proveedor.guardar()
            print(f"✓ Repuestos {cantidad} unidades de {producto.nombre}. Costo: ${costo:.2f}\n")
        except ValueError as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()

   
