# refinement.md — scikit-learn__scikit-learn-12973

Maps every operation of `Solution.lean`'s `impl` `do` block to its `patch.diff`
counterpart, tagged **R** (type refinement), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated `== real callee` by
G-AX), or **I** (identical concrete op). Every step is R, A, or I; no changed
op is inexpressible (no kind-3).

## A. The patch (gold, `patch.diff`)

The change makes `LassoLarsIC.fit`'s `copy_X` parameter default to `None`, adds
the resolution `if copy_X is None: copy_X = self.copy_X`, and feeds the resolved
value into the preprocessing call:

```python
-    def fit(self, X, y, copy_X=True):
+    def fit(self, X, y, copy_X=None):
...
+        if copy_X is None:
+            copy_X = self.copy_X
         X, y = check_X_y(X, y, y_numeric=True)
         X, y, Xmean, ymean, Xstd = LinearModel._preprocess_data(
-            X, y, self.fit_intercept, self.normalize, self.copy_X)
+            X, y, self.fit_intercept, self.normalize, copy_X)
```

The second consumer of the buffer, `lars_path(X, y, Gram=Gram, copy_X=copy_X,
...)` (`least_angle.py:1509-1512`), is textually untouched — but the change is
what makes the value it receives be the RESOLVED one. Before, the two consumers
were gated by two different quantities: `self.copy_X` for preprocessing and the
raw per-call parameter (defaulting `True`) for the descent. After, one resolved
decision governs both. See mapping.md §0 for the two call sites and for the TWO
buffers they leave behind.

Observable behaviour:

* F2P `test_lasso_lars_fit_copyX_behaviour` — the caller's `X` buffer is mutated
  in place **iff** the effective copy choice is `False`, where the effective
  choice is the per-call `copy_X` when explicitly supplied and the configured
  `self.copy_X` otherwise. This is an observation of the CALLER's buffer.
* P2P `test_lars_precompute[LassoLarsIC]` — refits one shared module-level
  matrix for `precompute in [True, False, 'auto', None]` with no per-call
  `copy_X` and a configured `copy_X=True` (the constructor default), and compares
  the `coef_` of the runs against each other. Its falsy `precompute` iterations
  are the ones on which the descent can reach the buffer it is handed. This is
  NOT an observation of the caller's buffer: with a truthy gate the preprocessing
  step hands the descent a buffer of its own, so the caller's buffer is preserved
  whatever the descent is told to do. What this test observes is the WORKING
  buffer, through the numbers `fit` reports from it: `fit` reads that buffer
  again at `R = y[:, np.newaxis] - np.dot(X, coef_path_)` (`:1520`), so column
  swaps landing in it move the residuals, hence `criterion_`, `n_best`,
  `alpha_` and `coef_` (mapping.md §0, §3.4). Measured: `coef_` differs between a
  truthy and a falsy descent gate on 39/40 fuzzed matrices.

Both observables are therefore needed, and they are independent: a run that
resolves the choice for preprocessing but forwards the RAW per-call value to the
descent passes the F2P observation and moves the P2P one.

## B. Operation correspondence

| # | `Solution.lean` impl op | `patch.diff` counterpart | tag |
|---|---|---|---|
| 1 | `let copy := effectiveCopy configuredCopy requestedCopy` | `if copy_X is None: copy_X = self.copy_X` — resolve the effective copy choice once (`requested.getD configured`) | **R** |
| 2 | `if copy then return prepareInPlace data target` | effective choice truthy: the resolved value reaches BOTH consumers as a truthy gate. Preprocessing copies internally (`base.py:117`), so the caller's buffer is untouched and the descent is handed preprocessing's own array; the descent then takes its defensive copy (`least_angle.py:176-180`), so that array is left holding exactly what preprocessing produced — and it is that array `fit` goes on to read at `:1520`. The op RETURNS it for that reason | **A-reference** (frames of `_preprocess_data` AND `lars_path`, on both buffers) |
| 3 | `else data := prepareInPlace data target` | effective choice falsy: `_preprocess_data(..., copy=False)` centers the caller's buffer in place (`base.py:150`), so `fit`'s local `X` and the caller's object are the same buffer from here on | **A-reference** (frame of `_preprocess_data`) |
| 4 | `data := searchInPlace data target` | effective choice falsy: `lars_path(X, y, Gram=Gram, copy_X=False, ...)` skips `X = X.copy('F')` and its column swaps (`least_angle.py:268`) land in that buffer, selected using `y` | **A-reference** (frame of `lars_path`) |
| 5 | `return data` (falsy leg) | on this leg the buffer `fit` reads at `:1520` IS the caller's buffer, so the two modeled outputs coincide; the op reports the same array as both | **I** (an aliasing fact of the falsy leg, no repo op of its own) |

