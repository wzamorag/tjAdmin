# 📖 Manual del Sistema de Restaurante Tía Juana

## Índice de Contenidos

1. [Introducción](#introducción)
2. [Acceso al Sistema](#acceso-al-sistema)
3. [Roles y Permisos](#roles-y-permisos)
4. [Gestión de Usuarios](#gestión-de-usuarios)
5. [Configuración del Menú](#configuración-del-menú)
6. [Gestión de Ingredientes e Inventario](#gestión-de-ingredientes-e-inventario)
7. [Sistema de Compras](#sistema-de-compras)
8. [Toma de Órdenes](#toma-de-órdenes)
9. [Despacho de Cocina y Bar](#despacho-de-cocina-y-bar)
10. [Sistema de Cobros](#sistema-de-cobros)
11. [Gestión de Anulaciones](#gestión-de-anulaciones)
12. [Sistema de Promociones](#sistema-de-promociones)
13. [Reportes y Análisis](#reportes-y-análisis)
14. [Monitoreo y Control](#monitoreo-y-control)
15. [Cierre Diario](#cierre-diario)
16. [Solución de Problemas](#solución-de-problemas)

---

## Introducción

El **Sistema de Restaurante Tía Juana** es una solución integral para la gestión completa de restaurantes que incluye:

- ✅ Control de inventarios y stock
- ✅ Toma de órdenes digitalizada
- ✅ Sistema de cobros con múltiples métodos de pago
- ✅ Despacho de cocina y bar
- ✅ Reportes avanzados y análisis de ventas
- ✅ Gestión de usuarios con roles específicos
- ✅ Sistema de promociones temporales
- ✅ Control de anulaciones y reversiones

---

## Acceso al Sistema

### 🔐 Página de Login

1. **Acceder al sistema**: Abrir la aplicación en el navegador
2. **Introducir credenciales**:
   - **Usuario**: Nombre de usuario asignado
   - **Contraseña**: Contraseña personal
3. **Iniciar sesión**: Hacer clic en "Iniciar Sesión"

### 🏠 Redirección Automática por Rol

El sistema redirige automáticamente según el rol del usuario:
- **Administradores**: Dashboard principal con acceso completo
- **Meseros**: Página de toma de órdenes
- **Personal de Cocina**: Panel de cocina
- **Personal de Bar**: Panel de bar
- **Cajeros**: Sistema de cobros

---

## Roles y Permisos

### 👑 Administrador (Rol 1)
**Acceso completo al sistema:**
- ✅ Gestión de usuarios y roles
- ✅ Configuración de menús y platos
- ✅ Control de inventario y compras
- ✅ Aprobación de anulaciones
- ✅ Reportes avanzados
- ✅ Gestión de promociones
- ✅ Configuración del sistema

### 💰 Cajero (Rol 2)
**Operaciones de caja:**
- ✅ Sistema de cobros
- ✅ Procesamiento de pagos
- ✅ Generación de tickets
- ✅ Consulta de órdenes
- ✅ Reportes básicos de ventas

### 👨‍🍳 Mesero (Rol 3)
**Atención al cliente:**
- ✅ Toma de órdenes
- ✅ Gestión de mesas
- ✅ Consulta de estado de órdenes
- ✅ Solicitud de anulaciones
- ✅ Entrega de órdenes

### 🍹 Personal de Bar (Rol 4)
**Despacho de bebidas:**
- ✅ Panel de bar
- ✅ Despacho de bebidas
- ✅ Actualización de estado de preparación
- ✅ Control de inventario de bar

### 🍳 Personal de Cocina (Rol 5)
**Preparación de alimentos:**
- ✅ Panel de cocina
- ✅ Despacho de platos
- ✅ Actualización de estado de preparación
- ✅ Control de tiempos de cocción

---

## Gestión de Usuarios

### ➕ Crear Usuario

1. **Acceder a "Gestión de Usuarios"**
2. **Completar información básica**:
   - Nombre completo
   - Nombre de usuario (único)
   - Contraseña inicial
   - Teléfono y correo electrónico
3. **Asignar rol**: Seleccionar el rol apropiado
4. **Estado**: Activar/desactivar usuario
5. **Guardar**: Confirmar creación

### ✏️ Editar Usuario

1. **Buscar usuario**: Usar filtros o lista completa
2. **Seleccionar "Editar"**
3. **Modificar campos** necesarios
4. **Cambiar rol** si es necesario
5. **Actualizar contraseña** (opcional)
6. **Guardar cambios**

### 🔍 Consultar Usuarios

- **Lista completa**: Ver todos los usuarios registrados
- **Filtros**: Por rol, estado activo/inactivo
- **Información**: Último acceso, estado, datos personales

---

## Configuración del Menú

### 📝 Gestión de Categorías

1. **Acceder a "Gestión de Menú"**
2. **Crear categorías**:
   - **Bar**: Bebidas, cócteles, licores
   - **Cocina**: Platos principales, entradas, postres
3. **Configurar estado**: Activar/desactivar categorías

### 🍽️ Gestión de Platos

#### ➕ Agregar Plato
1. **Información básica**:
   - Nombre del plato
   - Descripción detallada
   - Precio de venta
2. **Categorización**:
   - Seleccionar menú (Bar/Cocina)
   - Asignar categoría
3. **Estado**: Activar plato para venta
4. **Guardar**: Confirmar creación

#### 🔧 Configurar Ingredientes por Plato
1. **Seleccionar plato** existente
2. **Agregar ingredientes**:
   - Seleccionar ingrediente del inventario
   - Especificar cantidad necesaria
   - Confirmar unidad de medida
3. **Receta completa**: Asegurar todos los ingredientes estén incluidos

### 📊 Control de Disponibilidad

- **Stock automático**: El sistema calcula automáticamente si hay suficientes ingredientes
- **Platos no disponibles**: Se marcan automáticamente cuando faltan ingredientes
- **Actualización en tiempo real**: Disponibilidad se actualiza con cada venta

---

## Gestión de Ingredientes e Inventario

### 📦 Registro de Ingredientes

1. **Acceder a "Gestión de Ingredientes"**
2. **Agregar ingrediente**:
   - Nombre del ingrediente
   - Unidad de medida (gramos, litros, unidades, etc.)
   - Costo unitario
   - Stock inicial
3. **Configurar alertas**:
   - Stock mínimo crítico
   - Stock mínimo de advertencia
4. **Activar**: Habilitar para uso en recetas

### 📋 Control de Inventario

#### 📥 Movimientos de Entrada
1. **Seleccionar "Movimiento de Entrada"**
2. **Elegir ingrediente**
3. **Especificar cantidad**
4. **Indicar motivo**: Compra, ajuste, donación, etc.
5. **Registrar**: Confirmar entrada

#### 📤 Movimientos de Salida
1. **Seleccionar "Movimiento de Salida"**
2. **Elegir ingrediente**
3. **Especificar cantidad**
4. **Indicar motivo**: Venta, desperdicio, ajuste, etc.
5. **Registrar**: Confirmar salida

#### 🔍 Consulta de Stock
- **Stock actual**: Visualización en tiempo real
- **Historial de movimientos**: Registro completo de entradas y salidas
- **Usuario responsable**: Trazabilidad de cada movimiento
- **Alertas**: Notificaciones automáticas de stock bajo

---

## Sistema de Compras

### 🏪 Gestión de Proveedores

1. **Registrar proveedor**:
   - Nombre comercial y razón social
   - NIT y NRC (si aplica)
   - Datos de contacto
   - Tipo: Normal o Sujeto Excluido
2. **Estado**: Activar/desactivar proveedores

### 🛒 Registro de Compras

1. **Crear nueva compra**:
   - Seleccionar proveedor
   - Fecha de compra
   - Número de factura (opcional)
2. **Agregar productos**:
   - Seleccionar ingrediente
   - Cantidad comprada
   - Costo unitario
   - Calcular subtotal automático
3. **Finalizar compra**:
   - Revisar total
   - Confirmar compra
   - Generar factura en PDF

### 📄 Beneficios del Sistema de Compras

- **Actualización automática de inventario**
- **Control de costos por proveedor**
- **Generación de facturas profesionales**
- **Historial completo de compras**
- **Análisis de gastos por período**

---

## Toma de Órdenes

### 📱 Interfaz de Meseros

1. **Seleccionar mesa**: Elegir mesa disponible
2. **Agregar productos**:
   - Navegar por categorías (Bar/Cocina)
   - Seleccionar platos disponibles
   - Especificar cantidad
   - Agregar comentarios especiales
3. **Revisar orden**:
   - Verificar productos y cantidades
   - Calcular total automático
   - Modificar si es necesario
4. **Confirmar orden**: Enviar a cocina/bar

### 🍽️ Gestión de Mesas

#### Estados de Mesa:
- **🟢 Disponible**: Mesa libre para nuevos clientes
- **🔴 Ocupada**: Mesa con orden activa
- **🟡 Por limpiar**: Mesa pendiente de limpieza

#### Configuración de Mesas:
1. **Acceso administrativo** a "Gestión de Mesas"
2. **Crear/editar mesas**:
   - Número identificativo
   - Capacidad de personas
   - Descripción opcional
3. **Activar/desactivar** mesas según necesidad

### 📋 Estados de Órdenes

1. **🔄 Pendiente**: Orden registrada, esperando preparación
2. **👨‍🍳 Preparando**: En proceso de cocina/bar
3. **✅ Lista**: Preparada, pendiente de entrega
4. **🚚 Entregada**: Entregada al cliente, pendiente de pago
5. **💰 Pagada**: Orden completada y pagada

---

## Despacho de Cocina y Bar

### 🍳 Panel de Cocina

1. **Vista de órdenes pendientes**:
   - Lista de platos por orden
   - Información de mesa y mesero
   - Comentarios especiales del cliente
2. **Despacho individual**:
   - Marcar plato como "Preparado"
   - Registro automático de usuario y hora
3. **Control de tiempos**:
   - Tiempo transcurrido desde orden
   - Alertas por demoras excesivas
4. **Actualización en tiempo real**:
   - Refresh automático de órdenes
   - Notificaciones de nuevas órdenes

### 🍹 Panel de Bar

1. **Vista de bebidas pendientes**:
   - Lista específica de productos de bar
   - Priorización por tiempo de orden
2. **Despacho de bebidas**:
   - Marcar bebida como "Lista"
   - Control de stock automático
3. **Gestión de inventario**:
   - Actualización automática por despacho
   - Alertas de productos agotados

---

## Sistema de Cobros

### 💳 Procesamiento de Pagos

1. **Seleccionar orden lista**:
   - Vista de órdenes completadas
   - Información detallada de productos
   - Total calculado automáticamente

2. **Métodos de pago disponibles**:

#### 💵 Efectivo
- Ingresar monto recibido
- Cálculo automático de cambio
- Validación de monto suficiente

#### 💳 Tarjeta de Crédito/Débito
- Registro de transacción
- Número de referencia
- Tipo de tarjeta

#### 🏦 Transferencia Bancaria
- Número de referencia
- Banco emisor
- Validación de transacción

3. **Generar ticket**:
   - Ticket profesional en PDF
   - Información fiscal completa
   - Detalle de productos y pagos
   - Código QR para verificación

### 🧾 Características de los Tickets

- **Formato profesional** con logo del restaurante
- **Información fiscal** completa
- **Detalle itemizado** de productos
- **Totales claros** con impuestos
- **Método de pago** especificado
- **Fecha y hora** de transacción
- **Usuario cajero** responsable

---

## Gestión de Anulaciones

### 🗑️ Anulaciones de Productos Individuales

#### Proceso para Meseros:
1. **Solicitar anulación**:
   - Seleccionar producto específico
   - Indicar motivo detallado
   - Enviar solicitud a administración

#### Proceso para Administradores:
1. **Revisar solicitud**:
   - Evaluar motivo de anulación
   - Verificar información de la orden
2. **Tomar decisión**:
   - ✅ **Aprobar**: Reversión automática de inventario
   - ❌ **Rechazar**: Mantener producto en orden
3. **Notificación automática** al mesero solicitante

### 🗑️ Anulaciones de Órdenes Completas

1. **Solicitud de anulación**:
   - Mesero o administrador puede solicitar
   - Motivo detallado obligatorio
   - Confirmación requerida
2. **Proceso de aprobación**:
   - Validación administrativa
   - Revisión de inventario afectado
3. **Ejecución de anulación**:
   - Reversión completa de inventario
   - Registro en histórico de anulaciones
   - Actualización de estados

### 📊 Beneficios del Sistema de Anulaciones

- **Control total** de productos cancelados
- **Reversión automática** de inventario
- **Trazabilidad completa** de responsables
- **Reportes** de anulaciones para análisis
- **Flujo de aprobación** estructurado

---

## Sistema de Promociones

### 🎉 Creación de Promociones

1. **Información básica**:
   - Nombre de la promoción
   - Descripción detallada
   - Porcentaje de descuento
2. **Configuración temporal**:
   - Fecha y hora de inicio
   - Fecha y hora de fin
   - Duración automática
3. **Tipo de menú**:
   - **Bar**: Solo productos de bar
   - **Cocina**: Solo platos de cocina
4. **Estado**: Programada → Activa → Vencida

### ⚡ Activación Rápida

Botones de activación inmediata:
- **30 minutos**: Promoción express
- **1 hora**: Promoción de hora feliz
- **2 horas**: Promoción extendida
- **Personalizado**: Definir tiempo específico

### 📈 Control de Promociones

- **Vista de promociones activas**: Monitoreo en tiempo real
- **Historial de promociones**: Registro completo
- **Análisis de efectividad**: Ventas durante promociones
- **Activación/desactivación**: Control manual si es necesario

---

## Reportes y Análisis

### 📊 Reportes de Ventas

#### 📈 Reporte Diario/Semanal/Mensual
1. **Seleccionar período**: Día, semana, mes o personalizado
2. **Visualización**:
   - Total de ventas
   - Cantidad de órdenes
   - Productos más vendidos
   - Horarios de mayor actividad
3. **Exportación**: PDF y Excel disponibles

#### 🎯 Análisis de Márgenes
- **Cálculo automático** de ganancias por producto
- **Comparación costo vs precio** de venta
- **Análisis de rentabilidad** por período
- **Recomendaciones** de optimización

### 👨‍🍳 Reportes por Meseros

1. **Rendimiento individual**:
   - Ventas totales por mesero
   - Cantidad de mesas atendidas
   - Promedio de venta por mesa
2. **Análisis de propinas**:
   - Estimación de propinas por ventas
   - Comparación entre meseros
3. **Evaluación de desempeño**:
   - Órdenes completadas vs canceladas
   - Tiempo promedio de atención

### 📦 Reportes de Inventario

1. **Estado actual de stock**:
   - Productos con stock crítico
   - Valorización de inventario
   - Próximos vencimientos
2. **Movimientos de inventario**:
   - Entradas y salidas por período
   - Productos más utilizados
   - Análisis de desperdicios

### 🛒 Reportes de Compras

1. **Análisis de proveedores**:
   - Gastos por proveedor
   - Frecuencia de compras
   - Evaluación de costos
2. **Historial de compras**:
   - Compras por período
   - Productos más comprados
   - Tendencias de precios

### 📄 Formatos de Exportación

- **📊 Excel**: Datos tabulados para análisis
- **📄 PDF**: Reportes profesionales para presentación
- **📈 Gráficos interactivos**: Visualizaciones dinámicas
- **🎯 Filtros avanzados**: Personalización de consultas

---

## Monitoreo y Control

### 🖥️ Monitor de Órdenes (Administrativo)

1. **Vista unificada**:
   - Todas las órdenes activas
   - Estados en tiempo real
   - Tiempos de preparación
2. **Alertas automáticas**:
   - Órdenes con demora excesiva
   - Productos agotados
   - Mesas sin atender
3. **Control de flujo**:
   - Identificación de cuellos de botella
   - Redistribución de cargas de trabajo

### 👨‍🍳 Monitor de Meseros

1. **Rendimiento en tiempo real**:
   - Órdenes activas por mesero
   - Mesas asignadas
   - Estado de órdenes
2. **Métricas de productividad**:
   - Tiempo promedio por mesa
   - Satisfacción del cliente
   - Ventas generadas
3. **Alertas de gestión**:
   - Meseros sobrecargados
   - Mesas sin atender
   - Órdenes pendientes de entrega

### ⏱️ Control de Tiempos

- **Tiempo de preparación**: Desde orden hasta listo
- **Tiempo de entrega**: Desde listo hasta entregado
- **Tiempo total**: Experiencia completa del cliente
- **Benchmarks**: Comparación con estándares establecidos

---

## Cierre Diario

### 📋 Cierre Z

1. **Resumen diario automático**:
   - Total de ventas del día
   - Cantidad de órdenes procesadas
   - Métodos de pago utilizados
   - Productos más vendidos

2. **Información detallada**:
   - Ventas por hora
   - Rendimiento por mesero
   - Estado de inventario
   - Anulaciones del día

3. **Generación de reporte**:
   - PDF profesional para archivo
   - Información fiscal completa
   - Registro en historial de cierres

### 🎯 Beneficios del Cierre Diario

- **Control fiscal** diario
- **Detección temprana** de discrepancias
- **Análisis de tendencias** diarias
- **Base para proyecciones** futuras
- **Cumplimiento regulatorio**

---

## Solución de Problemas

### ❗ Problemas Comunes y Soluciones

#### 🔐 Problemas de Acceso
**Problema**: No puedo iniciar sesión
**Soluciones**:
- Verificar usuario y contraseña
- Contactar al administrador para reset
- Revisar estado de cuenta (activa/inactiva)

#### 📱 Problemas con Órdenes
**Problema**: No aparecen productos en el menú
**Soluciones**:
- Verificar disponibilidad de ingredientes
- Revisar si el plato está activado
- Contactar a administración para restock

**Problema**: Orden no aparece en cocina/bar
**Soluciones**:
- Refrescar pantalla de cocina/bar
- Verificar estado de la orden
- Revisar conectividad de red

#### 💰 Problemas de Cobro
**Problema**: No puedo procesar el pago
**Soluciones**:
- Verificar que la orden esté completada
- Revisar método de pago seleccionado
- Verificar conectividad para tarjetas

#### 📊 Problemas con Reportes
**Problema**: Reporte no genera datos
**Soluciones**:
- Verificar rango de fechas seleccionado
- Confirmar permisos de acceso al reporte
- Revisar filtros aplicados

### 📞 Contacto de Soporte

Para problemas técnicos que no se resuelvan con esta guía:
1. **Documentar el problema**: Captura de pantalla si es posible
2. **Contactar al administrador del sistema**
3. **Proporcionar información**:
   - Usuario afectado
   - Hora del problema
   - Pasos previos al error
   - Mensaje de error (si aplica)

### 🔄 Mantenimiento Preventivo

#### Recomendaciones diarias:
- **Cierre Z diario** completo
- **Respaldo de datos** automático
- **Limpieza de caché** del navegador si es necesario

#### Recomendaciones semanales:
- **Revisión de stock crítico**
- **Análisis de reportes de ventas**
- **Verificación de usuarios activos**

#### Recomendaciones mensuales:
- **Auditoría completa de inventario**
- **Evaluación de rendimiento del sistema**
- **Capacitación de usuarios nuevos**

---

## 🎯 Consejos para Maximizar el Uso del Sistema

### Para Administradores:
1. **Revisar diariamente** las alertas de stock
2. **Analizar semanalmente** los reportes de ventas
3. **Capacitar regularmente** al personal
4. **Mantener actualizada** la información de menú y precios

### Para Meseros:
1. **Verificar disponibilidad** antes de tomar órdenes
2. **Usar comentarios** para especificaciones especiales
3. **Confirmar órdenes** antes de enviar a cocina
4. **Mantener actualizado** el estado de las mesas

### Para Personal de Cocina/Bar:
1. **Revisar constantemente** el panel de órdenes
2. **Despachar en orden** de llegada
3. **Comunicar** problemas de stock inmediatamente
4. **Mantener tiempos** de preparación óptimos

### Para Cajeros:
1. **Verificar completitud** de órdenes antes de cobrar
2. **Confirmar método de pago** con el cliente
3. **Revisar totales** antes de procesar
4. **Entregar tickets** siempre al cliente

---

## 📞 Información de Contacto

**Sistema de Restaurante Tía Juana**
- **Versión**: 1.0
- **Soporte Técnico**: Contactar al administrador del sistema
- **Última Actualización**: 2025

---

**¡Gracias por utilizar el Sistema de Restaurante Tía Juana!**

Este manual será actualizado conforme se agreguen nuevas funcionalidades al sistema.