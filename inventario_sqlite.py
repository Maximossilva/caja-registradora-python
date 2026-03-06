# inventario_sqlite.py
#
# Gestiona el inventario de productos para una sucursal específica.
# Usa branch_product para obtener precio, stock y estado por sucursal.

from database import producto_repository
from producto import Producto


class InventarioSQLite:
    """
    Inventario vinculado a una sucursal.
    Cada instancia trabaja con un branch_id específico,
    así las queries solo traen productos de esa sucursal.
    """

    def __init__(self, branch_id=1):
        # La sucursal con la que trabaja este inventario
        self.branch_id = branch_id

    def mostrar_productos(self):
        """
        Muestra todos los productos activos en la sucursal actual.
        Precio y stock vienen de branch_product (no de product).
        """
        productos = producto_repository.get_active_products(self.branch_id)
        for name, price, stock in productos:
            print(f"{name} - Precio: ${price:.2f}")     

    def vender_producto(self, texto, cantidad=0):   
        """
        Búsqueda parcial de productos por nombre en la sucursal actual.
        Solo retorna productos activos en esta sucursal.

        Args:
            texto (str): Texto para buscar parcialmente
            cantidad (int): Ignorado (para compatibilidad con main.py)

        Returns:
            list: Lista de nombres de productos que coinciden
        """
        return producto_repository.search_by_name(texto, self.branch_id)

    def obtener_producto(self, nombre):
        """
        Obtiene un producto por nombre exacto en la sucursal actual.
        El precio viene de branch_product.price (no de product, que no tiene precio).

        Args:
            nombre (str): Nombre exacto del producto

        Returns:
            Producto: Objeto Producto si existe y está activo, None si no
        """
        producto = producto_repository.get_product_by_name(nombre, self.branch_id)

        if not producto:
            return None

        id_, name, price, stock = producto
        return Producto(nombre=name, precio=price, stock=stock)

    def aumentar_stock(self, nombre, cantidad):
        """
        Aumenta el stock de un producto en la sucursal actual.
        Modifica branch_product.stock sumando la cantidad.
        """
        if cantidad <= 0:
            raise ValueError("La cantidad a aumentar debe ser positiva.")

        rows = producto_repository.update_branch_product_stock(
            self.branch_id, nombre, cantidad  # positivo = aumentar
        )

        if rows == 0:
            raise ValueError(
                f"Producto '{nombre}' no encontrado (o sin stock en sucursal {self.branch_id})."
            )

    def disminuir_stock(self, nombre, cantidad):
        """
        Disminuye el stock de un producto en la sucursal actual.
        Valida que hay stock suficiente antes de restar.
        """
        if cantidad <= 0:
            raise ValueError("La cantidad a disminuir debe ser positiva.")

        # Verificar stock actual antes de reducir
        stock_actual = producto_repository.get_branch_product_stock(
            self.branch_id, nombre
        )

        if stock_actual is None:
            raise ValueError(
                f"Producto '{nombre}' no encontrado (o sin stock en sucursal {self.branch_id})."
            )

        if stock_actual < cantidad:
            raise ValueError(
                f"Stock insuficiente de {nombre}. Disponible: {stock_actual}, solicitado: {cantidad}."
            )

        rows = producto_repository.update_branch_product_stock(
            self.branch_id, nombre, -cantidad  # negativo = reducir
        )

        if rows == 0:
            raise ValueError(
                f"No se pudo actualizar stock de '{nombre}' en sucursal {self.branch_id}."
            )

    # Alias para compatibilidad con el resto del proyecto
    def reducir_stock(self, nombre, cantidad):
        self.disminuir_stock(nombre, cantidad)