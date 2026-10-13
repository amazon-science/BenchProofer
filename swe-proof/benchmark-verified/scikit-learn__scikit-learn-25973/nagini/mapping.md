# mapping.md — scikit-learn__scikit-learn-25973

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 10dbc142bd17ccf7bd38eec2ac04b52ce0d1009e`, states the type
abstraction, and gives the provenance of the consumed axiom and the deep-model
references (callee source + the exact behaviour each is validated against).

Repo file under change: `sklearn/feature_selection/_sequential.py`.

The fix introduces a call to one UNCHANGED library helper, `check_cv`, which
turns the configured cross-validation source into one that presents its whole
split family on every draw, BEFORE the selection loop, and threads the result
through every candidate scoring. That helper is modelled as a single consumed
`@ContractOnly` axiom (`secure_reusable_source`) whose `Ensures` is the unique
grantor of the abstract capability `presents_family`. The per-draw semantics (how
many splits one draw yields, given the source's facets and the draws that
preceded it) are modelled DEEPLY (`draw_count` / `step_completes`) and validated
== the real source's `split` by axiom_check.py / G-AX (A-reference).

Two things the earlier revision of this document got wrong are corrected here and
machine-measured in §4: the model's step index is the **candidate scoring**, not
the selection round; and the CONFIGURED source's own consumption is a modelled
observable, not an unconstrained one.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_features(src, n_scorings)` | `SequentialFeatureSelector.fit(self, X, y)` — `sklearn/feature_selection/_sequential.py:189`; the selection loop is `:276-284` and the per-candidate loop it drives is `_get_best_new_feature_score`'s `:302-315` | the modeled changed function: secures, before the selection loop, a source that presents its family on every draw, then draws it once per candidate scoring and reports the per-scoring counts + that source |
| `n_scorings` | the TOTAL number of candidate scorings one `fit` performs: `sum over rounds r < n_iterations of len(candidate_feature_indices)` = `sum_{r<n_iterations} (n_features - r)`, where `n_iterations` is `_sequential.py:268-272` and the candidate list is `np.flatnonzero(~current_mask)` at `:300` | the model's step count. NOT `n_iterations`: `fit` performs one `cross_val_score` — hence one `cv.split(...)` draw and one kept aggregate score — per CANDIDATE per round (`:308-315`), so a round contributes as many scoring steps as it has candidates. Measured exactly on the real patched repo over 20 configs (§4.1). |
| `secure_reusable_source(src)` *(A-consumed axiom)* | `check_cv(self.cv, y, classifier=is_classifier(self.estimator))` — `sklearn/model_selection/_split.py:2406` (called at `_sequential.py:262` post-patch) | unchanged library helper the fix now CALLS once before the loop; returns a source carrying the same split-family size and presenting it on every draw; unique grantor of the `presents_family` capability. Its consumption of the CONFIGURED source (exactly one draw when that source is one-shot, no score kept) is part of the contract. Validated == real `check_cv` by G-AX. |
| `presents_family(cv, src)` *(A-consumed capability, `@ContractOnly @Predicate`)* | the EFFECT of `check_cv(src, …)` returning a `_CVIterableWrapper` built from THAT argument (or a new-style splitter): a source whose every `.split()` re-presents the full split family of the source it was built from | unforgeable token naming BOTH sources. Abstract (no body), so it cannot be `Fold`ed; obtainable ONLY from `secure_reusable_source`'s `Ensures`, and only for the pair (its result, its argument). Pins "the scoring steps drew a source that presents THE CONFIGURED source's family on every draw" — which has no value-level witness (the family size alone is forgeable by echo, and a same-size family is forgeable by construction). Soundness check by G-AX. |
| `draw_splits(cv)` *(A-consumed axiom)* | ONE `cv.split(...)` draw inside one `cross_val_score(..., cv=cv, ...)` call (`_sequential.py:308-315` → `_validation.py:274`, `indices = cv.split(X, y, groups)`) | the per-scoring draw as an OPERATION rather than a computation: it advances the source's draw ledger by exactly one and reports the count that draw presented (`draw_count` of the facets and the prior-draw tally). The only way to obtain a draw. Its precondition `draws_taken == scores_kept` states that no draw is outstanding, i.e. the previous scoring's draw has already been aggregated. Validated == one real `.split()` by G-AX. |
| `keep_score(cv, c)` *(A-consumed axiom)* | one candidate scoring's aggregation: the `cross_val_score(..., cv=cv, ...).mean()` value stored into `scores[feature_idx]` at `_sequential.py:308-315` | keeping the ONE aggregate score a scoring step builds from its OWN draw. Its precondition `draws_taken == scores_kept + 1` states that exactly one draw is outstanding and that the committed count is that draw's, so a step cannot keep a score without drawing for itself. 1:1 with `draw_splits` in the real code: one `cross_val_score` call = one `cv.split(...)` draw = one stored score. Measured in §4.1. |
| `materialisable(src)` *(A-consumed domain token, `@ContractOnly @Predicate`)* | that `check_cv(src, …)` MATERIALISES its argument: the argument reaches the wrapping branch `_CVIterableWrapper(cv)` (`_split.py:2460`, taken when `not hasattr(cv, "split")`) or the `Integral` branch (`:2442-2451`), so the source the call returns is BUILT from the argument's family rather than BEING the argument | domain token, held by the source the caller supplies (exactly as `has_ledger(src)` is) and consumed by the one securing step. Abstract (no body), so no implementation can `Fold` it. Required by `select_features` and by `secure_reusable_source` only where the securing guarantee is not automatic — `Implies(src.reusable == False, materialisable(src))` — because `check_cv`'s third branch is `return cv` (`:2462`), a PASS-THROUGH that hands a one-shot argument straight back: for such an argument `Result().reusable == True`, `presents_family(Result(), src)` and the one-draw consumption are ALL false, and the real procedure does not present the specified behaviour at all. Which realizations are on which side is measured in §4.3. |
| `has_ledger(cv)` *(A-consumed: abstract `@Predicate`)* | that the object is a cv source whose consumption is observable at all | the token that makes a source's two tallies readable. Abstract, so no implementation can grant it; `secure_reusable_source` grants it for its result and preserves it for its argument. |
| `draws_taken(cv)` *(A-consumed `@Pure @ContractOnly` reader)* | how many draws have been taken off THAT object so far: for the secured source, the count of per-candidate `cross_val_score(..., cv=cv, ...)` draws; for the configured source, the count of consumptions of `self.cv` itself (`check_cv`'s `list(cv)` materialisation, plus any `cross_val_score(..., cv=self.cv, ...)`) | LEDGER 1. Abstract, so no implementation can set the tally; `secure_reusable_source` starts the result's at 0 and `draw_splits` is the sole `+1`. Every source that has the ledger keeps its OWN tally, the configured one included, and the two are separate resources — which is what lets the spec say where the procedure did NOT draw. Pins a control-flow effect with NO value-level witness: a source presenting its full family reports the SAME count on every draw, so the per-scoring counts are identical whether each step drew or one remembered number was reused. Soundness check by G-AX; measured on the real repo in §4.1-4.2; differentially measured by G-CONF. |
| `scores_kept(cv)` *(A-consumed `@Pure @ContractOnly` reader)* | how many aggregate scores have been KEPT from a draw of THAT object — i.e. how many `cross_val_score(..., cv=<that object>, ...).mean()` values were stored | LEDGER 2. `keep_score` is its sole `+1`, and it may run only while exactly one draw is outstanding, so the PAIR of tallies records the ORDER the two effects interleaved in and not merely their totals. This is what makes "every step drew for itself" expressible. NB the witness is the stored score, not a `_aggregate_score_dicts` call: `cross_validate` invokes that helper twice per scoring, so it is 2:1 with a kept score and would be the wrong binding (measured, §4.1). |
| `score_from_draw(cv, k)` *(A-consumed `@Pure @ContractOnly` reader)* | the split count that the `k`-th draw of that object presented and that the `k`-th kept score was aggregated over — the length of the per-split score list `_aggregate_score_dicts` receives for scoring `k` (`_validation.py:309`) | the JOURNAL the kept scores form. No implementation can write it (`keep_score` is the only writer), so a reported record required to equal this journal cannot be assembled out of remembered numbers. An empty draw ⇒ an empty list ⇒ `scores[0]` raises `IndexError` (`_validation.py:1948`), the reported failure. |
| `draw_count` / `step_completes` *(deep model — A-reference)* | one `cv.split(...)` draw inside `cross_val_score` (`_sequential.py:308-315`); a draw's emptiness ↔ `_aggregate_score_dicts` indexing an empty list (`_validation.py:1948`) | pure spec: the number of splits a single draw yields, as a function of source facets and prior draws; validated == real source `.split()` by G-AX |
| `MustTerminate(...)` in every contract | that `fit` returns `self` (`_sequential.py:292`) after a bounded `range(n_iterations)` loop over a bounded candidate list | the total-correctness obligation. `fit` is a terminating routine, so the model's must be too; without the obligation Nagini's default partial-correctness reading lets a routine that never returns discharge every postcondition vacuously while producing no record. The measure decreases across the scoring loop (`n_scorings - i + 1`), and each modelled operation carries the strictly smaller measure `1`, so an impl may perform the operations but may not diverge and may not discharge its own obligation by re-invoking itself. |
| `SplitSource` (`.size`, `.reusable`) | the `cv` cross-validation split source: `self.cv` as configured (`_sequential.py:186`), and post-patch the `cv` threaded `fit` → `_get_best_new_feature_score` → `cross_val_score(..., cv=...)` (`:296`, `:312`) | the cross-validation split source whose family size and per-draw presentation govern each scoring's draw |
| `SelectionResult` (`.counts`, `.cv`) | the per-scoring outcome of `fit` (each candidate scoring's `cross_val_score(...)` aggregation) together with the `cv` source those scorings drew | the observable the spec pins: the per-scoring split counts AND the source actually drawn — so the counts must flow from a witnessed secured source, not be echoed off the input |

The per-scoring draw site the change threads the source THROUGH:
`_get_best_new_feature_score(... cv ...)` (`:294`, called at `:296`) calls
`cross_val_score(estimator, X_new, y, cv=cv, scoring=..., n_jobs=...).mean()`
(`:308-315`) once per candidate. `cross_val_score` → `cross_validate` runs its own
`check_cv` (`_validation.py:265`) and then draws `cv.split(...)` once
(`_validation.py:274`); an empty draw makes `_aggregate_score_dicts` index an
empty `scores` list (`_validation.py:309`, `:1948`), raising `IndexError` (the
reported failure). "Whether a scoring's draw is non-empty" abstracts this draw.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `cv` cross-validation source (int / splitter / iterable / generator) | `SplitSource` with `size: int` (split-family size) and `reusable: bool` | the number of `(train, test)` pairs the source yields per draw ↔ `size`; "a source whose draws after the first present nothing" ↔ `reusable == False`; "a source whose every draw re-presents its whole family" ↔ `reusable == True`. These two facets do NOT decide which `check_cv` branch a source takes — that is `hasattr(cv, "split")` (`_split.py:2459`), an independent property — so the branch is carried as a separate DOMAIN token, `materialisable(src)` (§1), and the precondition admits a `reusable == False` source only together with it. The reported input (a `LeaveOneGroupOut().split(...)` generator) is `reusable == False` AND materialisable — it carries no `.split`, so `check_cv` wraps it — so it is admissible and is the case the specified behaviour turns on. A one-shot source that carries its OWN `.split` takes the pass-through branch and is NOT admissible; measured in §4.3. |
| the total candidate-scoring count (§1, `n_scorings`): `sum_{r<n_iterations}(n_features - r)`, driven by `n_iterations` (`_sequential.py:268-272`), `for _ in range(n_iterations)` (`:276`) and `for feature_idx in candidate_feature_indices` (`:302`) | `n_scorings: int >= 1` and `while i < n_scorings` | scoring index `i` ↔ the position of that `cross_val_score` call in the flattened (round, candidate) order; `n_scorings >= 1` (a fit always scores ≥ 1 candidate for the tested configs). The nesting is flattened because nothing the tested behaviour observes distinguishes the two levels: every candidate scoring is one independent draw-and-aggregate of the same source, and the `IndexError` is raised by whichever one first sees an empty draw. |
| scoring `k`'s `cross_val_score(...).mean()` being computable iff `cv` yielded ≥ 1 split in that draw | `step_completes(reusable, size, k)` ⇔ `draw_count(reusable, size, k) > 0` | "scoring `k` produced a usable (non-error) score" ↔ "scoring `k`'s draw was non-empty"; the `IndexError` on an empty draw ↔ a draw count of `0` |
| `cv = check_cv(self.cv, y, classifier=...)` computed once before the loop (`:262`), then `cv` passed to every candidate scoring (`:296`, `:312`) | `cv = secure_reusable_source(src)` once before the loop (granting `presents_family(cv, src)`), then drawn by every scoring step | the source secured before iterating, presenting its family on every draw ↔ the source carrying the `presents_family` capability drawn on every step |
| `check_cv`'s consumption of the configured source: on the iterable path `_CVIterableWrapper.__init__` does `self.cv = list(cv)` (`_split.py:2360`) — one traversal — and no later line of the patched `fit` or `_get_best_new_feature_score` mentions `self.cv` | the securing step takes exactly ONE draw of a one-shot `src` and keeps no score from it: `Implies(src.reusable == False, draws_taken(src) == Old(draws_taken(src)) + 1)` and `scores_kept(src) == Old(scores_kept(src))` | "the configured generator is materialised once and never consumed again" ↔ "the configured source's ledger stands at one draw and zero kept scores". Measured on the real repo (§4.2). Stated conditionally on `reusable == False` because `check_cv`'s other paths consume differently: the pass-through path (`return cv` for a source carrying its own `.split`) draws the argument once per later `.split()`, and the integral path draws it not at all — so an unconditional draw count would be UNFAITHFUL. The pass-through path is kept OUT of the `reusable == False` case by the `materialisable(src)` token (§1, §4.3): on that path a one-shot argument's ledger reaches one draw per later scoring, not one over the whole procedure. One-shot is the branch the gold patch changed and the branch the F2P test exercises. |
| `fit` returns `self` (`:292`); the per-scoring `cross_val_score` outcomes use the source threaded through | `SelectionResult(counts, cv)` | the per-scoring split counts and the source those scorings drew |
| `fit` terminates | `MustTerminate` in `select_features`'s precondition, measure `n_scorings - i + 1` on the loop, measure `1` on each modelled operation | a routine that answers ↔ a routine that discharges the obligation. See §1's `MustTerminate` row. |

The per-draw split COUNT and whether the source re-presents its family are the
only features of a CV source the tested behaviour observes (empty draw ⇒
IndexError; non-empty ⇒ a score), so the source is abstracted to those two
facets; the actual train/test index arrays are irrelevant to the bug and are not
modelled.

## 3. Consumed axiom + deep-model provenance (checked by G-AX / axiom_check.py)

### 3.1 `secure_reusable_source` + `presents_family` ↔ `check_cv` (A-consumed)
**Callee:** `sklearn.model_selection.check_cv(cv, y, *, classifier)`
(`sklearn/model_selection/_split.py:2406`). Source (base_commit):

```python
def check_cv(cv=5, y=None, *, classifier=False):
    cv = 5 if cv is None else cv
    if isinstance(cv, numbers.Integral):
        ...
        return StratifiedKFold(cv) / KFold(cv)
    if not hasattr(cv, "split") or isinstance(cv, str):
        if not isinstance(cv, Iterable) or isinstance(cv, str):
            raise ValueError(...)
        return _CVIterableWrapper(cv)            # the iterable/generator path
    return cv                                    # new-style splitter passed through
```

For an iterable (incl. a single-use generator) `check_cv` returns a
`_CVIterableWrapper`, whose constructor materialises the iterable into a list and
whose `split` re-presents that list on every call (`_split.py:2353-2403`):

```python
class _CVIterableWrapper(BaseCrossValidator):
    def __init__(self, cv):
        self.cv = list(cv)                       # materialise once == ONE draw
    def get_n_splits(self, X=None, y=None, groups=None):
        return len(self.cv)
    def split(self, X=None, y=None, groups=None):
        for train, test in self.cv:              # re-presents the full list each call
            yield train, test
```

**Consumed axiom contract (`secure_reusable_source`):** stated for an argument
the call MATERIALISES whenever that argument does not already present its family
on every draw (`Requires(Implies(src.reusable == False, materialisable(src)))`,
§1) — i.e. for the wrapping and integral branches, since the pass-through branch
`return cv` (`_split.py:2462`) hands a one-shot argument back unchanged and
guarantees none of what follows (§4.3). On that domain: the source `check_cv`
returns carries the SAME split-family size as the configured source
(`Result().size == src.size`, count preservation), presents that family on every
draw (`Result().reusable == True`), starts both of its own ledgers at zero, and
the call is the unique grantor of `presents_family(Result(), src)`. It also
states what the call does to the CONFIGURED source's ledgers: it keeps no score
from any draw of it (`scores_kept(src)` unchanged) and, when that source is
one-shot, takes exactly one draw of it (`+1`) — the `list(cv)` materialisation
above. This is the WEAKEST contract the proof needs: it asserts only
count-preservation, re-presentation, the capability grant, and the one-draw
consumption; it encodes neither `check_cv`'s int-input splitter construction, nor
its `ValueError` raise path, nor the actual split index arrays — none are needed.
**Why a capability, not a value:** "secured a source that presents its family on
every draw" is a control-flow property of the routine, not a value the result
carries (the family size `src.size` is the same whether or not a re-presenting
source was secured — so a value-only postcondition is echo-satisfiable). The
abstract `presents_family` token (granted only by this axiom, un-`Fold`able,
non-launderable across value-equal copies, and naming the ARGUMENT as well as the
result so a same-size family built from scratch does not satisfy it) pins it; the
result's `Ensures(presents_family(Result().cv, src))` forces every verifying impl
to route through this call.

### 3.2 `draw_count` ↔ a CV source's `split()` (A-reference, draw semantics)
**Re-presenting source** (`_CVIterableWrapper`, or any new-style splitter): each
`.split()` iterates the stored family afresh, so a draw yields `size` splits on
every step regardless of prior draws ⇔ `draw_count(True, size, prior) == size`.

**One-shot source** (a raw `LeaveOneGroupOut().split(...)` generator, the input
passed directly pre-patch): the generator yields its `size` pairs on the first
iteration and is then exhausted, yielding `0` on every later iteration ⇔
`draw_count(False, size, 0) == size` and `draw_count(False, size, prior>=1) == 0`.
This is the modelled exhaustion — the pre-patch cause of the reported
`IndexError` from the second candidate scoring on.

### 3.3 `draw_splits` / `keep_score` / the two ledgers ↔ one scoring's draw and aggregation (A-consumed)
One `cross_val_score(..., cv=cv, ...)` call performs exactly one `cv.split(...)`
draw (`_validation.py:274`) and yields exactly one aggregate value that
`_get_best_new_feature_score` stores (`_sequential.py:308-315`). So per scoring
step the real code advances the draw tally by one and the kept-score tally by one,
in that order, and the score it keeps is aggregated over exactly the splits of
that draw (`_validation.py:309`) — which is the `draws_taken == scores_kept` /
`draws_taken == scores_kept + 1` alternation and the `score_from_draw` journal.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `check_cv` on a
single-use split GENERATOR (`LeaveOneGroupOut().split(X, y, groups)`, the exact
reported scenario) and on a `KFold` splitter, then draws the returned source once
per step across many steps, asserting every draw yields the full positive family
(== `draw_count(True, size, *)`, the `presents_family` capability) and that the
size is preserved (== `secure_reusable_source(src).size == src.size`). It also
runs the RAW generator and asserts it yields the full family on the first draw and
`0` thereafter (== `draw_count(False, size, prior)`), confirming the modelled
exhaustion (the pre-patch IndexError cause) is real. It measures the securing
step's own consumption of the configured source (== the `+1` draw / unchanged
kept-score clauses of §3.1) and the 1:1 draw↔kept-score alternation of §3.3. It
imports only the package under test (`sklearn`, `numpy`); exit 0 iff sound.

## 4. Ledger bindings measured on the real repository

Both measurements drive the real `SequentialFeatureSelector.fit` end-to-end in
the instance image and count real events; they are what makes §1's ledger rows
claims about this repository rather than about the model.

### 4.1 `n_scorings`, and the 1:1 draw ↔ kept-score correspondence
Probe: count `KFold.split` calls on the configured splitter and
`cross_val_score` calls made from `_sequential`, for
`n_features ∈ {3,4,6} × k ∈ 1..n_features-1 × direction ∈ {forward, backward}`
(20 configs), gold-patched. Result: **for every config,
`draws == cross_val_score calls == sum_{r<n_iterations}(n_features - r)`** — e.g.
`n_features=6, k=5, forward`: `n_iterations=5`, predicted `6+5+4+3+2 = 20`,
measured `draws=20`, `scorings=20`. That is §1's `n_scorings` row and §3.3's
1:1 claim. The same run shows `_aggregate_score_dicts` firing **2× per scoring**
(40 for 20 scorings), which is why §1 binds `scores_kept` to the stored score and
not to that helper.

### 4.2 The configured source's own ledgers
Probe: a counting one-shot generator standing in for `LeaveOneGroupOut().split(…)`
as `cv`, recording every fresh consumption, plus a count of the scorings whose
`cv=` argument was that generator (`n_features=4, k=2, forward`, so
`n_scorings = 4+3 = 7`):

| repo state | `draws_taken(src)` | `scores_kept(src)` | `scores_kept(secured)` | outcome |
|---|---|---|---|---|
| **gold-patched** | **1** | **0** | **7** | completes |
| pre-patch (`cv=self.cv` per candidate) | 2 | 1 | 0 | `IndexError` |
| hoist `check_cv` but do NOT thread it | 2 | 0 | 0 | `IndexError` |

The gold row is exactly what the spec's configured-source postconditions state
(both stated for the one-shot case, which is the case this probe drives:
`src.reusable == False ⇒ scores_kept(src) == 0`;
`src.reusable == False ⇒ draws_taken(src) == 1`; and
`scores_kept(Result().cv) == n_scorings`, here 7). Both non-resolving rows
violate the draw-count clause (2 ≠ 1). The third row is the shape a recorded
refutation materialised: it hoists the securing call — so it can carry
`presents_family` — yet leaves the per-candidate scoring drawing the configured
source, and the configured source's ledger is what exposes it. (Its
`scores_kept(src)` reads 0 only because the `IndexError` aborts before the score
is stored; the discriminating clause for that row is the draw count.)

