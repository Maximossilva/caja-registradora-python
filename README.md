# Sistema de Supermercado (Backend en evolución)

Proyecto personal orientado a aprender arquitectura de software,
persistencia de datos y backend profesional en Python.

---

## Estado actual

Versión estable con:

- Arquitectura modular
- Persistencia en JSON
- Flujo cliente (main)
- Flujo gerente (main_gerente)
- Gestión de productos
- Gestión de proveedores
- Registro de ventas
- Sistema de caja
- Registro de socios
- Ticket de compra

Próxima migración: SQLite como base de datos real.

---

## Arquitectura

El proyecto está dividido en:

- **Dominio** → Entidades (Producto, Venta, Socio, Caja, etc.)
- **Servicios** → Lógica de negocio
- **Persistencia** → Actualmente JSON (en transición a SQLite)
- **Interfaz** → Consola (cliente y gerente)

---

## Objetivos del proyecto

- Migrar de JSON a SQLite
- Implementar relaciones reales con claves foráneas
- Soporte para múltiples cajas
- Estadísticas de ventas
- Exponer API REST con FastAPI
- Deploy en la nube
- Frontend simple conectado al backend

---

## Cómo ejecutar

```bash
python main.py