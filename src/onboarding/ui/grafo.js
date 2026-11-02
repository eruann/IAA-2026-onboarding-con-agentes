// andamiaje
// Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
// construya, pruebe o entienda el producto (talleres, diagramas, guías).
// No es parte del producto.

// Dibujo del grafo de agentes como diagrama de flujo, con trazo de Excalidraw.
//
// Lee el lineage (agents/grafo.json, generado desde el código) y lo dibuja: ELK
// calcula dónde va cada cosa y por dónde pasan las líneas, y rough.js (el motor
// de Excalidraw) lo dibuja con trazo a mano. Nada está armado para un grafo en
// particular: son reglas de diagrama de flujo que se aplican a lo que diga el JSON.
//
// - Si de un nodo salen varias flechas condicionales, va un rombo de decisión.
// - Si varias flechas llegan al mismo destino, se juntan en un tronco.
// - Lo que cada nodo usa de la knowledge layer se une con una línea punteada.
//
// Cada caja y cada línea lleva su data-id: el recorrido de un mensaje se marca
// cambiando clases, sin redibujar. Las librerías se cargan de jsDelivr.

const ELK_URL = "https://cdn.jsdelivr.net/npm/elkjs@0.9.3/lib/elk.bundled.js/+esm";
const ROUGH_URL = "https://cdn.jsdelivr.net/npm/roughjs@4/+esm";

const NS = "http://www.w3.org/2000/svg";
const FUENTE = "Kalam, 'Comic Sans MS', cursive";
// preserveVertices: los extremos quedan exactos, así los tramos que se juntan
// (el tronco hacia Fin) empalman sin quiebre.
const TRAZO = { roughness: 0.6, bowing: 0.8, disableMultiStroke: true, preserveVertices: true, seed: 7 };
const CAJA = { roughness: 1.1, bowing: 1, fillStyle: "hachure", hachureGap: 7, seed: 11 };
const COLOR = { linea: "#475569", texto: "#1f2937", suave: "#64748b", usa: "#60a5fa", modelo: "#6d28d9" };
// Funciones de la knowledge layer: relleno, borde y nota al lado del nombre
const ESTADOS = {
  usada: ["#dbeafe", "#1d4ed8", ""],
  pendiente: ["#fee2e2", "#b91c1c", "TODO"],
  nadie: ["#ffedd5", "#c2410c", "nadie la usa"],
  fuera: ["#f1f5f9", "#94a3b8", null], // la nota dice quién la usa
};
const ORDEN = ["usada", "pendiente", "nadie", "fuera"];

let librerias;
const dibujos = new Map(); // id del contenedor → { svg, flujo, vuelta }

function cargar() {
  librerias ??= Promise.all([import(ELK_URL), import(ROUGH_URL)]).then(([elk, rough]) => ({
    ELK: elk.default,
    rough: rough.default,
  }));
  return librerias;
}

const medir = (() => {
  const ctx = document.createElement("canvas").getContext("2d");
  return (texto, px) => {
    ctx.font = `${px}px ${FUENTE}`;
    return ctx.measureText(texto).width;
  };
})();

// --- Del lineage a un diagrama de flujo -----------------------------------------

function estadoDe(k) {
  if (k.usada_por_el_grafo) return "usada";
  if (k.pendiente) return "pendiente";
  return k.usada_fuera_del_grafo.length ? "fuera" : "nadie";
}

function notaDe(k) {
  const estado = estadoDe(k);
  if (estado !== "fuera") return ESTADOS[estado][2];
  return `la usa ${k.usada_fuera_del_grafo.map((archivo) => archivo.split("/").at(-1)).join(", ")}`;
}

function chipsDe(nodo, capa) {
  const chips = nodo.usa.map((u) => ({
    texto: `${u.funcion}()`,
    color: capa[u.funcion]?.pendiente ? ESTADOS.pendiente[1] : ESTADOS.usada[1],
  }));
  // El modelo, directo o a través de una función de la capa
  const via = nodo.usa.find((u) => capa[u.funcion]?.modelo);
  if (nodo.modelo) chips.push({ texto: "⚙ modelo", color: COLOR.modelo });
  else if (via) chips.push({ texto: `⚙ modelo vía ${via.funcion}`, color: COLOR.modelo });
  return chips;
}

