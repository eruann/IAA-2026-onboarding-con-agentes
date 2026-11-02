# Control de Temperatura en Cámaras

## Objeto y alcance

Definir cómo se monitorea y registra la temperatura en las cámaras de almacenamiento.

**Este procedimiento cubre el monitoreo en condiciones normales.** Qué hacer cuando la temperatura efectivamente se sale de rango está en el procedimiento de Excursiones de Temperatura, y ese es el documento que hay que abrir ante una alarma.

## Equipamiento de monitoreo

Cada cámara tiene:

- **Dos sensores independientes** conectados a TermoTrack, ubicados en los puntos identificados como más caliente y más frío por el mapeo térmico vigente.
- Un **termómetro de referencia calibrado**, para verificación manual.
- Un **alarmado local** (sirena y baliza) y alarmado remoto vía TermoTrack.

Los sensores registran cada **5 minutos**. TermoTrack conserva el histórico completo por 5 años.

## Rangos y umbrales de alarma

| Cámara                       | Rango operativo | Alarma preventiva                       | Alarma crítica                      |
|------------------------------|-----------------|-----------------------------------------|-------------------------------------|
| Cámaras frías (C1 a C4)      | 2 °C a 8 °C     | fuera de 3–7 °C por más de 15 min       | fuera de 2–8 °C, inmediata          |
| Ambiente controlado (A1, A2) | 15 °C a 25 °C   | fuera de 17–23 °C por más de 60 min     | fuera de 15–25 °C por más de 30 min |
| Congelado (F1, sólo Sarandí) | −25 °C a −15 °C | fuera de −24 a −16 °C por más de 30 min | fuera de −25 a −15 °C, inmediata    |

La **alarma preventiva** es un aviso: algo se está moviendo hacia el borde. No es una excursión. La **alarma crítica** indica que el rango ya se violó y dispara el procedimiento de Excursiones de Temperatura.

## Verificación manual diaria

Además del monitoreo continuo, una vez por turno el operario asignado:

1. Lee el termómetro de referencia de cada cámara.
2. Compara contra lo que muestra TermoTrack en ese momento.
3. Registra ambos valores en la planilla diaria de Sigma WMS.

Si la diferencia entre el termómetro de referencia y TermoTrack supera **0,5 °C**, se reporta a Sistemas y a Calidad: puede indicar un sensor descalibrado. No es una excursión, es un problema de instrumento, y se trata como control de cambios sobre el equipo.

## Calibración de sensores

- Los sensores de TermoTrack se calibran **cada 12 meses** contra patrón trazable, por proveedor externo.
- Los termómetros de referencia se calibran **cada 6 meses**.
- El cronograma lo lleva la Jefatura de Control de Calidad y Validaciones en Qualis.
- Un sensor con calibración vencida invalida los registros desde la fecha de vencimiento. Por eso el vencimiento de calibración es alerta roja en el tablero de Calidad.

## Mapeo térmico

Cada cámara tiene un mapeo térmico (MTC) que identifica los puntos más caliente y más frío y demuestra que toda la cámara está en rango, no sólo donde está el sensor.

El mapeo se repite:

- Cada **3 años** como rutina.
- Después de cualquier modificación del equipo de frío, del layout de estanterías o de la capacidad instalada.
- Después de una excursión cuya causa raíz haya sido atribuida al equipo.

## Apertura de puertas

Las cámaras frías registran apertura de puerta en TermoTrack. La apertura continua no debería superar los **10 minutos**. No es una excursión por sí misma, pero aperturas prolongadas recurrentes se revisan en la reunión mensual de Calidad porque son la causa raíz más frecuente de alarmas preventivas.

## Quién mira esto todos los días

La responsabilidad operativa del monitoreo es de la Supervisora de Cámaras Frías. Quién ocupa ese puesto figura en el Organigrama. La revisión documental semanal de los registros es de Aseguramiento de Calidad. Las alarmas se publican automáticamente en \#alertas-termotrack.
