"""Read-only: how each installed skill projection compares with the shared base."""
import json, sys
from pathlib import Path
sys.path.insert(0, "scripts")
import materialize_shared_skill_surface as m

ws = Path("C:/~shit")
manifest = m.load_manifest(Path("shared-skill-surface.json"))
roots = m.build_target_roots(manifest, ws)
registry = m.build_registry(manifest, ws, roots)
listed = {s["skill_name"]: s for s in registry["skills"]}
for target, root in roots.items():
    root = Path(root)
    rows = {"identical": [], "diverged": [], "missing": [], "unlisted-managed": [], "unmanaged": []}
    for name, skill in listed.items():
        d = root / name
        if not d.exists():
            rows["missing"].append(name); continue
        actual = {p.relative_to(d).as_posix(): p.read_text(encoding="utf-8", errors="replace")
                  for p in sorted(d.rglob("*")) if p.is_file() and p.name != m.MANAGED_MARKER}
        if actual == skill["files"]:
            rows["identical"].append(name)
        else:
            changed = sorted(k for k in set(actual) | set(skill["files"]) if actual.get(k) != skill["files"].get(k))
            rows["diverged"].append(f"{name} [{', '.join(changed[:4])}{' …' if len(changed) > 4 else ''}]")
    if root.exists():
        for d in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in listed):
            (rows["unlisted-managed"] if (d / m.MANAGED_MARKER).is_file() else rows["unmanaged"]).append(d.name)
    print(f"== {target}: {root} (exists={root.exists()})")
    for k, v in rows.items():
        print(f"   {k}: {len(v)}")
        if k in ("diverged", "unlisted-managed") and v:
            for x in v: print(f"      - {x}")