function armarFlujo(lineage) {
  const capa = Object.fromEntries(lineage.knowledge_layer.map((k) => [k.funcion, k]));
  const nodos = [
    { id: "__start__", tipo: "extremo", texto: "Inicio" },
    { id: "__end__", tipo: "extremo", texto: "Fin" },
    ...lineage.nodos.map((n) => ({ id: n.id, tipo: "nodo", texto: n.titulo, detalle: n.id, chips: chipsDe(n, capa) })),
  ];
  // `tramos`: qué flechas del grafo real representa cada línea dibujada (para
  // seguir el recorrido de un mensaje a través de rombos y troncos)
  const flechas = [];
  const salen = {};
  const llegan = {};
  for (const f of lineage.flechas) {
    (salen[f.desde] ??= []).push(f);
    (llegan[f.hasta] ??= []).push(f);
  }
  const clave = (f) => `${f.desde}>${f.hasta}`;

  // Rombo: varias flechas condicionales desde un mismo nodo
  const origen = {};
  for (const [desde, lista] of Object.entries(salen)) {
    if (lista.length < 2 || !lista.every((f) => f.condicional)) continue;
    const rombo = `decide_${desde}`;
    nodos.push({ id: rombo, tipo: "decision", texto: "¿qué tarea?" });
    flechas.push({ id: `${desde}>${rombo}`, desde, hasta: rombo, tramos: [[desde, null]] });
    for (const f of lista) origen[clave(f)] = rombo;
  }
  // Tronco: varias flechas hacia un mismo destino se juntan en un punto
  for (const [hasta, lista] of Object.entries(llegan)) {
    if (lista.length < 2) continue;
    const punto = `union_${hasta}`;
    nodos.push({ id: punto, tipo: "union" });
    flechas.push({ id: `${punto}>${hasta}`, desde: punto, hasta, tramos: lista.map((f) => [f.desde, hasta]) });
    for (const f of lista) {
      const desde = origen[clave(f)] ?? f.desde;
      flechas.push({ id: `${f.desde}>${punto}`, desde, hasta: punto, tramos: [[f.desde, hasta]], sinPunta: true });
    }
  }
  for (const f of lineage.flechas) {
    if (llegan[f.hasta].length > 1) continue;
    const desde = origen[clave(f)] ?? f.desde;
    flechas.push({ id: `${desde}>${f.hasta}`, desde, hasta: f.hasta, tramos: [[f.desde, f.hasta]], condicional: f.condicional && desde === f.desde });
  }

  // Knowledge layer: lo que usa el grafo arriba, después lo pendiente y lo demás
  const funciones = [...lineage.knowledge_layer].sort((a, b) => ORDEN.indexOf(estadoDe(a)) - ORDEN.indexOf(estadoDe(b)));
  for (const k of funciones) {
    nodos.push({ id: `k_${k.funcion}`, tipo: "conocimiento", texto: `${k.funcion}()`, estado: estadoDe(k), nota: notaDe(k), padre: "capa" });
  }
  for (const n of lineage.nodos) {
    for (const u of n.usa) flechas.push({ id: `${n.id}>k_${u.funcion}`, desde: n.id, hasta: `k_${u.funcion}`, tramos: [], usa: true });
  }
  return { nodos, flechas };
}

// --- Ubicación con ELK ----------------------------------------------------------

function tamaño(n) {
  if (n.tipo === "extremo") return [70, 44];
  if (n.tipo === "decision") return [64, 64];
  if (n.tipo === "union") return [2, 2];
  if (n.tipo === "conocimiento") return [medir(`${n.texto}  · ${n.nota}`, 13) + 30, 32];
  const chips = n.chips.map((c) => c.texto).join("  ·  ");
  const ancho = Math.max(medir(n.texto, 17), medir(n.detalle, 12), medir(chips, 12)) + 36;
  return [Math.max(170, ancho), chips ? 84 : 64];
}

const CON_PUERTOS = new Set(["union", "decision"]);

