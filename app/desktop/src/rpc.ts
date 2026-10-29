// Transport to the sidecar: through the Tauri shell when the UI runs in the app, over HTTP to
// `python -m app.sidecar.server --http 8765` when it runs in a browser (UI development only).
import { invoke } from "@tauri-apps/api/core";

export const inTauri = "__TAURI_INTERNALS__" in window;
const DEV_URL = "http://127.0.0.1:8765/rpc";

export async function rpc<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
  if (inTauri) {
    return invoke<T>("sidecar", { method, params });
  }
  const r = await fetch(DEV_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: 1, method, params }),
  });
  const answer = await r.json();
  if (answer.error) throw new Error(answer.error);
  return answer.result as T;
}

export async function pickFile(kind: "plan" | "profile", save = false): Promise<string | null> {
  if (!inTauri) {
    return window.prompt(save ? "Save the profile to (path):" : `Path of the ${kind} to open:`);
  }
  const dialog = await import("@tauri-apps/plugin-dialog");
  const filters = kind === "plan"
    ? [{ name: "Plan", extensions: ["dxf", "dwg", "DXF", "DWG"] }]
    : [{ name: "Studio profile", extensions: ["json"] }];
  if (save) return dialog.save({ filters, defaultPath: "studio-profile.json" });
  const picked = await dialog.open({ multiple: false, directory: false, filters });
  return typeof picked === "string" ? picked : null;
}
