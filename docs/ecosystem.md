# Community & Ecosystem Strategy

## Goals
- Foster an open, practitioner-driven community around GIS-OSS.
- Provide public benchmarks and prompt libraries so contributors can evaluate and extend the stack.
- Create a sustainable business model: open core, enterprise add-ons, and professional services.

## Pillars

### 1. GIS-Specific Benchmarks
- **SpatialBench** (working title): mix of municipal planning, environmental compliance, emergency management, and utilities tasks.
- Include vector + raster workloads, NL→SQL translation, tool orchestration, and narrative scoring.
- Maintain open-source harness under `benchmarks/spatialbench/` with reproducible datasets (CC0/ODbL).
- Publish leaderboards (self-hosted or Hugging Face Spaces) highlighting open models and fine-tuned variants.

### 2. University Partnerships
- Target urban planning, environmental science, and civil engineering departments.
- Offer course-ready Docker Compose environments, lab guides, and case studies.
- Sponsor capstone projects building add-ons (e.g., flood modeling, transportation analytics).
- Establish advisory council for periodic feedback on curriculum and tooling.

### 3. Open Core + Enterprise
- **Open Core**: core APIs, spatial toolkit, LLM orchestration, benchmarks, prompt library.
- **Enterprise Add-ons**:
  - Advanced governance (audit signing, RLS templates).
  - High-availability deployments (Kubernetes operators, managed PostGIS).
  - Premium integrations (FME Server connectors, ESRI extension packages).
  - Support / SLAs and customization services.
- Transparent roadmap: community votes weigh into open-core features, enterprise funding accelerates regulated-industry requirements.

### 4. Prompt & Scenario Library
- Curate prompts for common GIS questions: zoning, permit triage, disaster response, compliance, transportation.
- Store under `prompts/` with metadata (intent, required datasets, expected outputs).
- Provide Jupyter notebooks demonstrating prompts, expected SQL/tool chains, and result validation.
- Encourage community contributions via pull requests and discussion forums.

## Execution Plan
1. **Quarter 1**
   - Publish `SpatialBench` v0.1 (10 tasks, baseline metrics).
   - Launch prompt library with 25 vetted prompts and accompanying notebooks.
   - Announce university partnership program; onboard 1–2 pilot departments.
2. **Quarter 2**
   - Expand benchmarks to 30 tasks, add energy/carbon metrics.
   - Run first community challenge (best SQL/tool chain for planning scenario).
   - Release enterprise roadmap and begin design partner engagements.
3. **Quarter 3**
   - Host virtual summit / workshop with universities and municipal partners.
   - Release case studies showcasing 5×–10× productivity improvements.
   - Finalize licensing guidelines and contributor covenant.

## Community Support Channels
- GitHub Discussions for roadmap, Q&A, and prompt sharing.
- Monthly community call with roadmap updates and contributor demos.
- Slack/Discord workspace for real-time collaboration (moderated).
- Newsletter summarizing releases, benchmarks, and partner highlights.

## Success Metrics
- 50+ benchmark runs submitted within six months.
- 5 university partners incorporating GIS-OSS into coursework.
- Prompt library PRs from at least 10 external contributors.
- ≥3 enterprise design partners piloting advanced governance features.
