# registro_socio.py
#
# Gestiona socios/miembros del negocio.
# Usa la tabla member (antes: socio) del nuevo schema.

import hashlib
from socio import Socio
from database import producto_repository


class RegistroSocio:
    """
    Gestiona miembros/socios desde SQLite con la tabla member.
    """

    def __init__(self):
        pass

    def agregar_socio(self, usuario, password):
        """Agrega un nuevo socio/miembro a SQLite"""
        if isinstance(usuario, str):
            dni = usuario  # Usar nombre como DNI temporal
        else:
            dni = str(usuario)

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            # Insertar en la tabla member
            socio_id = producto_repository.create_member(
                name=usuario,
                dni=dni,
                password_hash=password_hash
            )

            # Retornar objeto Socio para compatibilidad
            nuevo_socio = Socio(
                id_socio=socio_id,
                usuario=usuario,
                password_hash=password_hash,
                descuento=10
            )
            return nuevo_socio

        except Exception as e:
            if "UNIQUE" in str(e):
                raise ValueError("El usuario ya existe")
            raise

    def buscar_por_usuario(self, usuario):
        """Busca un socio/miembro por nombre"""
        resultado = producto_repository.get_member_by_name(usuario)

        if resultado:
            id_, nombre, dni, password_hash, activo = resultado
            return Socio(
                id_socio=id_,
                usuario=nombre,
                password_hash=password_hash,
                descuento=10
            )
        return None

    def autenticar(self, usuario, password):
        """Autentica un socio verificando contraseña"""
        socio = self.buscar_por_usuario(usuario)

        if socio and socio.validar_password(password):
            return socio

        return None
