#!/usr/bin/env python3
"""
Convert Kothar training JSONL to llama.cpp finetune format.

Input: JSONL with {messages: [{role, content}...]} format
Output: Plain text with <SFT> delimiters and chat template applied

Usage:
  python3 scripts/convert_to_train_txt.py \
    --input output/dossier_training.jsonl \
    --output output/train.txt \
    --template chatml

Templates:
  - llama2: [INST] ... [/INST] format
  - chatml: <|im_start|> format (Qwen, etc.)
  - mistral: Mistral instruction format
"""
import argparse
import json
import sys
from pathlib import Path

TEMPLATES = {
    'llama2': {
        'bos': '<s>',
        'eos': '</s>',
        'system': '<<SYS>>\n{content}\n<</SYS>>\n\n',
        'user': '[INST] {content} [/INST] ',
        'assistant': '{content}',
    },
    'chatml': {
        'bos': '',
        'eos': '',
        'system': '<|im_start|>system\n{content}<|im_end|>\n',
        'user': '<|im_start|>user\n{content}<|im_end|>\n',
        'assistant': '<|im_start|>assistant\n{content}<|im_end|>\n',
    },
    'mistral': {
        'bos': '<s>',
        'eos': '</s>',
        'system': '',  # Mistral has no system token
        'user': '[INST] {content} [/INST] ',
        'assistant': '{content}',
    },
}


def convert_conversation(messages: list[dict], template: dict) -> str:
    """Convert a single conversation to templated text with proper BOS/EOS tokens."""
    parts = []

    # Add BOS token if present
    if template.get('bos'):
        parts.append(template['bos'])

    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')
        if role in template and template[role]:
            parts.append(template[role].format(content=content))
        elif role == 'assistant':
            # Always include assistant response
            parts.append(content)

    # Add EOS token if present
    if template.get('eos'):
        parts.append(template['eos'])

    return ''.join(parts)


def main():
    parser = argparse.ArgumentParser(
        description='Convert Kothar training JSONL to llama.cpp finetune format'
    )
    parser.add_argument('--input', '-i', required=True,
                        help='Input JSONL file with training conversations')
    parser.add_argument('--output', '-o', required=True,
                        help='Output text file for llama.cpp finetune')
    parser.add_argument('--template', '-t', default='chatml',
                        choices=TEMPLATES.keys(),
                        help='Chat template format (default: chatml for Qwen)')
    parser.add_argument('--delimiter', '-d', default='<SFT>',
                        help='Sample delimiter (default: <SFT>)')
    parser.add_argument('--filter-stage', '-s', default=None,
                        help='Only include samples with this stage (e.g., dossier_qa)')
    parser.add_argument('--min-assistant-length', type=int, default=20,
                        help='Minimum assistant response length in chars (default: 20)')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    template = TEMPLATES[args.template]
    samples = []
    skipped = {'empty': 0, 'short': 0, 'stage': 0}

    with open(input_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping malformed JSON at line {line_num}: {e}",
                      file=sys.stderr)
                continue

            # Filter by stage if specified
            if args.filter_stage and data.get('stage') != args.filter_stage:
                skipped['stage'] += 1
                continue

            messages = data.get('messages', [])
            if not messages or not isinstance(messages, list):
                skipped['empty'] += 1
                continue

            # Check assistant response length
            assistant_content = ''
            for msg in messages:
                if msg.get('role') == 'assistant':
                    assistant_content = msg.get('content', '')
                    break

            if len(assistant_content) < args.min_assistant_length:
                skipped['short'] += 1
                continue

            # Convert to template format
            text = convert_conversation(messages, template)
            if text.strip():
                samples.append(text)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        # llama.cpp expects delimiter BEFORE each sample (--sample-start)
        f.write(args.delimiter + args.delimiter.join(samples))

    # Report
    print(f"Converted {len(samples)} samples to {args.output}")
    print(f"  Template: {args.template}")
    print(f"  Delimiter: {args.delimiter}")
    if any(skipped.values()):
        print(f"  Skipped: {skipped['empty']} empty, {skipped['short']} short, "
              f"{skipped['stage']} filtered by stage")

    # Show sample preview
    if samples:
        preview = samples[0][:300] + '...' if len(samples[0]) > 300 else samples[0]
        print(f"\n--- Sample preview ---\n{preview}")


if __name__ == '__main__':
    main()
