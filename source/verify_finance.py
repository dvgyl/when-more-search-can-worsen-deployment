"""Check the supplied finance aggregates and finite-pool identities."""

from collections import Counter
import csv
from fractions import Fraction
import hashlib
import io
from itertools import combinations
import json
from math import comb, isclose
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA_FILES = {
    "finance_slopes.csv", "finance_universe.csv", "finance_bootstrap.csv", "finance_remedy_bootstrap.json",
    "finance_late_grid.json", "finance_additional_checks.json",
    "finance_figure_pool_B_candidates.csv", "finance_figure_pool_B_deciles.csv",
    "finance_figure_rank_bins.csv", "finance_figure_rank_gradient_16_32.csv",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected, message, tolerance=1e-12):
    require(isclose(float(actual), float(expected), rel_tol=0, abs_tol=tolerance), message)


def read_csv(name):
    with (DATA / name).open(newline="") as source:
        return list(csv.DictReader(source))


def source_csv(evidence, name):
    return list(csv.DictReader(io.StringIO(evidence["sources"][name]["csv"])))


def positive_capital(rows):
    return [row for row in rows if row["level"] in {"25M", "100M", "500M"}]


def check_hashes():
    manifest = json.loads((DATA / "manifest.json").read_text())
    require(set(manifest) == DATA_FILES, "The finance data manifest file set differs.")
    for name, record in manifest.items():
        actual = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
        require(actual == record["sha256"], f"The file hash differs for {name}.")
    evidence = json.loads((DATA / "finance_additional_checks.json").read_text())
    csv_count = 0
    for name, record in evidence["sources"].items():
        if record["format"] != "csv":
            continue
        payload = record["csv"].encode("utf-8")
        require(hashlib.sha256(payload).hexdigest() == record["sha256"],
                f"The embedded CSV hash differs for {name}.")
        require(len(payload) == record["bytes"], f"The embedded byte count differs for {name}.")
        require(len(source_csv(evidence, name)) == record["row_count"],
                f"The embedded row count differs for {name}.")
        csv_count += 1
    require(csv_count == 17, "The embedded CSV count differs.")
    for local, embedded in [
        ("finance_slopes.csv", "v2_primary_lambda_t1ls1_full.csv"),
        ("finance_bootstrap.csv", "v2_bootstrap_B_t1ls1.csv"),
    ]:
        require((DATA / local).read_bytes() == evidence["sources"][embedded]["csv"].encode(),
                f"The separate and embedded evidence differs for {local}.")
    print("PASS. Ten data hashes and 17 embedded CSV hashes, byte counts, and row counts agree.")
    return evidence


def check_universe():
    path = DATA / "finance_universe.csv"
    require(hashlib.sha256(path.read_bytes()).hexdigest() ==
            "67333905030707d7adbf3fbe41117af859eaa3c69a0c2a2e2ca72d03acd74cbd",
            "The retained universe identifier hash differs.")
    rows = read_csv("finance_universe.csv")
    require(len(rows) == 258, "The universe ticker count differs.")
    require(set(rows[0]) == {"panel_column_1based", "ticker"}, "The universe fields differ.")
    require(len({row["ticker"] for row in rows}) == 258, "Universe tickers are duplicated.")
    require(all(row["ticker"] and int(row["panel_column_1based"]) == index
                for index, row in enumerate(rows, 1)), "The universe panel-column order differs.")
    print("PASS. The 258 unique universe tickers retain their checked panel-column order.")


