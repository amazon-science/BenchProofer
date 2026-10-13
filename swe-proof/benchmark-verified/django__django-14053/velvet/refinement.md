# refinement.md — django__django-14053

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `reportCollected` `do` block plus the deep `collect`/`upsert` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). There are **no A legs** in this bundle: the changed function's new
behavior is modeled deeply over its read-only input stream `events`, and the one
callee involved (`_post_process`) is unchanged and supplies only that stream
(mapping.md §3.1). So there are no axioms, no `axiom_check.py`, and G-AX is a
skip.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The yield site — `HashedFilesMixin.post_process` (`storage.py:203`)

Gold hunks (`storage.py:226-262` post-patch): introduce
`processed_adjustable_paths = {}`; in the initial pass yield only non-adjustable
files / exceptions and collect adjustable files into the dict; in each adjustable
pass overwrite the dict entry instead of yielding; after the passes
`yield from processed_adjustable_paths.values()`.

| # | Solution.lean impl op (`reportCollected`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `events : List Obs` (read-only, not `mut`) | the stream produced by `self._post_process(...)` across all passes, restricted to adjustable observations | R | stream-of-records ↔ `List Obs` via the row bijection `(name, hashed_name) ↔ (fst, snd)` (mapping.md §2). `events` is read-only: the loop never mutates it (directive 5 — `ensures` frame is implicit, no `mut` on `events`). |
| A2 | `let mut result : List Obs := []` | `processed_adjustable_paths = {}` | I | initialize the order-preserving accumulator empty (the dict). |
| A3 | loop body `result := upsert result e.1 e.2` for each `e` in stream order | `processed_adjustable_paths[name] = (name, hashed_name, processed)` (executed in the initial pass for adjustable files, and in every adjustable pass) | I | one order-preserving keyed upsert per observation; `upsert` = "fresh key appended in first-encounter order, existing key overwritten in place" is exactly Python `dict` assignment semantics on `name`. mapping.md §3.2. |
| A4 | `return result` (= `collect events` by the loop invariant) | `yield from processed_adjustable_paths.values()` | I + R | reading the dict out in insertion order ↔ `result` in first-encounter order; the `out = collect events` postcondition pins the read-out to the keep-last/first-order collapse. The materialized generator's adjustable-file suffix ↔ `out` element-wise (R, row bijection). |
| A5 | `ensures (out.map Prod.fst).Nodup` | the F2P property: no `name` reported twice (`assertCountEqual(post_processed, set(post_processed))`) | I | dict keys are unique ⇒ `values()` reports each `name` once; the deep model proves `collect_nodup`. This is the discriminating clause the prepatch violates. |

Discriminating content of the change — a `name` observed in N passes is reported
**once** (post-patch) vs **N times** (pre-patch). It lives in `out = collect
events` together with `(out.map Prod.fst).Nodup`. The pre-patch skeleton
(`Solution_prepatch.lean`) yields every observation raw (`result := result ++
[e]`, i.e. `out = events`), so for any stream with a repeated key it has
`out ≠ collect events` AND `¬ (out.map Prod.fst).Nodup` — `prove_correct`
**fails on both** clauses (G-DIFF). This is exactly the pre-patch
`for ...: yield name, hashed_name, processed` (re-emit per pass).

## B. The unchanged callee — `_post_process` (no axiom)

`self._post_process(...)` (`storage.py:251`) is **not changed** by the patch and
is **not axiomatized**. Its sole role is producing the observation stream that is
the read-only input `events`. There is therefore no consumed axiom and no
A-reference deep model of a callee — `collect` is a deep model of the **changed
function's own** new dedup behavior, not of a callee. (mapping.md §3.1.)

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — replacing the
per-pass raw `yield` with an order-preserving keep-last dict collapse yielded
once at the end — is modeled **deeply** by `upsert`/`collect` and the verified
`while` loop (steps A2-A5), not hidden behind any axiom. No row is A.

## D. verify(Solution) ⇒ resolved

`reportCollected` verifies only if `out = collect events` (A4) and
`(out.map Prod.fst).Nodup` (A5). By R (`(name, hashed_name) ↔ Obs`, stream ↔
`List Obs`, mapping.md §2) the verified `out` equals the post-patch
`list(post_process(...))` adjustable-file report on every stream the real
`_post_process` can produce; by G-CONF the R/I transliteration of
`collect`/`upsert` agrees with the **real patched** `post_process` over ≥10⁵
fuzzed streams (including non-adjustable and exception records). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The single trust
point is refinement fidelity (this doc, G-CONF + G-EQ); there are no axioms
(G-AX skip).
