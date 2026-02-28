# Revisión arquitectónica – Caja registradora / Supermercado (Python)

Este documento resume la revisión de la arquitectura actual, una valoración, recomendaciones y un **roadmap escalonado** para escalar el proyecto sin sobreingeniería.

---

## 1. Resumen ejecutivo

| Aspecto | Valoración (1–5) | Comentario breve |
|--------|-------------------|-------------------|
| Separación de responsabilidades | 4 | Dominios bien delimitados; algún acoplamiento en rutas y UI. |
| Calidad de código | 4 | Código legible y documentado; detalles a unificar (rutas, errores). |
| Escalabilidad actual | 3 | JSON y paths fijos limitan crecimiento; diseño permite cambiar persistencia. |
| Testabilidad | 3.5 | Lógica de negocio testeable; falta capa de abstracción para I/O. |
| Consistencia | 3.5 | Pequeñas incoherencias (rutas, formato socios) ya corregidas o señaladas. |

**Calificación global: 3.8/5** – Base sólida para un proyecto educativo o un pequeño negocio; con los pasos indicados abajo se puede escalar de forma ordenada.

---

## 2. Análisis por capas y responsabilidades

### 2.1 Modelo de dominio (entidades)

**Archivos:** `producto.py`, `socio.py`, `carrito.py` (ItemCarrito + Carrito).

**Fortalezas:**

- **Producto**: Atributos claros, `tiene_stock`, `reducir_stock`, `to_dict`/`from_dict`. La regla de negocio “no reducir si no hay stock” está en la entidad (lanza `ValueError`), que es el lugar correcto.
- **Socio**: Contraseña hasheada (SHA-256), propiedades de solo lectura, `esta_activo()` y `from_dict`/`to_dict` bien usados. Buena encapsulación.
- **ItemCarrito**: Representa “producto + cantidad” en el carrito; no duplica lógica de inventario. `calcular_subtotal()` y `to_dict()` dejan claro el contrato para tickets y persistencia.
- **Carrito**: Dict por nombre para evitar duplicados y tener agregar/actualizar en O(1). Métodos `esta_vacio()`, `listar()`, `calcular_subtotal()` dejan a `main` y a `SesionVenta` sin lógica de contenedor.

**Recomendaciones menores:**

1. **Producto**: Unificar estilo con el resto (espacios en `__init__(self,nombre,precio,stock,descuento=0.0)` → `self, nombre, precio, stock, descuento=0.0`). Opcional: que `from_dict` acepte `descuento` si en el futuro lo guardas en JSON.
2. **Ruta de archivos**: Hoy `Inventario(archivo="productos.json")` y similares asumen que el proceso se ejecuta desde la raíz del proyecto. Si los JSON están en `json/`, conviene centralizar la ruta base (por ejemplo una constante o un `pathlib.Path` en un solo módulo de configuración) y usarla en Inventario, RegistroVentas y RegistroSocio. Así no se dispersan strings "json/..." por todo el código.

**Decisión de diseño (por qué está bien así):**

- El carrito guarda **referencia al Producto** del inventario, no una copia. Así el precio y el nombre siempre son los actuales hasta el momento del cierre de venta; al confirmar, usas `to_dict()` para el “snapshot” (precio al momento de la venta). Es la opción correcta para evitar desincronización.

---

### 2.2 Lógica de aplicación (casos de uso)

**Archivo:** `sesion_venta.py` – **SesionVenta**.

**Fortalezas:**

- Una sola clase que orquesta: validar stock → agregar al carrito → método de pago → totales → confirmar pago → reducir stock → registrar venta. Responsabilidad clara: “flujo de una venta”.
- **Orden de totales** documentado y correcto: subtotal → descuento socio → IVA sobre (subtotal - descuento) → recargo tarjeta. Fácil de auditar y de cambiar si cambia la normativa.
- Constantes de clase (`DESCUENTO_SOCIO`, `IVA`, `RECARGO_TARJETA`) concentran parámetros fiscales.
- Recibe `inventario` y `registro_venta` por constructor; el carrito se inyecta en `iniciar_venta(carrito)`. Eso facilita tests con mocks.

**Punto a mejorar:**

- **Acoplamiento a la implementación del carrito:** En `agregar_producto` se usa `self.carrito.items[nombre_producto]` (acceso al dict interno). Sería más robusto que el carrito expusiera algo como `cantidad_de(nombre_producto)` que devuelva 0 si no está, y que SesionVenta solo use esa API. Así, si mañana cambias el carrito a lista u otra estructura, solo cambias Carrito y no SesionVenta.

