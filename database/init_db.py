import sqlite3
import os


def init_database():
    """
    Inicializa la base de datos SQLite ejecutando el schema.sql.
    Si la BD esta vacia, inserta datos semilla:
    - 2 sucursales (Sucursal Centro, Sucursal Norte)
    - 2 cajas registradoras por sucursal (4 total)
    - 1 usuario owner (acceso global)
    - ~35 productos con precios y stock diferentes por sucursal
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "supermercado.db")
    schema_path = os.path.join(base_dir, "database", "schema.sql")

    connection = sqlite3.connect(db_path, timeout=20.0)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.isolation_level = None
    cursor = connection.cursor()

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = f.read()

        cursor.executescript(schema)
        connection.execute("PRAGMA foreign_keys = ON")

        cursor.execute("SELECT COUNT(*) FROM branch")
        if cursor.fetchone()[0] == 0:
            _seed_data(cursor)

        connection.commit()
    finally:
        connection.close()


def _seed_data(cursor):
    """
    Inserta datos semilla para que el sistema sea funcional desde el primer uso.
    Crea 2 sucursales, 4 cajas (2 por sucursal), un owner, y ~35 productos.
    """
    # ---- Sucursales ----
    cursor.execute(
        "INSERT INTO branch (name, address) VALUES (?, ?)",
        ("Sucursal Centro", "Av. Siempre Viva 123")
    )
    cursor.execute(
        "INSERT INTO branch (name, address) VALUES (?, ?)",
        ("Sucursal Norte", "Calle Falsa 456")
    )

    # ---- Cajas registradoras: 2 por sucursal ----
    # Sucursal Centro: caja 1 y caja 2
    cursor.execute(
        "INSERT INTO cash_register (branch_id, current_balance) VALUES (?, ?)",
        (1, 50000)
    )
    cursor.execute(
        "INSERT INTO cash_register (branch_id, current_balance) VALUES (?, ?)",
        (1, 25000)
    )
    # Sucursal Norte: caja 3 y caja 4
    cursor.execute(
        "INSERT INTO cash_register (branch_id, current_balance) VALUES (?, ?)",
        (2, 30000)
    )
    cursor.execute(
        "INSERT INTO cash_register (branch_id, current_balance) VALUES (?, ?)",
        (2, 15000)
    )

    # ---- Usuario owner (branch_id = NULL, acceso global) ----
    cursor.execute(
        "INSERT INTO user (name, role, branch_id) VALUES (?, ?, ?)",
        ("Admin", "owner", None)
    )

    # ---- Catalogo global de productos ----
    # (name, category)
    products = [
        # Bebidas (1-8)
        ("Coca Cola 500ml", "Bebidas"),
        ("Coca Cola 1.5L", "Bebidas"),
        ("Pepsi 500ml", "Bebidas"),
        ("Sprite 500ml", "Bebidas"),
        ("Fanta 500ml", "Bebidas"),
        ("Agua Mineral 500ml", "Bebidas"),
        ("Agua Mineral 1.5L", "Bebidas"),
        ("Jugo de Naranja 1L", "Bebidas"),
        # Lacteos (9-14)
        ("Leche Entera 1L", "Lacteos"),
        ("Leche Descremada 1L", "Lacteos"),
        ("Yogur Natural 200g", "Lacteos"),
        ("Queso Cremoso 1kg", "Lacteos"),
        ("Manteca 200g", "Lacteos"),
        ("Crema de Leche 200ml", "Lacteos"),
        # Panificados (15-19)
        ("Pan Lactal", "Panificados"),
        ("Pan Frances", "Panificados"),
        ("Medialunas x6", "Panificados"),
        ("Galletitas Dulces 200g", "Panificados"),
        ("Galletitas Saladas 200g", "Panificados"),
        # Almacen (20-28)
        ("Arroz 1kg", "Almacen"),
        ("Fideos Tirabuzones 500g", "Almacen"),
        ("Fideos Spaghetti 500g", "Almacen"),
        ("Aceite Girasol 1L", "Almacen"),
        ("Aceite Oliva 500ml", "Almacen"),
        ("Azucar 1kg", "Almacen"),
        ("Harina 1kg", "Almacen"),
        ("Sal Fina 500g", "Almacen"),
        ("Cafe Molido 250g", "Almacen"),
        # Limpieza (29-32)
        ("Detergente 750ml", "Limpieza"),
        ("Lavandina 1L", "Limpieza"),
        ("Jabon en Polvo 800g", "Limpieza"),
        ("Papel Higienico x4", "Limpieza"),
        # Snacks (33-35)
        ("Papas Fritas 150g", "Snacks"),
        ("Chocolate 100g", "Snacks"),
        ("Alfajor Triple", "Snacks"),
    ]

    for name, category in products:
        cursor.execute(
            "INSERT INTO product (name, category) VALUES (?, ?)",
            (name, category)
        )

    # ---- Asignar productos a sucursales ----
    # Formato: (product_id, price_centro, stock_centro, active_centro,
    #           price_norte, stock_norte, active_norte)
    assignments = [
        # Bebidas
        (1,   150,  100, 1,   170,  50,  1),
        (2,   250,   60, 1,   280,  30,  1),
        (3,   140,   80, 1,   160,  40,  1),
        (4,   140,   70, 1,   160,  35,  1),
        (5,   140,   60, 1,   160,  30,  1),
        (6,   100,  120, 1,   110,  80,  1),
        (7,   170,   50, 1,   190,  25,  1),
        (8,   200,   40, 1,   220,  20,  1),
        # Lacteos
        (9,   180,   80, 1,   190,  40,  1),
        (10,  190,   60, 1,   200,  30,  1),
        (11,  120,   90, 1,   130,  45,  1),
        (12,  600,   25, 1,   650,  15,  1),
        (13,  250,   40, 1,   270,  20,  1),
        (14,  180,   35, 1,   200,  18,  1),
        # Panificados
        (15,  200,   50, 1,   200,  30,  1),
        (16,  150,   80, 1,   150,  40,  1),
        (17,  350,   30, 1,   380,  15,  1),
        (18,  180,   60, 1,   190,  30,  1),
        (19,  160,   50, 1,   170,  25,  1),
        # Almacen
        (20,  120,   60, 1,   120,   0,  0),  # Arroz: INACTIVO en Norte
        (21,  100,   70, 1,   110,  35,  1),
        (22,  100,   70, 1,   110,  35,  1),
        (23,  300,   40, 1,   320,  20,  1),
        (24,  550,   20, 1,   580,  10,  1),
        (25,   90,   80, 1,   100,  40,  1),
        (26,   80,  100, 1,    90,  50,  1),
        (27,   60,  120, 1,    70,  60,  1),
        (28,  400,   30, 1,   430,  15,  1),
        # Limpieza
        (29,  200,   45, 1,   220,  22,  1),
        (30,  120,   50, 1,   130,  25,  1),
        (31,  350,   35, 1,   370,  18,  1),
        (32,  250,   60, 1,   270,  30,  1),
        # Snacks
        (33,  200,   50, 1,   220,  25,  1),
        (34,  150,   70, 1,   170,  35,  1),
        (35,  120,   80, 1,   130,  40,  1),
    ]

    for pid, pc, sc, ac, pn, sn, an in assignments:
        # Sucursal Centro (branch_id=1)
        cursor.execute(
            """INSERT INTO branch_product (branch_id, product_id, price, stock, active)
               VALUES (?, ?, ?, ?, ?)""",
            (1, pid, pc, sc, ac)
        )
        # Sucursal Norte (branch_id=2)
        cursor.execute(
            """INSERT INTO branch_product (branch_id, product_id, price, stock, active)
               VALUES (?, ?, ?, ?, ?)""",
            (2, pid, pn, sn, an)
        )
