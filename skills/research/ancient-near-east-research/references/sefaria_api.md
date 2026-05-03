# Sefaria API Reference

Complete reference for the Sefaria API used in Ancient Near East research.

## Base URL

```
https://www.sefaria.org/api/
```

No API key required. Rate limiting applies for heavy usage.

## Texts API (v3)

### Get Text

```
GET /api/v3/texts/{ref}
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ref` | string | Text reference (e.g., "Genesis.1.1-3") |
| `version` | string | `source` (Hebrew only), `all` (all versions) |
| `fill_in_missing_segments` | boolean | Include missing verses |

**Reference Format:**
- Simple: `Genesis.1.1`
- Range: `Genesis.1.1-3`
- Chapter: `Genesis.1`
- Cross-chapter: `Genesis.1.1-2.4`

**Example Request:**
```bash
curl -s "https://www.sefaria.org/api/v3/texts/Genesis.1.2"
```

**Example Response:**
```json
{
  "versions": [
    {
      "versionTitle": "Tanach with Ta'amei Hamikra",
      "language": "he",
      "text": "וְהָאָ֗רֶץ הָיְתָ֥ה תֹ֙הוּ֙ וָבֹ֔הוּ וְחֹ֖שֶׁךְ עַל־פְּנֵ֣י תְה֑וֹם וְר֣וּחַ אֱלֹהִ֔ים מְרַחֶ֖פֶת עַל־פְּנֵ֥י הַמָּֽיִם׃"
    },
    {
      "versionTitle": "The Koren Jerusalem Bible",
      "language": "en",
      "text": "Now the earth was unformed and void, and darkness was upon the face of the deep; and the spirit of God hovered over the face of the waters."
    }
  ],
  "ref": "Genesis 1:2",
  "heRef": "בראשית א׳:ב׳",
  "sectionRef": "Genesis 1",
  "indexTitle": "Genesis"
}
```

## Commentary API

### Get Commentary on a Verse

```
GET /api/v3/texts/{ref}?with=all
```

Or fetch specific commentary:
```
GET /api/v3/texts/Rashi_on_Genesis.1.2
```

**Available Commentaries (Hebrew Bible):**
- `Rashi_on_{Book}` - Rashi
- `Ibn_Ezra_on_{Book}` - Ibn Ezra
- `Ramban_on_{Book}` - Nachmanides
- `Targum_Onkelos_on_{Book}` - Aramaic translation
- `Targum_Neofiti` - Palestinian Targum (select books)

**Example:**
```bash
curl -s "https://www.sefaria.org/api/v3/texts/Rashi_on_Genesis.1.2"
```

## Search API

### Text Search

```
GET /api/search-wrapper?query={query}&type=text&filters={filters}
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Search term (supports Hebrew) |
| `type` | string | `text` or `sheet` |
| `filters` | string | Category filter (e.g., `Tanakh`, `Talmud`) |
| `size` | integer | Number of results (default 10) |

**Example - Search for תהום (Tehom):**
```bash
curl -s "https://www.sefaria.org/api/search-wrapper?query=תהום&type=text&filters=Tanakh&size=20"
```

## Links API

### Get Cross-References

```
GET /api/links/{ref}
```

Returns all texts that link to the given reference.

**Example:**
```bash
curl -s "https://www.sefaria.org/api/links/Genesis.1.2"
```

## Index API

### Get Book Information

```
GET /api/v2/index/{book}
```

**Example:**
```bash
curl -s "https://www.sefaria.org/api/v2/index/Genesis"
```

Returns structure, categories, and metadata about the book.

## Useful References for ANE Research

### Tehom (תהום) Occurrences

| Reference | Context |
|-----------|---------|
| Genesis 1:2 | Spirit hovering over the deep |
| Genesis 7:11 | Fountains of the great deep |
| Genesis 8:2 | Fountains of the deep stopped |
| Genesis 49:25 | Blessings of the deep |
| Deuteronomy 33:13 | Deep couching beneath |
| Psalm 33:7 | He gathers the deeps in storehouses |
| Psalm 42:8 | Deep calls unto deep |
| Psalm 77:17 | The depths were troubled |
| Psalm 104:6 | Covered it with the deep |
| Psalm 106:9 | Led them through the depths |
| Proverbs 8:27-28 | When he set the deep |
| Isaiah 51:10 | Dried the sea, the waters of the great deep |
| Ezekiel 26:19 | Bring up the deep upon you |
| Ezekiel 31:4 | The deep made him great |
| Amos 7:4 | Devoured the great deep |
| Jonah 2:6 | The deep was round about me |
| Habakkuk 3:10 | The deep uttered his voice |

### Asherah (אשרה) Occurrences

Key passages mentioning Asherah/Asherim:
- 1 Kings 15:13, 18:19
- 2 Kings 21:7, 23:4-7
- 2 Chronicles 15:16

### Leviathan (לויתן) Occurrences

- Job 3:8, 40:25-41:26
- Psalm 74:14, 104:26
- Isaiah 27:1

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Invalid reference format |
| 404 | Reference not found |
| 429 | Rate limited |

## Tips for Research Use

1. **Hebrew searches**: URL-encode Hebrew characters or use the search wrapper
2. **Batch requests**: Space out requests to avoid rate limiting
3. **Caching**: Cache frequently-used passages locally
4. **Commentary depth**: Use `with=all` sparingly - returns large payloads
