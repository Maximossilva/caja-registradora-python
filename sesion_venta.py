# sesion_venta.py

from datetime import datetime


class SesionVenta:
    """
    Orquesta el flujo completo de una venta.
    
    Responsabilidades:
    - Validar stock ANTES de agregar al carrito
    - Calcular totales con orden claro (subtotal → descuento → IVA → recargo)
    - Confirmar pago y reducir stock
    - Generar ticket
    """
    
    # Constantes de la clase (compartidas por todas las instancias)
    DESCUENTO_SOCIO = 0.10  # 10%
    IVA = 0.21              # 21%
    RECARGO_TARJETA = 0.10  # 10%
    
    def __init__(self, inventario, registro_venta, metodo_pago=None):
        """
        Args:
            inventario (Inventario): Gestiona productos y stock
            registro_venta (RegistroVentas): Guarda ventas en JSON
            metodo_pago (str): "efectivo" o "tarjeta" (opcional)
        """
        self.inventario = inventario
        self.registro_venta = registro_venta
        self.carrito = None
        self.venta_cerrada = False
        self.metodo_pago = metodo_pago
    
    def iniciar_venta(self, carrito):
        """
        Inicia una nueva sesión de venta.
        
        ¿Por qué recibir carrito como parámetro?
        - Flexibilidad: puedes pasar un carrito existente o uno nuevo
        - Testing: puedes inyectar un carrito mock
        """
        self.carrito = carrito
        self.venta_cerrada = False
    
    def agregar_producto(self, nombre_producto, cantidad):
        """
        Agrega producto al carrito CON VALIDACIÓN de stock.
        
        FLUJO:
        1. Busca el producto en el inventario
        2. Valida que existe
        3. Valida que hay stock suficiente (considerando lo que ya hay en el carrito)
        4. Si todo OK, lo agrega al carrito
        
        Args:
            nombre_producto (str): Nombre del producto
            cantidad (int): Cantidad a agregar
        
        Returns:
            bool: True si se agregó, False si hubo error
        """
        # 1. Obtener el OBJETO Producto del inventario
        producto = self.inventario.obtener_producto(nombre_producto)
        
        # 2. Validar que existe
        if not producto:
            print(f"❌ Producto '{nombre_producto}' no encontrado.")
            return False
        
        # 3. Calcular cuánto queremos en total (lo del carrito + lo nuevo)
        cantidad_en_carrito = 0
        if nombre_producto in self.carrito.items:
            cantidad_en_carrito = self.carrito.items[nombre_producto].cantidad
        
        cantidad_total_deseada = cantidad_en_carrito + cantidad
        
        # 4. Validar stock disponible
        if producto.stock < cantidad_total_deseada:
            print(f"❌ Stock insuficiente de {nombre_producto}.")
            print(f"   Disponible: {producto.stock}")
            print(f"   Ya en carrito: {cantidad_en_carrito}")
            print(f"   Solicitado: {cantidad}")
            return False
        
        # 5. Todo OK → Agregar al carrito
        # IMPORTANTE: Pasamos el OBJETO producto, no solo el nombre
        self.carrito.agregar(producto, cantidad)
        return True
    
    def establecer_metodo_pago(self, metodo):
        """
        Establece el método de pago.
        
        Args:
            metodo (str): "efectivo" o "tarjeta"
        """
        if metodo not in ["efectivo", "tarjeta"]:
            raise ValueError(f"Método de pago inválido: {metodo}")
        
        self.metodo_pago = metodo
    
    def calcular_totales(self, socio=None):
        """
        Calcula totales con ORDEN CLARO.
        
        ORDEN CORRECTO (según normativa fiscal argentina):
        1. Subtotal (suma de items SIN nada)
        2. Descuento de socio sobre subtotal
        3. IVA sobre (subtotal - descuento)
        4. Recargo de tarjeta sobre total con IVA
        
        Args:
            socio (Socio): Objeto socio si es cliente VIP, None si no
        
        Returns:
            tuple: (subtotal, iva, descuento, total)
        """
        # 1. SUBTOTAL: Suma de todos los items (precio * cantidad)
        subtotal = self.carrito.calcular_subtotal()
        
        # 2. DESCUENTO DE SOCIO (sobre subtotal)
        descuento = 0
        if socio:
            # descuento es un porcentaje (ej: 10)
            descuento = subtotal * (socio.descuento / 100)
        
        # Subtotal después de aplicar descuento
        subtotal_con_descuento = subtotal - descuento
        
        # 3. IVA (sobre subtotal ya descontado)
        iva = subtotal_con_descuento * self.IVA
        
        # 4. TOTAL antes de recargo
        total = subtotal_con_descuento + iva
        
        # 5. RECARGO DE TARJETA (sobre total con IVA)
        if self.metodo_pago == "tarjeta":
            recargo = total * self.RECARGO_TARJETA
            total += recargo
        
        # Redondear a 2 decimales
        return (
            round(subtotal, 2),
            round(iva, 2),
            round(descuento, 2),
            round(total, 2)
        )
    
    def confirmar_pago(self, metodo_pago, socio=None):
        """
        Confirma el pago y cierra la venta.
        
        FLUJO:
        1. Valida que no esté cerrada
        2. Valida que hay items
        3. Calcula totales
        4. Reduce stock en inventario (SI FALLA, lanza excepción)
        5. Registra venta en JSON
        6. Vacía carrito y marca como cerrada
        
        ¿Por qué NO validamos stock aquí?
        - Ya se validó en agregar_producto()
        - Si falla reducir_stock(), Producto.reducir_stock() lanza excepción automáticamente
        - ELIMINAMOS validación duplicada
        
        Returns:
            tuple: (subtotal, iva, descuento, total)
        """
        # 1. Validar que no esté cerrada
        if self.venta_cerrada:
            raise ValueError("La venta ya fue confirmada.")
        
        # 2. Validar que hay items
        if self.carrito.esta_vacio():
            raise ValueError("No hay productos en el carrito.")
        
        # 3. Establecer método de pago
        self.metodo_pago = metodo_pago
        
        # 4. Calcular totales
        subtotal, iva, descuento, total = self.calcular_totales(socio)
        
        # 5. Reducir stock (si falla, producto.reducir_stock() lanza ValueError)
        for item in self.carrito.listar():
            # ELIMINADO: Validación duplicada de stock
            # Ya se validó en agregar_producto()
            # Si no hay stock, reducir_stock() lanzará excepción
            self.inventario.reducir_stock(item.producto.nombre, item.cantidad)
        
        # 6. Registrar venta en JSON
        # Convertimos items a dict para guardar (snapshot del momento)
        items_dict = [item.to_dict() for item in self.carrito.listar()]
        
        self.registro_venta.registrar_venta(
            items=items_dict,
            subtotal=subtotal,
            iva=iva,
            descuento=descuento,
            total=total,
            metodo_pago=metodo_pago,
            es_socio=socio is not None
        )
        
        # 7. Vaciar carrito y marcar como cerrada
        self.carrito.vaciar()
        self.venta_cerrada = True
        
        return subtotal, iva, descuento, total