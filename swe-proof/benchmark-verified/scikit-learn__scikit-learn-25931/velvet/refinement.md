# refinement.md — scikit-learn__scikit-learn-25931

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `screenHandle` / `scorePublic` / `fitComputeOffset` `do` blocks, in that
declaration order — the file has exactly one screening and one scorer-invoking
declaration, and both facts are load-bearing, see A2′/A2″) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/abstracted callee — **A-consumed** where the proof uses the
axiom's `ensures`, **A-reference** where a value is validated == the real callee
by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The bug and the fix (one-paragraph orientation)

`IsolationForest.fit`, on the `contamination != "auto"` path, computed
`self.offset_ = np.percentile(self.score_samples(X), ...)`. `score_samples` is
the PUBLIC entry point and re-runs `self._validate_data(X)` on the
already-prepared training matrix; that second validation strips the input's
feature names and raises the spurious `UserWarning: X does not have valid
feature names`. The patch introduces a private `_score_samples` that scores
without re-validating, splits `score_samples` into `_validate_data` +
`_score_samples`, and reroutes `fit` to call `self._score_samples(X)`. The
`offset_` VALUE is unchanged; the only observable difference is that `fit` no
longer re-screens the prepared data (no warning). The F2P test
`test_iforest_preserve_feature_names` asserts exactly: fitting a DataFrame with
`contamination=0.05` raises NO `UserWarning`.

## A. The fit offset tail — `IsolationForest.fit` (`_iforest.py:348`)

Gold hunk:
```
- self.offset_ = np.percentile(self.score_samples(X), 100.0 * self.contamination)
+ self.offset_ = np.percentile(self._score_samples(X), 100.0 * self.contamination)
```

