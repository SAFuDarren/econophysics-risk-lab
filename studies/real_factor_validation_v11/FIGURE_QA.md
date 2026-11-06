# Scientific figure acceptance

Both figures were created in Python/Matplotlib at 183 mm width, with editable SVG/PDF text and 300 dpi PNG previews. They are research figures for this project, not figures certified by a journal. The final complete PNGs and every panel were visually inspected after the final layout changes.

| Figure / panel | Distinct evidence role | Center and uncertainty | Unit | Layout / glyph / collision | Accepted |
|---|---|---|---|---|---|
| RF1 a | Nominal factor count versus effective return modes | Estimated monthly path; not a replicate mean, no uncertainty band claimed | All 81 target months | Alignment pass; no clipping or missing glyph; zero collision findings | Yes |
| RF1 b | Covariance amplification and hedging | Estimated full/diagonal ratio path, not a replicate mean | Same months | Alignment pass; ratio 1 visible, full 0.355–2.301 range preserved | Yes |
| RF1 c | Descriptive performance of every frozen forecaster | Mean QLIKE; paired inference shown in d | Same 81 months | All 4 models and full HAR-Portfolio label visible; numerical labels moved off grid lines | Yes |
| RF1 d | Locked paired forecast comparisons | Mean and 95% basic paired-block interval | Calendar month | Both 3- and 6-month intervals; aligned; no collision | Yes |
| RF2 a | Rule-specific concentration and control path | Computed paths, not seed averages | Same 81 months | All 3 rules; Permuted higher periods fully retained | Yes |
| RF2 b | Concentration difference, separate from risk | Mean and 95% basic paired-block interval | Calendar month | Both controls and block choices; no collision | Yes |
| RF2 c | Uncertain subsequent risk increment | Mean and 95% basic paired-block interval | Calendar month, risk in units 10⁻⁶ | Both controls/block choices; mathtext rendered correctly | Yes |

Final programmatic checks:

- RF1/RF2 alignment gates: PASS at 1.5 physical point tolerance.
- RF1/RF2 PDF text floor: minimum 7.0 pt / 5.6 pt, none below 5 pt.
- RF1/RF2 rendered collision audits: zero FAIL, zero WARN. The RF1 detector also reports four informational contained-fill overlays; the final visual review found no obscured text or data.
- Source preflight: no FAIL. Warnings are the conservative math-script size estimate (resolved by the measured 5.6 pt PDF floor), 300 dpi PNG preview and absence of a TIFF submission raster. The primary plots are editable vectors; no journal TIFF submission is claimed.
- First-pass clipping and missing superscript glyphs were corrected before acceptance; QA references the final files, not the earlier renders.

The source preflight, alignment, PDF glyph and rendered collision JSONs are retained beside the figures. Diagnostic alignment SVG and collision-overlay PDF files are QA aids, not additional scientific figures for publication.
