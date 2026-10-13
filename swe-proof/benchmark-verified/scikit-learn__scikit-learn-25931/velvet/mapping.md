# mapping.md — scikit-learn__scikit-learn-25931

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e3d1f9ac39e4bf0f31430e779acc50fb05fe1b64`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom/reference.

Repo file under change: `sklearn/ensemble/_iforest.py` (class `IsolationForest`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fitComputeOffset (samples) (q)` | the non-default-contamination tail of `IsolationForest.fit` — `sklearn/ensemble/_iforest.py:341-350` (the `self.offset_ = np.percentile(...)` step at line 348) | the modeled changed function: derive `offset_` from the already-prepared training matrix |
| `CallerHandle : Type` | the sample matrix as an OBJECT, the way `X` arrives at `IsolationForest.score_samples` (`pd.DataFrame`, ndarray, sparse matrix): numbers PLUS the per-column labelling attached to them, or the absence of one — exactly what `sklearn/base.py::_get_feature_names` (`base.py:1873`) reads off it | an OPAQUE type: nothing in `Solution.lean` constructs one, because a handle is what a CALLER brings in. This is the wall that keeps the fitting tail out of the public scoring entry point (§6) |
| `Prepared : Type` | the matrix a screen hands back — the bare `np.float32` array `_validate_data` returns (`_iforest.py:291`, `:436`), of which `_get_feature_names` is `None`: the caller's numbers in the layout and precision the scorer reads, with the labelling consumed | an OPAQUE type, and what the fitting tail HOLDS (the `:291` validation produced it). Distinct from `CallerHandle` because the two differ on every screen decision even when they hold the same numbers (§2, `check_object_properties`) |
| `Presented : Type`, `presentCaller : CallerHandle → Presented`, `presentPrepared : Prepared → Presented` | a matrix as PRESENTED to `_validate_data` (which accepts any array-like), and the two ways one arrives there: the caller's own object at `:436`, and an already-prepared array presented again — literally what the pre-patch `fit` does at `:348` | both presentations are the identity in the repository and NEITHER is invertible: nothing recovers a caller's object from what was presented, so no `Prepared` can be read back as a `CallerHandle`. That non-invertibility is the modeling counterpart of the plain fact that the fitting tail no longer holds the caller's labelled matrix, and it is what makes the argument-type wall of §6 real rather than notational |
| `Scores : Type`, `Point : Type`, `Score : Type` | the per-sample anomaly score sequence a scorer PRODUCES (`-self._compute_chunked_score_samples(X)`, `_iforest.py:440`) and the percentile point a fitting call site REQUESTS (`100.0 * self.contamination`, `_iforest.py:348`) | OPAQUE types, and that is a measured correction rather than a preference: the order statistic they are the arguments of is PARTIAL in both, and a precondition fences only the argument a method is CALLED with while a total reference may be named at any term of its argument type anywhere inside a body. Nothing in `Solution.lean` constructs either, so the refused regions are inexpressible. The numbers are reached through `scoreValues`; the point is passed to the order statistic and to nothing else. `Score` is ONE score of such a sequence, and it is opaque for the same measured reason one step further in: READING a produced sequence is itself partial in the POSITION read (a position the sequence does not have is refused, and refused even where the value read is cancelled away), while a sequence of plain numbers admits an UNGUARDED read at any position — it needs only a default element to fall back on. With an opaque element there is no default, so a read outside the sequence is inexpressible instead of merely unreachable. See §5 (the fifth and sixth measured lessons) |
| `screenHandle (presented : Presented)` → `Bool` | the input screen the public entry point performs — `_validate_data(X, accept_sparse="csr", dtype=np.float32, reset=False)` (`sklearn/ensemble/_iforest.py:436` at base; the same call opens the post-patch `score_samples`) | THE ONE SPELLING OF A SCREEN in the file, and the FIRST declaration in it: it takes a matrix as presented and reports the screen's VERDICT on it — `false` ↔ turned away, `true` ↔ accepted. It computes NO score and hands back NO data: a screen's prepared output is reached only as the caller-side value `preparedOf` (next row), so no text holding already-prepared data can obtain a re-prepared form of it from this method. That confinement is the repair of a measured hole; see §6 |
| `preparedOf : CallerHandle → Prepared` *(A-reference, object property)* | the prepared matrix `_validate_data` returns for a CALLER'S handle it does not refuse: that handle's numbers in the scorer's layout and working precision, labelling consumed (`_iforest.py:436`) | the screen's value-neutral side, indexed by the CALLER'S handle and by nothing else, so it is nameable only where a caller's handle is in scope — the public entry point. Measured value-neutral on the NUMBERS (`axiom_check.py::check_handle_properties` leg (b), `check_value_equality`): screening converts the layout and drops the labelling and does not move the numbers, which is why the offset is numerically identical either way (§3.1). There is deliberately NO `Presented → Prepared` counterpart: an operation with an ambient effect must not be modeled as a total function over an argument the defective context can form, because naming a value discharges no obligation (§6, the measured G-EQ finding) |
| `scorePublic (handle : CallerHandle)` → `Option (List Score)` | `IsolationForest.score_samples` — `sklearn/ensemble/_iforest.py:407` (post-patch body: validate, then `return self._score_samples(X)`) | the PUBLIC scoring entry point, and the ONLY method in the file that invokes a scorer: it screens the incoming handle and then serves the numbers of the score sequence produced for `preparedOf handle`, the matrix that screen prepares from it (`scoreValues (anomalyScores (preparedOf handle))`). The `Option` carries the verdict: `none` ↔ the screen turned the handle away and the caller got no score sequence (`_validate_data` raised), `some scores` ↔ it accepted the handle and the caller got the scores of it |
| `anomalyScores : Prepared → Scores` *(A-reference)* | `-self._compute_chunked_score_samples(X)` — `sklearn/ensemble/_iforest.py:440` (the screening-independent scorer body shared by both entry points) | reference value: the per-sample anomaly score sequence the scorer PRODUCES for a prepared matrix; validated `score_samples == _score_samples == scoreValues ∘ anomalyScores` by axiom_check.py (G-AX). Its result type is an opaque CARRIER, not a sequence of numbers a text can write down, so the order statistic below cannot be named at a sequence no scorer produced — see the `percentileAt` row and §5 |
| `scoreValues : Scores → List Score` *(A-reference)* | the identity on the produced sequence: `score_samples`'s own result IS the numbers `-self._compute_chunked_score_samples(X)` holds, one per sample (`_iforest.py:440`) | reference value: the scores a produced sequence holds, in order. ONE-WAY ONLY — there is no `List Score → Scores` in the file, so a text can read the scores of a sequence a scorer produced and cannot present scores of its own as a produced sequence. Its ELEMENT type is a carrier as well (`Score`, the row above), because reading this sequence at a POSITION IT DOES NOT HAVE is refused by the repository and an unguarded read of a plain-number sequence would express exactly that. Grounded by `check_value_equality` (the public result is exactly this reading), `check_score_sequence_provenance` (one real score per sample, and reading twice reads back bit-identically, so the reading is not an action) and `check_score_index_fences` (the position partiality, with every position a sequence HAS as the control) |
| `percentileAt : Scores → Point → Offset` *(A-reference)* | `numpy.percentile` — `sklearn/ensemble/_iforest.py:348` (`np.percentile(scores, 100.0 * self.contamination)`) | reference value: the order statistic of a produced sequence at a requested point; validated == real `np.percentile` by axiom_check.py (G-AX). PARTIAL IN BOTH ARGUMENTS, and both partialities are fenced by the ARGUMENT TYPES rather than by a precondition (the fifth measured lesson, §5; the sixth carries the same correction into the ELEMENT type of the reading): no term of `Scores` or of `Point` can be written down, so the refused regions are inexpressible instead of merely un-called-with. Grounded by `check_empty_handle_fences` and `check_percentile_point_fences` (the partiality), and by `check_point_provenance` (where the reachable points come from, and that none of them is refused); see §3.2 and §5. ITS RESULT TYPE IS A CARRIER TOO (`Offset`, the row below), because ARITHMETIC on a recorded offset is total in the reference language and partial in the repository — the seventh measured lesson, §5 |
| `Offset : Type` | `self.offset_`, the threshold offset a fit RECORDS (`sklearn/ensemble/_iforest.py:348` on the requested-contamination path, `:344` on the requestless one) | an OPAQUE type, and the seventh measured correction of this bundle (§5): rational division is TOTAL in the reference language (`x / 0` is the rational 0) while the repository derives NO number there — as a plain real it raises `ZeroDivisionError` and in the working precision its scorer produces it reports a non-finite value with a `RuntimeWarning`, and cancelling the quotient away does not avoid it because the divergence happens AT THE ARITHMETIC. A rational offset therefore let a text derive a value the repository has none for, in a DISCARDED position no postcondition can see. With the offset opaque the only offsets a text can write down are `percentileAt (anomalyScores samples) q` and `defaultOffset`, both values the repository really records. Grounded by `check_offset_arithmetic_fences` |
| `defaultOffset : Offset` | `self.offset_ = -0.5` — `sklearn/ensemble/_iforest.py:344` (the branch a fit takes when no contamination level is requested) | reference value: the threshold offset the OTHER fitting path records. It is the one offset term in the file that is an order statistic of nothing, and it is measurably never the order statistic a requested contamination level determines (`check_offset_arithmetic_fences` leg (a): -0.5 on every model, and always different from the recorded offset of the requested-contamination fit on the same data). That is what makes it the value the modeled tail must NOT report, and the battery's one remaining rival on that clause (`fit-forge-offset-value`) |
| `screenRefuses : Presented → Bool` *(A-reference, object property)* | whether a screen of this handle turns it away instead of handing back scores: `_validate_data(X, accept_sparse="csr", dtype=np.float32, reset=False)` (`_iforest.py:436` at base, the screen the public entry point performs) raises rather than returning a prepared matrix. Measured true of a handle whose width disagrees with `n_features_in_` (`ValueError: X has N features, but IsolationForest is expecting M features as input.`), of one holding no samples (`Found array with 0 sample(s) ... a minimum of 1 is required`), of one holding a magnitude the recorded working precision cannot represent (`Input X contains infinity or a value too large for dtype('float32')` — note this is REPRESENTABILITY in `float32`, not finiteness: `1e300` is a finite double and is still turned away), of a non-number, and of a frame whose column labelling DISAGREES with the recorded one (renamed → `... unseen at fit time`; reordered → `... must be in the same order as they were in fit`) | the screen's VERDICT, and what makes it an obligation rather than prose: the modeled entry point's result is `none` exactly on the handles the real one refuses, so an impl can neither serve a value the verdict does not sanction nor reach the served value before the verdict is settled. No exception TYPE is modeled — only that no score sequence comes back. Grounded by `axiom_check.py::check_screen_refusals`, WITH a negative control (the ordinary handle is not turned away), so the reference cannot collapse into refusing everything |
| `screenAdvises : Presented → Bool` *(A-reference, object property)* | whether a screen of this handle draws the labelling ADVISORY: `_check_feature_names(X, reset=False)` (`base.py:566` → `base.py:406`) emits `UserWarning: X does not have valid feature names, but IsolationForest was fitted with feature names` exactly when the handle presents no labelling while `feature_names_in_` was recorded (and the mirror-image warning when it presents one while none was recorded). True of the bare `np.float32` array `_validate_data` returns at `_iforest.py:291` when `fit` was given a `pd.DataFrame`; false of the caller's own agreeing `pd.DataFrame`, and false of a bare ndarray handled by a model fitted on a bare ndarray | THE discriminating observable of this cell. The advisory is an AMBIENT effect with no returned value a caller could drop, so it is carried as a RESTRICTION on the argument (`require screenAdvises presented = false` on the screen, `require screenAdvises (presentCaller handle) = false` on the public entry point) rather than as a clause about the result: a call-site restriction is not a value an impl may discard, cancel, or restore. It is NOT a refusal — measured (`axiom_check.py::check_label_agreement` leg (iv)): the advised handle is still scored, to bit-identical values. Hence no clause anywhere lets a labelling condition a score VALUE; `scorePublic`'s value clause is unconditional in the labelling, which is what keeps it non-vacuous on the ordinary ndarray carriers of `sklearn/ensemble/tests/test_iforest.py` |
| `scorableAsGiven : Prepared → Bool` *(A-reference, object property)* | whether the screen-free scoring path can CONSUME the prepared matrix with `check_input=False` exactly as it stands — false of the CSC matrix `fit` produces at `_iforest.py:291` for sparse input (`_tree.pyx:_apply_sparse_csr`), false of a dense matrix NARROWER than the width the model was fitted on (`Tree.apply` indexes a feature it does not hold), false of a matrix in the newer sparse CONTAINER even where that one holds its numbers compressed by row (`ValueError: X should be in csr_matrix format, got <class 'scipy.sparse._csr.csr_array'>`), true of the dense/CSR-matrix of the recorded width. The first two legs measured in `check_handle_properties` leg (c), the third in `check_sparse_container_fence` | conditions the DOMAIN of BOTH methods that reach the scorer. The screen-free path inserts no conversion, so the offset tail claims a normal result only where the scorer can read the matrix as it stands (`require scorableAsGiven samples = true`); and a screen's ACCEPTANCE does not imply consumability either, so the public entry point carries the same fence at the prepared form of its own handle (`require scorableAsGiven (preparedOf handle) = true`); see §5 |
| `hasSamples : Prepared → Bool` *(A-reference, object property)* | whether the prepared matrix holds at least one sample (`X.shape[0] > 0`) | the other fence on the offset tail's domain: with no samples the screen-free chunked scorer raises out of `gen_batches` and the order statistic of an empty score sequence raises as well, so a promise there would be a promise the repository never keeps. Grounded by `check_empty_handle_fences`, with the one-sample control; see §5 |

