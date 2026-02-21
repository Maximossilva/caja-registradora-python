def estadisticas_por_fecha(fecha_buscar, archivo ="ventas.csv"):
    import csv
    
    ventas_del_dia = {}
    productos_vendidos = {}
    
    try:
        with open(archivo, mode="r",newline="",encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for fila in reader:
                
                fecha_fila = fila["fecha"].split(" ")[0]
                
                if fecha_fila == fecha_buscar:
                    
                    id_venta = int(fila["id_venta"])
                    total = float(fila["total_compra"])
                    producto = fila["producto"]
                    cantidad = int(fila["cantidad"])
                    
                    if id_venta not in ventas_del_dia:
                        ventas_del_dia[id_venta] = total
                    
                    if producto not in productos_vendidos:
                        productos_vendidos[producto] = 0
                        
                    productos_vendidos[producto] += cantidad
                    
        if not ventas_del_dia:
            print("No hay ventas en esta fecha.")
            return
        
        total_dia = sum(ventas_del_dia.values())
        cantidad_ventas = len(ventas_del_dia)
        ticket_promedio = total_dia / cantidad_ventas
        
        producto_mas_vendido = max(productos_vendidos, key=productos_vendidos.get)
        
        print("\n ESTADÍSTICAS")
        print("Fecha:", fecha_buscar)
        print("Total vendido:", round(total_dia, 2))
        print("Cantidad de ventas:", cantidad_ventas)
        print("Ticket promedio:", round(ticket_promedio, 2))
        print("Producto más vendido:", producto_mas_vendido)
        print("Cantidad vendida:", productos_vendidos[producto_mas_vendido])
    
    except FileNotFoundError:
        print("No existe archivo de ventas.")