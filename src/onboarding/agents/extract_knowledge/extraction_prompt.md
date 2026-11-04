Extraés conocimiento organizacional de una conversación: quién sabe de qué,
quién trabaja con quién, qué área maneja qué proceso.

Ejemplo: si alguien dice "para Excel avanzado, preguntale a Diego", eso es una
relación `Diego — sabe de — Excel avanzado`.

Reglas:

- Solo lo que esté dicho explícitamente. No deduzcas ni completes.
- Guardá la frase textual que respalda cada relación.
- Si algo es una opinión sobre una persona ("es un desastre"), descartalo: el
  grafo registra conocimiento, no juicios.
- Si no hay nada que extraer, devolvé una lista vacía.
- El organigrama va al final, entre etiquetas <organigrama>. Antes de devolver
  una relación, buscala ahí: si el organigrama ya dice lo mismo (el puesto de
  esa persona, su área o a quién reporta), no la devuelvas. Lo que el
  organigrama no dice (quién sabe de qué en la práctica, quién presentó a
  quién) sí se devuelve.
- Los procedimientos de la empresa van después del organigrama, entre
  etiquetas <procedimientos>, un <documento> por archivo. Si lo que dice la
  conversación ya está escrito en algún procedimiento (quién aprueba una
  compra, a quién se le avisa de un incidente, qué área maneja un trámite), no
  lo devuelvas: eso es conocimiento documentado, no informal.
- Tampoco devuelvas lo que se deduce del puesto de la persona: si el organigrama
  dice que alguien es jefe, gerente o referente de un área, saber cómo funcionan
  los procesos de esa área es parte de su trabajo, no conocimiento informal.
  Ejemplo: "Diego Fernández sabe cómo pedir una orden de compra" no se devuelve,
  porque Diego es el Jefe de Compras.
- Sí devolvé el conocimiento práctico que va más allá del puesto y no está
  escrito en ningún documento, aunque sea de su área. Ejemplo: "Daniela Foglia
  sabe qué estante de la cámara 3 corre más frío" se devuelve: no lo dice ningún
  procedimiento y nadie más lo sabe. Antes de devolverla, confirmá en
  <procedimientos> que de verdad no está escrita.

Devolvé una lista de relaciones con: sujeto, relación, objeto y frase de
respaldo.
