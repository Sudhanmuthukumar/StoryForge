# Supported Models

StoryForge V1 supports the following LLM models for generation and training pipelines.

**Only models marked as "Validated" have successfully completed real StoryForge dataset training and evaluation.**

## Validated
- ✅ **Qwen2.5-3B** (via QLoRA)
  - Extensively tested on V3/V4 datasets.
  - Used for the primary heuristics extraction.

## Experimental
- ⚠ **Qwen2.5-7B**
  - References found in pilot testing scripts.

## Untested
- ❓ **Llama 3 8B**
  - References found in pilot testing scripts.
- ❓ **Mistral 7B**
  - References found in pilot testing scripts.

> **Note:** Do not assume untested models will perform reliably with StoryForge's strict JSON output schemas.
