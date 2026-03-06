"""
Repository layer for database access.
All functions interact with the new multi-branch schema (English table names).

# Estructura de tablas que usa este módulo:
# - product: catálogo global (name, category)
# - branch_product: precio, stock y estado por sucursal
# - sale / sale_item: ventas con branch_id y price_at_sale
# - member: socios del negocio
# - supplier / product_supplier: proveedores y sus relaciones con productos
# - cash_register: cajas registradoras por sucursal
#
# CONCURRENCIA:
# process_sale_atomic() usa BEGIN IMMEDIATE para evitar race conditions.
# El timeout de 30s permite que una conexión espere si otra tiene el lock.
"""
import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'supermercado.db')

# Timeout de 30s: si otra conexión tiene el lock, esperamos en vez de fallar
CONNECTION_TIMEOUT = 30.0


def _get_connection():
    """
    Crea una conexión a la BD con foreign keys habilitadas.
    Timeout de 30s para soportar concurrencia (una caja espera si otra está en transacción).
    """
    conn = sqlite3.connect(DB_PATH, timeout=CONNECTION_TIMEOUT)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ===========================
# ATOMIC SALE TRANSACTION
# Esta es la función clave para concurrencia.
# Usa BEGIN IMMEDIATE para tomar un write lock ANTES de verificar stock.
# Así, entre "verificar stock" y "reducir stock", nadie más puede modificar la BD.
# ===========================

def process_sale_atomic(branch_id, cash_register_id, items, total_amount, timestamp, member_id=None):
    """
    Procesa una venta completa en UNA SOLA transacción atómica.

    FLUJO ATÓMICO (todo dentro de BEGIN IMMEDIATE ... COMMIT):
      1. Verificar stock de CADA producto
      2. Reducir stock de CADA producto
      3. Crear registro de venta (sale)
      4. Crear items de venta (sale_item) con price_at_sale congelado
      5. Actualizar saldo de la caja registradora

    Si algún producto no tiene stock suficiente → ROLLBACK completo,
    la BD queda exactamente como estaba antes.

    Args:
        branch_id (int): Sucursal donde se realiza la venta
        cash_register_id (int): Caja que procesa la venta
        items (list): Lista de dicts con {product_name, quantity, price_at_sale}
        total_amount (float): Monto total de la venta
        timestamp (str): Fecha/hora ISO
        member_id (int|None): ID del socio (None si no aplica)

    Returns:
        int: sale_id de la venta creada

    Raises:
        ValueError: Si stock insuficiente para algún producto
        sqlite3.OperationalError: Si hay un error de BD (timeout, etc)
    """
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        # BEGIN IMMEDIATE: toma el write lock AHORA, no espera al primer write.
        # Esto evita que otra transacción modifique el stock entre nuestro SELECT y UPDATE.
        cursor.execute("BEGIN IMMEDIATE")

        # --- Paso 1 y 2: Verificar y reducir stock de cada producto ---
        for item in items:
            product_name = item["product_name"]
            quantity = item["quantity"]

            # Verificar stock actual (con el lock tomado, este valor es confiable)
            cursor.execute(
                """SELECT bp.stock, p.id
                   FROM branch_product bp
                   JOIN product p ON p.id = bp.product_id
                   WHERE p.name = ? AND bp.branch_id = ? AND bp.active = 1""",
                (product_name, branch_id)
            )
            row = cursor.fetchone()

            if row is None:
                raise ValueError(
                    f"Producto '{product_name}' no encontrado o inactivo en sucursal {branch_id}"
                )

            current_stock, product_id = row

            if current_stock < quantity:
                raise ValueError(
                    f"Stock insuficiente de '{product_name}'. "
                    f"Disponible: {current_stock}, solicitado: {quantity}"
                )

            # Reducir stock (seguro porque tenemos el lock)
            cursor.execute(
                """UPDATE branch_product SET stock = stock - ?
                   WHERE branch_id = ? AND product_id = ?""",
                (quantity, branch_id, product_id)
            )

        # --- Paso 3: Crear el registro de venta ---
        cursor.execute(
            """INSERT INTO sale (branch_id, cash_register_id, total_amount, timestamp, member_id)
               VALUES (?, ?, ?, ?, ?)""",
            (branch_id, cash_register_id, total_amount, timestamp, member_id)
        )
        sale_id = cursor.lastrowid

        # --- Paso 4: Crear sale_items con precio congelado ---
        for item in items:
            product_name = item["product_name"]
            quantity = item["quantity"]
            price_at_sale = item["price_at_sale"]

            cursor.execute(
                "SELECT id FROM product WHERE name = ?",
                (product_name,)
            )
            product_id = cursor.fetchone()[0]

            cursor.execute(
                """INSERT INTO sale_item (sale_id, product_id, quantity, price_at_sale)
                   VALUES (?, ?, ?, ?)""",
                (sale_id, product_id, quantity, price_at_sale)
            )

        # --- Paso 5: Actualizar saldo de la caja ---
        cursor.execute(
            """UPDATE cash_register SET current_balance = current_balance + ?
               WHERE id = ?""",
            (total_amount, cash_register_id)
        )

        # Todo OK → aplicar todos los cambios de golpe
        conn.commit()
        return sale_id

    except Exception:
        # Si ALGO falla (stock insuficiente, FK invalido, lo que sea)
        # → deshacer TODO. La BD queda como si nada hubiera pasado.
        conn.rollback()
        raise

    finally:
        # Siempre cerrar la conexión (libera el lock para otras cajas)
        conn.close()


