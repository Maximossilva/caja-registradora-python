-- Habilitar foreign keys en SQLite (necesario para que las restricciones funcionen)
PRAGMA foreign_keys = ON;

-- ==========================
-- TABLA: branch
-- Representa una sucursal física del negocio.
-- Cada sucursal tiene su propio inventario, precios y cajas.
-- ==========================
CREATE TABLE IF NOT EXISTS branch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                -- Nombre de la sucursal (ej: "Sucursal Centro")
    address TEXT                       -- Dirección física (opcional)
);

-- ==========================
-- TABLA: user
-- Usuarios del sistema con roles diferenciados.
-- El owner (dueño) tiene branch_id NULL porque accede a todas las sucursales.
-- Los managers y cashiers pertenecen a una sola sucursal.
-- ==========================
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                -- Nombre completo del usuario
    role TEXT NOT NULL CHECK (role IN ('owner', 'manager', 'cashier')),  -- Rol con constraint CHECK para validar valores permitidos
    branch_id INTEGER,                 -- NULL para owner (acceso global), NOT NULL para manager/cashier
    FOREIGN KEY (branch_id) REFERENCES branch(id)
);

-- ==========================
-- TABLA: product
-- Catálogo global de productos. No depende de ninguna sucursal.
-- El precio y stock se manejan por sucursal en branch_product.
-- ==========================
CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                -- Nombre del producto (ej: "Coca Cola 500ml")
    category TEXT                      -- Categoría del producto (ej: "Bebidas", "Lácteos")
);

-- ==========================
-- TABLA: branch_product
-- Tabla pivote que conecta products con branches.
-- Cada fila indica que un producto está disponible en una sucursal específica,
-- con su propio precio, stock y estado activo/inactivo.
-- Constraint UNIQUE(branch_id, product_id) evita duplicados.
-- ==========================
CREATE TABLE IF NOT EXISTS branch_product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,        -- Sucursal donde está disponible el producto
    product_id INTEGER NOT NULL,       -- Producto global al que hace referencia
    price REAL NOT NULL,               -- Precio de venta en ESTA sucursal (puede variar entre sucursales)
    stock INTEGER NOT NULL DEFAULT 0,  -- Cantidad disponible en ESTA sucursal (independiente entre sucursales)
    active INTEGER NOT NULL DEFAULT 1, -- 1 = se vende en esta sucursal, 0 = no se vende aquí
    FOREIGN KEY (branch_id) REFERENCES branch(id),
    FOREIGN KEY (product_id) REFERENCES product(id),
    UNIQUE(branch_id, product_id)      -- Un producto solo puede aparecer una vez por sucursal
);

-- ==========================
-- TABLA: cash_register
-- Caja registradora asociada a una sucursal.
-- Cada sucursal puede tener múltiples cajas.
-- ==========================
CREATE TABLE IF NOT EXISTS cash_register (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,            -- Sucursal a la que pertenece esta caja
    current_balance REAL NOT NULL DEFAULT 0, -- Saldo actual en la caja
    FOREIGN KEY (branch_id) REFERENCES branch(id)
);

-- ==========================
-- TABLA: member
-- Socios/clientes registrados del negocio (antes: socio).
-- Se mantiene la funcionalidad existente, renombrada a inglés.
-- ==========================
CREATE TABLE IF NOT EXISTS member (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                -- Nombre del socio
    dni TEXT UNIQUE NOT NULL,          -- Documento de identidad único
    password TEXT NOT NULL,            -- Contraseña hasheada
    active INTEGER NOT NULL DEFAULT 1  -- 1 = activo, 0 = dado de baja
);

-- ==========================
-- TABLA: sale
-- Registro de cada venta realizada.
-- Guarda branch_id explícitamente para queries rápidas y para mantener
-- integridad histórica (si una caja cambia de sucursal, la venta queda correcta).
-- member_id es nullable porque no todas las ventas son de socios.
-- ==========================
CREATE TABLE IF NOT EXISTS sale (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,            -- Sucursal donde se realizó la venta
    cash_register_id INTEGER NOT NULL,     -- Caja que procesó la venta
    total_amount REAL NOT NULL,            -- Monto total de la venta
    timestamp TEXT NOT NULL,               -- Fecha y hora en formato ISO (ej: "2026-03-03 01:15:00")
    member_id INTEGER,                     -- Socio asociado (NULL si no es socio)
    FOREIGN KEY (branch_id) REFERENCES branch(id),
    FOREIGN KEY (cash_register_id) REFERENCES cash_register(id),
    FOREIGN KEY (member_id) REFERENCES member(id)
);

-- ==========================
-- TABLA: sale_item
-- Cada producto vendido dentro de una venta.
-- price_at_sale congela el precio al momento de la venta, así si después
-- cambia el precio en branch_product, el historial queda correcto.
-- ==========================
CREATE TABLE IF NOT EXISTS sale_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,              -- Venta a la que pertenece este item
    product_id INTEGER NOT NULL,           -- Producto vendido (referencia al catálogo global)
    quantity INTEGER NOT NULL,             -- Cantidad vendida
    price_at_sale REAL NOT NULL,           -- Precio unitario AL MOMENTO de la venta (congelado)
    FOREIGN KEY (sale_id) REFERENCES sale(id),
    FOREIGN KEY (product_id) REFERENCES product(id)
);

-- ==========================
-- TABLA: supplier
-- Proveedores del negocio (antes: proveedor).
-- Renombrada a inglés para consistencia.
-- ==========================
CREATE TABLE IF NOT EXISTS supplier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- Nombre del proveedor
    active INTEGER NOT NULL DEFAULT 1      -- 1 = activo, 0 = dado de baja
);

-- ==========================
-- TABLA: product_supplier
-- Relación entre productos y proveedores (antes: producto_proveedor).
-- Indica qué proveedor vende qué producto, a qué precio de compra,
-- y cuánto stock tiene disponible el proveedor.
-- Constraint UNIQUE para evitar duplicar la misma relación.
-- ==========================
CREATE TABLE IF NOT EXISTS product_supplier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,           -- Producto que provee
    supplier_id INTEGER NOT NULL,          -- Proveedor que lo vende
    purchase_price REAL NOT NULL,          -- Precio de compra al proveedor
    available_stock INTEGER NOT NULL DEFAULT 0, -- Stock disponible en el proveedor
    FOREIGN KEY (product_id) REFERENCES product(id),
    FOREIGN KEY (supplier_id) REFERENCES supplier(id),
    UNIQUE(product_id, supplier_id)        -- Un proveedor solo puede proveer un producto una vez
);