# main_gerente.py
#
# Punto de entrada para el flujo GERENTE: reponer stock a partir de proveedores.
# No es el flujo cliente (main.py): aquí se usa la caja y el gestor de proveedores
# para comprar mercadería y actualizar inventario.
#
# Uso: python main_gerente.py

from inventario import Inventario
from caja import Caja
from gestor_proveedor import GestorProveedor
from servicio_compra import ServicioCompra


def main():
    inventario = Inventario()
    caja = Caja()
    gestor_proveedor = GestorProveedor(inventario)
    servicio_compra = ServicioCompra(gestor_proveedor, caja)

    print("=== Reposición de stock (gerente) ===\n")
    print("Saldo en caja:", caja.saldo_actual())
    # Para pruebas: descomentar la línea siguiente para dar saldo inicial (ej. 50000).
    caja.ingresar(50000)
    

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
            inventario.guardar()
            print(f"✓ Repuestos {cantidad} unidades de {producto.nombre}. Costo: ${costo:.2f}\n")
        except ValueError as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()