function ubicar(ELK, flujo) {
  const conPuertos = new Set(flujo.nodos.filter((n) => CON_PUERTOS.has(n.tipo)).map((n) => n.id));
  const caja = (n) => {
    const [width, height] = tamaño(n);
    const nodo = { id: n.id, width, height };
    // Una sola entrada y una sola salida: las líneas se juntan en un tronco en
    // vez de llegar separadas
    if (conPuertos.has(n.id)) {
      nodo.layoutOptions = { "elk.portConstraints": "FIXED_POS" };
      nodo.ports = [
        { id: `${n.id}:in`, x: 0, y: height / 2, width: 0, height: 0, layoutOptions: { "elk.port.side": "WEST" } },
        { id: `${n.id}:out`, x: width, y: height / 2, width: 0, height: 0, layoutOptions: { "elk.port.side": "EAST" } },
      ];
    }
    return nodo;
  };
  return new ELK().layout({
    id: "raiz",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.edgeRouting": "ORTHOGONAL",
      "elk.hierarchyHandling": "INCLUDE_CHILDREN",
      "elk.spacing.nodeNode": "28",
      "elk.layered.spacing.nodeNodeBetweenLayers": "56",
      "elk.layered.spacing.edgeNodeBetweenLayers": "24",
      "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
    },
    children: [
      ...flujo.nodos.filter((n) => !n.padre).map(caja),
      {
        id: "capa",
        layoutOptions: {
          "elk.padding": "[top=44,left=16,bottom=16,right=16]",
          "elk.direction": "DOWN",
          "elk.spacing.nodeNode": "12",
          // Respeta el orden de armarFlujo
          "elk.layered.crossingMinimization.forceNodeModelOrder": "true",
        },
        children: flujo.nodos.filter((n) => n.padre === "capa").map(caja),
      },
    ],
    edges: flujo.flechas.map((f) => ({
      id: f.id,
      sources: [conPuertos.has(f.desde) ? `${f.desde}:out` : f.desde],
      targets: [conPuertos.has(f.hasta) ? `${f.hasta}:in` : f.hasta],
    })),
  });
}

// --- Dibujo con rough.js --------------------------------------------------------

function texto(padre, x, y, contenido, px, color, peso = 400) {
  const t = document.createElementNS(NS, "text");
  const atributos = {
    x, y, "text-anchor": "middle", "dominant-baseline": "middle",
    "font-family": FUENTE, "font-size": px, "font-weight": peso, fill: color,
  };
  for (const [k, v] of Object.entries(atributos)) t.setAttribute(k, v);
  t.textContent = contenido;
  padre.appendChild(t);
  return t;
}

function tramoDeTexto(t, contenido, color) {
  const span = document.createElementNS(NS, "tspan");
  span.textContent = contenido;
  span.setAttribute("fill", color);
  t.appendChild(span);
}

function grupo(padre, id) {
  const g = document.createElementNS(NS, "g");
  g.dataset.id = id;
  padre.appendChild(g);
  return g;
}

function dibujarNodo(rc, svg, n, { x, y, width: w, height: h }) {
  const g = grupo(svg, n.id);
  const cx = x + w / 2;
  if (n.tipo === "extremo") {
    g.appendChild(rc.ellipse(cx, y + h / 2, w, h, { ...CAJA, fill: "#ffffff", stroke: COLOR.linea }));
    texto(g, cx, y + h / 2, n.texto, 17, COLOR.texto);
  } else if (n.tipo === "decision") {
    g.appendChild(rc.polygon([[cx, y], [x + w, y + h / 2], [cx, y + h], [x, y + h / 2]], { ...CAJA, fill: "#e0f2fe", stroke: "#0369a1" }));
    texto(g, cx, y + h + 14, n.texto, 13, COLOR.suave);
  } else if (n.tipo === "union") {
    // Sin dibujo propio: solo une el tronco con la flecha que sigue (si no,
    // queda un hueco del ancho del punto)
    g.appendChild(rc.line(x - 1, y + h / 2, x + w + 1, y + h / 2, { ...TRAZO, stroke: COLOR.linea, strokeWidth: 1.6 }));
  } else if (n.tipo === "conocimiento") {
    const [relleno, borde] = ESTADOS[n.estado];
    g.appendChild(rc.rectangle(x, y, w, h, { ...CAJA, fill: relleno, stroke: borde, hachureGap: 5 }));
    const t = texto(g, cx, y + h / 2, n.texto, 13, n.estado === "fuera" ? COLOR.suave : COLOR.texto);
    if (n.nota) tramoDeTexto(t, `  · ${n.nota}`, n.estado === "fuera" ? COLOR.suave : borde);
  } else {
    g.appendChild(rc.rectangle(x, y, w, h, { ...CAJA, fill: "#fef3c7", stroke: "#b45309" }));
    texto(g, cx, y + 22, n.texto, 17, COLOR.texto, 600);
    texto(g, cx, y + 42, n.detalle, 12, COLOR.suave);
    if (n.chips.length) {
      const t = texto(g, cx, y + 64, "", 12, COLOR.texto);
      n.chips.forEach((c, i) => tramoDeTexto(t, (i ? "  ·  " : "") + c.texto, c.color));
    }
  }
}

