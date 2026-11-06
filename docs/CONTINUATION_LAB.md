# Research evidence workbench

The top of `web/lab.html` connects the retained weighted fast/slow network to the
latest controlled inference, risk and Bitcoin observation checks. The original
six foundation experiments and their research views remain available below it.
The learning-room links point to the same questions and formulas.

## Entry points

- `lab.html#research-bench`: overview and the current workbench.
- `lab.html#collective-channels`: common versus independent signals and feedback.
- `lab.html#collective-propagation`: known-state propagation and state-specific shocks.
- `lab.html#collective-inference`: observable-prefix state estimation and hidden truth.
- `lab.html#collective-risk`: matched forecasting and the Bitcoin transport check.

## What the reader can inspect

### Common signals and feedback

Choose among all five fixed interventions and both predeclared metrics. The upper
plot shows saved paired-bootstrap mean contrasts with baseline. RV contrasts are
scaled by the same fixed baseline mean; alignment differences are percentage
points. The lower plot retains all 128 paired seed differences. Their dispersion
is not uncertainty in a mean. The ten primary comparisons share Holm correction.
No UI control creates a new experimental configuration or interpolates results.

### State and shock response

Choose any of eight known initial states, one of three order doses, and a saved
horizon from 1 to 48. Full stochastic ensemble means are compared with independent
Monte Carlo reference means and the rejected deterministic mean-state iteration.
The reference band is Monte Carlo error of a mean, not future-outcome coverage.
An additional exact eight-state pulse comparison shows four increases and four
decreases in flow second moment. That earlier state set is explicitly separate
from the propagation set. The 128-seed pulse/RV interpretation remains visible.

### Macro-only state inference

All 128 test cases and all six inferred state targets are selectable. The visible
prefix is exactly ticks 65–96, the 32 bars available at prediction time. Raw 90%
state intervals from the conditional ensemble and same-law prior are displayed
before a reader reveals the hidden validation truth. Coverage is recalculated
across the complete test set. Fast-direction scores retain the direct F/V proxy.
The interface states that the simulator's K counts active effective units and
that the supplied model law, offline bank and calibration labels also cost
information. Revealing validation labels does not recompute any estimate.

### Risk and market transfer

The reader can select the predeclared primary 8-step horizon or secondary 1/48,
raw versus separately calibrated conditional-network intervals, and all four
paired references. Point losses do not change with interval calibration. The
method plot uses a nonnegative QLIKE axis and the same saved point-score rows; the selected raw versus
calibrated coverage applies to the conditional network. Paired loss differences
and their intervals, rather than overlap of separate mean intervals, support the
comparison. A second view compares all eight saved Bitcoin/simulator features.
Its simulator line is the min/max of 64 blocks, not a confidence interval. The
663 observed days and 1,989 overlapping-by-date blocks are stated explicitly.

Fitted controls and the conditional mixture share the labelled simulation bank.
The network additionally uses the supplied mechanistic law. TrailingRV computes
past RV without training labels; every method receives the same 64 interval
calibration labels. These costs are stated beside the online input length.

## Data and implementation

`web/assets/data/continuation-evidence.js` is the source-bound browser snapshot.
Every plot reads its numerical values; no fabricated market series or fitted
in-browser performance curve is added. Its same-origin source downloads retain
complete CSVs, SHA-256 provenance and a machine-readable source manifest.

- UI: `web/assets/continuation-lab.js` and `continuation-lab.css`.
- Data guide: `studies/collective_risk_continuation_v3/` and the download manifest.
- Numeric view checks: `node tests/test_continuation_lab.cjs`.
- Browser state: `window.ContinuationLab.state` and `selectTab`.

The workbench shares the site's language preference. Tabs support arrow, Home
and End keys. Controls preserve selected state through language changes and focus
through redraws. Responsive charts use their actual container width; the interface
retains reduced-motion preferences and visible keyboard focus. Deep links select
the new view without changing the preserved foundational experiment anchors.
