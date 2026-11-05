# Blender MCP servers, other tools, and the research behind this skill

Surveyed 2026-11-05 (Exa, Firecrawl, GitHub API). This skill runs headless scripts. An MCP server is optional, for
looking at a scene live.

## Why headless scripts

- **Reproducible:** each operation is a versioned script with its arguments, and `--factory-startup` ignores the
  user's preferences and add-ons.
- **Local:** nothing is uploaded, and no server is left listening.
- **Checkable:** every script writes a JSON report and renders, which the agent reads before it calls the work done.

## Options

| Option | What it is | Status (2026-11-05) | Licence | Use it for / risks |
|---|---|---|---|---|
| Headless `blender -b --factory-startup --python s.py -- args` | Full `bpy`, Cycles/EEVEE, baking, glTF | Ships with Blender (5.2.3 LTS here) | GPL (app) | **Default.** |
| **Blender Lab MCP** (official, projects.blender.org/lab/blender_mcp), the server behind Claude's Blender connector (2026-04-28) | 27 tools: `execute_blender_code`, `execute_blender_code_for_cli` (headless), scene and file reports, viewport and thumbnail renders, `search_api_docs`, `search_manual_docs` (offline) | v1.0.3 2026-09-11 | GPL-3.0+ | Live inspection, API look-ups. Needs Blender ≥ 5.1. Runs model-written code without guards (its page recommends a VM). No telemetry documented (unverified). |
| **MCP for Blender** (ahujasid/blender-mcp, PyPI `mcp-for-blender`) | Socket add-on, `execute_blender_code`, screenshots, Poly Haven / Sketchfab / Poly Pizza import, `generate_3d` through Meshy, Tripo, Rodin or Hunyuan3D | 33.4k★, v2.2.7, pushed 2026-11-04 | MIT | Sends an anonymous usage record by default (install id, tool names, OS, versions); prompts, code and screenshots only on opt-in. `DISABLE_TELEMETRY=true` turns all of it off. Arbitrary Python unless `BLENDER_MCP_SAFE_MODE=1`. Generation and import upload to third parties. **Never open licence-restricted scans in a session using it.** |
| `bpy` from pip (5.2.3) | Blender as a Python module | Official | GPL-3.0 | Needs exactly Python 3.13; large. Headless Blender does the same. |
| TMHSDigital/Blender-Developer-Tools | 26 Claude Code skills of tested bpy for 5.2/4.5 | 19★, 2026-11-03 | CC BY-NC-ND with MIT snippets, per its README (check before reusing) | Read for patterns; don't install wholesale. |
| PyMeshLab, Open3D, trimesh | Decimation keeping UVs, Poisson, hole filling, checks | Mature | GPL-3 / MIT / MIT | Scan cleanup without Blender, fully local. |
| gltf-transform CLI | `inspect`, `optimize`, Meshopt/Draco, WebP/KTX2 textures | 4.5.1 | MIT | Shrinking GLBs for the web. |
| TRELLIS.2, Hunyuan3D, Meshy, Rodin | Image/text → textured mesh | Active | MIT / Tencent / commercial | Rough new shapes only. TRELLIS needs CUDA (Mac ports unverified); the rest are uploads. Use the `meshy` skill for Meshy. |

### Installing the official MCP server (not done here)

Install its add-on from projects.blender.org/lab/blender_mcp into Blender 5.1+, start it from the add-on panel,
then register the MCP server in Claude Code as the project's README says. Keep scans out of any session where
model-written code runs live, or use `execute_blender_code_for_cli` on copies.

## What the research says works

- **Run, read the error, retry.** 3DCodeBench (DeepMind, 2026-05-31, arxiv.org/html/2606.01057v1): executable
  Blender scripts rose from 0.702 single-turn to 0.974 multi-turn. Most failures were API mismatches. Most working
  renders that went wrong did so through disconnected or floating parts. The `loose_parts` and
  `non_manifold_edges` fields in each report catch these.
- **More views help.** 3DHarnessBench (arxiv.org/abs/2609.06535, 2026-09-06): every model improved going from one
  view, to several, to choosing its own viewpoints, to full 3D access through Blender MCP. Hence the 4-view
  `contact.png`.
- **Fine spatial coherence is still the weak point.** BlenderWorld (arxiv.org/abs/2610.23986, 2026-10-14): 223
  tasks with multi-view rubric scoring. Always look at the renders, and check sizes against the report.
- **A verifier beats a bigger generator.** BlenderGym (CVPR 2025, arxiv.org/abs/2504.01786). See also LL3M
  (arxiv.org/abs/2508.08228: Blender doc retrieval plus a visual critic), BlenderAlchemy (arxiv.org/abs/2404.17672)
  and SceneCraft (arxiv.org/abs/2403.01248).
- **Scans can become editable code** (MeshCoder, arxiv.org/abs/2508.14879; CAD-Recode, arxiv.org/abs/2412.14042).
  These are research models, not tools.