### 4.3 Which sources the securing step MATERIALISES (the `materialisable` domain)
Probe: real `check_cv(src, y, classifier=True)` on each realization the type
abstraction (§2) maps into the model, recording whether the call returns its
ARGUMENT (`out is src`, the pass-through `return cv` at `_split.py:2462`) and how
many splits the RETURNED source presents on two consecutive draws; then the real
gold-patched `SequentialFeatureSelector.fit` driven end-to-end on the same source
with the §4.2 configuration (`n_features=4, k=2, forward`, so `n_scorings = 7`,
family size 3), reading the per-scoring split counts off the `scoring` callable
and the configured source's own consumptions off the source itself:

| `cv` realization | model facets | `check_cv` | returned source's 2 draws | patched `fit` | `draws_taken(src)` | admissible |
|---|---|---|---|---|---|---|
| one-shot GENERATOR, no `.split` | `size=3, reusable=False` | WRAPS (`_CVIterableWrapper`) | `(3, 3)` | completes, counts `[3]*7` | **1** | **yes** |
| one-shot object WITH `.split` | `size=3, reusable=False` | PASS-THROUGH (`out is src`) | `(3, 0)` | `IndexError` | 2 | no |
| shrinking object WITH `.split` | `size=3, reusable=False` | PASS-THROUGH (`out is src`) | `(3, 2)` | completes, counts `[3,2,2,2,2,2,2]` | 7 | no |
| `KFold(3)` splitter | `size=3, reusable=True` | pass-through | `(3, 3)` | completes | — | yes |
| list of 3 splits | `size=3, reusable=True` | WRAPS | `(3, 3)` | completes | — | yes |
| integer `3` | `size=3, reusable=True` | constructs `StratifiedKFold(3)` | `(3, 3)` | completes | — | yes |

