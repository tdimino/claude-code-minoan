# Script Iconography Assets

Acquired 2026-05-06/07 for the orthogonic lineage research synthesis and potential HTML visualization of five Bronze Age script families.

## Fonts

| File | Script | Glyphs | Unicode Block | License | Source |
|------|--------|--------|---------------|---------|--------|
| `fonts/NotoSansLinearA-Regular.ttf` | Linear A | 345 | U+10600–U+1077F | OFL 1.1 | [google/fonts](https://github.com/google/fonts/tree/main/ofl/notosanslineara) |
| `fonts/NotoSansLinearB-Regular.ttf` | Linear B | — | U+10000–U+100FF | OFL 1.1 | [google/fonts](https://github.com/google/fonts/tree/main/ofl/notosanslinearb) |
| `fonts/NotoSansCyproMinoan-Regular.ttf` | Cypro-Minoan | 104 | U+12F90–U+12FFF | OFL 1.1 | [google/fonts](https://github.com/google/fonts/tree/main/ofl/notosanscyprominoan) |
| `fonts/CretanHieroglyphs.ttf` | Cretan Hieroglyphic | ~128 | PUA (0xF2000) | Freeware ("free for any use") | [Font Library](https://fontlibrary.org/en/font/cretan-hieroglyphs) — George Douros |
| `fonts/VincaGimbutas.ttf` | Vinča/Old European | ~242 types | Custom encoding | Freeware | [Omniglot](https://www.omniglot.com/writing/vinca.htm) — Sorin Paliga, named after Marija Gimbutas |

## Images by Script Family

### Linear A (`linear-a/`)

| Asset | Description | Source |
|-------|-------------|--------|
| `sigla-sign-map.json` | 334 signs mapped: AB number → tablet PNG URL → Unicode codepoint | Scraped from [SigLA](https://sigla.phis.me/sign-list.html) |
| `signs/` (20 PNGs) | Photographic crops from actual tablets for key signs (AB23/mu, AB31/sa, AB08/a, AB57/ja, AB80/ma, AB28/i, AB06/na, AB41/si, AB04/te, AB77/ka, AB100/VIR, plus libation formula signs) | SigLA — open access |

SigLA URL pattern: `https://sigla.phis.me/document/{TABLET}/{TABLET}_{INDEX}.png`

### Proto-Sinaitic (`proto-sinaitic/`)

| Asset | Description | Source |
|-------|-------------|--------|
| 11 SVG files | Proto-Semitic letter sign forms (aleph through taw) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:Serabit_el-Khadim_proto-Sinaitic_inscriptions) — public domain |

File naming: `proto-semiticX-01.svg` where X = letter initial.

### Cypro-Minoan (`cypro-minoan/`)

| Asset | Description | Source |
|-------|-------------|--------|
| `Louvre-AM2336-CM2-tablet.jpg` | Louvre tablet AM 2336, CM 2 script, 1280×1946 JPEG | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Tablet_cypro-minoan_2_Louvre_AM2336.jpg) — public domain |
| `cypro-minoan-unicode-chart.pdf` | Unicode 17.0 chart U+12F90–12FFF, 104 signs | [unicode.org](https://www.unicode.org/charts/PDF/U12F90.pdf) |

### Vinča / Old European (`vincha/`)

| Asset | Description | Source |
|-------|-------------|--------|
| `Dispilio-tablet.png` | Wooden tablet, Lake Kastoria, Greece, c. 5260 BCE, 266×240 PNG | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Dispilio_tablet_text.png) — CC-licensed |
| `vinca-oldest-symbols.gif` | Oldest Vinča symbols chart | [Omniglot](https://www.omniglot.com/writing/vinca.htm) |
| `vinca-common-symbols.gif` | Common Vinča symbols chart | [Omniglot](https://www.omniglot.com/writing/vinca.htm) |
| `vinca-sign-chart.gif` | Three-period Vinča sign chart | [Omniglot](https://www.omniglot.com/writing/vinca.htm) |

### Cretan Hieroglyphic (`cretan-hieroglyphic/`)

| Asset | Description | Source |
|-------|-------------|--------|
| `CretanHieroglyphs-guide.pdf` | 24-page sign guide bundled with Douros font | George Douros, Font Library |
| `Ferrara-CH-Sign-Repertoires-2024.pdf` | 18 pages, Cambridge UP, open-access CC-BY-NC-ND | [CRIS Unibo](https://cris.unibo.it/handle/11585/991456) |
| `Anastasiadou-Seals-2016.pdf` | Seal photographs in context, Protopalatial Crete | [Aegeus Society](https://www.aegeussociety.org/) — open access |

## Academic PDFs (`~/Desktop/Thera-Knossos-Minos-Paper/sources/`)

| File | Size | Description |
|------|------|-------------|
| `Albright-Proto-Sinaitic-1969.pdf` | 19.5 MB | Foundational decipherment, sign plates. Internet Archive, public domain. |
| `Ferrara-Montecchi-Valerio-CH-LA-2022.pdf` | 1.8 MB | CH↔LA palaeographic comparison (*Pasiphae* XVI). Key paper for sign evolution mapping. |
| `Palmer-Aegean-Glyptic-2014.pdf` | 4.7 MB | PhD thesis, Birmingham. Aegean religious glyptic motifs. Open access. |
| `Ferrara-CH-Sign-Repertoires-2024.pdf` | 902 KB | CH sign inventory state-of-the-art. Cambridge UP, CC-BY-NC-ND. |
| `Valerio-Cypro-Minoan-2018.pdf` | 16.3 MB | PhD thesis, ~385 pages. Definitive CM sign catalog with LA↔CM↔Cypro-Greek tables. Open access. |
| `Anastasiadou-Seals-Script-2016.pdf` | 3.4 MB | Seals, script, regionalism in Protopalatial Crete. Aegeus Society, open access. |
| `Simons-Proto-Sinaitic-2011.pdf` | 958 KB | Proto-Sinaitic as alphabet progenitor. *Rosetta* 9, Birmingham. |
| `Winn-Danube-Script-2008.pdf` | 523 KB | Vinča signs: 242 types, 15 categories, ritual use. *J. Archaeomythology* 4. |

## Cross-Script Sign Evolution Map

`sign-evolution-map.json` — 20 key signs traced across CH → LA → LB, with Proto-Sinaitic cognates where attested. Each entry records:

- CH sign number, pictographic ancestor, Douros PUA codepoint
- LA AB number, phonetic value, Unicode codepoint, SigLA tablet image URL
- LB sign number, phonetic value
- Proto-Sinaitic letter and SVG file (9 of 20 signs)
- Semantic/cultic significance and NWS connections
- Graphic development tendencies (Ferrara's a–g typology)

Coverage: 9 signs span 4 scripts, 11 span 3. Confidence: 17 HIGH, 3 MEDIUM. Phonetic categories: 4 vowels, 3 dentals, 3 nasals, 5 sibilants, 2 semivowels, 2 liquids, 1 velar.

Source: Ferrara-Montecchi-Valério 2022 Appendix 1 (CH↔LA), Steele & Meissner 2017 (LA↔LB), Albright 1969 / Simons 2011 (Proto-Sinaitic).

## Build Script

`~/Desktop/Programming/scripts/sigla_build.py` — regenerates `sigla-sign-map.json` and downloads sign images from SigLA.

## HTML Visualization Notes

Three rendering tiers:
1. **Unicode-native** (browser fonts via Google Fonts CDN): Linear A, Linear B, Cypro-Minoan
2. **PUA font-based** (self-hosted TTF): Cretan Hieroglyphic (Douros), Vinča (Paliga/Gimbutas)
3. **Image-based** (SVG/PNG): Proto-Sinaitic (Wikimedia SVGs), SigLA tablet crops (all LA signs)

No existing tool shows a three-way CH↔LA↔LB sign evolution chart — that's the research gap this visualization fills.
