"""Render the finance mechanism figure from the supplied aggregate data."""

from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
INPUT_HASHES = {
    "finance_figure_pool_B_candidates.csv": "9f16917a405d0f70b4f08754dcf6800175969fbdb81f2fbedc83cea3ea45ce26",
    "finance_figure_pool_B_deciles.csv": "40b2f8082fadeb0323741374e560ae04a32f231ad09f0e34318ae13c80ee5c57",
    "finance_figure_rank_bins.csv": "6d636b8b861c6a0e664c23443f6f58242e869feaf152e5850c0f8c7253691e22",
    "finance_figure_rank_gradient_16_32.csv": "9e4980a0a6cbc86d5096027683999f5470d42402a1f5c82bdd9feec4b178234e",
}


def read_inputs():
    manifest_path = ROOT / "data" / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    tables = {}
    for name, expected in INPUT_HASHES.items():
        path = ROOT / "data" / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Input hash differs for {name}.")
        if name in manifest:
            entry = manifest[name]
            bound_hash = entry["sha256"] if isinstance(entry, dict) else entry
            if actual != bound_hash:
                raise ValueError(f"Manifest hash differs for {name}.")
        tables[name] = np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding="utf-8")
    return tables


def render():
    tables = read_inputs()
    bins = tables["finance_figure_rank_bins.csv"]
    candidates = tables["finance_figure_pool_B_candidates.csv"]
    deciles = tables["finance_figure_pool_B_deciles.csv"]
    gradient = tables["finance_figure_rank_gradient_16_32.csv"]
    if (len(bins), len(candidates), len(deciles), len(gradient)) != (60, 1500, 10, 2998):
        raise ValueError("The figure input row counts differ.")

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5,
        "axes.labelsize": 8.5, "axes.titlesize": 8.5,
        "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "axes.linewidth": 0.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.unicode_minus": True,
    })
    blue, orange, green = "#0072B2", "#D55E00", "#009E73"
    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.7))
    fig.subplots_adjust(left=0.105, right=0.975, bottom=0.26, top=0.78, wspace=0.62)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#E3E3E3", linewidth=0.45)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 50, 100])
        ax.set_xlabel("Proxy-score\npercentile", labelpad=4)
        ax.tick_params(pad=2)

    ax = axes[0]
    for budget, color, style, marker in [(1, green, ":", "o"), (4, blue, "--", "s"), (32, orange, "-", "^")]:
        rows = bins[bins["N"] == budget]
        if not np.isclose(rows["selection_probability"].sum(), 1.0, atol=1e-14):
            raise ValueError(f"Winner probabilities do not sum to one for N={budget}.")
        ax.plot(rows["rank_percentile_midpoint"], rows["selection_probability"],
                color=color, linestyle=style, marker=marker, markersize=2.6,
                linewidth=1.1, label=f"N = {budget}")
    ax.set_title("(a) Winner probabilities\n1,500-candidate pool", loc="left", pad=10)
    ax.set_ylabel("Probability per\n5-percentile bin", labelpad=4)
    ax.set_ylim(-0.015, 0.86)
    ax.set_yticks([0, 0.4, 0.8])
    ax.legend(loc="upper left", frameon=False, borderpad=0, handlelength=1.8,
              handletextpad=0.5, labelspacing=0.5)

    ax = axes[1]
    ax.scatter(candidates["gross_score_rank_percentile"],
               candidates["capacity_component_signed_sharpe_gap"],
               color=blue, s=2.5, alpha=0.28, linewidths=0)
    x = deciles["rank_percentile_midpoint"]
    ax.vlines(x, deciles["q25_signed_sharpe_gap"], deciles["q75_signed_sharpe_gap"],
              color="black", linewidth=1)
    for field in ["q25_signed_sharpe_gap", "q75_signed_sharpe_gap"]:
        ax.hlines(deciles[field], x - 1.4, x + 1.4, color="black", linewidth=0.8)
    ax.plot(x, deciles["mean_signed_sharpe_gap"], "o", color="black", markersize=3.1)
    ax.set_title("(b) Capacity component\nPool B, USD 500 million", loc="left", pad=10)
    ax.set_ylabel("Capacity component\n(signed Sharpe gap)", labelpad=4)
    ax.set_ylim(0, 4.15)
    ax.set_yticks([0, 2, 4])
    ax.text(0.04, 0.94, "1,500 candidates", transform=ax.transAxes, va="top", fontsize=8)
    ax.text(0.04, 0.81, "Decile mean\nand quartiles", transform=ax.transAxes,
            va="top", fontsize=8, linespacing=1.25)

    ax = axes[2]
    for pool, label, color, style, marker in [
        ("B", "Pool B", blue, "-", "o"),
        ("TER1", "Least-liquid\ntercile", orange, "--", "s"),
    ]:
        rows = gradient[gradient["pool"] == pool]
        rows = np.sort(rows, order="cut_rank")
        if len(rows) != 1499 or not np.all(rows["N1"] == 16) or not np.all(rows["N2"] == 32):
            raise ValueError(f"The rank-gradient grid differs for {pool}.")
        if not np.allclose(np.cumsum(rows["contribution"]), rows["cumulative"], atol=1e-12, rtol=0):
            raise ValueError(f"The cumulative rank-gradient terms differ for {pool}.")
        total = float(rows["total"][-1])
        if not np.isclose(rows["cumulative"][-1], total, atol=1e-12, rtol=0):
            raise ValueError(f"The rank-gradient endpoint differs for {pool}.")
        ax.plot(np.r_[0, rows["cut_percentile"]], np.r_[0, rows["cumulative"]],
                color=color, linestyle=style, linewidth=0.8,
                label=f"{label}\n{total:+.4f}")
        ax.plot(rows["cut_percentile"][-1], rows["cumulative"][-1],
                marker=marker, color=color, markersize=3.3, clip_on=False)
    ax.axhline(0, color="#777777", linewidth=0.6, zorder=1)
    ax.set_title("(c) Cumulative terms\n16 to 32 trials", loc="left", pad=10)
    ax.set_ylabel("Cumulative change\n(capacity component)", labelpad=4)
    ax.set_ylim(-0.24, 0.54)
    ax.set_yticks([-0.2, 0, 0.2, 0.4])
    ax.legend(loc="upper left", frameon=False, borderpad=0, handlelength=1.3,
              handletextpad=0.5, labelspacing=0.7, title="Endpoints", title_fontsize=8)

    destination = ROOT / "figures" / "finance-mechanism.pdf"
    destination.parent.mkdir(exist_ok=True)
    fig.savefig(destination, metadata={
        "Title": "Search reweights an observed, nonmonotone Sharpe gap",
        "Author": None, "Subject": "Fixed-pool finance mechanism calculations",
        "Keywords": None, "Creator": "render_finance_figure.py",
        "Producer": "Matplotlib", "CreationDate": None, "ModDate": None,
    })
    plt.close(fig)
    print(f"Rendered {destination.relative_to(ROOT)}.")


if __name__ == "__main__":
    render()
