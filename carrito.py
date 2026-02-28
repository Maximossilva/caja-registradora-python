# carrito.py

class ItemCarrito:
    """
    Representa UN producto en el carrito con su cantidad.
    
    ¿Por qué esta clase?
    - Separa el concepto de "producto en inventario" vs "producto en carrito"
    - En inventario: un producto tiene STOCK
    - En carrito: un producto tiene CANTIDAD que quiero comprar
    - NO duplicamos datos (precio, nombre), guardamos referencia al objeto Producto
    """
    
    def __init__(self, producto, cantidad):
        """
        Args:
            producto (Producto): REFERENCIA al objeto Producto del inventario
            cantidad (int): Cantidad que el cliente quiere comprar
        """
        # Guardamos la REFERENCIA al objeto Producto (no copiamos sus datos)
        self.producto = producto
        self.cantidad = cantidad
    
    def calcular_subtotal(self):
        """
        Calcula el subtotal de ESTE item (precio * cantidad).
        
        ¿Por qué aquí?
        - Es responsabilidad del item calcular cuánto cuesta
        - Usa el precio ACTUAL del producto (no una copia vieja)
        """
        return self.producto.precio * self.cantidad
    
    def to_dict(self):
        """
        Convierte el item a diccionario para guardar en JSON.
        
        ¿Por qué esto?
        - Cuando guardamos la venta, necesitamos un "snapshot" del momento
        - Guardamos el precio que tenía en ese momento (no la referencia)
        """
        return {
            "nombre": self.producto.nombre,
            "precio": self.producto.precio,  # Precio al momento de la venta
            "cantidad": self.cantidad
        }
    
    def __str__(self):
        """Para debugging: print(item)"""
        return f"{self.cantidad}x {self.producto.nombre} @ ${self.producto.precio}"


class Carrito:
    """
    Gestiona los items que el cliente quiere comprar.
    
    ¿Por qué dict en vez de list?
    - Acceso rápido por nombre: carrito.items["pan"]
    - No se repiten productos (si agregas pan dos veces, incrementa cantidad)
    """
    
    def __init__(self):
        # Dict: {"pan": ItemCarrito(...), "leche": ItemCarrito(...)}
        self.items = {}
    
    def agregar(self, producto, cantidad):
        """
        Agrega un producto al carrito o incrementa su cantidad.
        
        Args:
            producto (Producto): OBJETO Producto del inventario (no nombre string)
            cantidad (int): Cantidad a agregar
        
        ¿Por qué NO validamos stock aquí?
        - Separación de responsabilidades
        - Carrito solo sabe "tengo X items"
        - SesionVenta valida stock ANTES de llamar a este método
        """
        nombre = producto.nombre
        
        # Si el producto ya está en el carrito, incrementa cantidad
        if nombre in self.items:
            self.items[nombre].cantidad += cantidad
        else:
            # Si es nuevo, crea un ItemCarrito
            self.items[nombre] = ItemCarrito(producto, cantidad)
    
    def quitar(self, nombre):
        """
        Elimina un producto del carrito.
        
        Args:
            nombre (str): Nombre del producto a eliminar
        
        Returns:
            bool: True si se eliminó, False si no existía
        """
        if nombre in self.items:
            del self.items[nombre]
            return True
        return False
    
    def modificar_cantidad(self, nombre, nueva_cantidad):
        """
        Cambia la cantidad de un producto en el carrito.
        
        Args:
            nombre (str): Nombre del producto
            nueva_cantidad (int): Nueva cantidad (si es 0, elimina el producto)
        """
        if nombre in self.items:
            if nueva_cantidad <= 0:
                self.quitar(nombre)
            else:
                self.items[nombre].cantidad = nueva_cantidad
            return True
        return False
    
    def calcular_subtotal(self):
        """
        Suma los subtotales de TODOS los items del carrito.
        
        ¿Por qué aquí?
        - Carrito sabe sumar sus items
        - Cada ItemCarrito calcula su propio subtotal
        """
        return sum(item.calcular_subtotal() for item in self.items.values())
    
    def vaciar(self):
        """Elimina todos los items del carrito."""
        self.items.clear()
    
    def listar(self):
        """
        Devuelve lista de items para iterar.
        
        Returns:
            list: Lista de objetos ItemCarrito
        """
        return list(self.items.values())
    
    def esta_vacio(self):
        """Verifica si el carrito está vacío."""
        return len(self.items) == 0

    def cantidad_de(self, nombre):
        """
        Devuelve la cantidad actual de un producto en el carrito.
        
        Args:
            nombre (str): Nombre del producto.
        
        Returns:
            int: Cantidad en el carrito (0 si no existe).
        """
        item = self.items.get(nombre)
        return item.cantidad if item else 0
    
    def cantidad_total_items(self):
        """
        Suma la cantidad de TODOS los productos.
        
        Ejemplo: 2 panes + 3 leches = 5 items
        """
        return sum(item.cantidad for item in self.items.values())
    
    def __len__(self):
        """
        Permite usar len(carrito).
        
        Devuelve cantidad de productos DIFERENTES (no suma de cantidades).
        Ejemplo: 2 panes + 3 leches = len = 2 (dos productos diferentes)
        """
        return len(self.items)
    
    def __str__(self):
        """Para debugging: print(carrito)"""
        if self.esta_vacio():
            return "Carrito vacío"
        items_str = ", ".join(str(item) for item in self.items.values())
        return f"Carrito: {items_str}"