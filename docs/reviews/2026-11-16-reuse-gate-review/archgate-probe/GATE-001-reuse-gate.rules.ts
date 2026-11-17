/// <reference path="../rules.d.ts" />
import { createHash } from "node:crypto";

const PREFIX = "FLOSS/";
const SURFACE_GLOBS = [
  "scripts/**/*", "hooks/**/*", "docs/specs/**/*", "docs/adr/**/*",
  "packages/**/*", "ARF/dnas/**/*", ".github/workflows/**/*",
  "shared-agent-surface.json", "shared-agent-memory-surface.json",
  "shared-ai-roster-surface.json", "shared-context-surface.json",
  "shared-hook-surface.json", "shared-skill-surface.json",
];
const EXEMPT_SEGMENTS = ["/__pycache__/", "/scripts/tests/", "/tests/", "/target/", "/.venv/", "/venv/", "/archive/"];
const EXEMPT_NAMES = ["INDEX.md", ".gitignore", "__init__.py", "Cargo.lock"];
const LIMITED = ["FLOSS/packages/", "FLOSS/ARF/dnas/", "FLOSS/.github/workflows/", "FLOSS/shared-"];
const DEADLINE = "2027-03-16";
const WINDOW_DAYS = 120;
const REG = "docs/specs/spec-registry.json";

type Entry = { tier?: unknown; grandfathered?: unknown; reuse?: any };
async function entries(ctx: RuleContext): Promise<Record<string, Entry>> {
  const reg = (await ctx.readJSON(REG)) as { entries?: Record<string, Entry> };
  return reg.entries ?? {};
}
function gated(rel: string): boolean {
  const norm = "/" + (PREFIX + rel).toLowerCase() + "/";
  if (EXEMPT_SEGMENTS.some((s) => norm.includes(s))) return false;
  const name = rel.split("/").pop() ?? "";
  return !EXEMPT_NAMES.includes(name);
}
function grandfathered(rel: string, e: Entry | undefined): boolean {
  return !!e && e.grandfathered === true && !("tier" in e) && LIMITED.some((p) => rel.startsWith(p));
}

export default {
  rules: {
    "unregistered-artifact": {
      description: "R4: a file on a gated surface with no registry entry fails",
      async check(ctx: RuleContext) {
        const reg = await entries(ctx);
        const seen = new Set<string>();
        for (const g of SURFACE_GLOBS) {
          for (const f of await ctx.glob(g)) {
            const rel = f.replaceAll("\\", "/");
            if (seen.has(rel) || !gated(rel)) continue;
            seen.add(rel);
            if (!reg[PREFIX + rel]) ctx.report.violation({ message: "MISSING " + PREFIX + rel, file: rel });
          }
        }
        ctx.report.info({ message: "walked " + seen.size + " gated files", file: REG });
      },
    },
    "tier2-reviewer-object": {
      description: "R1: a tier-2 entry needs a structured reviewer",
      async check(ctx: RuleContext) {
        for (const [rel, e] of Object.entries(await entries(ctx))) {
          const r = e.reuse?.reviewer;
          if (e.tier === 2 && (typeof r !== "object" || r === null || Array.isArray(r)))
            ctx.report.violation({ message: "R1 " + rel + ": tier 2 reviewer must be an object", file: REG });
        }
      },
    },
    "evidence-window": {
      description: "R2: reuse evidence older than the window fails",
      async check(ctx: RuleContext) {
        for (const [rel, e] of Object.entries(await entries(ctx))) {
          const d = e.reuse?.search_date;
          if (typeof d !== "string") continue;
          const age = Math.floor((Date.now() - Date.parse(d + "T00:00:00Z")) / 86400000);
          if (age > WINDOW_DAYS) ctx.report.violation({ message: "R2 " + rel + ": evidence " + age + "d old", file: REG });
        }
      },
    },
    "reviewer-record-digest": {
      description: "R3: the reviewer record is a real file whose LF-normalised sha256 matches",
      async check(ctx: RuleContext) {
        for (const [rel, e] of Object.entries(await entries(ctx))) {
          const r = e.reuse?.reviewer;
          if (typeof r !== "object" || r === null || typeof r.record !== "string") continue;
          let text: string;
          try { text = await ctx.readFile(r.record); }
          catch { ctx.report.violation({ message: "R3 " + rel + ": record not found: " + r.record, file: REG }); continue; }
          const got = createHash("sha256").update(text.replaceAll("\r\n", "\n"), "utf8").digest("hex");
          if (r.record_sha256 && got !== r.record_sha256)
            ctx.report.violation({ message: "R3 " + rel + ": record digest " + got + " != " + r.record_sha256, file: r.record });
          else ctx.report.info({ message: "R3 " + rel + ": record digest ok " + got, file: r.record });
        }
      },
    },
    "grandfather-limits": {
      description: "Touch rule and deadline for surface-grandfathered entries",
      async check(ctx: RuleContext) {
        const reg = await entries(ctx);
        const past = new Date().toISOString().slice(0, 10) >= DEADLINE;
        let n = 0;
        for (const [rel, e] of Object.entries(reg)) {
          if (!grandfathered(rel, e)) continue;
          n++;
          if (past) ctx.report.violation({ message: rel + ": grandfathered past " + DEADLINE, file: REG });
        }
        for (const f of ctx.changedFiles) {
          const rel = PREFIX + f.replaceAll("\\", "/");
          if (grandfathered(rel, reg[rel])) ctx.report.violation({ message: rel + ": modified while still grandfathered", file: f });
        }
        ctx.report.info({ message: n + " grandfathered; changedFiles=" + ctx.changedFiles.length, file: REG });
      },
    },
  },
} satisfies RuleSet;
