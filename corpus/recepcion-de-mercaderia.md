# Recepción de Mercadería

## Objeto y alcance

Establecer cómo se recibe producto farmacéutico en cualquiera de los tres sitios de Farmalog Sur, desde que el camión llega al portón hasta que el stock queda disponible en Sigma WMS.

Aplica a producto de laboratorio cliente y a devoluciones de droguería. **No** aplica a insumos propios (cajas, refrigerantes, papelería), que se reciben por otro procedimiento.

## Responsabilidades

| Quién                 | Qué                                                       |
|-----------------------|-----------------------------------------------------------|
| Operario de recepción | Ejecuta la verificación física y carga en Sigma WMS       |
| Jefe de Depósito      | Autoriza la descarga y resuelve discrepancias de cantidad |
| Analista de QA        | Revisa la documentación y decide liberación o cuarentena  |
| Dirección Técnica     | Decide sobre producto con documentación faltante o dudosa |

## Verificación previa a la descarga

Antes de que se abra la puerta del camión, el operario de recepción verifica:

1. Que el remito del transportista coincida con la orden esperada en Sigma WMS.
2. Que el precinto esté intacto y su número coincida con el declarado en el remito.
3. Para envíos refrigerados o congelados: que el **registrador de temperatura venga dentro del envío** y que su identificador figure en la documentación.

Si el precinto está violado o ausente, **no se descarga**: se deja el camión cerrado y se avisa al Jefe de Depósito y a un Analista de QA. La decisión de descargar o rechazar es de Calidad.

## Descarga de producto refrigerado

El producto refrigerado no puede permanecer en zona de recepción más de **30 minutos** desde que se abre la puerta del camión hasta que ingresa a cámara. Este es el límite duro del procedimiento.

Si por cualquier motivo se van a superar los 30 minutos, se interrumpe la descarga, se cierra el camión y se retoma cuando haya capacidad de cámara disponible. Superar los 30 minutos sin interrumpir genera desvío obligatorio en Qualis.

Para producto de ambiente controlado (15–25 °C) no hay límite de permanencia en recepción, pero sí aplica el requisito de no dejar pallets en zona de tránsito al cierre del turno.

## Descarga del registrador

Para todo envío con cadena de frío:

1. Se retira el registrador del bulto.
2. Se descarga en TermoTrack con el número de envío asociado.
3. TermoTrack genera el informe de trayecto y lo adjunta automáticamente al ingreso en Sigma WMS.

**El stock no se libera hasta que el informe de trayecto esté cargado y revisado.** Mientras tanto queda en estado CUAR (cuarentena).

Si el registrador viene descargado, dañado o no se puede leer, el envío se trata como excursión presunta y se aplica el procedimiento de Excursiones de Temperatura.

## Verificación documental

El Analista de QA verifica contra el remito y el certificado de análisis del lote:

- Producto, presentación y lote coinciden.
- Fecha de vencimiento **mayor a 12 meses** desde la fecha de recepción. Con menos de 12 meses de vida útil remanente, se recibe igual pero se marca el lote como VIDA-CORTA en Sigma WMS y se notifica al cliente dentro de las 24 horas.
- Cantidad recibida = cantidad declarada. Cualquier diferencia se registra como discrepancia, aunque sea a favor.

## Liberación

Un lote pasa de CUAR a DISP (disponible) cuando se cumplen las cuatro condiciones:

1. Informe de trayecto sin excursiones, o excursión evaluada y aceptada por la DT.
2. Documentación completa y coincidente.
3. Inspección visual de bultos sin daño.
4. Registro de recepción firmado en Sigma WMS por el operario y por el Analista de QA.

La liberación la carga el Analista de QA. **La Dirección Técnica sólo interviene cuando hay excursión, documentación faltante o producto de trazabilidad especial.**

## Registros que genera este procedimiento

| Registro              | Dónde vive | Retención |
|-----------------------|------------|-----------|
| Registro de recepción | Sigma WMS  | 5 años    |
| Informe de trayecto   | TermoTrack | 5 años    |
| Desvío, si se generó  | Qualis     | 5 años    |
