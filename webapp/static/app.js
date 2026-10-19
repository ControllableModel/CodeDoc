/* CodeDoc console front-end: no framework, no build step. */

const state = {
  config: {},
  repositories: [],
  criteriaSets: [],
  templates: [],
  analysis: null,
  selectedFile: null,
  selectedEntity: null,
  entityDetail: null,
  sourceView: "source",
  outTab: "prompt",
  document: "",
  usage: { tokens: 0, cost: 0, calls: 0 },
};

const $ = (id) => document.getElementById(id);

function money(amount, currency) {
  const symbol = (currency || "USD") === "USD" ? "$" : "¥";
  const value = Number(amount || 0);
  return `${symbol}${value < 0.01 ? value.toFixed(4) : value.toFixed(3)}`;
}

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

function setStatus(text, kind) {
  const node = $("status");
  node.textContent = text;
  node.className = kind || "";
}

async function api(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.error) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

/* ------------------------------------------------------------------ config */
async function bootstrap() {
  const data = await api("/api/bootstrap");
  state.config = data.config;
  state.repositories = data.repositories;
  state.criteriaSets = data.criteria_sets;
  state.templates = data.templates;

  const repoSelect = $("repo");
  repoSelect.innerHTML = "";
  repoSelect.appendChild(el("option", "", "（选择仓库）")).value = "";
  for (const repo of state.repositories) {
    const option = el("option", "", `${repo.name}  ·  ${repo.py_files} py`);
    option.value = repo.name;
    repoSelect.appendChild(option);
  }

  // restore a sensible default: the small repo, so the first click is fast
  const preferred = state.repositories.find((r) => r.name === "ragflow")
    || state.repositories.find((r) => r.name === "flask-main")
    || state.repositories[0];
  if (preferred) repoSelect.value = preferred.name;

  fillConfigForm(data.config);
  renderCriteriaDetail();
  $("endpoint").textContent = `${data.config.model || "?"} @ ${data.config.base_url || "?"}`;
}

function fillConfigForm(config) {
  $("cfgKey").value = "";
  $("cfgKey").placeholder = config.api_key_present
    ? `已配置 ${config.api_key_hint}（留空则不修改）`
    : "sk-...";
  $("keyHint").textContent = config.api_key_present ? "已保存" : "未配置";
  $("cfgBase").value = config.base_url || "";
  $("cfgModel").value = config.model || "";
  $("cfgTemp").value = config.temperature ?? 1;
  $("cfgMaxTokens").value = config.max_tokens ?? 16000;
  $("cfgSourceBudget").value = config.source_budget ?? 8000;
  $("cfgRelevant").checked = !!config.relevant;

  const pricing = config.pricing || {};
  const modeSelect = $("cfgPriceMode");
  if (modeSelect) {
    modeSelect.value = pricing.mode || "standard";
    renderPriceTable(pricing, modeSelect.value);
    modeSelect.onchange = () => renderPriceTable(pricing, modeSelect.value);
  }

  const templateSelect = $("cfgTemplate");
  templateSelect.innerHTML = "";
  for (const template of state.templates) {
    const option = el("option", "", template.name);
    option.value = template.name;
    templateSelect.appendChild(option);
  }
  const noneOption = el("option", "", "none（IDE 基线：无准则模板）");
  noneOption.value = "none";
  templateSelect.appendChild(noneOption);
  templateSelect.value = config.template || "iso_26514.txt";

  const list = $("criteriaList");
  list.innerHTML = "";
  for (const set of state.criteriaSets) {
    const label = el("label");
    const box = document.createElement("input");
    box.type = "checkbox";
    box.value = set.id;
    box.checked = (config.criteria || []).includes(set.id);
    box.addEventListener("change", renderCriteriaDetail);
    label.appendChild(box);
    label.appendChild(document.createTextNode(set.id));
    list.appendChild(label);
  }
}

