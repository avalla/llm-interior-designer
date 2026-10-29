// SVG plan viewer: walls, rooms, openings, furniture (with its front), uses (access and splash zones, destinations),
// pan with the mouse, zoom with the wheel, highlight of the element a result is about.
import type { Bounds, Ring, Row, Scene } from "./types";

const NS = "http://www.w3.org/2000/svg";
const DIRS: Record<string, [number, number]> = { north: [0, 1], south: [0, -1], east: [1, 0], west: [-1, 0] };
export const LAYERS = ["drawing", "rooms", "furniture", "openings", "uses", "destinations"] as const;
type Layer = (typeof LAYERS)[number];

function el<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number>, parent?: Element) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  parent?.appendChild(e);
  return e;
}

// y is flipped once, on the drawing group: shapes keep plan coordinates, labels are placed at (x, -y)
const path = (rings: Ring[]) => rings.map((r) => "M" + r.map(([x, y]) => `${x},${y}`).join("L") + "Z").join("");
const lines = (ls: Ring[]) => ls.map((r) => "M" + r.map(([x, y]) => `${x},${y}`).join("L")).join("");

function centroid(r: Ring): [number, number] {
  const n = r.length - 1 || 1;
  let x = 0, y = 0;
  for (let i = 0; i < n; i++) { x += r[i][0]; y += r[i][1]; }
  return [x / n, y / n];
}

export class PlanView {
  private view: { x: number; y: number; w: number; h: number } = { x: 0, y: 0, w: 10, h: 10 };
  private groups = {} as Record<Layer | "base" | "labels" | "hl", SVGGElement>;
  private hidden = new Set<Layer>();
  private sceneBounds: Bounds | null = null;

  constructor(private svg: SVGSVGElement) {
    this.svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    this.panZoom();
  }

  render(scene: Scene) {
    this.svg.replaceChildren();
    const flip = el("g", { transform: "scale(1,-1)" }, this.svg);
    for (const name of ["drawing", "base", ...LAYERS.filter((l) => l !== "drawing"), "hl"] as const) {
      this.groups[name] = el("g", { "data-layer": name }, flip);
    }
    this.groups.labels = el("g", {}, this.svg);
    const g = this.groups;
    for (const r of scene.rooms) {
      el("path", { d: path(r.rings), class: "room" + (r.private ? " private" : "") }, g.rooms);
      const [x, y] = centroid(r.rings[0]);
      const t = el("text", { x, y: -y, class: "room-label" }, g.labels);
      t.textContent = `${r.name} · ${r.area.toFixed(1)} m²`;
    }
    // the drawing as it is, under what was recognised; one path per layer, so a layer can be lit from the mapping table
    for (const l of scene.drawing ?? []) {
      el("path", { d: lines(l.lines), class: `dwg ${l.category}`, "data-dwg-layer": l.name }, g.drawing);
    }
    el("path", { d: path(scene.walls), class: "wall", "fill-rule": "evenodd" }, g.base);
    for (const w of scene.windows) el("path", { d: path(w.rings), class: "window" }, g.base);
    for (const d of scene.doors) {
      el("path", { d: path(d.rings), class: "sweep" }, g.openings);
      el("path", { d: path(d.leaf), class: "leaf" }, g.openings);
    }
    for (const s of scene.slides) {
      el("path", { d: path(s.rings), class: "leaf" }, g.openings);
      el("path", { d: path(s.open), class: "sweep" }, g.openings);
    }
    for (const f of scene.furniture) {
      const cls = "furniture" + (f.hung ? " hung" : "") + (f.type === "unknown" ? " unknown" : "");
      const p = el("path", { d: path(f.rings), class: cls }, g.furniture);
      el("title", {}, p).textContent = `${f.item} (${f.block}) · ${f.type}` +
        (f.front ? ` · front ${f.front.side}, ${f.front.why} (${f.front.confidence})` : "");
      if (f.front && f.rings.length) {
        const [x, y] = centroid(f.rings[0]);
        const [dx, dy] = DIRS[f.front.side] ?? [0, 0];
        el("line", { x1: x, y1: y, x2: x + dx * 0.3, y2: y + dy * 0.3, class: "front" }, g.furniture);
      }
    }
    for (const a of scene.access) el("path", { d: path(a.rings), class: "zone" }, g.uses);
    for (const w of scene.wet) el("path", { d: path(w.rings), class: "wet" }, g.uses);
    for (const t of scene.targets) {
      el("title", {}, el("circle", { cx: t.point[0], cy: t.point[1], r: 0.07, class: "target" }, g.destinations))
        .textContent = t.label;
    }
    if (scene.start) el("circle", { cx: scene.start[0], cy: scene.start[1], r: 0.12, class: "start" }, g.destinations);
    for (const l of this.hidden) g[l].style.display = "none";
    this.sceneBounds = scene.bounds;
    this.fitAll();
  }

