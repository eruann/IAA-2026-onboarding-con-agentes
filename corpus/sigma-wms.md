# Sigma WMS

## Para qué sirve este manual

Este manual cubre las operaciones más frecuentes. El manual completo del proveedor está en Qualis, sección Sistemas.

## Ingreso

Sigma WMS se accede desde sigma.farmalogsur.local, sólo desde la red de cada sitio. **No hay acceso remoto ni por VPN**, por decisión de política de seguridad informática. Si necesitás consultar algo desde afuera, pedile a alguien en sitio o esperá.

El usuario es tu usuario de red. Si te bloqueaste, llamá a Mesa de Ayuda (interno 100).

## Estados de lote

| Estado     | Significado                                        | Quién lo puede cambiar                  |
|------------|----------------------------------------------------|-----------------------------------------|
| RECE       | Recibido, pendiente de verificación                | automático al cargar recepción          |
| CUAR       | En cuarentena, bloqueado                           | perfil Calidad, o automático por alarma |
| DISP       | Disponible para picking y despacho                 | perfil Calidad                          |
| VIDA-CORTA | Disponible pero con menos de 12 meses de vida útil | perfil Calidad                          |
| RETE       | Retenido por retiro del mercado                    | perfil Calidad                          |
| DEST       | Destinado a destrucción                            | perfil Calidad                          |

Sólo el perfil **Calidad** mueve lotes entre estados. El perfil Supervisor puede hacer ajustes de inventario pero **no** liberar de cuarentena.

## Buscar un lote

Stock \> Consulta de lote. Se puede buscar por:

- Número de lote (exacto).
- Código de producto.
- Serial individual, en la solapa **Trazabilidad** (no en la consulta general — error frecuente).

La consulta por serial es la que se usa en auditoría y muestra el historial completo de eventos de esa unidad.

## Cargar una recepción

Recepción \> Nueva. Campos obligatorios: proveedor/laboratorio, remito, producto, lote, vencimiento, cantidad, número de registrador si aplica.

Al guardar, el sistema:

1. Deja el lote en RECE.
2. Si el envío es de cadena de frío, exige la carga del informe de trayecto de TermoTrack antes de permitir el pase a DISP.
3. Genera el evento de trazabilidad si el producto está alcanzado.

**No se puede editar una recepción guardada.** Si te equivocaste, se anula y se rehace, y la anulación queda registrada con tu usuario. Sobrescribir un lote existente ("pisar el lote") no es posible desde la interfaz, pero sí por carga masiva, y por eso la carga masiva está limitada a Administrador.

## Cambiar un lote de estado

Stock \> Consulta de lote \> Acciones \> Cambiar estado. Pide:

- Estado destino.
- Motivo (lista cerrada).
- Número de desvío de Qualis, **obligatorio** si el destino es CUAR por excursión o por hallazgo de calidad.

El sistema no deja pasar un lote de CUAR a DISP sin que haya un desvío cerrado o una decisión de DT cargada. Es el control automático que evita la liberación informal.

## Generar un remito

Despacho \> Armado de pedido, se seleccionan las líneas, se confirma el picking y se emite el remito. Para envíos de cadena de frío, el sistema exige antes:

- La configuración de kit (ver Kit Térmico y Despacho).
- El número de registrador activado.
- El número de precinto.

Si falta cualquiera de los tres, el remito no se emite. No es un bug.

## Informes que más se usan en Calidad

| Informe                                  | Para qué                                                |
|------------------------------------------|---------------------------------------------------------|
| Lotes en cuarentena por antigüedad       | Detectar cuarentenas olvidadas                          |
| Recepciones sin informe de trayecto      | Control diario de cadena de frío                        |
| Transacciones de trazabilidad rechazadas | Revisión diaria de la Responsable de Trazabilidad ANMAT |
| Historial de lote                        | Punta a punta, para auditoría                           |
| Ajustes de inventario del período        | Revisión de desvíos de stock                            |

## Errores frecuentes

| Mensaje                                 | Qué significa realmente                                           |
|-----------------------------------------|-------------------------------------------------------------------|
| "Lote sin informe de trayecto asociado" | Falta descargar el registrador en TermoTrack                      |
| "Perfil sin permiso para la acción"     | Estás con perfil Consulta; todavía no completaste la calificación |
| "Secuencia de trazabilidad inválida"    | Se está informando un despacho de algo nunca recibido             |
| "Kit no habilitado para el destino"     | La autonomía del kit elegido no cubre el destino                  |
| "Sesión sólo disponible en red local"   | Estás intentando entrar por VPN; no se puede                      |
