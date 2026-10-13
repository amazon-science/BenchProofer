# refinement.md — scikit-learn__scikit-learn-25973

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_features` impl region and the pure draw-semantics functions
`draw_count` / `step_completes`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (the proof uses a `@ContractOnly`
contract's `Ensures`), **A-reference** (a deep model validated == the real callee
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There is **one consumed library axiom**: the unchanged helper the fix introduces a
call to — `check_cv` — modelled as `secure_reusable_source` (`@ContractOnly`),
the unique grantor of the abstract capability `presents_family`. The two effects a
scoring step performs on a source (`draw_splits`, `keep_score`) and the ledgers /
journal they write (`draws_taken`, `scores_kept`, `score_from_draw`) are modelled
as abstract operations and readers over the SAME repo events (mapping.md §3.3),
and the per-draw split semantics are modelled **deeply** (`draw_count` /
`step_completes`, A-reference). No axiom is placed on the function under change
(the selection loop is modelled by the verified loop).

The step index is the CANDIDATE SCORING, not the selection round: the real `fit`
performs one `cross_val_score` — hence one `cv.split(...)` draw and one kept
aggregate score — per candidate per round, so `n_scorings =
sum_{r<n_iterations}(n_features - r)`. Machine-measured exactly over 20 configs
(mapping.md §4.1).

## A. The change — secure, before the loop, a source that presents its family on every draw, and thread it through every scoring

The gold patch calls `check_cv(self.cv, ...)` ONCE before the selection loop,
threading the returned source through every candidate scoring — replacing the
per-candidate use of the configured (possibly one-shot) `self.cv`:

```
  fit():
+   cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))
    ...
    for _ in range(n_iterations):
        new_feature_idx, new_score = self._get_best_new_feature_score(
-           cloned_estimator, X, y, current_mask
+           cloned_estimator, X, y, cv, current_mask
        )
  _get_best_new_feature_score(self, estimator, X, y, cv, current_mask):
        ... cross_val_score(estimator, X_new, y,
-           cv=self.cv,
+           cv=cv,
            scoring=self.scoring, n_jobs=self.n_jobs).mean()
