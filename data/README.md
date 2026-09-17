# Datos de la empresa ficticia

Lo que carga el seed. Son datos, no documentación: la documentación va en
`corpus/`.

```bash
docker compose run --rm app python -m onboarding.seed
```

| Archivo | Qué tiene |
|---|---|
| `people.yaml` | personas: nombre, área, rol, si es ingresante |
| `quests.yaml` | las 6-8 misiones: título, puntos, evidencia, quién aprueba |
| `rewards.yaml` | catálogo ficticio de canje |

El seed es idempotente: se puede correr todas las veces que haga falta. Por eso
la base local es descartable — si algo se ensucia, `docker compose down -v` y de
nuevo.

Titular: PM (contenido) y rol Experiencia (carga).