| # | Solution.lean impl op (`fitComputeOffset`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `samples : Prepared` | `X` (already-prepared training matrix at line 348) | R | matrix ↔ an OPAQUE object type, identity on objects (mapping.md §2); value leg delegated to G-AX. The carrier is deliberately not the matrix CONTENTS: measured (`axiom_check.py::check_object_properties`), matrices holding bit-identical numbers disagree about the advisory, about the refusal and about readability, so a contents carrier cannot host the screen properties at all — an earlier `List Rat` revision of this spec was unsound for exactly that reason. The two NUMERICAL arguments of A5 are opaque carriers as well, for the related measured reason recorded there, and so is ONE SCORE of a produced sequence (B3), for that reason one step further in, and so is the OFFSET this method REPORTS (A6), for the same kind of reason one step further out — arithmetic on it is total in the reference language and partial in the repository. |
| A2 | **no screening counter anywhere in the logic** — not on this method, not on the screen, not on the public entry point either | the offset step adds nothing to the count of `_validate_data` calls | R | the absence is deliberate and load-bearing. A counter is a freely-written value, so `ensures checks = checksOld` pins bookkeeping, not conduct: advance-then-restore, discard-the-returned-copy and arithmetic-cancel all satisfy it while their Python images DO re-screen (mapping.md §6). Measured on an earlier spelling of this row: an impl that saved the counter, screened, and restored it verified. The discriminating content is A2′. |
| A2′ | this method's context says nothing about `screenAdvises`, against `require screenAdvises presented = false` on `screenHandle` — the only spelling of a screen in the frozen spec | the handle at the offset step is the label-free `np.float32` array returned by `_validate_data` at `_iforest.py:291`, never the caller's own object; and `_check_feature_names(..., reset=False)` emits the advisory precisely when a label-free handle is screened against a recorded `feature_names_in_` | R | **THE discriminating leg, and it is the SCREENING DELTA itself.** A CALL-SITE precondition cannot be discarded, cancelled, or restored — that is exactly the asymmetry with a counter. Since `screenAdvises` is opaque and nothing in this context bounds it, the screen is uncallable here OUTRIGHT, for this method's own matrix and for any argument it can form. Measured, all exit 1 on `⊢ screenAdvises (presentPrepared samples) = false`: the plain re-screen (the prepatch, at `Solution_prepatch.lean:476:31`, under `case «require_1: hasSamples samples = true»`), the double screen, the gratuitous screen with the reported verdict discarded; there is no other matrix to present instead, and the screen reports a verdict rather than data, so there is nothing coming back to present again either. What a precondition does NOT close is a GUARDED screen (`if screenAdvises (presentPrepared samples) then … else <screen>`), which verifies — measured, exit 0 — and is meant to: that branch has PROVED the screen silent, so its image re-runs the input preparation and reports nothing. It is carried as the positive control `pos-fit-provably-silent-rescreen` and measured harmless end to end (mapping.md §6: gold plus a guarded redundant screen runs `22 passed` in the official image). |
| A2″ | **the argument TYPE of the one scorer-invoking method**: `scorePublic` takes a `CallerHandle`, an axiomatized type with no constructor and no `Inhabited`/`Nonempty` instance; this method holds a `Prepared`, and presentation to a screen (`presentCaller`, `presentPrepared`) runs the other way and is not invertible, so it can form no argument for it | the offset step is a single `self._score_samples(X)` invocation; two would run the real chunked scorer twice, which `test_iforest_chunks_works1/2` detect by asserting the exact `get_chunk_n_rows` call count | R | closes INVOCATION MULTIPLICITY, which no clause of this logic can express (mapping.md §2.1, §6): a count is not a postcondition-visible value, a tally is advance-then-restore forgeable, and a by-value requirement is re-discharged by the second call — and, being a precondition, is guardable anyway, which is why an earlier revision's declaration-ORDER argument was measured insufficient (`scorePublic` must precede this method for this method to be the last in the file, and a rival then needs only a guard). Measured, every fabrication route, each a real build: `Classical.arbitrary` → `Application type mismatch … is expected to have type CallerHandle`; `default` → `failed to synthesize Inhabited CallerHandle`; `⟨⟩` → `The expected type CallerHandle is not an inductive type`; `Classical.choice` / a `sorry` term → `declaration uses 'sorry'` and the residual `⊢ screenAdvises (presentCaller …) = false`; binding the handle by `sorry` elaborates but `lean_verify.sh` reports `file elaborates but uses sorry/admit` (exit 3), so it is no verifying rival. Self-calling `fitComputeOffset` is `fail to show termination`. The argument types live inside the frozen spec region, so no same-spec rival can widen them. |
| A3 | `let scores := anomalyScores samples` (a VALUE reference, R-VALUE — mapping.md §2.1) | `self._score_samples(X)`, i.e. `-self._compute_chunked_score_samples(X)` with no `_validate_data` | A-reference (+ R) | this IS the gold edit, read on the value side: the offset is derived from the screen-free scores of the prepared matrix. A2′/A2″ are what make it the ONLY admissible way to reach them here — no reportable screen, and no scoring method this context can hand an argument to. Naming this value once or several times reads back as one invocation bound to one name (R-VALUE). |
| A4 | *(no counter write-back step)* | — | — | **Retired.** An earlier table had `checks := checks'` here and called it "implicit: no `_validate_data` ran", which was the false step: an impl may omit that write and still satisfy A2 (measured — it verified against that spec). With no counter on this path there is nothing to write back and nothing to omit. |
| A5 | `let off := percentileAt scores q`, at `scores : Scores` and `q : Point` | `np.percentile(..., 100.0 * self.contamination)` | A-reference | `percentileAt == np.percentile` (mapping.md §3.2); G-AX validated. The Lean reference is total and the callee is partial in BOTH arguments, so both partialities are fenced — by the ARGUMENT TYPES, which is the fifth measured lesson (mapping.md §5). An earlier revision fenced the point with `require 0 ≤ q ∧ q ≤ 100` and was refuted four ways by one move: a precondition fences the argument the method is CALLED with, while a total reference may be NAMED at any term of its argument type anywhere inside a body, so rivals naming the order statistic at a refused point in a value-neutral position verified while their faithful counterparts raise out of `np.percentile` (measured in the official image on the sharpest: F2P 0/1, 4 of 21 P2P failing). Both arguments are opaque carriers now, so a refused sequence or point cannot be written down at all, and the same correction was then measured to be needed one step further in, on the ELEMENT type of the reading in B3 (reading a produced sequence is partial in the POSITION read); `require hasSamples samples = true` remains for the score sequence, because it is what keeps the PRODUCED sequence non-empty (one score per sample — `check_score_sequence_provenance`). Grounded by `check_empty_handle_fences`, `check_percentile_point_fences` (the partiality, each with the control that no more than the divergence is excluded) and `check_point_provenance` (the reachable points are `100.0 * self.contamination` and none of them is refused). Its RESULT type is a carrier too, for the seventh measured lesson recorded at A6. |
| A6 | `return off` (assigned to `offset`) | `self.offset_ = ...` | R | the recorded scalar ↔ `offset : Offset`, an OPAQUE carrier (mapping.md §2, §5) — the SEVENTH measured lesson of this bundle, and the fifth one applied to a RESULT type. An earlier revision typed it `Rat`, and rational division is TOTAL there (`x / 0` is the rational 0, `(x - x)⁻¹` is 0) while the repository derives NO number for either: as a plain real it raises `ZeroDivisionError`, in the working precision the scorer produces it reports a non-finite value with a `RuntimeWarning`, and cancelling the quotient away recovers no number either, because the divergence happens AT THE ARITHMETIC (`check_offset_arithmetic_fences` legs (b), (c)). An independent audit refuted that revision with exactly that shape: a rival returning the required order statistic while ALSO forming `off / 0` in a DISCARDED position verified — no postcondition can see a discarded quotient — and the counterpart patch of the sharpest of them was measured in the official image to resolve nothing (the graded test passes; `test_iforest_works`, `test_score_samples`, `test_iforest_chunks_works1`, `test_iforest_chunks_works2` fail, consistently over three attempts). With the offset opaque no arithmetic on it elaborates (`failed to synthesize HDiv Offset ℕ`, `HSub Offset Offset`, `Neg Offset`; `Application type mismatch: The argument off has type Rat but is expected to have type Offset` for an aggregate or a written rational), and the only offsets a text can name are the required order statistic and `defaultOffset` — `self.offset_ = -0.5`, what the requestless fitting path records (`_iforest.py:344`), measured never to be the order statistic a requested level determines (leg (a)). That constant is the battery's one remaining rival on this clause (`fit-forge-offset-value`); the residual shape no spec text reaches — a number the text derives with arithmetic the repository leaves undefined and then DISCARDS, reachable from written constants, from a screening verdict's Boolean and from the produced sequence's length, in `Rat` and in `Nat` alike (four routes, each measured exit 0) — is recorded with its reading rule in mapping.md §2.2 (R-ARITH), never claimed as fenced. |