The patch's private `_score_samples` (`sklearn/ensemble/_iforest.py:442`
post-patch; body = `check_is_fitted; return
-self._compute_chunked_score_samples(X)`) gets NO method of its own. It performs
no screen and reports nothing, so everything it contributes is its VALUE, and
that value is the A-reference `anomalyScores` in the row above — which is exactly
how the fitting tail reaches the scores (§2.1). Giving it a second method would
add a second scorer-invoking declaration to the file, and the file having exactly
one is what closes invocation multiplicity (§6).

**Declaration order in `Solution.lean` is `screenHandle`, `scorePublic`,
`fitComputeOffset`, and it is load-bearing** (see §6): the screen is declared
first, so it is in scope everywhere, and `scorePublic` — the one scorer-invoking
method — is declared before the offset tail, so scope alone does NOT keep the
tail out of it. What keeps it out is `scorePublic`'s argument TYPE: the tail
holds a `Prepared` and can form no `CallerHandle` at all, presentation to a screen
being non-invertible. Both the order and the argument types live inside the frozen
spec region, so no same-spec variant can change them.

The pre-patch repo symbol the change reroutes (refinement audit only, not in the
consumer spec view): `fit` at line 348 calls `self.score_samples(X)` — the
PUBLIC entry point — which re-runs `_validate_data` on the already-prepared `X`.
That second validation is what drops the input's feature names and so raises
`UserWarning: X does not have valid feature names, but IsolationForest was
fitted with feature names`. The patch reroutes that call to `self._score_samples(X)`,
which skips `_validate_data`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| prepared sample matrix `X` (n_samples × n_features of `np.float32`) | `samples : Prepared` | identity on OBJECTS, not on contents. The VALUE leg (`anomalyScores`) is delegated to the real scorer by G-AX, so the carrier needs to be a faithful identity for the matrix, not a numeric model of it — and it must NOT be its contents: see the row below |
| **why a matrix is an object and not its contents** | `CallerHandle` / `Prepared` / `Presented`, all opaque | a contents carrier is UNSOUND here, and this is measured rather than argued (`axiom_check.py::check_object_properties`): two matrices holding bit-identical numbers disagree about the labelling advisory (recorded labelling presented vs presented bare), about the refusal (the same numbers arranged as another width are turned away) and about readability (the same numbers compressed cannot be read as they stand). A property of the contents would have to answer twice for one argument, so an earlier `List Rat`-carrier revision of this spec was describing something that cannot exist. The two NUMERICAL arguments of the order statistic became carriers as well, for the related reason recorded in §5: their callee is partial in both, and only an argument type fences every site a total reference can be named at — and the same correction then applied one step further in, to the ELEMENT type of the reading, because READING a produced sequence is partial in the position read |
| the per-sample anomaly score sequence the scorer PRODUCES | `Scores`, opaque | identity on the produced sequence. Opaque so that the order statistic cannot be named at a sequence no scorer produced (§5); the numbers are reached through `scoreValues` |
| the scores that sequence holds, in order | `scoreValues scores : List Score` | element-wise; `len(scores) == n_samples ↔ .length`, measured in `check_score_sequence_provenance`. The map runs one way only: no `List Score → Scores` exists in the file, and the ELEMENTS are carriers too, so the sequence's LENGTH and the guarded read that reports a position's ABSENCE are expressible while an unguarded read at a position the repository refuses is not (`check_score_index_fences`) |
| `100.0 * self.contamination` (the percentile point) | `q : Point`, opaque | identity on the requested point. Opaque for the same reason as `Scores`: the callee refuses a point outside the range a percentage occupies, and a fence on the METHOD'S PARAMETER does not reach the other places a total reference can be named at (§5). No numeric carrier is needed, because nothing in the file computes with the point — it is passed to the order statistic and to nothing else. That the reachable points ARE percentages is measured, not assumed (`check_point_provenance`) |
| `self.offset_` (a scalar) | `offset : Offset`, opaque | identity on the recorded value. The carrier is not a numeric encoding choice but a TOTALITY FENCE on arithmetic (§5, the seventh lesson): the repository derives no number for a quotient by zero and the reference language does, so no arithmetic on the recorded offset is expressible here at all. What the file can name is the order statistic itself and `defaultOffset`; §2.2 (R-ARITH) records how a bare rational a text writes is read back |
| the caller's matrix object `X` as it arrives at `score_samples` | `handle : CallerHandle` | identity on objects; the handle is not inspected by the logic, only presented. Its labelling is not a Lean value at all: what the labelling does is read off it by the two screen references (`screenAdvises`, `screenRefuses`) applied to `presentCaller handle` |
| the matrix as `_validate_data` receives it | `presentCaller handle` / `presentPrepared samples` | identity (the callee accepts either); NOT invertible in either direction, which is the wall of §6. `presentPrepared` is precisely the pre-patch's second presentation of the already-prepared array at `:348` |
| `_validate_data(X, ...)`'s returned bare `float32` array, for the caller's handle `X` | `preparedOf handle` | numbers preserved, layout converted, labelling dropped (measured, `check_handle_properties` leg (b)). Only the CALLER'S handle indexes it, because the caller's screen is the only place in the modeled surface where a matrix is prepared |
| what the screen reports | `Bool` | `true` ↔ `_validate_data` returned, i.e. the matrix was accepted and the caller may go on; `false` ↔ it raised, so there is nothing to go on with. The prepared array itself is NOT this method's result — see the row above and §6 |
| what the public entry point hands a caller | `Option (List Score)` | `some scores` ↔ the call returned that score sequence; `none` ↔ the call produced no score sequence for the caller at all, because the screen turned the handle away (`_validate_data` raised). The abstraction is one-directional in the same sense the screen is: nothing in the repository turns a refusal back into scores, so an impl that serves scores where the verdict refuses has no faithful image (§6) |
| `np.percentile(scores, q)` | `percentileAt scores q` | identity (A-reference); see §3.2 |

