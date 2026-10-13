# P2 adversarial audit — sympy__sympy-21379

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,7 @@
         p' := reduceByFactor p g
         q' := reduceByFactor q g
   | Except.error () =>
-      G := one
+      return Except.error ()
   return Except.ok (G, p', q')
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,6 @@
       G := g
       if g ≠ one then
         p' := reduceByFactor p g
-        q' := reduceByFactor q g
   | Except.error () =>
       G := one
   return Except.ok (G, p', q')
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,9 +91,9 @@
       if g ≠ one then
         p' := reduceByFactor p g
         q' := reduceByFactor q g
+      return Except.ok (G, p', q')
   | Except.error () =>
-      G := one
-  return Except.ok (G, p', q')
+      return Except.ok (one, q, p)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,7 +88,7 @@
   match extractFactor p q with
   | Except.ok g =>
       G := g
-      if g ≠ one then
+      if g = one then
         p' := reduceByFactor p g
         q' := reduceByFactor q g
   | Except.error () =>
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,6 @@
   let mut q' := q
   match extractFactor p q with
   | Except.ok g =>
-      G := g
       if g ≠ one then
         p' := reduceByFactor p g
         q' := reduceByFactor q g
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,18 +82,8 @@
 -- impl-start
 def implementation_factorReduce (p q : Expr) :
     Except Unit (Expr × Expr × Expr) := Id.run do
-  let mut G : Expr := one
-  let mut p' := p
-  let mut q' := q
-  match extractFactor p q with
-  | Except.ok g =>
-      G := g
-      if g ≠ one then
-        p' := reduceByFactor p g
-        q' := reduceByFactor q g
-  | Except.error () =>
-      G := one
-  return Except.ok (G, p', q')
+  let _ := extractFactor p q
+  return Except.ok (one, p, q)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,8 +89,8 @@
   | Except.ok g =>
       G := g
       if g ≠ one then
-        p' := reduceByFactor p g
-        q' := reduceByFactor q g
+        p' := reduceByFactor q g
+        q' := reduceByFactor p g
   | Except.error () =>
       G := one
   return Except.ok (G, p', q')
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,9 +88,8 @@
   match extractFactor p q with
   | Except.ok g =>
       G := g
-      if g ≠ one then
-        p' := reduceByFactor p g
-        q' := reduceByFactor q g
+      p' := reduceByFactor p g
+      q' := reduceByFactor q g
   | Except.error () =>
       G := one
   return Except.ok (G, p', q')
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Tolerating a failure of common-factor extraction during expression
simplification.

A symbolic-simplification step works on two expressions `p` and `q`. It first
asks a helper routine for a common factor shared by the two expressions:

  * If the routine succeeds with a factor `g`, that factor is recorded. When the
    factor is nontrivial (different from the unit `1`), both expressions are
    rewritten by dividing out the factor; when the factor is the unit, the two
    expressions are left unchanged.
  * For some symbolic expressions the factor-extraction routine cannot produce a
    result and signals a failure.

The desired behavior is that such a failure is TOLERATED rather than propagated:
when extraction fails the step falls back to treating the common factor as the
unit `1` and leaves both expressions unchanged, and the overall step always
produces a result instead of aborting.

We model the outcome as `Except Unit (Expr × Expr × Expr)`. `Except.ok (G, p, q)`
carries the recorded factor `G` together with the (possibly rewritten)
expressions forward; `Except.error ()` denotes the failure escaping the step. A
correct step never yields `Except.error ()`.
-/

-- axioms-start
/-- A symbolic expression, identified by its canonical representation. The
behavior under specification observes expressions only through equality
(comparing a factor against the unit) and through the unchanged helper routines
below, so a representation-tagged carrier is a faithful model. -/
structure Expr where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The unit expression `1`. -/
opaque one : Expr

/-- The unchanged helper routine that attempts to extract a common factor of two
expressions. `Except.ok g` is a successfully extracted factor `g`; `Except.error
()` is the routine signalling that it cannot handle the given expressions. Its
internal algorithm is outside this behavior and is left abstract: the
specification constrains none of its inner workings, only its result shape. -/
opaque extractFactor : Expr → Expr → Except Unit Expr

