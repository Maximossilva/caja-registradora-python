import json
import os
from inventario import Inventario
from socio import Socio
from database.init_db import init_database
from database import producto_repository
from config import PATH_SOCIOS, PATH_VENTAS
from pathlib import Path


def migrar_productos():
    """Migra productos desde JSON a SQLite"""
    print("🔄 Migrando productos...")
    inventario = Inventario()
    
    for producto in inventario.productos.values():
        try:
            producto_repository.crear_producto_con_stock(
                producto.nombre, 
                producto.precio, 
                producto.stock
            )
            print(f"  ✓ {producto.nombre}")
        except Exception as e:
            print(f"  ❌ {producto.nombre}: {e}")
    
    print("✓ Productos migrados\n")


def migrar_socios():
    """Migra socios desde JSON a SQLite"""
    print("🔄 Migrando socios...")
    
    # Cargar socios desde JSON
    try:
        with open(PATH_SOCIOS, "r", encoding="utf-8") as f:
            socios_data = json.load(f)
    except FileNotFoundError:
        print("⚠️  No se encontró archivo de socios. Saltando.\n")
        return
    
    for socio_data in socios_data:
        try:
            # Crear socio
            socio_id = producto_repository.crear_socio(
                nombre=socio_data.get("usuario"),
                dni=str(socio_data.get("id_socio")),  # Usar id_socio como DNI
                password_hash=socio_data.get("password_hash"),
                descuento=socio_data.get("descuento", 10)
            )
            print(f"  ✓ {socio_data.get('usuario')} (ID: {socio_id})")
        except Exception as e:
            # Si el socio ya existe (UNIQUE dni), saltarlo
            if "UNIQUE" in str(e):
                print(f"  ⚠️  {socio_data.get('usuario')} ya existe")
            else:
                print(f"  ❌ {socio_data.get('usuario')}: {e}")
    
    print("✓ Socios migrados\n")


def migrar_ventas():
    """Migra ventas desde JSON a SQLite"""
    print("🔄 Migrando ventas...")
    
    # Cargar ventas desde JSON
    try:
        with open(PATH_VENTAS, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            if not contenido:
                print("⚠️  No hay ventas para migrar.\n")
                return
            ventas_data = json.loads(contenido)
    except FileNotFoundError:
        print("⚠️  No se encontró archivo de ventas. Saltando.\n")
        return
    except json.JSONDecodeError:
        # Archivo vacío o inválido
        print("⚠️  Archivo de ventas vacío o inválido. Saltando.\n")
        return
    
    for venta_data in ventas_data:
        try:
            fecha = venta_data.get("fecha")
            total = venta_data.get("total")
            items = venta_data.get("items", [])
            es_socio = venta_data.get("es_socio", False)
            socio_id = None
            
            # Crear la venta
            venta_id = producto_repository.crear_venta(
                fecha=fecha,
                total=total,
                socio_id=socio_id,
                caja_id=1
            )
            
            # Crear items de la venta
            for item in items:
                nombre = item.get("nombre")
                precio = item.get("precio")
                cantidad = item.get("cantidad")
                
                # Obtener ID del producto
                producto_id = producto_repository.obtener_producto_id_por_nombre(nombre)
                
                if producto_id:
                    producto_repository.crear_item_venta(
                        venta_id=venta_id,
                        producto_id=producto_id,
                        cantidad=cantidad,
                        precio_unitario=precio
                    )
            
            print(f"  ✓ Venta ID {venta_id} - Total: ${total}")
        except Exception as e:
            print(f"  ❌ Venta ID {venta_data.get('id')}: {e}")
    
    print("✓ Ventas migradas\n")


def migrar_proveedores():
    """Migra proveedores y relaciones desde JSON a SQLite"""
    print("🔄 Migrando proveedores...")
    
    # Intentar cargar desde config, si no usar default
    try:
        from config import PATH_PROVEEDORES_PRODUCTOS
    except ImportError:
        PATH_PROVEEDORES_PRODUCTOS = Path("json") / "proveedores_productos.json"
    
    try:
        with open(PATH_PROVEEDORES_PRODUCTOS, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except FileNotFoundError:
        print("⚠️  No se encontró archivo de proveedores. Saltando.\n")
        return
    except json.JSONDecodeError:
        print("⚠️  Archivo de proveedores vacío o inválido. Saltando.\n")
        return
    
    proveedores_creados = set()
    relaciones_creadas = 0
    
    for row in datos:
        try:
            nombre_producto = row.get("nombre_producto")
            nombre_proveedor = row.get("nombre_proveedor")
            precio_compra = row.get("precio_compra")
            stock_disponible = row.get("stock_disponible", 0)
            
            # Obtener ID del producto
            producto_id = producto_repository.obtener_producto_id_por_nombre(nombre_producto)
            if not producto_id:
                print(f"  ⚠️  Producto '{nombre_producto}' no encontrado, saltando relación con {nombre_proveedor}")
                continue
            
            # Obtener o crear proveedor
            resultado = producto_repository.obtener_proveedor_por_nombre(nombre_proveedor)
            if resultado:
                proveedor_id, _ = resultado
            else:
                proveedor_id = producto_repository.crear_proveedor(nombre_proveedor)
                proveedores_creados.add(nombre_proveedor)
            
            # Crear relación
            try:
                producto_repository.crear_relacion_producto_proveedor(
                    producto_id=producto_id,
                    proveedor_id=proveedor_id,
                    precio_compra=precio_compra,
                    stock_inicial=stock_disponible
                )
                relaciones_creadas += 1
                print(f"  ✓ {nombre_proveedor} → {nombre_producto}")
            except Exception as e:
                if "UNIQUE" in str(e):
                    print(f"  ⚠️  {nombre_proveedor} → {nombre_producto} ya existe")
                else:
                    print(f"  ❌ {nombre_proveedor} → {nombre_producto}: {e}")
        
        except Exception as e:
            print(f"  ❌ Error procesando relación: {e}")
    
    print(f"✓ Proveedores migrados ({len(proveedores_creados)} proveedores, {relaciones_creadas} relaciones)\n")


def migrar():
    """Ejecuta todas las migraciones"""
    print("""
╔════════════════════════════════════════╗
║  MIGRACIÓN DE JSON A SQLITE            ║
╚════════════════════════════════════════╝
""")
    
    # 1. Inicializar base de datos
    print("🔄 Inicializando base de datos...")
    init_database()
    print("✓ Base de datos inicializada\n")
    
    # 2. Migrar productos
    migrar_productos()
    
    # 3. Migrar socios
    migrar_socios()
    
    # 4. Migrar ventas
    migrar_ventas()
    
    # 5. Migrar proveedores
    migrar_proveedores()
    
    print("""
╔════════════════════════════════════════╗
║  ✓ MIGRACIÓN COMPLETADA               ║
╚════════════════════════════════════════╝
""")


if __name__ == "__main__":
    migrar()
