from pathlib import Path


# Directorio base del proyecto (donde están los .py principales)
BASE_DIR = Path(__file__).resolve().parent

# Carpeta donde se guardan los archivos de datos (.json)
DATA_DIR = BASE_DIR / "json"

# Rutas completas a cada archivo JSON que usa la aplicación
PATH_PRODUCTOS = DATA_DIR / "productos.json"
PATH_VENTAS = DATA_DIR / "ventas.json"
PATH_SOCIOS = DATA_DIR / "socios.json"
# Relaciones producto–proveedor (precio_compra, stock_disponible). Cargado por GestorProveedor.
PATH_PROVEEDORES_PRODUCTOS = DATA_DIR / "proveedores_productos.json"

