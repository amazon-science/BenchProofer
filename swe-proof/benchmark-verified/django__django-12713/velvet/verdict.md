# P2 adversarial audit — django__django-12713

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec impl verifies while being wrong. All 7 distinct terminating wrong-value impls (prepatch overwrite, default-first swap, drop-default, drop-caller, constant-none echo, swapped guard polarity, boundary flip) are rejected by the single ensures clause `out = (if provided.isNone then computedDefault else provided)`. The only same-spec impls that verify are vacuous divergence (while true / done_with False) which have NO faithful refined patch and are excluded (see notes).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The only behaviour modeled here is the precedence
@@ -47,10 +47,8 @@
   ensures out = (if provided.isNone then computedDefault else provided)
   do
     -- impl-start
-    -- Start from the caller's choice; only when the caller supplied no widget do
-    -- we fall back to the default computed from the field.
     let mut widget := provided
-    if widget.isNone then
+    if computedDefault.isSome then
       widget := computedDefault
     return widget
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
 -- (No axiomatized callees. The only behaviour modeled here is the precedence
@@ -47,11 +47,9 @@
   ensures out = (if provided.isNone then computedDefault else provided)
   do
     -- impl-start
-    -- Start from the caller's choice; only when the caller supplied no widget do
-    -- we fall back to the default computed from the field.
-    let mut widget := provided
-    if widget.isNone then
-      widget := computedDefault
+    let mut widget := computedDefault
+    if provided.isNone then
+      widget := provided
     return widget
     -- impl-end
 
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
 -- (No axiomatized callees. The only behaviour modeled here is the precedence
@@ -47,12 +47,7 @@
   ensures out = (if provided.isNone then computedDefault else provided)
   do
     -- impl-start
-    -- Start from the caller's choice; only when the caller supplied no widget do
-    -- we fall back to the default computed from the field.
-    let mut widget := provided
-    if widget.isNone then
-      widget := computedDefault
-    return widget
+    return provided
     -- impl-end
 
 prove_correct resolveWidget by
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
 -- (No axiomatized callees. The only behaviour modeled here is the precedence
@@ -47,12 +47,7 @@
   ensures out = (if provided.isNone then computedDefault else provided)
   do
     -- impl-start
-    -- Start from the caller's choice; only when the caller supplied no widget do
-    -- we fall back to the default computed from the field.
-    let mut widget := provided
-    if widget.isNone then
-      widget := computedDefault
-    return widget
+    return computedDefault
     -- impl-end
 
 prove_correct resolveWidget by
```

Attack 5 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only behaviour modeled here is the precedence
@@ -47,12 +47,7 @@
   ensures out = (if provided.isNone then computedDefault else provided)
   do
     -- impl-start
-    -- Start from the caller's choice; only when the caller supplied no widget do
-    -- we fall back to the default computed from the field.
-    let mut widget := provided
-    if widget.isNone then
-      widget := computedDefault
-    return widget
+    return (none : Option Widget)
     -- impl-end
 
 prove_correct resolveWidget by
```

Attack 6 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only behaviour modeled here is the precedence
@@ -47,10 +47,8 @@
   ensures out = (if provided.isNone then computedDefault else provided)
   do
     -- impl-start
-    -- Start from the caller's choice; only when the caller supplied no widget do
-    -- we fall back to the default computed from the field.
     let mut widget := provided
-    if widget.isNone then
+    if widget.isSome then
       widget := computedDefault
     return widget
     -- impl-end
```

Attack 7 — `atk_11.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only behaviour modeled here is the precedence
@@ -47,11 +47,9 @@
   ensures out = (if provided.isNone then computedDefault else provided)
   do
     -- impl-start
-    -- Start from the caller's choice; only when the caller supplied no widget do
-    -- we fall back to the default computed from the field.
-    let mut widget := provided
-    if widget.isNone then
-      widget := computedDefault
+    let mut widget := computedDefault
+    if computedDefault.isNone then
+      widget := provided
     return widget
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only behaviour modeled here is the precedence
--  between a caller-supplied widget and a default widget computed from the input
--  field's characteristics. The computation of that default is UNCHANGED and is
--  taken as a FREE INPUT `computedDefault`, so the spec makes no behavioural
--  claim about how the default is derived and holds for every value of it (an R
--  abstraction, validated against the real default-selection chain by
--  conformance_check.py / G-CONF). Nothing is consumed as an axiom, hence no
--  G-AX. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An opaque widget identity. Only whether two widgets are the same object/kind
   is observable to the caller (the consumer compares the resolved widget to the
   one it supplied), so a tagged id is the faithful carrier. -/
structure Widget where
  id : Nat
deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve which widget to use for an input field.

   The caller may supply a widget explicitly (`provided` is `some`); when it
   does, that widget must be the one used. When the caller supplies none
   (`provided` is `none`), the widget is the default computed from the field's
   characteristics (`computedDefault`), which may itself be absent (`none`) when
   the field has no special default.

   Both inputs are read-only (neither `mut`): the routine inspects the supplied
   widget and the computed default and decides; it mutates neither (directive 5). -/
method resolveWidget (provided : Option Widget) (computedDefault : Option Widget)
    return (out : Option Widget)
  ensures out = (if provided.isNone then computedDefault else provided)
  do
    -- impl-start
    -- Start from the caller's choice; only when the caller supplied no widget do
    -- we fall back to the default computed from the field.
    let mut widget := provided
    if widget.isNone then
      widget := computedDefault
    return widget
    -- impl-end

prove_correct resolveWidget by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: method resolveWidget (provided computedDefault : Option Widget) return (out : Option Widget) ensures out = (if provided.isNone then computedDefault else provided). No axioms (meta.json axioms=[], deep_model_references=[]) => NO A-legs to audit; refinement is R/I only.

MACHINE RESULTS (scripts/lean_verify.sh, 300s; same_spec=True verified for every file via swebench_unified.markers.same_spec + get_backend('velvet')):
  positive_control (correct match-based impl, structurally different) -> exit 0 VERIFIES (spec non-vacuous).
  atk_1 prepatch bug, unconditional overwrite (== bundle Solution_prepatch impl region; diff confirms MATCH) -> exit 1 FAIL, goal `computedDefault = if provided.isNone ...` unprovable on provided=some,default=some,w!=d.
  atk_2 default-first swap -> exit 1 FAIL.
  atk_3 return provided (drop default) -> exit 1 FAIL (none-branch).
  atk_4 return computedDefault (drop caller) -> exit 1 FAIL.
  atk_9 constant none (ungrounded-oracle echo) -> exit 1 FAIL.
  atk_10 swapped guard polarity (apply default when provided.isSome) -> exit 1 FAIL.
  atk_11 boundary flip on computedDefault.isNone -> exit 1 FAIL.
All 7 terminating wrong-value attacks REJECTED; none is a candidate, so no resolve run was required. prepatch_reproduced=True (atk_1 is byte-identical to the bundle's Solution_prepatch impl region and fails on the discriminating F2P clause).

DIVERGENCE CLASS (reported for transparency; intentionally NOT in the mechanized attacks list): atk_5 (diverge on F2P case, else correct), atk_6 (diverge when provided.isSome), atk_7 (diverge all inputs), atk_8 (wrong value + diverge all inputs) — each `while true invariant True done_with False` — all verify VACUOUSLY (exit 0, completely clean logs). This is NOT a verify=>correct break:

(1) NO FAITHFUL REFINED PATCH EXISTS — refinement.md maps every impl op to a patch.diff op (R/A/I); the gold patch/impl is straight-line and terminating, so a non-terminating loop corresponds to no op in patch.diff. The only materializable 'patch' is an UNFAITHFUL `while True: pass` injection, which is not a faithful refinement, so the BROKEN rule's precondition ('materialize its FAITHFUL refined patch and run it') is unsatisfiable.

(2) GENERIC not spec-specific — the bundle uses the board-wide default `set_option loom.semantics.termination "partial"` (present in 401 velvet bundles); under partial correctness a diverging impl vacuously satisfies ANY postcondition, so if it counted as a break no partial-correctness bundle could ever pass. Divergence is a shared assumption of the verification semantics, not a weakness of this ensures clause.

REFINEMENT AUDIT (protocol step 3) — SOUND: legs A1=R (kwargs.get('widget') <-> provided; 'widget' not in kwargs <-> provided.isNone), A2=R (unchanged autocomplete/raw_id/filter selection-chain net assignment folded into free input computedDefault, the django__django-11095 ORACLE-choice precedent), A3=I (the added `if 'widget' not in kwargs:` guard modeled deeply as `if provided.isNone then computedDefault else provided`). Every leg is R or I; NO kind-3; NO A-legs/axioms => no callee-correspondence to audit. Crux bijection provided.isNone <-> 'widget' not in kwargs is faithful (formfield_overrides always merges a concrete widget class, never a None value). model<->patch: the patch's sole behavioural change (widget precedence) is fully captured; queryset/help-text blocks are unchanged and correctly unmodeled.

VERDICT SOUND: positive control verifies; >=5 (7) distinct terminating wrong-value attacks all rejected; prepatch reproduced; the only verifying same-spec impls are vacuous divergence with no faithful refined patch (excluded, not a break); refinement R/I only, no kind-3, faithful. Full write-up at ANALYSIS.md.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec impl verifies while being wrong. All 7 distinct terminating wrong-value impls (prepatch overwrite, default-first swap, drop-default, drop-caller, constant-none echo, swapped guard polarity, boundary flip) are rejected by the single ensures clause `out = (if provided.isNone then computedDefault else provided)`. The only same-spec impls that verify are vacuous divergence (while true / done_with False) which have NO faithful refined patch and are excluded (see notes).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only behaviour modeled here is the precedence
--  between a caller-supplied widget and a default widget computed from the input
--  field's characteristics. The computation of that default is UNCHANGED and is
--  taken as a FREE INPUT `computedDefault`, so the spec makes no behavioural
--  claim about how the default is derived and holds for every value of it (an R
--  abstraction, validated against the real default-selection chain by
--  conformance_check.py / G-CONF). Nothing is consumed as an axiom, hence no
--  G-AX. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An opaque widget identity. Only whether two widgets are the same object/kind
   is observable to the caller (the consumer compares the resolved widget to the
   one it supplied), so a tagged id is the faithful carrier. -/
structure Widget where
  id : Nat
deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve which widget to use for an input field.

   The caller may supply a widget explicitly (`provided` is `some`); when it
   does, that widget must be the one used. When the caller supplies none
   (`provided` is `none`), the widget is the default computed from the field's
   characteristics (`computedDefault`), which may itself be absent (`none`) when
   the field has no special default.

   Both inputs are read-only (neither `mut`): the routine inspects the supplied
   widget and the computed default and decides; it mutates neither (directive 5). -/
method resolveWidget (provided : Option Widget) (computedDefault : Option Widget)
    return (out : Option Widget)
  ensures out = (if provided.isNone then computedDefault else provided)
  do
    -- impl-start
    -- Start from the caller's choice; only when the caller supplied no widget do
    -- we fall back to the default computed from the field.
    let mut widget := provided
    if widget.isNone then
      widget := computedDefault
    return widget
    -- impl-end

prove_correct resolveWidget by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: method resolveWidget (provided computedDefault : Option Widget) return (out : Option Widget) ensures out = (if provided.isNone then computedDefault else provided). No axioms (meta.json axioms=[], deep_model_references=[]) => NO A-legs to audit; refinement is R/I only.

MACHINE RESULTS (scripts/lean_verify.sh, 300s; same_spec=True verified for every file via swebench_unified.markers.same_spec + get_backend('velvet')):
  positive_control (correct match-based impl, structurally different) -> exit 0 VERIFIES (spec non-vacuous).
  atk_1 prepatch bug, unconditional overwrite (== bundle Solution_prepatch impl region; diff confirms MATCH) -> exit 1 FAIL, goal `computedDefault = if provided.isNone ...` unprovable on provided=some,default=some,w!=d.
  atk_2 default-first swap -> exit 1 FAIL.
  atk_3 return provided (drop default) -> exit 1 FAIL (none-branch).
  atk_4 return computedDefault (drop caller) -> exit 1 FAIL.
  atk_9 constant none (ungrounded-oracle echo) -> exit 1 FAIL.
  atk_10 swapped guard polarity (apply default when provided.isSome) -> exit 1 FAIL.
  atk_11 boundary flip on computedDefault.isNone -> exit 1 FAIL.
All 7 terminating wrong-value attacks REJECTED; none is a candidate, so no resolve run was required. prepatch_reproduced=True (atk_1 is byte-identical to the bundle's Solution_prepatch impl region and fails on the discriminating F2P clause).

DIVERGENCE CLASS (reported for transparency; intentionally NOT in the mechanized attacks list): atk_5 (diverge on F2P case, else correct), atk_6 (diverge when provided.isSome), atk_7 (diverge all inputs), atk_8 (wrong value + diverge all inputs) — each `while true invariant True done_with False` — all verify VACUOUSLY (exit 0, completely clean logs). This is NOT a verify=>correct break:

(1) NO FAITHFUL REFINED PATCH EXISTS — refinement.md maps every impl op to a patch.diff op (R/A/I); the gold patch/impl is straight-line and terminating, so a non-terminating loop corresponds to no op in patch.diff. The only materializable 'patch' is an UNFAITHFUL `while True: pass` injection, which is not a faithful refinement, so the BROKEN rule's precondition ('materialize its FAITHFUL refined patch and run it') is unsatisfiable.

(2) GENERIC not spec-specific — the bundle uses the board-wide default `set_option loom.semantics.termination "partial"` (present in 401 velvet bundles); under partial correctness a diverging impl vacuously satisfies ANY postcondition, so if it counted as a break no partial-correctness bundle could ever pass. Divergence is a shared assumption of the verification semantics, not a weakness of this ensures clause.

REFINEMENT AUDIT (protocol step 3) — SOUND: legs A1=R (kwargs.get('widget') <-> provided; 'widget' not in kwargs <-> provided.isNone), A2=R (unchanged autocomplete/raw_id/filter selection-chain net assignment folded into free input computedDefault, the django__django-11095 ORACLE-choice precedent), A3=I (the added `if 'widget' not in kwargs:` guard modeled deeply as `if provided.isNone then computedDefault else provided`). Every leg is R or I; NO kind-3; NO A-legs/axioms => no callee-correspondence to audit. Crux bijection provided.isNone <-> 'widget' not in kwargs is faithful (formfield_overrides always merges a concrete widget class, never a None value). model<->patch: the patch's sole behavioural change (widget precedence) is fully captured; queryset/help-text blocks are unchanged and correctly unmodeled.

VERDICT SOUND: positive control verifies; >=5 (7) distinct terminating wrong-value attacks all rejected; prepatch reproduced; the only verifying same-spec impls are vacuous divergence with no faithful refined patch (excluded, not a break); refinement R/I only, no kind-3, faithful. Full write-up at ANALYSIS.md.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-12713 velvet bundle.

Mechanical checks:
- Solution.lean verifies (lean_verify.sh exit 0, loom_solve closes prove_correct resolveWidget).
- Solution_prepatch.lean FAILS the same spec (exit 1, unsolved goals on both branches) — spec discriminates the pre-patch bug (G-DIFF sanity holds).
- same_spec(Solution, Solution_prepatch, velvet) == True: the spec region (axioms/pure/pre/post + method signature + `ensures`) is byte-identical; only the impl region differs. Genuine same-spec/different-impl setup.

Postcondition under review: out = (if provided.isNone then computedDefault else provided).

Real repo behavior at base_commit 5b884d45 (confirmed by reading django/contrib/admin/options.py:242 formfield_for_manytomany and gold patch.diff): the patch wraps the unchanged autocomplete/raw_id/filter selection chain in `if 'widget' not in kwargs:`. Resolved widget = kwargs['widget'] after the block.
  * 'widget' in kwargs  (provided = some w): chain skipped, kwargs['widget'] keeps caller's w  ==> matches `else provided`.
  * 'widget' not in kwargs (provided = none): chain runs, assigns computed default (some d) or leaves absent (none) ==> matches `then computedDefault`.

Type abstraction (mapping.md/refinement.md) is sound: provided <-> kwargs.get('widget') (none iff 'widget' not in kwargs); Widget = opaque tagged id (caller observes only identity/kind, consistent with F2P test comparing field.widget to supplied CheckboxSelectMultiple); computedDefault <-> the UNCHANGED selection chain's net assignment folded to a free input (R abstraction, django-11095 ORACLE-choice precedent — the chain is unchanged by the patch, so the spec makes no claim about its internals, correctly). No axioms, no deep-model refs (consistent with meta.json axioms=[], deep_model_references=[]).

The postcondition is an exact equality: for EVERY (provided, computedDefault) pair the modeled precedence function returns precisely what the patched code assigns. It is not too strong (resolveWidget verifies for all inputs, incl. provided=some & computedDefault=some & differing — the F2P case where caller must win) and not too weak (prepatch rejected exactly there). I could construct no input on which the modeled function disagrees with the real post-patch callee's widget resolution. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over velvet spec_view) passes: 0 hard failures, 0 warnings. same_spec(Solution.lean, Solution_prepatch.lean) = True (byte-identical spec region). Reviewed the spec view line-by-line against the PUBLIC problem_statement only (hints_text empty, excluded per policy):

- No diff markers (@@, +++, index, diff --git) in the spec view.
- No gold-patch changed line reproduced. The spec models everything abstractly as `Option Widget` / `provided` / `computedDefault`; none of the gold-specific tokens (`kwargs`, `'widget' not in kwargs`, `AutocompleteSelectMultiple`, `ManyToManyRawIdWidget`, `FilteredSelectMultiple`, `filter_vertical`/`filter_horizontal`, `raw_id_fields`) appear.
- Patched file path (django/contrib/admin/options.py) and dotted module path do not appear.
- Only changed symbol is `formfield_for_manytomany`, which is present VERBATIM in the public problem_statement -> exempt; it also does not appear in the spec view (renamed to abstract `resolveWidget`).
- No fix/bug/pre-patch/previously/incorrectly narration in any spec-view comment or docstring. The pre-patch-bug narration lives only in refinement.md/mapping.md (auditor docs, not the consumer spec view — outside G-LEAK's screened surface).

Judgment on semantic over-leak beyond the lexical screen: the postcondition `out = (if provided.isNone then computedDefault else provided)` encodes correct behavior (caller-supplied widget wins; default used only when none supplied). This is exactly what the PUBLIC issue already requests ('Allow overriding widget in formfield_for_manytomany()... It does not work when I set widget param... different from formfield_for_foreignkey()'). It reveals no mechanism of the gold edit (the kwargs-membership guard, the specific widget constructors, the file) beyond what the problem_statement already discloses. The edit specifics are folded into free inputs and never surface. No leakage of the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.