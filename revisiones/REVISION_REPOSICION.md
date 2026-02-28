# Revisión: lógica de reposición de stock

## 1. Resumen

- **Lógica de negocio**: correcta (elegir proveedor más barato con stock, retirar de caja, descontar al proveedor, agregar al producto).
- Se corrigieron **bugs** en `ServicioCompra` y en `main.py` que impedían que funcionara bien.
- El **diseño** respeta responsabilidad única y separación de capas; se sugieren mejoras menores.

---

## 2. Errores corregidos

### 2.1. `ServicioCompra.reponer_producto`

| Problema | Antes | Después |
|----------|------|--------|
| **Validación de “sin proveedores” vs “sin stock”** | Solo se comprobaba `if not relacion`. Si había relaciones pero ninguna con stock, `relacion_valida` quedaba vacía y `min(relacion_valida, ...)` lanzaba `ValueError` poco claro. | Se distingue: `if not relaciones` → “No hay proveedores para el producto”; `if not con_stock` → “Ningún proveedor tiene stock suficiente”. |
| **Atributo inexistente** | Se usaba `self.capital`, que no existe en `ServicioCompra`. | Se usa `self.caja.saldo_actual()` para validar saldo antes de retirar. |
| **Mensaje de error de capital** | N/A | Se indica cuánto hace falta y cuánto hay en caja. |

### 2.2. `main.py`

| Problema | Antes | Después |
|----------|------|--------|
| **Construcción de `ServicioCompra`** | `ServicioCompra()` sin argumentos, pero el constructor exige `(gestor_proveedor, caja)` → fallo en ejecución. | Se crean `caja` y `gestor_proveedor` antes y se pasa `ServicioCompra(gestor_proveedor, caja)`. |
| **Ingreso en caja** | `Caja.ingresar(total)` (método de clase sin instancia). | `caja.ingresar(total)` sobre la instancia `caja`. |
| **Ticket vacío** | Se llamaba a `confirmar_pago` (que vacía el carrito) y después se hacía `items_dict = [item.to_dict() for item in carrito.listar()]`, por lo que el ticket siempre salía vacío. | Se obtienen y guardan `items_para_ticket` y totales **antes** de `confirmar_pago`; el ticket se arma con esos datos. |
| **Reposición en el flujo de venta** | `servicio_compra.reponer_producto(texto, 10)` dentro de “finalizar compra”: `texto` no es un `Producto` y no tiene sentido reponer automáticamente ahí. | Reposición movida a una opción de menú propia (“4. Reponer stock”) que pide producto (por nombre) y cantidad, obtiene el `Producto` con `inventario.obtener_producto`, llama a `reponer_producto(producto, cantidad)` y luego `inventario.guardar()`. |

---

## 3. Diseño y responsabilidades

### 3.1. Lo que está bien

- **Caja**: solo saldo e ingresar/retirar; valida saldo en `retirar`. Responsabilidad clara.
- **Producto**: `agregar_stock` sin lógica de negocio extra; coherente con el resto del dominio.
- **ProductoProveedor**: relación producto–proveedor con precio y stock; `hay_stock` y `descontar_stock` encapsulan la regla. Bien.
- **GestorProveedor**: mantiene la lista de relaciones y las filtra por producto. No sabe de caja ni de inventario. Correcto.
- **ServicioCompra**: orquesta “reponer”: busca relaciones, filtra por stock, elige más barato, valida caja, retira, descuenta proveedor, agrega stock al producto. Una sola responsabilidad (caso de uso de compra a proveedor).

### 3.2. Separación de capas

- **Dominio**: Caja, Producto, Proveedor, ProductoProveedor (reglas y datos).
- **Aplicación**: ServicioCompra (caso de uso).
- **Infraestructura / datos**: GestorProveedor (hoy en memoria; luego podría ser repositorio).
- **Entrada**: main (menú y llamadas a servicios).

Las dependencias van en la dirección correcta: main → ServicioCompra → GestorProveedor, Caja, Producto. No hay dependencias invertidas.

### 3.3. Mejora opcional: orden de operaciones y transacciones

En `reponer_producto` se hace: retirar de caja → descontar stock proveedor → agregar stock al producto. Si falla un paso posterior al retiro, la caja ya se modificó. Con todo en memoria no hay transacción; es aceptable para este alcance. Si más adelante uses base de datos, convendría un flujo transaccional (o compensación) para que “retirar + descontar + agregar” sea atómico.

---

## 4. Buenas prácticas

- Inyección de dependencias: `ServicioCompra(gestor_proveedor, caja)` permite probar con mocks.
- Validaciones en el lugar adecuado: saldo en Caja/retirar, stock en ProductoProveedor/descontar_stock; ServicioCompra solo orquesta y valida “hay al menos un proveedor con stock” y “caja alcanza”.
- Mensajes de error claros y diferenciados (sin proveedores / sin stock / capital insuficiente).

---

## 5. Mejoras simples recomendadas (antes de más funcionalidades)

1. **Persistencia del stock de proveedores**  
   Hoy `GestorProveedor` y sus `ProductoProveedor` están solo en memoria. Si reinicias la app, el `stock_disponible` que descontaste se “recupera”. Cuando quieras que la reposición sea persistente, habrá que guardar/cargar esas relaciones (por ejemplo en JSON, como productos y ventas).

2. **Reponer por búsqueda (opcional)**  
   En “4. Reponer stock” se pide el nombre exacto. Para homogeneizar con “Agregar producto”, podrías usar `inventario.buscar_por_nombre(texto)` y, si hay varios resultados, mostrar lista y que el usuario elija uno.

3. **Validar `cantidad > 0` en `ServicioCompra`**  
   Aunque main ya lo comprueba, por defensa podrías al inicio de `reponer_producto` hacer `if cantidad <= 0: raise ValueError("La cantidad debe ser positiva")`.

4. **Estilo en `Proveedor.from_dict`**  
   `Proveedor(data["nombre"],)` tiene una coma final; es válido en Python. Si quieres uniformidad con el resto del proyecto, puedes usar `data.get("nombre")` y un default si aplica.

---

## 6. Cómo comprobar que todo está estable

1. **Ejecutar el flujo de venta** (`python main.py`): opciones 1, 2, 3. Confirmar que el ticket muestra ítems y totales y que la caja ingresa el total.
2. **Datos de proveedores**: en `json/proveedores_productos.json` debe haber al menos una fila con `nombre_producto` que exista en el inventario (y `nombre_proveedor`, `precio_compra`, `stock_disponible`). El `GestorProveedor` los carga al iniciar.
3. **Reponer (flujo gerente)**: `python main_gerente.py`. Dar saldo a la caja antes (por ejemplo con un script que haga `caja.ingresar(monto)` o tras una venta en main). Reponer por nombre exacto del producto: debe restar de caja, bajar stock del proveedor y subir stock del producto; tras reponer se llama `gestor_proveedor.guardar()` e `inventario.guardar()`.

La reposición **no** está en el menú de `main.py` (flujo cliente); está en `main_gerente.py`. Ver también **PLAN_MEJORAS_Y_FASE2.md** para cuándo Fase 2, carpetas, API y mejoras.
