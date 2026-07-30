# Revision Log

This project went through several rounds of correction after external review. Kept here as a record of what changed and why; the README itself states only the current, corrected methodology and findings.

## v1 → v2

- **Pipeline automation.** Manually-run SQL statements replaced with a single, idempotent `pipeline.sql`; views converted to tables (source data is a static snapshot).
- **Missing-observation count corrected.** Original README stated 11 missing observations; the real number, traced to a query, is 24 (35 missing region-value cells collapsing to 24 club-season rows). Never previously verified against a query.
- **Value variable: season-average → as-of.** Original spec averaged a player's valuations across a season, letting that season's own performance partially inflate its own predictor. Replaced with the most recent valuation strictly before the season's start.
- **Standard errors: ordinary → club-clustered.** The same clubs recur across 14 seasons; ordinary OLS standard errors don't account for within-club error correlation.
- **Three functional-form specifications compared** (linear values, log values, total-value-plus-shares) to test whether the original "spine matters" finding was robust. It wasn't, except for Forward — which appeared in all three.
- **Influence diagnostics added.** Cook's distance identified one dominant club (`club_id 27`) as disproportionately influential; excluding it dropped R² substantially but left Forward's coefficient roughly unchanged.

## v2 → v3 (after a second, deeper critique)

- **Panel structure corrected.** "18 clubs repeating 14 times" was wrong and unchecked; the panel actually has 31 distinct clubs due to promotion/relegation — an unbalanced panel, not a clean grid. Noted as a few-cluster-bias caveat for clustered SEs.
- **Staleness diagnosis was wrong and has been corrected twice.** First reported as growing from 163 to 1,075 days for two structural reasons (career-stage effect, snapshot thinning). Restricting to players who actually appeared that season showed no growth trend at all — the original figures were an artifact of carrying retired/inactive players forward indefinitely via the season-calendar cross join. A second pass found the real mechanism: Transfermarkt batches valuations heavily around season transitions (~47% of as-of valuations fall in June, just before the July 1 cutoff), and season fixed effects already absorb this timing.
- **Duplicate-row check added.** Confirmed zero duplicate (player_id, season) rows in the as-of value table.
- **Baseline model added.** A total-value-only model (R²=0.538) was compared against the 7-region model (R²=0.571); a joint Wald test rejected the hypothesis that all regional shares are zero (p=0.0013) — evidence that positional distribution explains something beyond total spending, at the between-club level.
- **Club fixed effects added as the decisive test.** This is the test that actually answers "does a club's own shift toward a position predict its own point changes," rather than "do richer/better-distributed clubs do better." Initially run with HC1 (heteroskedasticity-robust) standard errors and an incorrect justification that clustering was redundant with club FE — corrected: club FE absorbs the time-invariant component of the error, not within-club serial correlation, so cluster-robust SEs alongside club FE are standard practice and were re-run.
- **Individual region coefficients are all insignificant under club FE** (with correct cluster SEs), but a **joint Wald test across all seven regions is significant at p=0.035** — meaning there is likely some real within-club association between positional value distribution and points, but severe multicollinearity among the seven region variables prevents attributing it to any single position.
- **Within-R² computed** (club+season demeaned): 0.037 — the joint effect, while statistically detectable, explains only about 3.7% of within-club point variation.
- **Club-season imbalance quantified.** Only 9 of 31 clubs have the full 14 seasons; 7 clubs have just 1-2 seasons and contribute little identification once absorbed by their own club dummy — effective identifying sample size is smaller than the raw 241 observations.
- **Dependent variable validated more thoroughly.** Every season has exactly 306 matches (correct for an 18-team double round robin); club_id 27 averages 81.64 points across all 14 seasons, consistent with Bayern Munich's known dominance — upgrading the earlier single-season spot-check to a multi-season one.

## v3 → v4 (final round)

- **The v3 headline (a marginally significant joint within-club effect, p=0.035) was itself retracted after cross-checking.** A classical F-test on the identical nested model comparison gave p=0.818 — a large enough gap, given only 31 clusters (several with just 1-2 seasons), to be a known symptom of cluster-robust over-rejection rather than a real signal.
- **Two further independent tests confirmed the retraction:** a single-degree-of-freedom, theory-motivated contrast (attacking regions vs. defensive regions) gave p=0.508; a Mundlak/correlated-random-effects model showed every within-club deviation term insignificant (p=0.21-0.90), closely matching the club-FE coefficients as an internal consistency check.
- **The Mundlak decomposition also produced the project's real positive finding:** three of the seven regions' club-level averages (not their within-club deviations) are significantly associated with points — centre-back and full-back positively, defensive midfield negatively. This became the new, better-evidenced version of the "between-club association" headline.
- **The earlier within-R² figure (0.037) was also corrected** to 0.019, via a proper nested-model comparison rather than a flawed manual demeaning.
- **The June valuation-batch figure was recomputed on a clean denominator.** The original ~47% figure was computed on a table that (as noted above) carries retired/inactive players into every future season, inflating the count. Computed directly on raw `player_valuations`: June is 22.1% and December 16.8% of all valuation records — elevated relative to an even 8.3%/month baseline and consistent with the summer/winter transfer windows, but a much more modest figure than first reported.
