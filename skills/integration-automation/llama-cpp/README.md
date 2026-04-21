# llama.cpp

Run GGUF models directly, load LoRA adapters, benchmark inference speed, and serve models via llama-server on Apple Silicon. Includes Qwen 3.5 serve scripts (9B dense + 35B MoE) with asymmetric KV cache and thinking mode. Secondary to Ollama---use when you need direct model control, LoRA hot-loading, or maximum tok/s.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Ollama is the primary local inference engine, but llama.cpp gives you direct control: LoRA adapter hot-swapping without rebuilding models, benchmarking, custom server configs, and 10--20% faster inference. Both share the same GGUF model files, so there's no duplication.

---

## Structure

```
llama-cpp/
  SKILL.md                          # Full usage guide with subprocess best practices
  README.md                         # This file
  scripts/
    llama_serve.sh                  # Generic llama-server (port 8081)
    llama_serve_qwen35.sh           # Qwen 3.5 35B MoE server
    llama_serve_qwen35_9b.sh        # Qwen 3.5 9B dense server (Q4 or F16)
    llama_lora.sh                   # LoRA adapter inference
    llama_bench.sh                  # Benchmark llama.cpp vs Ollama
    eval_local.sh                   # Local evaluation runner
    train_local.sh                  # Local training runner
    ollama_model_path.sh            # Resolve Ollama model → GGUF blob path
    convert_lora_to_gguf.py         # Convert HuggingFace LoRA → merged GGUF
    convert_to_train_txt.py         # Convert data to training format
```

---

## Usage

```bash
# Resolve Ollama model to GGUF path (avoids file duplication)
GGUF=$(ollama_model_path.sh qwen2.5:7b)

# Run inference
llama-cli -m "$GGUF" -p "Your prompt" -n 128 --n-gpu-layers all --single-turn

# Start OpenAI-compatible server (port 8081)
llama_serve.sh <model.gguf>

# Serve Qwen 3.5 9B with thinking mode
llama_serve_qwen35_9b.sh

# Benchmark llama.cpp vs Ollama
llama_bench.sh qwen2.5:7b

# Load LoRA adapter without merging
llama_lora.sh <base.gguf> <lora.gguf> "Your prompt"

# Convert HuggingFace LoRA to GGUF
python3 convert_lora_to_gguf.py --base <model> --lora <adapter> --output out.gguf
```

---

## When to Use llama.cpp vs Ollama

| Task | Use |
|------|-----|
| RLAMA queries | Ollama (native integration) |
| Quick model chat | Ollama (`ollama run`) |
| LoRA adapter testing | llama.cpp (`llama_lora.sh`) |
| Benchmarking tok/s | llama.cpp (`llama_bench.sh`) |
| Maximum inference speed | llama.cpp (10--20% faster) |
| Custom server config | llama.cpp (`llama_serve.sh`) |
| GGUF conversion | llama.cpp (`convert_lora_to_gguf.py`) |

---

## Qwen 3.5 Serve Scripts

| Script | Model | Memory | Speed |
|--------|-------|--------|-------|
| `llama_serve_qwen35_9b.sh` | 9B dense Q4 | ~6.6 GB | ~38 tok/s |
| `llama_serve_qwen35_9b.sh` (F16) | 9B dense BF16 | ~17.9 GB | ~8--12 tok/s |
| `llama_serve_qwen35.sh` | 35B MoE | 64+ GB | varies |

All Qwen scripts enable asymmetric KV cache (q8_0 keys + q4_0 values), saving ~60% KV memory vs FP16 cache.

---

## Setup

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- `brew install llama.cpp` (provides `llama-cli`, `llama-server`, `llama-quantize`)
- Ollama (for shared GGUF model files and `ollama_model_path.sh`)
- Python 3.10+ (for `convert_lora_to_gguf.py`)

---

## Related Skills

- **`rlama`**: Local RAG using Ollama as the inference backend.
- **`smolvlm`**: Local vision-language model (mlx-vlm, different engine).

---

## Requirements

- macOS Apple Silicon
- llama.cpp (`brew install llama.cpp`)
- Ollama (optional, for model path resolution and benchmarking)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/llama-cpp ~/.claude/skills/
```
