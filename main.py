import persistencia
import pagos   
import productos 
import socios 
import config 
import ventas


        
carrito = {}


def solicitar_datos_socio():
    es_socio = input("Es socio del super? (si/no): ").lower()
    
    if es_socio != "si":
        return None, None
    
    
    usuario = input("Usuario: ").strip()
    contraseña = input("Contraseña: ").strip()
    return usuario, contraseña   
      
        
    
def solicitar_metodo_pago():
    print("Metodos de pago")
    print("1- Efectivo")
    print("2- Tarjeta (recargo 10%)")
    
    
    
    while True:
        opcion = input("Elija el metodo: ").strip()
        if opcion in ["1","2"]:
            return opcion
        print("Opcion invalida. Elija 1 o 2")
        
           
def procesar_pago_efectivo(total):    
    pago_acumulado = 0
        
        
    while pago_acumulado < total:
        try:
            pago = float(input("Con cuanto va a pagar: "))
            if pago <= 0:
                print("Numero invalido")
                continue
            pago_acumulado += pago
            
            if pago_acumulado < total:
                falta = total - pago_acumulado
                print(f"Faltan ${falta:.2f}")
        except ValueError:
            print("Ingrese un numero valido")      
                
                
    vuelto = pagos.calcular_vuelto(pago_acumulado, total)      
        
    if vuelto > 0:
        print(f"Su vuelto es ${vuelto:.2f}")
        

                   
def imprimir_ticket(carrito,total):  
    print("\n" + "="*30)
    print("         TICKET DE COMPRA")
    print("="*30)
    
    for producto, info in carrito.items():
        subtotal = pagos.calcular_total(
                    info['precio'],
                    info['cantidad'],
                    info['descuento']
                    )
        print(f"{info['cantidad']}x {producto.capitalize():<15} ${subtotal:>8.2f}")  
    
    
    print("-"*30)
    print(f"{'TOTAL:':<25} ${total:>8.2f}")
    print("="*30 + "\n")
    
def procesar_compra(carrito):
    
    total = pagos.calcular_total_carrito(carrito)
    
    usuario, contraseña = solicitar_datos_socio()
    if usuario is not None:
        if socios.validar_socio(usuario,contraseña):
            total = socios.aplicar_descuento_socio(total)
            print(f"Descuento aplicado, TOTAL CON DESCUENTO: ${total:.2f}")
        else:
            print("Usuario o contraseña incorrectos")
    
    imprimir_ticket(carrito, total)
    
    metodo = solicitar_metodo_pago()
    
    if metodo == "2":
        total = pagos.recargo_tarjeta(total)
        print(f"Pago realizado con tarjeta: ${total:.2f}")
        print("Pago realizado correctamente!")
    else:
        procesar_pago_efectivo(total)
        print("Muchas gracias!")  
    
    persistencia.guardar_ventas_csv(carrito,total)    
                 
              
print("="*40)
print("    BIENVENIDO AL SUPERMERCADO")
print("="*40)

productos = persistencia.cargar_productos_csv()

if not productos:
    productos = ventas.productos_default()
    persistencia.guardar_productos_csv(productos)

while True:
    producto = input("Ingrese su producto (o 'salir' para terminar): ").strip().lower()
    if producto == "salir":
        break
    
   
    if producto not in productos:
        print(f"{producto} no esta en el inventario. Intente de nuevo")
        continue

    # Muestro precio como responsabilidad de UI
    precio = productos[producto]['precio']
    print(f"Precio: ${precio:.2f}")

    try:
        cantidad = int(input(f"Cantidad de {producto}: "))
    except ValueError:
        print("Porfavor ingrese un numero valido")
        continue

    
    resultado = ventas.agregar_productos(carrito,productos,producto,cantidad)
    print(resultado["mensaje"])

if carrito:
    resultado = ventas.confirmar_compra(carrito,productos)   
    if resultado["ok"]:
        persistencia.guardar_productos_csv(productos)
        persistencia.guardar_ventas_csv(resultado["productos_actualizados"])
        

    
      
print("\n" + "="*40) 
if carrito:
    procesar_compra(carrito)
else:       
    print("No se realizaron compras. ¡Hasta pronto!")
print("="*40)