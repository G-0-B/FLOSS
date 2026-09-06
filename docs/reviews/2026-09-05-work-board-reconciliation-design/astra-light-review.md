# External review — work-board reconciliation delta (verbatim)

```yaml
reviewer_self_id: gpt astra light  # self-declared in operator paste; [U]nverified
received: 2026-09-05, via operator chat paste
subject: docs/superpowers/specs/2026-09-05-work-board-reconciliation-delta.md v0.1.0
mutations_by_reviewer: none declared ("No design or board edits were made during this review")
```

Transcribed faithfully; formatting normalized, wording untouched:

---

The review is useful, but **D1–D10 should not be applied verbatim**. The design remains v0.1.1; the board's hash is unchanged.

| Items | Assessment and correction |
|---|---|
| **D1: freeze sources** | Accept. Preserve historical hashes and capture fresh hashes for every source actually used. The coordination plan has changed again since the review. |
| **D2: shared checks** | Accept with limits. Timestamp and reuse observations; refresh when relevant state changes. Local remote-tracking refs cannot establish live PR status. Embed results in the existing receipt to preserve file scope. |
| **D3 + D9: inventory coverage** | Revise substantially. The proposed keyword filter misses actual obligations at board lines **715, 716 and 722**, including Yumeichan consolidation. Its SHA pattern also captures dates. Review headings, table rows, bullets and prose; report candidate accounting separately from completeness. Sampling two sections cannot prove exhaustive coverage. |
| **D4: decision scope** | Keep the revision table. Reject "M1 DEFERRED binds none of the current text." Preserve the original decision and identify what changed; later edits neither erase that decision nor inherit approval. |
| **D5 + D6: efficient extraction** | Useful, with safeguards. Intent-level obligations must not disappear as "context." References need **source path + source hash + locator**, not the board hash for every source. Cross-source reconciliation remains necessary. |
| **D7: external atlas references** | Portability concern is valid. Plain-text citations alone don't fix availability. Label external sources and preserve only the bounded excerpts needed in the receipt. |
| **D8: base commit** | No defect established: a revision's base normally precedes its landing. Add the landing commit separately if useful. |
| **D10: purge approval** | No extra approval needed merely to preserve history during this already-selected lossless pass. Permanently changing the purge policy would be a separate decision. |

I also reproduced a defect in D2's proposed command using a harmless mock: it printed **`curl_rc=0` while the actual exit was `7`**. `$?` expands before curl runs. Capture the exit afterward.

The corrected direction fits your documentation-only scope. Runtime derived status, agent assignments, additional output files, and permanent policy changes would require separate authorization. **No design or board edits were made during this review.**