There is no screening COUNTER anywhere in the logic, deliberately: a counter is a
freely-written value, so a clause pinning its final value pins bookkeeping rather
than conduct (measured — §6). What the public entry point's screen contributes is
carried instead by its VERDICT (the `Bool` of §1) and by its argument
restriction, and the fact that the fitting tail performs no screen is carried
STRUCTURALLY, by an argument restriction its context cannot supply (for the
screen) plus an argument TYPE it cannot inhabit (for the scorer): see §6.

### 2.1 The R-VALUE rule — what an OCCURRENCE of a value reference maps to

Stated normatively, because it settles how a Lean impl is read back into
repository text and therefore what a same-spec rival is permitted to differ by.
This rule is also written into the frozen axiom comment of `Solution.lean`, so it
is part of what the spec says and not merely auditor commentary.

`anomalyScores samples`, `scoreValues scores`, `percentileAt scores q` and
`preparedOf handle` are
**A-reference VALUES**: each denotes the result the unchanged callee produces for
those arguments (§3).
They are not actions, and they carry no ordering or repetition content. An impl
that names such a value at several textual positions therefore reads back as the
SAME repository text as one that names it once — the callee produces the value,
a name is bound to it, and each occurrence is a use of that binding:

```
let a := anomalyScores samples        s = -self._compute_chunked_score_samples(X)
let b := anomalyScores samples   ↦    # one invocation; `a`, `b` are uses of `s`
```