The discriminating content — fit derives the offset WITHOUT re-screening — lives
ENTIRELY in the ADMISSIBILITY of the call (A2′). `Solution_prepatch.lean`
reproduces the bug by presenting the already-prepared matrix back to the SCREEN
— the step the public entry point performs before it scores anything — and fails
on that call's obligation, `⊢ screenAdvises (presentPrepared samples) = false`,
which is underivable in its context (G-DIFF; the failing goal is quoted in
verdict.md). Note WHICH obligation that is: not a shape or labelling fact about the
data, and not the domain fence either, but the screening delta itself. That goal is
the cell's observable stated directly: `screenAdvises (presentPrepared samples) =
true` IS the spurious advisory `test_iforest_preserve_feature_names` asserts the
absence of.

Why a counter cannot carry it, recorded because a prior audit measured exactly
this: the counter is a value, threaded in and out by the caller, so an impl may
screen and then put it back — `let saved := checks; …; checks := saved` — or simply
DISCARD the counter the callee returns and never assign `checks` at all. `ensures
checks = checksOld` holds in both cases, and the whole family (discard,
arithmetic-cancel, save-and-restore, double-screen, gratuitous-screen-plus-echo)
verified against that spec. Their faithful Python images all still call the
re-screening `score_samples(X)`, because `_validate_data` is an AMBIENT effect with
no discardable return: it consumes the DataFrame's column labels and, with
`feature_names_in_` recorded at `:291`, emits the spurious `UserWarning`. There is
no Python operation that un-screens, so the Lean cancellation was a modeling
artefact and the pin was unsound in the weak direction. Carrying no counter at all
removes the artefact: screening has exactly one spelling (invoking `screenHandle`),
and A2′ closes the whole family at the call site, independent of what an impl does
with any value it gets back.

## B. The scoring split — `score_samples` / `_score_samples` (`_iforest.py:407,442`)

Gold hunk (abridged):
```
  def score_samples(self, X):
