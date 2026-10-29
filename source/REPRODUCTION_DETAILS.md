# Reproduction details

This package permits checks of retained finance aggregates and regeneration of the mechanism figure. It does not permit full study reproduction. Raw prices, candidate return arrays, the complete simulator, and the original execution environment are not included. No model fitting, execution simulation, or bootstrap ran for this revision.

## Supplied evidence

`data/manifest.json` binds ten finance data files with SHA256 hashes. `verify_finance.py` checks these hashes before it checks reported quantities. It also checks all 17 embedded CSV payloads against their recorded hashes, byte counts, and row counts.

`finance_additional_checks.json` contains 29 retained source aggregates. CSV payloads preserve exact source text. JSON payloads preserve parsed values and record the original source hash. Parsed JSON does not retain original whitespace or key order. Thus the verifier checks embedded CSV byte hashes. It does not claim to reconstruct original JSON bytes from parsed values.

| File | Contents |
|---|---|
| `finance_universe.csv` | The 258 retained ticker identifiers in panel-column order. No prices, returns, or volumes. |
| `finance_slopes.csv` | Twenty primary rows. Four uncapped gross rows and sixteen positive-capital rows across four pools. |
| `finance_bootstrap.csv` | Retained selection-and-evaluation and evaluation-only block-bootstrap aggregates. |
| `finance_remedy_bootstrap.json` | Paired bootstrap summaries for the net-score and turnover-penalty mean gains. |
| `finance_late_grid.json` | Pool A's retained late-search-grid slope differences. |
| `finance_additional_checks.json` | Selector means and full retained sensitivity aggregates, with source hashes and interpretation limits. |
| `finance_figure_rank_bins.csv` | Sixty exact winner-probability bins for 1, 4, and 32 trials in a pool of 1,500 candidates. |
| `finance_figure_pool_B_candidates.csv` | The 1,500 ranked candidate scores and signed capacity components used in Figure 1(b). |
| `finance_figure_pool_B_deciles.csv` | Ten candidate-decile means and quartiles for Figure 1(b). |
| `finance_figure_rank_gradient_16_32.csv` | The 2,998 cumulative rank-gradient terms used in Figure 1(c). |

## Field definitions

`Lambda` is the fitted evaluation Sharpe slope per doubling of search. It uses budgets 1, 2, 4, 8, 16, and 32. `Lambda_gross` is the corresponding uncapped gross slope. A fitted slope and the difference between the two endpoints are different summaries.

`D` is the net-minus-gross slope difference. `D_fill`, `D_spread`, and `D_impact` are adjacent differences along the ordered path from uncapped gross to capped gross, spread-only, and net outcomes. `D_capacity_total` is `D_fill + D_impact`. The paper reports the negatives of `D` and `D_capacity_total`. For an interval `[lo, hi]`, this conversion gives `[-hi, -lo]`.

`V1` and `V32` are expected selected evaluation Sharpe at 1 and 32 trials. `pool_hit` is the fraction of candidates with positive evaluation Sharpe. `turn1` and `turn32` are expected selected turnover. At capital zero, these are uncapped desired turnover. At positive capital, these are executed turnover.

In the bootstrap CSV, `joint` resamples selection and evaluation separately and recomputes selection rankings. `eval_only` holds rankings fixed. `block` gives mean block length in days. `reps` gives the number of replicates. `lo95` and `hi95` give percentile interval endpoints. These retained intervals do not establish population confidence coverage.

Each selector mean equally weights four pools, three assumed capitals, and three evaluation capitals at 32 trials. This gives 36 dependent cells. The ex-post oracle uses evaluation outcomes. The simulator-free penalties use retrospective full-panel summaries. The net and deflated-net means agree at three decimal places. This agreement does not establish identical rankings or winners.

The figure's percentile direction is ascending selection score. Higher percentiles are better. This direction is the reverse of the main identity's convention, where rank 1 is best. The renderer preserves and labels the percentile direction. Panel (b) uses `(gross - capped gross) + (spread-only - net)` evaluation Sharpe. It is a signed capacity component, not the full gross-to-net gap or a cash cost.

## Verification scope

The standard-library verifier checks the primary slope decomposition, endpoint and sign counts, turnover increases, leave-one-candidate-out sensitivity, selector means, joint-interval sign conversion, search-grid and execution counts, the seven negative walk-forward cells, liquidity reversals, and the displayed figure data. Exact enumeration checks the winner-rank law, tail law, and finite-sum identities for pools with two to eight candidates. These are checks of formulas and retained evidence. They do not create new scientific observations.

The retained price snapshot ends on 24 July 2026. Vendor prices and candidate series are outside this package. The simulation omits financing and borrowing costs and does not model a funded investor account. Shared market history and candidate construction limit interpretation. Sensitivity-cell counts are not independent replications.

Historical source identifiers remain in data for traceability. They are identifiers, not local paths. No private paths, assistant reports, or unrelated study files are required by the public commands. The package asserts no new license grant. Availability of these aggregates does not establish permission to redistribute external price data.

## Universe identifiers and provenance

`finance_universe.csv` contains 258 unique ticker identifiers in the original panel-column order. Its SHA256 is `67333905030707d7adbf3fbe41117af859eaa3c69a0c2a2e2ca72d03acd74cbd`. The identifier source is the retained `panel_ext.npz` ticker array. That file's SHA256 is `ba09e6db95c1775a1f3c2772b45092927c48a544a1dae29fcc374e12e585ae8d`, which agrees with the retained run manifest. The original `panel.npz` has SHA256 `fa5aea06a2d78ae4d4fcac5e79eb049de687e61a6e20f435e5dba83a8e7b8c86`. Its ordered ticker list is identical. These source hashes document provenance. The panel files and market-data arrays are not distributed in this package.

The retained downloader starts from a fixed, hard-coded list of 347 unique tickers. No external index-constituent source or documented rule for constructing that initial list was established. The download stage lacks input and output hashes in the retained manifest. Thus the exact retained identifiers have a checked local source chain, but the initial list has limited provenance. The list is not established as a historical index membership list or a random market sample.

The executable panel filter requires more than 90% nonmissing adjusted-price coverage from 1 January 2009 through the retained endpoint. The extended panel keeps the original panel's ticker set and adds no names. Daily eligibility also depends on feature availability, price, and volume. The full ticker list therefore differs from the eligible set on a given day. Publishing these identifiers does not reconstruct missing or delisted names or remove survivor filtering.
