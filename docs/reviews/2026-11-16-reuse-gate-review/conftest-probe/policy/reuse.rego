# Probe only (2026-11-16): can conftest/OPA carry the reuse gate's checks?
# Input: docs/specs/spec-registry.json. Data (optional): data.tree.files, a
# list of canonical paths produced OUTSIDE conftest by a wrapper.
package main

window_ns := 120 * 24 * 60 * 60 * 1000000000

# R1 - a tier-2 entry whose reviewer is not a structured object fails.
deny contains msg if {
	some rel, entry in input.entries
	entry.tier == 2
	not is_object(entry.reuse.reviewer)
	msg := sprintf("R1 %s: tier 2 reviewer must be an object", [rel])
}

# R2 - reuse evidence older than the window fails.
deny contains msg if {
	some rel, entry in input.entries
	d := entry.reuse.search_date
	t := time.parse_rfc3339_ns(concat("", [d, "T00:00:00Z"]))
	time.now_ns() - t > window_ns
	msg := sprintf("R2 %s: search_date %s is older than 120 days", [rel, d])
}

# R4 - a file on a gated surface with no registry entry fails.
# Only possible if something else lists the tree and passes it in as data.
gated := {"FLOSS/scripts/", "FLOSS/packages/", "FLOSS/hooks/"}

deny contains msg if {
	some f in data.tree.files
	some g in gated
	startswith(f, g)
	not input.entries[f]
	msg := sprintf("R4 %s: on a gated surface with no entry", [f])
}
