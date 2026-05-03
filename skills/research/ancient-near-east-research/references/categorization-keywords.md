# Categorization Keywords for ANE Research

This document defines the keyword sets used to auto-categorize quotations into five themes. The `compile_quotations.py` script uses these keywords for content-based classification.

## Theme Categories

### 1. Thera (Volcanic/Aegean Context)

The Theran eruption (~1628 BCE) and its Mediterranean impact.

**Keywords:**
- `thera`, `akrotiri`, `santorini`
- `volcanic`, `eruption`, `tephra`, `pumice`
- `tempest stela`, `ahmose`
- `aegean`, `cyclades`, `cycladic`
- `bronze age collapse`
- `minoan eruption`
- `calliste` (ancient name for Thera)

**Related Scholars:** Marinatos, Friedrich, Manning

---

### 2. Knossos (Minoan Archaeology)

Palace culture, religious practices, and Linear A/B contexts.

**Keywords:**
- `knossos`, `labyrinth`, `palace`
- `minoan`, `crete`, `cretan`
- `evans`, `arthur evans`
- `linear a`, `linear b`
- `mycenaean`
- `lustral basin`
- `fresco`, `throne room`
- `bull leaping`, `bull leap`
- `snake goddess`, `priestess`
- `peak sanctuary`
- `horns of consecration`

**Related Scholars:** Evans, Marinatos, Castleden

---

### 3. Minos (Mythological/Greek Sources)

Greek mythology and its possible Near Eastern substrates.

**Keywords:**
- `minos`, `king minos`
- `minotaur`, `asterion`
- `daedalus`, `icarus`
- `ariadne`, `theseus`
- `thalassocracy`
- `zeus`, `europa`, `pasiphae`
- `cretan`, `dictaean`
- `dikta`, `dikte`, `dictaean cave`
- `kadmos`, `cadmus`
- `membliaros`
- `euphemos`
- `bezalel`, `moses` (Moses-Minos parallel)

**Related Scholars:** Astour, Gordon, Faure

---

### 4. Palestine (Biblical/Canaanite Context)

Hebrew Bible, Ugaritic texts, and Levantine connections.

**Keywords:**
- `palestine`, `israel`, `judah`, `jerusalem`
- `biblical`, `hebrew`, `aramaic`
- `canaanite`, `canaan`
- `philistine`, `gaza`
- `asherah`, `athirat`, `yahweh`
- `temple`, `solomon`, `david`
- `deuteronomy`, `chronicles`, `isaiah`, `psalms`
- `targum`, `talmud`, `midrash`
- `ugarit`, `ugaritic`, `ras shamra`
- `syria`, `lebanon`, `phoenician`, `phoenicia`
- `genesis`, `exodus`
- `tehom`, `tiamat`
- `leviathan`, `lotan`
- `gnostic`, `sethian`, `orphic`
- `nag hammadi`

**Related Scholars:** Cross, Smith, Wyatt, Day

---

### 5. Linguistics (Etymology/Semitic Analysis)

Comparative linguistics, etymology, and cognate analysis.

**Keywords:**
- `etymology`, `etymological`
- `linguistic`, `linguistics`
- `semitic`, `west semitic`
- `indo-european`
- `phonetic`, `phonology`, `phonological`
- `morphology`, `morphological`
- `cognate`, `cognates`
- `root`, `triliteral`
- `prefix`, `suffix`
- `comparative`, `comparison`
- `historical linguistics`
- `semantic`, `lexical`, `lexicon`
- `grammatical`, `syntax`
- `phoneme`, `consonant`, `vowel`
- `derivation`, `derived`
- `borrowing`, `loanword`
- `astour` (Michael Astour)
- `gordon` (Cyrus Gordon)
- `begadkephat`
- `tip'eret`, `tip'art`
- `purpura`, `purple`
- `kaphtor`, `caphtor`
- `p-r root`

**Related Scholars:** Astour, Gordon, Rendsburg, Hoch

---

## Usage

### Manual Categorization

Add a category tag to quotation markdown files:

```markdown
# Quotation Title

**Category:** Linguistics

> "The etymology of tip'eret shows clear connection to the p-r root..."
> — Astour, *Hellenosemitica*, p. 142
```

### Auto-Categorization

The `compile_quotations.py` script scans content for keywords and assigns the category with the highest match count:

```python
def categorize_by_content(title: str, content: str) -> str:
    search_text = (title + " " + content).lower()
    scores = {}
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in search_text)
        if score > 0:
            scores[theme] = score
    return max(scores, key=lambda x: scores[x]) if scores else "Uncategorized"
```

### Overlapping Categories

When content spans multiple themes, the algorithm assigns the theme with the most keyword matches. However, you can override by adding an explicit `**Category:**` tag.

**Example:** A quotation about "Tehom and Tiamat" might match both Palestine (tehom, tiamat) and Linguistics (etymology, cognate). The explicit tag takes precedence.

---

## Adding New Keywords

When encountering new relevant terms:

1. Identify the appropriate theme
2. Add the keyword to `compile_quotations.py`
3. Update this reference document
4. Re-run compilation to recategorize

---

## Cross-Theme Connections

The paper's central thesis involves cross-theme connections:

| Connection | Themes |
|------------|--------|
| Tehom ↔ Tiamat | Palestine + Linguistics |
| Membliaros etymology | Minos + Linguistics |
| Moses ↔ Minos parallel | Minos + Palestine |
| Thera eruption impact | Thera + Palestine (Tempest Stela) |
| Kaphtor = Crete | Knossos + Linguistics + Palestine |
| Purple dye trade | Knossos + Palestine + Linguistics |

These connections are the scholarly core of the 3-part paper series.
