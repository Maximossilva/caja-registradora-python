# Plan: mejoras simples, cuándo Fase 2, carpetas, API

Este documento responde **cuándo**, **dónde** y **por qué** aplicar cada cosa, sin hacer todo de golpe.

---

## 1. Cuándo pasar a Fase 2

**Fase 2** (en la revisión arquitectónica) era: persistencia más robusta, capa de repositorios, eventualmente SQL.

- **Cuándo**: Cuando notes **límites claros** del enfoque actual, por ejemplo:
  - Varios procesos o usuarios escribiendo a la vez (múltiples cajas, o una API con varios workers).
  - Necesidad de consultas (ventas por fecha, por socio, reportes) sin cargar todo en memoria.
  - Necesidad de transacciones (por ejemplo “venta + reducir stock + ingresar caja” atómico).

- **Antes de Fase 2** conviene:
  - Tener los flujos actuales estables (cliente en `main.py`, gerente en `main_gerente.py`).
  - Tener datos de prueba y persistencia JSON clara (productos, ventas, socios, proveedores_productos).
  - Haber probado bien la lógica (tests unitarios opcionales pero útiles).

No hace falta Fase 2 solo por “orden”: si un solo usuario usa la app y los JSON te alcanzan, puedes quedarte en Fase 1 y solo ir a Fase 2 cuando el uso real lo pida.

---

## 2. Carpetas (dominio, infraestructura, etc.)

**Idea**: Separar en carpetas tipo `dominio/`, `infraestructura/`, `aplicacion/` para que el código esté más ordenado.

- **Cuándo**: **Después** de tener más módulos y una frontera clara. Por ejemplo:
  - Cuando añadas una capa de API (FastAPI/Flask) y quieras separar “rutas” de “servicios”.
  - Cuando tengas varios repositorios (Inventario, RegistroVentas, GestorProveedor, etc.) y quieras agruparlos en `infraestructura/`.

- **Por qué no obligatorio ahora**: Con pocos archivos en la raíz, mover todo a carpetas implica cambiar muchos `import` y puede romper cosas sin aportar mucho todavía. La ganancia es sobre todo de **navegación** cuando el proyecto crece.

- **Recomendación**: Mantener la estructura actual hasta que tengas, por ejemplo, API o más de un “caso de uso” por capa. Ahí sí tiene sentido algo como:
  - `dominio/` → producto, socio, caja, carrito, proveedor, producto_proveedor
  - `aplicacion/` → sesion_venta, servicio_compra
  - `infraestructura/` → inventario, registro_ventas, registro_socio, gestor_proveedor
  - `entrada/` o `interfaz/` → main.py, main_gerente.py (y luego rutas API)

---

## 3. API REST: qué es, para qué sirve, cuándo implementarla

**Qué es**: Una capa que expone la misma lógica de negocio por **HTTP**: un cliente (navegador, app móvil, otro sistema) envía peticiones (GET/POST) y recibe JSON en lugar de usar la consola.

**Para qué sirve**:
  - Que un **frontend web** o una **app** consuma ventas, productos, reposición, etc. sin reescribir la lógica.
  - Que la misma lógica sirva para **varios clientes** (CLI, web, móvil).
  - Integrar con otros sistemas (contabilidad, reportes) vía HTTP.

**Cuándo implementarla**:
  - Cuando tengas un **cliente concreto** (pantalla web, app) o la necesidad explícita de “acceder desde fuera” (otro programa, otro equipo).
  - No es obligatorio antes de tener ese cliente; hacer una API “por si acaso” sin uso real suele generar código muerto.

**Cómo se implementaría** (sin hacerlo aún):
  - Se mantienen **igual** las clases de dominio y los servicios (SesionVenta, ServicioCompra). No imprimen; devuelven resultados o lanzan excepciones.
  - Se añade un **nuevo** punto de entrada (por ejemplo con FastAPI) que:
    - Recibe peticiones (ej. POST /reponer con { "producto": "Arroz Dia 500g", "cantidad": 10 }).
    - Construye inventario, caja, gestor_proveedor, servicio_compra (o los inyecta).
    - Llama a `servicio_compra.reponer_producto(producto, cantidad)`.
    - Convierte el resultado o la excepción en JSON y código HTTP (200, 400, etc.).
  - Así la **lógica** sigue en una sola capa (servicios) y la API es solo “traductor” HTTP ↔ servicios.

