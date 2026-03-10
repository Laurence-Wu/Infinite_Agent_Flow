# Sample Workflow

This is an example workflow demonstrating the Infinite Agent Flow card structure.

## Structure

```
sample_workflow/v1/
├── guidance.md      ← This file: high-level context for the agent
├── card_01.json     ← First task card
└── card_02.json     ← Second task card (loops back to card_01)
```

## How It Works

1. The engine deals `card_01.json` as `current_task.md`.
2. The agent reads the file, does the work, and appends `![stop]!`.
3. The engine archives the result, picks the next card, and deals it.
4. When `card_02` completes, its `next_card` points back to `card_01` — the loop repeats.

## Stop Token

Append `![stop]!` on its own line when all deliverables are complete.

## Creating Your Own Workflow

Copy this directory, rename the cards, and set your own instructions.
Set `"loop_id"` on each card to create multiple independent loops within one workflow.
