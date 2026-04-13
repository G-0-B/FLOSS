"""
Cell-scoped source chain writer for FLOSSIØULLK local agent nodes.

A "Cell" is a (DNA, agent) pair — the same unit Holochain uses. This
package owns the file-based precursor: one directory per Cell, one JSON
file per entry, topologically ordered via previous_hash links. When the
Holochain substrate comes online, each file on disk maps 1:1 onto a
source chain action with no structural rework.

Reading this package fresh? Open `cell.py` — `CellDirectory` is the only
public surface and its module docstring documents the full on-disk layout
and atomic-write strategy. The governing spec is
`docs/specs/2026-04-12-local-agent-node-design.md` §3.1.
"""
