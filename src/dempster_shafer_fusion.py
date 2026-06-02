"""
dempster_shafer_fusion.py
--------------------------
Belief fusion for heterogeneous agent diagnostics using Dempster-Shafer theory.

Scenario: Two agents analyse a network incident and produce conflicting
diagnostic hypotheses with different confidence levels. The DS combination
rule fuses their beliefs without erasing the diversity of their assessments.

This directly prototypes Verrou 3 of the CIFRE thesis (ref. 2026-51517):
"When heterogeneous agents produce contradictory diagnostics, what formal
mechanism arbitrates without erasing model diversity?"

Reference: Dempster (1967), Shafer (1976) — A Mathematical Theory of Evidence.
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from itertools import chain, combinations

sns.set_theme(style="whitegrid", font_scale=1.1)


#  Frame of Discernment 

# Possible diagnoses for a network incident
FRAME = frozenset(["DDoS", "Hardware_Failure", "Config_Error", "Normal"])


def powerset(s: frozenset) -> list[frozenset]:
    """All non-empty subsets of the frame of discernment."""
    lst = list(s)
    return [
        frozenset(c)
        for r in range(1, len(lst) + 1)
        for c in combinations(lst, r)
    ]


#  Basic Probability Assignment (BPA) 

class BPA:
    """
    Basic Probability Assignment (mass function) for Dempster-Shafer theory.

    m: 2^Θ → [0,1] such that Σ m(A) = 1 for all A ⊆ Θ, A ≠ ∅
    """

    def __init__(self, masses: dict[frozenset, float], name: str = ""):
        total = sum(masses.values())
        assert abs(total - 1.0) < 1e-6, f"Masses must sum to 1, got {total:.4f}"
        self.masses = masses
        self.name   = name

    def belief(self, A: frozenset) -> float:
        """Bel(A) = Σ m(B) for all B ⊆ A, B ≠ ∅"""
        return sum(m for B, m in self.masses.items() if B.issubset(A))

    def plausibility(self, A: frozenset) -> float:
        """Pl(A) = Σ m(B) for all B ∩ A ≠ ∅"""
        return sum(m for B, m in self.masses.items() if B & A)

    def uncertainty_interval(self, A: frozenset) -> tuple[float, float]:
        """[Bel(A), Pl(A)] — the uncertainty interval."""
        return self.belief(A), self.plausibility(A)

    def __repr__(self) -> str:
        lines = [f"BPA({self.name}):"]
        for A, m in sorted(self.masses.items(), key=lambda x: -x[1]):
            if m > 1e-6:
                label = "{" + ", ".join(sorted(A)) + "}"
                lines.append(f"  m({label}) = {m:.4f}")
        return "\n".join(lines)


#  Dempster Combination Rule 

def dempster_combine(bpa1: BPA, bpa2: BPA, name: str = "Combined") -> BPA:
    """
    Dempster's orthogonal sum: (m1 ⊕ m2)(A) = K^{-1} * Σ m1(B)*m2(C) for B∩C=A

    K = 1 - Σ m1(B)*m2(C) for B∩C=∅  (normalisation constant)

    A high conflict K close to 0 signals that the agents are in strong
    disagreement — an important diagnostic signal in itself.
    """
    combined: dict[frozenset, float] = {}
    conflict = 0.0

    for A1, m1 in bpa1.masses.items():
        for A2, m2 in bpa2.masses.items():
            intersection = A1 & A2
            if not intersection:
                conflict += m1 * m2
            else:
                combined[intersection] = combined.get(intersection, 0.0) + m1 * m2

    if abs(1.0 - conflict) < 1e-9:
        raise ValueError(
            f"Complete conflict between {bpa1.name} and {bpa2.name}. "
            "Agents are fully contradictory — cannot combine."
        )

    K = 1.0 - conflict
    normalised = {A: m / K for A, m in combined.items()}

    print(f"\n  Conflict K = {conflict:.4f}  "
          f"({'low' if conflict < 0.3 else 'moderate' if conflict < 0.6 else 'HIGH'} disagreement)")
    print(f"  Normalisation factor = {K:.4f}")

    return BPA(normalised, name=name)


#  Scenario 

def run_scenario() -> None:
    """
    Network incident diagnostic scenario.

    Context: A spike in latency + CPU usage is observed on a router.

    Agent A (ML-based anomaly detector):
      - Trained on traffic patterns
      - Confident it's DDoS or Hardware failure
      - Some residual uncertainty over the full frame

    Agent B (Rule-based expert system):
      - Uses configuration audit logs
      - Suspects Config_Error or Normal (false alarm)
      - Less certain about Hardware failure

    Question: How do we formally fuse their beliefs?
    """

    print("=" * 60)
    print("  DEMPSTER-SHAFER BELIEF FUSION")
    print("  Heterogeneous Agent Diagnostic Arbitration")
    print("=" * 60)

    # Agent A: ML anomaly detector
    agent_A = BPA({
        frozenset(["DDoS"]):                          0.50,
        frozenset(["Hardware_Failure"]):               0.25,
        frozenset(["DDoS", "Hardware_Failure"]):       0.15,
        FRAME:                                         0.10,  # total ignorance
    }, name="Agent-A (ML detector)")

    # Agent B: Rule-based expert system
    agent_B = BPA({
        frozenset(["Config_Error"]):                   0.40,
        frozenset(["Normal"]):                         0.30,
        frozenset(["Config_Error", "Normal"]):         0.20,
        FRAME:                                         0.10,
    }, name="Agent-B (Expert system)")

    print(f"\n{agent_A}")
    print(f"\n{agent_B}")

    # Combine
    print("\n--- Dempster Combination ---")
    combined = dempster_combine(agent_A, agent_B, name="Fused Belief")
    print(f"\n{combined}")

    # Print uncertainty intervals for key hypotheses
    print("\n--- Uncertainty Intervals [Bel(A), Pl(A)] ---")
    for hyp in sorted(FRAME):
        A   = frozenset([hyp])
        bel = combined.belief(A)
        pl  = combined.plausibility(A)
        print(f"  {hyp:<20}  [{bel:.3f}, {pl:.3f}]  width={pl-bel:.3f}")

    # Most supported hypothesis
    singletons = {frozenset([h]): combined.masses.get(frozenset([h]), 0.0)
                  for h in FRAME}
    best = max(singletons, key=singletons.get)
    print(f"\n  → Most supported diagnosis: {list(best)[0]} "
          f"(m = {singletons[best]:.4f})")

    return agent_A, agent_B, combined


#  Visualisation 

def plot_fusion(agent_A: BPA, agent_B: BPA, combined: BPA) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        "Dempster-Shafer Belief Fusion\n"
        "Heterogeneous Agent Diagnostic Arbitration",
        fontsize=13, fontweight="bold"
    )

    colors = {"DDoS": "#DC2626", "Hardware_Failure": "#F97316",
              "Config_Error": "#2563EB", "Normal": "#059669",
              "Mixed/Ignorance": "#9CA3AF"}

    def plot_bpa(ax, bpa, title):
        labels, vals, clrs = [], [], []
        for A, m in sorted(bpa.masses.items(), key=lambda x: -x[1]):
            if m < 1e-4:
                continue
            if len(A) == 1:
                lbl = list(A)[0]
                clr = colors.get(lbl, "#6B7280")
            else:
                lbl = "{" + ", ".join(sorted(A)[:2]) + (",...}" if len(A) > 2 else "}")
                clr = colors["Mixed/Ignorance"]
            labels.append(lbl)
            vals.append(m)
            clrs.append(clr)

        bars = ax.barh(labels, vals, color=clrs, alpha=0.85)
        ax.bar_label(bars, fmt="%.3f", fontsize=10, padding=3)
        ax.set_xlim(0, 0.75)
        ax.set_xlabel("Mass m(A)", fontsize=10)
        ax.set_title(title, fontweight="bold", fontsize=11)
        ax.grid(axis="x", alpha=0.3)

    plot_bpa(axes[0], agent_A,  "Agent A — ML Detector")
    plot_bpa(axes[1], agent_B,  "Agent B — Expert System")
    plot_bpa(axes[2], combined, "Fused Belief (DS Combination)")

    # Add uncertainty interval annotation on combined plot
    ax = axes[2]
    for i, hyp in enumerate(["DDoS", "Hardware_Failure", "Config_Error", "Normal"]):
        A   = frozenset([hyp])
        bel = combined.belief(A)
        pl  = combined.plausibility(A)
        if pl > 0.01:
            ax.annotate(
                f"[{bel:.2f},{pl:.2f}]",
                xy=(pl, hyp), xytext=(pl + 0.02, hyp),
                fontsize=7, color="gray", va="center",
            )

    plt.tight_layout()
    out = "dempster_shafer_fusion.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"\nFigure saved: {out}")
    plt.show()
    plt.close()


#  Conflict analysis 

def analyse_conflict_range() -> None:
    """
    Show how DS fusion behaves across a range of agent confidence levels.
    Key insight: high inter-agent conflict is itself a diagnostic signal
    — it means the situation is genuinely ambiguous.
    """
    print("\n--- Conflict Analysis ---")
    print("Varying Agent A's DDoS confidence from 0.1 to 0.9:\n")
    print(f"  {'DDoS conf':>10}  {'Conflict K':>12}  {'Fused DDoS mass':>16}")

    for conf in np.arange(0.1, 1.0, 0.1):
        try:
            A = BPA({
                frozenset(["DDoS"]):        round(conf, 1),
                frozenset(["Hardware_Failure"]): round(0.5 - conf/2, 2),
                FRAME:                       round(0.5 - conf/2, 2),
            }, name="A")
            B = BPA({
                frozenset(["Config_Error"]): 0.50,
                frozenset(["Normal"]):       0.30,
                FRAME:                       0.20,
            }, name="B")
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                fused = dempster_combine(A, B)
            conflict_line = [l for l in buf.getvalue().split("\n") if "Conflict" in l][0]
            k = float(conflict_line.split("=")[1].split()[0])
            ddos_mass = fused.masses.get(frozenset(["DDoS"]), 0.0)
            print(f"  {conf:>10.1f}  {k:>12.4f}  {ddos_mass:>16.4f}")
        except Exception:
            print(f"  {conf:>10.1f}  {'complete':>12}  {'N/A':>16}")


#  Main 

if __name__ == "__main__":
    agent_A, agent_B, combined = run_scenario()
    plot_fusion(agent_A, agent_B, combined)
    analyse_conflict_range()

    print("\n" + "="*60)
    print("  THESIS CONNECTION")
    print("="*60)
    print("""
  Verrou 3 — Belief Fusion & Arbitration Under Disagreement:

  This prototype shows that DS theory provides a principled
  framework for fusing heterogeneous agent diagnostics:

  1. The combination rule preserves each agent's individual
     contribution — no agent's belief is simply overridden.

  2. The conflict measure K quantifies inter-agent disagreement
     — high conflict is itself a diagnostic signal (ambiguous
     incident that neither agent can resolve alone).

  3. Uncertainty intervals [Bel(A), Pl(A)] provide a richer
     representation than a single probability — essential for
     auditable, explainable systems (Verrou 2).

  Open question for the thesis: how to update BPAs dynamically
  as new evidence arrives from the stream? DS is defined for
  static evidence — extending it to online/streaming settings
  is one of the thesis research axes.
    """)