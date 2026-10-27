# Interior design with FreeCAD and AI agents

A working base for designing **interior layouts and furnishing** of apartments and villas by talking to an agent
(Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode). The agent builds the 3D model in FreeCAD, **checks** it
against real-use rules (doors that open, space behind chairs, routes, daylight, wardrobe assembly...) and delivers the
files for **AutoCAD**.

The result is always a **preliminary proposal**: structure, building services and regulatory compliance must be checked by
licensed professionals. Every project's report explicitly lists what could not be verified.

## What it does

- **Onboarding**: collects starting files (DWG/DXF/PDF/photos), type of work, occupants, furnishing style, constraints;
  fills in a brief with the source of every item and an assumption log.
- **Model**: walls, doors (with jambs and reveals), windows (with subframes), sliding doors, furniture, in phases:
  envelope -> main furniture -> details.
- **Automatic checks** on every run, each with a status (VERIFIED / NON-COMPLIANT / NOT VERIFIABLE / NOT APPLICABLE) and a
  severity (blocking / significant / improvement):

  | Check | What it verifies |
  |---|---|
  | Openings | full trajectory of doors, window and wardrobe leaves, sliding doors: no 3D collision |
  | Handles and reveals | handle clear with the leaf at 90 degrees, at least 10 cm for the jamb |
  | Seats | from the surface edge: 75 cm to stand up, 90 to walk behind a seated person |
  | Access zones | 70 cm clear in front of wardrobes and cabinets |
  | Clearances | minimum and comfort widths between pairs of elements |
  | Routes | every use zone reachable from the entrance with a continuous 60 cm (5 cm grid) |
  | Light and air | windows >= 1/8 of the floor, bathroom ventilation, room crowding |
  | Brief constraints | e.g. TV not next to a window on the same wall |
  | Ergonomics | seat height matching the surface |
  | Assembly | tall wardrobes can be tilted up in the room |
  | Geometry | no object intersecting another or a wall |

- **Delivery**: 2D plan DWG with dimensions, layers and areas; 3D DWG that also opens in AutoCAD LT and Mac; STEP solids;
  PNG preview; `verification_report.md` with checks, rooms, rough openings and furniture schedule.

## Requirements

