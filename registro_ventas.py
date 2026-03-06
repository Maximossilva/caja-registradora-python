# registro_ventas.py
#
# Registra ventas en SQLite usando transacciones atómicas.
# Toda la venta (stock + sale + items + balance) se procesa en una sola transacción.

from datetime import datetime
from database import producto_repository


class RegistroVentas:
    """
    Registra ventas usando process_sale_atomic().
    Toda la operación (verificar stock, reducir stock, crear venta,
    crear items, actualizar caja) se ejecuta en UNA sola transacción.
    Si algo falla, NADA se modifica (ROLLBACK automático).
    """

    def __init__(self, branch_id=1, cash_register_id=1):
        # Sucursal y caja a las que se asocian las ventas
        self.branch_id = branch_id
        self.cash_register_id = cash_register_id

    def registrar_venta(
        self,
        items,
        subtotal,
        iva,
        descuento,
        total,
        metodo_pago,
        es_socio,
        socio_id=None
    ):
        """
        Registra una venta completa de forma atómica.

        IMPORTANTE: Esta función ahora también reduce el stock y actualiza
        el saldo de la caja. Ya NO es necesario llamar a
        inventario.reducir_stock() ni caja.ingresar() por separado.

        Args:
            items (list): Lista de dicts con {nombre, precio, cantidad}
            subtotal (float): Subtotal
            iva (float): IVA
            descuento (float): Descuento aplicado
            total (float): Total final
            metodo_pago (str): "efectivo" o "tarjeta"
            es_socio (bool): True si es socio
            socio_id (int): ID del socio (None si no aplica)

        Returns:
            int: sale_id de la venta creada

        Raises:
            ValueError: Si stock insuficiente para algún producto
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Convertir items al formato que espera process_sale_atomic
        # De {nombre, precio, cantidad} → {product_name, quantity, price_at_sale}
        atomic_items = []
        for item in items:
            atomic_items.append({
                "product_name": item["nombre"],
                "quantity": item["cantidad"],
                "price_at_sale": item["precio"]
            })

        # UNA sola llamada atómica: todo o nada
        # Si stock insuficiente → ValueError + ROLLBACK (nada se modifica)
        # Si todo OK → stock reducido + venta creada + caja actualizada
        sale_id = producto_repository.process_sale_atomic(
            branch_id=self.branch_id,
            cash_register_id=self.cash_register_id,
            items=atomic_items,
            total_amount=total,
            timestamp=timestamp,
            member_id=socio_id
        )

        return sale_id