/-- The unchanged helper routine that rewrites an expression by dividing out a
factor (the per-expression rewrite applied when a nontrivial common factor was
found). Left abstract — it is an outside callee, not part of the behavior under
specification. -/
opaque reduceByFactor : Expr → Expr → Expr
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is the control flow
-- around the two unchanged helper routines above.
-- pure-end

-- post-conditions-start
/-- The outcome of the common-factor simplification step on `(p, q)`.

If factor extraction succeeds with `g`: the result is `Except.ok (g, p', q')`
where, when `g` is the unit, both expressions are unchanged, and otherwise each
is rewritten by dividing out `g`.

If factor extraction fails: the failure is tolerated — the result is
`Except.ok (1, p, q)` (the factor recorded as the unit, both expressions
unchanged). The step never yields `Except.error ()`. -/
def problem_spec_factorReduce (p q : Expr)
    (result : Except Unit (Expr × Expr × Expr)) : Prop :=
  match extractFactor p q with
  | Except.ok g =>
      result = Except.ok
        (g,
         (if g = one then p else reduceByFactor p g),
         (if g = one then q else reduceByFactor q g))
  | Except.error () =>
      result = Except.ok (one, p, q)
-- post-conditions-end

-- impl-start
def implementation_factorReduce (p q : Expr) :
    Except Unit (Expr × Expr × Expr) := Id.run do
  let mut G : Expr := one
  let mut p' := p
  let mut q' := q
  match extractFactor p q with
  | Except.ok g =>
      G := g
      if g ≠ one then
        p' := reduceByFactor p g
        q' := reduceByFactor q g
  | Except.error () =>
      G := one
  return Except.ok (G, p', q')
-- impl-end

-- proof-start
theorem correct_factorReduce :
    ∀ (p q : Expr),
      problem_spec_factorReduce p q (implementation_factorReduce p q) := by
  intro p q
  unfold problem_spec_factorReduce implementation_factorReduce
  cases h : extractFactor p q with
  | ok g =>
      by_cases hg : g = one
      · simp only [Id.run, hg, ne_eq, not_true_eq_false, if_false, if_true]
        rfl
      · simp only [Id.run, hg, ne_eq, if_false]
        rfl
  | error e =>
      cases e
      rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TOTAL-FUNCTIONAL: problem_spec_factorReduce matches on extractFactor p q and pins the result EXACTLY for every input with zero output freedom — ok g -> ok (g, ite(g=one) p (reduceByFactor p g), ite(g=one) q (reduceByFactor q g)); error () -> ok (one, p, q). Any verifying impl is observationally equal to gold on all inputs.

### Protocol run
- Positive control pos_control.lean (byte-copy of gold Solution.lean): `bash scripts/lean_verify.sh <path>` -> EXIT 0. `#print axioms correct_factorReduce` -> [propext, Quot.sound], CLEAN (no sorryAx; opaque one/extractFactor/reduceByFactor correctly absent).
- All 8 attacks: same_spec via swebench_unified.markers.same_spec (lean) -> True (axioms/pure/pre/post byte-identical; only impl region edited).
- Verifications run concurrently (2 background batches of 4): every attack `bash scripts/lean_verify.sh atk_N.lean` -> EXIT 1 (proof error), each a GENUINE residual proof goal (semantic mismatch), not a syntax error.

### ATTACKS (all same_spec=True):
  atk_1 prepatch-bug (error()->return Except.error ()) EXIT1 residual `match Except.error PUnit.unit ...` != ok(one,p,q) — reproduces base_commit propagation bug; the discriminating clause.
  atk_2 partial-domain/asymmetric (rewrite p only, forget q) EXIT1 residual q unchanged vs reduceByFactor q g.
  atk_3 boundary/swap error branch ok(one,q,p) EXIT1 residual (one,q,p)!=(one,p,q).
  atk_4 boundary inverted condition (rewrite when g=one) EXIT1 residual `if ¬False` mismatch.
  atk_5 control-flow-effect (drop G:=g on success, G stays one) EXIT1 residual one vs g mismatch.
  atk_6 ungrounded-oracle echo (ignore extractFactor, always ok(one,p,q)) EXIT1 residual pure(ok(one,p,q)) != ok(g, reduceByFactor p g, reduceByFactor q g).
  atk_7 swapped reduce args (reduceByFactor q g / p g) EXIT1 residual reduceByFactor q g vs reduceByFactor p g.
  atk_8 control-flow (unconditional rewrite, no g≠one guard) EXIT1 residual rewrite applied when g=one.

