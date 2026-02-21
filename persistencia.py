import csv

def cargar_productos_csv(archivo="productos.csv"):
    productos = {}
    
    try:
        with open(archivo, mode="r", newline="",encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for fila in reader:
                nombre = fila["nombre"]
                
                productos[nombre] = {
                    "precio": float(fila["precio"]),
                    "descuento": float(fila["descuento"]),
                    "stock" :int(fila["stock"])
                }
    except FileNotFoundError:
        print("Archivo no encontrado. Se usaran productos por defecto.")
        
    return productos       

def guardar_productos_csv(productos, archivo = "productos.csv"):
    with open(archivo, mode="w", newline="", encoding="utf-8") as f:
        campos = ["nombre","precio","descuento","stock"]
        writer = csv.DictWriter(f, fieldnames=campos)
        
        writer.writeheader()
        
        for nombre, datos in productos.items():
            writer.writerow({
                "nombre": nombre,
                "precio": datos["precio"],
                "descuento": datos["descuento"],
                "stock": datos["stock"]
            })

def guardar_ventas_csv(carrito, total, archivo = "ventas.csv"):
    import csv
    from datetime import datetime
    
    id_venta = obtener_siguiente_id_venta(archivo)
    
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(archivo, mode="a", newline="", encoding="utf-8") as f:
        campos = ["id_venta","fecha","producto","cantidad","precio_unitario","total_compra"]
        writer = csv.DictWriter(f, fieldnames=campos)
        
        if f.tell() == 0:
            writer.writeheader()
        
        for producto, datos in carrito.items():
            writer.writerow({
                "id_venta": id_venta,
                "fecha" : fecha,
                "producto" : producto,
                "cantidad" : datos["cantidad"],
                "precio_unitario" : datos["precio"],
                "total_compra" : round(total,2)
            })
            
def obtener_siguiente_id_venta(archivo="ventas.csv"):
    import csv
    
    try:
        with open(archivo, mode="r", newline="",encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            
            if not reader:
                return 1 
            
            ultimo_id = int(reader[-1]["id_venta"])
            return ultimo_id + 1
    except FileNotFoundError:
        return 1 
    


            
    
            
         