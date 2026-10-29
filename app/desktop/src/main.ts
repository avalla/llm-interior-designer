// Interior Check: open a plan, confirm the mapping (layers, blocks, units, front convention), read the results on the
// plan. Every correction goes into the studio profile, which the next drawing of the studio starts from.
import { GLOSSARY, helpHtml, legendHtml } from "./help";
import { PlanView, LAYERS } from "./plan";
import { inTauri, pickFile, rpc } from "./rpc";
import type { Analysis, Profile, Row, Vocabulary } from "./types";

const $ = <T extends HTMLElement>(sel: string) => document.querySelector(sel) as T;
const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);

const state = {
  path: "" as string,
  profile: {} as Profile,
  analysis: null as Analysis | null,
  vocab: { categories: [], types: [], fronts: [] } as Vocabulary,
  tab: "results",
  selected: -1,
  dirty: false,
  bannerFolded: false,
};
const plan = new PlanView($<SVGSVGElement & HTMLElement>("#plan") as unknown as SVGSVGElement);

function status(text: string, error = false) {
  const s = $("#status");
  s.textContent = text;
  s.style.color = error ? "var(--bad)" : "";
}

async function analyse() {
  if (!state.path) return;
  status(`analysing ${state.path}…`);
  $<HTMLButtonElement>("#rerun").disabled = true;
  try {
    const t0 = performance.now();
    state.analysis = await rpc<Analysis>("analyse", { path: state.path, profile: state.profile });
    state.selected = -1;
    state.dirty = false;
    status(`analysed in ${((performance.now() - t0) / 1000).toFixed(1)} s`);
  } catch (e) {
    status(String(e), true);
  }
  $<HTMLButtonElement>("#rerun").disabled = false;
  $<HTMLButtonElement>("#save-profile").disabled = false;
  try {
    render();
  } catch (e) {                                   // a drawing that breaks the viewer must say so, not stay blank
    status(`cannot draw the plan: ${e}`, true);
    console.error(e);
  }
}

function render() {
  const a = state.analysis;
  $("#empty").style.display = a ? "none" : "";
  $("#layers").style.display = a ? "flex" : "none";
  $("#file").textContent = a ? a.name : "no plan open";
  if (a) plan.render(a.scene);
  renderBanner(a);
  const nc = a?.summary["NON-COMPLIANT"] ?? 0, nv = a?.summary["NOT VERIFIABLE"] ?? 0;
  $("#summary").innerHTML = !a ? "" : !a.checkable ? '<span class="chip warn">not checkable yet: see Mapping</span>' :
    `<span class="chip ${nc ? "bad" : "good"}">${nc} non-compliant</span> ` +
    (nv ? `<span class="chip warn">${nv} not verifiable</span>` : "");
  $("#confirm-count").textContent = a && a.mapping.confirm.length ? String(a.mapping.confirm.length) : "";
  $<HTMLButtonElement>("#rerun").classList.toggle("primary", state.dirty);
  renderPanel();
}

// What was found, what is missing and what to do, above the plan
function renderBanner(a: Analysis | null) {
  const b = $("#banner");
  b.style.display = a ? "flex" : "none";
  if (!a) return;
  const f = a.diagnosis.found;
  const item = (n: number, label: string) => `<span class="${n ? "" : "zero"}"><b>${n}</b> ${label}</span>`;
  b.classList.toggle("folded", state.bannerFolded);
  b.innerHTML = `<div class="found" title="Click to show or hide the notes">Found: ${f.walls_m2 ? `<b>${f.walls_m2}</b> m² of walls` : '<span class="zero">no walls</span>'} ·
      ${item(f.rooms, "rooms")} · ${item(f.doors + f.slides, "doors")} · ${item(f.windows, "windows")} ·
      ${item(f.furniture, "furniture")}</div>` +
    a.diagnosis.notes.map((n) => `<div class="note ${n.level}">${esc(n.text)}<div class="action">${esc(n.action)}</div></div>`)
      .join("");
}

function renderPanel() {
  document.querySelectorAll<HTMLButtonElement>("#tabs button").forEach((b) =>
    b.classList.toggle("active", b.dataset.tab === state.tab));
  const p = $("#panel"), a = state.analysis;
  if (!a) { p.innerHTML = '<p class="muted">No plan.</p>'; return; }
  p.innerHTML = state.tab === "results" ? resultsHtml(a) : state.tab === "mapping" ? mappingHtml(a) : assumptionsHtml(a);
}

