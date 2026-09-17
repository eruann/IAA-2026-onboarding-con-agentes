"""Tablas de la red informal. Titular: rol Grafo cultural y datos.

El grafo entra en dos tablas (decisión del docx: nada de Neo4j en este alcance):

    nodes(id, type, name, attributes)
        type: person | area | topic | process
    edges(id, source_id, relation, target_id, evidence, confidence, created_at)
        relation: knows_about | introduced | belongs_to | owns_process

`evidence` guarda la frase textual que originó la relación: sin eso no se puede
auditar lo que el agente afirma, ni mostrarle al ingresante de dónde salió.

TODO(grafo): definir los modelos y su migración. Tener en cuenta que la métrica
de cobertura compara estas filas contra eval/informal_network_ground_truth.yaml.
"""
