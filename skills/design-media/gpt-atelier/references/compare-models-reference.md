# Model Comparison Reference

`compare_models.py` generates the same prompt across multiple OpenAI image models and produces a dark-themed HTML comparison page with image cards, timing data, file sizes, error states, and a full model inventory table.

## Usage

```bash
python3 scripts/compare_models.py "prompt" [options]
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--models` | gpt-image-1 gpt-image-2 | Space-separated model list |
| `--all` | — | Compare all 6 known image models |
| `--size` | 1024x1024 | Image size (WxH) |
| `--quality` | high | low, medium, high, auto |
| `--format` | png | png, jpeg, webp |
| `--output` | ./output | Output directory for images + HTML |
| `--open` | — | Open the HTML page in browser after generation |
| `--list-models` | — | List available image models on your account and exit |

## Examples

```bash
# Quick A/B: gpt-image-1 vs gpt-image-2 (default pair)
python3 scripts/compare_models.py "A Minoan bull-leaper under golden light" --open

# Full lineup — all 6 models
python3 scripts/compare_models.py "Product shot of a ceramic vase on marble" --all --open

# Specific models for cost comparison
python3 scripts/compare_models.py "Logo for a tech startup" \
  --models gpt-image-1-mini gpt-image-1 gpt-image-2 --quality low --open

# Just check what models are available on your account
python3 scripts/compare_models.py "" --list-models
```

## Known Models

| Model | Notes |
|-------|-------|
| dall-e-2 | Legacy. 256/512/1024px. |
| dall-e-3 | Legacy. Revised prompts. 1024/1792px. |
| gpt-image-1-mini | Cheapest ($0.006/img low). Fast iteration. |
| gpt-image-1 | Multimodal native. Standard + high quality. |
| gpt-image-1.5 | Region-aware editing. 4x faster than v2. |
| gpt-image-2 | Reasoning-based. ~99% text rendering. 4K. Streaming. |
| chatgpt-image-latest | Alias for latest ChatGPT image model. |

## HTML Output

The generated HTML page includes:

- **Image cards** — each model's output with timing and file size
- **Error cards** — locked placeholder with verification link for blocked models
- **Model inventory table** — all available image models with status dots (green/yellow/red)
- **Dark theme** — SF Mono, #0a0a0a background, matches Subquadratic aesthetic

## Behavior Notes

- DALL-E models are forced to 1024x1024 (their max shared size) for fair comparison
- Models requiring org verification render as locked cards with a direct link to `platform.openai.com/settings/organization/general`
- The script queries the Models API to build the full inventory table, falling back to a hardcoded list if the API call fails
- Each model generates sequentially (not parallel) to avoid rate limits
