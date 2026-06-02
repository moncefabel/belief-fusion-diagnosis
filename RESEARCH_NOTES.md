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

### Experiment 2 — PCR5 vs DS (K=0.81)
PCR5 gives DDoS m=0.326 vs DS m=0.263. Both converge on same diagnosis.
PCR5 is more decisive under high conflict. Adaptive rule selection
(DS if K<0.5, PCR5 if K>0.7) is a concrete thesis research axis.

### Experiment 3 — Temporal Fusion (5 timesteps)
Key finding: pivot at t=3 (Config_Error briefly overtakes DDoS after config
audit). DDoS mass trajectory: [0.171, 0.222, 0.313, 0.243, 0.464].
K(t) correctly signals "defer decision" at t=3 (K=0.723 > 0.7).
Final convergence at t=4 (DDoS m=0.464, K=0.720).
Demonstrates K(t) as self-organisation signal — Verrou 4.