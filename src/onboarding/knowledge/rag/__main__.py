"""Ingesta del corpus como comando:

docker compose run --rm app python -m onboarding.knowledge.rag corpus
"""

from onboarding.knowledge.rag.ingest import main

main()