### Tag detail

* **#1 (R).** `effectiveCopy configured requested = requested.getD configured`
  is the type-refinement of the Python `if copy_X is None: copy_X = self.copy_X`
  under the bijection `None ↔ none`, `True/False ↔ some true/false`,
  `self.copy_X ↔ configuredCopy`. Pure data-flow; mechanically refuted by
  G-CONF (`conformance_check.py`).
* **#2 (A-reference).** The preserve leg is a claim about BOTH unchanged callees
  at once, and about BOTH buffers. Handed a truthy gate, preprocessing leaves the
  caller's buffer untouched (`data = dataOld`) AND the descent, handed a truthy
  gate, leaves preprocessing's array holding preprocessing's output
  (`work = prepareInPlace dataOld target`). The second half is the one the caller's
  buffer cannot express, because on this leg the caller's buffer is decoupled
  from the descent entirely.
* **#3 / #4 (A-reference).** The overwrite leg composes the two callees'
  in-place effects in call order: the descent operates on whatever preprocessing
  left in the buffer, hence
  `searchInPlace (prepareInPlace dataOld target) target`.
  `searchInPlace` takes the target because the swap selection reads `y`'s
  entries (measured: mapping.md §3.2). `prepareInPlace` takes it for a
  STRUCTURAL reason instead: the carrier is a FLAT array of entries (mapping.md
  §2) and preprocessing reduces COLUMN-WISE (`np.average(X, axis=0)`,
  `base.py:149`), so its output depends on how those entries divide into rows and
  columns — a division the flat carrier does not itself record. The target
  records it, because `check_X_y` (`:1504`) forces `len(y) == X.shape[0]`: the
  target's LENGTH is the row count, so `(dataOld, target)` fix the shape.
  Measured both ways: the same entries under targets of different lengths give
  preprocessing different output (G-AX `A4-shape-is-binding`), and the target's
  own ENTRIES are not read by it (mapping.md §3.1), so this argument is a shape
  witness rather than a numeric dependence. Neither symbol is ever equated to anything in the
  proof, so both are **A-references**, not consumed axioms. G-AX
  (`axiom_check.py`) validates each callee's frame and determinacy against the
  real unchanged callee exercised **directly** — never via `LassoLarsIC.fit`,
  which is the function under spec — over the modeled region of mapping.md §3.3,
  and it validates the composite two-buffer laws (its law D) as well as the
  per-callee ones.
* **#5 (I).** No repo statement corresponds; it records that on the falsy leg
  `fit`'s local `X` and the caller's object are one array, which is why the
  `false` leg's two clauses have the same right-hand side.