// ---------- results ----------
function rowHtml(r: Row, i: number) {
  const cls = r.status === "NON-COMPLIANT" ? r.sev || "blocking" : r.sev === "improvement" ? "improvement" :
    r.status === "VERIFIED" ? "verified" : "significant";
  const sel = i === state.selected, g = GLOSSARY[r.cat];
  return `<div class="row ${cls}${sel ? " selected" : ""}" data-row="${i}">
    <div class="what">${esc(r.cat)} · ${esc(r.elem)}${g ? `<span class="q" data-help="${esc(r.cat)}" title="What does this check mean?">?</span>` : ""}</div>
    <div>${esc(r.measure)} <span class="muted">(${esc(r.threshold)})</span></div>
    <div class="meta">${[r.room, r.sev, r.note].filter(Boolean).map(esc).join(" · ")}</div>
    ${sel ? `<div class="explain">${g ? esc(g.what) + "<br>" : ""}<span class="muted">Measured: ${esc(r.method)}</span>
      ${r.where.bounds ? "" : '<br><span class="muted">This result has no single place on the plan.</span>'}</div>` : ""}</div>`;
}

function resultsHtml(a: Analysis) {
  if (!a.checkable) {
    const todo = a.diagnosis.notes.map((n) => `<li><b>${esc(n.text)}</b><br>${esc(n.action)}</li>`).join("");
    return `<p>This drawing cannot be checked yet.</p><ol>${todo}</ol>`;
  }
  const rows = a.results.map((r, i) => [r, i] as const);
  const bad = rows.filter(([r]) => r.status === "NON-COMPLIANT");
  const notv = rows.filter(([r]) => r.status === "NOT VERIFIABLE");
  const better = rows.filter(([r]) => r.status === "VERIFIED" && r.sev === "improvement");
  const ok = rows.filter(([r]) => r.status === "VERIFIED" && r.sev !== "improvement");
  const list = (xs: typeof rows) => xs.map(([r, i]) => rowHtml(r, i)).join("");
  const intro = bad.length ? '<p class="muted small">Click a result to see it on the plan; <b>?</b> explains the check.</p>'
    : `<p class="ok-msg">No issues found in ${a.results.length} checks.</p>`;
  return `${intro}<h3>Non-compliant (${bad.length})</h3>${list(bad) || '<p class="muted">None.</p>'}
    ${notv.length ? `<h3>Not verifiable (${notv.length})</h3>${list(notv)}` : ""}
    ${better.length ? `<h3>Below comfort (${better.length})</h3>${list(better)}` : ""}
    <details><summary>Verified (${ok.length})</summary>${list(ok)}</details>`;
}

// ---------- mapping ----------
function conf(c: number) {
  return `<span class="conf ${c < 0.5 ? "low" : c < 0.7 ? "mid" : "high"}">${c.toFixed(1)}</span>`;
}

function select(kind: string, name: string, value: string, options: string[]) {
  return `<select data-kind="${kind}" data-name="${esc(name)}">${options.map((o) =>
    `<option${o === value ? " selected" : ""}>${esc(o)}</option>`).join("")}</select>`;
}

// Catalogue codes (AR01, AR02...) are typed once per family: the row's name is the glob the profile stores (AR*).
function families(blocks: Analysis["mapping"]["blocks"]) {
  const groups = new Map<string, Analysis["mapping"]["blocks"]>();
  for (const b of blocks) {
    const code = /^([A-Za-z][A-Za-z_-]*?)[-_]?\d+$/.exec(b.name);
    const key = code ? code[1] + "*" : b.name;
    groups.set(key, [...(groups.get(key) ?? []), b]);
  }
  return [...groups].map(([name, bs]) => {
    const types = new Set(bs.map((b) => b.applied));
    const c = Math.min(...bs.map((b) => b.candidates[0]?.confidence ?? 0));
    const why = bs[0].candidates[0]?.why ?? "no keyword";
    return { name, count: bs.reduce((n, b) => n + b.count, 0), applied: types.size === 1 ? bs[0].applied : "unknown",
             confidence: c, why: types.size === 1 ? why : "mixed: " + [...types].join(", ") };
  });
}