NO wrong impl CLOSES with clean axioms, so the break condition (a verifying impl whose materialized faithful patch does NOT resolve) is UNREACHABLE — no patch materialization/resolve run was required (patches={}); every closing impl is forced to (a) tolerate extraction failure with exactly ok(one,p,q) and (b) rewrite BOTH operands on the nontrivial branch, i.e. transliterate to gold's try/except PolynomialError: G=S.One + unchanged if G!=1: p,q=[gcd_terms(i/G,…)…].

REFINEMENT.MD A-LEG AUDIT: Solution.lean declares 3 opaque callees, 0 axiom. No axiom <callee>_prop declared/consumed (A-consumed=none). Legs are all R / A-reference / I — NO kind-3 (ungrounded). A-references correspond faithfully to real callees at base_commit 624217179aaf8d094e6ff75b7493ad1ee47599b0: extractFactor<->gcd (sympy/core/mod.py:169 / polys/polytools.py:5306), reduceByFactor<->gcd_terms(i/G, clear=False, fraction=False) (mod.py:171-172 / core/exprtools.py), one<->S.One. Row 6 (the fix): caught PolynomialError -> error() arm -> G:=one, operands unchanged; matches gold except-clause. Proof consumes NO callee result property, so no over-strong contract to drift (G-AX justified skip). Correspondence holds.

VERDICT: SOUND — 8 distinct same-spec wrong impls (incl. prepatch bug) all fail to verify with genuine residual goals; positive control verifies with clean axioms; refinement A-legs faithful.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Tolerating a failure of common-factor extraction during expression
simplification.

A symbolic-simplification step works on two expressions `p` and `q`. It first
asks a helper routine for a common factor shared by the two expressions:

  * If the routine succeeds with a factor `g`, that factor is recorded. When the
    factor is nontrivial (different from the unit `1`), both expressions are
    rewritten by dividing out the factor; when the factor is the unit, the two
    expressions are left unchanged.
  * For some symbolic expressions the factor-extraction routine cannot produce a
    result and signals a failure.

The desired behavior is that such a failure is TOLERATED rather than propagated:
when extraction fails the step falls back to treating the common factor as the
unit `1` and leaves both expressions unchanged, and the overall step always
produces a result instead of aborting.

We model the outcome as `Except Unit (Expr × Expr × Expr)`. `Except.ok (G, p, q)`
carries the recorded factor `G` together with the (possibly rewritten)
expressions forward; `Except.error ()` denotes the failure escaping the step. A
correct step never yields `Except.error ()`.
-/

-- axioms-start
/-- A symbolic expression, identified by its canonical representation. The
behavior under specification observes expressions only through equality
(comparing a factor against the unit) and through the unchanged helper routines
below, so a representation-tagged carrier is a faithful model. -/
structure Expr where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The unit expression `1`. -/
opaque one : Expr

/-- The unchanged helper routine that attempts to extract a common factor of two
expressions. `Except.ok g` is a successfully extracted factor `g`; `Except.error
()` is the routine signalling that it cannot handle the given expressions. Its
internal algorithm is outside this behavior and is left abstract: the
specification constrains none of its inner workings, only its result shape. -/
opaque extractFactor : Expr → Expr → Except Unit Expr

/-- The unchanged helper routine that rewrites an expression by dividing out a
factor (the per-expression rewrite applied when a nontrivial common factor was
found). Left abstract — it is an outside callee, not part of the behavior under
specification. -/
opaque reduceByFactor : Expr → Expr → Expr
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is the control flow
-- around the two unchanged helper routines above.
-- pure-end

-- post-conditions-start
/-- The outcome of the common-factor simplification step on `(p, q)`.

If factor extraction succeeds with `g`: the result is `Except.ok (g, p', q')`
where, when `g` is the unit, both expressions are unchanged, and otherwise each
is rewritten by dividing out `g`.

If factor extraction fails: the failure is tolerated — the result is
`Except.ok (1, p, q)` (the factor recorded as the unit, both expressions
unchanged). The step never yields `Except.error ()`. -/
def problem_spec_factorReduce (p q : Expr)
    (result : Except Unit (Expr × Expr × Expr)) : Prop :=
  match extractFactor p q with
  | Except.ok g =>
      result = Except.ok
        (g,
         (if g = one then p else reduceByFactor p g),
         (if g = one then q else reduceByFactor q g))
  | Except.error () =>
      result = Except.ok (one, p, q)
