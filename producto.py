class Producto:
    def __init__(self,nombre,precio,stock,descuento=0.0):
        self.nombre = nombre
        self.precio = precio
        self.stock = stock
        self.descuento = descuento
        
    def __eq__(self, other):
        if not isinstance(other, Producto):
            return False
        return self.nombre == other.nombre
        
    def tiene_stock(self,cantidad):
        return self.stock >= cantidad
        
    def reducir_stock(self,cantidad):
        if not self.tiene_stock(cantidad):
            raise ValueError(f"Stock insuficiente de {self.nombre}. Disponible: {self.stock}")
        self.stock -= cantidad        
        
    def agregar_stock(self,cantidad):
        self.stock += cantidad
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio} (Stock:{self.stock})"
    
    def to_dict(self):
        return {
            "nombre" : self.nombre,
            "precio" : self.precio,
            "stock" : self.stock
        }
    
    @staticmethod
    def from_dict(data):
        return Producto(
            data["nombre"],
            data["precio"],
            data["stock"]
        )
    

        
   