def check_primary():
    rows = read_csv("finance_slopes.csv")
    require(len(rows) == 20, "The primary row count differs.")
    primary = [row for row in rows if float(row["A"]) > 0]
    require(len(primary) == 16, "The positive-capital row count differs.")
    require(len({(r["pool"], r["level"]) for r in rows}) == 20, "Primary cells are duplicated.")
    for row in primary:
        for left, right, label in [
            (float(row["Lambda"]) - float(row["Lambda_gross"]), row["D"], "total"),
            (sum(float(row[k]) for k in ["D_fill", "D_spread", "D_impact"]), row["D"], "ordered"),
            (float(row["D_fill"]) + float(row["D_impact"]), row["D_capacity_total"], "capacity"),
        ]:
            close(left, right, f"The {label} slope decomposition differs.")
        require(float(row["D"]) < 0 and float(row["D_capacity_total"]) < 0,
                "A primary gap sign differs.")
        require(float(row["turn32"]) > float(row["turn1"]), "Executed turnover does not increase.")
        for field in ["Lambda", "D", "D_capacity_total"]:
            require(float(row[field]) * float(row[field + "_lwo"]) > 0,
                    f"The leave-one-candidate-out sign differs for {field}.")
    require(sum(float(r["Lambda"]) < 0 for r in primary) == 9, "The negative slope count differs.")
    require(sum(float(r["V32"]) < float(r["V1"]) for r in primary) == 11,
            "The negative endpoint count differs.")
    require(sum(float(r["Lambda"]) < 0 for r in primary if r["level"] == "500M") == 3,
            "The USD 500 million negative slope count differs.")
    capacity_move = max(abs(float(r["D_capacity_total_lwo"]) / float(r["D_capacity_total"]) - 1)
                        for r in primary)
    close(capacity_move, 0.08578921177685989, "The maximum capacity sensitivity differs.")
    d25 = next(r for r in primary if r["pool"] == "D" and r["level"] == "25M")
    close(abs(float(d25["Lambda_lwo"]) / float(d25["Lambda"]) - 1), 0.8857064927012588,
          "The near-zero net slope sensitivity differs.")
    gross_levels = [-0.09473190890870471, -0.10930786438029283, -0.114225270281, -0.1312279846]
    for pool, expected in zip("ABCD", gross_levels):
        row = next(r for r in rows if r["pool"] == pool and r["level"] == "gross")
        close(row["V1"], expected, "The gross performance level differs.", tolerance=1e-9)
    a500 = next(r for r in primary if r["pool"] == "A" and r["level"] == "500M")
    a2b = next(r for r in primary if r["pool"] == "A" and r["level"] == "2B")
    require(-float(a2b["D_capacity_total"]) < -float(a500["D_capacity_total"]),
            "The pool-A capital reversal differs.")
    require(sum(r["Q_monotone"] == "False" for r in primary if r["pool"] == "A") == 4,
            "The pool-A monotonicity failures differ.")
    d500 = next(r for r in primary if r["pool"] == "D" and r["level"] == "500M")
    close(d500["turn1"], 0.137439931036, "The turnover starting level differs.", 1e-9)
    close(d500["turn32"], 0.1992286269, "The turnover ending level differs.", 1e-9)
    print("PASS. Primary decomposition, sign counts, levels, turnover, and sensitivity checks agree.")


def check_uncertainty():
    rows = read_csv("finance_bootstrap.csv")
    def select(mode, quantity):
        selected = [r for r in rows if r["pool"] == "B_t1ls1" and r["mode"] == mode
                    and r["block"] == "21" and r["quantity"] == quantity]
        require(len(selected) == 1, "The reference bootstrap cell is missing or duplicated.")
        return selected[0]
    joint = select("joint", "D_capacity_total_500M")
    close(-float(joint["hi95"]), -0.021941700371746763, "The lower joint interval differs.")
    close(-float(joint["lo95"]), 0.120891768335904, "The upper joint interval differs.")
    close(joint["frac_negative"], 0.879, "The positive capacity replicate fraction differs.")
    require(int(joint["reps"]) == 1000, "The bootstrap replicate count differs.")
    gross = select("joint", "Lambda_gross")
    close(gross["lo95"], -0.043820823446608564, "The gross lower interval differs.")
    close(gross["hi95"], 0.06780618901466971, "The gross upper interval differs.")
    fixed = select("eval_only", "D_capacity_total_500M")
    close(-float(fixed["hi95"]), 0.03834234229284132, "The fixed-ranking lower interval differs.")
    close(-float(fixed["lo95"]), 0.05514759691764884, "The fixed-ranking upper interval differs.")
    remedy = json.loads((DATA / "finance_remedy_bootstrap.json").read_text())
    for name, expected in [("net_score", 0.42975754275006317), ("turnover_penalty", 0.453087360660436)]:
        value = remedy["estimands"][name]
        close(value["point"], expected, "The paired selector gain differs.")
        require(value["lo95"] > 0 and value["frac_positive"] == 1, "The paired selector signs differ.")
    require(remedy["cells"] == 36 and remedy["stationary_bootstrap"]["reps"] == 1000,
            "The paired bootstrap design differs.")
    print("PASS. Joint and fixed-ranking interval conversions and paired gain summaries agree.")


