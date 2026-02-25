# ticket.py (NUEVO ARCHIVO)

from datetime import datetime


class Ticket:
    """
    Genera tickets de venta.
    
    ¿Por qué clase separada?
    - Separación de responsabilidades: SesionVenta no debe saber cómo se imprime
    - Reutilizable: Puedes generar ticket de venta antigua sin recrear sesión
    - Testeable: Puedes probar generación de ticket sin todo el flujo de venta
    """
    
    def __init__(self, items, subtotal, iva, descuento, total, metodo_pago, fecha=None):
        """
        Args:
            items (list): Lista de dict con {"nombre", "precio", "cantidad"}
            subtotal (float): Subtotal sin IVA ni descuentos
            iva (float): Monto de IVA
            descuento (float): Monto de descuento aplicado
            total (float): Total final
            metodo_pago (str): "efectivo" o "tarjeta"
            fecha (datetime): Fecha de la venta (si None, usa ahora)
        """
        self.items = items
        self.subtotal = subtotal
        self.iva = iva
        self.descuento = descuento
        self.total = total
        self.metodo_pago = metodo_pago
        self.fecha = fecha or datetime.now()  # Si no se pasa, usa fecha actual
    
    def generar_texto(self):
        """
        Genera el texto del ticket.
        
        ¿Por qué retornar string en vez de imprimir directo?
        - Flexibilidad: Puedes imprimirlo, guardarlo en archivo, enviarlo por email
        - Testeable: Puedes verificar el contenido sin capturar stdout
        
        Returns:
            str: Texto completo del ticket
        """
        lineas = []
        
        # Encabezado
        lineas.append("=" * 50)
        lineas.append("             TICKET DE VENTA")
        lineas.append("=" * 50)
        lineas.append(f"Fecha: {self.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
        lineas.append("-" * 50)
        
        # Items
        for item in self.items:
            nombre = item['nombre']
            precio = item['precio']
            cantidad = item['cantidad']
            subtotal_item = precio * cantidad
            
            lineas.append(f"{cantidad}x {nombre.capitalize()}")
            lineas.append(f"   ${precio:.2f} c/u = ${subtotal_item:.2f}")
        
        lineas.append("-" * 50)
        
        # Totales
        lineas.append(f"Subtotal:        ${self.subtotal:>10.2f}")
        
        if self.descuento > 0:
            lineas.append(f"Descuento:      -${self.descuento:>10.2f}")
        
        lineas.append(f"IVA (21%):       ${self.iva:>10.2f}")
        
        if self.metodo_pago == "tarjeta":
            recargo = self.total - (self.subtotal - self.descuento + self.iva)
            lineas.append(f"Recargo tarjeta: ${recargo:>10.2f}")
        
        lineas.append("-" * 50)
        lineas.append(f"TOTAL:           ${self.total:>10.2f}")
        lineas.append(f"Método: {self.metodo_pago.capitalize()}")
        lineas.append("=" * 50)
        lineas.append("       Gracias por su compra")
        lineas.append("=" * 50)
        
        return "\n".join(lineas)
    
    def imprimir(self):
        """Imprime el ticket en consola."""
        print(self.generar_texto())
    
    def guardar_archivo(self, nombre_archivo):
        """
        Guarda el ticket en un archivo de texto.
        
        Útil para:
        - Enviar por email
        - Archivar ventas
        - Imprimir después
        """
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(self.generar_texto())