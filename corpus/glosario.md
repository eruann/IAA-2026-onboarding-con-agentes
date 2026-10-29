# Glosario y Siglas

## Siglas de calidad y regulatorio

| Sigla | Significado                                                            | Qué es en la práctica                                                                                                |
|-------|------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| POE   | Procedimiento Operativo Estándar                                       | El documento que dice cómo se hace una tarea. Si hacés algo distinto a lo que dice el POE vigente, eso es un desvío. |
| ANMAT | Administración Nacional de Medicamentos, Alimentos y Tecnología Médica | El regulador. Nos habilita y nos puede suspender.                                                                    |
| DT    | Dirección Técnica                                                      | La farmacéutica responsable ante ANMAT. Quién ocupa el puesto y quién es su suplente figura en el Organigrama.        |
| BPD   | Buenas Prácticas de Distribución                                       | El marco de referencia sobre el que están escritos nuestros POEs.                                                    |
| CAPA  | Acción Correctiva y Acción Preventiva                                  | El plan que se arma después de un desvío para que no vuelva a pasar.                                                 |
| NC    | No Conformidad                                                         | Un incumplimiento detectado, normalmente en una auditoría.                                                           |
| CC    | Control de Cambios                                                     | El procedimiento para modificar algo validado (un equipo, un POE, un sistema).                                       |
| MTC   | Mapeo Térmico de Cámara                                                | El estudio que demuestra que toda la cámara, no sólo el sensor, está en rango.                                       |

## Siglas de operaciones

| Sigla                     | Significado                                                      | Qué es en la práctica                                              |
|---------------------------|------------------------------------------------------------------|--------------------------------------------------------------------|
| SGA / WMS                 | Sistema de Gestión de Almacenes                                  | Acá se llama **Sigma WMS**. Todo movimiento de stock pasa por ahí. |
| Kit térmico               | Caja isotérmica + refrigerantes acondicionados + registrador     | Lo que mantiene el rango durante el transporte.                    |
| Registrador (data logger) | Dispositivo que graba temperatura en el tiempo                   | Va dentro del kit. Sin su descarga, el envío no se puede liberar.  |
| Excursión                 | Salida del rango de temperatura permitido                        | El evento que más nos importa evitar. Ver Excursiones de Temperatura. |
| Cuarentena                | Estado de stock bloqueado a la espera de una decisión de Calidad | En Sigma WMS se ve como estado CUAR.                               |
| Cross-dock                | Recepción y reexpedición sin almacenamiento prolongado           | Lo que hacen los sitios de Córdoba y Mendoza.                      |
| Picking                   | Armado del pedido levantando unidades del stock                  | —                                                                  |
| Logística inversa         | Devoluciones, retiros y destrucción                              | —                                                                  |

## Rangos de temperatura, dicho de una vez

| Nombre interno       | Rango                            | Uso típico                                         |
|----------------------|----------------------------------|----------------------------------------------------|
| Refrigerado / "frío" | 2 °C a 8 °C                      | Vacunas, insulinas, biológicos                     |
| Ambiente controlado  | 15 °C a 25 °C                    | Genéricos, comprimidos, la mayoría del volumen     |
| Congelado            | −25 °C a −15 °C (nominal −20 °C) | Sólo algunos productos de Verenta, sólo en Sarandí |

Cuando alguien dice "frío" sin aclarar, se refiere a 2–8 °C. "Congelado" siempre se dice explícito porque es la excepción.

## Sistemas internos

| Sistema    | Para qué sirve                                                              |
|------------|-----------------------------------------------------------------------------|
| Sigma WMS  | Stock, lotes, remitos, picking, estados de cuarentena                       |
| TermoTrack | Monitoreo continuo de temperatura de cámaras y descarga de registradores    |
| Qualis     | Desvíos, CAPA, control de cambios, registros de capacitación y calificación |
| Slack      | Comunicación diaria y alarmas automáticas de TermoTrack                     |

## Jerga que no vas a encontrar en ningún manual

- **"Tirar un Qualis"**: abrir un desvío en el sistema Qualis.
- **"Está en cuarenta"**: está en cuarentena (estado CUAR).
- **"El mono"**: el registrador de temperatura que viaja dentro del kit térmico.
- **"Pisar el lote"**: cargar mal un lote en Sigma WMS sobrescribiendo uno existente. Es un error grave y genera desvío automático.
- **"Camión parado"**: un despacho frenado por Calidad. Se dice con resignación.