def check_selectors(evidence):
    rows = source_csv(evidence, "v2_remedy_t1ls1_full.csv")
    simfree = source_csv(evidence, "v2_simfree_ls1.csv")
    expected = [
        ("gross", None, -0.5009621944361425, 0.0),
        ("turnscreen", None, -0.29765246054408667, 0.20330973389205584),
        ("turnpenalty", None, -0.047874834783472674, 0.45308735965266983),
        ("net@A'", None, -0.07120465301966192, 0.4297575414164806),
        ("dsr@A'", None, -0.07123083151391836, 0.42973136292222414),
        ("oracle", None, 0.21985899022608726, 0.7208211846622298),
        ("simulator-free penalty", "eta0.5", -0.16903937075338954, 0.33192282368275294),
        ("simulator-free penalty", "eta0.11", -0.22912384147138645, 0.27183835296475606),
    ]
    table = (ROOT / "finance-remedy-table.tex").read_text()
    for criterion, variant, level, gain in expected:
        selected = [r for r in (simfree if variant else rows)
                    if r.get("variant") == variant] if variant else [r for r in rows if r["criterion"] == criterion]
        require(len(selected) == 36, f"The selector cell count differs for {criterion}.")
        close(mean(float(r["V32"]) for r in selected), level, f"The selector level differs for {criterion}.")
        actual_gain = mean(float(r["gain"]) if variant else float(r["V32"]) - float(r["V32_gross_baseline"])
                           for r in selected)
        close(actual_gain, gain, f"The selector gain differs for {criterion}.")
        summaries = [r for r in evidence["derived_summary"]["selectors"]
                     if r["criterion"] == criterion and r.get("variant") == variant]
        require(len(summaries) == 1, "The derived selector summary is missing or duplicated.")
        close(summaries[0]["mean_net_sharpe"], level, "The derived selector level differs.")
        close(summaries[0]["mean_gain"], gain, "The derived selector gain differs.")
        require(f"{level:+.3f}" in table and (f"{gain:+.3f}" if gain else "0.000") in table,
                "A displayed selector value differs.")
    print("PASS. All eight selector means and gains reproduce from their 36-cell aggregates.")


def check_sensitivity(evidence):
    grids = source_csv(evidence, "v2_gridsens_t1ls1_full.csv")
    require(len(grids) == 64 and len({r["grid"] for r in grids}) == 5, "The anchored-grid counts differ.")
    require(all(float(r["D_capacity_total"]) < 0 for r in grids), "An anchored-grid sign differs.")
    execution = positive_capital(source_csv(evidence, "v2_envelope_t1ls1_full.csv"))
    require(len(execution) == 324, "The execution cell count differs.")
    require(len({(r["kappa"], r["spread"], r["eta"]) for r in execution}) == 27,
            "The execution setting count differs.")
    require(all(float(r["D_capacity_total"]) < 0 for r in execution), "An execution sign differs.")
    walk = positive_capital(source_csv(evidence, "v2_walkforward_t1ls1_full.csv"))
    require(len(walk) == 72, "The walk-forward cell count differs.")
    negatives = {(r["pool"], r["fold"], r["level"]) for r in walk if float(r["D_capacity_total"]) > 0}
    expected = {("B", "f6", level) for level in ["25M", "100M", "500M"]}
    expected |= {("C", "f3", level) for level in ["25M", "100M", "500M"]}
    expected.add(("C", "f6", "500M"))
    require(negatives == expected, "The seven negative walk-forward cells differ.")
    terciles = positive_capital(source_csv(evidence, "v2_tercilesls1.csv"))
    require(len(terciles) == 9, "The liquidity cell count differs.")
    require({r["pool"] for r in terciles if float(r["D_capacity_total"]) > 0} == {"TER2"},
            "The liquidity reversal differs.")
    require(sum(float(r["D_capacity_total"]) > 0 for r in terciles) == 3,
            "The middle-tercile negative count differs.")
    late = json.loads((DATA / "finance_late_grid.json").read_text())
    close(-late["8..32"]["500M"], -0.006969592529888928, "The late-grid reversal differs.")
    stress = source_csv(evidence, "v2_misspec_ls1.csv")
    require(len(stress) == 2916 and all(float(r["gain"]) > 0 for r in stress),
            "The retained selector stress-grid counts differ.")
    print("PASS. Search grids, execution settings, walk-forward failures, and liquidity reversals agree.")