// Puntos de una línea. ELK a veces mete un codo de 1 o 2 px para compensar una
// diferencia mínima de altura: la línea sigue derecha con la altura (o el x) que
// traía, así no aparece un escalón.
function puntosDe(seccion) {
  const puntos = [seccion.startPoint, ...(seccion.bendPoints ?? []), seccion.endPoint].map((p) => [p.x, p.y]);
  for (let i = 1; i < puntos.length; i++) {
    for (const eje of [0, 1]) {
      if (Math.abs(puntos[i][eje] - puntos[i - 1][eje]) < 6) puntos[i][eje] = puntos[i - 1][eje];
    }
  }
  // Sin puntos repetidos: rough.js dibuja raro los tramos de largo cero
  return puntos.filter((p, i) => i === 0 || p[0] !== puntos[i - 1][0] || p[1] !== puntos[i - 1][1]);
}

function dibujarFlecha(rc, svg, f, edge) {
  const g = grupo(svg, f.id);
  g.classList.add("flecha");
  const color = f.usa ? COLOR.usa : COLOR.linea;
  const opciones = { ...TRAZO, stroke: color, strokeWidth: f.usa ? 1.2 : 1.6 };
  if (f.usa) opciones.strokeLineDash = [4, 5];
  else if (f.condicional) opciones.strokeLineDash = [7, 7];
  for (const seccion of edge?.sections ?? []) {
    const puntos = puntosDe(seccion);
    g.appendChild(rc.linearPath(puntos, opciones));
    // Punta en "V" en el flujo. Las líneas "usa" van sin punta: el nodo llama a
    // la función y recibe la respuesta, va y vuelve.
    if (f.sinPunta || f.usa || puntos.length < 2) continue;
    const [x, y] = puntos.at(-1);
    const [px, py] = puntos.at(-2);
    const angulo = Math.atan2(y - py, x - px);
    for (const giro of [0.5, -0.5]) {
      g.appendChild(rc.line(x, y, x - 10 * Math.cos(angulo + giro), y - 10 * Math.sin(angulo + giro), { ...TRAZO, stroke: color, strokeWidth: 1.6 }));
    }
  }
}

// --- Zoom: rueda hacia el mouse, arrastrar para moverse, doble clic para ver todo

function habilitarZoom(svg) {
  const inicial = svg.viewBox.baseVal;
  const original = [inicial.x, inicial.y, inicial.width, inicial.height];
  let caja = [...original];
  const aplicar = () => svg.setAttribute("viewBox", caja.join(" "));
  svg.addEventListener("wheel", (evento) => {
    evento.preventDefault();
    const r = svg.getBoundingClientRect();
    const mx = caja[0] + ((evento.clientX - r.left) / r.width) * caja[2];
    const my = caja[1] + ((evento.clientY - r.top) / r.height) * caja[3];
    const factor = evento.deltaY > 0 ? 1.15 : 1 / 1.15;
    caja = [mx - (mx - caja[0]) * factor, my - (my - caja[1]) * factor, caja[2] * factor, caja[3] * factor];
    aplicar();
  });
  let arrastre = null;
  svg.addEventListener("pointerdown", (evento) => {
    arrastre = { x: evento.clientX, y: evento.clientY, caja: [...caja] };
    svg.setPointerCapture(evento.pointerId);
    svg.style.cursor = "grabbing";
  });
  svg.addEventListener("pointermove", (evento) => {
    if (!arrastre) return;
    const r = svg.getBoundingClientRect();
    caja[0] = arrastre.caja[0] - ((evento.clientX - arrastre.x) / r.width) * caja[2];
    caja[1] = arrastre.caja[1] - ((evento.clientY - arrastre.y) / r.height) * caja[3];
    aplicar();
  });
  svg.addEventListener("pointerup", () => {
    arrastre = null;
    svg.style.cursor = "grab";
  });
  svg.addEventListener("dblclick", () => {
    caja = [...original];
    aplicar();
  });
  svg.style.cursor = "grab";
  svg.style.touchAction = "none";
}