-     check_is_fitted(self)
      X = self._validate_data(X, ..., reset=False)        # the one screen
-     return -self._compute_chunked_score_samples(X)
+     return self._score_samples(X)
+
+ def _score_samples(self, X):
+     check_is_fitted(self)
+     return -self._compute_chunked_score_samples(X)
```

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `screenHandle`: consult the verdict — `return false` on refusal, `return true` otherwise | the screen post-patch `score_samples` opens with: `X = self._validate_data(X, accept_sparse="csr", dtype=np.float32, reset=False)`, which either raises or hands back the prepared matrix | I | the ONE spelling of a screen in the file, and it computes no score: its result is the screen's VERDICT. `false` ↔ `_validate_data` raised, so nobody gets anything to go on with; `true` ↔ it returned, so the caller may proceed. The prepared matrix itself is deliberately NOT this method's result — it is the caller-side value `preparedOf` (B3′), because a screen's output modeled as a reference over a matrix AS PRESENTED is nameable by a context holding already-prepared data and so bypasses every call-site obligation (measured; mapping.md §6, third lesson). Its `require screenAdvises presented = false` is what makes the spurious report inadmissible where it matters (A2′): the advisory is an ambient effect with no returned value a caller could drop, so it is carried where an impl cannot discard, cancel, or restore it. |
| B2 | `scorePublic`: screen the handle first (`screenHandle (presentCaller handle)`), then, only where that screen accepted it, serve `some (scoreValues (anomalyScores (preparedOf handle)))`, else `none` | post-patch `score_samples` as a whole: `X = self._validate_data(...)` then `return self._score_samples(X)` | I (+ A-reference) | the ONLY method in the file that invokes a scorer, and it does so only on the matrix its own screen prepared. The screening call and the value `preparedOf handle` are ONE repository operation — the `_validate_data` at `_iforest.py:436` — read on its two sides: the ACTION (which is what carries the argument restriction) and the A-reference VALUE it produces, exactly the convention A3 already uses for `anomalyScores`. Its `ensures` makes the served value depend on the verdict — `if screenRefuses (presentCaller handle) then none else some (scoreValues (anomalyScores (preparedOf handle)))` — so screen-before-score is an obligation of this row rather than a comment on it: measured, exit 1 for an impl that scores every handle, one that refuses every handle, and one keyed on the advisory instead of the refusal. The value leg is UNCONDITIONAL in the labelling (the advisory appears in no `ensures`), which is what keeps it non-vacuous on the bare-ndarray carriers of 7 of the 21 P2P tests and is measured correct by G-AX leg (iv): the advised handle is scored, to bit-identical values. Its DOMAIN carries one fence besides the advisory restriction — `require scorableAsGiven (preparedOf handle) = true` — because a screen's ACCEPTANCE does not settle what the scorer can consume, and an earlier revision read it as if it did. Measured at the base commit (`check_sparse_container_fence`): `check_array(accept_sparse="csr")` preserves the container, so a handle in the newer sparse containers is accepted by that screen and the prepared matrix it hands back is then refused by `_apply_sparse_csr`, i.e. the real `score_samples` raises `ValueError: X should be in csr_matrix format, got <class 'scipy.sparse._csr.csr_array'>` and there is no served value for a clause to promise. The controls bound the fence: the dense matrix and the older sparse containers (`csr_matrix`, `csc_matrix`, `coo_matrix`) of the same numbers are accepted, consumed and served, and `fit` refuses the newer container outright, so no offset tail meets that region — every arrangement the graded scoring surface uses lies inside the fence (mapping.md §5). |
| B3 | the patch's private `_score_samples` has NO method of its own; it appears as the A-reference VALUE `anomalyScores` — read with `scoreValues` inside `scorePublic` (`scoreValues (anomalyScores (preparedOf handle))`), and as `anomalyScores samples` in the offset tail (A3) | post-patch `_score_samples`: NO `_validate_data`, `return -_compute_chunked_score_samples(X)` | A-reference (+ R) | it screens nothing and reports nothing, so everything it contributes is its value, and a value is what an A-reference is (mapping.md §2.1). Modeling it as a second method would put a second scorer-invoking declaration in the file, and the file having exactly ONE is what closes invocation multiplicity (A2″). The domain fence that method used to carry lives on the offset tail instead: `require hasSamples samples = true`, because the chunked scorer raises on a prepared matrix with no samples rather than returning an empty score sequence (G-AX, `check_empty_handle_fences`). The reading itself is `scoreValues : Scores → List Score` over an OPAQUE element type, which is the sixth measured lesson and the fifth one applied one step further in: READING a produced sequence is partial in the POSITION read (`IndexError` far past the end, at the length, and at the mirror position before the start, and refused just the same where the value read is cancelled away — `check_score_index_fences`), while a reading into plain numbers admits an UNGUARDED read at any position, because such a read needs only a default element to fall back on. A judge's audit refuted the plain-number reading four ways with that one move (`nums[1000]!` in the offset tail, cancelled and as a two-way branch; `nums[nums.length]!`; the same probe inside `scorePublic`) — all four VERIFIED while their faithful counterparts fail the graded test and 4 of 21 P2P tests, or 13 of 21 for the public one. With an opaque element there is no default to fall back on, so those rivals no longer elaborate (`failed to synthesize Inhabited Score`, measured), while what the repository DOES serve stays expressible and still verifies: the sequence's LENGTH and the guarded read that reports a position's ABSENCE, both exit 0. Nothing in the spec computes with a single score — the order statistic takes the SEQUENCE and the served clause is an equality of sequences — so the fence excludes only the divergence. |
| B3′ | `preparedOf : CallerHandle → Prepared` — the prepared matrix the caller's screen produces, and the ONLY producer of a `Prepared` in the file | the `X` that `self._validate_data(X, accept_sparse="csr", dtype=np.float32, reset=False)` returns inside `score_samples` (`_iforest.py:436`) | A-reference (+ R) | indexed by the CALLER'S handle and by nothing else, so it is nameable only where a caller's handle is in scope — inside `scorePublic`, whose screen produced it. Measured value-neutral on the numbers (`check_handle_properties` leg (b), `check_value_equality`): the screen converts the layout and consumes the labelling, it does not move the numbers. There is deliberately no `Presented → Prepared` counterpart, and that asymmetry is the repair of a measured hole rather than a modeling taste: with one, the offset tail could name the screen's own output for the data it already holds, with no call site and hence no obligation, and the faithful image of such a rival re-runs the input preparation (measured in the official image: `FAIL_TO_PASS` 0/1, `PASS_TO_PASS` 21/21). See mapping.md §6. |
| B4 | `anomalyScores` is the same reference in both places it occurs | the shared scorer body `-_compute_chunked_score_samples(X)` | A-reference | screening-independence of the value: `score_samples(X)` equals the screen-free scoring of the prepared matrix (`-_compute_chunked_score_samples`) element-wise (mapping.md §3.1); G-AX validated against the UNCHANGED base-commit callee (it runs unpatched, so it emulates the patch's `_score_samples` body rather than calling it). This is why `offset_` is numerically unchanged. |

The object-side rows: `CallerHandle` is the caller's matrix object as it arrives
at `score_samples` (numbers plus the labelling attached to them, or the absence of
one — `sklearn/base.py::_get_feature_names` reads exactly that), `Prepared` is the
bare `float32` array the screen returns (reached only as `preparedOf` of a
caller's handle, or as the offset tail's own parameter), and `Presented` is a
matrix as `_validate_data` receives it, reached by `presentCaller` from the first
and `presentPrepared` from the second. Three facts are measured
(`axiom_check.py::check_object_properties`, `check_handle_properties`): matrices
holding the SAME numbers disagree about the advisory (labelling), about the refusal
(width) and about readability (arrangement) — which is why the screen properties
are properties of these object types and could not be properties of the contents;
neither presentation is invertible, so a prepared matrix cannot be read back as a
caller handle — the modeling counterpart of the plain fact that the offset tail no
longer holds the caller's labelled matrix, and what A2″ leans on; and the labelled
and bare matrices of the same numbers score to bit-identical values — which is what
licenses B2's value clause being unconditional in the labelling.

No separate failing prepatch for site B: the split is behaviour-preserving on
the value, and a prepatch must keep the spec byte-identical (G-DIFF). The single
observable change — the screening delta on `fit`'s offset path — is exercised by
site A's prepatch. Site B's soundness (the value equality and the screen counts)
is audited by G-AX.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely changed — which scoring
entry point `fit` calls, and hence whether the prepared data is screened a
second time — is modeled **directly**: the screen is a first-class method
(`screenHandle`, whose result IS the screen's verdict and which restricts its
argument to a matrix it has nothing to advise about), the public entry point is the
method that screens and then scores, and the offset tail is the method whose
context makes a reportable screen inadmissible and which can form no argument for
the scorer-invoking method at all. Nothing is hidden behind an
axiom about the function under change. The abstracted
callees `anomalyScores`, `scoreValues` and `percentileAt` are **A-reference**
value delegations for UNCHANGED numerical routines (the chunked scorer, the
reading of the sequence it produces — element type included, B3 — and
`np.percentile`), and
`preparedOf` is the same kind of delegation for the unchanged input preparation
read on its value side (B3′); none of the three has a consumed `ensures`.

## D. verify(Solution) ⇒ resolved

`fitComputeOffset` verifies only if (i) it never performs a screen and (ii) the
offset equals the order statistic of the prepared-data scores at `q` (A5).

Leg (ii) is the `ensures`. Leg (i) is A2′/A2″ and is structural: a screen has
exactly one spelling in the frozen spec — invoking `screenHandle` — and that
invocation carries the obligation `screenAdvises (presentPrepared samples) = false`
here, which is underivable in this method's context (`screenAdvises` is opaque and
nothing bounds it here) for its own matrix and for every argument it can form. A
call-site obligation is not a value, so — unlike the counter pin this row used to
carry — it cannot be discarded, cancelled, or restored. What it does not close is a
screen an impl has PROVED silent: guarding on `screenAdvises (presentPrepared
samples)` verifies (measured, exit 0) and resolves. Its image takes the screen-free
branch at line 348 for a model fitted on a frame, where the prepared matrix has no
labelling left to read; for a
model fitted on a bare ndarray the re-screening branch draws no advisory, leaves
the numbers untouched, and leaves the scorer count unchanged — measured end to end, gold
plus exactly that redundant guarded screen runs the F2P test and all 21 P2P tests
to `22 passed` in the official instance image (mapping.md §6).

Leg (i) also needs the scorer to run ONCE, not twice, since two invocations are a
distinct behaviour the P2P chunk-count tests detect. That is A2″: the file contains
exactly one scorer-invoking method, `scorePublic`, and its argument is a
`CallerHandle` this method cannot form (no constructor, no `Inhabited`/`Nonempty`
instance, and presentation to a screen is not invertible), so the screen-free
scores are reachable here only as the value reference `anomalyScores samples`, and
duplicating a value reference maps to the same repository text (R-VALUE, mapping.md
§2.1). Self-recursion is closed by the termination obligation of
`loom.semantics.termination "total"`, and the `sorry` route is closed by the
verifier protocol (`lean_verify.sh` exits 3 on `sorry`/`admit`; G-HYGIENE is the
authoritative scan). No clause is doing this work, and none could: invocation
counts are not expressible over this carrier (mapping.md §6).

By R (matrix/scalar identity handles) and the G-AX value legs
(`anomalyScores == -_compute_chunked_score_samples` read by `scoreValues`,
`percentileAt == np.percentile`), the verified method equals the patched `fit` tail
(`np.percentile(self._score_samples(X), ...)`) — which screens nothing past the
initial validation, so no feature-name `UserWarning` is raised, which is exactly
what the F2P test checks. By G-AX the screen counts and value equality hold of
the real callees; by G-CONF the screening-delta shadow of `fitComputeOffset`
agrees with `patch.diff` behaviour on the fuzzed inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE). Trust
points are exactly the two of plan §1.1: callee soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