  /** The whole plan in view (F key, Fit button). */
  fitAll() {
    if (this.sceneBounds) this.fit(this.sceneBounds, 0.6);
  }

  /** Lights the lines of one drawing layer (mapping table hover); null switches it off. */
  lightLayer(name: string | null) {
    this.svg.querySelectorAll<SVGPathElement>("[data-dwg-layer]").forEach((p) =>
      p.classList.toggle("lit", p.dataset.dwgLayer === name));
  }

  toggle(layer: Layer, on: boolean) {
    on ? this.hidden.delete(layer) : this.hidden.add(layer);
    if (this.groups[layer]) this.groups[layer].style.display = on ? "" : "none";
  }

  highlight(row: Row | null) {
    const g = this.groups.hl;
    if (!g) return;
    g.replaceChildren();
    if (!row) return;
    if (row.where.shapes.length) el("path", { d: path(row.where.shapes), class: "hl" }, g);
    for (const [x, y] of row.where.points) el("circle", { cx: x, cy: y, r: 0.15, class: "hl-point" }, g);
    if (row.where.bounds) {                       // keep the room around the element in view
      const [x0, y0, x1, y1] = row.where.bounds, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
      const h = Math.max(x1 - x0, y1 - y0, 4) / 2;
      this.fit([cx - h, cy - h, cx + h, cy + h], 1.0);
    }
  }

  fit([x0, y0, x1, y1]: Bounds, margin: number) {
    this.view = { x: x0 - margin, y: -y1 - margin, w: x1 - x0 + 2 * margin, h: y1 - y0 + 2 * margin };
    this.apply();
  }

  private apply() {
    const v = this.view;
    this.svg.setAttribute("viewBox", `${v.x} ${v.y} ${v.w} ${v.h}`);
  }

  private panZoom() {
    let last: [number, number] | null = null;
    const scale = () => {
      const r = this.svg.getBoundingClientRect();
      return Math.max(this.view.w / r.width, this.view.h / r.height);
    };
    this.svg.addEventListener("wheel", (e) => {
      e.preventDefault();
      const r = this.svg.getBoundingClientRect(), s = scale();
      const k = Math.exp(e.deltaY * 0.0015);
      const cx = this.view.x + this.view.w / 2 + (e.clientX - r.left - r.width / 2) * s;
      const cy = this.view.y + this.view.h / 2 + (e.clientY - r.top - r.height / 2) * s;
      this.view = { x: cx - (cx - this.view.x) * k, y: cy - (cy - this.view.y) * k, w: this.view.w * k, h: this.view.h * k };
      this.apply();
    }, { passive: false });
    this.svg.addEventListener("pointerdown", (e) => {
      last = [e.clientX, e.clientY];
      this.svg.setPointerCapture(e.pointerId);
      this.svg.classList.add("dragging");
    });
    this.svg.addEventListener("pointermove", (e) => {
      if (!last) return;
      const s = scale();
      this.view.x -= (e.clientX - last[0]) * s;
      this.view.y -= (e.clientY - last[1]) * s;
      last = [e.clientX, e.clientY];
      this.apply();
    });
    const stop = () => { last = null; this.svg.classList.remove("dragging"); };
    this.svg.addEventListener("pointerup", stop);
    this.svg.addEventListener("pointercancel", stop);
  }
}
