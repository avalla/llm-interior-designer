# Interior Check (desktop shell)

Tauri v2 window + TypeScript UI around the Python sidecar (`app/sidecar/server.py`), which does the work: plan
recognition, furniture semantics, checks. Architecture and decisions: `docs/desktop-app.md` (D6).

## Run in development

```bash
cd app/desktop
npm install
npm run tauri dev          # builds the shell, starts Vite on :1420, opens the window
```

The shell starts the sidecar on the first request with `uv run --with ezdxf --with shapely python -m app.sidecar.server`
from the repository root, so `uv` must be on the PATH. Set `INTERIORS_SIDECAR` to run another command (program and
arguments separated by spaces). DWG files need the ODA File Converter, found at its default install place.

UI work in a browser, without the shell:

```bash
uv run --with ezdxf --with shapely python -m app.sidecar.server --http 8765     # repository root
npm run dev                                                                     # app/desktop
# http://localhost:1420/?path=/abs/plan.dxf&profile=/abs/profile.json&tab=mapping
```

## Layout

| Path | Role |
|---|---|
| `src/main.ts` | state, panels (results, mapping, assumptions), profile load/save |
| `src/plan.ts` | SVG plan viewer: layers, pan and zoom, highlight of a result |
| `src/rpc.ts` | transport: Tauri command `sidecar` in the app, HTTP in a browser |
| `src/types.ts` | shapes of the sidecar's answers |
| `src-tauri/src/lib.rs` | starts, feeds and restarts the sidecar (JSON lines over stdio) |

## Tests

`npm run build` (TypeScript check + bundle); `cargo test --lib` in `src-tauri` (a sidecar that dies is restarted and
the request repeated); `app/tests/sidecar_smoke.py` for the sidecar itself. All three run in CI.

## Packaging

`.github/workflows/package.yml` (push to main, tags `v*`, or run by hand) builds the Windows installer: PyInstaller
freezes the sidecar into one `interiors-sidecar.exe`, a smoke test runs it on a room drawn on the spot, Tauri bundles
it next to the app (`src-tauri/tauri.release.conf.json`, `externalBin`) in an NSIS installer, uploaded as the artifact
`interior-check-windows`. Unsigned: SmartScreen asks once (More info -> Run anyway); per-user install, no admin rights.
The same build on macOS, locally:

```bash
uv run --with pyinstaller --with ezdxf --with shapely pyinstaller --onefile --name interiors-sidecar --paths . \
  --paths app/core --collect-data ezdxf app/sidecar/server.py                       # repository root
cp dist/interiors-sidecar app/desktop/src-tauri/binaries/interiors-sidecar-$(rustc -vV | sed -n 's/^host: //p')
cd app/desktop && npx tauri build --config src-tauri/tauri.release.conf.json --bundles app
```

## Not yet

Code signing, per-piece front and type overrides kept across re-imports, PDF report, annotated DXF.
