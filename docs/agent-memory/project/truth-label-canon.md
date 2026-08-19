---
id: project-truth-label-canon
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_truth_label_canon.md
title: Truth-status label scheme is canonical
legacy_description: ✅ Verified / ⚠️ Specified / 🔮 Aspirational / ❌ Unverified-or-Blocked
  is the canonical claim-truth scheme used in FLOSSI0ULLK-Architecture-Spec-v0.1 and
  ADR drafts
origin_session_id: 567c823f-3cba-4d75-866d-600bd4286e6f
---

The four-label truth-status scheme defined in Spine v0.5 has been adopted in canonical architecture documents:

- ✅ **Verified** — running, tested, confirmed
- ⚠️ **Specified** — designed and documented; not yet built or validated
- 🔮 **Aspirational** — intended direction; no spec or implementation
- ❌ **Unverified / Blocked** — claimed elsewhere but contradicted or not buildable yet

**Why:** Prior architecture docs blurred "designed" and "running." Without status discipline, every claim becomes load-bearing whether it's tested or not. The scheme forces honesty about what's actually built. It is also a forcing function for proper Phase 0 framing — Rose Forest DNA being `❌ Blocked` is unmissable when every layer carries a label.

**Where it lives:**
- `FLOSS/docs/architecture/FLOSSI0ULLK-Architecture-Spec-v0.1.md` (historical architecture intake with supersession banners; deprecates the "four planes" framing).
- `METAHARNESS_OPERATING_MODEL.md` carries `truth_status: "Specified"` in its YAML front matter.
- Filewatch metaharness plan also uses the scheme.

**Outstanding governance question:** Spine v0.5 defines the scheme; a separate "Context Continuation Artifact v0.2.0" variant was referenced externally but the source isn't on disk. There's also an outstanding critique flagged by another model. **A dedicated governance ADR canonicalizing the scheme is still pending** — Architecture-Spec-v0.1 uses the scheme without that ADR being merged, so its authority is conventional, not yet codified.

**How to apply:**
- When writing or reviewing architecture/spec docs, label every load-bearing claim with one of the four statuses.
- When you read a doc that's missing labels, treat unlabeled claims as `⚠️ Specified` at best until verified.
- Don't upgrade ⚠️→✅ or 🔮→⚠️ without an ADR or test record. The labels are commitments, not aspirations themselves.
- The pending governance ADR is the right place to surface the missing-critique question; flag it if it comes up.
