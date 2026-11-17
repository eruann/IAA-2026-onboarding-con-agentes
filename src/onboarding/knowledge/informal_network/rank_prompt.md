Alguien pregunta a quién recurrir. Ya se encontraron, en el grafo de conocimiento
de la empresa, personas relacionadas con lo que pregunta. Ordenalas de la que
mejor encaja a la que peor: ¿quién es la indicada para lo que se pregunta?

Te paso las personas entre etiquetas `<personas>`, cada una con su id, su nombre,
su puesto y su empresa si se saben, y todo lo que se sabe de ella (de qué sabe y
de qué se encarga, con la frase que lo dijo).

Mirá el perfil completo, no solo la palabra que coincidió con la pregunta.
Ejemplo: si preguntan por el oficial de cuentas del banco, encaja más alguien del
banco que trata los costos y la relación comercial con la empresa que alguien que
se encarga de una tarea puntual, como descontar cheques.

Reglas:

- Devolvé los ids de la lista, copiados tal cual, del que mejor encaja al que peor.
- Con cada id, el motivo en una línea: por qué encaja. Si la función que se
  pregunta no figura tal cual en lo que se sabe de la persona, decilo y explicá
  por qué se acerca. Ejemplo: "No figura como oficial de cuentas; se acerca por su
  perfil comercial con el banco (costos financieros)".
- Por lo general hay una sola persona por función: si dos personas se acercan, la primera es la
  más probable y el motivo de la segunda dice por qué queda después.
- Si alguien no tiene nada que ver con la pregunta, dejalo afuera. Compartir la
  empresa o una palabra no alcanza: si preguntan por el maestranza del banco y
  nadie se encarga de eso, alguien del banco que descuenta cheques no encaja.
- Si nadie encaja, devolvé una lista vacía. Es mejor no derivar a nadie que
  derivar a la persona equivocada.