So `reusable` alone does NOT decide the branch: rows 1-3 all abstract to
`reusable == False`, and only row 1 is the branch §3.1's contract describes.
`materialisable(src)` is exactly "the call does not merely hand this source back"
— TRUE of rows 1, 5, 6 (and vacuously not required of the `reusable == True`
rows 4-6, whose guarantees hold on every branch) and FALSE of rows 2-3.
`select_features` admits a `reusable == False` source only together with the
token, so rows 2-3 are outside the specified domain: they are precisely the
sources for which every clause of the securing contract is false and for which
the real patched procedure either raises or reports a different per-scoring
record, and nothing in this bundle is claimed of them. Row 1 is the realization
the specified behaviour turns on, so the narrowing costs the specification none
of the behaviour under change: `size` is preserved, the returned source
re-presents the family on every draw, the configured source's ledger stands at
exactly one draw, and the procedure completes with `counts == [3]*7`.

## G-CONF (differential conformance: MODEL vs REAL patched repo)

`conformance_check.py` refutes the refinement leg no other gate covers — that
`model.py`'s impl region agrees with the real gold-patched repository code.

**Pinned fuzz seed: `SEED = 25973`** (module constant `SEED`;
`TARGET_INPUTS = 100_000`).

**Shadow (provenance "direct").** The `# impl-start`/`# impl-end` region of
`select_features`, copied VERBATIM with only `Assert(...)` and the
`# invariants-start`/`-end` block deleted — the statement lines are
byte-identical to §1's modeled function. Dependencies carried across the same
way: the whole `# pure-start`/`# pure-end` region (`draw_count`,
`step_completes`) and `SplitSource` / `SelectionResult` as plain records
(their model constructors are field stores under permission contracts). No
`PSeq` shim is needed — the model's only sequence is a `List[int]` built by
`append`.

