/* Dependency graph view: force-directed layout on a canvas, no external library. */

const graph = {
  data: null,
  nodes: [],
  edges: [],
  byId: new Map(),
  selected: null,
  focusMode: true,
  depth: 1,
  kinds: new Set(["inherits", "subclassed_by", "instantiated_at", "overrides",
                  "overridden_by", "dispatch_candidates"]),
  alpha: 0,
  raf: null,
  dragging: null,
  hover: null,
  transform: { x: 0, y: 0, k: 1 },
};

const KIND_COLOR = {
  class: "#b39cff",
  method: "#64d6f0",
  function: "#a5dd7a",
  external: "#54637a",
};

const EDGE_COLOR = {
  inherits: "#4cc2ff",
  subclassed_by: "#17becf",
  instantiated_at: "#35d07f",
  overrides: "#ff5c7a",
  overridden_by: "#ff9db0",
  dispatch_candidates: "#f5a524",
  attribute_access: "#7a8aa0",
  calls: "#5b6b82",
  called_by: "#3d4a5c",
};

function graphCanvas() {
  return $("graphCanvas");
}

async function loadGraph(focus) {
  const { repo, customPath, mode, limit, seed } = analysisParams();
  const params = new URLSearchParams({ repo, path: customPath, mode, limit, seed });
  if (graph.focusMode && focus) {
    params.set("focus", focus);
    params.set("depth", String(graph.depth));
  }
  params.set("kinds", [...graph.kinds].join(","));
  setStatus("加载关系图…", "warn");
  const data = await api(`/api/graph?${params}`);
  graph.data = data;
  initGraphLayout();
  setStatus(`关系图：${data.counts.nodes} 节点 / ${data.counts.edges} 边${focus ? ` · 以 ${focus.split(".").pop()} 为中心` : ""}`, "ok");
}

function initGraphLayout() {
  const data = graph.data;
  const canvas = graphCanvas();
  if (!canvas) return;
  const width = canvas.clientWidth || 600;
  const height = canvas.clientHeight || 500;

  graph.nodes = data.nodes.map((node, index) => {
    const angle = (index / Math.max(1, data.nodes.length)) * Math.PI * 2;
    const radius = Math.min(width, height) * 0.33;
    return {
      ...node,
      x: width / 2 + Math.cos(angle) * radius * (0.6 + Math.random() * 0.6),
      y: height / 2 + Math.sin(angle) * radius * (0.6 + Math.random() * 0.6),
      vx: 0,
      vy: 0,
      degree: 0,
    };
  });
  graph.byId = new Map(graph.nodes.map((node) => [node.id, node]));
  graph.edges = data.edges
    .filter((edge) => graph.byId.has(edge.source) && graph.byId.has(edge.target))
    .map((edge) => ({ ...edge }));
  for (const edge of graph.edges) {
    graph.byId.get(edge.source).degree += 1;
    graph.byId.get(edge.target).degree += 1;
  }
  graph.transform = { x: 0, y: 0, k: 1 };
  graph.alpha = 1;
  if (!graph.raf) loopGraph();
}

function stepGraph(width, height) {
  const nodes = graph.nodes;
  const alpha = graph.alpha;
  // repulsion
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i];
      const b = nodes[j];
      let dx = a.x - b.x;
      let dy = a.y - b.y;
      let dist = Math.hypot(dx, dy) || 0.01;
      if (dist < 140) {
        const force = (900 * alpha) / (dist * dist);
        dx /= dist; dy /= dist;
        a.vx += dx * force; a.vy += dy * force;
        b.vx -= dx * force; b.vy -= dy * force;
      }
    }
  }
  // springs
  for (const edge of graph.edges) {
    const a = graph.byId.get(edge.source);
    const b = graph.byId.get(edge.target);
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const dist = Math.hypot(dx, dy) || 0.01;
    const rest = 90;
    const force = (dist - rest) * 0.02 * alpha;
    const ux = dx / dist; const uy = dy / dist;
    a.vx += ux * force; a.vy += uy * force;
    b.vx -= ux * force; b.vy -= uy * force;
  }
  // centring
  for (const node of nodes) {
    node.vx += (width / 2 - node.x) * 0.002 * alpha;
    node.vy += (height / 2 - node.y) * 0.002 * alpha;
    node.vx *= 0.86; node.vy *= 0.86;
    node.x += node.vx; node.y += node.vy;
    node.x = Math.max(24, Math.min(width - 24, node.x));
    node.y = Math.max(24, Math.min(height - 24, node.y));
  }
  graph.alpha *= 0.985;
}