---

## 4. Mejoras simples del punto 5: cuándo / dónde / por qué

(Referencia: “Mejoras simples recomendadas” en REVISION_REPOSICION.md.)

| Mejora | Cuándo | Dónde | Por qué |
|--------|--------|--------|---------|
| **Persistencia stock proveedores** | Ya aplicada | `GestorProveedor` + `json/proveedores_productos.json` | Sin datos ni persistencia no se puede “saber si el proveedor tiene stock”. Ahora hay un JSON con relaciones (producto, proveedor, precio, stock) que se carga al iniciar y se guarda tras reponer o agregar relación. |
| **Reponer por búsqueda** | Cuando uses el flujo gerente con muchos productos | `main_gerente.py`: usar `inventario.buscar_por_nombre(texto)` y, si hay varios, mostrar lista y que el usuario elija | Mejora UX; no es crítica si repones pocos productos o por nombre exacto. |
| **Validar cantidad en ServicioCompra** | Ya aplicada | `servicio_compra.reponer_producto` al inicio | El servicio debe ser defensivo aunque la UI también valide. |
| **Estilo Proveedor.from_dict** | Opcional, cuando toques ese archivo | `proveedor.py`: `data.get("nombre", "")` si quieres default | Solo consistencia; no cambia comportamiento. |

---

## 5. UTF-8 en productos.json (La Serenísima)

**Problema**: En el JSON, “Serenísima” aparecía como `Seren\u00c3\u00adsima` (mojibake: la “í” guardada como dos bytes interpretados mal).

**Qué se hizo**:
  - Reemplazo en `productos.json` de ese texto por `Serenísima` correcto.
  - En **lectura/escritura** de JSON (Inventario, RegistroVentas, GestorProveedor, etc.) se usa siempre `encoding="utf-8"` en `open()` y, donde corresponda, `ensure_ascii=False` en `json.dump` para que tildes y eñes se guarden legibles.

**Por qué**: En Windows a veces el default de `open()` no es UTF-8; si guardas sin indicar encoding, las tildes pueden corromperse. Fijar UTF-8 en todos los puntos que tocan JSON evita que vuelva a pasar.

---

## 6. Cómo sabemos si el proveedor tiene stock (datos iniciales)

**Problema**: Si no hay ningún dato que diga “qué productos tiene cada proveedor y cuánto”, no se puede reponer.

**Qué se hizo**:
  - **Archivo** `json/proveedores_productos.json` con una lista de relaciones: `nombre_producto`, `nombre_proveedor`, `precio_compra`, `stock_disponible`.
  - **GestorProveedor** recibe `inventario` y la ruta de ese archivo. En `_cargar()`:
    - Lee el JSON.
    - Para cada fila, obtiene el `Producto` con `inventario.obtener_producto(nombre_producto)` (solo se cargan productos que existan en inventario).
    - Crea o reutiliza un `Proveedor` por nombre (cache `_proveedores`).
    - Arma `ProductoProveedor` y lo añade a `relaciones`.
  - Tras **reponer** (o agregar relación), quien use el servicio debe llamar `gestor_proveedor.guardar()` para persistir el `stock_disponible` actualizado.

**Alternativa no elegida**: Un dict hardcodeado en código. Rechazado porque los datos crecen y es mejor tenerlos en un archivo (fácil de editar, versionar y reemplazar por BD después).

Con esto tienes **datos iniciales** y **persistencia** del stock de proveedor. Para probar reponer: tener al menos una fila en `proveedores_productos.json` cuyo producto exista en `productos.json` y dar saldo a la caja. En `main_gerente.py` la caja empieza en 0 cada vez; para pruebas puedes descomentar `caja.ingresar(50000)` al inicio o, en el futuro, cargar la caja desde un archivo si la compartes entre procesos.