-- post-conditions-end

-- impl-start
def implementation_factorReduce (p q : Expr) :
    Except Unit (Expr × Expr × Expr) := Id.run do
  let mut G : Expr := one
  let mut p' := p
  let mut q' := q
  match extractFactor p q with
  | Except.ok g =>
      G := g
      if g ≠ one then
        p' := reduceByFactor p g
        q' := reduceByFactor q g
  | Except.error () =>
      G := one
  return Except.ok (G, p', q')
-- impl-end

-- proof-start
theorem correct_factorReduce :
    ∀ (p q : Expr),
      problem_spec_factorReduce p q (implementation_factorReduce p q) := by
  intro p q
  unfold problem_spec_factorReduce implementation_factorReduce
  cases h : extractFactor p q with
  | ok g =>
      by_cases hg : g = one
      · simp only [Id.run, hg, ne_eq, not_true_eq_false, if_false, if_true]
        rfl
      · simp only [Id.run, hg, ne_eq, if_false]
        rfl
  | error e =>
      cases e
      rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TOTAL-FUNCTIONAL: problem_spec_factorReduce matches on extractFactor p q and pins the result EXACTLY for every input with zero output freedom — ok g -> ok (g, ite(g=one) p (reduceByFactor p g), ite(g=one) q (reduceByFactor q g)); error () -> ok (one, p, q). Any verifying impl is observationally equal to gold on all inputs.

### Protocol run
- Positive control pos_control.lean (byte-copy of gold Solution.lean): `bash scripts/lean_verify.sh <path>` -> EXIT 0. `#print axioms correct_factorReduce` -> [propext, Quot.sound], CLEAN (no sorryAx; opaque one/extractFactor/reduceByFactor correctly absent).
- All 8 attacks: same_spec via swebench_unified.markers.same_spec (lean) -> True (axioms/pure/pre/post byte-identical; only impl region edited).
- Verifications run concurrently (2 background batches of 4): every attack `bash scripts/lean_verify.sh atk_N.lean` -> EXIT 1 (proof error), each a GENUINE residual proof goal (semantic mismatch), not a syntax error.

### ATTACKS (all same_spec=True):
  atk_1 prepatch-bug (error()->return Except.error ()) EXIT1 residual `match Except.error PUnit.unit ...` != ok(one,p,q) — reproduces base_commit propagation bug; the discriminating clause.
  atk_2 partial-domain/asymmetric (rewrite p only, forget q) EXIT1 residual q unchanged vs reduceByFactor q g.
  atk_3 boundary/swap error branch ok(one,q,p) EXIT1 residual (one,q,p)!=(one,p,q).
  atk_4 boundary inverted condition (rewrite when g=one) EXIT1 residual `if ¬False` mismatch.
  atk_5 control-flow-effect (drop G:=g on success, G stays one) EXIT1 residual one vs g mismatch.
  atk_6 ungrounded-oracle echo (ignore extractFactor, always ok(one,p,q)) EXIT1 residual pure(ok(one,p,q)) != ok(g, reduceByFactor p g, reduceByFactor q g).
  atk_7 swapped reduce args (reduceByFactor q g / p g) EXIT1 residual reduceByFactor q g vs reduceByFactor p g.
  atk_8 control-flow (unconditional rewrite, no g≠one guard) EXIT1 residual rewrite applied when g=one.

NO wrong impl CLOSES with clean axioms, so the break condition (a verifying impl whose materialized faithful patch does NOT resolve) is UNREACHABLE — no patch materialization/resolve run was required (patches={}); every closing impl is forced to (a) tolerate extraction failure with exactly ok(one,p,q) and (b) rewrite BOTH operands on the nontrivial branch, i.e. transliterate to gold's try/except PolynomialError: G=S.One + unchanged if G!=1: p,q=[gcd_terms(i/G,…)…].

