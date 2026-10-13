# P2 adversarial audit — sympy__sympy-17139

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,9 @@
   (isMatchingPow rv = true → expIsReal rv = true → result = transform rv)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_powerRewrite (rv : Expr) : Expr := Id.run do
-  if !(isMatchingPow rv) then
-    return rv
   if !(expIsReal rv) then
     return rv
   return transform rv
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,11 +60,10 @@
   (isMatchingPow rv = true → expIsReal rv = true → result = transform rv)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_powerRewrite (rv : Expr) : Expr := Id.run do
   if !(isMatchingPow rv) then
-    return rv
-  if !(expIsReal rv) then
     return rv
   return transform rv
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,13 +60,9 @@
   (isMatchingPow rv = true → expIsReal rv = true → result = transform rv)
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_powerRewrite (rv : Expr) : Expr := Id.run do
-  if !(isMatchingPow rv) then
-    return rv
-  if !(expIsReal rv) then
-    return rv
-  return transform rv
+def implementation_powerRewrite (rv : Expr) : Expr := rv
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,11 +60,12 @@
   (isMatchingPow rv = true → expIsReal rv = true → result = transform rv)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_powerRewrite (rv : Expr) : Expr := Id.run do
   if !(isMatchingPow rv) then
     return rv
-  if !(expIsReal rv) then
+  if expIsReal rv then
     return rv
   return transform rv
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,13 +60,9 @@
   (isMatchingPow rv = true → expIsReal rv = true → result = transform rv)
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_powerRewrite (rv : Expr) : Expr := Id.run do
-  if !(isMatchingPow rv) then
-    return rv
-  if !(expIsReal rv) then
-    return rv
-  return transform rv
+def implementation_powerRewrite (rv : Expr) : Expr := transform rv
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,13 +60,14 @@
   (isMatchingPow rv = true → expIsReal rv = true → result = transform rv)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_powerRewrite (rv : Expr) : Expr := Id.run do
   if !(isMatchingPow rv) then
     return rv
   if !(expIsReal rv) then
     return rv
-  return transform rv
+  return transform (transform rv)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
A guarded rewrite rule for power expressions.

The rule targets an expression only when it is a power whose base is a specific
matching form. For such a matching power the rule applies a rewrite that depends
on the exponent's numeric properties (its sign and magnitude). That rewrite is
only meaningful when the exponent denotes a real quantity: the decisions it makes
are ordering comparisons on the exponent, which are undefined for a non-real
exponent.

The rule therefore behaves as follows:

  * an expression that is not a matching power is returned unchanged;
  * a matching power whose exponent is not a real quantity is returned unchanged;
  * a matching power with a real exponent is returned as the rewrite of that
    power.

Guarding on the exponent being real is what lets the rule leave a matching power
with a non-real exponent untouched instead of attempting an order-based rewrite
that its exponent cannot support.
-/

-- axioms-start
-- Three UNCHANGED outside operations are used identically by the specification
-- and the implementation, so each is carried as an opaque callee and NO property
-- of any is consumed (G-AX skips):
--
--   * `isMatchingPow` — the structural test recognising the expressions this rule
--     acts on (a power whose base has the targeted form). A pure predicate on the
--     expression; its internal structure is out of scope here.
--   * `expIsReal` — the query deciding whether the expression's exponent denotes a
--     real quantity. Carried as an opaque predicate.
--   * `transform` — the exponent-driven rewrite tail applied to a matching power
--     with a real exponent: the WHOLE unchanged body (its sign/magnitude decisions,
--     including the sub-cases that return the input unchanged). Carried opaquely so
--     the result on the real-exponent branch is pinned to its input.
--
-- The expression itself is an opaque carrier: only equality and the two queries
-- above are observed, so it is modelled as a `Nat` tag.
abbrev Expr := Nat
opaque isMatchingPow : Expr → Bool
opaque expIsReal : Expr → Bool
opaque transform : Expr → Expr
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The result of the guarded rewrite: a non-matching expression is unchanged; a
matching power with a non-real exponent is unchanged; a matching power with a real
exponent is the rewrite of that power. -/
def problem_spec_powerRewrite (rv : Expr) (result : Expr) : Prop :=
  (isMatchingPow rv = false → result = rv) ∧
  (isMatchingPow rv = true → expIsReal rv = false → result = rv) ∧
  (isMatchingPow rv = true → expIsReal rv = true → result = transform rv)
-- post-conditions-end

-- impl-start
def implementation_powerRewrite (rv : Expr) : Expr := Id.run do
  if !(isMatchingPow rv) then
    return rv
  if !(expIsReal rv) then
    return rv
  return transform rv
