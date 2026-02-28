import json
from pathlib import Path

from producto_proveedor import ProductoProveedor
from proveedor import Proveedor

# Ruta por defecto; se puede inyectar para tests o otro entorno.
try:
    from config import PATH_PROVEEDORES_PRODUCTOS
except ImportError:
    PATH_PROVEEDORES_PRODUCTOS = Path("json") / "proveedores_productos.json"


class GestorProveedor:
    """
    Mantiene las relaciones producto–proveedor (quién vende qué, a qué precio y con qué stock).
    Carga y guarda en JSON: así hay datos iniciales y el stock del proveedor persiste tras reponer.
    """

    def __init__(self, inventario, archivo=PATH_PROVEEDORES_PRODUCTOS):
        # inventario: para resolver nombre_producto (string en JSON) -> objeto Producto al cargar.
        self.inventario = inventario
        self.archivo = Path(archivo) if isinstance(archivo, str) else archivo
        self.relaciones = []
        self._proveedores = {}  # nombre_proveedor -> Proveedor (reutilizar misma instancia)
        self._cargar()

    def _cargar(self):
        """Carga relaciones desde JSON. Solo incluye filas cuyo producto exista en inventario."""
        try:
            with open(self.archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except FileNotFoundError:
            return
        for row in datos:
            nombre_producto = row.get("nombre_producto")
            nombre_proveedor = row.get("nombre_proveedor")
            producto = self.inventario.obtener_producto(nombre_producto) if nombre_producto else None
            if producto is None:
                continue
            proveedor = self._proveedores.get(nombre_proveedor)
            if proveedor is None:
                proveedor = Proveedor(nombre_proveedor)
                self._proveedores[nombre_proveedor] = proveedor
            rel = ProductoProveedor(
                producto, proveedor,
                row["precio_compra"],
                row["stock_disponible"]
            )
            self.relaciones.append(rel)

    def guardar(self):
        """Persiste relaciones (incluido stock actual) en JSON. Llamar tras reponer o agregar_relacion."""
        # ensure_ascii=False para que "Serenísima" etc. se guarden como UTF-8 legible, no \u00ed.
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "nombre_producto": r.producto.nombre,
                        "nombre_proveedor": r.proveedor.nombre,
                        "precio_compra": r.precio_compra,
                        "stock_disponible": r.stock_disponible,
                    }
                    for r in self.relaciones
                ],
                f, indent=2, ensure_ascii=False
            )

    def agregar_relacion(self, producto, proveedor, precio, stock):
        relacion = ProductoProveedor(producto, proveedor, precio, stock)
        self.relaciones.append(relacion)
        if proveedor.nombre not in self._proveedores:
            self._proveedores[proveedor.nombre] = proveedor
        self.guardar()

    def buscar_por_producto(self, producto):
        return [r for r in self.relaciones if r.producto == producto]