```

| # | model.py impl op | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `src: SplitSource` with `.size` (split-family size) and `.reusable` (re-presents family vs one-shot) | the `cv` cross-validation source configured on the estimator (`self.cv`, `_sequential.py:186`) | R | the number of `(train, test)` splits the source yields per draw ↔ `.size`; "a source whose draws after the first present nothing" ↔ `.reusable == False`, "a source whose every draw re-presents its whole family" ↔ `.reusable == True` (mapping.md §2). These facets do NOT by themselves decide which `check_cv` branch a source takes (`hasattr(cv, "split")` does), so the precondition admits a `.reusable == False` source only together with the `materialisable(src)` domain token (A1b): the reported input — a `LeaveOneGroupOut().split(...)` generator, which carries no `.split` and is therefore materialised by the wrapping branch — is admissible and is the case the specified behaviour turns on, while a one-shot source carrying its OWN `.split`, which that helper hands straight back, is outside the domain (mapping.md §4.3). |
| A1b | `materialisable(src)` (`@ContractOnly @Predicate`, abstract/no body), required by `select_features` and by `secure_reusable_source` under `Implies(src.reusable == False, ...)` | that `check_cv(self.cv, …)` MATERIALISES its argument: the argument reaches the wrapping branch `_CVIterableWrapper(cv)` (`_split.py:2460`, taken when `not hasattr(cv, "split")`) or the `Integral` branch (`:2442-2451`), rather than the pass-through `return cv` (`:2462`) | **A-consumed** | a DOMAIN token, exactly as `has_ledger(src)` is: held by the source the caller supplies and consumed by the one securing step. Abstract, so no impl can `Fold` it into existence, and it is not a facet of the source, so it hands the impl no new value to compute with — it only says which sources A3 speaks about. It is what keeps A3/A3b/A3c from claiming more than `check_cv` does: on the pass-through branch the helper returns the ARGUMENT, so `Result().reusable == True`, the `presents_family` grant and the one-draw consumption are all false of the real code, and the procedure raises `IndexError` (machine-measured over six realizations, mapping.md §4.3). Demanded only under `reusable == False` — the weakest sufficient narrowing — because a source that already re-presents its family satisfies the contract on every branch, pass-through included. |
| A2 | `n_scorings: int`, `n_scorings >= 1`, `while i < n_scorings` | the flattened (round, candidate) scoring sequence: `for _ in range(n_iterations)` (`:276`) over `for feature_idx in candidate_feature_indices` (`:302`), i.e. `sum_{r<n_iterations}(n_features - r)` scorings | R + I | one loop pass ↔ one candidate scoring, i.e. one `cross_val_score` call (`:308-315`). The nesting is flattened because every candidate scoring is one independent draw-and-aggregate of the same source and the `IndexError` is raised by whichever one first sees an empty draw; nothing the tested behaviour observes distinguishes the two levels. `n_scorings >= 1`: a fit scores ≥ 1 candidate for the tested configs. Binding measured exactly (mapping.md §4.1). |
| A3 | `cv = secure_reusable_source(src)` evaluated ONCE, before the loop, granting `presents_family(cv, src)` | `cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))` evaluated once, before the loop (`_sequential.py:262`) | **A-consumed** | `check_cv` is the UNCHANGED helper the fix now CALLS. Modelled as `secure_reusable_source`, a `@ContractOnly` callee whose `Ensures` gives size preservation, `reusable == True`, the `presents_family` grant (A3b), zero ledgers on the result, and what the call does to the ARGUMENT's ledgers (A3c). The proof CONSUMES this contract: it is the unique producer of the capability, so the materialisation step cannot be faked. The contract is the WEAKEST sufficient one and is validated == the real `check_cv`/`_CVIterableWrapper` by G-AX (mapping.md §3.1). **Hoisting this call out of the loop and threading its result through is the entire content of the change.** |
| A3b | `presents_family(cv, src)` (`@ContractOnly @Predicate`, abstract/no body) | the EFFECT of `check_cv(self.cv, …)` returning a source built from THAT argument that re-presents its full split family on every `.split()` | **A-consumed** | An unforgeable capability token naming BOTH sources. Abstract, so no impl can `Fold` it; tied to object references, so it cannot be laundered across value-equal copies; and because it names the argument, a same-size family built from scratch does not satisfy it. The ONLY way to obtain it is from `secure_reusable_source`'s `Ensures` (A3). `select_features`'s postcondition `Ensures(presents_family(Result().cv, src))` therefore forces every verifying impl to route the reported source through that call. This closes the echo cheat: securing a re-presenting source is a control-flow property with no value-level discriminator (the family size is the same either way), so it is pinned by the capability, not by a value. Provenance checked by G-AX. |
| A3c | the same call's effect on `src`'s ledgers: `scores_kept(src)` unchanged and, when `src.reusable == False`, `draws_taken(src) == Old(...) + 1` | `_CVIterableWrapper.__init__` doing `self.cv = list(cv)` (`_split.py:2360`) — exactly one traversal of the configured generator — and no other line of the patched `fit`/`_get_best_new_feature_score` touching `self.cv` | **A-consumed** | the securing step is ITSELF the configured source's one and only consumption. Stated conditionally on `reusable == False` because check_cv's other paths consume differently (pass-through: once per later `.split()`; integral: not at all), so an unconditional count would be UNFAITHFUL; one-shot is the branch the patch changed and the branch the F2P test exercises. Measured on the real repo: gold takes exactly 1 draw of the configured generator (mapping.md §4.2). |
| A4 | each step: `c = draw_splits(cv)` — PERFORM one draw of the secured source and record the count that draw presented; advances `draws_taken(cv)` from `i` to `i+1`, permitted only while no draw is outstanding | each candidate: `_get_best_new_feature_score(..., cv, ...)` → `cross_val_score(..., cv=cv, ...)` performs exactly one `cv.split(...)` draw (`_validation.py:274`) | R + **A-consumed** + **A-reference** | Drawing is an EFFECT on the source, so it is modelled as an operation, not as a readable function of the source's facets: it advances the ledger by exactly one and returns `draw_count(reusable, size, prior_tally)` — the **deeply-modelled** per-draw semantics validated == the real source's `.split()` by G-AX (a re-presenting source yields `size` every draw; a one-shot generator yields `size` once then `0`). Making the draw an operation is what forces the loop to actually draw: the count cannot be obtained without advancing the ledger. |
| A4b | each step: `keep_score(cv, c)` — commit the one aggregate score built from THAT draw; advances `scores_kept(cv)` and writes `score_from_draw`, permitted only while exactly one draw is outstanding and only for that draw's own count | each candidate: the `cross_val_score(...).mean()` value stored into `scores[feature_idx]` (`_sequential.py:308-315`), aggregated by `_aggregate_score_dicts` over exactly the splits of that draw (`_validation.py:309`) | R + **A-consumed** | 1:1 with A4 in the real code (one `cross_val_score` call = one draw = one stored score; machine-measured, mapping.md §4.1). The two preconditions (`draws_taken == scores_kept` to draw, `== scores_kept + 1` to keep) make the effects strictly ALTERNATE, which is what forbids taking all the draws up front and then reporting remembered numbers. The score VALUES are irrelevant to the tested behaviour (it only requires no exception); what is modelled is the split count the aggregation ran over, because that is what the `IndexError` depends on. |
| A5 | `return SelectionResult(used, cv)`; postconditions pin the reported source's capability, size, `reusable`, every `counts[k] == draw_count(...) == src.size >= 1`, **both of its ledgers at `n_scorings`**, the record == the journal, **and the CONFIGURED source's ledgers at zero kept scores / one draw** | every candidate scoring's `cross_val_score` draws the threaded `cv` and sees a non-empty split set, so `_aggregate_score_dicts` never indexes an empty list — `fit` completes without `IndexError` | R | "every scoring drew a witnessed source that re-presents the configured source's full positive family, and nothing drew the configured source again" ⇔ "no scoring aggregated an empty score set" ⇔ "`fit` runs without error". |
| A6 | `MustTerminate` in the precondition, measure `1` on each modelled operation, loop measure `n_scorings - i + 1` | `fit` returns `self` (`:292`) after a bounded `range(n_iterations)` loop over a bounded candidate list | R | the procedure must ANSWER. Nagini is partial-correctness by default, so without this a routine that never returns discharges every clause above vacuously while producing no record. The operation measures are strictly below the procedure's, so an impl may perform the operations but cannot discharge its own obligation by re-invoking itself. |

## B. The discriminating clauses and the prepatch

The spec's load-bearing postconditions are

```
Ensures(presents_family(Result().cv, src))                # capability, A3b
Ensures(Result().cv.size == src.size and Result().cv.reusable == True)
Ensures(Forall k: Result().counts[k]
                  == draw_count(Result().cv.reusable, Result().cv.size, k))