-- impl-end

-- proof-start
theorem correct_powerRewrite :
    ∀ (rv : Expr),
      problem_spec_powerRewrite rv (implementation_powerRewrite rv) := by
  intro rv
  unfold problem_spec_powerRewrite implementation_powerRewrite
  refine ⟨?_, ?_, ?_⟩
  · intro h
    simp only [Id.run, h, Bool.not_false, if_true, pure]
  · intro h1 h2
    simp only [Id.run, h1, h2, Bool.not_true, Bool.not_false, if_true, bind, pure,
      Bool.false_eq_true, if_false]
  · intro h1 h2
    simp only [Id.run, h1, h2, Bool.not_true, bind, pure, Bool.false_eq_true, if_false]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_powerRewrite pins `result` EXACTLY across three exhaustive, mutually-exclusive boolean cases keyed on the two observable opaque queries: (isMatchingPow=false→result=rv) ∧ (isMatchingPow=true ∧ expIsReal=false→result=rv) ∧ (isMatchingPow=true ∧ expIsReal=true→result=transform rv). Because isMatchingPow/expIsReal/transform are opaque with NO consumed axioms (G-AX skips; they cancel between spec and impl), any impl that deviates from this three-way decision tree leaves an unprovable goal (e.g. rv = transform rv with transform opaque). So the spec is fully-determining and verify⇒correct here.

Same_spec confirmed True for pos + all 6 attacks (axioms/pure/pre/post byte-identical; only impl region edited).

Positive control (gold impl): `bash scripts/lean_verify.sh .../pos.lean` → exit 0. `#print axioms correct_powerRewrite` → 'depends on axioms: [propext, Quot.sound]' (clean; no sorryAx, no custom axioms).

6 DISTINCT same-spec wrong impls, all `bash scripts/lean_verify.sh atk_N.lean` → exit 1 (genuine spec disagreement, NOT compile error):
- atk_1 partial-domain: drops isMatchingPow early-exit, guards only on expIsReal → exit 1.
- atk_2 prepatch/boundary bug (the recorded prepatch defect: no realness guard, `if !isMatchingPow then rv; return transform rv`) → exit 1, error 'unsolved goals' at the middle conjunct (matching non-real exponent must be rv, impl gives transform rv). PREPATCH REPRODUCED.
- atk_3 control-flow-effect: identity `rv` (never transforms) → exit 1, 'simp made no progress' on the real-branch conjunct (result=transform rv unprovable).
- atk_4 inverted realness guard (transform on non-real, rv on real) → exit 1.
- atk_5 ungrounded-oracle echo: always `transform rv` → exit 1, 'simp made no progress' on the non-matching and non-real conjuncts.
- atk_6 boundary: double-transform `transform (transform rv)` on real branch → exit 1.

Since NO wrong impl closed with clean axioms, no faithful patches were materialized/resolve-run (step 2 vacuously satisfied — nothing to falsify).

refinement.md audit: 3 legs, all tagged R or R/I; NO A-consumed, NO A-reference, NO kind-3 (unjustified axiomatization of a changed op). The changed op (op 2, the added rv.exp.is_real realness guard) is modeled DEEPLY as a control-flow branch over the observable expIsReal query per SPEC_GUIDE §3 (not axiomatized), and pinned in the spec's middle conjunct. isMatchingPow/expIsReal/transform are UNCHANGED callees carried as opaque signatures appearing identically on spec and impl (cancel in the differential), so G-AX correctly skips. Correspondence to real callees (fu.py:502 structural test, fu.py:504 added is_real guard, fu.py:506-521 rewrite body) is sound per mapping.md. No A-leg correspondence defect found.

All 6 attacks + positive control fully verified; nothing left INCONCLUSIVE.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
A guarded rewrite rule for power expressions.

The rule targets an expression only when it is a power whose base is a specific
matching form. For such a matching power the rule applies a rewrite that depends
on the exponent's numeric properties (its sign and magnitude). That rewrite is
only meaningful when the exponent denotes a real quantity: the decisions it makes
are ordering comparisons on the exponent, which are undefined for a non-real
exponent.

The rule therefore behaves as follows:

  * an expression that is not a matching power is returned unchanged;
  * a matching power whose exponent is not a real quantity is returned unchanged;
  * a matching power with a real exponent is returned as the rewrite of that
    power.

Guarding on the exponent being real is what lets the rule leave a matching power
with a non-real exponent untouched instead of attempting an order-based rewrite
that its exponent cannot support.
-/

