# P2 adversarial audit — sympy__sympy-17318

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,9 +96,9 @@
 -- impl-start
 def implementation_decompose (p : List Addend) : Except Unit NestedForm := Id.run do
   if allSquarePosRat p then
+    return Except.ok (depthMatch p)
+  else
     return fastDecomp p
-  else
-    return Except.ok (depthMatch p)
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
 
 -- impl-start
 def implementation_decompose (p : List Addend) : Except Unit NestedForm := Id.run do
-  if allSquarePosRat p then
+  if p.all (fun a => a.sq.isSome) then
     return fastDecomp p
   else
     return Except.ok (depthMatch p)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,10 +95,7 @@
 
 -- impl-start
 def implementation_decompose (p : List Addend) : Except Unit NestedForm := Id.run do
-  if allSquarePosRat p then
-    return fastDecomp p
-  else
-    return Except.ok (depthMatch p)
+  return fastDecomp p
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,10 +95,7 @@
 
 -- impl-start
 def implementation_decompose (p : List Addend) : Except Unit NestedForm := Id.run do
-  if allSquarePosRat p then
-    return fastDecomp p
-  else
-    return Except.ok (depthMatch p)
+  return Except.ok (depthMatch p)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
   if allSquarePosRat p then
     return fastDecomp p
   else
-    return Except.ok (depthMatch p)
+    return Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,9 +96,9 @@
 -- impl-start
 def implementation_decompose (p : List Addend) : Except Unit NestedForm := Id.run do
   if allSquarePosRat p then
-    return fastDecomp p
+    return fastDecomp p.reverse
   else
-    return Except.ok (depthMatch p)
+    return Except.ok (depthMatch p.reverse)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
 
 -- impl-start
 def implementation_decompose (p : List Addend) : Except Unit NestedForm := Id.run do
-  if allSquarePosRat p then
+  if allSquarePosRat p && !p.isEmpty then
     return fastDecomp p
   else
     return Except.ok (depthMatch p)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Decomposing an additive expression into a nested-square-root normal form.

An additive expression is presented as a list of addends. The routine tries to
express it in a normal form built around square roots. Each addend has a square;
the square is classified by whether it is a rational number and, if so, by its
sign.

The behavior is governed by a single decision over the addends:

* When EVERY addend's square is a positive rational, a specialized fast
  decomposition routine applies. That routine is the source of the result on
  this branch; its result is returned unchanged.

* Otherwise — i.e. as soon as some addend's square fails to be a positive
  rational (it is not rational at all, or it is a non-positive rational) — the
  fast routine is not applicable, and a general depth-based matcher produces the
  result instead. The general matcher always yields a normal form (possibly the
  empty one, meaning "no nontrivial decomposition").

We model the outcome as `Except Unit NestedForm`. `Except.ok f` carries a
returned normal form `f`; `Except.error ()` denotes the fast routine being
unable to process its argument and that inability escaping the computation. A
correct computation routes to the general matcher whenever the fast routine is
not applicable, and therefore yields `Except.ok` on that branch — it never lets
an inapplicability escape.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- A single addend of the additive expression. `sq` is the value of the
addend's square WHEN that square is a rational number (`some q`), and `none`
when the square is not rational. `tag` is an opaque identity distinguishing
addends that share the same square. The decision that drives the behavior
observes only `sq`; the two decomposition routines below observe the full
addend. -/
structure Addend where
  sq : Option Rat
  tag : Nat
deriving DecidableEq, Inhabited, Repr

/-- A nested-square-root normal form (the kind of object the routine returns),
identified by its canonical representation. Observed only through equality. -/
structure NestedForm where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The unchanged specialized fast decomposition routine. It is applicable only
when every addend's square is a positive rational; `Except.ok f` is a produced
normal form `f`, and `Except.error ()` is the routine signalling it cannot
process its argument (the inability that, unguarded, escapes the computation).
Its internal algorithm lies outside this behavior and is left abstract. -/
opaque fastDecomp : List Addend → Except Unit NestedForm

/-- The unchanged general depth-based matcher: it always produces a normal form
(possibly the empty one) for any additive expression. Left abstract — it is an
outside callee, not part of the behavior under specification. -/
opaque depthMatch : List Addend → NestedForm
-- axioms-end

-- pure-start
/-- Whether a single addend's square is a positive rational: the square must be
rational (`some q`) and that rational must be strictly positive. -/
def squarePosRat (a : Addend) : Bool :=
  match a.sq with
  | some q => decide (0 < q)
  | none => false

