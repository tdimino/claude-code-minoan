# Cuneiform Database Resources

This reference documents access methods for CDLI and ORACC cuneiform databases.

## CDLI - Cuneiform Digital Library Initiative

**URL:** https://cdli.earth

The CDLI provides access to over 500,000 cuneiform texts from Mesopotamia. Primary resource for Sumerian and Akkadian inscriptions.

### Verified API Endpoints

```bash
# Artifact metadata + ATF transliteration (VERIFIED WORKING)
curl -s "https://cdli.earth/artifacts/P480701.json"
# Returns JSON with: id, designation, inscription.atf (full ATF text)

# Key P-numbers for ANE research:
# P480701 = Enuma Elish composite (full 7-tablet text)
# P369757 = Gilgamesh Epic excerpts
# P273880 = Atrahasis flood narrative
```

### Search Methods

- Text search: https://cdli.earth/search (web interface only)
- Browse by period, genre, or provenance
- Programmatic access: Use P-numbers directly with JSON API

### Key Collections

- Royal inscriptions
- Administrative texts
- Literary texts (myths, hymns)
- Lexical lists

---

## ORACC - Open Richly Annotated Cuneiform Corpus

**URL:** https://oracc.museum.upenn.edu

Curated scholarly editions of cuneiform texts with linguistic annotation.

### Verified API Endpoints

```bash
# Project list (VERIFIED WORKING)
curl -s "https://oracc.museum.upenn.edu/projectlist.json"

# Text edition from project
curl -s "https://oracc.museum.upenn.edu/{project}/corpusjson/{P-number}.json"

# Glossary
curl -s "https://oracc.museum.upenn.edu/{project}/glossary-{lang}.json"
# Languages: sux (Sumerian), akk (Akkadian)
```

### Key Sub-projects

| Project | Description |
|---------|-------------|
| **AMGG** | Ancient Mesopotamian Gods and Goddesses (deity information) |
| **ETCSL** | Electronic Text Corpus of Sumerian Literature |
| **SAAo** | State Archives of Assyria online |
| **RINAP** | Royal Inscriptions of the Neo-Assyrian Period |
| **CAMS** | Corpus of Ancient Mesopotamian Scholarship |

### Direct Access URLs

```
# Deity lookup (Tiamat, Marduk, etc.)
https://oracc.museum.upenn.edu/amgg/listofdeities/{deity-name}/

# Sumerian literary texts
https://oracc.museum.upenn.edu/etcsl/
```

---

## eTACT / ETANA

**URL:** https://etana.org

Electronic Tools and Ancient Near Eastern Archives - digitized publications and resources.

---

## Script Commands

### Fetch CDLI Artifact Metadata

```bash
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py cdli P123456
```

### Fetch Inscription Text (ATF Format)

```bash
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py cdli-inscription P123456
```

### List ORACC Projects

```bash
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py oracc-projects
```

### Fetch ORACC Text Edition

```bash
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py oracc-text rimanum P295625
```

### Fetch ORACC Glossary

```bash
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py oracc-glossary rimanum akk
```

### Look Up Deity in AMGG

```bash
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py deity tiamat
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py deity marduk
```

---

## ATF Format Overview

ATF (ASCII Transliteration Format) is the standard for representing cuneiform texts:

```
&P480701 = Enuma Elish
#atf: lang akk

@tablet
@obverse
1. e-nu-ma e-liš la na-bu-u2 šá-ma-mu
#tr.en: When on high, the heaven was not named
2. šap-liš am-ma-tum šu-ma la zak-rat
#tr.en: Below, the earth was not called by name
```

**Key:**
- `&P...` = P-number identifier
- `@tablet`, `@obverse`, `@reverse` = physical structure
- Lines numbered, transliteration in lowercase
- `#tr.en:` = English translation
