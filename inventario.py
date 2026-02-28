import json
from producto import Producto
from config import PATH_PRODUCTOS


class Inventario:
    def __init__(self, archivo=PATH_PRODUCTOS):
        self.archivo = archivo
        self.productos = {}
        self.cargar()
        
    def cargar(self):
        try:
            with open(self.archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
                
                for item in datos:
                    producto = Producto.from_dict(item)
                    self.productos[producto.nombre.lower()] = producto
        except FileNotFoundError:
            self.productos = {}
    
    def guardar(self):
        with open(self.archivo, "w", encoding="utf-8") as f:
            datos = [p.to_dict() for p in self.productos.values()]
            json.dump(datos,f,indent=4)
        
    def agregar_producto(self,producto):
        self.productos[producto.nombre.lower()] = producto
        self.guardar()
    
    def obtener_producto(self,nombre):
        return self.productos.get(nombre.lower())
    
    def mostrar_productos(self):
        for producto in self.productos.values():
            print(f"{producto.nombre} - Precio: {producto.precio}")
            
    def buscar_por_nombre(self,texto):
        resultados = []
        for producto in self.productos.values():
            if texto.lower() in producto.nombre.lower():
                resultados.append(producto.nombre)
        return resultados

    def reducir_stock(self, nombre,cantidad):
        producto = self.obtener_producto(nombre)
        
        if not producto:
            raise ValueError("Producto no encontrado")
        
        producto.reducir_stock(cantidad)
        
        self.guardar()
            
            