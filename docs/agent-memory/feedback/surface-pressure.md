---
id: feedback-surface-pressure
type: feedback
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: feedback_surface_pressure.md
title: Surface friction, don't smooth it away silently
legacy_description: When blockers or errors appear, name them out loud — pressure
  helps this user make progress
origin_session_id: 9b0295fa-b336-4ff9-860b-fda5479b0e6a
---

When something breaks, is half-working, or is blocked on a step the user needs to take (restart, config, manual test), **say so explicitly** — don't silently disable/work around/defer it to keep the session clean.

**Why:** The user has been working on FLOSSIØULLK for 2+ years and has explicitly described struggling with executive function / chronic procrastination ("I work best under extreme pressure... extreme procrastination my whole life, even past the point of the deadlines. I do things for other people but not for myself"). They literally said: "if you had just let me know that's why it was saying that, I didn't mind, it's actually pressure for me to finish getting it working." Smoothing blockers into the background removes a signal they use. Part of what this project is for, in the user's own words, is helping people "broken by things we never agreed to let break us."

**How to apply:**
- When I hit an error I can't immediately fix, name it in plain terms and say what's still blocked, instead of quietly disabling the failing piece.
- When a fix requires a user action (restart, credential, manual test), state that explicitly and flag it as the next step — don't stash it as a footnote.
- If I'm about to disable/comment-out/try/except something to make an error message go away, stop and ask: does the user need to see this? Default to yes.
- Don't soften this into reassurance theater. Say "X is broken, here's why, here's what unblocks it." Let the friction exist in their view.
- This is NOT license to catastrophize or invent problems. Only surface real ones.