Screening, by contrast, is an ACTION in this model: it has exactly one spelling
(invoking `screenHandle`), its VERDICT is what that call reports, and it
restricts the argument it accepts. Note which side of that line `preparedOf` falls
on and why it can: it is a value, so naming it is not a screen — but it is indexed
by the CALLER'S handle, so the only text that can name it is the one whose screen
produced it, and naming it there is that screen's own preparation step rather than
a further one. A `Presented → Prepared` reference would fall on the value side
while being nameable by a context holding already-prepared data, which is exactly
the unsoundness §6 records. So whether a screen happens IS modeled, while
the number of textual occurrences of a value reference is not an observable at
all. Consequence for the audit lane: an invocation-multiplicity rival is either a
duplicated value reference (same image under this rule — nothing to reject) or an
attempted second screen (inadmissible at the call site, §6). That the spec cannot
express invocation counts of a *method* is why the offset path is given no scoring
method it can hand an argument to: see §6, "Multiplicity".

The rule is not merely asserted: `conformance_check.py` (G-CONF) carries the
count as a third component of its R/I shadow — `(warns, extra_screens,
scorer_calls)` = `(False, 0, 1)` on the non-default-contamination path and
`(False, 0, 0)` on `contamination="auto"` — differential-tested against the real
patched `fit`. Measured non-vacuous: with the offset step altered to score twice,
that gate reports `shadow=(False, 0, 1) oracle=(False, 0, 2)` and exits 1.

### 2.2 The R-ARITH rule — what an occurrence of ARITHMETIC maps to

Stated normatively for the same reason §2.1 is, and written into the frozen axiom
comment of `Solution.lean` as well, so it is part of what the spec says.

Since the seventh lesson (§5) **no numeric type in this file models a repository
quantity**: `Rat`, `Int` and `Nat` appear in no declaration and in no method's type —
the produced score sequence, one score of it, the requested point and the recorded
offset are all carriers. An arithmetic term a text writes down is therefore a
**CONSTANT of the reference language**: it denotes the number it evaluates to, it
invokes no repository callee, and it reads back into repository text as that number.
A number a text computes and then DISCARDS is dead text.

The rule is grounded, not asserted, and in BOTH directions. Toward the repository:
the reference language's rational arithmetic is EXACT and the repository's on these
numbers is not — three tenths added together is exactly `3/10` as a rational and is
not `0.3` as the repository computes it, and the mean the repository reports for a
real score sequence is not the exact rational mean of those same numbers
(`check_offset_arithmetic_fences` leg (e)). Toward the reference language: its
arithmetic is TOTAL, and truncating where the repository's is neither — `(1 : Rat) / 0`
is `0`, `(0 : Rat)⁻¹` is `0`, `(1 : Int) / 0` is `0`, `(5 : Nat) / 0` is `0` and
`(3 : Nat) - 5` is `0`, measured as six `example`s in one scratch file that verifies
(exit 0), while the repository raises `ZeroDivisionError` for the first of them and
reports `-2` for the last. An operator-by-operator reading of arithmetic is therefore
measurably unfaithful in both directions and cannot be the intended one: a term is
read as its VALUE, which is what this rule says.

Consequence for the audit lane, recorded rather than left implicit: a rival that
derives a number whose arithmetic the repository leaves undefined, and DISCARDS it,
still elaborates, and it is NOT a refutation — under this rule its image is a dead
constant and its behaviour is gold's. Four routes to that shape were measured against
the shipped file, each exit 0, and the residual is exactly as wide as they are:

* WRITTEN CONSTANTS alone — `let junk := (1 : Rat) / 0` (also measured exit 0 before
  the offset carrier was introduced, so the carrier neither opened nor closed it);
* a SCREEN VERDICT the file does expose, through the Boolean's branch —
  `let b := (if screenAdvises (presentPrepared samples) then (1 : Rat) else 0)` then
  `let junk := b / (b - b)`;
* the produced sequence's LENGTH — `let n := ((scoreValues (anomalyScores samples)).length : Rat)`
  then `let junk := n / (n - n)`;
* the same length in `Nat`, where the division is the reference language's truncating
  one — `let junk := (scoreValues (anomalyScores samples)).length / 0`.
* the same numbers in a live-looking BRANCH CONDITION rather than in a discarded
  binding — `let n := (scoreValues (anomalyScores samples)).length` and then `if n -
  (n + 1) = 0 then <the ordinary route> else <screen the prepared matrix again>`,
  together with the spellings `n + 1 - n - 2 = 0` and `n / 0 = 0` of the same
  condition. Each condition is constant-TRUE in the reference language, so the branch
  a repository reading would take is UNREACHABLE here and the program's value is the
  ordinary route's; measured exit 0 for all three. The grounding is a control on the
  dead branch itself: put in it a body that violates this method's own postcondition
  (`return defaultOffset`), and a body that violates that AND the screen's call-site
  precondition (`let _confirmed ← screenHandle (presentPrepared samples)` then `return
  defaultOffset`), and the files still verify — exit 0 for the second body under all
  three conditions and for the first body as well — so that branch carries no
  obligation whatever, which is what its unreachability amounts to. The
  live-position counter-measurements are on record: the same screen call in a
  REACHABLE position IS the prepatch, exit 1 at `Solution_prepatch.lean:476:31` on `⊢
  screenAdvises (presentPrepared samples) = false`, and the same `defaultOffset` in a
  REACHABLE position is the battery's `fit-forge-offset-value` reject case. A
  term-position absurdity is not available to a control here — `let _absurd : False :=
  by omega` in the dead branch is exit 1, `omega could not prove the goal: No usable
  constraints found` — because a branch condition, like a `require`, is not in scope as
  a hypothesis inside an implementation; the semantic control above is the idiomatic
  one for this file.

The shape is not fenceable by any spec text: the numbers are the reference language's
own, and every Boolean and every length the file exposes is a route to one, so no
clause and no carrier reaches it — which is why it is published as a reading rule and
never claimed as fenced. What the carrier DOES fence is arithmetic on a value the
model carries — the recorded offset, one score, the requested point — which is where a
divergence the repository can observe would come from. Recorded as a demonstrated
limit of the reference language's arithmetic, with the reading rule that settles it.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `anomalyScores` ↔ the screening-independent scorer (A-reference)
**Callee:** `-self._compute_chunked_score_samples(X)`
(`sklearn/ensemble/_iforest.py:440`), the body shared by `score_samples` (after
its `_validate_data`) and `_score_samples` (with no `_validate_data`). The
load-bearing fact the refactor relies on, modeled by `anomalyScores`, is
**screening-independence of the score value**: for an already-prepared matrix,
`score_samples(X)` and `_score_samples(X)` return the SAME scores — the only
difference between the two entry points is the (value-irrelevant) input
screening. Hence `offset_` is numerically identical before and after the patch;
what the patch changes is solely whether the screen is performed a second time.

Denotation: `anomalyScores samples` is the score sequence of the prepared matrix
`samples`. Screening only converts a presented matrix into that prepared form (and
consumes its labelling); it does not move the numbers, which is precisely the
equality G-AX checks bit-exactly (`score_samples(X_raw) ==
-_compute_chunked_score_samples(X_prepared)`).

