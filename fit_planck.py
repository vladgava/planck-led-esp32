"""Fit Planck's constant from LED forward voltages measured at 1 mA.

Model: e*V = h*c/lambda + const  ->  V = (h*c/e) * (1/lambda) + b
Usage: python fit_planck.py [--lang en|ro]
"""
import argparse
import csv
from collections import OrderedDict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

E = 1.602176634e-19      # C
C = 299792458.0          # m/s
H_REF = 6.62607015e-34   # J*s
T95_DOF2 = 4.303         # Student t, 95 % two-sided, 2 degrees of freedom (4 points)

LABELS = {
    "en": dict(names={"red": "Red", "yellow": "Yellow", "green": "Green", "blue": "Blue"},
               x="1/λ [μm⁻¹]  (nominal λ from datasheets, not measured)",
               y="LED voltage at 1 mA [V]",
               title="Planck's constant from four LEDs, measured with an ESP32",
               fit="Linear fit: h = {h:.2f}·10⁻³⁴ J·s", out="planck_fit.png"),
    "ro": dict(names={"red": "Roșu", "yellow": "Galben", "green": "Verde", "blue": "Albastru"},
               x="1/λ [μm⁻¹]  (λ tipic din fișe, nemăsurat)",
               y="Tensiunea LED la 1 mA [V]",
               title="Constanta lui Planck din patru LED-uri, măsurată cu ESP32",
               fit="Fit liniar: h = {h:.2f}·10⁻³⁴ J·s", out="planck_fit_ro.png"),
}
COLORS = {"red": "#d62728", "yellow": "#e0a800", "green": "#2ca02c", "blue": "#1f4fd8"}
OFFSETS = {"red": (8, -14), "yellow": (8, -14), "green": (-52, 6), "blue": (-8, -18)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=LABELS, default="en")
    L = LABELS[ap.parse_args().lang]

    root = Path(__file__).resolve().parent.parent
    runs, lam_nm = OrderedDict(), {}
    with open(root / "data" / "vled_at_1mA.csv") as f:
        for r in csv.DictReader(f):
            runs.setdefault(r["led"], []).append(float(r["v_mV"]) / 1000)
            lam_nm[r["led"]] = float(r["wavelength_nm_assumed"])

    leds = list(runs)
    V = np.array([np.mean(runs[k]) for k in leds])
    spread_mV = [(max(runs[k]) - min(runs[k])) * 1000 for k in leds]
    x = np.array([1 / (lam_nm[k] * 1e-9) for k in leds])          # 1/m

    (slope, icpt), cov = np.polyfit(x, V, 1, cov=True)
    h = slope * E / C
    se = np.sqrt(cov[0, 0]) * E / C
    print(f"h = {h:.3e} J*s  (fit s.e. {se:.2e}, {se / h * 100:.0f} %)")
    print(f"deviation from {H_REF:.3e}: {(h / H_REF - 1) * 100:+.1f} %, "
          f"{(h - H_REF) / se:.1f} sigma")
    print(f"95 % interval (t, 2 dof): +-{T95_DOF2 * se:.2e}")
    print(f"intercept {icpt:.3f} V; residuals (mV): "
          + ", ".join(f"{k} {(v - (slope * xi + icpt)) * 1000:+.0f}"
                      for k, v, xi in zip(leds, V, x)))
    print("run-to-run range (mV): "
          + ", ".join(f"{k} {s:.0f}" for k, s in zip(leds, spread_mV)))

    rng = np.random.default_rng(1)
    lam = np.array([lam_nm[k] for k in leds]) * 1e-9
    mc = [np.polyfit(1 / (lam + rng.normal(0, 10e-9, len(leds))),
                     V + rng.normal(0, 0.010, len(leds)), 1)[0] * E / C
          for _ in range(20000)]
    print(f"Monte Carlo (sigma_lambda 10 nm, sigma_V 10 mV): sd {np.std(mc):.2e}")
    for g in (0.97, 1.03):
        print(f"ADC gain {g}: h = {np.polyfit(x, V * g, 1)[0] * E / C:.2e}")

    fig, ax = plt.subplots(figsize=(7, 4.6), dpi=200)
    xs = np.linspace(x.min() * 0.97, x.max() * 1.03, 50)
    ax.plot(xs / 1e6, slope * xs + icpt, color="#c8372d", lw=1.6, ls="--",
            label=L["fit"].format(h=h * 1e34))
    for k, v, xi in zip(leds, V, x):
        ax.plot(xi / 1e6, v, "o", color=COLORS[k], ms=9)
        ax.annotate(L["names"][k], (xi / 1e6, v), textcoords="offset points",
                    xytext=OFFSETS[k], fontsize=9, color="#333")
    ax.set_xlabel(L["x"]); ax.set_ylabel(L["y"]); ax.set_title(L["title"], fontsize=11)
    ax.grid(alpha=.3); ax.legend(frameon=False)
    fig.tight_layout()
    out = root / "figures" / L["out"]
    fig.savefig(out)
    print("saved", out)


if __name__ == "__main__":
    main()
