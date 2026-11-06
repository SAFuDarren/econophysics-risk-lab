# Source, vintage and terms record

Official source: Kenneth R. French Data Library, Dartmouth Tuck. Sources were downloaded directly from the two official routes fixed in `PROTOCOL.json`:

- [Daily five-factor CSV archive](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip)
- [Daily momentum CSV archive](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip)

`checks/download_manifest.json` records the retrieval UTC time, HTTP headers, byte count, SHA256 and archive members. The ZIP integrity checks passed. Both source files identify the 202609 CRSP database and contain the copyright notice of Eugene F. Fama and Kenneth R. French for 2026. The copyright is retained; we do not assert an open-data license over these source files or grant rights that the original authors have not granted.

The study starts in 1990, uses all six fixed series on their daily intersection and ends on 30 September 2026. Returns are converted from source percent to decimal. No external synthetic observations, future monthly values or other data vendors are appended.

The [official library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) documents the switch from legacy FIZ to CIZ production with the January 2025 release. The current download is therefore a single current vintage, with possible historical revisions, not an archive of what the market observed in each historical month. This restriction applies even though the chronological modeling features do not use future monthly returns.

Descriptions of [five-factor construction](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html) and [daily momentum](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor_daily.html) establish that these are constructed research-portfolio returns. They are not counts of quant firms, actual strategy holdings, order flows, or measured factor adoption.

## Public release boundary

Publish the project-authored protocol, source code, derived monthly tables/predictions/figures, statistical appendix, data dictionary and the original source routes with checksums. Keep the two official ZIP files, extracted source CSV files and full daily source panel in the local cache. Public reproduction should obtain the source from its original provider and verify the saved checksums; a changed vintage must be identified rather than passed off as the same frozen input. The project code license does not cover the copyrighted source files.