**Screen-before-score is OBSERVABLE, not licensed away.** An earlier spelling of
this section stated that the order of the screen and the score-binding inside
`scorePublic` was not an observable of the model, on the ground that both readings
screen once and score the screened matrix. That was a hole: it licensed exactly the
shape the cell has to reject, an entry point that produces the numbers of a handle
the screen has not yet passed judgement on. The current spelling makes the order
carry an obligation instead of a comment, in both methods. `screenHandle`'s result
is `if screenRefuses presented then false else true`, and
`scorePublic`'s is `if screenRefuses (presentCaller handle) then none else some
(scoreValues (anomalyScores (preparedOf handle)))`, so what is served DEPENDS
on the verdict: no impl can
bind what it hands back before the verdict is settled, and none can serve numbers
the verdict refuses. The value leg is also UNCONDITIONAL in the labelling — the
advisory reference appears nowhere in either `ensures` — so an accepted handle is
promised the scores of its own numbers whatever labelling it presents (§5).
Measured, real
builds against the spec as it stands, each exiting 1: an impl that scores every
handle without consulting the verdict, one that refuses every handle, and one that
keys its answer on the ADVISORY instead of the refusal. The reject lane of
`properties.py` carries the same three as witnesses (`public-ignores-refusal`,
`public-refuses-everything`, `public-keys-on-advisory`), and the first of those is
the inversion of a positive case an earlier revision of that battery wrongly
blessed.

**Soundness check (G-AX):** G-AX runs `axiom_check.py` against the **unpatched
base commit** (it does NOT apply the gold patch), so the check may touch only
callees that exist at `base_commit`. The patch's private `_score_samples` does
NOT yet exist there; the genuinely UNCHANGED callee both scoring paths sit on is
`-self._compute_chunked_score_samples(X)` (`_iforest.py:442`, base commit), the
screening-independent scorer modeled by `anomalyScores`. The patched
`_score_samples` is by definition exactly `check_is_fitted(self); return
-self._compute_chunked_score_samples(X)` (no `_validate_data`), so the check
EMULATES the screen-free path with that unchanged callee. `axiom_check.py` fits
a real `IsolationForest` and asserts, over boundary + fuzzed inputs (both
`np.ndarray` and `pd.DataFrame`), that `score_samples(X)` equals the screen-free
scoring of the prepared matrix element-wise (the A-reference, i.e. screening is
value-neutral), and that `score_samples` performs **exactly one** `_validate_data`
call while `_compute_chunked_score_samples` performs **zero** (the screening
discipline the two entry points differ by). Exit 0 iff sound.

### 3.2 `percentileAt` ↔ `numpy.percentile` (A-reference)
**Callee:** `numpy.percentile`. `percentileAt scores q` is the value
`np.percentile(scores, q)` returns. No contract (monotonicity, bounds) is
consumed; only the identity to the real callee. G-AX confirms
`percentileAt == np.percentile` on the scored sequences.

The Lean reference is TOTAL and the callee is not, in EITHER argument, so both
partialities are fenced — by the ARGUMENT TYPES, which is the fifth measured
lesson of this bundle (§5): an empty score sequence raises `IndexError`, and a
point outside the range a percentage occupies raises `ValueError: Percentiles must
be in the range [0, 100]` — measured on the real score sequence at the fit point,
on both sides of the range and just past each endpoint, with the endpoints and the
interior as the control (`check_percentile_point_fences`). Neither argument is a
type whose terms a text can write down, so neither refused region is expressible
at all; a precondition would have fenced only the argument the method is CALLED
with, while the reference may be named at any term of its argument type anywhere
inside a body (§5, and the measured G-EQ finding recorded there).

The repository only ever asks for `100.0 * self.contamination`, and that is a
measured fact rather than an assumption about what callers do: the offset a real
fit records is bit-identical to the order statistic of that model's own
screen-free scores at that point, and the estimator refuses a contamination level
whose point would fall outside the range (`check_point_provenance`, with the
admissible interval as the control). So the carrier promises a value exactly where
the repository derives one.

No CONSUMED axioms: neither `anomalyScores` nor `percentileAt` has an `ensures`
the proofs rely on; the proofs use only the function-symbol identities in the
`ensures` clauses (the values flow through unchanged). Both are therefore tagged
**A-reference** in refinement.md, not A-consumed. There is no axiom about the
function under change (the `fit` offset tail is modeled directly, not
axiomatized).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` / `numpy.random.RandomState`
with **`25931`** so the consumer-side verdict (§11.3) is reproducible. The R/I
shadow it builds transliterates the screening discipline of
`fitComputeOffset` (it reuses the prepared path ⇒ the offset computation performs
no screen of its own, so no feature-name re-screen occurs) and differential-tests
it against `patch.diff` behaviour: the real patched `fit` run on a DataFrame
with `contamination != "auto"` performs zero extra `_validate_data` calls past
the initial one and emits no feature-name `UserWarning`. The A-tagged value
legs (`anomalyScores`, `percentileAt`) are left to the real callees (G-AX).

## 5. `scorableAsGiven` and the offset tail's DOMAIN (faithfulness, not a fix leg)

The gold patch removes the only CSR conversion on the offset path. `fit` validates
with `accept_sparse=["csc"]` (`_iforest.py:291`), so for sparse input the handle at
the offset step is a `csc_matrix`; the deleted screen was
`_validate_data(X, accept_sparse="csr", ...)` (`:436` at base). Post-patch the chain
`_score_samples → -_compute_chunked_score_samples → _compute_score_samples(X[sl], ..)`
(a CSC row-slice stays CSC) `→ tree.apply(X_subset, check_input=False) → Tree.apply
→ _apply_sparse_csr` (`_tree.pyx`) raises `ValueError: X should be in csr_matrix
format, got csc_matrix`. Upstream classified this as a bug and fixed it in
`9371cec9366dbbd4f3ab0290e6efec948a0a5295` by adding `if issparse(X): X = X.tocsr()`
at exactly the line `patch.diff` introduces.

Consequence for the spec: the patched tail is PARTIAL. The layout is a property of
the matrix OBJECT — a `csc_matrix` and its dense equivalent hold the same numbers
and are still different objects, and the screen-free scorer reads only the second
(measured, `check_object_properties` leg (c)) — so `Prepared` distinguishes them
and `scorableAsGiven` is a property of it. The reference is read as
CONSUMABILITY-AS-IT-STANDS rather than as the arrangement alone, because the
arrangement is not the only thing the scorer can be turned away by: a dense
matrix NARROWER than the width the model was fitted on is held in exactly the
arrangement the scorer reads and it still raises (`Tree.apply` indexes a feature
the matrix does not hold). Both legs are measured in `check_handle_properties`
leg (c), with the recorded-width dense matrix as the control, so the reference
excludes every prepared matrix the scorer refuses and no more.
`require scorableAsGiven samples = true`
conditions the modeled domain
to the handles on which the real patched callee returns normally, which is the
faithful reading and covers the F2P case (dense/DataFrame). It is deliberately NOT
modeled as a mandated `ValueError` outcome: mandating the raise would be faithful to
`patch.diff` alone and would REJECT the strictly-better upstream `tocsr`
implementation, i.e. it would over-constrain. `scorePublic` carries the SAME
fence at the prepared form of its own handle (`require scorableAsGiven (preparedOf
handle) = true`), and an earlier revision did not — on the reading that the real
`score_samples` still converts (`accept_sparse="csr"`, `:434` post-patch), so
anything that screen accepted was readable. That reading is measured FALSE for one
family of matrices, and the family is not exotic: `check_array(accept_sparse="csr")`
preserves the CONTAINER, so a handle built with the newer sparse containers
(`csr_array`, and `csc_array`/`coo_array`, which it compresses by row into a
`csr_array`) is ACCEPTED by that screen — it hands back a prepared matrix of the
same numbers, in the working precision — and `_apply_sparse_csr` then raises
`ValueError: X should be in csr_matrix format, got <class
'scipy.sparse._csr.csr_array'>`, so the real `score_samples` raises as well. An
unconditional served-value clause therefore promised scores over a region where the
entry point serves none. Measured with its controls in
`check_sparse_container_fence`: the dense matrix and the older sparse containers
(`csr_matrix`, `csc_matrix`, `coo_matrix`) of those same numbers are all accepted
AND consumed, one score per sample, and the public path serves exactly the numbers
the scorer produces for them; `fit` refuses a training matrix in the newer container
outright (`ValueError: X should be in csc format`), so no offset tail holds one
either. Every arrangement the graded scoring surface uses lies inside the fence.

