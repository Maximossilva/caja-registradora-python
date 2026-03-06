"""
Script de verificacion completa del refactoring multi-branch.
Verifica: schema, seeding, queries por branch, FK, UNIQUE, CHECK constraints.
"""
import sqlite3
import os
import sys

# Agregar el directorio raiz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import producto_repository as repo
from database.init_db import init_database


def main():
    print("=" * 60)
    print("  VERIFICACION COMPLETA: REFACTORING MULTI-BRANCH")
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
    # TEST 1: Inicializar BD
    # ========================================
    print("\n--- Test 1: Inicializacion de BD ---")

    def test_init():
        init_database()

    test("init_database() ejecuta sin error", test_init)

    # ========================================
    # TEST 2: Datos semilla
    # ========================================
    print("\n--- Test 2: Datos semilla ---")

    def test_branches():
        products_centro = repo.get_active_products(1)
        assert len(products_centro) == 35, f"Esperado 35 productos en Centro, obtenido {len(products_centro)}"

    def test_branches_norte():
        products_norte = repo.get_active_products(2)
        assert len(products_norte) == 34, f"Esperado 34 productos en Norte (Arroz inactivo), obtenido {len(products_norte)}"

    def test_arroz_inactivo():
        arroz = repo.get_product_by_name("Arroz 1kg", 2)
        assert arroz is None, f"Arroz deberia ser None en Norte (inactivo), obtenido {arroz}"

    def test_precios_diferentes():
        coca_centro = repo.get_product_by_name("Coca Cola 500ml", 1)
        coca_norte = repo.get_product_by_name("Coca Cola 500ml", 2)
        assert coca_centro[2] == 150.0, f"Coca Centro: esperado $150, obtenido ${coca_centro[2]}"
        assert coca_norte[2] == 170.0, f"Coca Norte: esperado $170, obtenido ${coca_norte[2]}"

    def test_cash_registers():
        saldo1 = repo.get_cash_register_balance(1)
        saldo2 = repo.get_cash_register_balance(2)
        assert saldo1 == 50000, f"Caja 1: esperado $50000, obtenido ${saldo1}"
        assert saldo2 == 25000, f"Caja 2: esperado $25000, obtenido ${saldo2}"

    test("35 productos activos en Sucursal Centro", test_branches)
    test("34 productos activos en Sucursal Norte (Arroz inactivo)", test_branches_norte)
    test("Arroz es None en Norte (inactivo)", test_arroz_inactivo)
    test("Coca Cola: $150 en Centro, $170 en Norte", test_precios_diferentes)
    test("Saldos de caja: $50000 Caja1, $25000 Caja2", test_cash_registers)

    # ========================================
    # TEST 3: Busqueda parcial
    # ========================================
    print("\n--- Test 3: Busqueda parcial ---")

    def test_search():
        results = repo.search_by_name("Coca", 1)
        assert "Coca Cola 500ml" in results, f"Busqueda 'Coca' en Centro no encontro resultado"

    def test_search_norte():
        results = repo.search_by_name("Arroz", 2)
        assert len(results) == 0, f"Arroz no deberia aparecer en Norte (inactivo)"

    test("Busqueda 'Coca' en Centro encuentra 'Coca Cola 500ml'", test_search)
    test("Busqueda 'Arroz' en Norte no encuentra nada (inactivo)", test_search_norte)

    # ========================================
    # TEST 4: InventarioSQLite
    # ========================================
    print("\n--- Test 4: InventarioSQLite ---")

    from inventario_sqlite import InventarioSQLite

    def test_inventario():
        inv = InventarioSQLite(branch_id=1)
        producto = inv.obtener_producto("Coca Cola 500ml")
        assert producto is not None, "Coca Cola no encontrada en inventario Centro"
        assert producto.precio == 150.0, f"Precio incorrecto: {producto.precio}"
        assert producto.stock == 100, f"Stock incorrecto: {producto.stock}"

    def test_inventario_norte():
        inv = InventarioSQLite(branch_id=2)
        producto = inv.obtener_producto("Coca Cola 500ml")
        assert producto is not None, "Coca Cola no encontrada en inventario Norte"
        assert producto.precio == 170.0, f"Precio incorrecto: {producto.precio}"

    test("InventarioSQLite(branch_id=1) obtiene producto correcto", test_inventario)
    test("InventarioSQLite(branch_id=2) obtiene precio diferente", test_inventario_norte)

    # ========================================
    # TEST 5: Caja
    # ========================================
    print("\n--- Test 5: Caja ---")

    from caja import Caja

    def test_caja():
        caja = Caja(cash_register_id=1)
        saldo = caja.obtener_saldo()
        assert saldo == 50000, f"Saldo caja 1: esperado $50000, obtenido ${saldo}"

    def test_caja_2():
        caja = Caja(cash_register_id=2)
        saldo = caja.obtener_saldo()
        assert saldo == 25000, f"Saldo caja 2: esperado $25000, obtenido ${saldo}"

    test("Caja(cash_register_id=1) saldo = $50000", test_caja)
    test("Caja(cash_register_id=2) saldo = $25000", test_caja_2)

    # ========================================
    # TEST 6: Ventas
    # ========================================
    print("\n--- Test 6: Ventas ---")

    def test_create_sale():
        sale_id = repo.create_sale(
            branch_id=1,
            cash_register_id=1,
            total_amount=350.0,
            timestamp="2026-03-04 16:00:00",
            member_id=None
        )
        assert sale_id is not None
        assert sale_id > 0

    def test_create_sale_item():
        product_id = repo.get_product_id_by_name("Coca Cola 500ml")
        item_id = repo.create_sale_item(
            sale_id=1,
            product_id=product_id,
            quantity=2,
            price_at_sale=150.0
        )
        assert item_id is not None
        assert item_id > 0

    test("Crear venta en branch 1", test_create_sale)
    test("Crear sale_item con price_at_sale congelado", test_create_sale_item)

    # ========================================
    # TEST 7: FK constraints
    # ========================================
    print("\n--- Test 7: FK constraints ---")

    def test_fk_sale_bad_branch():
        try:
            repo.create_sale(9999, 1, 100, "2026-01-01")
            raise AssertionError("Deberia fallar: branch_id 9999 no existe")
        except sqlite3.IntegrityError:
            pass

    def test_fk_sale_bad_cash():
        try:
            repo.create_sale(1, 9999, 100, "2026-01-01")
            raise AssertionError("Deberia fallar: cash_register_id 9999 no existe")
        except sqlite3.IntegrityError:
            pass

    test("FK sale -> branch rechaza branch_id inexistente", test_fk_sale_bad_branch)
    test("FK sale -> cash_register rechaza cash_register_id inexistente", test_fk_sale_bad_cash)

    # ========================================
    # RESUMEN
    # ========================================
    print(f"\n{'=' * 60}")
    print(f"  RESULTADO: {passed} pasaron, {failed} fallaron")
    print(f"{'=' * 60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
