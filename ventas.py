def agregar_productos(carrito, productos, nombre, cantidad):
    """
    Agrega productos al carrito validando stock y existencia.
    
    Args:
        carrito (dict): Diccionario con los productos en el carrito.
        productos (dict): Diccionario con la base de datos de productos.
        nombre (str): Nombre del producto a agregar.
        cantidad (int): Cantidad a agregar.
        
    Returns:
        dict: Resultado de la operación con claves 'ok', 'mensaje', 'cantidad_en_carrito'.
    """
    # Validar que el producto exista
    if nombre not in productos:
        return {
            "ok": False,
            "mensaje": f"El producto '{nombre}' no existe.",
            "cantidad_en_carrito": 0
        }
    
    # Validar cantidad positiva
    if cantidad <= 0:
        return {
            "ok": False,
            "mensaje": "La cantidad debe ser mayor a 0.",
            "cantidad_en_carrito": 0
        }
        
    stock_actual = productos[nombre]['stock']
    
    # Calcular cantidad ya en carrito
    cantidad_en_carrito = 0
    if nombre in carrito:
        cantidad_en_carrito = carrito[nombre]['cantidad']
        
    cantidad_total_deseada = cantidad_en_carrito + cantidad
    
    # Validar stock
    if cantidad_total_deseada > stock_actual:
        return {
            "ok": False,
            "mensaje": f"No hay stock suficiente. Stock: {stock_actual}, En carrito: {cantidad_en_carrito}, Solicitado: {cantidad}.",
            "cantidad_en_carrito": cantidad_en_carrito
        }
        
    # Si pasa todas las validaciones, agregar al carrito
    precio = productos[nombre]['precio']
    descuento = productos[nombre]['descuento']
    
    if nombre in carrito:
        carrito[nombre]['cantidad'] += cantidad
    else:
        carrito[nombre] = {
            'precio': precio,
            'cantidad': cantidad,
            'descuento': descuento
        }
        
    return {
        "ok": True,
        "mensaje": f"Se agregaron {cantidad} unidades de {nombre} al carrito.",
        "cantidad_en_carrito": carrito[nombre]['cantidad']
    }

def confirmar_compra(carrito,productos):
    if not carrito:
        return {
            "ok" : False,
            "mensaje" : "El carrito esta vacio",
        }
        
    productos_actualizados = []   
    
    for nombre, datos in carrito.items():
        cantidad = datos["cantidad"]
        productos[nombre]["stock"] -= cantidad  
        productos_actualizados.append(nombre)
        
    
    carrito.clear()
    
    return {
        "ok" : True,
        "mensaje" : "Compra confirmada",
        "productos_actualizados" : productos_actualizados
        }      
    
    
