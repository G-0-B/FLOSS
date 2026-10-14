"""Native POSIX check of F4: the same fixture against the code before and after."""
import importlib.util, json, sys, tempfile, traceback
from pathlib import Path

HERE = Path(__file__).parent

def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

for name in ("skill_before", "skill_after"):
    m = load(name)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ws = d / "workspace"; ws.mkdir()
        root = d / "skills"
        bad = root / "a-bad-identity"; bad.mkdir(parents=True)
        (bad / m.MANAGED_MARKER).write_text(json.dumps({
            "managed_by": m.MANAGED_BY, "skill_name": "a-bad-identity",
            "workspace_root": str(ws) + "\x00tail"}), encoding="utf-8")
        own = root / "b-own-withdrawn"; own.mkdir()
        (own / m.MANAGED_MARKER).write_text(json.dumps({
            "managed_by": m.MANAGED_BY, "skill_name": "b-own-withdrawn",
            "source_path": str(ws / "skills" / "b-own-withdrawn"),
            "workspace_root": str(ws.resolve())}), encoding="utf-8")
        try:
            messages, drift = m.prune_stale_projections(
                "posix", root, set(), check=True, dry_run=False, owner_root=ws)
            print(name, "OK drift=%s" % drift)
            for line in messages:
                print("   ", line.replace(str(d), "<tmp>"))
        except Exception as exc:
            print(name, "RAISED", type(exc).__name__ + ":", exc)
            print("   ", traceback.format_exc().strip().splitlines()[-3].strip())
print(sys.platform, sys.version.split()[0])
