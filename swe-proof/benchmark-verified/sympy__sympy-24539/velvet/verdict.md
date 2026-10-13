# P2 adversarial audit — sympy__sympy-24539

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_7.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The conversion that renders a sparse multivariate datum (a map from monomials
@@ -74,18 +74,13 @@
   ensures out = asExprSpec d ringSymbols symbols
   do
     -- impl-start
-    -- Choose the list of generator names to render over, then hand the datum and
-    -- that list to the unchanged renderer. The caller's own names are honored
-    -- when one per generator is supplied; the datum's names are used when the
-    -- caller supplies none; any other caller length is rejected.
+    -- prepatch bug: every non-rejected path overwrites chosen with ringSymbols,
+    -- so a correctly-sized caller list is silently discarded.
     let mut chosen : List Int := symbols
-    if symbols.isEmpty then
+    if (!symbols.isEmpty) && symbols.length != ringSymbols.length then
+      return Except.error AsExprErr.wrongNumberOfSymbols
+    else
       chosen := ringSymbols
-    else
-      if symbols.length = ringSymbols.length then
-        chosen := symbols
-      else
-        return Except.error AsExprErr.wrongNumberOfSymbols
     return Except.ok (exprFromDict d chosen)
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The conversion that renders a sparse multivariate datum (a map from monomials
@@ -74,15 +74,11 @@
   ensures out = asExprSpec d ringSymbols symbols
   do
     -- impl-start
-    -- Choose the list of generator names to render over, then hand the datum and
-    -- that list to the unchanged renderer. The caller's own names are honored
-    -- when one per generator is supplied; the datum's names are used when the
-    -- caller supplies none; any other caller length is rejected.
     let mut chosen : List Int := symbols
     if symbols.isEmpty then
       chosen := ringSymbols
     else
-      if symbols.length = ringSymbols.length then
+      if symbols.length <= ringSymbols.length then
         chosen := symbols
       else
         return Except.error AsExprErr.wrongNumberOfSymbols
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The conversion that renders a sparse multivariate datum (a map from monomials
@@ -74,19 +74,8 @@
   ensures out = asExprSpec d ringSymbols symbols
   do
     -- impl-start
-    -- Choose the list of generator names to render over, then hand the datum and
-    -- that list to the unchanged renderer. The caller's own names are honored
-    -- when one per generator is supplied; the datum's names are used when the
-    -- caller supplies none; any other caller length is rejected.
-    let mut chosen : List Int := symbols
-    if symbols.isEmpty then
-      chosen := ringSymbols
-    else
-      if symbols.length = ringSymbols.length then
-        chosen := symbols
-      else
-        return Except.error AsExprErr.wrongNumberOfSymbols
-    return Except.ok (exprFromDict d chosen)
+    -- always forward the caller list, never use ringSymbols, never reject
+    return Except.ok (exprFromDict d symbols)
     -- impl-end
 
 prove_correct asExpr by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The conversion that renders a sparse multivariate datum (a map from monomials
@@ -74,16 +74,12 @@
   ensures out = asExprSpec d ringSymbols symbols
   do
     -- impl-start
-    -- Choose the list of generator names to render over, then hand the datum and
-    -- that list to the unchanged renderer. The caller's own names are honored
-    -- when one per generator is supplied; the datum's names are used when the
-    -- caller supplies none; any other caller length is rejected.
-    let mut chosen : List Int := symbols
+    let mut chosen : List Int := ringSymbols
     if symbols.isEmpty then
-      chosen := ringSymbols
+      chosen := symbols
     else
       if symbols.length = ringSymbols.length then
-        chosen := symbols
+        chosen := ringSymbols
       else
         return Except.error AsExprErr.wrongNumberOfSymbols
     return Except.ok (exprFromDict d chosen)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The conversion that renders a sparse multivariate datum (a map from monomials
@@ -74,13 +74,9 @@
   ensures out = asExprSpec d ringSymbols symbols
   do
     -- impl-start
-    -- Choose the list of generator names to render over, then hand the datum and
-    -- that list to the unchanged renderer. The caller's own names are honored
-    -- when one per generator is supplied; the datum's names are used when the
-    -- caller supplies none; any other caller length is rejected.
     let mut chosen : List Int := symbols
     if symbols.isEmpty then
-      chosen := ringSymbols
+      return Except.error AsExprErr.wrongNumberOfSymbols
     else
       if symbols.length = ringSymbols.length then
         chosen := symbols
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- The conversion that renders a sparse multivariate datum (a map from monomials
@@ -74,18 +74,11 @@
   ensures out = asExprSpec d ringSymbols symbols
   do
     -- impl-start
-    -- Choose the list of generator names to render over, then hand the datum and
-    -- that list to the unchanged renderer. The caller's own names are honored
-    -- when one per generator is supplied; the datum's names are used when the
-    -- caller supplies none; any other caller length is rejected.
     let mut chosen : List Int := symbols
     if symbols.isEmpty then
       chosen := ringSymbols
     else
-      if symbols.length = ringSymbols.length then
-        chosen := symbols
-      else
-        return Except.error AsExprErr.wrongNumberOfSymbols
+      chosen := symbols
     return Except.ok (exprFromDict d chosen)
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The conversion that renders a sparse multivariate datum (a map from monomials
   to ground coefficients) into a symbolic expression over a GIVEN ordered list
   of generator names. An UNCHANGED helper the operation delegates to: modeled as
   an uninterpreted function because the operation never inspects the expression
   it produces — its only responsibility is to decide WHICH list of generator
   names to hand over, so no contract is owed about the rendered value
   (directive 7). The datum, each generator name, and the produced expression are
   opaque handles (`Int`); the bijection to the repository value space is in
   mapping.md (G-AX / G-CONF use it). Provenance + executable soundness check:
   mapping.md §3 / axiom_check.py (G-AX). -/
opaque exprFromDict : Int → List Int → Int
-- axioms-end

-- pure-start
/- The only failure the desired behavior distinguishes: a caller-supplied list of
   generator names whose length does not match the number of generators the datum
   lives over. -/
inductive AsExprErr where
  | wrongNumberOfSymbols
  deriving DecidableEq

/- The intended outcome of rendering the datum `d` over an optional caller list of
   generator names `symbols`, given the datum's own ordered generator names
   `ringSymbols` (whose length is the number of generators):

     * if the caller supplies NO names, render over the datum's own names;
     * otherwise, if the supplied list has exactly one name per generator, render
       over the SUPPLIED names (they are honored, not discarded);
     * otherwise the request is rejected.

   Honoring a correctly-sized caller list is the behavior the public problem
   statement requires. -/
def asExprSpec (d : Int) (ringSymbols : List Int) (symbols : List Int) :
    Except AsExprErr Int :=
  if symbols.isEmpty then
    Except.ok (exprFromDict d ringSymbols)
  else
    if symbols.length = ringSymbols.length then
      Except.ok (exprFromDict d symbols)
    else
      Except.error AsExprErr.wrongNumberOfSymbols
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a sparse multivariate datum as a symbolic expression, letting the caller
   choose the generator names.

   `d` is the datum (a map from monomials to ground coefficients) and `ringSymbols`
   are the datum's own ordered generator names — both read-only, so neither is
   `mut`. `symbols` is the caller's optional list of names. Desired behavior: when
   the caller supplies a list whose length equals the number of generators
   (`ringSymbols.length`), the expression must be rendered over the caller's names;
   when the caller supplies nothing, the datum's own names are used; when the
   caller supplies a list of any other length, the request is rejected. The
   expression itself is produced by the unchanged rendering helper from the datum
   and the chosen names; the operation's only responsibility is to pick that list
   of names correctly (mapping.md §2). -/
method asExpr (d : Int) (ringSymbols : List Int) (symbols : List Int)
    return (out : Except AsExprErr Int)
  ensures out = asExprSpec d ringSymbols symbols
  do
    -- impl-start
    -- Restructured but faithful: decide the chosen name list via a nested if
    -- with early returns; behaviorally identical to asExprSpec.
    if symbols.isEmpty then
      return Except.ok (exprFromDict d ringSymbols)
    if symbols.length = ringSymbols.length then
      return Except.ok (exprFromDict d symbols)
    return Except.error AsExprErr.wrongNumberOfSymbols
    -- impl-end

prove_correct asExpr by
  loom_solve <;> simp_all [asExprSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for velvet sympy__sympy-24539. gold worktree Env: source activate.

SPEC SHAPE: `method asExpr` has `ensures out = asExprSpec d ringSymbols symbols`, a TOTAL functional pin. asExprSpec: symbols.isEmpty -> ok(exprFromDict d ringSymbols); else length=ringSymbols.length -> ok(exprFromDict d symbols); else error .wrongNumberOfSymbols. exprFromDict is opaque with NO ensures (A-reference). Because the postcondition equates the returned value to the full spec expression (with opaque but injective-observable exprFromDict — G-AX establishes uses-gens), every behaviorally-distinct impl is refuted by prove_correct.

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec, verified; impl region only edited). Each verified with `bash scripts/lean_verify.sh <f>` run concurrently (batches of 4 then 3):
- atk_1 (prepatch bug / control-flow-effect): non-empty wrong-len rejected, ELSE overwrites chosen:=ringSymbols on every non-rejected path incl. correctly-sized. -> exit 1, error 'unsolved goals' at impl line (goal exprFromDict d ringSymbols = exprFromDict d symbols under ¬symbols=[]). PREPATCH REPRODUCED.
- atk_2 (boundary): honors any non-empty list with length <= ngens instead of == ngens. -> exit 1 unsolved goals.
- atk_3 (ungrounded-oracle echo): always `ok (exprFromDict d symbols)`, ignores empty/length. -> exit 1 unsolved goals.
- atk_4 (swapped branches): empty->symbols, matched-length->ringSymbols. -> exit 1 unsolved goals.
- atk_5 (partial-domain): treats empty list as error instead of using ring names. -> exit 1 unsolved goals.
- atk_6 (drop length check): honors ANY non-empty list, never rejects wrong-length. -> exit 1 unsolved goals.
All six FAIL to verify — the spec is tight; NO verifying wrong impl exists, so there is no verifying-wrong-impl faithful patch to run (patches={}).

POSITIVE CONTROL atk_7 (restructured-but-faithful, nested-if early-return, behaviorally == asExprSpec): same_spec=True, lean_verify exit 0 (VERIFIES, no sorry). Its faithful patch is the gold patch.diff (verbatim). RESOLVE RUN via swebench_unified.harness.run_resolve('sympy__sympy-24539', patch.diff): RESOLVED=True, completed=True, attempts=1, flaky=False, note='resolved'. So the sole verifying impl corresponds to a resolving patch (verify => resolved holds).

REFINEMENT.MD AUDIT: legs A1-A3 = R (datum/symbol-tuple <-> Int/List Int; only .length + list identity observed) — sound. A4-A6 = I (post-patch rings.py:618-624 3-way selection == asExprSpec, confirmed against sympy/polys/rings.py:617-626). A7 = A-reference + I: real expr_from_dict(rep,*gens) at polyutils.py:375 renders via `for g,m in zip(gens,monom)` -> deterministic pure fn that genuinely USES gens, UNCHANGED by patch, modeled opaque no-ensures; correspondence holds. No kind-3 (inexpressible-changed-op) legs; no consumed axiom over-claimed (directive 7 respected: the CHANGED op — honoring a correctly-sized caller list — is modeled directly as I legs over the A-reference callee, not hidden behind an axiom). G-AX obligations (determinism, uses-gens observability, unchanged default branch, wrong-length rejection at base_commit) are the correct scope; the discriminator (correctly-sized list honored) is correctly deferred to G-CONF/G-DIFF/G-GOLD.

CONCLUSION: >=6 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, swapped, dropped-check) + prepatch bug all encoded and verified; NONE verifies against the frozen spec. The one verifying impl resolves under the official harness. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_7.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The conversion that renders a sparse multivariate datum (a map from monomials
   to ground coefficients) into a symbolic expression over a GIVEN ordered list
   of generator names. An UNCHANGED helper the operation delegates to: modeled as
   an uninterpreted function because the operation never inspects the expression
   it produces — its only responsibility is to decide WHICH list of generator
   names to hand over, so no contract is owed about the rendered value
   (directive 7). The datum, each generator name, and the produced expression are
   opaque handles (`Int`); the bijection to the repository value space is in
   mapping.md (G-AX / G-CONF use it). Provenance + executable soundness check:
   mapping.md §3 / axiom_check.py (G-AX). -/
opaque exprFromDict : Int → List Int → Int
-- axioms-end

-- pure-start
/- The only failure the desired behavior distinguishes: a caller-supplied list of
   generator names whose length does not match the number of generators the datum
   lives over. -/
inductive AsExprErr where
  | wrongNumberOfSymbols
  deriving DecidableEq

/- The intended outcome of rendering the datum `d` over an optional caller list of
   generator names `symbols`, given the datum's own ordered generator names
   `ringSymbols` (whose length is the number of generators):

     * if the caller supplies NO names, render over the datum's own names;
     * otherwise, if the supplied list has exactly one name per generator, render
       over the SUPPLIED names (they are honored, not discarded);
     * otherwise the request is rejected.

   Honoring a correctly-sized caller list is the behavior the public problem
   statement requires. -/
def asExprSpec (d : Int) (ringSymbols : List Int) (symbols : List Int) :
    Except AsExprErr Int :=
  if symbols.isEmpty then
    Except.ok (exprFromDict d ringSymbols)
  else
    if symbols.length = ringSymbols.length then
      Except.ok (exprFromDict d symbols)
    else
      Except.error AsExprErr.wrongNumberOfSymbols
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a sparse multivariate datum as a symbolic expression, letting the caller
   choose the generator names.

   `d` is the datum (a map from monomials to ground coefficients) and `ringSymbols`
   are the datum's own ordered generator names — both read-only, so neither is
   `mut`. `symbols` is the caller's optional list of names. Desired behavior: when
   the caller supplies a list whose length equals the number of generators
   (`ringSymbols.length`), the expression must be rendered over the caller's names;
   when the caller supplies nothing, the datum's own names are used; when the
   caller supplies a list of any other length, the request is rejected. The
   expression itself is produced by the unchanged rendering helper from the datum
   and the chosen names; the operation's only responsibility is to pick that list
   of names correctly (mapping.md §2). -/
method asExpr (d : Int) (ringSymbols : List Int) (symbols : List Int)
    return (out : Except AsExprErr Int)
  ensures out = asExprSpec d ringSymbols symbols
  do
    -- impl-start
    -- Restructured but faithful: decide the chosen name list via a nested if
    -- with early returns; behaviorally identical to asExprSpec.
    if symbols.isEmpty then
      return Except.ok (exprFromDict d ringSymbols)
    if symbols.length = ringSymbols.length then
      return Except.ok (exprFromDict d symbols)
    return Except.error AsExprErr.wrongNumberOfSymbols
    -- impl-end

prove_correct asExpr by
  loom_solve <;> simp_all [asExprSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for velvet sympy__sympy-24539. gold worktree Env: source activate.

SPEC SHAPE: `method asExpr` has `ensures out = asExprSpec d ringSymbols symbols`, a TOTAL functional pin. asExprSpec: symbols.isEmpty -> ok(exprFromDict d ringSymbols); else length=ringSymbols.length -> ok(exprFromDict d symbols); else error .wrongNumberOfSymbols. exprFromDict is opaque with NO ensures (A-reference). Because the postcondition equates the returned value to the full spec expression (with opaque but injective-observable exprFromDict — G-AX establishes uses-gens), every behaviorally-distinct impl is refuted by prove_correct.

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec, verified; impl region only edited). Each verified with `bash scripts/lean_verify.sh <f>` run concurrently (batches of 4 then 3):
- atk_1 (prepatch bug / control-flow-effect): non-empty wrong-len rejected, ELSE overwrites chosen:=ringSymbols on every non-rejected path incl. correctly-sized. -> exit 1, error 'unsolved goals' at impl line (goal exprFromDict d ringSymbols = exprFromDict d symbols under ¬symbols=[]). PREPATCH REPRODUCED.
- atk_2 (boundary): honors any non-empty list with length <= ngens instead of == ngens. -> exit 1 unsolved goals.
- atk_3 (ungrounded-oracle echo): always `ok (exprFromDict d symbols)`, ignores empty/length. -> exit 1 unsolved goals.
- atk_4 (swapped branches): empty->symbols, matched-length->ringSymbols. -> exit 1 unsolved goals.
- atk_5 (partial-domain): treats empty list as error instead of using ring names. -> exit 1 unsolved goals.
- atk_6 (drop length check): honors ANY non-empty list, never rejects wrong-length. -> exit 1 unsolved goals.
All six FAIL to verify — the spec is tight; NO verifying wrong impl exists, so there is no verifying-wrong-impl faithful patch to run (patches={}).

POSITIVE CONTROL atk_7 (restructured-but-faithful, nested-if early-return, behaviorally == asExprSpec): same_spec=True, lean_verify exit 0 (VERIFIES, no sorry). Its faithful patch is the gold patch.diff (verbatim). RESOLVE RUN via swebench_unified.harness.run_resolve('sympy__sympy-24539', patch.diff): RESOLVED=True, completed=True, attempts=1, flaky=False, note='resolved'. So the sole verifying impl corresponds to a resolving patch (verify => resolved holds).

REFINEMENT.MD AUDIT: legs A1-A3 = R (datum/symbol-tuple <-> Int/List Int; only .length + list identity observed) — sound. A4-A6 = I (post-patch rings.py:618-624 3-way selection == asExprSpec, confirmed against sympy/polys/rings.py:617-626). A7 = A-reference + I: real expr_from_dict(rep,*gens) at polyutils.py:375 renders via `for g,m in zip(gens,monom)` -> deterministic pure fn that genuinely USES gens, UNCHANGED by patch, modeled opaque no-ensures; correspondence holds. No kind-3 (inexpressible-changed-op) legs; no consumed axiom over-claimed (directive 7 respected: the CHANGED op — honoring a correctly-sized caller list — is modeled directly as I legs over the A-reference callee, not hidden behind an axiom). G-AX obligations (determinism, uses-gens observability, unchanged default branch, wrong-length rejection at base_commit) are the correct scope; the discriminator (correctly-sized list honored) is correctly deferred to G-CONF/G-DIFF/G-GOLD.

CONCLUSION: >=6 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, swapped, dropped-check) + prepatch bug all encoded and verified; NONE verifies against the frozen spec. The one verifying impl resolves under the official harness. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True). asExprSpec faithfully models the real patched PolyElement.as_expr: (1) empty symbols -> own names [matches expr_from_dict(datum,*ring.symbols)]; (2) non-empty len==ngens -> supplied names HONORED and forwarded verbatim [f.as_expr(a,b,c)==expr_from_dict(datum,a,b,c), confirmed]; (3) non-empty wrong length -> Except.error <-> real ValueError('Wrong number of symbols...'). Modeling invariant ringSymbols.length==ngens holds in the real repo (R.ngens==len(R.symbols)), so the two-list encoding creates no unreachable/over-strong states. opaque exprFromDict carries NO ensures, so the spec asserts nothing about the rendered Expr beyond it being a pure fn of (datum, chosen list) that is forwarded verbatim — exactly the unchanged real callee's behavior (axiom_check confirms determinism + uses-gens at base_commit). Conformance_check.py run against the real patched repo: 100038 fuzzed inputs (seed 24539, rings ngens 1..4, boundary + random length draws) -> 0 disagreements, exit 0. No diverging input exists; spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Velvet sympy__sympy-24539. same_spec(Solution.lean, Solution_prepatch.lean, lean)=True (byte-identical spec region; prepatch differs only in elided impl). The consumer spec view formalizes exactly the behavior the PUBLIC problem_statement already specifies: the problem_statement names PolyElement.as_expr(), states that a correctly-sized caller symbol list is currently ignored in favor of self.ring.symbols, and asks that supplied symbols be honored. asExprSpec's three-branch selection (empty->ringSymbols; matching length->supplied symbols; else->reject) is a faithful encoding of that publicly-stated desired behavior — a spec is obligated to encode it, and it discloses nothing edit-localizing beyond the problem_statement. Gold-edit specifics live only in the auditor docs (refinement.md/mapping.md), NOT the spec view: the new message text ('Wrong number of symbols'), the old text ('not enough symbols'), the %s format, the if/elif control-flow restructuring, and the repo symbols (rings.py, expr_from_dict, as_expr_dict, ngens, raise ValueError) are all ABSENT from the spec view. Lexical screen confirms: leakage.screen(...) passed=True, hard_failures=[], warnings=[]; no diff markers, no patched file path, no bug/fix narration. meta G-LEAK=pass 'spec view clean'; no RELAXED_LEAKAGE.md and relaxed_leakage unset, so no deferral needed. No gold reconstruction possible from the spec view beyond what problem_statement already reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