def quantile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def check_figure():
    bins = read_csv("finance_figure_rank_bins.csv")
    require(len(bins) == 60, "The probability-bin count differs.")
    for row in bins:
        budget, index = int(row["N"]), int(row["bin"])
        exact = Fraction(comb(index * 75, budget) - comb((index - 1) * 75, budget), comb(1500, budget))
        close(row["selection_probability"], float(exact), "An exact probability bin differs.", 1e-15)
    candidates = read_csv("finance_figure_pool_B_candidates.csv")
    deciles = read_csv("finance_figure_pool_B_deciles.csv")
    require(len(candidates) == 1500 and len(deciles) == 10, "The candidate or decile count differs.")
    for index, row in enumerate(candidates):
        require(int(row["gross_score_rank_ascending"]) == index + 1, "Candidate ranks differ.")
        close(row["gross_score_rank_percentile"], (index + 0.5) / 1500 * 100, "Rank percentiles differ.")
        gap = (float(row["gross_evaluation_sharpe"]) - float(row["capped_gross_evaluation_sharpe"]))
        gap += float(row["spread_only_evaluation_sharpe"]) - float(row["net_evaluation_sharpe"])
        close(gap, row["capacity_component_signed_sharpe_gap"], "A candidate capacity component differs.")
    for index, row in enumerate(deciles):
        values = [float(r["capacity_component_signed_sharpe_gap"]) for r in candidates[index * 150:(index + 1) * 150]]
        require(int(row["candidate_count"]) == 150, "A decile size differs.")
        close(mean(values), row["mean_signed_sharpe_gap"], "A decile mean differs.")
        for p, field in [(0.25, "q25_signed_sharpe_gap"), (0.75, "q75_signed_sharpe_gap")]:
            close(quantile(values, p), row[field], "A decile quartile differs.")
    gradients = read_csv("finance_figure_rank_gradient_16_32.csv")
    require(len(gradients) == 2998, "The rank-gradient row count differs.")
    for pool, endpoint in [("B", 0.06689876173996878), ("TER1", 0.04910256982598504)]:
        selected = [r for r in gradients if r["pool"] == pool]
        require(len(selected) == 1499, "A pool's rank-gradient count differs.")
        cumulative = 0.0
        for index, row in enumerate(selected, 1):
            require(int(row["cut_rank"]) == index and row["N1"] == "16" and row["N2"] == "32",
                    "A rank-gradient cut or budget differs.")
            close(float(row["delta_q"]) * float(row["exposure_increment"]), row["contribution"],
                  "A rank-gradient product differs.")
            cumulative += float(row["contribution"])
            close(cumulative, row["cumulative"], "A cumulative rank-gradient term differs.")
        close(cumulative, endpoint, "A displayed rank-gradient endpoint differs.")
    print("PASS. Figure probabilities, candidate gaps, decile summaries, and cumulative terms agree.")


def choose(n, k):
    return comb(n, k) if 0 <= k <= n else 0


def check_rank_law():
    cases = 0
    for size in range(2, 9):
        q = [Fraction((rank * rank + 3 * rank) % 7 - 3, 3) for rank in range(1, size + 1)]
        curves = {}
        tails = {}
        for budget in range(1, size + 1):
            subsets = list(combinations(range(1, size + 1), budget))
            winners = Counter(min(subset) for subset in subsets)
            probabilities = [Fraction(choose(size - rank, budget - 1), comb(size, budget))
                             for rank in range(1, size + 1)]
            require(all(probabilities[r - 1] == Fraction(winners[r], len(subsets))
                        for r in range(1, size + 1)), "The enumerated rank law differs.")
            tail = [Fraction(choose(size - cut, budget), comb(size, budget)) for cut in range(1, size)]
            require(all(tail[k - 1] == sum(probabilities[k:]) for k in range(1, size)),
                    "The enumerated tail law differs.")
            value = sum(p * outcome for p, outcome in zip(probabilities, q))
            require(value == q[0] + sum((q[k] - q[k - 1]) * tail[k - 1] for k in range(1, size)),
                    "The finite-sum rank identity differs.")
            curves[budget], tails[budget] = value, tail
            cases += 1
        for old in range(1, size):
            for new in range(old + 1, size + 1):
                changes = [b - a for a, b in zip(tails[old], tails[new])]
                require(all(value <= 0 for value in changes), "A tail change has the wrong sign.")
                require(curves[new] - curves[old] == sum((q[k] - q[k - 1]) * changes[k - 1]
                                                        for k in range(1, size)),
                        "The rank-gradient change identity differs.")
    print(f"PASS. Exact enumeration checks {cases} pool-budget cases and all budget-pair identities.")


def main():
    evidence = check_hashes()
    check_universe()
    check_primary()
    check_uncertainty()
    check_selectors(evidence)
    check_sensitivity(evidence)
    check_figure()
    check_rank_law()
    print("All finance aggregate checks passed. No study execution was required.")


if __name__ == "__main__":
    main()