// --- Recorrido de un mensaje ----------------------------------------------------

// Los data-id por los que pasó el mensaje, en orden: nodos y líneas, pasando por
// el rombo y el tronco cuando los hay.
function pasosDelRecorrido(flujo, visitados) {
  const camino = ["__start__", ...visitados, "__end__"];
  const pasos = [];
  for (let i = 0; i < camino.length - 1; i++) {
    const [a, b] = [camino[i], camino[i + 1]];
    const tramo = flujo.flechas.filter((f) => f.tramos.some(([x, y]) => x === a && (y === b || y === null)));
    pasos.push(a);
    let actual = a;
    while (actual !== b) {
      const f = tramo.find((f) => f.desde === actual);
      if (!f) break;
      pasos.push(f.id);
      actual = f.hasta;
      if (actual !== b) pasos.push(actual);
    }
  }
  pasos.push(camino.at(-1));
  return pasos;
}

// Pinta el recorrido paso a paso, sin redibujar. Si llega otro mensaje mientras
// se anima, el anterior se corta.
window.marcarRecorrido = async (destino, visitados) => {
  const dibujo = dibujos.get(destino);
  if (!dibujo) return;
  const vuelta = ++dibujo.vuelta;
  for (const el of dibujo.svg.querySelectorAll(".resaltado")) el.classList.remove("resaltado");
  if (!visitados.length) return;
  for (const id of pasosDelRecorrido(dibujo.flujo, visitados)) {
    if (vuelta !== dibujo.vuelta) return;
    dibujo.svg.querySelector(`[data-id="${CSS.escape(id)}"]`)?.classList.add("resaltado");
    await new Promise((listo) => setTimeout(listo, 220));
  }
};

// El contenedor puede tardar en aparecer (p. ej. recién abierto el diálogo)
async function esperar(id) {
  for (let intento = 0; intento < 50; intento++) {
    const elemento = document.getElementById(id);
    if (elemento) return elemento;
    await new Promise((listo) => setTimeout(listo, 20));
  }
  return null;
}

window.dibujarGrafo = async (destino, lineage, visitados = []) => {
  const [{ ELK, rough }, contenedor] = await Promise.all([cargar(), esperar(destino)]);
  if (!contenedor) return;
  await document.fonts.load(`17px ${FUENTE}`);
  const flujo = armarFlujo(lineage);
  const ubicado = await ubicar(ELK, flujo);
  const svg = document.createElementNS(NS, "svg");
  const rc = rough.svg(svg);

  // Posiciones absolutas (las de adentro de la capa vienen relativas a ella)
  const caja = {};
  for (const c of ubicado.children) {
    caja[c.id] = c;
    for (const h of c.children ?? []) caja[h.id] = { ...h, x: h.x + c.x, y: h.y + c.y };
  }
  const capa = grupo(svg, "capa");
  capa.appendChild(rc.rectangle(caja.capa.x, caja.capa.y, caja.capa.width, caja.capa.height, { ...TRAZO, stroke: "#94a3b8", strokeLineDash: [6, 6] }));
  texto(capa, caja.capa.x + caja.capa.width / 2, caja.capa.y + 22, "Knowledge layer", 15, COLOR.texto, 600);

  const lineas = Object.fromEntries(ubicado.edges.map((e) => [e.id, e]));
  for (const f of flujo.flechas) dibujarFlecha(rc, svg, f, lineas[f.id]);
  for (const n of flujo.nodos) dibujarNodo(rc, svg, n, caja[n.id]);

  svg.setAttribute("viewBox", `-10 -10 ${ubicado.width + 20} ${ubicado.height + 30}`);
  svg.style.width = "100%";
  svg.style.height = contenedor.dataset.alto || "auto";
  contenedor.replaceChildren(svg);
  habilitarZoom(svg);
  dibujos.set(destino, { svg, flujo, vuelta: 0 });
  if (visitados.length) await window.marcarRecorrido(destino, visitados);
};