**Por qué no poner más cosas en SesionVenta:**

- No conviene que SesionVenta imprima mensajes de error con `print`. Mejor que devuelva resultados (p. ej. un pequeño DTO o códigos de error) y que quien llame (main o una futura API) decida si imprime, registra o devuelve JSON. Así la misma lógica sirve para CLI y para API.

---

### 2.3 Persistencia (repositorios / almacenamiento)

**Archivos:** `inventario.py` (productos), `registro_ventas.py`, `registro_socio.py`.

**Fortalezas:**

- Cada “repositorio” tiene un solo archivo JSON y métodos `cargar`/`guardar`. Responsabilidad clara.
- **Inventario**: Mantiene un dict en memoria indexado por nombre; `cargar()` y `guardar()` encapsulan el formato. Uso correcto de `Producto.from_dict`/`to_dict`.
- **RegistroVentas**: Lista de ventas, ID secuencial, `registrar_venta` con todos los campos necesarios. Formato estable.
- **RegistroSocio**: Tras la corrección, `_guardar` escribe una **lista** de dicts, coherente con `_cargar`, que itera sobre esa lista. Así no se rompe al guardar y volver a cargar.

**Problemas corregidos en esta revisión:**

1. **Import erróneo** en `registro_socio.py`: se eliminó `from super import socio` (inexistente y sobrante).
2. **Inconsistencia persistencia socios**: `_guardar` escribía un objeto `{ usuario: {...} }` y `_cargar` esperaba una lista. Se unificó a lista de dicts, igual que ventas y productos.

**Recomendaciones:**

1. **Rutas de archivos**: No hardcodear `"productos.json"`, `"ventas.json"`, `"socios.json"` en cada clase. Definir una ruta base (p. ej. `json/` o una carpeta de datos) en un solo sitio y construir paths ahí. Ejemplo:

   ```python
   # config.py (o constants.py)
   from pathlib import Path
   DIR_DATOS = Path(__file__).resolve().parent / "json"
   ```

   Luego en cada repositorio usar `DIR_DATOS / "productos.json"` etc. Así, al mover el proyecto o desplegar, solo tocas un lugar.

2. **Encoding y FileNotFoundError**: En `guardar()` usar `encoding="utf-8"` en los `open()` para evitar problemas con tildes en nombres (ya se ve algún carácter raro en productos.json). Para `cargar()`, `FileNotFoundError` está bien; opcionalmente podrías loguear o tener un valor por defecto en lugar de silenciar por completo, según qué quieras para diagnóstico.

3. **Concurrencia**: Con JSON, dos procesos no deben escribir al mismo archivo a la vez. Para un solo usuario/una sola caja está bien. Cuando haya varios procesos o API con múltiples workers, será el momento de pasar a SQL o a un almacén que gestione concurrencia (ver roadmap).

---

### 2.4 Salida (ticket)

**Archivo:** `ticket.py`.

**Fortalezas:**

- Clase dedicada solo a “contenido e impresión del ticket”. `generar_texto()` devuelve un string; `imprimir()` y `guardar_archivo()` reutilizan ese string. Así se puede testear el texto sin tocar I/O y, en el futuro, enviar el mismo texto por API o a una impresora.
- Recibe datos ya calculados (items, subtotal, iva, descuento, total, metodo_pago). No depende de SesionVenta ni del carrito; solo de estructuras simples (listas de dicts, números). Buen desacoplamiento.

**Recomendación menor:**

- Si el recargo tarjeta se calcula en SesionVenta, el ticket podría recibir ya el monto de recargo en lugar de derivarlo de total/subtotal/iva (para no duplicar la fórmula). Es opcional; mientras la fórmula sea única en SesionVenta y el ticket solo “muestre” lo que recibe, es aceptable.

---

### 2.5 Orquestación y entrada (CLI)

**Archivo:** `main.py`.

**Fortalezas:**

- Crea dependencias (inventario, registro_socio, registro_ventas, carrito, sesion) y las conecta. No contiene fórmulas de IVA ni de stock; solo menú, input y llamadas a sesión/inventario/registro_socio. Buena separación.
- Flujo claro: mostrar productos, agregar producto, finalizar compra (método de pago, socio, totales, pago efectivo/tarjeta, confirmar, ticket).

**Puntos a mejorar:**

