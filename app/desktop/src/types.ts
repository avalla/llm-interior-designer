// Shapes of the sidecar's answers (app/sidecar/server.py). Coordinates in metres, y up.
export type Ring = [number, number][];
export type Bounds = [number, number, number, number];

export interface Candidate { confidence: number; why: string; category?: string; type?: string }
export interface Front { item: string; side: string; why: string; confidence: number }

export interface Scene {
  bounds: Bounds | null;
  walls: Ring[];
  rooms: { rings: Ring[]; name: string; area: number; private: boolean }[];
  doors: { rings: Ring[]; name: string; leaf: Ring[] }[];
  slides: { rings: Ring[]; name: string; open: Ring[] }[];
  windows: { rings: Ring[]; name: string }[];
  furniture: { rings: Ring[]; item: string; block: string; type: string; hung: boolean; front: Front | null }[];
  access: { rings: Ring[]; label: string }[];
  wet: { rings: Ring[]; label: string }[];
  targets: { label: string; point: [number, number] }[];
  start: [number, number] | null;
  drawing: { name: string; category: string; lines: Ring[] }[];
}

export interface Diagnosis {
  found: { walls_m2: number; doors: number; slides: number; windows: number; rooms: number; furniture: number };
  notes: { level: "error" | "warn" | "info"; text: string; action: string }[];
}

export interface Row {
  cat: string; elem: string; measure: string; threshold: string; status: string; sev: string; method: string;
  note: string; room: string;
  where: { shapes: Ring[]; points: [number, number][]; bounds: Bounds | null };
}

export interface Profile {
  units?: string;
  layers?: Record<string, string>;
  blocks?: Record<string, string>;
  front?: string | null;
}

export interface Analysis {
  name: string;
  checkable: boolean;
  units: { factor: number; note: string };
  scene: Scene;
  mapping: {
    layers: { name: string; applied: string; candidates: Candidate[] }[];
    blocks: { name: string; count: number; applied: string; candidates: Candidate[] }[];
    fronts: Front[];
    confirm: { kind: string; name: string; applied: string; confidence: number }[];
  };
  assumptions: string[];
  unrecognised: Record<string, unknown>[];
  results: Row[];
  summary: Record<string, number>;
  profile: Profile;
  diagnosis: Diagnosis;
}

export interface Vocabulary { categories: string[]; types: string[]; fronts: string[] }