def get_cash_registers_by_branch(branch_id):
    """
    Obtiene todas las cajas registradoras de una sucursal.
    Returns: lista de (id, current_balance)
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, current_balance FROM cash_register WHERE branch_id = ?",
        (branch_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return results


# ===========================
# PRODUCTS + BRANCH_PRODUCT
# Producto es global; precio, stock y active dependen de la sucursal.
# ===========================

def create_product(name, category=None):
    """
    Crea un producto global (sin precio ni stock — eso va en branch_product).
    Returns: product_id
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO product (name, category) VALUES (?, ?)",
        (name, category)
    )
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id


def create_product_with_branch(name, category, branch_id, price, initial_stock):
    """
    Crea un producto global Y lo asocia a una sucursal en un solo paso.
    Útil para seeding y para cuando se crea un producto desde una sucursal específica.
    Returns: product_id
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        # Crear producto global
        cursor.execute(
            "INSERT INTO product (name, category) VALUES (?, ?)",
            (name, category)
        )
        product_id = cursor.lastrowid

        # Asociar a la sucursal con precio y stock
        cursor.execute(
            """INSERT INTO branch_product (branch_id, product_id, price, stock, active)
               VALUES (?, ?, ?, ?, 1)""",
            (branch_id, product_id, price, initial_stock)
        )
        conn.commit()
    finally:
        conn.close()
    return product_id


def assign_product_to_branch(branch_id, product_id, price, stock=0, active=1):
    """
    Asigna un producto existente a una sucursal (crea la fila en branch_product).
    Esto permite que el mismo producto esté en múltiples sucursales con precios diferentes.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO branch_product (branch_id, product_id, price, stock, active)
               VALUES (?, ?, ?, ?, ?)""",
            (branch_id, product_id, price, stock, active)
        )
        conn.commit()
    finally:
        conn.close()


def get_active_products(branch_id):
    """
    Obtiene todos los productos activos en una sucursal específica.
    Returns: lista de (name, price, stock)
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT p.name, bp.price, bp.stock
           FROM product p
           JOIN branch_product bp ON p.id = bp.product_id
           WHERE bp.branch_id = ? AND bp.active = 1""",
        (branch_id,)
    )
    products = cursor.fetchall()
    conn.close()
    return products


def get_product_by_name(name, branch_id):
    """
    Obtiene un producto por nombre exacto en una sucursal específica.
    El precio viene de branch_product (no de product, que no tiene precio).
    Returns: (product_id, name, price, stock) o None
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT p.id, p.name, bp.price, bp.stock
           FROM product p
           JOIN branch_product bp ON p.id = bp.product_id
           WHERE p.name = ? AND bp.branch_id = ? AND bp.active = 1""",
        (name, branch_id)
    )
    product = cursor.fetchone()
    conn.close()
    return product


def search_by_name(partial_name, branch_id):
    """
    Búsqueda parcial de productos por nombre (case-insensitive) en una sucursal.
    Solo retorna productos activos en esa sucursal.
    Returns: lista de nombres
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT p.name
           FROM product p
           JOIN branch_product bp ON p.id = bp.product_id
           WHERE p.name LIKE ? AND bp.branch_id = ? AND bp.active = 1""",
        (f"%{partial_name}%", branch_id)
    )
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]


def get_product_id_by_name(name):
    """
    Obtiene el ID de un producto global por su nombre.
    No depende de sucursal porque product es global.
    Returns: product_id o None
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM product WHERE name = ?",
        (name,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def update_branch_product_stock(branch_id, product_name, quantity_delta):
    """
    Modifica el stock de un producto en una sucursal (suma o resta).
    quantity_delta positivo = aumentar, negativo = reducir.
    Returns: rows affected
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE branch_product
               SET stock = stock + ?
               WHERE branch_id = ?
                 AND product_id = (SELECT id FROM product WHERE name = ?)""",
            (quantity_delta, branch_id, product_name)
        )
        rows = cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    return rows


def get_branch_product_stock(branch_id, product_name):
    """
    Obtiene el stock actual de un producto en una sucursal.
    Returns: cantidad (int) o None si no se encuentra
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT bp.stock
           FROM branch_product bp
           JOIN product p ON p.id = bp.product_id
           WHERE p.name = ? AND bp.branch_id = ? AND bp.active = 1""",
        (product_name, branch_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# ===========================
# MEMBERS (antes: socios)
# ===========================

def create_member(name, dni, password_hash):
    """
    Inserta un nuevo miembro/socio.
    Returns: member_id
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO member (name, dni, password, active)
           VALUES (?, ?, ?, 1)""",
        (name, dni, password_hash)
    )
    member_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return member_id