function drawGraph() {
  const canvas = graphCanvas();
  if (!canvas || !graph.nodes.length) return;
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (canvas.width !== width * ratio || canvas.height !== height * ratio) {
    canvas.width = width * ratio;
    canvas.height = height * ratio;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);

  ctx.save();
  ctx.translate(graph.transform.x, graph.transform.y);
  ctx.scale(graph.transform.k, graph.transform.k);

  // edges
  for (const edge of graph.edges) {
    const a = graph.byId.get(edge.source);
    const b = graph.byId.get(edge.target);
    if (!a || !b) continue;
    const emphasised = graph.selected
      && (edge.source === graph.selected || edge.target === graph.selected);
    ctx.strokeStyle = EDGE_COLOR[edge.kind] || "#444";
    ctx.globalAlpha = emphasised ? 0.95 : 0.32;
    ctx.lineWidth = emphasised ? 2.2 : 1;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    const mx = (a.x + b.x) / 2;
    const my = (a.y + b.y) / 2 - 12;
    ctx.quadraticCurveTo(mx, my, b.x, b.y);
    ctx.stroke();
    // arrow head
    const angle = Math.atan2(b.y - my, b.x - mx);
    const r = nodeRadius(b) + 2;
    ctx.globalAlpha = emphasised ? 0.95 : 0.32;
    ctx.beginPath();
    ctx.moveTo(b.x - Math.cos(angle - 0.4) * (r + 6), b.y - Math.sin(angle - 0.4) * (r + 6));
    ctx.lineTo(b.x - Math.cos(angle) * r, b.y - Math.sin(angle) * r);
    ctx.lineTo(b.x - Math.cos(angle + 0.4) * (r + 6), b.y - Math.sin(angle + 0.4) * (r + 6));
    ctx.stroke();
  }

  // nodes
  for (const node of graph.nodes) {
    const r = nodeRadius(node);
    ctx.globalAlpha = 1;
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
    ctx.fillStyle = KIND_COLOR[node.kind] || "#8899aa";
    if (node.kind === "class") {
      ctx.fill();
    } else {
      ctx.globalAlpha = 0.85;
      ctx.fill();
      ctx.globalAlpha = 1;
    }
    ctx.lineWidth = node.id === graph.selected ? 3 : 1;
    ctx.strokeStyle = node.id === graph.selected ? "#ffffff"
      : (graph.hover && graph.hover.id === node.id ? "#9fc4ec" : "rgba(0,0,0,.45)");
    ctx.stroke();

    const showLabel = graph.nodes.length <= 60
      || node.id === graph.selected
      || (graph.hover && graph.hover.id === node.id)
      || node.degree >= 6;
    if (showLabel) {
      ctx.font = `${graph.nodes.length > 120 ? 9 : 10.5}px "JetBrains Mono", Consolas, monospace`;
      ctx.fillStyle = node.id === graph.selected ? "#ffffff" : "#c3d3e8";
      ctx.textAlign = "center";
      ctx.fillText(shortName(node), node.x, node.y + r + 12);
    }
  }
  ctx.restore();

  // legend
  ctx.font = '10px "JetBrains Mono", monospace';
  ctx.textAlign = "left";
  let y = 14;
  for (const kind of graph.kinds) {
    ctx.fillStyle = EDGE_COLOR[kind] || "#666";
    ctx.fillRect(10, y - 6, 14, 3);
    ctx.fillStyle = "#8b9ab0";
    ctx.fillText(kind, 30, y);
    y += 14;
  }
}