There is **no A-consumed axiom**, **no `:|`-stub**, and **no kind-3** op. The
impl region contains one R op (#1) and the A-reference-governed buffer
assignments (#2, #3, #4); `conf_skip = false` because the resolution op #1 is
R-tagged and mechanically checkable.

## C. Why `verify ⟹ correct` (spec-strength argument)

The four `ensures` clauses pin the exit contents of BOTH observable buffers,
ACROSS THE WHOLE RUN, as functions of the effective choice and the modeled
inputs:

* `effectiveCopy … = true  → data = dataOld`
* `bothRoutinesDeliver dataOld target → effectiveCopy … = true  → work = prepareInPlace dataOld target`
* `bothRoutinesDeliver dataOld target → effectiveCopy … = false → data = searchInPlace (prepareInPlace dataOld target) target`
* `bothRoutinesDeliver dataOld target → effectiveCopy … = false → work = searchInPlace (prepareInPlace dataOld target) target`

The three clauses that name a routine's OUTPUT are stated where the two-routine
sequence produces one. Neither routine is total: on a `(buffer, target)` pair
whose reduction leaves the float64 range the routine signals instead of returning
(mapping.md §3.5), and there the composite terms denote nothing, so an
unconditional equation would assert something the repo has no value for. The
hypothesis is a DOMAIN restriction on the modeled callees, not a weakening of the
obligation: it ranges over `(dataOld, target)` alone — not over the copy choice,
which is measured not to affect definedness — so on every pair where it holds all
four clauses bind exactly as they did, and it cannot be used to make a delivered
buffer vary with the choice. The frame clause carries no hypothesis at all,
because routine 1 copies before it reduces and the caller's buffer therefore
survives the preserve leg even on a signalling pair (measured: 297 preserve-leg
observations on the signalling class, 0 violations).

**This does not narrow away the behaviour the patch changes.** On every
signalling pair the pre-patch and post-patch `fit` raise identically (same
exception, same site, all six choice combinations, measured by applying and
reverting `patch.diff` in the built image), so the delta the instance is about
lives entirely on the delivering pairs. The discrimination below is unaffected,
and `Solution_prepatch.lean` still fails to verify.

Four consequences, each of which an implementation must satisfy to verify:

1. **The second routine's gate is constrained on the PRESERVE leg — by `work`,
   not by `data`.** This is the load-bearing clause, and it is worth being
   explicit about why the caller's buffer alone cannot carry it. On the preserve
   leg the first routine works on a buffer of its own, so *whatever* the second
   routine is told to do it cannot touch the caller's buffer: `data = dataOld`
   holds for an implementation that gates the second routine correctly and
   equally for one that gates it by the raw per-call value, by a constant, or by
   nothing at all. A caller's-buffer-only model therefore says nothing about the
   second routine on this leg — which is precisely the shape of behaviour that
   moves `test_lars_precompute[LassoLarsIC]`.

   `work = prepareInPlace dataOld target` is what closes it. An implementation
   that hands the second routine a falsy gate while the effective choice is
   `true` leaves `work` holding
   `searchInPlace (prepareInPlace dataOld target) target`, and the clause then
   demands
   `searchInPlace (prepareInPlace dataOld target) target = prepareInPlace dataOld target`,
   unprovable for an opaque `searchInPlace`. Measured, on the two shapes the
   audit produced (`scripts/lean_verify.sh` exit codes; every variant is
   `same_spec` with the shipped `Solution.lean`, differing only inside the impl
   region):

   | variant | what it models | exit |
   |---|---|---|
   | recorded attack, ported to carry `work` | second routine reworks the first routine's own buffer on the preserve leg, and the run reports that buffer | **1** — unsolved goal `searchInPlace (prepareInPlace dataOld target) target = prepareInPlace dataOld target` under `if_pos : effectiveCopy … = true` |
   | raw-gate rival | second routine reads the RAW per-call value (`requestedCopy.getD false`) on both legs | **1** — same goal, under `if_pos` plus `if_neg : ¬requestedCopy.getD false = true` |
   | drops the second routine | second routine never runs | **1** |
   | correct-but-different control | explicit `match` resolution, composite written in one assignment, carrying `work` | **0** — verifies (so the added clause is not too strong) |
   | recorded attack ported LITERALLY, i.e. keeping its DISCARDED term and still reporting `prepareInPlace dataOld target` | *not* a run in which the second routine wrote the buffer — see below | **0** |

   The rejecting branch is FEASIBLE in each rejected variant (the hypothesis is
   satisfiable, e.g. `configuredCopy = true, requestedCopy = none`), so the
   refutation is not a vacuous guard.

   The last row is reported for completeness and is not a residual hole. Both
   routines are pure opaque transforms, so forming a term and discarding it is not
   an account of the second routine having written anything; `work` denotes a VALUE
   — the contents of `fit`'s local `X` at `:1512` (mapping.md §1, §3.4). A text that
   reports `prepareInPlace dataOld target` there is asserting that the buffer handed on
   still holds the first routine's output, which in the repo happens exactly when
   the second routine took its defensive copy — the gold behaviour, whose patch
   resolves. The raw-gate Python behaviour and the discarded-term reading cannot be
   claimed of the same impl: the first row above is what that behaviour's faithful
   model looks like, and it is rejected.
2. **Both consumers are governed on the OVERWRITE leg.** The `false` leg equates
   both buffers at EXIT — after both A-referenced routines — to the composite
   `searchInPlace (prepareInPlace dataOld target) target`. An implementation that lets
   only the first routine write cannot produce that term, so it fails (measured:
   the drop-the-second-routine variant, exit 1).
3. **The per-call choice cannot be ignored.** The baseline skeleton gates the
   two routines by two different quantities (the configured choice and the raw
   per-call one, absent → truthy), which is the pre-change repo. At
   `configuredCopy = true`, `requestedCopy = some false` (the F2P scenario:
   default-constructed `LassoLarsIC`, then `fit(X, y, copy_X=False)`) the
   effective choice is `false` while the skeleton preserves, so the `false` leg
   demands `dataOld = searchInPlace (prepareInPlace dataOld target) target` —
   unprovable.
   Confirmed: `Solution_prepatch.lean` fails with unsolved goals on multiple
   clauses (exit 1), while `Solution.lean` verifies (exit 0).
4. **Both buffers' exit contents are determinate.** Each clause equates its
   buffer to a term built only from `dataOld`, `target` and the choice, so no
   verifying implementation may leave either buffer holding a value the model's
   own inputs fail to determine. This is the faithfulness obligation, and it is
   what the modeled region of mapping.md §3.3 exists to make true: every input
   either routine reads that is not a modeled input is PINNED to a constant, the
   pin table is proved COMPLETE by parsing `fit`'s own two call statements —
   `self.<attr>` reads, local aliases and **literal keyword arguments** alike
   (`axiom_check.py: check_pin_table_complete`) — and each pin's provenance is
   checked against the constructor default (`check_pin_provenance`) — every
   estimator pin IS the default except `precompute`, the one deliberate
   narrowing, which the modeled region takes falsy because that is the only
   setting under which the second routine reaches the buffer at all, and it is the
   setting both observable behaviours above are stated in. FOUR of the region's
   conjuncts are not settings at all but properties of the buffer itself, and all
   four are decided by `in_modeled_region` in both check scripts. Two of them are
   DETERMINACY pins on inputs the signature does not carry; the other two are
   DOMAIN conjuncts, excluding runs in which the clauses' terms have no referent
   because a routine never hands one back:

   * it must be a FLOAT buffer — `check_array(X, copy=False, dtype=FLOAT_DTYPES)
     is X`. Outside that, the repo converts the buffer into a private array and no
     in-place write reaches the caller at all, so the two legs stop being
     distinguishable (measured: `guard-int-outside-region`);
   * its element FORMAT must be `float64`. The first routine's reduction is
     carried out in the buffer's own precision, so two buffers holding EXACTLY
     the same entries as `float32` and as `float64` hand the second routine
     different arrays — and the difference reaches `coef_`. The float32 and
     float16 members of `FLOAT_DTYPES` are perfectly reachable; they are simply
     DIFFERENT modeled inputs, and no argument of the signature carries the
     format (measured: `guard-format-is-necessary`, mapping.md §3.3);
   * its MEMORY LAYOUT must be C-contiguous, because the same reduction runs
     along the memory stride (`np.average(X, axis=0)`, `base.py:149`) and numpy's
     pairwise summation blocks along it, so identical contents in C and in F order
     give different output in the last float bits and the difference again
     propagates to `coef_` (measured: `guard-forder-is-necessary`, and the
     off-pin `c_contiguous` twin, against a same-layout control that is
     bit-identical — a layout dependence, not nondeterminism).
   * its centering must stay inside the float64 RANGE — a DOMAIN conjunct, like
     the first bullet rather than the middle two. The first routine subtracts the
     column mean in place (`base.py:149-150`) and hands the result straight to a
     step whose own validation asserts finiteness (`base.py:152` →
     `validation.py:51`), so for a buffer sitting near the top of the range that
     step RAISES: the first routine never returns, the second never runs, and
     neither clause's right-hand side denotes anything. The witness is finite,
     `float64` and C-contiguous on entry (`X = [[1e308], [1e308]]`) and the
     caller is left holding `[-inf, -inf]`, which is neither `dataOld` nor the
     composite — so this could not be repaired by pinning anything; the run has
     to be outside the region. The conjunct is the repo's own reduction re-run on
     the caller's own entries, never a magnitude threshold: measured `1e307`
     inside and completing, `1e308` / `1.7e308` excluded and raising (GUARD 4),
     and over a band straddling the ceiling 35 accepted-and-completed, 5
     excluded-and-raised, 0 accepted-and-raising — in G-AX and, against the real
     `fit`, in G-CONF (mapping.md §3.3, the RANGE row).

   Without the two determinacy pins the first routine's output would not be a
   function of the entry contents and the clauses' terms would not be determined;
   without the two domain conjuncts they would have no referent at all. Estimator
   pins measured load-bearing on 3/3 matrices each: `normalize`, `positive`,
   `max_iter ∈ {1,2}`; `eps` and `method` reported honestly as conservative pins
   whose off-pin runs were not observed to change the composite. The two symbols'
   SECOND arguments are what make clause-level determinacy a real constraint
   rather than a vacuous one. `searchInPlace`'s is numeric: the descent's effect
   genuinely varies with the target's entries (mapping.md §3.2), and a unary
   symbol could not equal the several distinct exit buffers one entry buffer
   produces under different targets. `prepareInPlace`'s is structural: the target's
   LENGTH is the row count (`check_X_y` forces `len(y) == X.shape[0]`), so it is
   what divides the flat carrier into the rows and columns the column-wise
   reduction sums over — measured binding (`A4-shape-is-binding`), and measured
   NOT to read the target's entries, so the argument buys the shape and nothing
   else.

Conversely the spec is not too strong: an implementation that resolves the
choice by any equivalent means and applies the two routines in order, reporting
the buffer the second routine was handed, verifies — measured as the
correct-but-different control in the table above (exit 0).
