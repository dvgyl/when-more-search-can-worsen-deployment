# When More Search Can Worsen Deployment

**Best-of-N Selection on an Incomplete Proxy**  
Dev D. Goyal

This paper asks whether wider search can worsen deployment when the selection score omits a cost. It uses standard finite-pool rank probabilities and a trading simulation to measure how search changes the gross-to-net Sharpe gap.

- [Paper](NewInML_2026_Camera_Ready.pdf)
- [Supporting methods](NewInML_2026_Supporting_Methods.pdf)
- [Source archive](NewInML_2026_Source.zip)
- [Mechanism figure](source/figures/finance-mechanism.pdf)
- [Source and verification instructions](source/README.md)
- [Reproduction scope](source/REPRODUCTION_DETAILS.md)

The primary fitted gap slopes are positive in all 16 pool-by-capital cells. The joint selection-evaluation interval for pool B's capacity component at USD 500 million includes zero. All tested non-oracle rules have negative mean net Sharpe on the comparison grid. The paper reports negative cases and the limits of the execution model. It does not establish profitability or a stable effect on another market path.

This package contains retained aggregates, ticker identifiers, figure inputs, document sources, and verification scripts. It does not contain raw vendor prices or the complete simulator. The scripts check principal aggregate values and regenerate the figure. They do not replay the raw market study. No new license grant for external data is asserted.

To check the supplied evidence:

```sh
cd source
python3 verify_finance.py
```

The paper states no external funding and no competing interests. It discloses substantive AI assistance and author responsibility.
