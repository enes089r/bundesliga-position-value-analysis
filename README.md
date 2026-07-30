# Bundesliga Position-Value Analysis

Does spending on more valuable players in specific positions translate into more league points? This project builds a squad-value dataset in SQL and runs a regression in Python to find out — for the Bundesliga, across 14 seasons (2012–2025).

The code speaks for itself; this README explains **why** each choice was made and what the evidence actually supports. A full record of earlier drafts' mistakes and how each was found and corrected is kept in `CHANGELOG.md` rather than here.

---

## Research Question

For a given club-season, does having more valuable players in a specific **positional region** (goalkeeper, defense, midfield, attack) lead to more league points — and does this hold for every region, or only some?

---

## Headline Finding

**Squad value distribution is a between-club characteristic, not a within-club lever.**

Across clubs, how a squad's value is distributed matters, not just how much it has in total. Splitting each region's value into a club's own long-run average ("between") and its season-to-season deviation from that average ("within") makes this precise: a club's **average** centre-back value (+1.31 points per €1m, p<.001) and **average** full-back value (+1.27, p=.007) are positively associated with its average points, while its average defensive-midfield value is *negatively* associated (−0.51, p<.001). These are real, well-evidenced cross-club correlations — but they describe what kind of club tends to do well, not what a specific club should do differently.

For the **within-club** question — does a club that shifts investment toward a region, relative to its own history, win more points in that season? — the answer is a clean, well-triangulated no. Three independent tests agree: a classical F-test comparing the full model to a club+season-only baseline gives F = 0.52, p = 0.818 (within-R² of just 1.9%); a single-degree-of-freedom, theory-motivated contrast (attacking regions vs. defensive regions) gives p = 0.508; and every within-club deviation term in a correlated-random-effects model is insignificant (p ranging 0.21–0.90). An earlier round of this analysis reported a marginally significant *joint* test across all seven regions (p = 0.035) — that result did not survive comparison against these more reliable tests and is retracted here as a false positive from cluster-robust inference over-rejecting with a small, unevenly-sized set of clusters (see below).

**In plain terms:** which positions a well-performing club tends to have valuable are informative about that club's overall profile, but this analysis finds no evidence that a specific club can raise its points by reallocating value toward any particular position.

---

## Data

Not included in this repository due to file size.