async function renderCriteriaDetail() {
  const chosen = [...document.querySelectorAll("#criteriaList input:checked")].map((b) => b.value);
  const host = $("criteriaDetail");
  host.innerHTML = "";
  if (!chosen.length) {
    host.appendChild(el("p", "hint", "未选择准则集。生成仍可运行，但判官将无维度可打分。"));
    return;
  }
  for (const setId of chosen) {
    const data = await api(`/api/criteria?id=${encodeURIComponent(setId)}`);
    host.appendChild(el("div", "crit", `${setId} · ${data.criteria.length} 条 · axis=${data.axis_role}`));
    for (const criterion of data.criteria) {
      const row = el("div", "crit");
      row.appendChild(el("b", "", criterion.name));
      row.appendChild(document.createTextNode(` — ${criterion.category} · ${criterion.level}`));
      if (criterion.applies_to.length < 3) {
        row.appendChild(document.createTextNode(" "));
        const na = el("span", "na", `不适用: ${["class", "method", "function"].filter((k) => !criterion.applies_to.includes(k)).join(",")}`);
        row.appendChild(na);
      }
      host.appendChild(row);
    }
  }
}

function renderPriceTable(pricing, mode) {
  const host = $("priceTable");
  if (!host) return;
  const tiers = pricing.tiers || {};
  const rows = [
    ["短上下文 输入", (tiers.short?.[mode]?.input ?? "—")],
    ["短上下文 输出", (tiers.short?.[mode]?.output ?? "—")],
    ["短上下文 缓存输入", (tiers.short?.[mode]?.cached_input ?? "—")],
    ["长上下文 输入", (tiers.long?.[mode]?.input ?? "—")],
    ["长上下文 输出", (tiers.long?.[mode]?.output ?? "—")],
    ["长上下文 缓存输入", (tiers.long?.[mode]?.cached_input ?? "—")],
  ];
  const unit = pricing.currency === "USD" ? "USD" : (pricing.currency || "");
  host.innerHTML = rows
    .map(([label, value]) => `<div class="crit"><b>${label}</b> — ${value} per 1M tokens (${unit})</div>`)
    .join("") + `<div class="crit">长上下文阈值：${(pricing.long_context_threshold || 272000).toLocaleString()} tokens</div>`;
}

