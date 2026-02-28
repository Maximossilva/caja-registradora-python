class Proveedor:
    def __init__(self, nombre):
        self.nombre = nombre
        
    def to_dict(self):
        return {
            "nombre": self.nombre
        }
    
    @staticmethod
    def from_dict(data):
        return Proveedor(
            data["nombre"],
        )