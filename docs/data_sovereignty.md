# Indigenous Data Sovereignty Framework

This note pulls together what we heard from the review committee. It’s here to keep GIS-OSS grounded in “GIS by and with Tribes,” honoring sovereign rights and cultural protocols at every step.

## Sovereignty vs. Privacy
- **Privacy** focuses on individual protection (PII, confidentiality).
- **Sovereignty** is a collective right: Nations govern how data is collected, classified, accessed, and shared.
- **Principle**: All data—maps, reports, model outputs—remain under tribal control in perpetuity and can be repatriated on request.

### Living Data Protocol
Treat every dataset (TEK, ceremonial sites, audio narratives, etc.) as a living relative. Each must carry:
- caretaker metadata (knowledge holder, council, department)
- consent status (collective consent, elder approval)
- seasonal availability (winter-only, ceremony months, etc.)
- gender/age restrictions (e.g., women-only plant knowledge)
- purpose restrictions (ceremonial vs. planning use)
- repatriation clause (exportable back to tribe in original + derived forms)

## CARE Principles Integration

| CARE | Implementation Requirement |
|------|----------------------------|
| Collective Benefit | Every feature must document how it benefits the entire community (grants, protection, knowledge preservation). |
| Authority to Control | Tribe retains decision-making over data categories, sharing, deletion, and platform updates. |
| Responsibility | Project must build tribal capacity (training, hiring, code ownership) and protect cultural knowledge. |
| Ethics | Align workflows with cultural protocols, consent, and reciprocity; refuse use cases that violate community values. |

Embed these checks in the consent engine (see `docs/community_process.md`).

## Data Classifications

```yaml
classification:
  public: General environmental observations + open datasets
  sensitive: Resource locations, population stats, grant dashboards
  protected: Cultural use areas, traditional crops, treaty-use maps
  sacred: Ceremonial sites, burial grounds, TEK narratives, elders’ recordings

controls:
  seasonal: Access window by moon/season
  gender_age: e.g., {"women": true, "men": false, "youth": false}
  purpose: ["ceremony", "planning", "education"]
  consent: elder_approval_required?, council_resolution_required?
```

- **Sacred data** never leaves secure storage; exports must redact geometry and watermark outputs.
- **Protected data** requires explicit consent trail (council resolution, elder sign-off, FPIC documentation).

## Access & Consent Matrix

| Factor | Examples | Enforcement |
|--------|----------|-------------|
| Role-based | Environmental staff, cultural liaisons, elders, youth interns | Assign both administrative (GIS analyst) and traditional roles (Knowledge Keeper) |
| Seasonal | “Accessible only during Winter Moon” | Consent engine denies requests outside window |
| Gender/Age | Women-only plant knowledge | Attribute filters tied to user profile |
| Purpose-based | Ceremony, grant writing, schooling | Prompt includes purpose; consent engine evaluates permissibility |
| FPIC | Free, Prior, Informed Consent for new use | Workflow triggers council review before new dataset/tool adoption |

## Governance Hooks Needed
- **Tribal IRB Integration**: record IRB approvals/conditions in metadata; block access if expired.
- **FPIC Workflow**: track each dataset/tool request through consent engine; require council resolution for new sharing arrangements.
- **Data Sharing Agreements**: template + metadata that specify with whom, for what, and for how long data may be shared (federal/state agencies).
- **Traditional Knowledge IP**: include TK labels (e.g., TK Seasonal, TK Women) to signal rights/responsibilities.
- **Audit Context**: logs must capture purpose, consent tokens, elder approvals, and downstream dissemination (e.g., which report was generated).

## Repatriation & Exit Clauses
- Provide “export & repatriate” function that bundles raw/processed data plus audit logs.
- Ensure code + configuration can transfers to tribal IT; include legal MOU ensuring code ownership or joint stewardship.
- If partnership ends, system must:
  1. Delete non-tribal copies.
  2. Return all derived outputs (models, reports) to tribe.
  3. Document deletion in audit ledger with council confirmation.

## Where To Start
1. **Consent engine** — capture seasonal/role/purpose rules in JSON, enforce them in middleware, and return clear messages when access is paused.
2. **Classification metadata** — extend STAC/metadata models with classification + consent status so downstream tools stay aware.
3. **Audit enhancements** — add purpose, consent token, elder approval ID (when applicable) to every log entry.
4. **Toolkit support** — include SDK helpers like `with_consent(role="elder", purpose="ceremony")` and redaction utilities for exports.
5. **User management** — connect to tribal identity systems or store traditional roles locally so the consent engine has context.

Refer to `docs/community_process.md` and `docs/legal_architecture.md` for partner engagement and legal structures that wrap these technical requirements.