/-- Whether EVERY addend of the expression has a positive-rational square — the
decision that selects the fast decomposition routine. -/
def allSquarePosRat (p : List Addend) : Bool :=
  p.all squarePosRat
-- pure-end

-- post-conditions-start
/-- The outcome of decomposing the additive expression `p`.

If every addend's square is a positive rational: the fast routine is applicable
and its result is returned unchanged (`result = fastDecomp p`).

Otherwise: the fast routine is not applicable, so the general matcher produces
the result and it is returned as `Except.ok (depthMatch p)`. The computation
never propagates the fast routine's inability on this branch. -/
def problem_spec_decompose (p : List Addend) (result : Except Unit NestedForm) : Prop :=
  if allSquarePosRat p = true then
    result = fastDecomp p
  else
    result = Except.ok (depthMatch p)
-- post-conditions-end

-- impl-start
def implementation_decompose (p : List Addend) : Except Unit NestedForm := Id.run do
  if allSquarePosRat p then
    return fastDecomp p
  else
    return Except.ok (depthMatch p)
-- impl-end

-- proof-start
theorem correct_decompose :
    ∀ (p : List Addend),
      problem_spec_decompose p (implementation_decompose p) := by
  intro p
  unfold problem_spec_decompose implementation_decompose
  by_cases h : allSquarePosRat p = true
  · simp only [Id.run, h, if_true]; rfl
  · simp only [Id.run, h]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output on BOTH branches: problem_spec_decompose p result := if allSquarePosRat p then result = fastDecomp p else result = Except.ok (depthMatch p). Both routines are `opaque` (fastDecomp, depthMatch) with no reduction equations, so any same-spec impl deviating from the exact gold control cannot close its proof (rfl fails; no alternate rewrite path exists because opaque = no equation lemmas). Ran positive control + 7 DISTINCT same_spec=True wrong impls concurrently (<=4 at a time) via scripts/lean_verify.sh.

### Results
- pos_control: EXIT=0, verifies. `#print axioms correct_decompose` => [propext] only (clean; opaque callees register no axioms). Files pos_control.lean / pos_axcheck.lean.
- atk_1 (branches swapped): EXIT=1, genuine rfl failure lines 111/112.
- atk_2 (PREPATCH bug: guard `p.all (fun a => a.sq.isSome)`, rational-only, omits positivity): EXIT=1, genuine rfl failure. Prepatch behavior reproduced/encoded.
- atk_3 (always fastDecomp p): EXIT=1, rfl failure at 109.
- atk_4 (always Except.ok (depthMatch p)): EXIT=1, rfl failure at 108.
- atk_5 (control-flow-effect: else escapes Except.error ()): EXIT=1, rfl failure; goal (if false=true then pure (fastDecomp p) else pure (Except.error ())) = Except.ok (depthMatch p) unclosable.
- atk_6 (ungrounded-oracle echo: callees fed p.reverse): EXIT=1, rfl failure 111/112.
- atk_7 (boundary: extra `!p.isEmpty` conjunct, breaks empty-list case where all=true selects fast): EXIT=1, rfl failure.

All 7 attacks are genuine `rfl`/proof failures (not syntax errors), so NO wrong impl produced a closing clean-axiom proof; protocol step 2 (materialize+resolve faithful patch) has no verify-and-not-correct witness to run. Commands: `bash scripts/lean_verify.sh <path>`. same_spec verified True for all 7 attacks + pos_control via swebench_unified.markers.same_spec on backend 'lean'.

refinement.md audit: Leg 1 (guard) = R, deeply modeled as allSquarePosRat (exact Option Rat arithmetic; matches patched `all(sq.is_Rational and sq.is_positive)`). Legs 2/3 (fastDecomp<->split_surds, depthMatch<->depth matcher) = A-reference, both opaque, NO property consumed by the proof; correspondence to real callees documented in mapping.md and consistent. No A-consumed axiom, no kind-3 (unjustified) legs. A-leg correspondence holds. Sound.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Decomposing an additive expression into a nested-square-root normal form.

An additive expression is presented as a list of addends. The routine tries to
express it in a normal form built around square roots. Each addend has a square;
the square is classified by whether it is a rational number and, if so, by its
sign.

The behavior is governed by a single decision over the addends:

* When EVERY addend's square is a positive rational, a specialized fast
  decomposition routine applies. That routine is the source of the result on
  this branch; its result is returned unchanged.