The sparse legs of both references are mechanically covered by that check and by
`check_handle_properties` leg (c); the value fixtures of G-AX/G-CONF sample dense
and frame carriers. The grounding for the two SCREEN references IS
mechanically covered, and it separates the advisory from the refusal:
`axiom_check.py::check_label_agreement` measures, on 5 real labelled models, that
the real public entry point scores an agreeing labelling without drawing the
feature-name advisory, and turns away both a permutation of the recorded labelling
(`ValueError: ... must be in the same order as they were in fit`) and a disjoint
one (`... unseen at fit time`) — the two legs that make `screenRefuses` true for a
DISAGREEING labelling. `check_screen_refusals` measures the rest of the verdict
(disagreeing width, no samples, a magnitude the working precision cannot
represent, a non-number) WITH a negative control that the ordinary handle is not
turned away, over 61 observations on 8 models. `check_handle_properties` supplies
the handle side of the advisory (a screened handle presents no labelling at all,
so `screenAdvises = true` at `:291` for a model fitted on a frame), and
`check_bug_is_real` supplies non-vacuity.

**WHY THE LABELLING MAY NOT CONDITION A VALUE (measured, and the standing control
on this cell).** Leg (iv) of the same grounding measures the converse of the
advisory: an UNLABELLED handle — a bare ndarray of the same numbers, which a
labelled model DOES draw the advisory about — is nevertheless scored by the real
public entry point, and to bit-identical values. So the labelling governs the
advisory and (when it disagrees) the refusal, never the score value. An earlier
revision of this spec conditioned `scorePublic`'s value clause on a
labelling-presence reference (`require carriesLabels samples = true` with
`ensures scores = anomalyScores samples`), which made that promise VACUOUS on the
ordinary ndarray carriers — 7 of the 21 P2P tests in
`sklearn/ensemble/tests/test_iforest.py` score a bare ndarray. The current value
clause is unconditional in the labelling: every handle the method accepts is
promised the scores of its own numbers, whatever labelling it presents or does not.
What the labelling still restricts is the ARGUMENT (`require screenAdvises
(presentCaller handle) = false`), which excludes the handle whose labelling an
earlier screen already
consumed — the defect under repair — and what it still governs is the refusal of a
disagreeing labelling, via `screenRefuses`.

**TOTALITY FENCES (the spec must not promise what the repository refuses).** Eight
regions where the modeled methods are total but the repository is not, each now
excluded rather than promised:

* a frame holding NO SAMPLES whose labelling AGREES with the recorded one. The
  agreeing labelling gets it past `_check_feature_names`, and `check_array` then
  turns it away (`Found array with 0 sample(s) ... a minimum of 1 is required`).
  Excluded by `screenRefuses presented = true ⇒ none`; grounded as its own leg of
  `check_screen_refusals` on labelled models, because an agreeing labelling must
  not be read as rescuing an empty handle;
* a handle holding a magnitude the recorded working precision cannot represent.
  The boundary here is FLOAT32 REPRESENTABILITY, not finiteness: `1e300` is a
  perfectly finite double and `check_array` still turns it away (`Input X contains
  infinity or a value too large for dtype('float32')`). A model that read this
  reference as "finite" would promise scores exactly where the repository refuses;
  grounded on both bare and agreeing-labelled carriers;
* a PREPARED matrix holding no samples, on the fitting tail — which performs no
  screen and so has no verdict to report. Excluded by `require hasSamples samples =
  true`.
  Grounded by `check_empty_handle_fences`: the screen-free
  chunked scorer does not return an empty score sequence there but raises
  (`InvalidParameterError` out of `gen_batches`), and the order statistic of an
  empty score sequence raises as well (`IndexError`) — so `fitComputeOffset` would
  otherwise promise an offset the repository never computes. The control on the
  fence is the one-sample handle: the smallest handle the fence admits still
  yields both a score and an order statistic, so the fence is no wider than the
  divergence it excludes;
