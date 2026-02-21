# Sistema de Caja Registradora en Python

Proyecto personal desarrollado para aprender arquitectura de software, separación de responsabilidades y gestión de estado en aplicaciones de consola.

## Funcionalidades actuales

- Gestión de productos y stock
- Carrito de compras
- Confirmación de venta
- Actualización automática de inventario
- Sistema de socios
- Persistencia en archivos CSV
- Módulo de estadísticas
- Arquitectura modular (separación por capas)

## Arquitectura

El sistema está dividido en módulos:

- main.py → flujo principal e interfaz
- ventas.py → lógica de venta
- productos.py → gestión de productos
- persistencia.py → lectura y escritura de archivos
- estadisticas.py → análisis de ventas
- socios.py → gestión de socios

Se aplicó separación entre:
- lógica de negocio
- interfaz
- persistencia de datos

## Lo que aprendí en este proyecto

- Refactorización progresiva
- Separación de responsabilidades
- Manejo de estado mutable
- Uso práctico de Git y control de versiones
- Persistencia con CSV
- Diseño orientado a escalabilidad

## Próximos pasos

- Implementar modo gerente
- Introducir primeras clases (Carrito, Inventario)
- Mejorar separación UI / lógica
- Migrar ciertos datos a JSON si es necesario
- Agregar análisis de productos más vendidos

---

Proyecto en evolución constante.