async function saveConfig() {
  const payload = {
    base_url: $("cfgBase").value.trim(),
    model: $("cfgModel").value.trim(),
    temperature: parseFloat($("cfgTemp").value),
    max_tokens: parseInt($("cfgMaxTokens").value, 10),
    source_budget: parseInt($("cfgSourceBudget").value, 10),
    template: $("cfgTemplate").value,
    relevant: $("cfgRelevant").checked,
    criteria: [...document.querySelectorAll("#criteriaList input:checked")].map((b) => b.value),
  };
  if ($("cfgPriceMode")) {
    payload.pricing = { ...(state.config.pricing || {}), mode: $("cfgPriceMode").value };
  }
  const key = $("cfgKey").value.trim();
  if (key) payload.api_key = key;

  const data = await api("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  state.config = data.config;
  fillConfigForm(data.config);
  $("endpoint").textContent = `${data.config.model} @ ${data.config.base_url}`;
  $("drawer").classList.add("hidden");
  setStatus("配置已保存", "ok");
}

/* ---------------------------------------------------------------- analysis */
function analysisParams() {
  const repo = $("repo").value;
  const customPath = $("customPath").value.trim();
  const mode = $("mode").value;
  const limit = mode === "sample" ? parseInt($("limit").value, 10) || 60 : 0;
  const seed = parseInt($("seed").value, 10) || 42;
  return { repo, customPath, mode, limit, seed };
}

async function runAnalysis() {
  const { repo, customPath, mode, limit, seed } = analysisParams();
  if (!repo && !customPath) {
    setStatus("请选择仓库或填写路径", "warn");
    return;
  }
  $("analyzeBtn").disabled = true;
  setStatus("正在构建依赖索引…", "warn");
  const params = new URLSearchParams({ repo, path: customPath, mode, limit, seed });

  try {
    const { job } = await api(`/api/analyze?${params}`);
    let result = null;
    for (;;) {
      await new Promise((resolve) => setTimeout(resolve, 400));
      const status = await api(`/api/job?id=${job}`);
      if (status.status === "done") { result = status.result; break; }
      if (status.status === "error") throw new Error(status.error);
    }
    state.analysis = result;
    state.selectedFile = null;
    state.selectedEntity = null;
    state.entityDetail = null;
    state.document = "";
    renderFiles();
    renderEntityStrip();
    $("sourceBody").innerHTML = '<span class="hint">← 选择左侧文件，再点上方实体</span>';
    $("outBody").innerHTML = '<span class="hint">选择实体后，这里显示提示词全文。</span>';
    $("generateBtn").disabled = true;
    $("batchBtn").disabled = false;

    const c = result.counts;
    $("fileCount").textContent = `${c.files} 文件 · ${c.entities} 实体`;
    $("counts").textContent = `类 ${c.classes} / 方法 ${c.methods} / 函数 ${c.functions} · ${mode === "sample" ? `抽样 ${limit}（seed ${seed}）` : "全量"}`;
    setStatus(`分析完成：${result.repo_path}`, "ok");
  } catch (error) {
    setStatus(`分析失败：${error.message}`, "err");
  } finally {
    $("analyzeBtn").disabled = false;
  }
}

/* ------------------------------------------------------------------ render */
function renderFiles() {
  const host = $("fileTree");
  host.innerHTML = "";
  if (!state.analysis) return;
  const files = state.analysis.files;
  if (!files.length) {
    host.appendChild(el("p", "hint", "没有可生成的实体。"));
    return;
  }
  for (const file of files) {
    const row = el("div", "file");
    if (state.selectedFile === file.path) row.classList.add("active");
    const name = el("div", "fname");
    name.appendChild(el("b", "", file.path.split(/[\\/]/).pop()));
    name.appendChild(el("span", "", `${file.entities.length}`));
    row.appendChild(name);
    row.appendChild(el("div", "paths", file.path));
    row.addEventListener("click", () => selectFile(file.path));
    host.appendChild(row);
  }
}

function selectFile(path) {
  state.selectedFile = path;
  renderFiles();
  renderEntityStrip();
  const first = (state.analysis.files.find((f) => f.path === path) || {}).entities?.[0];
  if (first) selectEntity(first.qname);
}

function renderEntityStrip() {
  const host = $("entityStrip");
  host.innerHTML = "";
  const file = state.analysis?.files.find((f) => f.path === state.selectedFile);
  if (!file) {
    host.appendChild(el("span", "hint", "选择文件后显示其中的实体"));
    return;
  }
  for (const entity of file.entities) {
    const chip = el("div", `chip ${entity.kind}`);
    if (state.selectedEntity === entity.qname) chip.classList.add("active");
    chip.appendChild(el("span", "k", entity.kind));
    chip.appendChild(document.createTextNode(entity.name));
    const relCount = Object.values(entity.relations || {}).reduce((a, b) => a + b, 0);
    if (relCount) {
      const badge = el("span", "k", `${relCount}`);
      badge.style.background = "#123";
      chip.appendChild(badge);
    }
    chip.title = `${entity.qname}\n关系: ${JSON.stringify(entity.relations)}`;
    chip.addEventListener("click", () => selectEntity(entity.qname));
    host.appendChild(chip);
  }
}

async function selectEntity(qname) {
  state.selectedEntity = qname;
  renderEntityStrip();
  const { repo, customPath, mode, limit, seed } = analysisParams();
  const params = new URLSearchParams({ repo, path: customPath, mode, limit, seed, qname });
  setStatus("加载实体详情…", "warn");
  try {
    const detail = await api(`/api/entity?${params}`);
    state.entityDetail = detail;
    $("sourceTitle").textContent = `${detail.kind} · ${detail.name}`;
    $("promptStats").textContent = `提示词 ${detail.prompt_chars.toLocaleString()} 字符${detail.prompt_clipped ? " · 源码已裁剪" : ""}`;
    renderSource();
    const doc = await api(`/api/document?repo=${encodeURIComponent(repo)}&qname=${encodeURIComponent(qname)}`);
    state.document = doc.document || "";
    renderOutput();
    $("generateBtn").disabled = false;
    setStatus(`已选择 ${detail.qname}`, "ok");
  } catch (error) {
    setStatus(`加载失败：${error.message}`, "err");
  }
}

function renderSource() {
  const graphPane = $("graphPane");
  const sourcePre = $("sourceBody");
  if (state.sourceView === "graph") {
    sourcePre.classList.add("hidden");
    graphPane.classList.remove("hidden");
    loadGraph(state.selectedEntity).catch((error) => setStatus(error.message, "err"));
    return;
  }
  graphPane.classList.add("hidden");
  sourcePre.classList.remove("hidden");
  const detail = state.entityDetail;
  if (!detail) return;
  const text = state.sourceView === "source" ? detail.source : detail.prompt_source;
  const label = state.sourceView === "source" ? "完整源码" : "注入提示词的视图（类：__init__ 全量 + 方法签名）";
  sourcePre.textContent = `# ${label}\n${"-".repeat(60)}\n${text}`;
}

function renderOutput() {
  const host = $("outBody");
  const detail = state.entityDetail;
  if (!detail) return;
  host.innerHTML = "";

  if (state.outTab === "prompt") {
    host.textContent = detail.prompt;
    return;
  }

  if (state.outTab === "document") {
    if (!state.document) {
      host.appendChild(el("p", "hint", "尚未生成。点击右上「生成文档」（会真实调用模型并计费）。"));
      return;
    }
    host.textContent = state.document;
    return;
  }

  if (state.outTab === "relations") {
    const grid = el("div", "rel-grid");
    const blocks = Object.entries(detail.relations || {});
    if (!blocks.length) {
      grid.appendChild(el("p", "hint", "该实体没有可注入的关系。"));
    }
    for (const [label, targets] of blocks) {
      const block = el("div", "rel-block");
      block.appendChild(el("h3", "", `${label} · ${targets.length}`));
      const list = el("ul");
      for (const target of targets) list.appendChild(el("li", "", target));
      block.appendChild(list);
      grid.appendChild(block);
    }
    const meta = el("div", "rel-block");
    meta.appendChild(el("h3", "", "上下文摘要"));
    const ul = el("ul");
    ul.appendChild(el("li", "", `Uses: ${detail.uses.length ? detail.uses.join(", ") : "—"}`));
    ul.appendChild(el("li", "", `Used by: ${detail.used_by.length ? detail.used_by.join(", ") : "—"}`));
    ul.appendChild(el("li", "", `多态契约: ${detail.is_polymorphic ? "是" : "否"}`));
    ul.appendChild(el("li", "", `模板: ${detail.template}`));
    meta.appendChild(ul);
    grid.appendChild(meta);
    host.appendChild(grid);
    return;
  }

  if (state.outTab === "params") {
    const table = el("table", "params-table");
    const rows = [
      ["模型", detail.params.model],
      ["接口地址", detail.params.base_url],
      ["生成温度", detail.params.temperature],
      ["提示词上限 (字符)", detail.params.max_tokens],
      ["源码预算 (字符)", detail.params.source_budget],
      ["语言", detail.params.language],
      ["注入依赖", detail.params.relevant ? "是" : "否"],
      ["模板", detail.template],
      ["提示词长度", `${detail.prompt_chars.toLocaleString()} 字符`],
      ["源码行数", `${(detail.source.match(/\n/g) || []).length + 1}`],
      ["注入视图行数", `${(detail.prompt_source.match(/\n/g) || []).length + 1}`],
      ["实际调用", `POST ${detail.params.base_url}/chat/completions`],
    ];
    for (const [key, value] of rows) {
      const tr = el("tr");
      tr.appendChild(el("td", "", key));
      tr.appendChild(el("td", "", String(value)));
      table.appendChild(tr);
    }
    const wrap = el("div");
    wrap.style.padding = "8px 12px";
    wrap.appendChild(table);
    host.appendChild(wrap);
  }
}

/* --------------------------------------------------------------- generation */
async function generate() {
  if (!state.selectedEntity) return;
  const { repo, customPath, mode, limit, seed } = analysisParams();
  $("generateBtn").disabled = true;
  setStatus("生成中（真实调用模型）…", "warn");
  try {
    const body = {
      repo, path: customPath, mode, limit, seed, qname: state.selectedEntity,
      temperature: parseFloat($("cfgTemp").value) || 1,
      max_tokens: parseInt($("cfgMaxTokens").value, 10) || 16000,
      source_budget: parseInt($("cfgSourceBudget").value, 10) || 8000,
      template: $("cfgTemplate").value,
    };
    const result = await api("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    state.document = result.document;
    state.outTab = "document";
    document.querySelectorAll("#outTabs .tab").forEach((tab) =>
      tab.classList.toggle("active", tab.dataset.tab === "document"));
    renderOutput();

    state.usage.tokens += result.tokens.prompt + result.tokens.completion;
    state.usage.cost += result.cost_cny;
    state.usage.calls += 1;
    $("usage").textContent = `本次会话：${state.usage.calls} 次调用 · ${state.usage.tokens.toLocaleString()} tokens · ${money(state.usage.cost, result.currency)}`;
    const detail = result.cost_detail || {};
    setStatus(`生成完成：${result.chars} 字符 · ${result.seconds}s · in ${result.tokens.prompt}`
      + (result.tokens.cached ? `(缓存 ${result.tokens.cached})` : "")
      + ` / out ${result.tokens.completion} tokens · ${money(result.cost, result.currency)}`
      + (detail.mode ? ` · ${detail.tier}/${detail.mode}` : ""), "ok");
  } catch (error) {
    setStatus(`生成失败：${error.message}`, "err");
  } finally {
    $("generateBtn").disabled = false;
  }
}

/* ------------------------------------------------------------ batch generation */
async function generateAll() {
  if (!state.analysis) {
    setStatus("请先分析仓库", "warn");
    return;
  }
  const { repo, customPath, mode, limit, seed } = analysisParams();
  const total = state.analysis.counts.entities;
  const pricing = (state.config.pricing || {});
  const priceMode = pricing.mode || "standard";
  const tier = (pricing.tiers || {}).short || {};
  const rate = tier[priceMode] || tier.standard || {};
  const guess = total * ((1400 / 1e6) * (rate.input || 0) + (2100 / 1e6) * (rate.output || 0));
  if (!confirm(`将为 ${total} 个实体生成文档（真实调用模型，按 ${pricing.currency || "USD"} ${priceMode} 费率估算约 ${money(guess, pricing.currency)}），继续？`)) return;

  $("batchBtn").disabled = true;
  setStatus(`批量生成中：0/${total}`, "warn");
  try {
    const { job } = await api("/api/generate_all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        repo, path: customPath, mode, limit, seed,
        temperature: parseFloat($("cfgTemp").value) || 1,
        max_tokens: parseInt($("cfgMaxTokens").value, 10) || 16000,
        source_budget: parseInt($("cfgSourceBudget").value, 10) || 8000,
        template: $("cfgTemplate").value,
      }),
    });
    let last = null;
    for (;;) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      const status = await api(`/api/job?id=${job}`);
      if (status.status === "error") throw new Error(status.error);
      const progress = status.progress || {};
      last = status;
      const done = progress.done || 0;
      setStatus(`批量生成：${done}/${progress.total || total} · ${money(progress.cost, progress.currency)}`
        + (progress.failed ? ` · 失败 ${progress.failed}` : ""), "warn");
      $("usage").textContent = `本次会话：in ${(progress.prompt_tokens || 0).toLocaleString()}`
        + ` / out ${(progress.completion_tokens || 0).toLocaleString()} tokens · `
        + money(progress.cost, progress.currency);
      if (status.status === "done" || status.status === "cancelled") break;
    }
    const progress = last.progress || {};
    setStatus(`批量完成：${progress.done}/${progress.total} 实体 · ${money(progress.cost, progress.currency)}`
      + (progress.failed ? ` · 失败 ${progress.failed}` : ""), "ok");
    if (state.selectedEntity) {
      const doc = await api(`/api/document?repo=${encodeURIComponent(repo)}&qname=${encodeURIComponent(state.selectedEntity)}`);
      state.document = doc.document || "";
      renderOutput();
    }
  } catch (error) {
    setStatus(`批量生成失败：${error.message}`, "err");
  } finally {
    $("batchBtn").disabled = false;
  }
}

