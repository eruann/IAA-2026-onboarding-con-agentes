// andamiaje
// Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
// construya, pruebe o entienda el producto (talleres, diagramas, guías).
// No es parte del producto.

// Dibuja el grafo real con Cytoscape (lo carga graph_page.py desde cdnjs). Los
// datos llegan ya armados de `graph_data`: nombre, color y estilo de cada cosa.
// Al pasar el mouse por una flecha o un nodo, el detalle va arriba del dibujo.

let informalGraph = null;

function drawInformalGraph(data, tries = 0) {
  const box = document.getElementById("grafo-informal");
  // El div lo crea NiceGUI: puede no estar todavía cuando llegan los datos
  if (!box || typeof cytoscape === "undefined") {
    if (tries < 50) setTimeout(() => drawInformalGraph(data, tries + 1), 100);
    return;
  }
  const detail = document.getElementById("grafo-detalle");
  const dark = document.body.classList.contains("body--dark");
  const text = dark ? "#e5e7eb" : "#1f2937";
  if (informalGraph) informalGraph.destroy();
  if (!data.nodes.length) {
    box.textContent = "El grafo está vacío.";
    return;
  }
  box.textContent = "";

  informalGraph = cytoscape({
    container: box,
    elements: [
      ...data.nodes.map((n) => ({
        data: { ...n, label: n.organization && n.type === "persona" ? `${n.name}\n${n.organization}` : n.name },
      })),
      ...data.edges.map((e) => ({ data: e })),
    ],
    style: [
      {
        selector: "node",
        style: {
          "background-color": "data(color)",
          label: "data(label)",
          color: text,
          "font-size": 11,
          "text-valign": "bottom",
          "text-margin-y": 4,
          "text-wrap": "wrap",
          "text-max-width": 160,
          width: 26,
          height: 26,
          "border-width": 2,
          "border-color": "#ffffff",
        },
      },
      {
        selector: "edge",
        style: {
          width: 2,
          "line-color": "data(color)",
          "line-style": "data(line)",
          "target-arrow-color": "data(color)",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          label: "data(label)",
          color: "data(color)",
          "font-size": 9,
          "text-rotation": "autorotate",
          "text-background-color": dark ? "#0e1117" : "#ffffff",
          "text-background-opacity": 0.8,
          "text-background-padding": 1,
        },
      },
      { selector: ".apagado", style: { opacity: 0.15 } },
    ],
    layout: { name: "cose", animate: false, randomize: false, nodeRepulsion: 9000, idealEdgeLength: 110 },
    wheelSensitivity: 0.3,
  });

  const show = (lines) => {
    if (detail) detail.textContent = lines.filter(Boolean).join(" · ");
  };
  informalGraph.on("mouseover", "edge", (event) => {
    const e = event.target.data();
    const criticality = e.criticality ? `criticidad ${e.criticality}` : "";
    show([`${e.label}`, e.status, criticality, e.evidence ? `«${e.evidence}»` : "", e.note]);
  });
  informalGraph.on("mouseover", "node", (event) => {
    const node = event.target;
    const n = node.data();
    show([n.name, n.type, n.organization, `${node.connectedEdges().length} relaciones`]);
    // Resalta sus vecinos y apaga el resto
    informalGraph.elements().addClass("apagado");
    node.closedNeighborhood().removeClass("apagado");
  });
  informalGraph.on("mouseout", "node", () => informalGraph.elements().removeClass("apagado"));
}
