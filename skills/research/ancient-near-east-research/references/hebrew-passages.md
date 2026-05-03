# Key Hebrew Bible Passages for ANE Comparative Research

This reference documents essential Hebrew Bible passages and their connections to Ancient Near Eastern texts.

## Primary Comparative Passages

| Topic | Reference | Hebrew Term | Connection |
|-------|-----------|-------------|------------|
| Primordial Waters | Genesis 1:2 | תְּהוֹם (tehom) | Babylonian Tiamat |
| Spirit over Waters | Genesis 1:2 | רוּחַ אֱלֹהִים | Targum: רחם (rachem) |
| Asherah Poles | 1 Kings 18:19 | אֲשֵׁרָה | Ugaritic Athirat |
| Sea Monster | Isaiah 27:1 | לִוְיָתָן | Ugaritic Lotan (*ltn*) |
| Deep/Abyss | Psalm 104:6 | תְּהוֹם | Cosmic waters |
| Heavenly Host | 1 Kings 22:19 | צְבָא הַשָּׁמַיִם | Divine council |
| Earth as Footstool | Isaiah 66:1 | הֲדֹם | Ugaritic *hdm id* |
| Caphtor Origin | Amos 9:7 | כַּפְתּוֹר | Crete (Kaptaru) |
| Sea Monsters | Genesis 1:21 | תַּנִּינִים | Ugaritic *tnn* |

## Genesis 1:2 - The Central Text

```
וְהָאָ֗רֶץ הָיְתָ֥ה תֹ֙הוּ֙ וָבֹ֔הוּ וְחֹ֖שֶׁךְ עַל־פְּנֵ֣י תְה֑וֹם וְר֣וּחַ אֱלֹהִ֔ים מְרַחֶ֖פֶת עַל־פְּנֵ֥י הַמָּֽיִם׃
```

**Literal translation:**
"And the earth was *tohu va-vohu*, and darkness upon the face of *Tehom*, and *Ruach Elohim* hovering upon the face of the waters."

**Key Terms:**
- **תֹ֙הוּ֙ וָבֹ֔הוּ** (tohu va-vohu) — "formless and void" / primordial chaos
- **תְּהוֹם** (tehom) — the deep, cognate with Akkadian *Tiamat*
- **רוּחַ אֱלֹהִים** (ruach elohim) — spirit/wind of Elohim

## Commentaries Available via Sefaria

- **Rashi** — Medieval French exegete (פשט/peshat focus)
- **Ibn Ezra** — Spanish grammarian, rationalist
- **Ramban** — Nachmanides, Kabbalistic interpretation
- **Targum Onkelos** — Babylonian Aramaic translation
- **Targum Neofiti** — Palestinian Aramaic (important for רחם references)
- **Midrash Rabbah** — Aggadic interpretations

## Fetch Commands

```bash
# Genesis 1:2 with Hebrew and translation
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_sefaria.py "Genesis 1:2"

# With Rashi commentary
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_sefaria.py "Genesis 1:2" --with-rashi

# Hebrew only
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_sefaria.py "Genesis 1:2" --hebrew-only

# Search for Tehom references
curl -s "https://www.sefaria.org/api/search-wrapper?query=תהום&type=text&filters=Tanakh"
```

## Leviathan / Lotan Parallels

### Isaiah 27:1
```
בַּיּ֣וֹם הַה֡וּא יִפְקֹ֣ד יְהוָה֩ בְּחַרְבּ֨וֹ הַקָּשָׁ֜ה וְהַגְּדוֹלָ֣ה וְהַֽחֲזָקָ֗ה
עַ֤ל לִוְיָתָן֙ נָחָ֣שׁ בָּרִ֔חַ וְעַל֙ לִוְיָתָ֔ן נָחָ֖שׁ עֲקַלָּת֑וֹן
וְהָרַ֥ג אֶת־הַתַּנִּ֖ין אֲשֶׁ֥ר בַּיָּֽם׃
```

**Translation:** "On that day YHWH will punish with his sword... Leviathan the fleeing serpent, Leviathan the twisting serpent; and he will slay the Tannin that is in the sea."

**Ugaritic Parallel (KTU 1.5:I:1-3):**
```
ltn bṯn brḥ
tšly bṯn ʿqltn
šlyṭ d šbʿt rašm
```
"Lotan the fleeing serpent, you struck the twisting serpent, the potentate with seven heads"

## Athirat/Asherah References

| Hebrew | Reference | Context |
|--------|-----------|---------|
| אֲשֵׁרָה | 1 Kings 18:19 | 400 prophets of Asherah |
| אֲשֵׁרִים | 2 Kings 23:14 | Asherah poles destroyed |
| אֲשֵׁרָה | 2 Kings 21:7 | Asherah image in Temple |

**Ugaritic:** *ʾaṯrt* / *ʾaṯrt ym* — "Athirat of the Sea"
- Consort of El in the Ugaritic pantheon
- "She who walks on the Sea" (*rbt ʾaṯrt ym*)

## Caphtor (Kaphtor) References

| Reference | Hebrew | Context |
|-----------|--------|---------|
| Amos 9:7 | כַּפְתּוֹר | Philistine origin from Caphtor |
| Jeremiah 47:4 | כַּפְתּוֹר | "island of Caphtor" |
| Deuteronomy 2:23 | כַּפְתֹּרִים | Caphtorim people |
| Genesis 10:14 | כַּפְתֹּרִים | Table of Nations |

**Identification:** Caphtor = Crete (Kaptaru in Akkadian, *kftw* in Egyptian)

## Isaiah 66:1 - Earth as Footstool

```
כֹּ֚ה אָמַ֣ר יְהוָ֔ה הַשָּׁמַ֣יִם כִּסְאִ֔י וְהָאָ֖רֶץ הֲדֹ֣ם רַגְלָ֑י
```

**Key Term:** הֲדֹם (*hadom*) — footstool
- Ugaritic cognate: *hdm* in KTU 51:1:35
- Kothar-wa-Khasis fashions *hdm id* — "footstool of Ida" (Mount Ida, Crete)
- Egyptian loanword: *hdmw* (Caphtorian origin per Gordon)

**Significance:** "Earth as divine footstool" motif connects Biblical cosmology to Minoan sacred geography.