The `@ContractOnly` axioms have no body to copy, so the shadow CALLS the real
callees §1 binds them to — `sklearn.model_selection.check_cv` (`_split.py:2406`,
invoked by the patch at `_sequential.py:262`) for `secure_reusable_source`, and
real draws/aggregations for `draw_splits` / `keep_score` — and MEASURES both
facets of the returned carrier and both ledgers off those real events. Neither
`Result().size == src.size` nor `Result().reusable == True` nor either ledger
clause is assumed; the axioms are exercised. Bridge context reaches those calls
through a module-level `_CTX` rather than the signature, keeping the impl
region's call sites character-for-character §1's.

**Oracle: CALLED, not transliterated.** The real patched
`SequentialFeatureSelector.fit` (§1: `_sequential.py:189`, selection loop
:276-284) is driven end-to-end via `sfs.fit(X, y)`. The `check_cv` call the patch
adds, the threading of `cv` into `_get_best_new_feature_score`, the per-candidate
`cross_val_score(..., cv=cv, ...)` draw (:308-315) and the
`_aggregate_score_dicts` aggregation are all the repo's own code. The modeled
observable is read back through the `scoring` callable: `cross_val_score` invokes
it once per split, so consecutive probe calls sharing a candidate-column
signature count that draw's splits; the stream is segmented into scoring steps by
the repo's own candidate count (`n_features - r`). `tol=None` with an integer
`n_features_to_select` forces `is_auto_select` False (:275), so the repo cannot
`break` early and runs exactly `n_iterations` rounds — hence exactly `n_scorings`
candidate scorings (§4.1). A raise from the real `fit` is recorded as a
DISAGREEMENT, not swallowed.

