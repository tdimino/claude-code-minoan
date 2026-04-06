# Muqarnas Reference Images

Style anchors for the Muqarnasi daimon. These photographs teach Gemini what muqarnas look like—the geometric precision, material qualities, light/shadow interplay, and viewing perspective.

## Selected (Active Style Anchors)

Images in `selected/` are loaded as base64 context with every Muqarnasi API call.

| File | Source | Tradition |
|------|--------|-----------|
| `isfahan_01.jpg` | @ShiaVisuals / Ghasem Baneshi | Persian (Isfahan) |
| `isfahan_02.jpg` | @ShiaVisuals / Ghasem Baneshi | Persian (Isfahan) |
| `isfahan_03.jpg` | @ShiaVisuals / Ghasem Baneshi | Persian (Isfahan) |
| `isfahan_04.jpg` | @ShiaVisuals / Ghasem Baneshi | Persian (Isfahan) |

Source tweet: https://x.com/ShiaVisuals/status/2040387878509768841 (April 4, 2026)
Location: Isfahan, Iran (likely Shah Mosque / Imam Mosque, Safavid era)

## Adding References

To diversify beyond Persian tradition, add photographs from:
- **Moorish**: Alhambra (Sala de Dos Hermanas, Granada) — carved stucco, monochrome
- **Mamluk**: Cairo mosques — stone-carved, massive
- **Timurid**: Samarkand (Bibi-Khanum, Registan) — polychrome tile
- **Ottoman**: Selimiye Mosque (Edirne) — painted wood
- **Mughal**: Wazir Khan Mosque (Lahore) — marble, pietra dura

Place new images in `selected/` (max 4 total for context efficiency) or in tradition-specific subdirectories for CLI `--reference` overrides.
