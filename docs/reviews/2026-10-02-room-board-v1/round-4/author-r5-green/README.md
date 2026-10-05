# Author receipts for revision 5

Plan revision 5 SHA-256: f2a8392e874a6f90c6818657fccc0050625da518fb09860dff0d58c68b8d1752

- results.json, baseline.txt, phase1.txt, proposal.txt: the required green set on base, Phase 1 and Phase 2 trees rebuilt by green_compare.py from the sources the plan inlines (archive of 4aab13e, A2A files from 225287c). Same machine and environment for all three; installed dependencies, MCP 1.27.0.
- deploy_harness.ps1 and deploy-harness-powershell.json / deploy-harness-pwsh.json: the 26 inert checks of the Deployment helper block (fake checkouts, scratch port 19994, scratch log, scratch git repo), run under Windows PowerShell 5.1 and PowerShell 7.

Author evidence, not review findings. The scripts reference scratch paths from the authoring session.