| Component | Version / notes |
|---|---|
| macOS | project paths are for macOS |
| [FreeCAD](https://www.freecad.org) | 1.1 (tested with 1.1.4) |
| **FreeCAD MCP** addon | from [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp), folder `addon/FreeCADMCP` |
| An agent with MCP and Agent Skills support | Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode; with the `freecad` MCP server registered |
| [uv](https://docs.astral.sh/uv/) | runs the MCP server (`uvx`) and the `ezdxf` scripts |
| [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter) | free, in `/Applications`: DWG <-> DXF conversion |

## Installation

1. **FreeCAD**: `brew install --cask freecad` (or from the website).
2. **MCP addon** inside FreeCAD:
   ```bash
   git clone --depth 1 https://github.com/neka-nat/freecad-mcp.git /tmp/freecad-mcp
   mkdir -p ~/Library/Application\ Support/FreeCAD/v1-1/Mod/
   cp -r /tmp/freecad-mcp/addon/FreeCADMCP ~/Library/Application\ Support/FreeCAD/v1-1/Mod/
   ```
   Restart FreeCAD. To update the addon later, repeat the copy from a fresh clone.
3. **MCP server** in the agent you use (once). The command is always `uvx freecad-mcp`:
   - Claude Code: `claude mcp add --scope user freecad -- uvx freecad-mcp`
   - Codex: in `~/.codex/config.toml`
     ```toml
     [mcp_servers.freecad]
     command = "uvx"
     args = ["freecad-mcp"]
     ```
   - Cursor (`.cursor/mcp.json`), Gemini CLI (`~/.gemini/settings.json`):
     ```json
     { "mcpServers": { "freecad": { "command": "uvx", "args": ["freecad-mcp"] } } }
     ```
   - Others (Copilot, OpenCode): the same command/arguments pair in their MCP configuration file.
4. **ODA File Converter**: download the `.dmg` for your processor from the page above and drag the app into
   `/Applications`. It is needed to produce and read DWG files.
5. Optionally, set the converter path in FreeCAD (Preferences, or from the Python console) to open/save DWG from the
   FreeCAD GUI too: `/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter`.

## Starting a session

1. Open FreeCAD, choose the **MCP Addon** workbench (*View -> Workbench*) and click **Start RPC Server**.
   The Report view shows `RPC Server started at 127.0.0.1:9875`.
2. Open the agent **in this folder**. Instructions are in `AGENTS.md` (Claude Code reaches it through `CLAUDE.md`,
   Gemini CLI through `GEMINI.md`); skills are in `.agents/skills/`, with `.claude/skills` as a link for Claude Code.
3. Ask for what you need, or call a skill by name (`/name` in Claude Code, `$name` in Codex):

| Skill | When |
|---|---|
| `project-onboarding` | new project: initial questions, brief, survey of the starting plan |
| `furnishing` | lay out and furnish, until the checks are at zero |
| `review-layout` | judge a plan, a DWG, a photo or a sketch, without changing anything |
| `export-autocad` | produce 2D/3D DWG, STEP and report |

Skills also trigger on their own when the request matches ("start from this plan", "what do you think?",
"send me the DWGs").

## How it works

```
brief.md ──> project.py ──(MCP execute_code)──> FreeCAD: 3D model
                 │                                   │
                 │                      lib/interiors.py verify()
                 │                                   │
                 │                   output/verification_report.md
                 │                                   │
                 └──── interiors.export() ──> output/*.FCStd, *.step + build/ (plan, meshes, annotations)
                                                     │
                                  tools/export.sh ──> output/*_Plan.dwg, *_3D.dwg, *_Plan.png
                                                      (ODA File Converter + ezdxf, with round-trip check)
```

- The **model lives in the script** `projects/<name>/project.py`: every change is made there and rerun; the `.FCStd` is an
  output, not the source.
- `lib/interiors.py` is the shared engine: primitives, doors, windows, sliding doors, use registration
  (`chair`, `access_zone`, `destination`, `clearance`, `tv`, ...), checks and export.
- Thresholds live in `docs/design-rules.md` (minimum / comfort / source) and in the engine's `RULES` dictionary.

### Manual commands

Run a project (from the MCP `execute_code` tool, or FreeCAD's Python console):

```python
P = "/Users/andrea/dev/tmp/freecad/projects/apartment-100sqm/project.py"
exec(open(P).read(), {"__file__": P, "__name__": "__main__"})
```

Export:

```python
import interiors; interiors.export()          # in FreeCAD, after running the project
```
```bash
tools/export.sh projects/apartment-100sqm     # in the terminal: ends with "round-trip OK"
```

Read a starting plan:

```bash
uv run --with ezdxf python tools/read_plan.py projects/<name>/input/plan.dwg
```

## Structure

```
AGENTS.md                  instructions for the agent
CLAUDE.md / GEMINI.md      point to AGENTS.md (Claude Code, Gemini CLI)
README.md                  this file
lib/interiors.py           engine: model, checks, export
tools/                     read_plan.py, export.sh, annotate_plan.py, export_3d_dwg.py
docs/
  method.md                priorities, phases, per-room checks, scenarios, antipatterns, delivery format
  design-rules.md          thresholds
  brief-template.md        brief to fill in
  lessons.md               lessons learned (L01, L02, ...)
projects/
  _template/project.py     skeleton for a new project
  apartment-100sqm/        complete example
    brief.md, project.py
    input/                 client files            (excluded from git)
    output/                generated files         (excluded from git)
archive/                   previous (Italian) versions, read-only
.agents/skills/            project-onboarding, furnishing, review-layout, export-autocad (Agent Skills standard)
.claude/skills             link to .agents/skills (Claude Code)
```

## Opening the results in AutoCAD

| File | AutoCAD Windows | AutoCAD Mac | AutoCAD LT |
|---|---|---|---|
| `*_Plan.dwg` (2D, dimensions, layers) | Open | Open | Open |
| `*_3D.dwg` (coloured meshes, one layer per room) | Open | Open | Open (viewing) |
| `*_3D.step` (editable solids) | `IMPORT` | not supported | not supported |

DWG files are AutoCAD 2018 format, units in millimetres.

## Limits

- **Geometric and functional** checks: building services, structure, local regulations, acoustics and lighting are not
  modelled and appear in the report as NOT VERIFIABLE.
- Furniture are **indicative footprints**: on a real project replace them with the dimensions from product data sheets.
- Dimensions are only as good as their source: photos or unscaled plans give layouts only, declared as estimated.
- Absolute paths (`/Users/andrea/dev/tmp/freecad/...`) in the examples must be adapted if the folder is moved.
- On Windows, git recreates the `.claude/skills` symlink only with `core.symlinks` enabled.

## References

- Method: base residential design prompt (Astra) and phased workflow of
  [interioragent](https://github.com/KunalMGupta/interioragent), merged into `docs/method.md`.
- FreeCAD <-> MCP bridge: [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp).
- Agent Skills standard: [agentskills.io](https://agentskills.io/specification).
- License: MIT, see `LICENSE`.
