# Corpus de la empresa ficticia

15 a 25 documentos cortos en Markdown: manuales de proceso, organigrama,
políticas internas, FAQs. Es lo que un equipo de RRHH/IT tendría hoy en su wiki.

Ficticia a propósito: el repo es público y así no hay que sanitizar información
real de nadie.

## Formato

Un archivo `.md` por documento, con encabezados `##` por sección. El agente cita
**documento + sección**, así que los encabezados no son decorativos: son la
unidad de cita.

```markdown
# Compras

## Pedido de compra

Toda compra se pide por el formulario interno y la aprueba el jefe de área...

## Excepciones

Las compras de menos de 50 dólares las autoriza el propio equipo.
```

## Reglas

- Español, oraciones cortas, sin ambigüedad: si un proceso tiene dos pasos, que
  se vean los dos pasos.
- Nombres de personas ficticios y consistentes entre documentos: la red
  informal se arma con esos nombres.
- Nada de datos reales de ninguna empresa ni persona.
- Cada documento tiene que poder responder al menos una pregunta del set de
  `eval/rag_questions.yaml`. Si no responde ninguna, sobra.

Después de agregar o cambiar documentos:

```bash
docker compose run --rm app python -m onboarding.knowledge.rag corpus
```

Titular: PM, con apoyo del rol RAG.
