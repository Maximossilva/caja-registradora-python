

from config import RECARGO_TARJETA,IVA
    

def calcular_total_carrito(carrito):   
    total = 0
     
    for item , info in carrito.items():
        total += calcular_total(info['precio'],info['cantidad'],info['descuento'])
    return total

#calculamos el precio y nos devuelve el resultado
def calcular_total(precio,cantidad,descuento,):
    #nos devuelve el resultado de toda la operacion con iva y descuentos inlcuidos (en caso de tener)
    return (precio * cantidad) * (1 + IVA) * (1 - descuento)


#metodo de pago
def recargo_tarjeta(total):
    return total * (1 + RECARGO_TARJETA)

def calcular_vuelto(pago_acumulado,total):
    return pago_acumulado - total




              
           
                 