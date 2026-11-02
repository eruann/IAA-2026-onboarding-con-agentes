# Kit Térmico y Despacho

## Objeto

Definir cómo se acondiciona y despacha producto que requiere control de temperatura durante el transporte.

## Configuraciones de kit habilitadas

Sólo se pueden usar las configuraciones validadas. Usar una combinación no listada es desvío crítico, aunque "parezca que va a funcionar".

| Configuración | Rango objetivo | Autonomía validada | Uso                                    |
|---------------|----------------|--------------------|----------------------------------------|
| K2-24         | 2–8 °C         | 24 horas           | AMBA y Gran La Plata                   |
| K2-48         | 2–8 °C         | 48 horas           | Interior, destinos con conexión diaria |
| K2-72         | 2–8 °C         | 72 horas           | Patagonia y NOA                        |
| KA-48         | 15–25 °C       | 48 horas           | Ambiente controlado en verano          |
| KF-24         | −25 a −15 °C   | 24 horas           | Congelado, sólo desde Sarandí          |

La autonomía validada se declaró con perfil de verano (peor caso). No se extiende "porque hace frío afuera".

## Acondicionamiento de refrigerantes

Los refrigerantes (geles) tienen que estar **acondicionados**, no simplemente congelados. El acondicionamiento es el período de estabilización a temperatura intermedia que evita que el gel congelado toque el producto y lo congele.

| Kit                   | Preparación del gel                    | Tiempo de acondicionamiento                |
|-----------------------|----------------------------------------|--------------------------------------------|
| K2-24 / K2-48 / K2-72 | Congelado a −20 °C, luego estabilizado | **mínimo 4 horas** a 2–8 °C antes de armar |
| KA-48                 | Refrigerado a 5 °C                     | 2 horas a ambiente                         |
| KF-24                 | Congelado a −20 °C                     | sin acondicionamiento                      |

Armar un kit frío con geles recién sacados del freezer es el error clásico y produce **congelamiento del producto**, que es una excursión tan grave como el calor. Una insulina congelada se descarta igual que una insulina a 30 °C.

## Secuencia de armado

1. Verificar en Sigma WMS la configuración de kit que corresponde al destino y al producto.
2. Retirar la caja isotérmica y verificar que no tenga fisuras ni el aislante húmedo.
3. Colocar la capa inferior de geles acondicionados.
4. Colocar el producto **envuelto en la lámina separadora**, nunca en contacto directo con el gel.
5. Colocar el **registrador de temperatura activado**, junto al producto, no pegado al gel.
6. Colocar la capa superior de geles.
7. Cerrar, precintar y registrar en Sigma WMS: número de kit, número de registrador, número de precinto.

El registrador se activa **antes** de cerrar y se verifica que esté registrando. Un registrador sin activar equivale a un envío sin registro, y ya sabemos qué significa eso acá.

## Ventana de despacho

Desde que se cierra el kit hasta que el camión sale no pueden pasar más de **2 horas**. El kit consume autonomía desde que se cierra, no desde que sale.

Si el despacho se demora más de 2 horas, el kit se desarma, el producto vuelve a cámara y se rearma con geles nuevos acondicionados cuando el camión esté disponible.

## Documentación que viaja

| Documento                                         | Emite                               |
|---------------------------------------------------|-------------------------------------|
| Remito                                            | Sigma WMS                           |
| Constancia de acondicionamiento                   | Sigma WMS, se imprime con el remito |
| Instructivo de contingencia para el transportista | Adjunto fijo                        |

## Qué se le dice al transportista

Tres cosas, siempre, aunque sea el mismo chofer de siempre:

1. Que el bulto no se abre por ningún motivo hasta destino.
2. Que si hay demora mayor a la autonomía del kit, llame a \#ops-sarandi o al teléfono de guardia antes de improvisar.
3. Que el registrador viaja adentro y se descarga en destino.

## Registro de salida

La salida se confirma en Sigma WMS con hora real de partida. La constancia de acondicionamiento más la hora de cierre del kit y la hora de salida son lo que permite reconstruir la autonomía consumida si después aparece una excursión. Sin esas tres horas cargadas, la evaluación de impacto del procedimiento de Excursiones de Temperatura no se puede hacer.