function nodeRadius(node) {
  return 4 + Math.min(9, Math.sqrt(node.degree || 1) * 2.4);
}

function shortName(node) {
  const text = node.name || node.id;
  return text.length > 26 ? text.slice(0, 24) + "…" : text;
}

function loopGraph() {
  const canvas = graphCanvas();
  if (!canvas || !canvas.clientWidth) {
    graph.raf = requestAnimationFrame(loopGraph);
    return;
  }
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (graph.alpha > 0.005) stepGraph(width, height);
  drawGraph();
  graph.raf = requestAnimationFrame(loopGraph);
}

function graphHit(event) {
  const canvas = graphCanvas();
  const rect = canvas.getBoundingClientRect();
  const x = (event.clientX - rect.left - graph.transform.x) / graph.transform.k;
  const y = (event.clientY - rect.top - graph.transform.y) / graph.transform.k;
  let best = null;
  let bestDist = Infinity;
  for (const node of graph.nodes) {
    const dist = Math.hypot(node.x - x, node.y - y);
    if (dist < nodeRadius(node) + 6 && dist < bestDist) {
      best = node;
      bestDist = dist;
    }
  }
  return { node: best, x, y };
}

function wireGraphInteractions() {
  const canvas = graphCanvas();
  if (!canvas) return;

  canvas.addEventListener("mousemove", (event) => {
    const hit = graphHit(event);
    graph.hover = hit.node;
    canvas.style.cursor = hit.node ? "pointer" : "grab";
    if (graph.dragging) {
      graph.dragging.x = hit.x;
      graph.dragging.y = hit.y;
      graph.dragging.vx = 0;
      graph.dragging.vy = 0;
      graph.alpha = Math.max(graph.alpha, 0.25);
    }
  });

  canvas.addEventListener("mousedown", (event) => {
    const hit = graphHit(event);
    if (hit.node) graph.dragging = hit.node;
  });

  canvas.addEventListener("mouseup", () => { graph.dragging = null; });

  canvas.addEventListener("click", async (event) => {
    const hit = graphHit(event);
    if (!hit.node) return;
    graph.selected = hit.node.id;
    if (hit.node.kind !== "external" && hit.node.qname) {
      await selectEntity(hit.node.qname);
    } else if (hit.node.kind === "external") {
      setStatus(`外部依赖 ${hit.node.name} 不在本仓库内，无实体可打开`, "warn");
    }
  });

  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    const canvasRect = canvas.getBoundingClientRect();
    const mx = event.clientX - canvasRect.left;
    const my = event.clientY - canvasRect.top;
    const factor = event.deltaY < 0 ? 1.12 : 0.89;
    const k = Math.max(0.35, Math.min(3.2, graph.transform.k * factor));
    const ratio = k / graph.transform.k;
    graph.transform.x = mx - (mx - graph.transform.x) * ratio;
    graph.transform.y = my - (my - graph.transform.y) * ratio;
    graph.transform.k = k;
  }, { passive: false });

  document.querySelectorAll("#graphKinds input").forEach((box) => {
    box.addEventListener("change", () => {
      if (box.checked) graph.kinds.add(box.value);
      else graph.kinds.delete(box.value);
      loadGraph(state.selectedEntity).catch((error) => setStatus(error.message, "err"));
    });
  });

  const depthInput = $("graphDepth");
  if (depthInput) {
    depthInput.addEventListener("change", () => {
      graph.depth = parseInt(depthInput.value, 10) || 1;
      loadGraph(state.selectedEntity).catch((error) => setStatus(error.message, "err"));
    });
  }

  const focusBox = $("graphFocus");
  if (focusBox) {
    focusBox.addEventListener("change", () => {
      graph.focusMode = focusBox.checked;
      loadGraph(state.selectedEntity).catch((error) => setStatus(error.message, "err"));
    });
  }

  const resetBtn = $("graphReset");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      initGraphLayout();
      setStatus("布局已重新计算", "ok");
    });
  }
}