-- axioms-start
-- Three UNCHANGED outside operations are used identically by the specification
-- and the implementation, so each is carried as an opaque callee and NO property
-- of any is consumed (G-AX skips):
--
--   * `isMatchingPow` — the structural test recognising the expressions this rule
--     acts on (a power whose base has the targeted form). A pure predicate on the
--     expression; its internal structure is out of scope here.
--   * `expIsReal` — the query deciding whether the expression's exponent denotes a
--     real quantity. Carried as an opaque predicate.
--   * `transform` — the exponent-driven rewrite tail applied to a matching power
--     with a real exponent: the WHOLE unchanged body (its sign/magnitude decisions,
--     including the sub-cases that return the input unchanged). Carried opaquely so
--     the result on the real-exponent branch is pinned to its input.
--
-- The expression itself is an opaque carrier: only equality and the two queries
-- above are observed, so it is modelled as a `Nat` tag.
abbrev Expr := Nat
opaque isMatchingPow : Expr → Bool
opaque expIsReal : Expr → Bool
opaque transform : Expr → Expr
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The result of the guarded rewrite: a non-matching expression is unchanged; a
matching power with a non-real exponent is unchanged; a matching power with a real
exponent is the rewrite of that power. -/
def problem_spec_powerRewrite (rv : Expr) (result : Expr) : Prop :=
  (isMatchingPow rv = false → result = rv) ∧
  (isMatchingPow rv = true → expIsReal rv = false → result = rv) ∧
  (isMatchingPow rv = true → expIsReal rv = true → result = transform rv)
-- post-conditions-end

-- impl-start
def implementation_powerRewrite (rv : Expr) : Expr := Id.run do
  if !(isMatchingPow rv) then
    return rv
  if !(expIsReal rv) then
    return rv
  return transform rv
-- impl-end

-- proof-start
theorem correct_powerRewrite :
    ∀ (rv : Expr),
      problem_spec_powerRewrite rv (implementation_powerRewrite rv) := by
  intro rv
  unfold problem_spec_powerRewrite implementation_powerRewrite
  refine ⟨?_, ?_, ?_⟩
  · intro h
    simp only [Id.run, h, Bool.not_false, if_true, pure]
  · intro h1 h2
    simp only [Id.run, h1, h2, Bool.not_true, Bool.not_false, if_true, bind, pure,
      Bool.false_eq_true, if_false]
  · intro h1 h2
    simp only [Id.run, h1, h2, Bool.not_true, bind, pure, Bool.false_eq_true, if_false]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_powerRewrite pins `result` EXACTLY across three exhaustive, mutually-exclusive boolean cases keyed on the two observable opaque queries: (isMatchingPow=false→result=rv) ∧ (isMatchingPow=true ∧ expIsReal=false→result=rv) ∧ (isMatchingPow=true ∧ expIsReal=true→result=transform rv). Because isMatchingPow/expIsReal/transform are opaque with NO consumed axioms (G-AX skips; they cancel between spec and impl), any impl that deviates from this three-way decision tree leaves an unprovable goal (e.g. rv = transform rv with transform opaque). So the spec is fully-determining and verify⇒correct here.

Same_spec confirmed True for pos + all 6 attacks (axioms/pure/pre/post byte-identical; only impl region edited).

Positive control (gold impl): `bash scripts/lean_verify.sh .../pos.lean` → exit 0. `#print axioms correct_powerRewrite` → 'depends on axioms: [propext, Quot.sound]' (clean; no sorryAx, no custom axioms).

6 DISTINCT same-spec wrong impls, all `bash scripts/lean_verify.sh atk_N.lean` → exit 1 (genuine spec disagreement, NOT compile error):
- atk_1 partial-domain: drops isMatchingPow early-exit, guards only on expIsReal → exit 1.
- atk_2 prepatch/boundary bug (the recorded prepatch defect: no realness guard, `if !isMatchingPow then rv; return transform rv`) → exit 1, error 'unsolved goals' at the middle conjunct (matching non-real exponent must be rv, impl gives transform rv). PREPATCH REPRODUCED.
- atk_3 control-flow-effect: identity `rv` (never transforms) → exit 1, 'simp made no progress' on the real-branch conjunct (result=transform rv unprovable).
- atk_4 inverted realness guard (transform on non-real, rv on real) → exit 1.
- atk_5 ungrounded-oracle echo: always `transform rv` → exit 1, 'simp made no progress' on the non-matching and non-real conjuncts.
- atk_6 boundary: double-transform `transform (transform rv)` on real branch → exit 1.

