# Fixtures

Real API responses captured live on 2026-10-19; used by `test_offline.py`.

| File | Request |
|---|---|
| `answer_response.json` | POST /answer, model exa |
| `answer_stream.sse` | POST /answer, stream: true (OpenAI-style deltas, citations, cost, [DONE]) |
| `search_auto_text_output.json` | POST /search auto + text outputSchema + includeDomains exa.ai |
| `search_lite.json` | POST /search lite + highlights |
| `search_lite_summary_400.json` | POST /search lite + summary → 400 INVALID_REQUEST_BODY |
| `search_ignored_field_warning.json` | POST /search lite + deprecated highlightsPerUrl → IGNORED_FIELD warning |
| `agent_run_created.json` | POST /agent/runs effort minimal |
| `agent_run_completed.json` | GET /agent/runs/{id} after completion |
| `agent_error_budget_fixed.json` | POST /agent/runs effort medium + budget → 400 agent error envelope |
