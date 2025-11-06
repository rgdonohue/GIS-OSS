# Model Training & Fine-Tuning Plan

## Overview

GIS-OSS will rely on a tiered language-model stack, each fine-tuned on targeted
datasets to maximize accuracy and cost efficiency.

| Tier | Role | Base Model | Target Data |
|------|------|------------|-------------|
| Router | Intent classification, policy enforcement, tool routing | 2–3B distilled model (e.g., Qwen 1.5B, Phi-3-mini) | Labeled municipal planning queries, PostGIS task tags |
| SQL Generator | Deterministic SQL/tool parameter generation | CodeLlama 7B (or equivalent) | PostGIS docs, ESRI→PostGIS translations, curated NL→SQL pairs |
| Report Writer | Narrative summaries, planning memos, executive briefs | Qwen 2.5 7B/14B (LoRA) | Real municipal planning documents + human-written responses |
| Fallback | Complex reasoning, escalations | Qwen 2.5 32B / Llama 3.1 70B | Frozen base model (no tuning initially) |

## Data Sources

1. **PostGIS Documentation** – scrape and segment:
   - Function definitions (ST_*, spatial relationships)
   - Example queries + explanations
   - Indexing and performance guidance
   - Projection/transformation best practices

2. **Municipal Planning Corpus**
   - Public zoning board minutes & agendas
   - City open-data portals (permits, zoning changes, environmental reports)
   - Planning RFPs, transportation studies, land-use updates
   - Annotate queries with intent labels (e.g., `buffer`, `change_detection`, `compliance_check`)

3. **ESRI → PostGIS Translation Set**
   - GeoProcessing ModelBuilder/ArcPy scripts mapped to SQL + spatial tool calls
   - ESRI REST/Query examples with equivalent PostGIS expressions
   - FME workspace snippets showing ArcGIS connectors translated to PostGIS flows

4. **Narrative Training Data**
   - Municipal plan summaries
   - Environmental impact assessments
   - Community engagement reports
   - Annotated with tone, audience, and required citations

## Annotation Strategy

### Router Labels
- `intent`: primary task (buffer, nearest, intersect, aggregate, temporal_change, licensing)
- `domain`: planning, environmental, utilities, transportation, emergency
- `confidence`: human-rated difficulty (easy/medium/hard)
- `requires_data`: yes/no (whether additional data ingestion is needed)

### SQL/Tool Labels
- `sql`: final PostGIS SQL statement(s)
- `tools`: ordered list of tool invocations (e.g., `buffer_geometry`, `calculate_area`)
- `validation`: optional tests/assertions (expected feature count, area range)
- `notes`: rationale or warnings (e.g., projection caveats)

### Narrative Labels
- `audience`: planner, executive, public briefing
- `structure`: intro, findings, recommendations, next steps
- `voice`: authoritative, consultative, neutral
- `sources`: references or data sources cited

## Fine-Tuning Recipes

### Router Model (Intent Classifier)
- Base: Qwen 1.5B, Phi-3-mini, or Llama 3 3B distilled
- Method: LoRA (QLoRA) with task + domain labels in instruction format
- Dataset size: 5–10k labeled prompts
- Evaluation: accuracy, macro-F1 across intents; confusion matrix to ensure coverage

### SQL Generator
- Base: CodeLlama 7B (or StarCoder-derived model)
- Method: Supervised fine-tuning (LoRA) on NL→SQL pairs, augmented with few-shot tool examples
- Dataset size: 3–5k high-quality pairs; augment with synthetic queries validated by experts
- Evaluation:
  - Exact match on SQL (ignoring whitespace)
  - Execution success (queries run against sample db)
  - Tool invocation accuracy (expected vs predicted tool chain)

### Report Writer
- Base: Qwen 2.5 7B or Llama 3.1 8B
- Method: LoRA on instruction-style datasets (prompt + context → structured response)
- Dataset size: 2–3k curated municipal narratives (can start smaller)
- Evaluation: BLEU/ROUGE for structure, human evaluation for tone/completeness, citation accuracy checks

### Fallback Model
- Initially use base Qwen 32B or Llama 70B without tuning
- Add rejection/guardrail prompts referencing router metadata
- Future: limited LoRA for domain-specific refusal style if needed

## Training Pipeline

1. **Data Ingestion**
   - Use `scripts/datasets/` (to be created) for collecting/scraping sources
   - Store raw text as JSONL with metadata (source, license, timestamp)

2. **Preprocessing**
   - Normalize text (remove boilerplate, unify units)
   - Generate PostGIS↔ESRI pairs with mapping dictionaries
   - Convert to instruction format (prompt, context, expected response)

3. **Annotation Tooling**
   - Lightweight Streamlit/Label Studio app for manual labeling
   - Auto-suggest labels based on heuristics, human confirm/adjust

4. **Training**
   - Use Hugging Face PEFT for LoRA runs
   - Track experiments with Weights & Biases or MLflow
   - Save adapters under `models/finetuned/<tier>/<version>`

5. **Evaluation**
   - Maintain a `benchmarks/` directory with:
     - Router intent test set
     - SQL execution harness (pytest plugin hitting local PostGIS)
     - Narrative QA (keyword checks, custom scoring scripts)

6. **Deployment**
   - Serve router + SQL generator via vLLM (multi-model) or separate containers
   - Cache LoRA adapters for on-demand loading
   - Include version metadata in API responses (`model_version`, `adapter_version`)

## Next Steps

1. Draft Week 8 backlog items:
   - Dataset acquisition checklist
   - Annotation tooling selection
   - Initial LoRA experiments for router model

2. Build minimal dataset samples for proof-of-concept (10–20 examples each)

3. Wire evaluation harness to CI (run small router/SQL regression suite on pull requests)
