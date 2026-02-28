class ServicioCompra:
    """
    Caso de uso: compra a proveedores (reposición de stock).
    No imprime nada; devuelve datos o lanza excepciones. Así sirve igual para CLI o API.
    """

    def __init__(self, gestor_proveedor, caja):
        self.gestor_proveedor = gestor_proveedor
        self.caja = caja

    def reponer_producto(self, producto, cantidad):
        # --- Validación temprana de cantidad ---
        # Decisión: validar aquí además de en la UI. Así la regla está en un solo lugar
        # y si alguien llama al servicio desde otro sitio (ej. API) no se olvida.
        # Alternativa: no validar y confiar en la UI; rechazada porque el servicio debe ser defensivo.
        if cantidad <= 0:
            raise ValueError("La cantidad a reponer debe ser positiva.")

        # --- Proveedores que venden este producto ---
        relaciones = self.gestor_proveedor.buscar_por_producto(producto)
        # Decisión: distinguir "no hay proveedores" de "ninguno tiene stock".
        # Antes se comprobaba solo `if not relaciones` y luego se usaba `min(relacion_valida)`;
        # si había relaciones pero ninguna con stock, relacion_valida estaba vacía y min() fallaba con un error poco claro.
        if not relaciones:
            raise ValueError(f"No hay proveedores para el producto {producto.nombre}")

        # --- Filtrar los que tienen stock suficiente ---
        con_stock = [r for r in relaciones if r.hay_stock(cantidad)]
        if not con_stock:
            raise ValueError(
                f"Ningún proveedor tiene stock suficiente de {producto.nombre} (solicitado: {cantidad})"
            )

        # --- Elegir el más barato (misma lógica que antes) ---
        proveedor_elegido = min(con_stock, key=lambda r: r.precio_compra)
        costo_total = proveedor_elegido.precio_compra * cantidad

        # --- Validar saldo en caja antes de tocar nada ---
        # Antes se usaba self.capital (no existía) y fallaba en ejecución.
        # Decisión: usar self.caja.saldo_actual() y dar un mensaje claro (cuánto falta, cuánto hay).
        # Alternativa: solo llamar a retirar() y dejar que Caja lance; es válido, pero el mensaje es menos informativo.
        if self.caja.saldo_actual() < costo_total:
            raise ValueError(
                f"Capital insuficiente para comprar {cantidad} de {producto.nombre}. "
                f"Necesita: ${costo_total:.2f}, saldo: ${self.caja.saldo_actual():.2f}"
            )

        # --- Orden de operaciones: retirar → descontar proveedor → agregar al producto ---
        # Si fallara algo después de retirar, quedaríamos con caja descontada y stock sin actualizar.
        # Para un proyecto con BD sería un flujo transaccional; con JSON es aceptable así por ahora.
        self.caja.retirar(costo_total)
        proveedor_elegido.descontar_stock(cantidad)
        producto.agregar_stock(cantidad)

        return costo_total
        
        