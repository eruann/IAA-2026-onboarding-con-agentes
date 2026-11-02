# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Ingesta del corpus como comando:

docker compose run --rm app python -m onboarding.knowledge.rag corpus
"""

from onboarding.knowledge.rag.ingest import main

main()