def get_member_by_name(name):
    """
    Obtiene un miembro/socio por nombre exacto.
    Returns: (id, name, dni, password, active) o None
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, name, dni, password, active
           FROM member WHERE name = ? AND active = 1""",
        (name,)
    )
    member = cursor.fetchone()
    conn.close()
    return member


def get_member_by_dni(dni):
    """
    Obtiene un miembro/socio por DNI.
    Returns: (id, name, dni, password, active) o None
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, name, dni, password, active
           FROM member WHERE dni = ? AND active = 1""",
        (dni,)
    )
    member = cursor.fetchone()
    conn.close()
    return member


# ===========================
# SALES (antes: ventas)
# Cada venta pertenece a una sucursal y una caja.
# ===========================

def create_sale(branch_id, cash_register_id, total_amount, timestamp, member_id=None):
    """
    Registra una nueva venta.
    branch_id se guarda explícitamente para queries rápidas.
    member_id es nullable (no todas las ventas son de socios).
    Returns: sale_id
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO sale (branch_id, cash_register_id, total_amount, timestamp, member_id)
               VALUES (?, ?, ?, ?, ?)""",
            (branch_id, cash_register_id, total_amount, timestamp, member_id)
        )
        sale_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    return sale_id


def create_sale_item(sale_id, product_id, quantity, price_at_sale):
    """
    Inserta un item en una venta.
    price_at_sale congela el precio al momento de la venta (historial correcto).
    Returns: sale_item_id
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO sale_item (sale_id, product_id, quantity, price_at_sale)
               VALUES (?, ?, ?, ?)""",
            (sale_id, product_id, quantity, price_at_sale)
        )
        item_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    return item_id


# ===========================
# CASH REGISTER (antes: caja)
# ===========================

def update_cash_register_balance(cash_register_id, amount_delta):
    """
    Modifica el saldo de una caja registradora.
    amount_delta positivo = ingreso, negativo = retiro.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE cash_register
               SET current_balance = current_balance + ?
               WHERE id = ?""",
            (amount_delta, cash_register_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_cash_register_balance(cash_register_id):
    """
    Obtiene el saldo actual de una caja registradora.
    Returns: saldo (float)
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT current_balance FROM cash_register WHERE id = ?",
        (cash_register_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


# ===========================
# SUPPLIERS (antes: proveedores)
# ===========================

def create_supplier(name):
    """
    Crea un nuevo proveedor.
    Returns: supplier_id
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO supplier (name, active) VALUES (?, 1)",
            (name,)
        )
        supplier_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    return supplier_id


def get_supplier_by_name(name):
    """
    Obtiene un proveedor por nombre.
    Returns: (id, name) o None
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name FROM supplier WHERE name = ? AND active = 1",
        (name,)
    )
    result = cursor.fetchone()
    conn.close()
    return result


def get_all_suppliers():
    """
    Obtiene todos los proveedores activos.
    Returns: lista de (id, name)
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM supplier WHERE active = 1")
    results = cursor.fetchall()
    conn.close()
    return results


def create_product_supplier_relation(product_id, supplier_id, purchase_price, initial_stock=0):
    """
    Crea una relación entre producto y proveedor.
    Returns: relation_id
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO product_supplier (product_id, supplier_id, purchase_price, available_stock)
               VALUES (?, ?, ?, ?)""",
            (product_id, supplier_id, purchase_price, initial_stock)
        )
        relation_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    return relation_id


def get_relations_by_product(product_id):
    """
    Obtiene todos los proveedores que venden un producto.
    Returns: lista de (relation_id, product_id, supplier_id, supplier_name, purchase_price, available_stock)
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT ps.id, ps.product_id, ps.supplier_id, s.name, ps.purchase_price, ps.available_stock
           FROM product_supplier ps
           JOIN supplier s ON ps.supplier_id = s.id
           WHERE ps.product_id = ?""",
        (product_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return results


def get_relations_by_supplier(supplier_id):
    """
    Obtiene todos los productos que un proveedor vende.
    Returns: lista de (relation_id, product_id, product_name, purchase_price, available_stock)
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT ps.id, ps.product_id, p.name, ps.purchase_price, ps.available_stock
           FROM product_supplier ps
           JOIN product p ON ps.product_id = p.id
           WHERE ps.supplier_id = ?""",
        (supplier_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return results


def set_supplier_stock(relation_id, quantity):
    """
    Establece el stock disponible de una relación producto-proveedor a un valor fijo.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE product_supplier SET available_stock = ? WHERE id = ?",
            (quantity, relation_id)
        )
        conn.commit()
    finally:
        conn.close()


def update_supplier_stock(relation_id, quantity_delta):
    """
    Modifica el stock disponible de una relación producto-proveedor.
    quantity_delta positivo = aumentar, negativo = reducir.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE product_supplier SET available_stock = available_stock + ? WHERE id = ?",
            (quantity_delta, relation_id)
        )
        conn.commit()
    finally:
        conn.close()
