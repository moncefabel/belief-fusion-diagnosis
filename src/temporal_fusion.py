"""
temporal_fusion.py
------------------
Sequential belief fusion — how fused beliefs evolve as evidence arrives.
Run from src/: python temporal_fusion.py
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io, contextlib
from dempster_shafer_fusion import BPA, dempster_combine, FRAME

sns.set_theme(style="whitegrid", font_scale=1.1)
RESULTS = "../results"
HYPS    = sorted(FRAME)


#  Stream definition 

STREAM = [
    {
        "desc": "t=0 — CPU spike detected",
        "A": {frozenset(["DDoS"]): 0.30, frozenset(["Hardware_Failure"]): 0.20, FRAME: 0.50},
        "B": {frozenset(["Config_Error"]): 0.25, frozenset(["Normal"]): 0.35, FRAME: 0.40},
    },
    {
        "desc": "t=1 — Latency spike added",
        "A": {frozenset(["DDoS"]): 0.40, frozenset(["Hardware_Failure"]): 0.20,
              frozenset(["DDoS", "Hardware_Failure"]): 0.20, FRAME: 0.20},
        "B": {frozenset(["Config_Error"]): 0.30, frozenset(["Normal"]): 0.25,
              frozenset(["Config_Error", "Normal"]): 0.25, FRAME: 0.20},
    },
    {
        "desc": "t=2 — Packet drop detected",
        "A": {frozenset(["DDoS"]): 0.50, frozenset(["Hardware_Failure"]): 0.20,
              frozenset(["DDoS", "Hardware_Failure"]): 0.15, FRAME: 0.15},
        "B": {frozenset(["Config_Error"]): 0.35, frozenset(["Normal"]): 0.15,
              frozenset(["Config_Error", "Normal"]): 0.30, FRAME: 0.20},
    },
    {
        "desc": "t=3 — Config audit: recent change found",
        "A": {frozenset(["DDoS"]): 0.45, frozenset(["Hardware_Failure"]): 0.25,
              frozenset(["DDoS", "Hardware_Failure"]): 0.15, FRAME: 0.15},
        "B": {frozenset(["Config_Error"]): 0.55, frozenset(["Normal"]): 0.10,
              frozenset(["Config_Error", "Normal"]): 0.20, FRAME: 0.15},
    },
    {
        "desc": "t=4 — Threat intel confirms DDoS signature",
        "A": {frozenset(["DDoS"]): 0.65, frozenset(["Hardware_Failure"]): 0.15,
              frozenset(["DDoS", "Hardware_Failure"]): 0.10, FRAME: 0.10},
        "B": {frozenset(["Config_Error"]): 0.40, frozenset(["Normal"]): 0.05,
              frozenset(["Config_Error", "Normal"]): 0.35, FRAME: 0.20},
    },
]


#  Run 

def run_stream() -> list[dict]:
    history = []

    print("=" * 65)
    print("  TEMPORAL BELIEF FUSION")
    print("=" * 65)

    for t, step in enumerate(STREAM):
        A = BPA(step["A"], name=f"A-t{t}")
        B = BPA(step["B"], name=f"B-t{t}")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fused = dempster_combine(A, B, name=f"Fused-t{t}")
        k_line = [l for l in buf.getvalue().split("\n") if "Conflict K" in l][0]
        k = float(k_line.split("=")[1].split()[0])

        best = max(HYPS, key=lambda h: fused.masses.get(frozenset([h]), 0))

        row = {"t": t, "desc": step["desc"], "K": k, "best": best}
        for hyp in HYPS:
            h = frozenset([hyp])
            row[f"m_{hyp}"]   = fused.masses.get(h, 0)
            row[f"bel_{hyp}"] = fused.belief(h)
            row[f"pl_{hyp}"]  = fused.plausibility(h)

        history.append(row)

        print(f"\n  {step['desc']}")
        print(f"  K = {k:.3f}  |  Best → {best} "
              f"(m = {fused.masses.get(frozenset([best]),0):.3f})")
        for hyp in HYPS:
            h = frozenset([hyp])
            print(f"    {hyp:<20}  "
                  f"m={fused.masses.get(h,0):.3f}  "
                  f"[{fused.belief(h):.3f}, {fused.plausibility(h):.3f}]")

    return history


#  Plot 

def plot_temporal(history: list[dict]) -> None:
    colors = {
        "DDoS":             "#DC2626",
        "Hardware_Failure": "#F97316",
        "Config_Error":     "#2563EB",
        "Normal":           "#059669",
    }
    ts    = [r["t"]    for r in history]
    ks    = [r["K"]    for r in history]
    bests = [r["best"] for r in history]
    descs = [r["desc"].split("—")[1].strip()[:22] for r in history]

    fig, axes = plt.subplots(2, 1, figsize=(11, 9))
    fig.suptitle(
        "Temporal Belief Fusion — Sequential Evidence Integration\n"
        "Fused beliefs evolve as new network observations arrive",
        fontsize=13, fontweight="bold"
    )

    # Panel 1: mass evolution
    ax = axes[0]
    for hyp in HYPS:
        ms   = [r[f"m_{hyp}"]   for r in history]
        bels = [r[f"bel_{hyp}"] for r in history]
        pls  = [r[f"pl_{hyp}"]  for r in history]
        ax.plot(ts, ms, marker="o", lw=2.2,
                color=colors[hyp], label=hyp)
        ax.fill_between(ts, bels, pls,
                        alpha=0.10, color=colors[hyp])

    ax.set_ylabel("Mass m(A)  [shaded: Bel–Pl interval]", fontsize=10)
    ax.set_title("Fused Belief per Hypothesis", fontweight="bold")
    ax.legend(fontsize=10, loc="upper left")
    ax.set_xticks(ts)
    ax.set_xticklabels([f"t={t}\n{d}" for t, d in zip(ts, descs)], fontsize=8)
    ax.set_ylim(0, 0.85)
    ax.grid(alpha=0.3)

    # Panel 2: conflict K
    ax = axes[1]
    ax.plot(ts, ks, marker="s", lw=2.5, color="#7C3AED", label="Conflict K")
    ax.fill_between(ts, 0, ks, alpha=0.15, color="#7C3AED")
    ax.axhline(0.7, color="red",    ls="--", lw=1.2, alpha=0.7, label="Zadeh risk (K=0.7)")
    ax.axhline(0.5, color="orange", ls="--", lw=1.0, alpha=0.6, label="Moderate conflict")

    for t, k, best in zip(ts, ks, bests):
        ax.annotate(f"→{best}", (t, k),
                    xytext=(0, 12), textcoords="offset points",
                    fontsize=8, ha="center", color=colors.get(best, "black"))

    ax.set_ylabel("Inter-agent Conflict K", fontsize=10)
    ax.set_xlabel("Timestep", fontsize=10)
    ax.set_title("Conflict K(t) — Signal of Diagnostic Maturity",
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xticks(ts)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    out = f"{RESULTS}/temporal_fusion.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"\nFigure saved: {out}")
    plt.close()


#  Main 

if __name__ == "__main__":
    history = run_stream()
    plot_temporal(history)

    final = history[-1]
    print(f"""
Key findings:
  Final best diagnosis : {final['best']}
  Final conflict K     : {final['K']:.3f}
  DDoS mass trajectory : {[round(r['m_DDoS'],3) for r in history]}

K(t) as self-organisation signal:
  K > 0.7  →  defer decision, request more evidence
  K < 0.3  →  agents converge, safe to commit
  → Directly addresses Verrou 4 (self-organisation under time constraints)
""")