> **andamiaje**
>
> Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
> construya, pruebe o entienda el producto (talleres, diagramas, guías).
> No es parte del producto.

# Taller Grafo cultural y datos

**Tu parte:** lo no escrito, quién sabe qué más allá del organigrama.

## Qué construís y qué trae el taller

**Lo construís vos:**

- `agents/extract_knowledge/` → tu agente: `node.py` saca las relaciones con
  `extract_triples`, cada una con la frase que la respalda (**ya funciona**), con
  sus instrucciones en `extraction_prompt.md`, las guarda y devuelve la lista. A
  diferencia de los demás agentes, no conversa: la respuesta la arma el código,
  sin `ask_model`, para que el modelo no sume preguntas ni comentarios.
- `agents/extract_knowledge/identity.py` → `resolve_person`: antes de guardar,
  compara cada persona extraída con las que ya se conocen (organigrama y grafo,
  `known_people`). El **score** es la mitad del parecido literal del nombre
  (`name_similarity`, sin modelo: "Diego Fernandez Lopez Monier" y "Diego
  Fernández" dan 1) y la mitad de la similitud semántica que evalúa el modelo
  (¿la frase y el puesto encajan con lo que se sabe del candidato?), con sus
  instrucciones en `identity_prompt.md`. El modelo además da su **confianza**.
  Score ≥ 0,75, confianza ≥ 0,7 y semántica ≥ 0,6 (o confianza ≥ 0,8, aunque la
  frase no hable del puesto), sin otro candidato creíble a menos de 0,1 de score
  (dos "Juan Pérez": queda en duda), o con el mismo nombre y apellido, una sola
  persona que se llama así, ninguna otra organización en la frase y confianza
  ≥ 0,5: es la misma persona y la relación se guarda con
  el nombre que ya existe, en un solo nodo. Score ≥ 0,5 y confianza ≥ 0,3 (la
  duda; si el modelo casi lo descarta, es otra persona): se guarda con
  el nombre nuevo y una arista `may_be_same` entre las dos personas, pendiente,
  con el score como peso (`weight`) y la confianza, para que alguien la valide.
  Aunque el nombre sea idéntico lo juzga el modelo, que lee la frase ("Diego
  Fernandez del banco Macro" no es el Jefe de Compras); si no es la misma, se
  guarda aparte, con el nombre limpio y un id propio (`diego-fernandez-banco-macro`):
  la relación lleva ese id en `subject_id`, y `person_profile` y `who_knows_about`
  buscan por id para no mezclar homónimos.
  Si no
  hay nadie parecido, no se llama al modelo.
- `knowledge/informal_network/triples.py` → `KnowledgeTriple`: la forma de una
  relación, lo que el resto del sistema usa de tu parte.
- `knowledge/informal_network/store.py` → `save_triples` / `load_graph`: guardan
  el grafo en `data/informal_network.json` hasta que estén las tablas. Evitan
  duplicados, marcan pendiente lo que se niega y unen con un nodo `conflict` dos
  relaciones exclusivas que chocan. Tu agente ya guarda ahí lo que extrae.
  `save_possible_match` vincula con una arista `may_be_same` a dos personas que
  pueden ser la misma, con su peso, para que alguien lo valide. `rename_person`
  le pone a una persona un nombre más completo (el id no cambia): cuando el agente unifica a alguien
  del grafo y la mención trae más palabras ("Diego Fernandes Hamilton" contra
  "Diego Fernández"), el nodo pasa a llamarse así, también si es del organigrama
  (su puesto sale del id). Para que el nombre llegue entero, `extract_triples`
  le suma al sujeto los apellidos que siguen en la frase si el modelo los recortó,
  y le devuelve al objeto las palabras de la frase si el modelo las "corrigió"
  ("banco micro" no pasa a "banco macro"). Para descartar lo que ya está escrito,
  `extract_triples` no le manda al modelo todos los procedimientos: primero un grep
  (`_grep_procedures`) elige los que nombran alguna palabra de la conversación, más
  `bienvenida.md` (de ahí sale la criticidad); si no encuentra ninguno, van todos.
  Lo único que se deduce es la herramienta de algo que alguien hizo: "hizo la tabla
  dinámica del informe de ventas" y la conversación o un procedimiento dice que el
  informe es un Excel, entonces sabe de Excel. El modelo lo devuelve aparte
  (`inferred`) y `_inferred` lo controla igual que lo dicho: la frase textual y la
  herramienta nombrada en la conversación o en el documento que cita; si no, se
  descarta. Va como `knows_about` de criticidad baja, pendiente, con `inferred` y el
  motivo en `review_note` ("deducido: … (lo dice sigma-wms.md)"). Si después alguien
  lo dice, la relación pasa a ser dicha (`store.py`). La herramienta también
  puede salir del grafo: si la frase dice con qué se hace algo sin nombrar a nadie
  ("el tablero de Gestión es de Superset"), el modelo lo devuelve en `tool_facts`,
  `save_tool` lo anota en el nodo de esa cosa y deduce que quien ya la hace o sabe
  de ella sabe de Superset; si alguien lo dice después, se deduce al guardar. Busca
  la cosa por sus palabras, sin tildes ni plural y con una letra de diferencia
  ("tablero de gestió" es "tablero de Gestión"). Si no se sabe de qué organización es la
  persona (ni organigrama, ni frase, ni su nodo), la relación pide revisión
  (`needs_review`): queda pendiente aunque sea `low`, con su criticidad tal cual,
  en vez de confirmarse sola. Lo de apoyo de oficina (librería, útiles, almuerzo,
  eventos) es `low`. Si la persona es del organigrama y la tarea no encaja con su
  puesto oficial según los procedimientos (el Gerente de Calidad "se encarga de
  llamar a los clientes para cobrar"), `_review_if_off_role` le pide al modelo que
  lo juzgue (`role_fit_prompt.md`) y la relación queda pendiente con una nota
  (`review_note`: "no coincide con su puesto (…): la cobranza la gestiona
  Tesorería") que se ve en la respuesta y en la columna detalle de la tarjeta. No
  se descarta: puede ser justo lo que el organigrama no muestra.
- `knowledge/informal_network/queries.py` → `who_knows_about` (a quién
  preguntarle por un tema: por defecto solo los nombres, lo acordado con los demás
  roles; con `detailed=True`, la ficha con su puesto y su empresa: del organigrama
  si es de la empresa, o lo que dijo la conversación si es de afuera) y `what_is_known_about` (lo que se dijo del tema, con
  su frase: el procedimiento no escrito). Buscan por palabras en el JSON, sin
  tildes ni plural; con un modelo, además, el modelo ordena a las personas por
  quién encaja mejor con la pregunta mirando todo lo que se sabe de cada una
  (`rank_prompt.md`): para el oficial de cuentas, el del perfil comercial con el
  banco antes que el de una tarea puntual. A quien no encaja lo deja afuera,
  aunque sea una sola persona: que tenga "banco" en un tema no lo hace el
  maestranza del banco; si no encaja nadie, no deriva a nadie. Cada persona trae
  el motivo (`reason`, columna en el taller; si la función no figura tal cual en
  el grafo, lo dice: "no figura como oficial de cuentas; se acerca por…") y si sus
  relaciones están aprobadas (`status`: "confirmada", "pendiente" o "1 de 2
  confirmadas"). Sin modelo, ordenan por respaldo: primero quien tiene más relaciones
  confirmadas, después más relaciones en total. Si no encuentran nada, el
  modelo elige los temas cercanos del grafo (`related_topics`, prompt en
  `related_prompt.md`): "liquidación de IVA" lleva a "impuestos". Solo puede
  elegir temas que ya están en el grafo.
- `knowledge/informal_network/models.py`: las tablas `nodes` y `edges`. Pendiente.
- `knowledge/informal_network/store.py` → `pending_reviews` / `review`: lo pendiente
  lo revisa una persona. Una relación se aprueba (confirmada) o se rechaza
  (`REJECTED`: queda con su historial, las consultas no la ven y no se vuelve a
  proponer). Aprobar una duda de identidad (`may_be_same`) une a las dos personas
  en un nodo: el que ya existía, con el nombre más completo y sus relaciones sin
  repetir; rechazarla dice que son distintas. En una contradicción, aprobar una
  rechaza la otra y cierra el conflicto. `set_organization` guarda la organización
  de una persona que dijo quien revisa.

**Lo trae el taller** (`workshop.py`, en esta carpeta): el chat con tu agente y
las pruebas, en las tres secciones de siempre: `extract_triples` sale de tu
agente y `who_knows_about`, de la knowledge layer. Lo ad hoc (`checks.py`) es la
tarjeta para autorizar: `authorize` pone en el taller `pending_reviews`, `review` y
`set_organization`; y la página del grafo (`graph_page.py` y `graph_page.js`), que el
taller muestra embebida en "Ver el grafo".

## Qué falta

1. Tablas `nodes` y `edges` con su migración (`informal_network/models.py`).
2. Pasar el guardado y las consultas del JSON a esas tablas.
3. Que el agente de RAG use `who_knows_about()` para derivar cuando no hay
   documentación.
4. Medir la cobertura contra `eval/informal_network_ground_truth.yaml`.

## Qué probar en el taller

- **Chat**: escribile a tu agente una conversación ("Para Excel avanzado,
  preguntale a Diego Fernández") y te devuelve las relaciones que encontró, con
  su respaldo. El panel **Grafo** marca el recorrido por `extract_knowledge`.
  Elegí un modelo con salida estructurada: con el `fake` falla.
  Si preguntás (el mensaje termina en `?`: "¿Quién sabe de impuestos?", "¿Cómo
  se recupera el backup?"), no extrae: responde con el grafo quién sabe y lo que
  se dijo, con la misma consulta (palabras primero, después temas cercanos).
- **Extraer relaciones**: lo mismo, llamando a `extract_triples` directo. Podés
  comparar dos modelos lado a lado. Necesita un modelo con salida estructurada.
- **Autorizar**: sin `edge_ids`, **Probar** te lista lo que espera revisión
  (relación, ¿misma persona?, contradicción), con su frase y su `edge_id`; en
  organización dice «falta» si la persona no tiene una conocida (ni organigrama,
  ni frase, ni su nodo). Poné uno o varios ("3, 5, 7") y aprobar o rechazar: te dice
  qué hizo y te muestra lo que queda; lo que no pongas sigue pendiente. Si escribís
  la organización, se guarda en la persona de esas relaciones a la que le falte,
  aunque la relación se rechace.
- **Ver el grafo**: una página embebida con el grafo real
  (`data/informal_network.json`), dibujada con Cytoscape. Las personas, los temas,
  los procesos y las organizaciones son nodos de distinto color, y cada relación
  es una flecha con su `#id`: llena si está confirmada, rayada si está pendiente y
  naranja si es una duda de "¿misma persona?" y violeta si es deducida (con su
  motivo en el detalle). Los nodos se arrastran y se hace
  zoom con la rueda; al pasar el mouse por una flecha se ven la frase y la
  criticidad, y por un nodo, sus vecinos resaltados. Con "Mostrar las rechazadas"
  también aparecen, en gris punteado. Después de extraer o autorizar, tocá
  **Recargar**. También se abre en otra pestaña (`/ui/talleres/grafo`).
- **¿Quién sabe de?**: escribí un tema y te devuelve a quién derivaría el agente.
  Si el tema no está tal cual en el grafo, el modelo que elijas busca los
  cercanos.

## Pedidos de plan para Claude Code o Codex

Prendé el modo plan (Claude Code: `Shift+Tab` hasta *plan mode*; Codex:
`/plan`; más detalle en `DEVELOPMENT.md`, "Primero el plan") y pedí, por
ejemplo:

- `Armame un plan para crear las tablas nodes y edges (informal_network/models.py) con su migración. Explicame cada columna y para qué sirve.`
- `Armame un plan para que mi agente (agents/extract_knowledge) guarde las relaciones en nodes/edges. ¿Qué archivos toca y cómo lo pruebo?`
- `Armame un plan para implementar who_knows_about() sobre nodes/edges. ¿Cómo ordena a las personas y por qué?`
- `Armame un plan para sumar a mi taller una prueba que muestre la cobertura contra el ground truth.`

Leé el plan, preguntá lo que no entiendas y recién ahí aprobalo.
