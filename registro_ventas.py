import json
from datetime import datetime
from config import PATH_VENTAS


class RegistroVentas:
    def __init__(self, archivo=PATH_VENTAS):
        self.archivo = archivo
        self.ventas = []
        self.cargar()
    
    def cargar(self):
        try:
            with open(self.archivo, "r", encoding="utf-8") as f:
                contenido = f.read().strip()
                if not contenido:
                    self.ventas = []
                else:
                    self.ventas = json.loads(contenido)
        except FileNotFoundError:
            self.ventas = []
            
    def guardar(self):
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(self.ventas, f, indent=4)
    
    def generar_id(self):
        if not self.ventas:
            return 1 
        ultimo_id = self.ventas[-1]["id"]
        
        return ultimo_id + 1

    def registrar_venta(
        self,
        items,
        subtotal,
        iva,
        descuento,
        total,
        metodo_pago,
        es_socio
    ):
        nueva_venta = {
            "id": self.generar_id(),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": items,
            "subtotal": subtotal,
            "iva": iva,
            "descuento": descuento,
            "total": total,
            "metodo_pago" : metodo_pago,
            "es_socio": es_socio
        }
        
        self.ventas.append(nueva_venta)
        self.guardar()