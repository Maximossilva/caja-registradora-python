# caja.py
#
# Gestiona una caja registradora específica (cash_register).
# Cada instancia trabaja con un cash_register_id,
# permitiendo múltiples cajas por sucursal.

import sqlite3
import os
from database import producto_repository


class Caja:
    """
    Representa una caja registradora vinculada a una sucursal.
    Usa la tabla cash_register del nuevo schema.
    """

    def __init__(self, cash_register_id=1):
        # ID de la caja registradora con la que trabaja esta instancia
        self.cash_register_id = cash_register_id

    def ingresar(self, monto):
        """
        Registra un ingreso de dinero en la caja.
        Se llama después de confirmar una venta.
        """
        producto_repository.update_cash_register_balance(
            self.cash_register_id, monto  # positivo = ingreso
        )

    def obtener_saldo(self):
        """
        Obtiene el saldo actual de esta caja registradora.
        Returns: saldo (float)
        """
        return producto_repository.get_cash_register_balance(self.cash_register_id)

    def retirar(self, monto):
        """
        Retira dinero de la caja (ej: compra a proveedores).
        Valida que haya saldo suficiente antes de retirar.
        Returns: saldo después del retiro
        """
        saldo_actual = self.obtener_saldo()
        if saldo_actual < monto:
            raise ValueError("Saldo insuficiente")

        producto_repository.update_cash_register_balance(
            self.cash_register_id, -monto  # negativo = retiro
        )
        return self.obtener_saldo()

    def to_dict(self):
        return {
            "saldo": self.obtener_saldo()
        }