/* -------------------------------------------------------------------- wiring */
function wire() {
  $("analyzeBtn").addEventListener("click", runAnalysis);
  $("batchBtn").addEventListener("click", generateAll);
  if (typeof wireGraphInteractions === "function") wireGraphInteractions();
  $("generateBtn").addEventListener("click", generate);
  $("configBtn").addEventListener("click", () => $("drawer").classList.remove("hidden"));
  $("closeDrawer").addEventListener("click", () => $("drawer").classList.add("hidden"));
  $("saveConfig").addEventListener("click", () => saveConfig().catch((e) => setStatus(e.message, "err")));
  $("copyBtn").addEventListener("click", async () => {
    await navigator.clipboard.writeText($("outBody").textContent || "");
    setStatus("已复制当前面板内容", "ok");
  });

  $("mode").addEventListener("change", () => {
    $("limitField").style.opacity = $("mode").value === "sample" ? "1" : ".4";
  });

  document.querySelectorAll("#sourceTabs .tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll("#sourceTabs .tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      state.sourceView = tab.dataset.view;
      renderSource();
    });
  });

  document.querySelectorAll("#outTabs .tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll("#outTabs .tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      state.outTab = tab.dataset.tab;
      renderOutput();
    });
  });

  $("repo").addEventListener("change", () => { $("customPath").value = ""; });
}

wire();
bootstrap().catch((error) => setStatus(`初始化失败：${error.message}`, "err"));
