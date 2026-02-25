# main.py

from registro_socio import RegistroSocio
from sesion_venta import SesionVenta
from inventario import Inventario
from registro_ventas import RegistroVentas
from carrito import Carrito  # ← Importar explícitamente
from ticket import Ticket     # ← Nueva clase


def main():
    inventario = Inventario()
    registro_socio = RegistroSocio()
    registro_ventas = RegistroVentas()
    
    # Crear carrito ANTES de sesión
    carrito = Carrito()
    sesion = SesionVenta(inventario, registro_ventas)
    sesion.iniciar_venta(carrito)

    socio_autenticado = None

    while True:
        print("""
=========================================
          SUPERMERCADO   
=========================================
""")
        print("\n========== BIENVENIDO ==========")
        print("1. Mostrar productos")
        print("2. Agregar producto")
        print("3. Finalizar compra")
        print("=======================================\n")

        opcion = input("Seleccione una opción: ")

        # ---------------- MOSTRAR PRODUCTOS ----------------
        if opcion == "1":
            inventario.mostrar_productos()

        # ---------------- AGREGAR PRODUCTO ----------------
        elif opcion == "2":
            texto = input("\nIngrese el nombre del producto: ")
            resultados = inventario.buscar_por_nombre(texto)

            if not resultados:
                print("Producto no encontrado.")
                continue

            if len(resultados) == 1:
                nombre_elegido = resultados[0]
            else:
                print("\nResultados encontrados:")
                for i, nombre in enumerate(resultados, 1):
                    print(f"{i}. {nombre}")

                try:
                    opcion_elegida = int(input("Elija una opción: "))
                    nombre_elegido = resultados[opcion_elegida - 1]
                except (ValueError, IndexError):
                    print("Opción no válida.")
                    continue

            print(f"\nProducto elegido: {nombre_elegido}")

            try:
                cantidad = int(input("Ingrese la cantidad: "))
                if cantidad <= 0:
                    print("Ingrese una cantidad válida.")
                    continue
            except ValueError:
                print("Ingrese un número válido.")
                continue

            resultado = sesion.agregar_producto(nombre_elegido, cantidad)

            if resultado:
                print(" Producto agregado al carrito correctamente.")
            else:
                print(" No se pudo agregar el producto.")

        # ---------------- FINALIZAR COMPRA ----------------
        elif opcion == "3":

            # ← CAMBIO: Usar carrito.esta_vacio() en vez de carrito.items
            if carrito.esta_vacio():
                print("\n No hay productos en el carrito.")
                break

            print("\n========== MÉTODOS DE PAGO ==========")
            print("1. Efectivo")
            print("2. Tarjeta")
            print("=====================================\n")

            metodo_pago = input("Seleccione el método de pago: ")

            if metodo_pago == "1":
                sesion.establecer_metodo_pago("efectivo")
            elif metodo_pago == "2":
                sesion.establecer_metodo_pago("tarjeta")
            else:
                print("Opción no válida.")
                continue
            
            respuesta = input("\n¿Es usted socio? (si/no): ").lower()
            if respuesta == "si":
                usuario = input("Ingrese su usuario: ")
                password = input("Ingrese su contraseña: ")

                socio_autenticado = registro_socio.autenticar(usuario, password)

                if socio_autenticado:
                    print(f"\n✓ Bienvenido, {socio_autenticado.usuario}.")
                    print(f"   Se aplicará un descuento del {socio_autenticado.descuento}%.")
                else:
                    print("\n Usuario o contraseña incorrectos.")
                    print("   Continuando sin aplicar descuento.")
            
            # Calcular totales
            subtotal, iva, descuento, total = sesion.calcular_totales(socio_autenticado)

            print("\n========== RESUMEN DE COMPRA ==========")
            print(f"Subtotal:  ${subtotal:.2f}")
            print(f"IVA (21%): ${iva:.2f}")
            
            if descuento > 0:
                print(f"Descuento: -${descuento:.2f}")
            
            print("---------------------------------------")
            print(f"TOTAL A PAGAR: ${total:.2f}")
            print("=======================================\n")

            # -------- PAGO EN EFECTIVO --------
            if metodo_pago == "1":
                pago_acumulado = 0

                while pago_acumulado < total:
                    try:
                        monto = float(input("¿Con cuánto desea pagar?: $"))
                        if monto <= 0:
                            print("Ingrese un monto válido.")
                            continue

                        pago_acumulado += monto

                        if pago_acumulado < total:
                            faltante = total - pago_acumulado
                            print(f"  Dinero insuficiente. Faltan ${faltante:.2f}")

                    except ValueError:
                        print("Ingrese un número válido.")

                vuelto = pago_acumulado - total

                if vuelto > 0:
                    print(f"\n✓ Su vuelto es: ${vuelto:.2f}")

            # Confirmar pago
            try:
                sesion.confirmar_pago(
                    "efectivo" if metodo_pago == "1" else "tarjeta",
                    socio_autenticado
                )
                
                # ← CAMBIO: Usar nueva clase Ticket
                # Obtener items como lista de dicts
                items_dict = [item.to_dict() for item in carrito.listar()]
                
                ticket = Ticket(
                    items=items_dict,
                    subtotal=subtotal,
                    iva=iva,
                    descuento=descuento,
                    total=total,
                    metodo_pago="efectivo" if metodo_pago == "1" else "tarjeta"
                )
                
                # Imprimir ticket
                ticket.imprimir()
                
                # Opcional: Guardar en archivo
                #ticket.guardar_archivo(f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

                print("\n✅ Compra finalizada con éxito.")
                print("   Gracias por su compra.\n")

            except ValueError as e:
                print(f"\n Error: {e}")

            break

        # ---------------- OPCIÓN INVÁLIDA ----------------
        else:
            print(" Opción no válida.")


if __name__ == "__main__":
    main()