function mappingHtml(a: Analysis) {
  const m = a.mapping, pr = state.profile;
  const units = ["auto", "mm", "cm", "m", "in"];
  const layers = m.layers.filter((l) => l.candidates.length || pr.layers?.[l.name]).map((l) => {
    const c = l.candidates[0];
    return `<tr data-layer-row="${esc(l.name)}" class="${pr.layers?.[l.name] ? "changed" : ""}"><td>${esc(l.name)}</td>
      <td>${select("layer", l.name, l.applied, state.vocab.categories)}</td>
      <td>${c ? conf(c.confidence) : ""}</td><td class="why">${c ? esc(c.why) : ""}</td></tr>`;
  }).join("");
  const blocks = families(m.blocks)
    .sort((x, y) => x.confidence - y.confidence || x.name.localeCompare(y.name))
    .map((f) => `<tr class="${pr.blocks?.[f.name] ? "changed" : ""}"><td>${esc(f.name)}${f.count > 1 ? ` ×${f.count}` : ""}</td>
        <td>${select("block", f.name, f.applied, ["unknown", ...state.vocab.types])}</td>
        <td>${conf(f.confidence)}</td><td class="why">${esc(f.why)}</td></tr>`).join("");
  const fronts = m.fronts.filter((f) => f.confidence < 0.7).map((f) =>
    `<tr><td>${esc(f.item)}</td><td>${esc(f.side)}</td><td>${conf(f.confidence)}</td><td class="why">${esc(f.why)}</td></tr>`).join("");
  const todo = m.confirm.length ? `<p class="todo"><b>${m.confirm.length} choices to confirm</b> (confidence below 0.7,
      in red or orange below). Change what is wrong, press <b>Re-analyse</b>, then <b>Save profile</b>.</p>`
    : '<p class="ok-msg">Everything was read with good confidence.</p>';
  return `${todo}<p class="muted small">Hover a layer to see its lines on the plan. Corrections go into the studio profile, so
    the next plan of the studio is read correctly at once.</p>
    <h3>Units</h3><p>1 drawing unit = ${a.units.factor} m <span class="why">(${esc(a.units.note)})</span><br>
      Override: ${select("units", "units", pr.units ?? "auto", units)}</p>
    <h3>Layers</h3><table><tr><th>Layer</th><th>Category</th><th>Conf.</th><th>Evidence</th></tr>${layers}</table>
    <h3>Blocks (${m.blocks.length})</h3>
    <table><tr><th>Block</th><th>Type</th><th>Conf.</th><th>Evidence</th></tr>${blocks}</table>
    <h3>Furniture fronts</h3>
    <p>Front of furniture blocks: ${select("front", "front", pr.front ?? "infer from the plan",
      ["infer from the plan", ...state.vocab.fronts])} <span class="why">block axis that faces the room</span></p>
    ${fronts ? `<table><tr><th>Piece</th><th>Front</th><th>Conf.</th><th>Why</th></tr>${fronts}</table>`
      : '<p class="muted">No front below 0.7.</p>'}`;
}

function assumptionsHtml(a: Analysis) {
  const un = a.unrecognised.map((u) => `<li>${esc(JSON.stringify(u))}</li>`).join("");
  return `<h3>Assumptions (${a.assumptions.length})</h3><p class="muted">Defaults the plan does not state; check them.</p>
    <ul>${a.assumptions.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
    ${un ? `<h3>Not recognised</h3><ul>${un}</ul>` : ""}`;
}

function onMappingChange(e: Event) {
  const s = e.target as HTMLSelectElement;
  const kind = s.dataset.kind!, name = s.dataset.name!, v = s.value;
  const pr = state.profile;
  if (kind === "layer") (pr.layers ??= {})[name] = v;
  if (kind === "block") v === "unknown" ? delete pr.blocks?.[name] : ((pr.blocks ??= {})[name] = v);
  if (kind === "units") v === "auto" ? delete pr.units : (pr.units = v);
  if (kind === "front") v.startsWith("infer") ? delete pr.front : (pr.front = v);
  state.dirty = true;
  status("mapping changed: press Re-analyse");
  render();
}

// ---------- wiring ----------
async function openPlan(path?: string | null) {
  path ??= await pickFile("plan");
  if (!path) return;
  state.path = path;
  await analyse();
}

$("#open").addEventListener("click", () => openPlan());
$("#open-2").addEventListener("click", () => openPlan());
$("#demo").addEventListener("click", async () => {
  try {
    await openPlan((await rpc<{ path: string }>("demo")).path);
  } catch (e) { status(String(e), true); }
});
$("#fit").addEventListener("click", () => plan.fitAll());
$("#legend-toggle").addEventListener("click", () => $("#legend").classList.toggle("shown"));

