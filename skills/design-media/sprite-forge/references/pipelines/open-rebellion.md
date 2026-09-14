# Open Rebellion profile (pointer)

The Star Wars Rebellion reimplementation keeps its sprite pipeline in the repository, not in this skill: profile `scripts/sprites/rebellion.pipeline.json`, decoders `scripts/sprites/tactical3d.py` and `scripts/sprites/type302.py`, Blender renderer `scripts/sprites/render_original_meshes.py`, fighter texture export `scripts/sprites/export_fighter_textures.py`, and the guide `agent_docs/sprites.md` under `/Users/tomdimino/Desktop/Programming/open-rebellion`. Read that guide before touching any of it: it states which outputs are `faithful-hd` candidates (advisor droid deterministic family transform via `faithful_hd_pipeline.py --kind advisor`) and which are `experimental-remaster` review artifacts (direction sheets rendered from the original 87 meshes, native fighter texture references). Run a track with:

```bash
cd /Users/tomdimino/Desktop/Programming/open-rebellion
python3 ~/.claude/skills/sprite-forge/scripts/run_pipeline.py scripts/sprites/rebellion.pipeline.json --dry-run
python3 ~/.claude/skills/sprite-forge/scripts/run_pipeline.py scripts/sprites/rebellion.pipeline.json --stage render-meshes
```

Generic parts this profile relies on: `pixel_scale.py --family` (Scale2x in palette-index space, family sha256), `stitch_spritesheet.py --atlas v2 --directions 8`, `run_pipeline.py` run manifests. Nothing generative is used on parity-relevant assets.