* Otherwise — i.e. as soon as some addend's square fails to be a positive
  rational (it is not rational at all, or it is a non-positive rational) — the
  fast routine is not applicable, and a general depth-based matcher produces the
  result instead. The general matcher always yields a normal form (possibly the
  empty one, meaning "no nontrivial decomposition").

We model the outcome as `Except Unit NestedForm`. `Except.ok f` carries a
returned normal form `f`; `Except.error ()` denotes the fast routine being
unable to process its argument and that inability escaping the computation. A
correct computation routes to the general matcher whenever the fast routine is
not applicable, and therefore yields `Except.ok` on that branch — it never lets
an inapplicability escape.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- A single addend of the additive expression. `sq` is the value of the
addend's square WHEN that square is a rational number (`some q`), and `none`
when the square is not rational. `tag` is an opaque identity distinguishing
addends that share the same square. The decision that drives the behavior
observes only `sq`; the two decomposition routines below observe the full
addend. -/
structure Addend where
  sq : Option Rat
  tag : Nat
deriving DecidableEq, Inhabited, Repr

/-- A nested-square-root normal form (the kind of object the routine returns),
identified by its canonical representation. Observed only through equality. -/
structure NestedForm where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The unchanged specialized fast decomposition routine. It is applicable only
when every addend's square is a positive rational; `Except.ok f` is a produced
normal form `f`, and `Except.error ()` is the routine signalling it cannot
process its argument (the inability that, unguarded, escapes the computation).
Its internal algorithm lies outside this behavior and is left abstract. -/
opaque fastDecomp : List Addend → Except Unit NestedForm

/-- The unchanged general depth-based matcher: it always produces a normal form
(possibly the empty one) for any additive expression. Left abstract — it is an
outside callee, not part of the behavior under specification. -/
opaque depthMatch : List Addend → NestedForm
-- axioms-end

-- pure-start
/-- Whether a single addend's square is a positive rational: the square must be
rational (`some q`) and that rational must be strictly positive. -/
def squarePosRat (a : Addend) : Bool :=
  match a.sq with
  | some q => decide (0 < q)
  | none => false

/-- Whether EVERY addend of the expression has a positive-rational square — the
decision that selects the fast decomposition routine. -/
def allSquarePosRat (p : List Addend) : Bool :=
  p.all squarePosRat
-- pure-end

-- post-conditions-start
/-- The outcome of decomposing the additive expression `p`.

If every addend's square is a positive rational: the fast routine is applicable
and its result is returned unchanged (`result = fastDecomp p`).

Otherwise: the fast routine is not applicable, so the general matcher produces
the result and it is returned as `Except.ok (depthMatch p)`. The computation
never propagates the fast routine's inability on this branch. -/
def problem_spec_decompose (p : List Addend) (result : Except Unit NestedForm) : Prop :=
  if allSquarePosRat p = true then
    result = fastDecomp p
  else
    result = Except.ok (depthMatch p)
-- post-conditions-end

-- impl-start
def implementation_decompose (p : List Addend) : Except Unit NestedForm := Id.run do
  if allSquarePosRat p then
    return fastDecomp p
  else
    return Except.ok (depthMatch p)
-- impl-end

-- proof-start
theorem correct_decompose :
    ∀ (p : List Addend),
      problem_spec_decompose p (implementation_decompose p) := by
  intro p
  unfold problem_spec_decompose implementation_decompose
  by_cases h : allSquarePosRat p = true
  · simp only [Id.run, h, if_true]; rfl
  · simp only [Id.run, h]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output on BOTH branches: problem_spec_decompose p result := if allSquarePosRat p then result = fastDecomp p else result = Except.ok (depthMatch p). Both routines are `opaque` (fastDecomp, depthMatch) with no reduction equations, so any same-spec impl deviating from the exact gold control cannot close its proof (rfl fails; no alternate rewrite path exists because opaque = no equation lemmas). Ran positive control + 7 DISTINCT same_spec=True wrong impls concurrently (<=4 at a time) via scripts/lean_verify.sh.