// ---------- help ----------
function openHelp(focus?: string) {
  const d = $("#help-drawer");
  $("#help-body").innerHTML = helpHtml(focus);
  d.hidden = false;
  const target = focus && document.getElementById("help-" + focus.replace(/\s/g, "-"));
  if (target) target.scrollIntoView({ block: "center" });
}
const closeHelp = () => { $("#help-drawer").hidden = true; };
$("#help").addEventListener("click", () => ($("#help-drawer").hidden ? openHelp() : closeHelp()));
$("#help-2").addEventListener("click", () => openHelp());
$("#help-close").addEventListener("click", closeHelp);
document.addEventListener("keydown", (e) => {
  if ((e.target as HTMLElement).closest("select, input, textarea")) return;
  if (e.key === "F1" || e.key === "?") { e.preventDefault(); openHelp(); }
  else if (e.key === "Escape") closeHelp();
  else if (e.key === "f" || e.key === "F") plan.fitAll();
});

// ---------- drag and drop (desktop app: the webview reports the dropped paths) ----------
if (inTauri) {
  import("@tauri-apps/api/webview").then(({ getCurrentWebview }) =>
    getCurrentWebview().onDragDropEvent((ev) => {
      const drop = $("#drop"), p = ev.payload;
      if (p.type === "enter" || p.type === "over") drop.classList.add("shown");
      else drop.classList.remove("shown");
      if (p.type === "drop") {
        const plan = p.paths.find((x) => /\.(dxf|dwg)$/i.test(x));
        plan ? openPlan(plan) : status("drop a .dxf or .dwg file", true);
      }
    }));
}
$("#rerun").addEventListener("click", analyse);
$("#load-profile").addEventListener("click", async () => {
  const path = await pickFile("profile");
  if (!path) return;
  try {
    state.profile = await rpc<Profile>("load_profile", { path });
    status(`profile ${path} loaded`);
    if (state.path) await analyse();
  } catch (e) { status(String(e), true); }
});
$("#save-profile").addEventListener("click", async () => {
  const path = await pickFile("profile", true);
  if (!path) return;
  try {
    await rpc("save_profile", { path, profile: state.profile });
    status(`profile saved to ${path}`);
  } catch (e) { status(String(e), true); }
});
$("#tabs").addEventListener("click", (e) => {
  const t = (e.target as HTMLElement).closest("button")?.dataset.tab;
  if (t) { state.tab = t; renderPanel(); }
});
$("#banner").addEventListener("click", () => {                // the notes can be folded away to see the plan
  state.bannerFolded = !state.bannerFolded;
  $("#banner").classList.toggle("folded", state.bannerFolded);
});
$("#panel").addEventListener("change", onMappingChange);
$("#panel").addEventListener("mouseover", (e) =>          // hovering a layer lights its lines on the plan
  plan.lightLayer((e.target as HTMLElement).closest<HTMLElement>("[data-layer-row]")?.dataset.layerRow ?? null));
$("#panel").addEventListener("mouseleave", () => plan.lightLayer(null));
$("#panel").addEventListener("click", (e) => {
  const q = (e.target as HTMLElement).closest<HTMLElement>("[data-help]");
  if (q) { openHelp(q.dataset.help); return; }
  const r = (e.target as HTMLElement).closest<HTMLElement>("[data-row]");
  if (!r || !state.analysis) return;
  state.selected = Number(r.dataset.row);
  plan.highlight(state.analysis.results[state.selected]);
  renderPanel();
});
$("#layer-boxes").innerHTML = LAYERS.map((l) =>
  `<label><input type="checkbox" data-layer="${l}" checked> ${l}</label>`).join("");
$("#legend").innerHTML = legendHtml();
$("#layers").addEventListener("change", (e) => {
  const c = e.target as HTMLInputElement;
  plan.toggle(c.dataset.layer as (typeof LAYERS)[number], c.checked);
});

(async () => {
  render();
  try {
    state.vocab = await rpc<Vocabulary>("vocabulary");
    status("ready");
  } catch (e) {
    status(`analysis engine not available: ${e}`, true);
  }
  // development: ?path=...&profile=... opens a plan at start
  const q = new URLSearchParams(location.search);
  if (q.get("profile")) state.profile = await rpc<Profile>("load_profile", { path: q.get("profile")! });
  if (q.get("tab")) state.tab = q.get("tab")!;
  if (q.get("path")) await openPlan(q.get("path"));
})();
