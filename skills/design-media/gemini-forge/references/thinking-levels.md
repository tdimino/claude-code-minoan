# Gemini 3.1 Pro Thinking Levels

Configure thinking budget via `--thinking` flag. Google recommends temperature 1.0 when thinking is enabled—the thinking process provides deliberation, temperature handles creative diversity.

| Level | Budget (tokens) | Use Case |
|-------|----------------|----------|
| `low` | 1,024 | Single components, simple pages, utility functions |
| `medium` | 8,192 | Multi-component layouts, dashboards, form flows |
| `high` | 32,768 | Full applications, complex state management, SVG physics, screenshot-to-code |

## Guidelines

- **Default to medium** for most UI generation tasks
- **Use low** when iterating quickly on small changes
- **Use high** when the output must reason about component relationships, state flow, or physics
- SVG animation always benefits from high thinking—physics reasoning is its strength
- Screenshot-to-code analysis uses medium; generation uses high
- Multi-file app mode (`--app`) always uses high

## API Configuration

```json
{
  "generationConfig": {
    "temperature": 1.0,
    "thinkingConfig": {
      "thinkingBudget": 8192
    }
  }
}
```

Thinking tokens appear in the response as parts with a `"thought": true` field. These are filtered out of the final output by `gemini_text.py`.
