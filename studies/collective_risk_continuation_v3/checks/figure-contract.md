# Figure contract

The original D/N/V figures are copied without numerical or visual adaptation.
Their exact provenance is retained in `copied-figure-provenance.json`.

The new R figure asks whether conditioning on the observable prefix provides
additional risk accuracy at the fixed primary 8-step horizon. A single forest
panel shows all four prespecified paired contrasts, not differences inferred
from overlapping marginal loss intervals. The three strong-control intervals
cross zero. The weaker trailing-RV comparison is retained in neutral grey.

The backend is Python, reused from the supplied Python figure workflow. Final
size is 183 × 85 mm with editable SVG/PDF text, an 8 pt glyph floor, restrained
navy/teal/grey and uncertainty bars. Every selected contrast is included. The
independent unit is a full simulated test history, n=128; uncertainty is a 95%
paired basic-bootstrap interval from 19,999 draws. Holm adjustment is recorded
for the four primary comparisons in the source table. No market or latent-state
identification claim is attached to the plotted forecast differences.
