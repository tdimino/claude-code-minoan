# Key Akkadian Terms for ANE Research

This reference documents essential Akkadian terminology, Enuma Elish passages, and cognate relationships for comparative research.

## Core Akkadian Terms

| Akkadian | Transliteration | Meaning | Hebrew Cognate | Connection |
|----------|-----------------|---------|----------------|------------|
| 𒀭𒋾𒊩𒆳 | Ti-amat | Sea goddess | תְּהוֹם (Tehom) | Primordial waters |
| 𒌓𒈬𒄷𒁍𒌨 | um-mu hu-bur | Mother Hubur | — | Primordial womb |
| 𒉺𒋾𒃲𒆳𒆷𒈠 | pa-ti-qa-at ka-la-ma | Fashioner of all | — | Creation epithet |
| 𒀭𒀫𒌓 | Marduk | Storm god | — | Defeats Tiamat |
| 𒂍𒉡𒈠𒂊𒇺 | Enūma Eliš | "When on high" | — | Creation epic |
| 𒅗 | pû (KA) | mouth | פֶּה (peh) | Anatomical term |
| — | pi-i-ša | "her mouth" | — | Possessed form |
| — | mu-al-li-da-at | "she who bore" | — | Birth epithet |
| 𒀀𒀊𒍪 | apsu / apsû | fresh water abyss | — | Male primordial |
| 𒆠𒋾 | ki-ti | earth | — | Cosmological term |

## Enuma Elish Key Passages

### Tablet I, Line 4 — Tiamat as Universal Mother

```
mu-um-mu ti-amat mu-al-li-da-at gim-ri-šu₂-un
```
**Translation:** "And Mummu-Tiamat, she who bore them all"

**Analysis:**
- **mu-um-mu** — primordial form/chaos (sometimes a deity name)
- **ti-amat** — the sea goddess
- **mu-al-li-da-at** — feminine active participle "she who gives birth"
- **gim-ri-šu₂-un** — "all of them" (totality)

### Tablet I, Line 133 — Mother Hubur Epithet

```
um-ma hu-bur pa-ti-qat ka-la-mu
```
**Translation:** "Mother Hubur, she who fashions all things"

**Analysis:**
- **um-ma** — mother
- **hu-bur** — river of the underworld (also epithet of Tiamat)
- **pa-ti-qat** — feminine "fashioner, creator"
- **ka-la-mu** — "all, everything"

### Tablet IV, Lines 96-100 — Mouth of Tiamat

```
as Tiamat opened her mouth to its full extent (pi-i-ša)
He drove in the evil wind, while as yet she had not shut her lips
The terrible winds filled her belly
```

**Key Term:** Akkadian **pû** (𒅗) = "mouth"
- Possessed form: **pi-i-ša** = "her mouth"
- Connects to Sethian Gnostic **phikola** = "dark water" (Hippolytus)
- The "mouth" of Tiamat as origin point

## Tiamat Epithets

| Akkadian | Meaning | Significance |
|----------|---------|--------------|
| ti'āmat | "the sea" | Primary name |
| mummu ti'āmat | "chaos sea" | Primordial form |
| ummu hubur | "Mother Hubur" | Underworld river |
| mu-al-li-da-at gimri-šun | "she who bore them all" | Universal mother |
| pa-ti-qa-at ka-la-ma | "fashioner of all" | Demiurgic role |

## Hebrew-Akkadian Cognate Pairs

| Hebrew | Akkadian | Meaning | Notes |
|--------|----------|---------|-------|
| תְּהוֹם (tehom) | ti'āmat | primordial water | Primary cognate pair |
| לִוְיָתָן (livyatan) | — | sea monster | cf. Ugaritic *ltn* |
| פֶּה (peh) | pû | mouth | Common Semitic |
| שָׁמַיִם (shamayim) | šamû | heaven(s) | Dual form |
| אֶרֶץ (eretz) | erṣetu | earth | Common Semitic |
| רוּחַ (ruach) | — | spirit/wind | No direct cognate |

## Cosmogonic Pattern (Cross-Cultural)

The creation-from-watery-chaos pattern appears across:

### 1. Babylonian (Enuma Elish)
- Tiamat (salt water) + Apsu (fresh water)
- Marduk defeats Tiamat, splits body
- Creates heaven/earth from halves

### 2. Biblical Hebrew (Genesis 1)
- תְּהוֹם (Tehom) — primordial waters
- רוּחַ אֱלֹהִים מְרַחֶפֶת (Ruach Elohim merachefet) — spirit hovers
- Separation of waters above/below

### 3. Gnostic (On the Origin of the World)
- "limitless darkness and bottomless water"
- "a spirit moving to and fro upon the waters"
- Demiurge separates watery substance

### 4. Greek-Semitic (Astour's Analysis)
- Membliaros = מם־בלי־אר "waters without light"
- Euphemos walking on water = רוח אלהים מרחפת

## CDLI/ORACC Resources

### Enuma Elish Full Text
- **CDLI P480701** — Composite text of all 7 tablets
- Fetch: `curl -s "https://cdli.earth/artifacts/P480701.json"`

### AMGG Deity Lookups
- Tiamat: `https://oracc.museum.upenn.edu/amgg/listofdeities/tiamat/`
- Marduk: `https://oracc.museum.upenn.edu/amgg/listofdeities/marduk/`

### Key P-Numbers
| P-Number | Content |
|----------|---------|
| P480701 | Enuma Elish composite |
| P369757 | Gilgamesh Epic excerpts |
| P273880 | Atrahasis flood narrative |

## Script Fetch Commands

```bash
# Tiamat deity info
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py deity tiamat

# Enuma Elish text
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py cdli-inscription P480701

# ORACC glossary (Akkadian)
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py oracc-glossary cams akk
```