Ensures(Forall k: Result().counts[k] == src.size)
Ensures(Forall k: Result().counts[k] >= 1)
Ensures(has_ledger(Result().cv))
Ensures(draws_taken(Result().cv) == n_scorings)           # ledger 1, A4
Ensures(scores_kept(Result().cv) == n_scorings)           # ledger 2, A4b
Ensures(Forall k: Result().counts[k] == score_from_draw(Result().cv, k))
Ensures(has_ledger(src))                                  # the CONFIGURED source
Ensures(Implies(src.reusable == False, scores_kept(src) == 0))    # A3c
Ensures(Implies(src.reusable == False, draws_taken(src) == 1))    # A3c
Requires(MustTerminate(2))                                # A6
Invariant(MustTerminate(n_scorings - i + 1))              # A6, the loop measure
```

These are FIVE independent pins, and every one is load-bearing:

1. **`presents_family(Result().cv, src)`** pins **which object** the scorings
   reported — they secured a re-presenting source built from the configured one,
   rather than reporting the raw configured source or a same-size family made from
   scratch. It has no value-level witness (the family size is the same either
   way), so it cannot be discharged by echoing the input.
2. **`draws_taken(Result().cv) == n_scorings`** pins **that each scoring actually
   drew that source**. The value clauses alone CANNOT express this. Under the
   spec's own forced facts (`Result().cv.reusable == True`,
   `Result().cv.size == src.size`), `draw_count(True, src.size, k)` is the
   CONSTANT `src.size` for every `k`, so the recorded counts are byte-identical
   whether each scoring drew the secured source, reused a single remembered count,
   or echoed the input's family size. The ledger separates them: it starts at 0 on
   a freshly secured source, `draw_splits` is its only `+1`, and neither the
   predicate nor the tally can be produced by an implementation, so a tally of
   `n_scorings` is reachable only by performing `n_scorings` real draws.
3. **`scores_kept(Result().cv) == n_scorings` plus the journal equality and the
   two alternation preconditions** pin **the ORDER**: that each scoring's kept
   score was built from that scoring's OWN draw. A total-tally obligation alone
   would not — a routine could take all `n_scorings` draws up front and then
   report remembered numbers, matching every count clause and both totals. Because
   a score may be kept only while its own draw is the single outstanding one, and
   because each reported entry must equal the journal entry that draw wrote, the
   effects must interleave draw, keep, draw, keep.
4. **The CONFIGURED source's own ledgers** (`scores_kept(src) == 0`, and
   `draws_taken(src) == 1` when it is one-shot) pin **where the procedure did NOT
   draw**. Nothing above constrains them: clauses 1-3 speak only about the source
   the result reports, so a routine that secures a source, reports it with both
   ledgers full — and *separately* leaves some scoring drawing the configured
   source, or re-secures the configured source per scoring — satisfies all of
   them. This is the clause that excludes the whole non-resolving redistribution
   family, and it is measured on the real repository (mapping.md §4.2): gold
   `draws_taken(src) = 1, scores_kept(src) = 0`; pre-patch `2, 1`; the
   hoist-but-don't-thread rival `2, 0`. It is true of the gold patch and false of
   both non-resolving neighbours. Stated conditionally on `reusable == False`
   because `check_cv`'s other paths consume the argument differently (A3c) — a
   narrower statement would be weaker, an unconditional one would be unfaithful.
5. **`MustTerminate`** pins that the procedure ANSWERS. Without it every clause
   above is dischargeable vacuously by a routine that never returns.

Pin 4 is what makes A3c (the securing call's consumption of the configured
source) a stated obligation rather than an unobservable one. Without it the spec
admitted implementations that secure the source, report it with full ledgers, and
still leave a scoring step consuming `self.cv` — machine-confirmed as verifying
while their faithful patch does NOT resolve, because that scoring draws an
exhausted generator and `_aggregate_score_dicts` raises `IndexError`. The reject
cases `scoring-draws-configured-source`, `keep-off-configured-draw` and
`resecure-per-scoring` in properties.py hold that lane closed; pin 5's lane is
held by `diverges-never-answers`.

One refinement rule the pins above make explicit, because the recorded
refutation of the earlier (total-tally) spec travelled exactly this route: **a
scoring step that performs no modelled `(draw_splits, keep_score)` pair does not
refine to a real candidate scoring that performs no draw.** A candidate scoring
IS a `cross_val_score(..., cv=?, ...)` call (A4/A4b, `_sequential.py:308-315`),
and that call always draws whatever source it is handed (`_validation.py:274`).
So a rival whose step performs no modelled draw of the secured source refines to
a real step whose `cv=` argument is something else — in the reachable cases the
configured `self.cv`, which for the reported one-shot input is a modelled draw of
`src` and is fixed at exactly one draw over the whole procedure by pin 4. There
is no admissible third option: the change site cannot score a candidate without
drawing something, and any source it draws is either the secured one (a
`draw_splits(cv)`) or the configured one (a draw of `src`). That is why the
ledger pair is stated as an alternation rather than as two totals: it removes
"the step drew nothing" as a shape a verifying rival can occupy.

`model_prepatch.py` keeps the spec **byte-identical** (the whole spec view,
through `post-conditions-end`, is shared) and reproduces the pre-patch control
flow: it draws the configured source `src` **directly** inside the scoring loop
(`draw_count(cv.reusable, cv.size, i)` on a `cv` carrying the configured
reusability), never calling `secure_reusable_source`. It therefore (i) never
obtains `presents_family` on the source it reports, so it **fails** the capability
postcondition `presents_family(Result().cv, src)` (the reported verifier error is
exactly `There might be insufficient permission to access
presents_family(Result().cv, src)`), and (ii) when the configured source is
one-shot (`src.reusable == False`, the admissible input), records `0` from the
second scoring on, contradicting `counts[k] == src.size`. Both are genuine
pre-patch defects; this is the one independently-observable fixed behaviour, so
one prepatch suffices (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The operation that
genuinely *changed* — securing a re-presenting CV source once before the loop and
threading it through every candidate scoring (vs. drawing the one-shot configured
source per candidate) — is modelled by the consumed axiom `secure_reusable_source`
+ its unforgeable capability `presents_family` (A3/A3b), the ledger effects
`draw_splits` / `keep_score` (A4/A4b) and the deeply-modelled draw semantics
`draw_count` (A-reference). There is **no** axiom about the function under change
(the selection loop is modelled deeply by the verified loop), and no ungrounded
answer-key oracle: the postcondition is pinned by structural relations on the
actual input carrier (`size`, the `draw_count` arithmetic), by the capability that
the result must be *produced by* the securing call, and by ledgers on both sources
that only the modelled operations can advance.

## D. verify(model) ⇒ resolved

`select_features` verifies only if (i) it secures a source carrying the
`presents_family` capability against `src` ONCE before the loop
(`secure_reusable_source`, A3/A3b — the capability cannot be fabricated), (ii)
every scoring step draws that source and aggregates its own draw, so both its
ledgers reach `n_scorings` and every reported count is that draw's journal entry
(A4/A4b), (iii) no step draws or keeps a score off the CONFIGURED source, whose
ledgers stay at one draw and zero kept scores (A3c), and (iv) it answers (A6). By
R (CV source ↔ `SplitSource`, candidate scoring ↔ index, `n_scorings >= 1`) the
verified routine equals the gold `fit`: it computes `cv = check_cv(self.cv, ...)`
before the loop and draws THAT source, and only that source, in every candidate
scoring. By G-AX the axiom + deep models are sound: the real `check_cv` builds a
`_CVIterableWrapper` that materialises a one-shot generator with a single
traversal into a source re-presenting the full count on every `.split()` (== the
`secure_reusable_source` axiom incl. its one-draw consumption of the argument, +
`draw_count(True,size,*)`), one `cross_val_score` is one draw and one kept score
(== `draw_splits`/`keep_score`), and a raw generator exhausts after the first draw
(== `draw_count(False,size,prior)`). Hence every candidate scoring of the real
`fit` likewise sees a non-empty split set, so `cross_val_score` never aggregates
an empty score list and `fit` completes — exactly the F2P requirement
(`test_cv_generator_support` passes; the unchanged P2P selection behaviour is
preserved because the secured source presents the same splits a single consumption
of the configured source would). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement, the consumed `check_cv`
axiom, and the G-AX-audited deep models, and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: axiom/deep-model soundness
(G-AX) and refinement fidelity (this document, G-EQ).
