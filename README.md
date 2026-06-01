# belief-fusion-diagnosis

> **Dempster-Shafer belief fusion for heterogeneous agent diagnostic arbitration**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Research Prototype](https://img.shields.io/badge/status-research%20prototype-purple.svg)]()

---

## Motivation

When heterogeneous algorithmic agents independently analyse the same
network incident and produce **contradictory diagnostic hypotheses**,
how do we formally arbitrate without simply overriding one agent's
assessment?

This is **Verrou 3** of the target CIFRE doctoral thesis
(Orange Innovation / EURECOM, ref. 2026-51517):

> *"When heterogeneous agents produce contradictory diagnostics, what
> formal mechanism arbitrates without erasing the diversity of models?"*

This repository prototypes an answer using **Dempster-Shafer (DS)
theory of evidence** — a framework for fusing uncertain, partial, and
conflicting beliefs from multiple independent sources.

---

## Why Dempster-Shafer?

Standard probabilistic fusion (e.g., Bayesian) requires a shared prior
and assumes all agents reason over the same probability space. In a
heterogeneous multi-agent system, this assumption fails:

- Agent A (ML-based) outputs class probabilities from training data
- Agent B (rule-based expert system) outputs confidence scores from audit logs
- Agent C (causal model) reasons over intervention probabilities

DS theory provides a principled framework that:

1. **Preserves agent diversity** — each agent's belief mass is maintained
2. **Quantifies conflict** — inter-agent disagreement K is a diagnostic
   signal in itself (high K = genuinely ambiguous incident)
3. **Produces uncertainty intervals** [Bel(A), Pl(A)] rather than point
   estimates — essential for auditable, explainable systems
4. **Requires no prior** — agents contribute evidence, not posteriors

---

## Scenario

Two agents analyse a network incident (latency spike + CPU spike on a router):

| Agent | Type | Hypotheses | Confidence |
|---|---|---|---|
| **Agent A** | ML anomaly detector | DDoS (0.50), Hardware Failure (0.25) | High on DDoS |
| **Agent B** | Rule-based expert | Config Error (0.40), Normal (0.30) | High on Config |

The agents are in **partial conflict** — A suspects an attack, B suspects
a configuration issue. DS combination fuses their beliefs and produces a
normalised posterior over all hypotheses.

---

## Results

```
Agent A (ML detector):
  m({DDoS})                    = 0.5000
  m({Hardware_Failure})        = 0.2500
  m({DDoS, Hardware_Failure})  = 0.1500
  m(Θ)                         = 0.1000

Agent B (Expert system):
  m({Config_Error})            = 0.4000
  m({Normal})                  = 0.3000
  m({Config_Error, Normal})    = 0.2000
  m(Θ)                         = 0.1000

Conflict K = 0.5750  (moderate disagreement)

Fused Belief:
  m({DDoS})                    = 0.2353
  m({Hardware_Failure})        = 0.0588
  m({Config_Error})            = 0.2353
  m({Normal})                  = 0.1765
  ...

Uncertainty intervals [Bel(A), Pl(A)]:
  DDoS            [0.235, 0.471]  width=0.235
  Config_Error    [0.235, 0.471]  width=0.235
  Normal          [0.176, 0.412]  width=0.235
  Hardware_Failure[0.059, 0.294]  width=0.235
```

**Key finding:** After fusion, DDoS and Config_Error are equally
supported (m = 0.235). The moderate conflict (K = 0.575) signals
genuine diagnostic ambiguity — neither agent alone has sufficient
evidence. This is the correct output: the system should escalate
rather than commit to a single diagnosis.

![Dempster-Shafer Fusion](results/dempster_shafer_fusion.png)

---

## Thesis Implications

**Verrou 3 — Formal arbitration under disagreement:**
DS combination provides a tractable arbitration mechanism that preserves
agent diversity and quantifies conflict as an explicit output — directly
enabling the explainability requirements of the target thesis.

**Verrou 2 — Uncertainty intervals as semantic contracts:**
The [Bel(A), Pl(A)] output is richer than a probability estimate — it
encodes what is *known* (belief) vs what is *possible* (plausibility),
enabling formal reasoning over agent agreement and disagreement.

**Open question for the thesis:**
DS theory is defined for static evidence. Extending it to **online /
streaming settings** — where agent beliefs must be updated incrementally
as new observations arrive — is one of the core research axes. Dynamic
DS (Dezert-Smarandache) and contextual discounting are candidate
extensions.

---

## Quickstart

```bash
git clone https://github.com/moncefabel/belief-fusion-diagnosis
cd belief-fusion-diagnosis
pip install numpy matplotlib seaborn
python dempster_shafer_fusion.py
```

No heavy dependencies — pure Python + numpy. Runs in under 5 seconds.

---

## Repository Structure

```
belief-fusion-diagnosis/
├── dempster_shafer_fusion.py   # BPA, combination rule, scenario, plots
├── results/
│   └── dempster_shafer_fusion.png
├── RESEARCH_NOTES.md
└── README.md
```

---

## Connection to stream-anomaly-benchmark

This project is the formal reasoning companion to
[stream-anomaly-benchmark](https://github.com/moncefabel/stream-anomaly-benchmark).

The benchmark addresses **when** to trigger a decision (trilemma).
This project addresses **how** to arbitrate **between** conflicting
agent decisions once triggered.

Together they prototype the two core coordination problems in
heterogeneous multi-agent incident diagnosis.

---

## References

- Shafer, G. (1976). *A Mathematical Theory of Evidence*. Princeton University Press.
- Dempster, A. P. (1967). Upper and lower probabilities induced by a
  multivalued mapping. *Annals of Mathematical Statistics*, 38(2), 325–339.
- Tailhardat, L. et al. (2023). NORIA-O: an Ontology for Anomaly Detection
  and Incident Management in ICT Systems. *ESWC 2023*.
- Achenchabe, Y., Bondu, A., et al. (2021). Early Classification of Time
  Series. *Machine Learning*, 110, 1481–1517.

---

## Author

**Moncef Bouhabel** — ML Engineer, Master ML for Data Science, Université Paris Cité
[github.com/moncefabel](https://github.com/moncefabel)