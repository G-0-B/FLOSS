# Computer-Use Gateway — Workstation Surface Lease

```yaml
id: "computer-use-gateway-spec"
version: "0.1.0"
kind: "spec"
status: "Active"
created: "2026-08-25"
truth_status: "Specified; lease unit tests Verified on landing"
schema: "computer-use-gateway.schema.json"
approval: "Operator AFK go-ahead 2026-08-25; SendInput remains default-deny"
```

## What this is

A Plane A **router**, not a controller, for sharing one Windows workstation among many MCP hosts. It grants and revokes **surface leases**. It does not plan tasks and it does not inject input.

Compose, do not build an AgentOS. Actuators stay behind the lease: Playwright MCP for web, HWND inventory for observe-only desktop, future FlaUI/Cua only after probe.

## Surfaces

`desktop` | `hwnd:<id>` | `display:<n>` | `browser:<ctx>` | `terminal:<pane>`

Browser exclusive does not conflict with desktop exclusive.

## Modes

- `observe-only`: may share a surface; may run `uia.snapshot` only.
- `exclusive`: one holder per surface; may run `uia.invoke` / `uia.set_value` once an actuator is wired.
- Human preemption freezes exclusive actuation.

## Default-deny

`sendinput` and `screenshot` fail closed even with an exclusive lease until an operator policy enables them. Live `uia.invoke` is leased but unwired until a probe lands.

## Runtime

- Package: `FLOSS/packages/computer_use_gateway/`
- HTTP daemon: `127.0.0.1:7333/mcp` (PID file `computer_use.pid`)
- Audit: `.agent-surface/heartbeat/janus-computer-use-audit.jsonl`

## Tools

`acquire_lease`, `release_lease`, `snapshot`, `invoke`, `sendinput`, `preempt_human`

## Falsifiers

Retire if: lease tests fail; two exclusive holders on one surface succeed; SendInput succeeds without policy; daemon binds non-loopback.
