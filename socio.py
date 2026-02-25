# socio.py

import hashlib
from datetime import date, timedelta


class Socio:
    """
    Representa un socio del supermercado con descuentos.
    
    Responsabilidades:
    - Mantener datos del socio (id, usuario, password)
    - Validar contraseña
    - Verificar si está activo (pagó cuota)
    """
    
    def __init__(self, id_socio, usuario, password=None, password_hash=None, 
                 fecha_ultimo_pago=None, descuento=10):
        """
        Args:
            id_socio (str): ID único del socio
            usuario (str): Nombre de usuario
            password (str): Contraseña en texto plano (se hasheará)
            password_hash (str): Hash de la contraseña (si ya está hasheada)
            fecha_ultimo_pago (str): Fecha ISO del último pago
            descuento (int): Porcentaje de descuento (default 10%)
        """
        # Atributos privados (no deben modificarse desde fuera)
        self._id = id_socio
        self._usuario = usuario
        self._password_hash = None
        self._fecha_ultimo_pago = None
        self._descuento = descuento
        
        # ELIMINADO: self.carrito (no corresponde aquí)
        # ¿Por qué? El carrito es de la SESIÓN de venta, no del socio
        
        # Hashear contraseña
        if password_hash:
            # Si ya tenemos el hash (cargando desde JSON), lo usamos
            self._password_hash = password_hash
        elif password:
            # Si tenemos password en texto plano, lo hasheamos
            self._password_hash = self._hashear_password(password)
        else:
            raise ValueError("Debe proporcionarse password o password_hash")
        
        # Procesar fecha
        if fecha_ultimo_pago:
            self._fecha_ultimo_pago = date.fromisoformat(fecha_ultimo_pago)
        else:
            self._fecha_ultimo_pago = date.today()
    
    def _hashear_password(self, password):
        """
        Hashea una contraseña con SHA-256.
        
        ¿Por qué privado?
        - Es un detalle de implementación interna
        - Nadie fuera de la clase necesita llamarlo
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validar_password(self, password_ingresada):
        """
        Valida si la contraseña ingresada es correcta.
        
        Args:
            password_ingresada (str): Contraseña en texto plano
        
        Returns:
            bool: True si es correcta
        
        ¿Por qué este método?
        - Encapsulación: No exponemos el hash directamente
        - Seguridad: Comparamos hashes, no texto plano
        """
        return self._password_hash == self._hashear_password(password_ingresada)
    
    def esta_activo(self):
        """
        Verifica si el socio tiene la cuota al día (últimos 30 días).
        
        Returns:
            bool: True si está activo
        """
        hoy = date.today()
        return hoy <= self._fecha_ultimo_pago + timedelta(days=30)
    
    def registrar_pago(self):
        """Registra un pago de cuota (actualiza fecha)."""
        self._fecha_ultimo_pago = date.today()
    
    def to_dict(self):
        """
        Convierte el socio a diccionario para guardar en JSON.
        
        Returns:
            dict: Datos del socio serializables
        """
        return {
            "id_socio": self._id,  # ← CORREGIDO: era "id"
            "usuario": self._usuario,
            "password_hash": self._password_hash,
            "fecha_ultimo_pago": self._fecha_ultimo_pago.isoformat(),
            "descuento": self._descuento  # ← AGREGADO: faltaba
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Crea un socio desde un diccionario (cargar desde JSON).
        
        Args:
            data (dict): Datos del socio
        
        Returns:
            Socio: Nueva instancia
        """
        return cls(
            id_socio=data["id_socio"],
            usuario=data["usuario"],
            password_hash=data["password_hash"],
            fecha_ultimo_pago=data.get("fecha_ultimo_pago"),
            descuento=data.get("descuento", 10)  # ← AGREGADO: con default
        )
    
    # Properties para acceso controlado (SOLO LECTURA)
    
    @property
    def id(self):
        """ID del socio (solo lectura)."""
        return self._id
    
    @property
    def usuario(self):
        """Usuario del socio (solo lectura)."""
        return self._usuario
    
    @property
    def descuento(self):
        """Porcentaje de descuento (solo lectura)."""
        return self._descuento
    
    @property
    def fecha_ultimo_pago(self):
        """Fecha del último pago (solo lectura)."""
        return self._fecha_ultimo_pago