1. **Rutas de JSON**: Si los archivos están en `json/`, pasar esas rutas al construir Inventario, RegistroVentas y RegistroSocio (o usar la ruta base sugerida en config).
2. **Mensajes de error de negocio**: Hoy SesionVenta hace `print(...)` en `agregar_producto`. Idealmente SesionVenta no imprima; podría devolver un resultado (éxito/error + mensaje) y main haría el `print`. Así la lógica es reutilizable desde una API que devuelva JSON.
3. **Longitud de main**: Para mantenerlo legible, se puede extraer a funciones por caso (ej. `opcion_mostrar_productos(inventario)`, `opcion_agregar_producto(sesion, inventario)`, `opcion_finalizar_compra(...)`). Cada función recibe lo que necesita y main queda como un “menú” que solo llama a esas funciones. No es obligatorio ahora; es un siguiente paso cuando quieras añadir más opciones.

---

## 3. Diagrama de dependencias (conceptual)

```
main.py
  ├── Inventario (productos)
  ├── RegistroSocio (socios)
  ├── RegistroVentas (ventas)
  ├── Carrito
  ├── SesionVenta(inventario, registro_ventas)  → usa carrito inyectado
  └── Ticket (solo datos; no depende de sesión)

SesionVenta
  ├── Inventario (obtener_producto, reducir_stock)
  ├── Carrito (agregar, listar, calcular_subtotal, vaciar, esta_vacio)
  └── RegistroVentas (registrar_venta)

Carrito
  └── ItemCarrito(producto, cantidad)  → producto es Producto del inventario

Inventario / RegistroVentas / RegistroSocio
  └── JSON (archivos)
```

No hay dependencias circulares. El flujo es: entrada (main) → orquestación (SesionVenta) → dominio (Carrito, Producto, Socio) y persistencia (Inventario, RegistroVentas, RegistroSocio). Es una estructura que permite luego introducir una capa de servicios o de API sin rehacer todo.

---

## 4. Próximos pasos recomendados (orden sugerido)

### Fase 1 – Reforzar arquitectura y consistencia (corto plazo)

1. **Centralizar rutas de datos**
   - Crear un módulo (p. ej. `config.py`) con `DIR_DATOS = Path(__file__).resolve().parent / "json"`.
   - Pasar a Inventario, RegistroVentas y RegistroSocio el path completo (ej. `DIR_DATOS / "productos.json"`). Así no dependes del directorio de trabajo y evitas duplicar strings.
   - **Por qué:** Un solo punto de verdad para “dónde están los datos” facilita despliegue y tests (por ejemplo, usar un directorio temporal).

2. **Desacoplar mensajes de error de SesionVenta**
   - En `agregar_producto`, en lugar de `print(...)` y `return False`, devolver una tupla o un pequeño objeto, por ejemplo `(True, None)` o `(False, "Stock insuficiente de X")`.
   - En `main`, según el resultado, hacer el `print` del mensaje. SesionVenta solo decide “éxito/error” y el mensaje; la presentación queda en main.
   - **Por qué:** Reutilizar la misma lógica desde una API que devuelva JSON; además, tests unitarios no contaminan stdout.

3. **Opcional: API estable del Carrito para SesionVenta**
   - Añadir en Carrito algo como `def cantidad_de(self, nombre_producto): return self.items.get(nombre_producto).cantidad if nombre_producto in self.items else 0`.
   - En SesionVenta, usar `self.carrito.cantidad_de(nombre_producto)` en lugar de acceder a `self.carrito.items[...]`.
   - **Por qué:** Encapsular la estructura interna del carrito; menos acoplamiento y más fácil de cambiar la implementación después.

### Fase 2 – Persistencia más robusta (cuando notes límites del JSON)

4. **Mantener JSON como está** hasta que tengas al menos uno de estos requisitos:
   - Varios procesos/workers escribiendo a la vez (múltiples cajas o API con varios workers).
   - Necesidad de consultas (por fecha, por socio, por producto) sin cargar todo en memoria.
   - Necesidad de integridad transaccional (por ejemplo, “venta + reducir stock” en una sola transacción).

5. **Cuando llegue el momento de base de datos:**
   - Introducir una **capa de repositorios** con interfaces (abstractas o por convención): por ejemplo `InventarioRepository` con `obtener_producto(nombre)`, `reducir_stock(nombre, cantidad)`, `guardar()`. La implementación actual sería `InventarioRepositoryJSON`; más adelante añadirías `InventarioRepositorySQL` que hable con SQLite/Postgres.
   - El dominio (Producto, Carrito, SesionVenta) no debe conocer JSON ni SQL; solo usa “algo que me da productos y que acepta reducir stock”. Así el cambio de JSON a SQL se hace en una capa y el resto del código casi no cambia.
   - **Por qué no SQL ya:** Para un solo usuario y datos en un solo archivo, JSON es suficiente. Añadir SQL sin necesidad añade complejidad (esquema, migraciones, backups) sin beneficio inmediato.

