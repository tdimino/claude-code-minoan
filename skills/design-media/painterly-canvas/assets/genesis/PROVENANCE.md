# Provenance

`endless-painted-world.html` is the work this skill was distilled from. It is unlicensed, so it is gitignored and not distributed with the skill: fetch it locally with the command below and keep it byte-for-byte as downloaded.

| Field | Value |
|---|---|
| Title | Endless Painted World — Living Impressions |
| Author | George Kenwright ([@GeokenAI](https://x.com/GeokenAI)), creative producer, Google DeepMind, London |
| Made with | Gemini 4 Neon, per the author's announcement of 2026-11-18 |
| Source | https://endless-painted-world.georgekenwright.workers.dev/ |
| Retrieved | 2026-11-20 |
| Size | 470,412 bytes, 7,397 lines |
| SHA-256 | `aae6d84e5fea0b058bb569e5283afee3928d7a95c180bbcd38ceebde22586a3d` |

## Rights

The file itself contains no license, copyright line or author credit; its canonical and Open Graph URLs are unfilled placeholders (`YOUR_DOMAIN_HERE`). Authorship is established by the hosting subdomain and by George Kenwright's own announcement of the piece on X. No license means no grant of reuse: treat the file as a study reference, credit him wherever work derived from it appears, and ask him before redistributing it or shipping code copied from it.

The references and `SKILL.md` are prose written for this skill from a reading of the file. `painterly-starter.html` is a simplified reimplementation of the same method: its brushstroke function is modeled closely on the genesis's `paintedStroke`, so treat the starter as derived from George Kenwright's work and credit him wherever it is used.

## Fetch

When the file is absent, download it and verify it before reading:

```bash
curl -fsSL https://endless-painted-world.georgekenwright.workers.dev/ -o assets/genesis/endless-painted-world.html
echo "aae6d84e5fea0b058bb569e5283afee3928d7a95c180bbcd38ceebde22586a3d  assets/genesis/endless-painted-world.html" | shasum -a 256 -c
```

A checksum mismatch means the author has changed the page, and every line number in `references/` is then unreliable. Regenerate the index with the grep at the foot of `references/genesis-map.md` before using it.

## Use

- Open it in a browser to see the target quality.
- Read sections by line range using `references/genesis-map.md`.
- Do not edit it. Line numbers throughout the references depend on this exact copy.
- A modified copy (the skill's `extend` mode) is a derivative of an unlicensed work: fine for private study, and not to be published without the author's permission.
