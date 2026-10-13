# mapping.md — scikit-learn__scikit-learn-12973

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a7b8b9e9e16d4e15fabda5ae615086c2e1c47d8a`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), gives the
provenance of the two deep-model references, and states the MODELED REGION —
the configuration on which the modeled quantities are functions of the modeled
inputs.

Repo file under change: `sklearn/linear_model/least_angle.py`.

## 0. The two consumers of the buffer, and the TWO buffers they leave behind

`LassoLarsIC.fit` hands its `X` to **two** numeric routines in sequence, and BOTH
can write in place the buffer they are handed. Each is gated by a copy flag:

| # | call site | routine | gate it is passed |
|---|---|---|---|
| 1 | `least_angle.py:1503-1504` | `LinearModel._preprocess_data(X, y, fit_intercept, normalize, <gate>)` (`base.py:93`) | pre-patch `self.copy_X`; post-patch the resolved `copy_X` |
| 2 | `least_angle.py:1509-1512` | `lars_path(X, y, Gram=Gram, copy_X=<gate>, ...)` (`least_angle.py:31`) | the `fit` parameter `copy_X` — **unchanged by the patch at this site**, but post-patch it is the RESOLVED value |

Routine 1 copies internally iff its gate is truthy (`check_array(X, copy=copy,
..., dtype=FLOAT_DTYPES)`, `base.py:117`) and otherwise centers `X` in place
(`X -= X_offset`, `base.py:150`).

Routine 2 takes its defensive copy iff `copy_X` is truthy (`if copy_X: X =
X.copy('F')`, `least_angle.py:176-180`), reached only on the `Gram is None or
Gram is False` branch (`:174`). With no copy taken, the descent's column swaps
`X.T[n], X.T[m] = swap(X.T[n], X.T[m])` (`:268`) land in the buffer it was
handed, and which columns get swapped depends on the target vector `y`.

**`fit` writes one name `X`, but two DISTINCT buffers are observable per run, and
the model must carry both:**

| model output | the repo object | why it is observable |
|---|---|---|
| `data` | the array **the caller still holds** after `fit` returns — the object passed in at `:1482` | the caller reads it: `assert copy_X == np.array_equal(X, X_copy)` in the F2P test |
| `work` | the value of `fit`'s local `X` **immediately after the routine-2 call returns** (`:1512`), i.e. what routine 1 returned as routine 2 left it | `fit` READS it at `:1520`, `R = y[:, np.newaxis] - np.dot(X, coef_path_)`, and those residuals drive `self.criterion_` (`:1536`), `n_best`, `self.alpha_` and `self.coef_`. So the numbers `fit` reports are a function of `work` |

The two come apart **exactly on the leg the change is about.** When routine 1's
gate is truthy it hands routine 2 a buffer of its own, so the caller's buffer is
preserved *whatever routine 2 is told to do* — routine 2's gate is INVISIBLE in
`data` there. Only `work` records it: with a truthy gate routine 2 copies and
leaves `work` holding routine 1's output; with a falsy one it swaps columns in
`work`, and `fit` then forms the residuals against a column order that no longer
matches `coef_path_`, so the reported coefficients change.

That is the mechanism behind the P2P behaviour: `test_lars_precompute` refits one
shared matrix with no per-call choice and compares `coef_` across `precompute`
values, and its falsy `precompute` iterations are the ones on which routine 2
reaches `work`. A run that resolves the choice for routine 1 but forwards the raw
per-call value (absent → falsy) to routine 2 preserves the caller's buffer and
still reports different coefficients.

The pre-change baseline gates the two routines by two DIFFERENT quantities
(`self.copy_X` and the raw per-call `copy_X`, default `True`); the change makes
ONE resolved decision govern them both, hence both buffers.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `applyWithCopyChoice (mut data) (target) (configuredCopy) (requestedCopy)` | `LassoLarsIC.fit(self, X, y, copy_X)` — `least_angle.py:1482` (class `LassoLarsIC` at `:1351`) | the modeled changed function: resolve the per-call vs configured copy choice, then run the buffer through both routines of §0 under it |
| `configuredCopy` | `self.copy_X` set in `LassoLarsIC.__init__` — `least_angle.py:1477` (param at `:1470`) | the copy choice fixed at construction |
| `requestedCopy : Option Bool` | the `copy_X` parameter of `fit` — post-patch default `None` (`least_angle.py:1482` post-patch) | the optional per-call copy choice; `None ↔ none`, `True ↔ some true`, `False ↔ some false` |
| `effectiveCopy configured requested` | the resolution `if copy_X is None: copy_X = self.copy_X` (post-patch, immediately before `least_angle.py:1503`) | the effective copy decision = `Option.getD` |
| `data : Array Int` (`mut`) | the caller's feature matrix `X` (a numpy array buffer), as it exists in the CALLER's frame | buffer #1 of §0 |
| `work : Array Int` (returned) | the value of `fit`'s local `X` at `least_angle.py:1512`, after the routine-2 call returned | buffer #2 of §0; `fit` reads it at `:1520` to build the residuals, so `self.coef_` / `self.alpha_` are functions of it |
| `target : Array Int` | the `y` argument of `fit` (`least_angle.py:1482`), forwarded to routine 2 at `:1510` | the companion target vector; routine 2 reads it, so both buffers' exit contents depend on it |
| `prepareInPlace` *(deep-model reference, A-reference)* | the transform ROUTINE 1 applies — `_preprocess_data` (`base.py:93`), centering at `base.py:150` | unchanged numeric preprocessor; only its FRAME effect and its output CONTENTS are observed. **BINARY in `(buffer, target)`**: `_preprocess_data` reduces COLUMN-WISE (`np.average(X, axis=0)`, `base.py:149`), so its output depends on how the buffer's entries divide into rows and columns. The Lean carrier is a FLAT array (§2), which does not carry that division; `target` does, because `check_X_y` (`:1504`) forces `len(y) == X.shape[0]`, so `n_samples = target.size` and `n_features = dataOld.size / target.size`. The target's own ENTRIES are measured NOT to be read by routine 1 (§3.1), so this argument is a shape witness, not a numeric dependence. Validated by G-AX §3.1 |
| `searchInPlace` *(deep-model reference, A-reference)* | the transform ROUTINE 2 applies to the buffer it was handed — `lars_path` (`least_angle.py:31`), column swaps at `:268`, copy skipped at `:176-180` | unchanged descent routine; only its FRAME effect on that buffer is observed, as a function of the buffer AND `y`; validated by G-AX §3.2 |

The pre-change repo expressions the patch replaces (refinement audit only, not
in the consumer spec view): routine 1's gate is `self.copy_X` (the configured
choice, `least_angle.py:1504` pre-patch) while routine 2's gate is the raw
per-call parameter whose pre-patch default is `True` (`:1482`, `:1510`) — two
independent gates, neither of them the effective choice.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `X` — a numpy feature matrix in the caller's frame (a mutable buffer) | `data : Array Int` | a numpy array `X` ↔ an `Array` of its entries in C order. This enumeration is FLAT, so by itself it does not carry the buffer's row/column division, its element format, or its memory order — and each of those is a real input of routine 1, which reduces column-wise along the memory stride (`base.py:149`). The model therefore carries the division through the SIGNATURE rather than assuming it away: `target.size` is `n_samples` (`check_X_y` at `:1504` forces `len(y) == X.shape[0]`), so `(dataOld, target)` jointly determine the shape, which is why `prepareInPlace` is binary (§1). Element format and memory order are pinned structurally by §3.3, since no argument of the signature carries them. Measured: at a fixed format and order, `(entries, target)` determine both routines' outputs exactly (0 violations over 40 random shapes). The observed property is the buffer's CONTENTS at exit, compared for EQUALITY: either equal to its entry contents, or equal to what the two routines of §0 produce from those contents and `y`. **The entry type is abstracted away, not claimed to be integral.** Every obligation in the spec view is an equation between whole buffers (`data = dataOld`, `work = prepareInPlace dataOld target`, `… = searchInPlace (prepareInPlace dataOld target) target`); no clause, lemma or `require` mentions an entry, an arithmetic operation on entries, or an ordering, so the only structure the carrier must supply is decidable equality on the index→entry map. `Int` is chosen for that because a witness can name a literal buffer in it. In particular the model does NOT say that a caller buffer whose dtype is integral gets written: an integral buffer is OUTSIDE the modeled region (§3.3), where the repo's own `check_array` converts it into a private array and no write reaches the caller at all. The modeled region is a `FLOAT_DTYPES` buffer. |
| the value of `fit`'s local `X` after the routine-2 call (`:1512`) | `work : Array Int` | same array↔`Array` reading, same entry-type abstraction. It is not the caller's object, so it is observed through what the run REPORTS from it (`self.coef_`; see §3.4 and `conformance_check.py`) |
| `y` — the numpy target vector passed to `fit` | `target : Array Int` | a numpy 1-D array ↔ an `Array` of its entries; same equality-only reading, same entry-type abstraction |
| `self.copy_X` (a Python `bool`) | `configuredCopy : Bool` | `True ↔ true`, `False ↔ false` |
| `fit`'s `copy_X` argument (post-patch `bool` or `None`) | `requestedCopy : Option Bool` | `None ↔ none`, `True ↔ some true`, `False ↔ some false` |
| `if copy_X is None: copy_X = self.copy_X` | `effectiveCopy configured requested = requested.getD configured` | the resolution: explicit per-call choice wins, else the configured default |
| the caller's buffer surviving BOTH routines of §0 intact | `data = dataOld` | the buffer is entry-for-entry its entry value |
| routine 2 leaving the buffer it was handed as routine 1 produced it | `work = prepareInPlace dataOld target` | routine 2 took its defensive copy, so `fit` reports numbers built from routine 1's output |
| a buffer holding what routine 1 then routine 2 wrote into it | `… = searchInPlace (prepareInPlace dataOld target) target` | the exit contents as a function of the entry contents and the target |

`mut data` is the directive-5 frame carrier: the `true` leg pins
`data = dataOld` (read-only frame stated explicitly, for the whole run); only
the `false` leg may overwrite it. `work` is a returned value, not a frame
carrier: it is a fresh buffer on the `true` leg and the caller's own buffer on
the `false` leg, and each leg pins it to a term over `(dataOld, target)`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

Both constructs are deep-model REFERENCES: neither symbol's value is ever
equated to anything in the proof, which closes purely by the impl's assignments
plus the `effectiveCopy` reduction. There is **no consumed `axiom`** and **no
`:|`-stub** in this bundle.

### 3.1 `prepareInPlace` ↔ routine 1's transform (A-reference)
**Callee:** `sklearn.linear_model.base._preprocess_data(X, y, fit_intercept,
normalize, copy)` (`base.py:93`). **Unchanged** by the patch. Its numeric return
values other than the buffer are irrelevant here; the modeled properties are:

* **frame, gate truthy** ⇒ `X` is copied internally (`check_array(X, copy=True,
  ..., dtype=FLOAT_DTYPES)`, `base.py:117`), so the caller's buffer is left
  intact and routine 2 is handed a different object;
* **frame, gate falsy** ⇒ the caller's buffer is written in place (`X -=
  X_offset`, `base.py:150`, under `fit_intercept=True`) and routine 2 is handed
  that same object;
* **determinacy** ⇒ **at the pinned configuration of §3.3**, the OUTPUT CONTENTS
  are a function of the entry contents AND the target's LENGTH. Measured:
  replay-deterministic; independent of the target's VALUES at a fixed length;
  and independent of its own gate (`axiom_check.py` law A3). Gate-independence
  is what licenses ONE symbol `prepareInPlace` denoting routine 1's output on
  BOTH legs. The symbol is BINARY because the routine reduces column-wise, so
  its output depends on the buffer's row/column division, which the flat carrier
  of §2 does not record and `target.size` does: measured, two buffers with the
  SAME flat C-order entries under targets of different lengths (shapes `(6,4)`
  vs `(4,6)`, `(12,2)`, `(24,1)`, `(8,3)`, `(3,8)`, `(2,12)`) give routine 1
  DIFFERENT output, so a unary symbol could not equal them all. Value-independence
  at a fixed length is what keeps the second argument a shape witness rather than
  a licence to vary with the target. The qualifier is load-bearing and is NOT a caveat added after the
  fact: routine 1's output genuinely varies with `self.normalize`, which is why
  `normalize` is a PINNED row of §3.3 rather than an omission. Off that pin the
  unary reading would be false, and `axiom_check.py` both asserts the pin and
  measures it load-bearing.

### 3.2 `searchInPlace` ↔ routine 2's transform (A-reference)
**Callee:** `sklearn.linear_model.least_angle.lars_path(X, y, Gram=..., copy_X=...,
copy_Gram=True, alpha_min=0.0, method='lasso', ...)` (`least_angle.py:31`).
**Unchanged** by the patch (the patch does not touch `lars_path` nor the
arguments `fit` passes it at `:1510`). Modeled properties:

* **frame, gate truthy** ⇒ the defensive copy is taken (`if copy_X: X =
  X.copy('F')`, `:176-180`), so **the buffer it was handed** is left intact —
  whether that buffer is the caller's or routine 1's private one;
* **frame, gate falsy** (and `Gram` falsy, §3.3) ⇒ the copy is skipped and the
  descent's column swaps (`:268`) land in the buffer it was handed;
* **determinacy** ⇒ **at the pinned configuration of §3.3**, the resulting
  contents are a function of the buffer it received AND the target vector `y`.
  Both arguments are genuinely read: measured deterministic on replay, and
  measured to differ across distinct `y` at fixed buffer (`axiom_check.py`),
  which is what forces `searchInPlace` to be BINARY. A unary symbol could not be
  equal to several distinct exit buffers for one entry buffer. The qualifier is
  again load-bearing: `max_iter`, `positive` and `eps` are further inputs of this
  descent, which is why each is a PINNED row of §3.3, and `axiom_check.py`
  measures `max_iter` and `positive` to change the composite.

The two references compose in the model exactly as the two calls compose in the
repo: routine 2 receives whatever routine 1 produced, hence
`searchInPlace (prepareInPlace dataOld target) target`.

### 3.3 The MODELED REGION (the guards that make both buffers determinate)

The equations of §2 are asserted of the configuration below.
`axiom_check.py` and `conformance_check.py` both HOLD the region and ASSERT it
rather than assuming it, and `axiom_check.py` additionally proves this table is
**complete**: it parses `fit`'s own two call statements and fails unless every
argument they pass is either a modeled input (`X`, `y`, the gate) or a row of
this table. Completeness covers all three ways an argument can be written —
`self.<attr>` reads, local names (each checked to be an alias of a pinned
attribute), and **literal keyword arguments**, which are compared by value
against the `PIN_*` constants this module itself uses; a positional literal or a
`**kwargs` call at either site is rejected outright, since neither could be
pinned under a name. The buffer-shape guards (dtype, element format, layout) and
the buffer's own arithmetic RANGE are not call arguments and are enforced
separately, by `in_modeled_region`.

Two KINDS of row appear below, and it is worth separating them.

* **DETERMINACY pins** hold something that IS an input of a modeled routine but
  that no argument of the modeled signature carries (the element format, the
  memory layout, and every estimator/literal setting). Off such a pin the
  modeled buffer would still exist but would not be a FUNCTION of the modeled
  inputs.
* **DOMAIN rows** exclude runs in which the modeled buffers have no referent at
  all, because a routine never returns one: the float-matrix row (`check_array`
  hands routine 1 a private array, so nothing the model names is the caller's
  buffer) and the RANGE row (routine 1 raises, so routine 2 never runs). Nothing
  is claimed of those runs, and neither leg's equation is asserted there.

| guard | Python expression that enforces/decides it | provenance | why it is needed |
|---|---|---|---|
| the buffer is a float matrix | `check_array(X, copy=False, dtype=FLOAT_DTYPES) is X` — true for `float64`/`float32`, FALSE for `int64` | structural | with an integer buffer, `check_array` allocates a converted array and NO in-place write reaches the caller's buffer at all; the falsy-gate leg would then also preserve it, so the two legs would not be distinguishable |
| the buffer is dense | not a `scipy.sparse` matrix | structural | the sparse path in `_preprocess_data` does not center in place |
| the buffer is **C-contiguous** AND its element format is `float64` | `X.flags['C_CONTIGUOUS'] and X.dtype == np.float64` — asserted by `in_modeled_region` in both `axiom_check.py` and `conformance_check.py` | structural narrowing | **memory layout is a real input of routine 1.** It reduces over the buffer (`X_offset = np.average(X, axis=0)`, `base.py:149`, then `f_normalize(..., copy=False)`, `base.py:152`) and numpy's pairwise summation blocks along the memory STRIDE, so the summation ORDER — hence the last bits of the float result — depends on the layout. Two buffers with *identical contents* and different layout therefore hand routine 2 different arrays, and the difference is not internal: it reaches `coef_`, `alpha_` and `criterion_`. So without this row `prepareInPlace` would not be a function of the entry contents and neither modeled buffer would be determined by the modeled inputs. Measured, on equal-contents C/F twins: routine 1's output differs (`check_guards` GUARD 3) and the composite differs (`check_pins_are_load_bearing`, off-pin `c_contiguous`); the same-layout control is bit-identical, so this is a layout dependence and not nondeterminism. An F-ordered caller buffer is reachable — the routines do write it — but it is OUTSIDE the modeled region, and the model claims nothing there. **The element format is pinned for exactly the same reason and is NOT a dtype-reachability claim:** the float32/float16 members of `FLOAT_DTYPES` are fully reachable (measured: `check_X_y` returns the caller's own object and the falsy leg writes it for all three), but the reduction is carried out in the buffer's own precision, so two buffers with EXACTLY equal entries in different formats hand routine 2 different arrays (measured through the real `fit`: float32 vs float64 at equal contents, `work` differs, max abs diff 7.4e-08, and `coef_` differs). Neither format nor order is carried by any argument of the modeled signature, so both must be held for the modeled buffers to be functions of the modeled inputs |
| the buffer's centering stays inside the float64 **RANGE** | `np.isfinite(np.average(X, axis=0)).all()` AND `np.isfinite(X - np.average(X, axis=0)).all()` — `reduction_stays_in_range`, called from `in_modeled_region` in both `axiom_check.py` and `conformance_check.py`; `in_modeled_region` additionally returns `False` when the repo's own `check_array` REJECTS the buffer up front (a non-finite entry, an empty buffer) | **DOMAIN row** — decided by re-running the repo's own reduction on the caller's own entries, never by a magnitude threshold this bundle invents | routine 1 centers the buffer (`X_offset = np.average(X, axis=0)`, `base.py:149`, then `X -= X_offset`, `base.py:150`) and hands the result straight to `f_normalize(..., copy=False)` (`base.py:152`), whose own `check_array` asserts that every entry is finite (`validation.py:51`). When the mean's summation or the subtraction leaves the float64 range, that assertion RAISES: routine 1 never returns, routine 2 never runs, and there is no buffer for `searchInPlace (prepareInPlace dataOld target) target` to denote. This is NOT the non-finite-input case — the witness `X = [[1e308], [1e308]]` is finite, `float64`, C-contiguous and `check_array`-clean on entry, yet the buffer the caller is left holding (`[-inf, -inf]`) is neither `dataOld` nor the composite, so no determinacy pin could repair it; only excluding the run can. Measured, and the boundary is the repo's rather than a threshold: `1e307` is INSIDE the region and completes (`guard-range-control-runs`), `1e308` and `1.7e308` are excluded and observed to raise (`check_guards` GUARD 4), and over a 40-point band of magnitudes straddling the ceiling the region predicate agrees with whether the routines can run at all — 35 buffers accepted and completed, 5 excluded and raised, **0 accepted-and-raising** (`range-boundary-accepted-and-runs` / `range-boundary-excluded-and-raises` in G-AX; `check_range_boundary` in G-CONF, which decides `raises` against the real `LassoLarsIC.fit`) |
| `precompute` is falsy at routine 2 | `self.precompute in (False, None)` → `Gram = self.precompute` (`least_angle.py:1507`) is falsy → branch `:174` taken | **deliberate narrowing** — the constructor default `'auto'` is truthy | only this branch skips the copy and swaps columns in the buffer routine 2 was handed; with `precompute` truthy or an array, routine 2 never writes that buffer and the second stage collapses. This is the setting BOTH observable behaviours of the change are stated in: the F2P test builds `LassoLarsIC(copy_X=…, precompute=False)`, and the P2P sweep `precompute in [True, False, 'auto', None]` reaches the buffer exactly on its falsy entries |
| `fit_intercept` is set | `self.fit_intercept` (`:1503`) | constructor default `True` | routine 1's in-place centering (`base.py:150`) is under this flag |
| `normalize` is set | `self.normalize` (`:1504`) | constructor default `True` | routine 1's output contents depend on it (measured: stepping off this pin changes the composite on 3/3 matrices), so it is an input of the transform and must be fixed for `prepareInPlace` to be a function of the buffer alone |
| `max_iter` is 500 | `max_iter = self.max_iter` (`:1505`), passed at `:1511` | constructor default `500` | routine 2's descent length depends on it (measured: `max_iter ∈ {1,2}` changes the composite on 3/3 matrices), so it is an input of routine 2's transform |
| `eps` is machine epsilon | `self.eps` (`:1512`) | constructor default `np.finfo(float).eps` | a tolerance of the same descent; pinned for the same reason as `max_iter`. Reported honestly: stepping off this pin was NOT observed to change the composite on the matrices tried, so the pin is conservative rather than measured-necessary |
| `positive` is unset | `self.positive` (`:1512`) | constructor default `False` | selects a different descent; measured to change the composite on 3/3 matrices |
| `verbose` is unset | `self.verbose` (`:1511`) | constructor default `False` | passed to routine 2; pinned for completeness (it only prints) |
| `method` is `'lasso'` | the LITERAL `method='lasso'` at `:1510` | fixed by the call site itself — `fit` has no setting for it | it selects the lasso descent rather than LAR, so it is an input of routine 2 and must be held. Reported honestly: the off-pin run (`method='lar'`) was NOT observed to change the composite on the 3 matrices tried, so like `eps` this pin is conservative rather than measured-necessary |
| `copy_Gram` is set | the LITERAL `copy_Gram=True` at `:1510` | fixed by the call site | a setting of routine 2; pinned for completeness (with a falsy `Gram` there is no Gram to copy) |
| `alpha_min` is `0.0` | the LITERAL `alpha_min=0.0` at `:1510` | fixed by the call site | routine 2's stopping threshold, hence how far the descent runs and how many column swaps land in the buffer |
| `return_n_iter` is set | the LITERAL `return_n_iter=True` at `:1512` | fixed by the call site | a setting of routine 2; pinned for completeness (it only widens the returned tuple) |

The last four rows are **literal** arguments of the call site rather than
estimator settings, and they are pinned for exactly the same reason: they are
inputs of the modeled routines that the modeled signature does not carry. They
are held as `PIN_METHOD`, `PIN_COPY_GRAM`, `PIN_ALPHA_MIN` and
`PIN_RETURN_N_ITER` in `axiom_check.py`, which USES those constants when it
exercises routine 2 and separately asserts that each equals the value `fit`'s own
call text passes — so this table cannot drift from the call site in either
direction.

`self.criterion` is NOT in this table because it is not an argument of either
routine and therefore not an input of any modeled quantity. It is pinned to its
default in `conformance_check.py` only because that check's proxy for `work` is
the coefficient vector the tail reports, and the tail reads `criterion`.

Degenerate float inputs (e.g. an all-zero matrix, where centering and swapping
happen to leave the contents equal to the entry contents) are INSIDE the region
and require nothing extra: the model asserts an EQUATION to an opaque function,
not that the buffer changed, so a coincidental fixpoint satisfies it. That is
why `axiom_check.py` asserts each frame law as `preserve ⇒ unchanged` plus
`determinacy`, and asserts `falsy ⇒ changed` only on the non-degenerate class
where the callee is measured to write.

### 3.4 How `work` is observed (it is not the caller's object)

`work` is a local of `fit`, so no caller can read it directly. It is observable
through what `fit` REPORTS from it: `:1520` builds the residuals from it, and
`self.coef_` / `self.alpha_` follow. `conformance_check.py` therefore compares
`model.coef_` against the coefficient vector the modeled `work` buffer implies,
computing the latter by composing the two REAL routines under ONE gate and then
transliterating `fit`'s UNCHANGED tail (`:1514-1545`, including
`base._set_intercept`'s `coef_ / X_scale`). Measured: that transliteration
reproduces the real `coef_` bit-for-bit on every input of the corpus, the two
legs give different coefficients on every input of the corpus, and a run that
gates routine 2 by the raw per-call value agrees on the caller's buffer for all
69 boundary inputs while the coefficient comparison catches 13 of them —
including `(configuredCopy = true, requestedCopy = none)`, the P2P scenario.

**What `work` denotes is a VALUE, not a call record.** The model has no notion of
"routine 2 was invoked": both routines are pure opaque transforms, so an impl that
forms `searchInPlace (prepareInPlace data) target` and then discards it, reporting
`prepareInPlace dataOld` as `work`, is not modeling a run in which routine 2 wrote
the buffer it was handed. By the binding in §1 it is modeling a run in which
`fit`'s local `X` at `:1512` still holds routine 1's output — i.e. one in which
routine 2 took its defensive copy, i.e. was handed a truthy gate. The faithful
Python refinement of such a text is therefore the gold behaviour, and it resolves.
A text whose Python counterpart lets routine 2 write that buffer must report the
written value, `searchInPlace (prepareInPlace dataOld) target`, because that is
what `:1520` reads; the discarded-term reading and the raw-gate Python patch cannot
both be claimed of one impl.

### 3.5 `bothRoutinesDeliver` ↔ the domain of the two-routine sequence (precondition)

**Neither modeled routine is total, and the modeled region admits inputs where
they signal.** The region of §3.3 pins dtype, layout and the call settings, all of
which are properties of the buffer's *representation*; none of them bounds the
buffer's *magnitudes*, and the routines both check the entries they compute:

* **routine 1.** `_preprocess_data` centers (`X -= X_offset`, `base.py:150`) and
  then normalizes (`f_normalize(..., copy=False)`, `base.py:152`), and normalize
  re-validates through `check_array` → `_assert_all_finite`
  (`validation.py:568`, `:51`). If `X_offset = np.average(X, axis=0)`
  (`base.py:149`) overflows, the centering writes `±inf` into the buffer it was
  handed and the finiteness assertion then raises `ValueError`. Observed:
  `X = [[1e308], [1e308]]`, `y = [1., 2.]`, `precompute=False`, `copy_X=False` →
  `ValueError: Input contains NaN, infinity or a value too large for
  dtype('float64')`; routine 2 never entered (spy: `entered=False`); caller's
  buffer left `[-inf, -inf]`.
* **routine 2.** With routine 1 delivering, `lars_path` can still raise from its
  own descent (`least_angle.py:259`) when the *target* overflows. Observed:
  `X` a finite 4×2 gaussian, `y = [1e308, 1e308, -1e308, 1e308]` → routine 1
  returns, routine 2 is entered and raises.

**This is NOT a per-entry condition, which is why the predicate is over the pair
rather than a finiteness conjunct in `in_modeled_region`.** The witness above has
`np.isfinite(X).all() = True`, and so does
`X = [[6e307], [6e307], [6e307]]` — every entry is a perfectly ordinary finite
`float64`, and the raise comes from the *reduction* of them overflowing. A guard
on the entries one at a time therefore cannot express this class, and the
`y`-driven arm shows the condition is not a property of the buffer alone either.
Hence one opaque `Prop` over `(buffer, target)`.

**Measured properties that license the modeling:**

| property | measurement |
|---|---|
| **gate-independent** — whether the sequence delivers does not depend on the copy choice, so ONE predicate covers every leg and may be stated ahead of the choice | 673 in-region buffers × all 6 `(configuredCopy, requestedCopy)` combinations: **0 gate-dependent** (71 pairs signal on all six, 602 deliver on all six) |
| **deterministic** — it is a function, not a coin flip | 0 replay disagreements over the same 673 |
| **the frame clause does NOT need it** — routine 1 copies *before* it reduces, so on the preserve leg a mid-reduction signal cannot reach the caller's buffer | 860 in-region buffers (99 of them signalling) × the 3 preserve-leg combinations = 297 preserve-leg observations on the signalling class: **0 violations of `data = dataOld`**. This is why the guard sits on the three output clauses and the frame clause is left unconditional |
| **the boundary is strictly inside the region, so this is a real gap and not the region's edge** | on `[[v], [v]]`: `v ≤ 1e307` delivers, `v ≥ 1e308` signals |

**The precondition does not narrow away any behavior the patch changes.** The
gold patch was applied and reverted around the same five inputs: on every
signalling input, pre-patch and post-patch `fit` raise **identically** (same
exception, same site) for all six combinations. The delta the instance is about
lives entirely on the delivering pairs, so excluding the signalling ones removes
no discriminating behavior — confirmed by the prepatch twin still failing the
repaired spec, and by G-PBT's 15 cases (11 of them rejections) still passing.

**Soundness check (G-AX):** `axiom_check.py` exercises the REAL unchanged
callees `_preprocess_data` and `lars_path` **directly** (NOT via
`LassoLarsIC.fit` — that is the function under spec, and the choice-resolution it
performs is the *changed* op; G-AX must validate only unchanged callees,
SPEC_GUIDE §0.7). Because both callees are unchanged by the patch, the laws it
validates hold identically on the in-tree (pre-patch) source G-AX runs against —
no `apply_gold` needed. Imports only `sklearn` + `numpy` + stdlib. Exit 0 iff
sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12973`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`effectiveCopy` (the R/I-tagged resolution op) to Python; the two A-referenced
routines are NOT transliterated — the shadow instead composes the real routines
under the resolved gate and predicts the observables the run must report, and the
oracle runs the real patched `LassoLarsIC.fit`. The observable per input is the
triple

    (resolved_choice, caller_buffer_matches_modeled, coefficients_match_modeled)

where the third component is the `work` buffer's observable consequence (§3.4)
and is what makes routine 2's gate visible on the preserve leg.
