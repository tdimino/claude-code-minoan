# Troubleshooting

## Common Errors

### `model_not_found` or `does not exist`
gpt-image-2 may not be available on your account yet. Use `--fast` (gpt-image-1.5) or `--mini` (gpt-image-1-mini) as fallback. Run `python test_connection.py --check-models` to see what's available.

### `content_policy_violation`
Prompt was flagged by content moderation. Try:
- Use `--moderation low` for less restrictive filtering
- Replace "military", "weapon", "war" with "cinematic", "dramatic", "professional"
- For artistic/dark themes, consider using nano-banana-pro instead

### `invalid_size`
Size must satisfy: both dimensions multiples of 16, max edge 3840px, aspect ratio ≤3:1, total pixels 655,360-8,294,400. Use a preset (`--size square`) to avoid calculation.

### `rate_limit_exceeded`
Add `sleep 2` between batch calls. Check your tier limits at `platform.openai.com/settings`.

### Mask errors
- Mask must be same dimensions as input image
- Mask must have an alpha channel (PNG with transparency)
- `edit_image.py` auto-converts B&W masks if Pillow is installed: `pip install Pillow`

### `authentication_error`
Check `OPENAI_API_KEY` is set: `echo $OPENAI_API_KEY`
Verify at `platform.openai.com/api-keys`.

### Slow generation (>60s)
- Complex prompts with many elements take longer
- Use `--quality low` or `--quality medium` for faster iteration
- Use `--format jpeg` instead of `png` for lower latency
- gpt-image-1.5 (`--fast`) is ~4x faster than gpt-image-1

### `unknown_parameter: response_format`
`gpt-image-2` does not accept the legacy `response_format` parameter (used by DALL-E). It always returns `b64_json`. Use `output_format` to select `png`, `jpeg`, or `webp` instead.

### `organization_verification_required` (403)
GPT Image models require API Organization Verification. Go to `platform.openai.com/settings/organization/general` and click "Verify Organization". While waiting, use `--fast` (gpt-image-1.5) or `--mini` (gpt-image-1-mini) as fallbacks. `test_connection.py` automatically falls back to gpt-image-1.5 when it detects this error.

## Testing

```bash
# Full connectivity check
python scripts/test_connection.py --check-models --generate-test

# JSON output for scripting
python scripts/test_connection.py --check-models --json
```
