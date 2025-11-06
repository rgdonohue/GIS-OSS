# Legal & Jurisdictional Architecture

This document consolidates legal guidance to ensure GIS-OSS complies with tribal, federal, and state obligations while
preserving Tribal sovereignty and limiting liability.

## Legal Frameworks To Embed

### CARE Principles (see `docs/data_sovereignty.md`)
- Enforce Collective Benefit, Authority to Control, Responsibility, Ethics at every workflow.

### Free, Prior, and Informed Consent (FPIC)
- FPIC checkpoints required before:
  - ingesting new datasets (especially TEK or sacred information)
  - sharing data/reports with external entities
  - enabling new automated workflows affecting cultural resources
- Consent engine must store FPIC status and block actions lacking consent.

### Treaty & Trust Responsibilities
- Support datasets and analytics referencing:
  - Ceded territory/treaty maps (hunting, fishing, gathering rights)
  - Winters Doctrine water rights (priority dates, flow levels)
  - Sacred site protections (American Indian Religious Freedom Act)
  - NAGPRA compliance for archaeological data exports
- Include modules for treaty defense (historical use stats, upstream impacts).

### Jurisdictional Complexities
- Expose configuration for:
  - Checkerboard lands (trust vs fee vs allotted parcels)
  - Public Law 280 states (state criminal/civil jurisdiction interplay)
  - Concurrent jurisdiction agreements (tribal-state MOUs)
  - Federal trust obligations (BIA oversight, TAAMS connectors)

### Sovereign Immunity & Liability
- Ensure system design and contracts preserve tribal sovereign immunity.
- Include indemnification clauses for vendors (project contributors) to protect the tribe.
- Clarify liability if sacred knowledge is exposed; require insurance or contingency plans.
- Default dispute resolution forum: tribal courts or designated cultural council.

## Legal Architecture Layers

```yaml
data_classification:
  public:
    description: Environmental data intended for broad sharing
    sharing: open
  sensitive:
    description: Resource locations, demographic stats
    sharing: requires FTPC + council approval
  protected:
    description: Critical habitats, TEK-linked species, ceremonial areas
    sharing: requires elder + cultural committee approval, export redaction
  sacred:
    description: Ceremonial/burial sites, oral histories, dream maps
    sharing: prohibited unless explicit ceremony dictates

access_matrix:
  role_based:
    - environmental_staff
    - cultural_keeper
    - legal_counsel
    - youth_intern
  traditional_roles:
    - elder
    - medicine_person
    - water_protector
    - fire_keeper
  temporal:
    - ceremony_window
    - seasonal_access
  purpose:
    - ceremony
    - grant_application
    - treaty_defense
    - education

audit_log:
  fields:
    - user_id / traditional_role
    - consent_token / FPIC reference
    - treaty_rights invoked
    - purpose
    - output_id (report/map) with watermark
```

## Federal & Tribal System Integration
- **TAAMS** (Trust Asset and Accounting Management System) — land/trust status data.
- **NIOGEMS** — oil & gas lease data for resource management.
- **BIA GIS Services** — authoritative boundaries and cadastral data.
- **IHS RPMS** — environmental health data (with HIPAA considerations).
- **HUD IHBG** — housing boundaries/demographic data.
- Build connectors/ETL jobs that respect data sharing agreements and audit access.

## Contractual Components

### Memorandum of Understanding (MOU)
Include clauses covering:
- Tribal ownership of data and derivative outputs.
- Source code ownership/licensing (preferably shared or Tribal-owned).
- Repatriation obligations at project termination.
- Annual review aligned with cultural calendars (e.g., winter council).
- Dispute resolution (Tribal Court, cultural councils).
- Insurance/indemnification for breaches (sacred knowledge exposure).

### Data Sharing Agreements
- Define allowed recipients (federal agencies, co-management partners).
- Specify purpose limitations, expiration dates, consent tokens.
- Record obligations for returning data and destroying copies.

## Recommended Legal Tasks
- Create legal review checklist (Treaty rights, FPIC, CARE, jurisdiction, liability).
- Implement consent engine enforcement for treaty/sacred data.
- Draft template agreements (MOU, data sharing, repatriation).
- Integrate with Tribal IRB approvals (store IRB IDs, expiration).
- Provide legal audit reports summarizing treaty rights invoked, consent records, external sharing.

Refer to `docs/data_sovereignty.md` and `docs/community_process.md` for governance protocols that complement this legal scaffolding.
