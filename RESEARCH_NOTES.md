# Research Notes

## Session 1 — 2026-05-31

### Experiment 1 — DS Combination on Synthetic Network Incident

**Scenario:** Two heterogeneous agents (ML detector + expert system)
produce conflicting diagnoses on a simulated network incident.

**Finding:** DS combination with K=0.575 (moderate conflict) produces
equal support for DDoS and Config_Error (m=0.235 each).
High conflict is itself a diagnostic signal — the incident is genuinely
ambiguous and should trigger escalation rather than auto-remediation.

**Open question:** DS is defined for static evidence. How to extend
to online streaming settings where agent beliefs update incrementally?
Dynamic DS (Dezert-Smarandache) and contextual discounting are
candidate extensions for the thesis.