Since NO wrong impl closed with clean axioms, no faithful patches were materialized/resolve-run (step 2 vacuously satisfied — nothing to falsify).

refinement.md audit: 3 legs, all tagged R or R/I; NO A-consumed, NO A-reference, NO kind-3 (unjustified axiomatization of a changed op). The changed op (op 2, the added rv.exp.is_real realness guard) is modeled DEEPLY as a control-flow branch over the observable expIsReal query per SPEC_GUIDE §3 (not axiomatized), and pinned in the spec's middle conjunct. isMatchingPow/expIsReal/transform are UNCHANGED callees carried as opaque signatures appearing identically on spec and impl (cancel in the differential), so G-AX correctly skips. Correspondence to real callees (fu.py:502 structural test, fu.py:504 added is_real guard, fu.py:506-521 rewrite body) is sound per mapping.md. No A-leg correspondence defect found.

All 6 attacks + positive control fully verified; nothing left INCONCLUSIVE.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sympy__sympy-17139 lean bundle. Modeled function `_f` (sympy/simplify/fu.py:496-521, per-node rewrite inside _TR56); confirmed real post-patch source in worktree at base commit 1d3327b8e9 + patch.diff (adds `if not rv.exp.is_real: return rv` after the matching test).

### Checks performed
1. same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) = True — spec region (axioms/pure/post-conditions) is byte-identical between patch and prepatch; the fix lives only in impl+proof, as required.
2. Solution.lean elaborates cleanly (lean_verify exit 0); `#print axioms correct_powerRewrite` = [propext, Quot.sound] only — NO sorryAx, proof is genuine. Prepatch fails (uses sorry; its guard-less impl `return transform rv` disagrees with the spec's middle conjunct), so the spec is discriminating, not vacuous.
3. conformance_check.py passes 120,005 inputs, 0 disagreements.

FAITHFULNESS ANALYSIS — no diverging input exists:
The spec's three conjuncts key on isMatchingPow then expIsReal, matching the real guard precedence exactly (structural test first, realness guard second, rewrite body last).
The only real hazard is the SymPy fuzzy-bool: rv.exp.is_real ∈ {True,False,None}, and real `not rv.exp.is_real` takes the early-return for BOTH False and None. The model collapses this correctly: expIsReal=true ⟺ is_real is True (take transform), expIsReal=false ⟺ is_real ∈ {False,None} (return rv). Conjunct 2 therefore covers both non-True cases exactly as reality does — no over-strengthening, no divergence.
The rewrite body is folded into opaque `transform`, appearing identically on spec and impl sides, so conjunct 3 cannot disagree with the real callee on any input. (This is an abstraction that keeps the spec at least as WEAK as reality on the transform leg — the opposite of a too-strong defect; any concern about it being too weak is a panel_1 echo question, out of scope for faithfulness.)

Conclusion: the modeled function agrees with the real _f on every input; the spec is a faithful, not-too-strong characterization of post-patch behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen, lean flavor) passes with zero hard failures — independently reproduced: no diff markers; no gold-patch line reproduced (>=8 char normalized); no patched file path (fu.py) or dotted module path (sympy.simplify.fu) in the spec view; no spec-view identifier embedding a patched repo symbol; no comment/docstring naming a patched symbol (no _f, _TR56, TR6, cos, sin, is_real); no bug/fix/patch narration tokens. same_spec(Solution.lean, Solution_prepatch.lean)=True, so the spec view carries no impl-specific signal distinguishing gold from prepatch.

Semantic G-PANEL-3 judgment: the spec view leaks NOTHING beyond the public problem_statement and in fact discloses LESS localization than it. The public problem_statement contains the full traceback naming sympy/simplify/fu.py, functions _f/_TR56/TR6, the exact failing line 'if (rv.exp < 0) == True:', the TypeError 'Invalid comparison of complex I', and the reproducer simplify(cos(x)**I) — from which the fix (guard on non-real exponent before the ordering comparison) is essentially determined. The spec view abstracts all of this to opaque callees (isMatchingPow, expIsReal, transform) over a Nat tag, naming no repo file/function/symbol and quoting no gold-diff line. Its behavioral docstring — a three-way branch where a matching power with a non-real exponent is returned unchanged because ordering comparisons are undefined for non-real exponents — is the necessary specification of the required behavior (which any faithful spec must pin) and is fully deducible from the public traceback. This is specification, not leakage of the edit's location or diff. Not a relaxed bundle; no RELAXED_LEAKAGE.md present or needed.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
