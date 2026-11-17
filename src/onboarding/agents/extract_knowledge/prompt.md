Este agente no conversa: su respuesta no la redacta el modelo. Devuelve la lista
de relaciones que sacó del texto (quién sabe de qué, quién presentó a quién y
qué área maneja qué proceso). Las instrucciones que sí usa el modelo, las de
extraer, están en `extraction_prompt.md`.

Reglas:

1. Solo las relaciones que encontró, cada una con su frase de respaldo entre
   comillas, su criticidad y si quedó confirmada o pendiente en el grafo.
2. Sin preguntas ni comentarios: si no hay relaciones, lo dice y nada más.
3. Nada de opiniones sobre las personas: registra conocimiento, no juicios.
