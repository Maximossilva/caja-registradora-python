class ProductoProveedor:
    def __init__(self, producto, proveedor, precio_compra, stock_disponible):
        self.producto = producto
        self.proveedor = proveedor
        self.precio_compra = precio_compra
        self.stock_disponible = stock_disponible
        
    def hay_stock(self,cantidad):
        return self.stock_disponible >= cantidad
    
    def descontar_stock(self,cantidad):
        if not self.hay_stock(cantidad):
            raise ValueError(f"Stock insuficiente de {self.producto.nombre}. Disponible: {self.stock_disponible}")
        self.stock_disponible -= cantidad
        
    def agregar_stock(self,cantidad):
        self.stock_disponible += cantidad
        
    def to_dict(self):
        return {
            "producto": self.producto.to_dict(),
            "proveedor": self.proveedor.to_dict(),
            "precio_compra": self.precio_compra,
            "stock_disponible": self.stock_disponible
        }