- **Source:** [Player Scores dataset (Transfermarkt) — Kaggle](https://www.kaggle.com/datasets/davidcariboo/player-scores)
- **Tables loaded:** `club_games`, `games`, `players`, `player_valuations`, `appearances` — the only tables the pipeline references.
- **Setup:** Load the CSVs into a MySQL schema, then run `pipeline.sql`.

---

## Methodology & Key Decisions

### Dependent variable — league points (Y)

Points per club-season, computed from match results (win = 3, draw = 1, loss = 0), derived from goals, filtered to the Bundesliga (`competition_id = 'L1'`).

**Validated two ways.** Every season contains exactly 306 matches (the correct total for an 18-team double round robin). Separately, `club_id 27` averages 81.64 points across all 14 seasons — consistent with Bayern Munich's known dominance over this period, and matching, in one specific season, their real 2012–13 record of 91 points. This is a structural and a substantive check, not exhaustive validation against official standings for all 252 club-seasons (see Limitations).

### Independent variable — regional squad value (X)

Each region's value is a **minute-weighted average** of player market values, measuring the quality of who actually plays rather than squad depth or a simple average.

### As-of value construction

`player_season_value` uses the most recent valuation strictly before a season's start (July 1), not a season average — avoiding the case where a season's own performance inflates its own predictor via a mid-season revaluation. Built via a `season_calendar` table joined against `player_valuations` through a correlated `MAX(date)` subquery (a window-function version repeatedly stalled on this dataset; the subquery resolves in about a minute with a covering index on `(player_id, date)`). Checked for duplicate `(player_id, season)` rows — none found.

**A residual limitation:** the *minutes* used to weight each player's value within a region are still same-season minutes, so an unexpectedly strong season that earns a player more playing time still shifts his region's value within that same season.

### Positional grouping — 7 regions

Goalkeeper, Centre-Back, Full-Back, Defensive Midfield, Central Midfield, Winger, Forward. **Open issue:** Left Midfield (566 players) and Right Midfield (565 players) currently sit inside Central Midfield rather than Winger. Given that no individual region is separately identifiable within-club regardless, testing this reclassification is a lower priority than it would otherwise be, but remains unaddressed.

### Panel structure and standard errors

The panel contains **31 distinct clubs** across 14 seasons (not a repeating set of 18 — the Bundesliga has promotion and relegation, so the panel is unbalanced). Season distribution per club is highly uneven: only 9 of 31 clubs have the full 14 seasons; 7 clubs have just 1–2 seasons and are essentially fully absorbed by their own club-fixed-effect dummy, contributing little identifying information. **This directly caused a false positive:** a cluster-robust joint Wald test on the within-club model gave p = 0.035, but a classical F-test on the identical model comparison gave p = 0.818 — a large enough gap, given the small and uneven cluster count, to be a known symptom of cluster-robust inference over-rejecting rather than a real signal. The classical F-test and two other independent checks (see Headline Finding) are treated as the more trustworthy evidence here.

Relegation and promotion also mean the sample is survivorship-shaped, not a fixed random panel — clubs that stayed longer did so by being good enough to avoid relegation, and this selection isn't modeled or corrected for.

### Controlling for market inflation

Season fixed effects (`C(season)`) absorb each season's market-wide baseline rather than deflating nominal values with an unsuitable CPI.

### Missing values

252 club-seasons is the full grid (14 seasons × 18 clubs-per-season), zero unmatched rows on the points join. 35 region-value cells are missing, collapsing to 24 distinct club-season rows with at least one missing region. Under the as-of value spec, only 11 rows are dropped — fewer than under the earlier season-average spec, likely because the as-of query searches a player's entire valuation history before a season, not just within it.

Separately, 586 players have a `NULL` sub_position and are silently excluded from every region; this affects at most 0.23% of playing-time appearance-rows in any single season — negligible.

---

## Robustness Checks

### Valuation Staleness

An earlier pass reported valuation staleness (days between a season's start and the last known prior valuation) growing from 163 to 1,075 days across the panel. **That was an artifact.** The underlying table was carrying every player who ever had a valuation forward into every future season, including retired and inactive players. Restricting to players who actually appeared that season showed no growth trend — values fluctuate between 11 and 176 days with no clear direction.

The actual mechanism: Transfermarkt batches valuations around the transfer windows — checked directly on the raw `player_valuations` table (not the season-calendar cross join, which would double-count inactive players), June accounts for 22.1% and December for 16.8% of all valuation records, well above the ~8.3% each month would get if valuations were spread evenly. This aligns with the summer and winter transfer windows. Because this is a seasonal timing pattern, **season fixed effects already absorb it** — the model doesn't rely on staleness being low by chance.

### Influence Diagnostics

Cook's distance on the (non-club-FE) linear model found no catastrophic single-observation influence (max D = 0.071), but flagged one club as structurally over-represented among the most influential rows — a preview of the between-club effect confirmed formally below.

---

## The Decisive Test: Club Fixed Effects and the Mundlak Decomposition

**Club fixed effects,** with cluster-robust standard errors (club FE absorbs the time-invariant component of each club's error, not within-club serial correlation over time — both are needed together, which is standard panel-econometrics practice):

| Region | Coef | SE | 95% CI | p |
|---|---|---|---|---|
| Central Midfield | 0.192 | 0.166 | [-0.133, 0.516] | 0.248 |
| Forward | 0.051 | 0.084 | [-0.113, 0.215] | 0.544 |
| Goalkeeper | 0.043 | 0.113 | [-0.178, 0.264] | 0.701 |
| Winger | 0.001 | 0.049 | [-0.095, 0.097] | 0.988 |
| Full-Back | -0.066 | 0.161 | [-0.381, 0.250] | 0.683 |
| Defensive Midfield | -0.102 | 0.103 | [-0.303, 0.099] | 0.319 |
| Centre-Back | -0.073 | 0.229 | [-0.521, 0.376] | 0.751 |

No region is individually significant. Comparing these confidence intervals against the non-club-FE (between-club) coefficients: only for Goalkeeper (non-FE coef 0.402, outside this CI) and, marginally, Forward (0.254, just outside 0.215) does the within-club estimate rule out the between-club magnitude. For Centre-Back and Central Midfield, the within-club CIs are wide enough that the between-club estimates fall *inside* them — these two are not shown to differ from their between-club values, only too imprecisely estimated within-club to say either way.

**Why do some regions have tighter CIs than others?** Checked directly via a season-adjusted within/between variance decomposition, run for all seven regions rather than just one:

| Region | Within share of variance |
|---|---|
| Goalkeeper | 0.495 |
| Winger | 0.392 |
| Full-Back | 0.338 |
| Defensive Midfield | 0.299 |
| Forward | 0.222 |
| Central Midfield | 0.208 |
| Centre-Back | 0.189 |

This explains the pattern above directly: Centre-Back and Central Midfield have the *least* within-club variation to work with (19% and 21% of their total variance), which is exactly why their within-club estimates are too imprecise to rule out the between-club magnitude — not evidence that their true within-club effect differs from zero, just weaker power to say either way. Goalkeeper, by contrast, has the most within-club variation of any region (49%) and *still* shows a tight, clearly-null within-club estimate — the strongest and best-powered null result in the table.

**Was the earlier joint significance (p=0.035) real?** No — checked against three more reliable alternatives, all agreeing on a null:

- **Classical F-test**, comparing the 7-region model to a club+season-only baseline, on the identical variables: F = 0.52, p = 0.818. Corrected within-R² = 0.019 — a small number consistent with this F-statistic (an earlier, differently-computed within-R² of 0.037 was based on a flawed manual demeaning and is superseded by this nested-model comparison).
- **A single-df, theory-motivated contrast** — attacking regions (forward + winger) vs. defensive regions (centre-back + full-back) — rather than testing all seven regions at once: χ² = 0.44, p = 0.508.
- **A Mundlak (correlated random effects) decomposition**, splitting each region into its club-level mean and its within-club deviation: every deviation term is insignificant (p from 0.21 to 0.90), closely matching the club-FE coefficients above (e.g. forward: 0.049 vs. 0.051 — a useful internal consistency check). Meanwhile, three of the seven club-mean terms *are* significant — see Headline Finding.

The original 7-region joint Wald test (p = 0.035) sits alone against all three of these. Given only 31 clusters — several with just 1–2 seasons — cluster-robust Wald tests are known to over-reject in exactly this situation. That result is retracted as a false positive rather than treated as suggestive evidence.

The plot below shows the non-FE (between-club, blue) and club-FE (within-club, red) confidence intervals side by side for all seven regions. Two regions — Forward and Goalkeeper — show the blue point sitting outside the red interval, visually confirming these are the only two where the within-club test rules out the between-club magnitude; for the other five, including Central Midfield, the blue point falls inside the red interval.

![Non-FE vs. club-FE coefficient comparison](coef_comparison.png)

---

## Findings

- **Between clubs, defensive value is where the real signal is** — average centre-back and full-back value are positively associated with average points; average defensive-midfield value is negatively associated. These are correlational, not causal, and describe club profiles rather than a lever any one club can pull.
- **Within clubs, no region — individually, jointly, or via a theory-motivated contrast — shows a detectable effect**, across three independently-constructed tests that all agree.
- **A cluster-robust joint test initially suggested a marginal within-club signal (p=0.035); this did not survive scrutiny** and is documented here as a caught and corrected false positive, not a finding.
- **Valuation staleness, initially misdiagnosed twice, was ultimately traced to a real, sensible mechanism** (transfer-window batching) that is fully absorbed by the model's existing season fixed effects.

---

## Limitations

- **No individual position, and no attack-vs-defense grouping, can be recommended based on this analysis** for a specific club's own strategy — only the described between-club profile finding is well-evidenced.
- **31 clusters, several with only 1–2 seasons, makes cluster-robust inference unreliable for tests that aren't cross-checked** — as demonstrated directly by the retracted p=0.035 result. Any future test in this framework should be checked against a classical or bootstrap alternative before being reported.
- **Relegation and promotion make the sample survivorship-shaped**, not a fixed random panel — unaddressed here.
- **The dependent variable was validated structurally and against real football history for one club across all 14 seasons, not exhaustively against official standings for all 252 club-seasons.**
- **Region grouping (Left/Right Midfield in Central Midfield rather than Winger) remains untested**, now lower priority given the within-club null.
- **Reverse causality is only partially addressed** — same-season minutes still weight the region-value calculation.
- **Position labels don't capture tactical role**, an omitted wage-bill variable likely explains points better than squad value, and findings may be Bundesliga-specific.

---

## Roadmap

- **Systematic dependent-variable validation** against official Bundesliga standings for all 252 club-seasons.
- **A wild cluster bootstrap** as a standard cross-check for any future cluster-robust test in this framework, given the demonstrated over-rejection risk.
- **Investigate the between-club defensive-value pattern further** — is negative defensive-midfield value a real effect, or a proxy for something else (e.g. clubs under relegation pressure investing heavily and unsuccessfully in defensive midfield)?
- **Phase 2 — performance drivers**, still paused on data availability, now framed around the between-club defensive-value pattern rather than a specific position.
- **A fully rigorous version** would use a within-transformed FE estimator matched to the effective (not raw) cluster count, and test the Mundlak club-means directly against a total-value control rather than reading them descriptively — scoped here for time and portfolio purposes rather than pursued.

---

## Technical Notes

- **Views converted to tables** — source data is a static snapshot, so materialized tables replaced views throughout.
- **An index that hurt, and one that helped.** Adding an index on the `appearances` join columns misled the query optimizer into a much worse plan earlier in this project; a `(player_id, date)` index on `player_valuations` was necessary and made the as-of construction fast.
- **Unconditional hash joins can produce silent cartesian explosions.** A diagnostic query without `STRAIGHT_JOIN` caused MySQL to hash-join two large tables with no shared condition, producing an intermediate result of ~4.29 billion rows.
- **A cluster-robust joint test can disagree with a classical F-test on the identical model comparison — check both.** This project's clearest methodological lesson: with a small, uneven number of clusters, don't trust a single test type for a joint hypothesis.

---

## Quickstart

1. **Database setup:** Create a MySQL schema (any name), load the Transfermarkt CSVs into it, connect to it, then run `pipeline.sql` — a single, idempotent script (its `DROP TABLE IF EXISTS` header makes it safe to re-run from scratch).
2. **Diagnostics:** connected to the same schema, run `checks.sql` — it holds the queries used to verify row counts, missingness, join integrity, and data quality.
3. **Python environment:** `pip install pandas numpy statsmodels sqlalchemy pymysql matplotlib`
4. **Run the analysis:** edit the connection string at the top of `main.py` with your own password and schema name, then run it — the club fixed-effects and Mundlak models are the primary specifications; non-FE specifications are retained for the between/within comparison described above.

---

## Structure

```
pipeline.sql          — full data-prep pipeline (single, idempotent script)
checks.sql            — diagnostic / data-quality queries
python/main.py        — model specifications, VIF, influence diagnostics, club-FE and Mundlak models
coef_comparison.png   — non-FE vs. club-FE coefficient comparison plot
CHANGELOG.md          — full revision history: what earlier drafts got wrong and how it was found
```

---

## Status

Phase 1 (squad value → league points) is complete. The final, evidence-based conclusion: squad value distribution is associated with points between clubs — with defensive value (centre-back, full-back, defensive midfield) as the specific, well-evidenced part of that pattern — but no individual position's within-club investment can be shown to drive a club's own points, a conclusion triangulated across three independent tests after an initial, seemingly-positive result turned out to be a statistical artifact. That correction process, along with every other one in this project, is documented in `CHANGELOG.md`.