**Type bridge (§2 inverted).** model -> repo (`concretize_source`):
`SplitSource(size, reusable=False)` becomes a single-traversal GENERATOR of
`size` `(train, test)` pairs (the reported `LeaveOneGroupOut().split(...)`
shape); `reusable=True` becomes a LIST (check_cv's `_CVIterableWrapper` path), a
`KFold(size)` splitter (pass-through path) or the INTEGER `size`
(`StratifiedKFold` construction path), so all four check_cv paths are covered.
`n_scorings` maps onto `n_features_to_select=k` plus `direction` via the repo's
own arithmetic (:268-272 and the per-round candidate count :300): forward gives
`sum_{r<k}(n_features-r)`, backward `sum_{r<n_features-k}(n_features-r)`.
repo -> model (`abstract_source`): a real cv object becomes a `SplitSource` whose
`size` is the family one `.split()` draw yields and whose `reusable` is whether a
SECOND draw re-presents that same positive family. Every generated input
satisfies the Requires by construction (`size >= 1 > 0`, `n_scorings >= 1`,
ledgers at 0 on a fresh object).

**Inputs: 100000, exhaustive-then-fuzz.** The modeled space reachable through the
real `fit` is FINITE (924 configs: `size` 1..6 x 4 realizations x `n_features`
2..7 x both directions x `k` 1..n_features-1, minus the `size < 2` configs
`KFold`/`StratifiedKFold` reject). Phase 1 ENUMERATES all 924 exhaustively —
stronger than 1e5 samples of them, not weaker — boundary configs first: `size ==
1`, `n_scorings == 1` (the case pre-patch gets RIGHT, so it must not be
flagged), the F2P shape (one-shot generator with more than one candidate
scoring), `n_features == 2` (the repo's `ensure_min_features` floor), and each
check_cv path. Phase 2 fuzzes the SAME space to 100000 with the pinned seed,
sampling weighted 1/`trial_cost` so 1e5 real `fit` runs fit the gate's 1800s
budget; that shifts the mix only — full support retained, and every config
already ran once in phase 1, so nothing is dropped. Unweighted the check also
passes (100000 inputs, 0 disagreements, 16m17s in-container).

**Legs.** Leg 1 (impl region): per-scoring split counts + the secured family's
measured `size`/`reusable`. Leg 2 (pure region): `step_completes(...)` vs whether
scoring `k` of the real run actually produced a score. Leg 3 (ledgers): the
secured source's measured draw and kept-score tallies, and the CONFIGURED
source's, against what the impl region's operations claim — the leg that measures
§4.2's table rather than re-deriving it from the model.

**Capable of failing (negative control).** With the gold patch REVERTED the
one-shot-generator inputs drive an exhausted source from the second candidate
scoring, and the real `fit` raises `IndexError: list index out of range` — the
reported bug. Measured in-container: unpatched **252 disagreements over 924
inputs, exit 1**; patched **100000 inputs, 0 disagreements, exit 0**.
