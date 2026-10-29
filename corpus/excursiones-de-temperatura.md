# Excursiones de Temperatura

## Objeto

Definir qué hacer **cuando la temperatura ya se salió del rango permitido**, en cámara o en tránsito. Este es el procedimiento de emergencia de la empresa. El monitoreo en condiciones normales está en Control de Temperatura en Cámaras.

## Definición

Se considera excursión toda salida del rango operativo declarado para el producto, sin importar la duración. Un solo registro de 8,3 °C en una cámara fría es una excursión.

No son excursiones: las alarmas preventivas, las lecturas durante una apertura de puerta registrada menor a 10 minutos que recupera rango sola, y las diferencias entre termómetro de referencia y sensor (eso es un problema de instrumento, ver Control de Temperatura en Cámaras, sección Verificación manual diaria).

## Los primeros 15 minutos

Ante una alarma crítica, quien la reciba ejecuta en este orden:

1. **Aislar, no mover.** El producto afectado no se toca, no se cambia de cámara y no se despacha. Si hay un despacho en curso con ese producto, se frena.
2. **Bloquear en Sigma WMS.** Pasar el stock afectado a estado CUAR.
3. **Avisar.** Mensaje en \#alertas-termotrack indicando cámara, hora, temperatura registrada y productos involucrados.
4. **Llamar por teléfono** al Supervisor de Cámaras o al Jefe de Depósito. Slack no alcanza: si la alarma es crítica, se llama.

No se espera a tener la causa identificada para hacer estos cuatro pasos.

## A quién se escala

| Cuándo                                           | A quién se llama                                                                                  |
|--------------------------------------------------|---------------------------------------------------------------------------------------------------|
| Lunes a viernes, 7 a 19 hs                       | La Supervisora de Cámaras Frías. Si no responde en 10 min, el Jefe de Depósito Sarandí.           |
| Fuera de ese horario, fines de semana y feriados | **El Director Técnico suplente, que está de guardia**                                             |
| Excursión en tránsito (camión en ruta)           | El Jefe de Transporte y Distribución y en paralelo el paso anterior                               |

La Directora Técnica se involucra siempre, pero la llamada inicial fuera de horario va al DT suplente de guardia, no a ella. Quién ocupa cada puesto figura en el Organigrama.

## Evaluación de impacto

Dentro de las **24 horas** de detectada, el Analista de QA arma el legajo de la excursión con:

- Curva completa de temperatura descargada de TermoTrack (no un resumen: la curva).
- Tiempo total fuera de rango y temperatura máxima/mínima alcanzada.
- Listado de lotes afectados con cantidades.
- Historial de excursiones previas de esos mismos lotes (el efecto es acumulativo).

Con eso se consulta la **especificación de estabilidad del producto**, que provee el laboratorio cliente. Cada producto tolera distinto: algunos biológicos de Verenta no toleran ni una hora fuera de rango; varios genéricos de Nortelab toleran desviaciones importantes.

## Quién decide el destino del producto

La decisión de **liberar, reprocesar o destruir** producto que sufrió una excursión es exclusiva de la **Dirección Técnica**. No la puede tomar el Gerente de Calidad, ni el Gerente de Operaciones, ni el cliente por teléfono.

En productos de Verenta, además, la decisión requiere conformidad escrita del laboratorio antes de liberar. Sin ese correo, el lote no sale aunque la DT lo considere apto.

## Plazos

| Acción                                   | Plazo máximo                |
|------------------------------------------|-----------------------------|
| Aislamiento y bloqueo en Sigma WMS       | Inmediato                   |
| Aviso en \#alertas-termotrack y llamado  | 15 minutos                  |
| Apertura del desvío en Qualis            | 24 horas                    |
| Legajo de evaluación de impacto completo | 24 horas                    |
| Decisión de la DT                        | 72 horas desde la detección |
| Notificación al laboratorio cliente      | 48 horas                    |
| Plan de CAPA cargado                     | 10 días hábiles             |

## Excursión en tránsito

Si el registrador de un envío en curso muestra excursión al llegar a destino:

1. El destinatario **no recibe** el producto hasta que Calidad evalúe.
2. El transportista deja el producto en el kit térmico cerrado.
3. Se aplica el mismo flujo de la sección Evaluación de impacto.
4. Si el producto vuelve a Farmalog Sur, ingresa como devolución, en cuarentena, y nunca reingresa a stock disponible sin decisión de la DT.

## Error frecuente que conviene evitar

El reflejo natural cuando una cámara se va de rango es **mover el producto a otra cámara para salvarlo**. Está mal y es la causa más común de que una excursión menor se transforme en un problema serio: se pierde la trazabilidad de qué producto estuvo expuesto a qué, se contamina el stock de la cámara receptora con producto de estado indefinido, y la evaluación de impacto posterior se vuelve imposible.

Primero se aísla y se registra. Recién después, y sólo con autorización de la DT o del Supervisor de Cámaras, se evalúa reubicar.