REFINEMENT.MD A-LEG AUDIT: Solution.lean declares 3 opaque callees, 0 axiom. No axiom <callee>_prop declared/consumed (A-consumed=none). Legs are all R / A-reference / I — NO kind-3 (ungrounded). A-references correspond faithfully to real callees at base_commit 624217179aaf8d094e6ff75b7493ad1ee47599b0: extractFactor<->gcd (sympy/core/mod.py:169 / polys/polytools.py:5306), reduceByFactor<->gcd_terms(i/G, clear=False, fraction=False) (mod.py:171-172 / core/exprtools.py), one<->S.One. Row 6 (the fix): caught PolynomialError -> error() arm -> G:=one, operands unchanged; matches gold except-clause. Proof consumes NO callee result property, so no over-strong contract to drift (G-AX justified skip). Correspondence holds.

VERDICT: SOUND — 8 distinct same-spec wrong impls (incl. prepatch bug) all fail to verify with genuine residual goals; positive control verifies with clean axioms; refinement A-legs faithful.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (drift) check for sympy__sympy-21379 lean bundle. The spec models the Mod.eval 'extract gcd' block: extractFactor=gcd (Except.ok g / Except.error () = PolynomialError raise), reduceByFactor=gcd_terms(i/G), one=S.One. Verified: (1) Solution.lean compiles (lean_verify exit 0) and #print axioms correct_factorReduce = [propext, Quot.sound] — no sorryAx, proof genuine. (2) same_spec(Solution, prepatch, lean-backend) = True — spec region byte-identical. (3) Repo worktree at base_commit 624217179a confirms PolynomialError originates from gcd(p,q) at mod.py:169, matching the extractFactor→error() modeling. Examined the one real drift candidate: the gold try/except wraps BOTH gcd AND the gcd_terms rewrite, but the spec models reduceByFactor(gcd_terms) as a TOTAL opaque callee. Divergence would need gcd to succeed with g≠1 while gcd_terms(i/g) then raises PolynomialError (real→ok(1,p,q); spec→ok(g,reduced,reduced)). Probed 1635 randomized success-branch (g≠1) cases plus targeted Piecewise/exotic inputs: gcd_terms never raised PolynomialError — its _gcd_terms/primitive/factor_terms path handles Piecewise gracefully and never hits the parallel_poly_from_expr generator machinery that raises 'Piecewise generators do not make sense'. Thus the modeled function agrees with the real callee on all reachable inputs. On gcd-success it matches; on gcd raising PolynomialError it matches (G=S.One, p,q unchanged, block completes = ok(one,p,q)). Non-PolynomialError exceptions from gcd are outside the modeled callee contract (error() ↦ PolynomialError only per mapping.md). No diverging input found; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (not hints_text, which carries the exact gold diff). Findings:

1) Spec byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean) = True — prepatch differs only in impl/proof regions; the spec view (imports/docstring/axioms/pure/post-conditions) is identical. Spec-view hash matches meta.json G-HYGIENE region_hashes.spec_view (d57a0f72...).

2) Mechanical G-LEAK (leakage.screen) passes with zero failures: no reproduced gold-patch line, no diff markers, no patched file path (sympy/core/mod.py) or module path, no changed-symbol echo (changed symbols {eval, doit} absent from spec view), no fix-narration keywords (bug/fix/patch/etc.).

3) Semantic scan for gold-edit disclosure beyond problem_statement: the gold edit wraps the gcd/gcd_terms block of Mod.eval in try/except PolynomialError: G = S.One (sympy/core/mod.py). NONE of the repo/edit-specific tokens appear in the spec view — no 'gcd', 'PolynomialError', 'mod.py', 'S.One', 'gcd_terms', 'polytools', 'polyerrors', 'doit', 'Piecewise', 'subs', 'try', or 'issue 21373'. The lone 'except' hit is Lean's `Except` error-monad carrier type, a legitimate abstract modeling device, not the Python `except` keyword.

4) The spec is fully abstracted: generic model names (extractFactor, reduceByFactor, one, Expr) and prose describing a generic 'common-factor simplification step' whose helper-routine failure is TOLERATED by falling back to the unit and always producing a result. This states the required post-fix behavior at the necessary abstraction level for a spec; it names no repo file/symbol/mechanism and does not disclose the concrete fix (catching an exception). A solver gains no localization of the gold edit that the public bug report (unexpected PolynomialError surfacing out of subs) does not already imply. The problem_statement itself already establishes that a PolynomialError must stop surfacing.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
