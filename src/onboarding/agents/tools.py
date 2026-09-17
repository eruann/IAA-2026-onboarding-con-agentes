"""Herramientas que los agentes pueden llamar. Titular: rol Agentes.

Regla: una tool es una función chica con tipos claros que envuelve la interfaz
pública de otro módulo (`rag`, `knowledge`, `game`). Nada de SQL acá adentro.

TODO(agentes): definir el set inicial, por ejemplo
  - buscar_documentacion(consulta) -> fragmentos con fuente
  - quien_sabe_de(tema) -> personas sugeridas
  - misiones_pendientes(persona) -> lista de misiones
"""