### Results
- pos_control: EXIT=0, verifies. `#print axioms correct_decompose` => [propext] only (clean; opaque callees register no axioms). Files pos_control.lean / pos_axcheck.lean.
- atk_1 (branches swapped): EXIT=1, genuine rfl failure lines 111/112.
- atk_2 (PREPATCH bug: guard `p.all (fun a => a.sq.isSome)`, rational-only, omits positivity): EXIT=1, genuine rfl failure. Prepatch behavior reproduced/encoded.
- atk_3 (always fastDecomp p): EXIT=1, rfl failure at 109.
- atk_4 (always Except.ok (depthMatch p)): EXIT=1, rfl failure at 108.
- atk_5 (control-flow-effect: else escapes Except.error ()): EXIT=1, rfl failure; goal (if false=true then pure (fastDecomp p) else pure (Except.error ())) = Except.ok (depthMatch p) unclosable.
- atk_6 (ungrounded-oracle echo: callees fed p.reverse): EXIT=1, rfl failure 111/112.
- atk_7 (boundary: extra `!p.isEmpty` conjunct, breaks empty-list case where all=true selects fast): EXIT=1, rfl failure.

All 7 attacks are genuine `rfl`/proof failures (not syntax errors), so NO wrong impl produced a closing clean-axiom proof; protocol step 2 (materialize+resolve faithful patch) has no verify-and-not-correct witness to run. Commands: `bash scripts/lean_verify.sh <path>`. same_spec verified True for all 7 attacks + pos_control via swebench_unified.markers.same_spec on backend 'lean'.

refinement.md audit: Leg 1 (guard) = R, deeply modeled as allSquarePosRat (exact Option Rat arithmetic; matches patched `all(sq.is_Rational and sq.is_positive)`). Legs 2/3 (fastDecomp<->split_surds, depthMatch<->depth matcher) = A-reference, both opaque, NO property consumed by the proof; correspondence to real callees documented in mapping.md and consistent. No A-consumed axiom, no kind-3 (unjustified) legs. A-leg correspondence holds. Sound.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real repo callee.

Model shape: only the guard predicate `allSquarePosRat` is deeply modeled (R-content); the two decomposition routines (`fastDecomp`↔`split_surds`, `depthMatch`↔the depth-based matcher) are honestly abstract `opaque` A-reference values whose properties the proof never consumes, so the spec cannot over- or under-constrain them.

Guard fidelity: conformance_check.py (Python shadow of `allSquarePosRat` vs the EXACT patched predicate `all(sq.is_Rational and sq.is_positive for sq in [x**2 for x in pargs])`) run against the real sympy source with mpmath: checked=120010, disagreements=0 (pinned seed 17318), including boundary shapes 4+I, I, mixed-sign, non-positive rational, and irrational-square addends. squarePosRat(none)=false correctly matches sympy's None/False is_Rational falsy semantics; squarePosRat(some q)=(0<q) matches is_Rational∧is_positive for a definite Rational.

Routing fidelity: guard-true → result=fastDecomp p (== the returned split_surds result); guard-false → result=Except.ok (depthMatch p), i.e. success, never error. The 'never error on the non-fast branch' claim is exactly what the gold patch installs (base_commit raised IndexError from split_surds; the patch routes non-positive-rational-square expressions to the general matcher which returns a form). F2P test_issue_12420 (_sqrt_match(4+I)==[], no raise) confirms real behavior matches — the spec is not too strong.

Integrity: Solution.lean compiles (exit 0); #print axioms correct_decompose = [propext] only, no sorryAx (genuine proof). same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Solution_prepatch.lean fails (uses sorry: the carried gold proof cannot close on the discriminating clause where allSquarePosRat=false yet every square is rational), confirming the spec discriminates the gold behavior change. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigor checks: same_spec(Solution, Solution_prepatch, lean)=True (frozen spec regions axioms/pure/post-conditions byte-identical); lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). Gold edit strengthens the _sqrt_match is_Add guard from all((x**2).is_Rational) to all(sq.is_Rational and sq.is_positive) — adding the POSITIVITY requirement so a complex/imaginary addend (square = negative rational) no longer enters split_surds and IndexError is avoided. Public problem_statement already discloses: the full traceback _sqrt_match->split_surds->_split_gcd->g=a[0] IndexError, the failing input (3 - sqrt(2)*sqrt(4 + 3*I) + 3*I)/2 whose imaginary addend has a NEGATIVE-rational square, and the instruction 'If an expression cannot be denested it should be returned unchanged.' The gold diff text itself appears ONLY in hints_text (excluded from the leakage standard). Spec view uses only abstract carriers (Addend.sq : Option Rat, opaque fastDecomp/depthMatch, NestedForm) — no repo symbol names (split_surds/_sqrt_match), no file paths, no concrete input expression, no gold-patch tokens. Its 'positive rational' guard is the natural publicly-derivable characterization of split_surds applicability given the traceback and the negative-square offending input; a behavioral spec necessarily describes correct behavior. No line hands over the gold edit beyond what problem_statement already implies. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
