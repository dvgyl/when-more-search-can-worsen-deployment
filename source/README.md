# When More Search Can Worsen Deployment

This package contains the finance paper, supporting methods, retained aggregate results, and figure inputs. The paper studies how gross-score selection changes modeled net trading outcomes. Its rank identity is standard finite-pool accounting. The principal joint uncertainty interval includes zero. The results do not establish future profitability.

The source repository is [when-more-search-can-worsen-deployment](https://github.com/dvgyl/when-more-search-can-worsen-deployment).

## Build and check

Run these commands from this directory. Document compilation requires Tectonic and access to its TeX dependencies. The main paper uses the included NeurIPS 2026 workshop style. The supplement uses the standard article class and geometry package.

```sh
tectonic -X compile main.tex
tectonic -X compile supplement.tex
python3 verify_finance.py
```

The verifier uses only the Python standard library. It checks aggregate hashes, the 17 embedded CSV payloads, reported finance summaries and negative cases, figure inputs, and small-pool rank identities by exact enumeration. It does not fit models, simulate trades, or generate bootstrap draws. A successful check does not establish statistical validity or venue approval.

The main document reads `abstract.tex`, `finance-remedy-table.tex`, and `checklist.tex`. The supplement reads `finance-feature-table.tex`. Figure 1 is included as `figures/finance-mechanism.pdf`. Regenerate it with the supplied input CSV files.

```sh
python3 -m pip install -r requirements-figures.txt
python3 render_finance_figure.py
```

The figure renderer uses NumPy and Matplotlib. It checks fixed input hashes and corresponding entries in `data/manifest.json`. It reads only package-relative files. It reproduces the display from retained aggregate inputs. It does not rerun the study. PDF metadata excludes creation and modification dates.

## Data and interpretation

This is an aggregate reproduction package. `data/finance_universe.csv` gives the 258 retained ticker identifiers in panel-column order. It contains no prices, returns, or volumes. It does not contain raw vendor prices, candidate return arrays, the full simulator, or a complete environment for rerunning the study. `REPRODUCTION_DETAILS.md` describes the supplied files and their limits. No raw-data redistribution permission or new license grant is asserted.

The stored finance slope differences use net minus gross. The paper uses gross minus net. Thus `Gamma=-D` and `Gamma_cap=-D_capacity_total`. Negate interval endpoints and reverse their order. Gross slopes and selector gains keep their stored signs.

The capacity component is a signed Sharpe gap. It combines the ordered capping and impact components and omits the adjacent spread component. It is not a measured cash cost. The figure's quartile ranges describe candidate spread. They do not give uncertainty in a population mean.

## Source package contents

The package contains only the following files. Other project studies and private working records are outside this package.

```text
README.md
REPRODUCTION_DETAILS.md
main.tex
abstract.tex
checklist.tex
supplement.tex
finance-feature-table.tex
finance-remedy-table.tex
refs.bib
neurips_2026.sty
requirements-figures.txt
render_finance_figure.py
verify_finance.py
figures/finance-mechanism.pdf
data/manifest.json
data/finance_slopes.csv
data/finance_universe.csv
data/finance_bootstrap.csv
data/finance_remedy_bootstrap.json
data/finance_late_grid.json
data/finance_additional_checks.json
data/finance_figure_pool_B_candidates.csv
data/finance_figure_pool_B_deciles.csv
data/finance_figure_rank_bins.csv
data/finance_figure_rank_gradient_16_32.csv
```
