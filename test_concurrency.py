"""
Tests de concurrencia para el sistema multi-branch.
Usa threading para simular dos cajas vendiendo al mismo tiempo.

ARQUITECTURA DEL TEST:
- Cada test crea una BD temporal (no toca supermercado.db)
- usa threading.Thread para simular 2 cajas concurrentes
- Verifica que el stock nunca quede negativo (race condition detectada)
- Verifica que los balances de caja se actualicen correctamente

COMO FUNCIONA BEGIN IMMEDIATE:
- Sin BEGIN IMMEDIATE: Thread A lee stock=5, Thread B lee stock=5,
  ambos restan 3 → stock = -1 (BUG)
- Con BEGIN IMMEDIATE: Thread A toma el lock y lee stock=5, Thread B espera.
  Thread A resta 3 → stock=2, commit, libera lock.
  Thread B toma el lock, lee stock=2, intenta restar 3 → falla (stock insuficiente).
"""
import os
import sys
import sqlite3
import threading
import tempfile
import shutil
import time

# Agregar root al path para importar modulos del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import producto_repository as repo


def setup_test_db():
    """
    Crea una BD temporal con datos de prueba.
    Devuelve el path a la BD temporal.
    Parcheamos repo.DB_PATH para que apunte a la BD temporal.
    """
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_concurrency.db")
    schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")

    # Parchear el path de la BD para que el repository use nuestra BD temporal
    repo.DB_PATH = db_path

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    with open(schema_path, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    conn.execute("PRAGMA foreign_keys = ON")

    # Crear branch, cash registers y productos de prueba
    cursor.execute("INSERT INTO branch (name, address) VALUES ('Test Branch', 'Test Addr')")

    # 2 cajas en la misma sucursal
    cursor.execute("INSERT INTO cash_register (branch_id, current_balance) VALUES (1, 10000)")
    cursor.execute("INSERT INTO cash_register (branch_id, current_balance) VALUES (1, 10000)")

    # Producto con stock limitado (5 unidades)
    cursor.execute("INSERT INTO product (name, category) VALUES ('Producto Escaso', 'Test')")
    cursor.execute(
        "INSERT INTO branch_product (branch_id, product_id, price, stock, active) VALUES (1, 1, 100, 5, 1)"
    )

    # Producto con stock amplio (100 unidades)
    cursor.execute("INSERT INTO product (name, category) VALUES ('Producto Abundante', 'Test')")
    cursor.execute(
        "INSERT INTO branch_product (branch_id, product_id, price, stock, active) VALUES (1, 2, 50, 100, 1)"
    )

    conn.commit()
    conn.close()
    return temp_dir


def cleanup_test_db(temp_dir):
    """Limpia la BD temporal y restaura el path original"""
    original_db = os.path.join(os.path.dirname(__file__), "supermercado.db")
    repo.DB_PATH = original_db
    shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    print("=" * 60)
    print("  TESTS DE CONCURRENCIA: TRANSACCIONES ATOMICAS")
    print("=" * 60)

    passed = 0
    failed = 0

    def test(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"  [OK] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    # ========================================
    # TEST 1: Dos cajas compiten por stock escaso
    # Stock = 5, Caja A pide 3, Caja B pide 3
    # Solo UNA debe tener exito
    # ========================================
    print("\n--- Test 1: Dos cajas compiten por stock escaso ---")
    print("    Stock=5, Caja A pide 3, Caja B pide 3. Solo 1 debe ganar.")

    def test_race_condition():
        temp_dir = setup_test_db()
        try:
            results = {"caja_a": None, "caja_b": None}
            errors = {"caja_a": None, "caja_b": None}

            def sell_from_cash_register(cash_register_id, result_key):
                try:
                    sale_id = repo.process_sale_atomic(
                        branch_id=1,
                        cash_register_id=cash_register_id,
                        items=[{
                            "product_name": "Producto Escaso",
                            "quantity": 3,
                            "price_at_sale": 100
                        }],
                        total_amount=300,
                        timestamp="2026-03-05 00:00:00"
                    )
                    results[result_key] = sale_id
                except (ValueError, sqlite3.OperationalError) as e:
                    errors[result_key] = str(e)

            # Lanzar 2 threads: caja 1 y caja 2 intentan vender al mismo tiempo
            thread_a = threading.Thread(target=sell_from_cash_register, args=(1, "caja_a"))
            thread_b = threading.Thread(target=sell_from_cash_register, args=(2, "caja_b"))

            thread_a.start()
            thread_b.start()
            thread_a.join(timeout=10)
            thread_b.join(timeout=10)

            # Exactamente UNA debe haber tenido exito
            success_count = sum(1 for v in results.values() if v is not None)
            error_count = sum(1 for v in errors.values() if v is not None)

            assert success_count == 1, (
                f"Esperado: 1 exito, obtenido: {success_count}. "
                f"Results: {results}, Errors: {errors}"
            )
            assert error_count == 1, (
                f"Esperado: 1 error, obtenido: {error_count}. "
                f"Errors: {errors}"
            )

            # Verificar que el stock final es 2 (5 - 3 = 2, no negativo)
            stock = repo.get_branch_product_stock(1, "Producto Escaso")
            assert stock == 2, f"Stock final: esperado 2, obtenido {stock}"

        finally:
            cleanup_test_db(temp_dir)

    test("Solo una caja gana cuando compiten por stock escaso", test_race_condition)

    # ========================================
    # TEST 2: Stock NO queda negativo
    # ========================================
    print("\n--- Test 2: Stock nunca queda negativo ---")
    print("    10 threads piden 3 unidades cada uno. Stock=5.")

    def test_no_negative_stock():
        temp_dir = setup_test_db()
        try:
            results = []
            errors_list = []
            lock = threading.Lock()

            def try_sell(thread_id):
                try:
                    sale_id = repo.process_sale_atomic(
                        branch_id=1,
                        cash_register_id=1,
                        items=[{
                            "product_name": "Producto Escaso",
                            "quantity": 3,
                            "price_at_sale": 100
                        }],
                        total_amount=300,
                        timestamp=f"2026-03-05 00:00:{thread_id:02d}"
                    )
                    with lock:
                        results.append(sale_id)
                except (ValueError, sqlite3.OperationalError) as e:
                    with lock:
                        errors_list.append(str(e))

            # 10 threads intentan comprar 3 unidades (solo 5 disponibles)
            threads = [threading.Thread(target=try_sell, args=(i,)) for i in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=15)

            # Solo 1 deberia haber tenido exito (5/3 = 1 venta completa)
            assert len(results) == 1, f"Esperado 1 exito, obtenido {len(results)}"
            assert len(errors_list) == 9, f"Esperado 9 errores, obtenido {len(errors_list)}"

            # Stock final: 5 - 3 = 2 (nunca negativo)
            stock = repo.get_branch_product_stock(1, "Producto Escaso")
            assert stock >= 0, f"Stock negativo detectado: {stock}"
            assert stock == 2, f"Stock final: esperado 2, obtenido {stock}"

        finally:
            cleanup_test_db(temp_dir)

    test("Stock nunca queda negativo con 10 threads concurrentes", test_no_negative_stock)

    # ========================================
    # TEST 3: Dos cajas venden productos DIFERENTES
    # Ambas deben tener exito (no se bloquean innecesariamente)
    # ========================================
    print("\n--- Test 3: Dos cajas venden productos diferentes ---")
    print("    Caja A vende Producto Escaso. Caja B vende Producto Abundante.")

    def test_different_products():
        temp_dir = setup_test_db()
        try:
            results = {"caja_a": None, "caja_b": None}
            errors = {"caja_a": None, "caja_b": None}

            def sell_product(cash_register_id, product_name, result_key):
                try:
                    sale_id = repo.process_sale_atomic(
                        branch_id=1,
                        cash_register_id=cash_register_id,
                        items=[{
                            "product_name": product_name,
                            "quantity": 2,
                            "price_at_sale": 100
                        }],
                        total_amount=200,
                        timestamp="2026-03-05 00:00:00"
                    )
                    results[result_key] = sale_id
                except Exception as e:
                    errors[result_key] = str(e)

            thread_a = threading.Thread(
                target=sell_product, args=(1, "Producto Escaso", "caja_a")
            )
            thread_b = threading.Thread(
                target=sell_product, args=(2, "Producto Abundante", "caja_b")
            )

            thread_a.start()
            thread_b.start()
            thread_a.join(timeout=10)
            thread_b.join(timeout=10)

            # Ambas deben tener exito
            assert results["caja_a"] is not None, f"Caja A fallo: {errors['caja_a']}"
            assert results["caja_b"] is not None, f"Caja B fallo: {errors['caja_b']}"

        finally:
            cleanup_test_db(temp_dir)

    test("Ambas cajas tienen exito vendiendo productos diferentes", test_different_products)

    # ========================================
    # TEST 4: Rollback completo si stock insuficiente
    # Si pido 2 productos y el segundo no tiene stock,
    # el primero tampoco se reduce
    # ========================================
    print("\n--- Test 4: Rollback completo en stock insuficiente ---")
    print("    Pido Producto Escaso (3) + Producto Abundante (200). Abundante tiene solo 100.")

    def test_rollback():
        temp_dir = setup_test_db()
        try:
            stock_escaso_antes = repo.get_branch_product_stock(1, "Producto Escaso")
            stock_abundante_antes = repo.get_branch_product_stock(1, "Producto Abundante")
            balance_antes = repo.get_cash_register_balance(1)

            try:
                repo.process_sale_atomic(
                    branch_id=1,
                    cash_register_id=1,
                    items=[
                        {"product_name": "Producto Escaso", "quantity": 3, "price_at_sale": 100},
                        {"product_name": "Producto Abundante", "quantity": 200, "price_at_sale": 50},
                    ],
                    total_amount=10300,
                    timestamp="2026-03-05 00:00:00"
                )
                raise AssertionError("Deberia haber fallado por stock insuficiente")
            except ValueError:
                pass  # Esperado

            # Verificar que NADA cambio (rollback completo)
            stock_escaso_despues = repo.get_branch_product_stock(1, "Producto Escaso")
            stock_abundante_despues = repo.get_branch_product_stock(1, "Producto Abundante")
            balance_despues = repo.get_cash_register_balance(1)

            assert stock_escaso_despues == stock_escaso_antes, (
                f"Stock Escaso cambio de {stock_escaso_antes} a {stock_escaso_despues}"
            )
            assert stock_abundante_despues == stock_abundante_antes, (
                f"Stock Abundante cambio de {stock_abundante_antes} a {stock_abundante_despues}"
            )
            assert balance_despues == balance_antes, (
                f"Balance caja cambio de {balance_antes} a {balance_despues}"
            )

        finally:
            cleanup_test_db(temp_dir)

    test("Rollback completo: stock y balance intactos si falla un item", test_rollback)

    # ========================================
    # TEST 5: Venta exitosa actualiza todo correctamente
    # ========================================
    print("\n--- Test 5: Venta exitosa actualiza stock, balance y registros ---")

    def test_successful_sale():
        temp_dir = setup_test_db()
        try:
            stock_antes = repo.get_branch_product_stock(1, "Producto Escaso")
            balance_antes = repo.get_cash_register_balance(1)

            sale_id = repo.process_sale_atomic(
                branch_id=1,
                cash_register_id=1,
                items=[
                    {"product_name": "Producto Escaso", "quantity": 2, "price_at_sale": 100},
                    {"product_name": "Producto Abundante", "quantity": 3, "price_at_sale": 50},
                ],
                total_amount=350,
                timestamp="2026-03-05 00:00:00"
            )

            # Verificar stock reducido
            stock_despues = repo.get_branch_product_stock(1, "Producto Escaso")
            assert stock_despues == stock_antes - 2, (
                f"Stock Escaso: esperado {stock_antes - 2}, obtenido {stock_despues}"
            )

            stock_abundante = repo.get_branch_product_stock(1, "Producto Abundante")
            assert stock_abundante == 100 - 3, (
                f"Stock Abundante: esperado 97, obtenido {stock_abundante}"
            )

            # Verificar balance actualizado
            balance_despues = repo.get_cash_register_balance(1)
            assert balance_despues == balance_antes + 350, (
                f"Balance: esperado {balance_antes + 350}, obtenido {balance_despues}"
            )

            # Verificar sale_id valido
            assert sale_id is not None and sale_id > 0

        finally:
            cleanup_test_db(temp_dir)

    test("Venta exitosa: stock, balance y sale_id correctos", test_successful_sale)

    # ========================================
    # TEST 6: Multiples cajas registradoras con balances independientes
    # ========================================
    print("\n--- Test 6: Balances independientes por caja ---")

    def test_independent_balances():
        temp_dir = setup_test_db()
        try:
            balance_caja1_antes = repo.get_cash_register_balance(1)
            balance_caja2_antes = repo.get_cash_register_balance(2)

            # Venta en caja 1
            repo.process_sale_atomic(
                branch_id=1,
                cash_register_id=1,
                items=[{"product_name": "Producto Abundante", "quantity": 1, "price_at_sale": 50}],
                total_amount=50,
                timestamp="2026-03-05 00:00:01"
            )

            # Venta en caja 2
            repo.process_sale_atomic(
                branch_id=1,
                cash_register_id=2,
                items=[{"product_name": "Producto Abundante", "quantity": 2, "price_at_sale": 50}],
                total_amount=100,
                timestamp="2026-03-05 00:00:02"
            )

            # Verificar que cada caja tiene su propio balance
            balance_caja1_despues = repo.get_cash_register_balance(1)
            balance_caja2_despues = repo.get_cash_register_balance(2)

            assert balance_caja1_despues == balance_caja1_antes + 50, (
                f"Caja 1: esperado {balance_caja1_antes + 50}, obtenido {balance_caja1_despues}"
            )
            assert balance_caja2_despues == balance_caja2_antes + 100, (
                f"Caja 2: esperado {balance_caja2_antes + 100}, obtenido {balance_caja2_despues}"
            )

        finally:
            cleanup_test_db(temp_dir)

    test("Caja 1 y Caja 2 tienen balances independientes", test_independent_balances)

    # ========================================
    # RESUMEN
    # ========================================
    print(f"\n{'=' * 60}")
    print(f"  RESULTADO: {passed} pasaron, {failed} fallaron")
    print(f"{'=' * 60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