### Fase 3 – Nuevas funcionalidades (según prioridad de negocio)

6. **Tests unitarios**
   - Prioridad: SesionVenta (cálculo de totales, validación de stock), Producto (reducir_stock, tiene_stock), Carrito (agregar, subtotal). Los repositorios se pueden mockear (objeto que devuelve listas/dicts predefinidos).
   - **Por qué ahora:** Con la estructura actual, inyectar mocks es fácil. Los tests te darán confianza al tocar persistencia o al añadir descuentos/impuestos.

7. **Más opciones en main (opcional)**
   - Por ejemplo: ver carrito actual, quitar item, modificar cantidad, cancelar venta. La lógica “quitar item” o “modificar cantidad” puede vivir en SesionVenta (validando stock si aplica) y el carrito ya tiene `quitar` y `modificar_cantidad`.

### Fase 4 – API y frontend (cuando quieras otra interfaz)

8. **API REST (FastAPI o Flask)**
   - Misma lógica: crear Inventario, RegistroVentas, RegistroSocio, SesionVenta (por request o por sesión HTTP). Los endpoints llamarían a `sesion.agregar_producto`, `sesion.calcular_totales`, `sesion.confirmar_pago`, etc., y devolverían JSON en lugar de imprimir.
   - Mantener main.py para uso en consola; la API sería otro “punto de entrada” que reutiliza las mismas clases.
   - **Por qué después de Fase 1–2:** Primero conviene tener rutas centralizadas y mensajes desacoplados; así la API no arrastra prints ni rutas hardcodeadas.

9. **Frontend (web o app)**
   - Consumiría la API. No hace falta tocar la lógica de negocio en Python; solo exponer endpoints bien definidos (productos, carrito, finalizar compra, socios si aplica).

10. **Despliegue**
    - Cuando tengas API + frontend (o solo API), desplegar backend (ej. en un VPS o PaaS) y servir front estático o app. La base de datos (si ya migraste a SQL) iría en el mismo servidor o en un servicio gestionado. Mantener configuración (rutas, URLs de DB) por variables de entorno.

---

## 5. Roadmap visual (resumido)

| Fase | Cuándo | Qué hacer | Por qué |
|------|--------|------------|---------|
| 1 | Ya | Rutas centralizadas, mensajes fuera de SesionVenta, opcional `cantidad_de` en Carrito | Consistencia, preparar para API y tests |
| 2 | Cuando JSON sea limitante | Capa repositorios + opción SQL (SQLite primero) | Concurrencia, consultas, integridad |
| 3 | Cuando añadas features | Tests unitarios, más opciones de carrito/venta | Confianza y UX sin reescribir |
| 4 | Cuando quieras otra UI | API REST, luego frontend | Reutilizar la misma lógica |
| 5 | Cuando vayas a producción | Deploy, env vars, backups DB | Seguridad y mantenibilidad |

---

## 6. Qué evitar (sobreingeniería por ahora)

- **No** introducir capas de “servicios” genéricos si con SesionVenta te basta; solo si más adelante tengas varios flujos (ventas, devoluciones, abonos) y quieras un servicio por flujo.
- **No** pasar a SQL ni a Docker hasta que tengas un motivo claro (varios usuarios, concurrencia, necesidad de consultas complejas).
- **No** añadir cache (Redis, etc.) ni colas de mensajes hasta que el rendimiento o la asincronía lo exijan.

---

## 7. Cambios ya aplicados en el código

- **registro_socio.py**: Eliminado el import erróneo `from super import socio`. Corregido `_guardar()` para persistir una **lista** de dicts (igual que `_cargar`), evitando que tras la primera escritura el archivo quedara en formato dict y rompiera la carga.

Con esto, la revisión arquitectónica queda cerrada: tienes una base sólida, una valoración clara, recomendaciones priorizadas y un roadmap para escalar paso a paso sin sobreingeniería. Si quieres, el siguiente paso concreto puede ser implementar la centralización de rutas (Fase 1.1) o el retorno de errores desde SesionVenta (Fase 1.2); puedo guiarte línea a línea en el archivo que elijas.