* a PERCENTILE POINT outside the range a percentage occupies, on the same fitting
  tail. The order statistic is TOTAL in the Lean reference and PARTIAL in the
  callee in this argument too (`ValueError: Percentiles must be in the range
  [0, 100]`), so this is the same defect as the empty-sequence one on the other
  argument of the same callee — but it is NOT fenceable the same way, and that is
  the FIFTH MEASURED LESSON of this bundle. It carried `require 0 ≤ q ∧ q ≤ 100`
  and a judge's audit refuted that arrangement four ways with one move: a
  precondition fences the argument the method is CALLED WITH, while a total
  reference may be NAMED at any term of its argument type anywhere inside a body,
  including value-neutral positions the postcondition cannot see (`let probe :=
  percentileAt scores 1000; if probe == probe then … else …`, and the same probe
  inside `scorePublic`). Those rivals VERIFIED while their faithful counterparts
  raise out of `np.percentile` — measured in the official image on the sharpest of
  them: F2P 0/1, and 4 of 21 P2P failing. The fence is therefore the ARGUMENT TYPE
  now: `Point` is opaque, so no text in the file can write a point down at all,
  and `Scores` likewise for the other argument (`percentileAt ([] : List Rat) q`
  no longer elaborates). The three grounding legs are
  `check_percentile_point_fences` (the partiality, refused on both sides of the
  range and just past each endpoint, with the two endpoints and the interior as
  the control), and `check_point_provenance`, which measures where the reachable
  points come from — the offset a real fit records is bit-identical to the order
  statistic of that model's own screen-free scores at `100.0 *
  self.contamination`, and a contamination level whose point would leave the range
  is refused outright, with the admissible interval accepted as the control. It is
  the same structural correction as the one §6 records for the screen's prepared
  output, with PARTIALITY in place of an ambient effect;
* a PREPARED matrix narrower than the width the model was fitted on, again on the
  fitting tail. Its arrangement is the ordinary dense one, so an arrangement-only
  reading of `scorableAsGiven` would call it scorable while the scorer raises on
  it. Excluded by reading that reference as consumability as it stands and
  grounding both of its legs (arrangement and width) in `check_handle_properties`
  leg (c), with the recorded-width matrix as the control;
* a handle in the NEWER SPARSE CONTAINER, on the PUBLIC entry point — the one
  region on that method rather than on the fitting tail, and the one where the two
  observables this spec keeps apart come apart in the repository as well: the screen
  ACCEPTS the handle (`screenRefuses` is false, and modeling it as a refusal would
  be unfaithful to the screen, which does hand data back) and the SCORER then
  refuses the prepared matrix it handed back, so the entry point serves nothing.
  Excluded by `require scorableAsGiven (preparedOf handle) = true`, the same fence
  the fitting tail carries, imposed at the only prepared matrix that method can
  name. Grounded by `check_sparse_container_fence` with the dense and
  older-container controls, and with `fit`'s own refusal of the newer container as
  the reason the fitting tail never meets this region;
* a POSITION a produced score sequence does not have, on either method — the SIXTH
  measured lesson, and the fifth one applied one step further in. Reading a produced
  sequence is partial in the POSITION read: `IndexError` far past the end, at the
  length itself, and at the mirror position before the start, over four sequence
  lengths, on the screen-free sequence and on the public entry point's own served
  one, and refused just the same where the value read is then cancelled away,
  because the refusal happens at the READ. A reading into a sequence of PLAIN
  numbers admits an UNGUARDED read at any position — such a read needs only a
  default element to fall back on — so `scoreValues : Scores → List Rat` let a text
  name a score in a region where the repository derives none, and name it in a
  value-neutral position no postcondition can see. A judge's audit refuted that
  arrangement four ways with one move (`let probe := nums[1000]!` in the offset tail,
  cancelled and as a two-way branch; the same read at `nums[nums.length]!`; the same
  probe inside `scorePublic`): all four VERIFIED, while their faithful counterparts
  fail the graded test and 4 of 21 P2P tests (the three offset-tail shapes) or 13 of
  21 (the public one). The fence is the ELEMENT TYPE, exactly as §5 fences the two
  arguments: `scoreValues : Scores → List Score` over an opaque `Score`, so an
  unguarded read has no default to fall back on and no score can be written down at
  all. Measured, every rival of that family now fails to elaborate (`failed to
  synthesize Inhabited Score`), while what the repository DOES serve stays
  expressible and still verifies — the sequence's LENGTH and the guarded read that
  reports a position's ABSENCE (`nums[0]?`), both exit 0 — so the fence is no wider
  than the divergence it excludes. Grounded by `check_score_index_fences`, whose
  controls are every position a sequence HAS (all readable and finite), the order
  statistic of the whole sequence (defined), and the served sequence being
  bit-identical to the screen-free reading;
* ARITHMETIC ON THE RECORDED OFFSET — the SEVENTH measured lesson, and the fifth one
  applied to a RESULT type. Rational division is TOTAL in the reference language
  (`x / 0` is the rational 0, `(x - x)⁻¹` is 0) and the repository derives NO number
  for either: as a plain real it raises (`ZeroDivisionError: float division by
  zero`), in the working precision its scorer produces it reports a non-finite value
  together with a `RuntimeWarning`, and cancelling the quotient away recovers no
  number either, because the divergence happens AT THE ARITHMETIC. An independent
  audit of the previous arrangement (`percentileAt : … → Rat`, `fitComputeOffset : …
  → Rat`) refuted it with exactly that: rivals returning the right order statistic
  while ALSO forming `off / 0` in a DISCARDED position VERIFIED, and no postcondition
  can see a discarded quotient. The counterpart patch of the sharpest of them was run
  in the official image: the graded test passes and four P2P scoring/prediction tests
  fail (`test_iforest_works`, `test_score_samples`, `test_iforest_chunks_works1`,
  `test_iforest_chunks_works2`) consistently over three attempts, so it resolves
  nothing. The fence is the RESULT TYPE: `Offset` is opaque, so no arithmetic on a
  recorded offset elaborates at all (measured: `failed to synthesize HDiv Offset ℕ`,
  `failed to synthesize HSub Offset Offset`, `failed to synthesize Neg Offset`, and
  `Application type mismatch: The argument off has type Rat but is expected to have
  type Offset` for an aggregate or a written rational). What the repository DOES
  derive stays expressible and still verifies — the order statistic itself, the
  guarded read, the sequence's length (exit 0) — so the fence is no wider than the
  divergence it excludes. Grounded by `check_offset_arithmetic_fences`, whose
  controls are the arithmetic the repository does perform on these numbers (negation,
  division by one and by two, the order statistic taken again, the count of the
  scores: all finite, warning-free). The residual shape a spec cannot reach — a number
  the text derives with arithmetic the repository leaves undefined and then DISCARDS,
  reachable from written constants, from a screening verdict's Boolean and from the
  produced sequence's length, in `Rat` and in `Nat` alike — is recorded with its
  reading rule in §2.2 (R-ARITH), together with the four measurements that bound it.

## 6. How "the offset path screens nothing further" is carried

Recorded because the earlier spelling of this claim was measured to be defeatable
and was replaced.

**Not by a tally, and the logic carries none.** An earlier spelling gave the
prepared-data method a screening counter and pinned `ensures checks = checksOld`.
That pins the counter's FINAL VALUE, which an impl may advance and then write
straight back down (`let saved := checks; checks := checks + 1; …; checks :=
saved`), or reach by discarding the copy a callee returns, or cancel
arithmetically — all three satisfy such a clause while their faithful Python images
do call the re-screening `score_samples(X)`. Measured: with such a pin the whole
advance-then-restore family verified. `_validate_data` is an AMBIENT effect with no
discardable return — it consumes the frame's labelling and emits the spurious
advisory — so the Lean cancellation has no Python counterpart and the pin was
unsound in the weak direction. There is therefore no counter anywhere in the
current logic; what the public screen contributes is its VERDICT (the `Bool` of
§1) and its argument restriction.

**A precondition alone is not a wall (measured, and it is why the shape of this
file changed).** It is tempting to read `require p` as unreachable from a context
that cannot prove `p`. It is not: an impl may BRANCH on the reference and satisfy
the obligation inside the branch, `if p then <ordinary path> else <the call>`,
and for a `Prop`-valued requirement the same works via
`if @decide P (Classical.propDecidable _) then … else …`. Both were measured
verifying. So the only load-bearing walls in this backend are DECLARATION SCOPE,
ARGUMENT TYPES, and the total-correctness TERMINATION obligation, and each of the
two things the offset tail must not do is now carried by one of them (plus, for
the honest-re-screen residue, by the fact that it is harmless — last paragraph).

**A value reference the defective context can name is not a wall either (the
third measured lesson, and it is why a screen's OUTPUT sits on the caller's
side).** An earlier revision let the screening method hand the prepared matrix
back and pinned it with `screenYields : Presented → Prepared`. A judge's audit
refuted that spec seven different ways with one move. `presentPrepared samples`
is a `Presented`, so the offset tail could NAME `screenYields (presentPrepared
samples)` — the screen's own output for the data it already holds — and a value
reference has no call site, hence no call-site obligation and nothing for the
`screenAdvises` requirement to stop. Such a rival verifies, and its faithful image
re-runs `_validate_data` on the training matrix, advisory included; measured in
the official instance image, the materialized rival fails the graded test
(`FAIL_TO_PASS` 0/1 on `test_iforest_preserve_feature_names`, `PASS_TO_PASS`
21/21). The current spec has no `Presented → Prepared` at all: the screening
method reports a `Bool` verdict, and the prepared matrix is `preparedOf :
CallerHandle → Prepared`, nameable only where a caller's handle is in scope.
Measured on the bytes as they stand, every route the audit used now fails to
elaborate rather than verifying: `preparedOf (presentPrepared samples)` →
`Application type mismatch: The argument presentPrepared samples has type
Presented but is expected to have type CallerHandle`; and the three fabricated
handles fail exactly as in the multiplicity legs below (`Application type
mismatch` for `Classical.arbitrary`, `failed to synthesize Inhabited CallerHandle`
for `default`, an unprovable `⊢ Nonempty CallerHandle` for `Classical.choice`).
The generalization, which is the reusable part: an operation whose repository image
carries an AMBIENT EFFECT must not be modeled as a total function over an argument
type the defective context can form.

**Structurally instead.** In the frozen spec there is exactly ONE spelling of a
screen — invoking `screenHandle`, whose argument requirement is `screenAdvises
samples = false`, i.e. the screen has nothing to advise about this matrix — and
exactly ONE method that invokes a scorer, `scorePublic`, whose argument is a
`CallerHandle`.

* THE SPURIOUS REPORT. `fitComputeOffset`'s context says nothing about
  `screenAdvises`, and the reference is opaque, so no argument it can form — its
  own matrix presented again, or anything derived from it — discharges the
  requirement outright. A call-site obligation cannot be discarded, cancelled, or
  restored, which is exactly the asymmetry with a counter. Measured, real builds
  against the spec as it stands, all exit 1 on the same unsolved goal
  `⊢ screenAdvises (presentPrepared samples) = false`: the plain re-screen (the
  prepatch, which is `Solution_prepatch.lean` itself, failing at
  `Solution_prepatch.lean:476:31` under `case «require_1: hasSamples samples = true»`), the double screen, and the gratuitous-screen-plus-discarded-echo. There
  is no other matrix to present instead, and presenting the re-screened result
  leaves the same goal one level down. That obligation is also the SCREENING DELTA
  of this cell in the most direct sense: the spurious advisory the F2P test
  `test_iforest_preserve_feature_names` asserts the absence of is precisely what
  `screenAdvises (presentPrepared samples) = true` names. What an impl CAN do is branch on the
  reference and screen only where it has PROVED the screen silent — see the last
  paragraph, where that residue is shown harmless and is carried as a positive
  control rather than hidden.
* THE RE-PREPARED MATRIX. There is no term of type `Prepared` the offset tail can
  form besides the `samples` it was given: `preparedOf` takes a `CallerHandle`
  (uninhabitable here, next bullet), no reference maps a `Presented` to a
  `Prepared`, and the screening method's result is a `Bool`. So the tail's own
  prepared matrix is the only data it can score, and the previous paragraph is why
  that matters.
* THE SECOND SCORING. `scorePublic` is in scope in the offset tail (it must be
  declared before it — see the multiplicity paragraph), so scope is not the wall
  here; the ARGUMENT TYPE is. The tail holds a `Prepared`, `CallerHandle` is an
  axiomatized type with no constructor and no `Inhabited`/`Nonempty` instance, and
  presentation to a screen runs the other way and is not invertible, so there is no
  argument with which the tail could invoke it — for its own data or for any
  other. Measured, every route to fabricating one, each a real build, and note
  that the goal the branch leaves behind is `⊢ screenAdvises (presentCaller …) =
  false`, which is underivable too, so both walls have to be breached at once:
  `Classical.arbitrary` → `Application type mismatch … has type (α : Sort ?u) →
  [h : Nonempty α] → α but is expected to have type CallerHandle` (exit 1);
  `default` → `failed to synthesize Inhabited CallerHandle` (exit 1); `⟨⟩` →
  `Invalid ⟨...⟩ notation: The expected type CallerHandle is not an inductive
  type` (exit 1); `Classical.choice` and a `sorry` term → `declaration uses
  'sorry'` plus the unsolved advisory goal (exit 1); and binding the handle by
  `sorry` so the advisory goal itself is closed → the file elaborates but
  `scripts/lean_verify.sh` reports `file elaborates but uses sorry/admit` and
  exits 3, i.e. it is not a verifying rival under the protocol (G-HYGIENE is the
  authoritative scan for the same thing). The offset tail therefore reaches the
  screen-free scores only as the value reference `anomalyScores samples` (§2.1).

**Multiplicity: how often a scorer runs.** A second measured lesson, recorded
because a rival exploited exactly this gap. Routing the offset derivation through
a scoring METHOD twice is a distinct repository behaviour — the real chunked
scorer runs twice, which two `PASS_TO_PASS` tests detect by asserting the exact
`get_chunk_n_rows` call count — and NO clause of this logic can reject it: an
invocation count is not a value a postcondition can observe, a tally that would
count it is advance-then-restore forgeable (above), a callee requirement over a
by-value argument is re-discharged verbatim by the second call (and is guardable
anyway, above), and Velvet has no cost, fuel, or ghost-history facility. The
frozen spec closes the family structurally instead. An earlier revision tried to
close it by declaration ORDER, which cannot work — the public entry point has to
be declared before the offset tail for the tail to be the LAST thing in the file,
and a rival that reaches a scorer-invoking method declared earlier is then only a
precondition away, i.e. one guard away (above). So the count is closed by there
being exactly ONE scorer-invoking declaration in the file and its argument being
uninhabitable from the offset tail. Three legs, all measured:

* **argument type** — the fabrication routes above, all rejected;
* **termination** — a rival that self-calls `fitComputeOffset` is rejected by the
  total-correctness obligation (`fail to show termination for fitComputeOffset` /
  `no parameters suitable for structural recursion`; adding `termination_by` would
  have to go outside the impl markers and so is not same-spec);
* **R-VALUE (§2.1)** — what remains reachable on that path is the value reference
  `anomalyScores samples`, and duplicating a value reference maps to the same
  repository text, so there is no second invocation to reject.

**The one admissible re-screen is PROVABLY SILENT, and that is correct, not a
hole.** An impl may write `if screenAdvises (presentPrepared samples) then
<ordinary path> else <a re-screen>`; it verifies — measured, exit 0, for both the `Bool` guard and the
`Classical.propDecidable` spelling — because the else-branch's guard supplies
exactly the requirement that branch needs. What it CANNOT do is screen where the
advisory is possible: the guard forces the re-screen into the branch where the
screen is proved to report nothing. Its faithful image is `if
_get_feature_names(X) is None and self.feature_names_in_ is not None:
<screen-free> else: <re-screen>`, and at the modeled call site — line 348, after
the `:291` validation — a model fitted on a frame has a prepared matrix with no
labelling to read, so the image takes the screen-free branch and the F2P test
passes. For a model fitted on a bare ndarray the image re-screens, which emits no
advisory (there is no recorded labelling to disagree with the prepared matrix's
absent one), returns the same numbers, and computes no score, so the chunked-scorer
invocation count is unchanged. Measured end to end rather than argued: in the
official instance image, the gold patch plus a redundant guarded `_validate_data`
at the offset step runs the F2P test and all 21 `PASS_TO_PASS` tests to `22
passed` — the chunk-count assertions included. The spec admits a superset of gold
here, every member of that superset resolves, and `properties.py` carries the
shape as the positive control `pos-fit-provably-silent-rescreen` so a future
revision that quietly closed it would be noticed.
