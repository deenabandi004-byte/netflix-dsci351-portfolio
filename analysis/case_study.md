# DSCI 351 — Netflix Analysis, Case Study Writeup

Companion writeup to the code in this repo. Covers the analytics reasoning and the free-response answers from Part 2 of the project.

## Part 2.2.1 — Spark analytics discussion

### Q1. Genre breadth over time
Split `listed_in` on commas and counted the resulting array size per movie, then grouped by `release_year` and averaged. Genre breadth stays roughly stable at **2–3 genres per movie** across every decade — Netflix's tagging convention hasn't gotten meaningfully more or less granular over time.

### Q2. Catalog depth per genre
Exploded `listed_in` so each (movie, genre) pair is its own row, then took `max(release_year) − min(release_year)` per genre. Depth by genre:

| Genre | Oldest | Newest | Depth |
|---|---|---|---|
| Documentaries | 1942 | 2021 | 79 |
| Classic Movies | 1942 | 2018 | 76 |
| Comedies, Dramas, International Movies | 1954 | 2021 | 67 |
| Faith & Spirituality | 2000 | 2021 | 21 |

Netflix's oldest content lives in **Documentaries** and **Classic Movies**; the shallowest catalog is **Faith & Spirituality**.

### Q3. Rating vs. genre breadth
Filtered to only known-valid MPAA/TV ratings (dataset is dirty), then averaged genre count per rating. **UR** ≈ 2.67 avg genres, **TV-Y** ≈ 1.26. Interpretation: unrated content spans multiple genres because there's no gating framework; children's content is narrowly tagged.

### Q4. Added-year vs release-year lag walkthrough
The supplied pipeline computes how many years elapsed between a title's theatrical release and its date added to Netflix:

1. `netflix_parsed` — parses `date_added` (a string like "October 5, 2020") into a proper date, then extracts `added_year`
2. `lag_df` — creates the numeric `lag = added_year − release_year`
3. `lag_exploded` — explodes multi-genre rows so each (title, genre) becomes its own row, and buckets `release_year` into a decade
4. `lag_summary` — groups by (`genre`, `decade`) and computes mean, median, p25, p75 of `lag`, plus a count; filters to groups of at least 5 titles for statistical stability

Output pattern: older content (1940s–1960s) has **50–70+ year** lags because it was added to Netflix decades after theatrical release; recent content has short lags.

## Part 2.2.2 — Optimization results

Workload: the `lag_summary` DataFrame from 2.2.1 Q4. Metric: `df.count()` runtime, measured with `time.perf_counter()`.

| Optimization | Runtime | Δ vs baseline |
|---|---|---|
| Baseline | 1.1998 s | — |
| Cache exploded intermediate | 0.9196 s | −23.4% |
| Column pruning + early filters | 1.0483 s | −12.6% |
| Repartition by group keys | ~data-dependent | ~ |

### Where the shuffles came from
`.explain(True)` on `lag_summary` surfaced two `Exchange` nodes:
1. `Exchange hashpartitioning(genre, release_decade)` — from `groupBy`. Rows for the same key have to be co-located on one partition before the aggregation can run.
2. `Exchange rangepartitioning` — from the final `orderBy`, which needs a global sort.

Shuffles are the expensive parts of a Spark job because they push data across the network and hit disk. All three optimizations target either the shuffle input volume or the pipeline recomputation cost.

### Why cache `lag_exploded`?
It sits immediately after `explode`, which multiplies rows by the average number of genres per title. Caching that materialized wide DataFrame means the aggregation reads from memory instead of rebuilding it from the raw CSV each time — worth 23% here.

### Why column pruning helps
The raw `netflix` DataFrame has 12+ columns but the lag pipeline only needs three (`date_added`, `release_year`, `listed_in`). Dropping the rest early cuts the amount of data that has to be shuffled during `groupBy`, saving both memory and network bytes.

### Why repartitioning by the group keys
`repartition(4, "genre", "release_decade")` pre-partitions data on the same keys the downstream `groupBy` will use. On a real cluster this can eliminate one shuffle stage; on a single-node Colab it's data-distribution dependent — the technique is what generalizes.

## Part 2.3 — MongoDB free response

### Q1. Embed watchlists vs. reference them
**Embed** when watchlists stay small (under ~100 items), are always fetched with the user, and query simplicity matters most. Read performance is best (no join), consistency is easier (single-document atomic updates), and the model is straightforward.

**Reference** when watchlists can grow unbounded (risking the 16 MB document limit), when watchlists need to be queried independently, or when multiple users could share a watchlist. Cross-collection queries need `$lookup` or two round-trips, and multi-document updates need transactions — harder consistency, but scales further.

### Q2. Indexing a `release_year` + `rating` filter that occasionally sorts by `release_year`
**a) Which index:** compound index on `{ release_year: 1, rating: 1 }`. Putting `release_year` first satisfies both the compound filter *and* the sort (leftmost-prefix rule).

**b) Downside of too many indexes:**
- Every insert / update has to also update every index → write throughput drops
- Indexes cost disk space and RAM (working-set pressure)
- The query planner has more candidates to evaluate before executing

**c) Verify usage:** `db.collection.find({ ... }).sort({ release_year: 1 }).explain("executionStats")`. Look for `winningPlan.stage == "IXSCAN"` (index scan) instead of `COLLSCAN`, and compare `totalKeysExamined` vs `totalDocsExamined` — close-to-equal is good, wildly larger docs than keys means the index isn't selective enough.

### Q3. Aggregation pipeline vs. application code

**Factors to weigh:**
1. **Data volume** — pushing computation to the database avoids transferring raw rows over the network
2. **Complexity** — simple `$group` / `$avg` is trivial in an aggregation pipeline; branching business logic is clearer in application code
3. **Frequency** — a hot-path query benefits from being pre-optimized and indexed at the DB layer
4. **Team familiarity** — aggregation pipelines have their own syntax; not everyone can maintain them

**Aggregation pipeline is better:** computing "total movies watched per user + avg rating given" across millions of records. The DB uses indexes, runs in parallel, and returns tiny aggregated results instead of shipping raw rows.

**Application code is better:** computing recommendation scores that call an external ML API, or business logic that changes every sprint. Application code is easier to test, deploy, and reason about when the logic isn't a pure aggregation.
