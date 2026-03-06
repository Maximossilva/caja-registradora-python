# gestor_proveedor.py
#
# Gestiona relaciones producto-proveedor desde SQLite.
# Usa las tablas supplier y product_supplier del nuevo schema.

from database import producto_repository
from producto_proveedor import ProductoProveedor
from proveedor import Proveedor


class GestorProveedor:
    """
    Gestiona relaciones producto-proveedor desde SQLite.
    Usa las tablas supplier y product_supplier (antes: proveedor y producto_proveedor).
    """

    def __init__(self, inventario):
        # inventario: InventarioSQLite (para búsquedas de productos)
        self.inventario = inventario
        self.relaciones = []
        self._proveedores_cache = {}
        self._cargar()

    def _cargar(self):
        """Carga todas las relaciones desde SQLite usando tablas en inglés"""
        self.relaciones = []
        self._proveedores_cache = {}

        # Obtener todos los proveedores activos (tabla supplier)
        todos_proveedores = producto_repository.get_all_suppliers()

        for proveedor_id, nombre_proveedor in todos_proveedores:
            # Crear objeto Proveedor una sola vez
            proveedor_obj = Proveedor(nombre_proveedor)
            proveedor_obj.id = proveedor_id
            self._proveedores_cache[nombre_proveedor] = proveedor_obj

            # Obtener relaciones de este proveedor (tabla product_supplier)
            relaciones_bd = producto_repository.get_relations_by_supplier(proveedor_id)

            for relacion_id, producto_id, nombre_producto, precio_compra, stock_disponible in relaciones_bd:
                # Obtener objeto Producto desde el inventario
                producto = self.inventario.obtener_producto(nombre_producto)

                if producto:
                    rel = ProductoProveedor(
                        producto=producto,
                        proveedor=proveedor_obj,
                        precio_compra=precio_compra,
                        stock_disponible=stock_disponible
                    )
                    rel.id_relacion = relacion_id
                    self.relaciones.append(rel)

    def guardar(self):
        """
        Persiste cambios en la BD.
        Usa set_supplier_stock para actualizar stock del proveedor.
        """
        for rel in self.relaciones:
            if hasattr(rel, 'id_relacion'):
                producto_repository.set_supplier_stock(
                    rel.id_relacion,
                    rel.stock_disponible
                )

    def agregar_relacion(self, nombre_producto, nombre_proveedor, precio_compra, stock_inicial=0):
        """Agrega una nueva relación producto-proveedor a SQLite"""
        # Obtener ID del producto global
        producto_id = producto_repository.get_product_id_by_name(nombre_producto)

        if not producto_id:
            raise ValueError(f"Producto '{nombre_producto}' no encontrado")

        # Obtener o crear proveedor (tabla supplier)
        resultado = producto_repository.get_supplier_by_name(nombre_proveedor)
        if resultado:
            proveedor_id, _ = resultado
        else:
            proveedor_id = producto_repository.create_supplier(nombre_proveedor)

        # Crear relación en BD (tabla product_supplier)
        relacion_id = producto_repository.create_product_supplier_relation(
            product_id=producto_id,
            supplier_id=proveedor_id,
            purchase_price=precio_compra,
            initial_stock=stock_inicial
        )

        # Agregar a la lista en memoria
        producto = self.inventario.obtener_producto(nombre_producto)
        if not producto:
            raise ValueError(f"No se pudo obtener producto '{nombre_producto}'")

        if nombre_proveedor not in self._proveedores_cache:
            proveedor = Proveedor(nombre_proveedor)
            proveedor.id = proveedor_id
            self._proveedores_cache[nombre_proveedor] = proveedor
        else:
            proveedor = self._proveedores_cache[nombre_proveedor]

        rel = ProductoProveedor(
            producto=producto,
            proveedor=proveedor,
            precio_compra=precio_compra,
            stock_disponible=stock_inicial
        )
        rel.id_relacion = relacion_id
        self.relaciones.append(rel)

    def buscar_por_producto(self, producto):
        """Retorna todas las relaciones (proveedores que venden este producto)"""
        return [r for r in self.relaciones if r.producto == producto]
