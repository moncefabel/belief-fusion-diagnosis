"""
dsmt_comparison.py
------------------
DS vs PCR5 comparison for high-conflict agent scenarios.
Run from src/: python dsmt_comparison.py
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dempster_shafer_fusion import BPA, dempster_combine, FRAME
import io, contextlib

sns.set_theme(style="whitegrid", font_scale=1.1)
RESULTS = "../results"


# ── PCR5 ──────────────────────────────────────────────────────────────────────

def pcr5_combine(bpa1: BPA, bpa2: BPA, name: str = "PCR5") -> tuple:
    """
    PCR5 — Proportional Conflict Redistribution rule 5.
    For each conflicting pair (A1, A2): redistribute conflict mass back
    proportionally to m1(A1) and m2(A2).
    """
    combined: dict[frozenset, float] = {}
    conflicts = []
    conflict_total = 0.0

    for A1, m1 in bpa1.masses.items():
        for A2, m2 in bpa2.masses.items():
            inter = A1 & A2
            if not inter:
                conflicts.append((A1, A2, m1 * m2))
                conflict_total += m1 * m2
            else:
                combined[inter] = combined.get(inter, 0.0) + m1 * m2

    for A1, A2, cm in conflicts:
        m1_A1 = bpa1.masses.get(A1, 0.0)
        m2_A2 = bpa2.masses.get(A2, 0.0)
        denom = m1_A1 + m2_A2
        if denom > 1e-10:
            combined[A1] = combined.get(A1, 0.0) + cm * m1_A1 / denom
            combined[A2] = combined.get(A2, 0.0) + cm * m2_A2 / denom

    total = sum(combined.values())
    return BPA({A: m / total for A, m in combined.items()}, name=name), conflict_total


# ── Comparison ────────────────────────────────────────────────────────────────

def run_comparison(agent_A: BPA, agent_B: BPA) -> dict:
    print("=" * 60)
    print("  DS vs PCR5 — High Conflict Scenario")
    print("=" * 60)

    # DS
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ds = dempster_combine(agent_A, agent_B, name="DS")
    k_line = [l for l in buf.getvalue().split("\n") if "Conflict K" in l][0]
    k = float(k_line.split("=")[1].split()[0])

    # PCR5
    pcr5, conflict = pcr5_combine(agent_A, agent_B, name="PCR5")

    print(f"\nConflict K = {k:.4f} (same for both rules)")

    hyps = sorted(FRAME)
    print(f"\n{'Hypothesis':<22} {'DS':>8} {'PCR5':>8} {'Delta':>8}")
    print("-" * 50)
    for hyp in hyps:
        A  = frozenset([hyp])
        ds_m   = ds.masses.get(A, 0)
        pcr_m  = pcr5.masses.get(A, 0)
        delta  = pcr_m - ds_m
        print(f"  {hyp:<20}  {ds_m:>8.4f}  {pcr_m:>8.4f}  {delta:>+8.4f}")

    best_ds   = max(hyps, key=lambda h: ds.masses.get(frozenset([h]), 0))
    best_pcr5 = max(hyps, key=lambda h: pcr5.masses.get(frozenset([h]), 0))
    print(f"\n  DS   best: {best_ds}")
    print(f"  PCR5 best: {best_pcr5}")

    return {"DS": ds, "PCR5": pcr5, "K": k}


def plot_comparison(results: dict) -> None:
    hyps   = sorted(FRAME)
    colors = {"DS": "#DC2626", "PCR5": "#2563EB"}
    x = np.arange(len(hyps))
    w = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))

    for i, method in enumerate(["DS", "PCR5"]):
        bpa  = results[method]
        vals = [bpa.masses.get(frozenset([h]), 0) for h in hyps]
        bars = ax.bar(x + (i - 0.5) * w, vals, w,
                      label=method, color=colors[method], alpha=0.85)
        ax.bar_label(bars, fmt="%.3f", fontsize=9, padding=2)

    ax.set_xticks(x)
    ax.set_xticklabels(hyps, fontsize=11)
    ax.set_ylabel("Mass m(A)", fontsize=11)
    ax.set_ylim(0, 0.55)
    ax.set_title(
        f"DS vs PCR5 — K = {results['K']:.2f} (HIGH conflict)\n"
        "PCR5 redistributes conflict proportionally — more conservative",
        fontsize=12, fontweight="bold"
    )
    ax.axhline(0.30, color="gray", ls="--", lw=1, alpha=0.5)
    ax.text(3.55, 0.31, "Zadeh risk zone", fontsize=8, color="gray")
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out = f"{RESULTS}/dsmt_comparison.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"\nFigure saved: {out}")
    plt.close()


if __name__ == "__main__":
    agent_A = BPA({
        frozenset(["DDoS"]):                     0.50,
        frozenset(["Hardware_Failure"]):          0.25,
        frozenset(["DDoS", "Hardware_Failure"]):  0.15,
        FRAME:                                    0.10,
    }, name="Agent-A")

    agent_B = BPA({
        frozenset(["Config_Error"]):              0.40,
        frozenset(["Normal"]):                    0.30,
        frozenset(["Config_Error", "Normal"]):    0.20,
        FRAME:                                    0.10,
    }, name="Agent-B")

    results = run_comparison(agent_A, agent_B)
    plot_comparison(results)

    print("""
Thesis implication:
  K < 0.5  → DS appropriate (low conflict)
  K > 0.7  → PCR5 preferred (avoid Zadeh paradox)
  Adaptive rule selection based on K is a thesis research axis.
""")