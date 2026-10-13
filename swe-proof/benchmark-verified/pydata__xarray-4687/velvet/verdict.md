# P2 adversarial audit — pydata__xarray-4687

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,11 +88,8 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
-    let resolved : Bool := keepAttributes.getD globalKeepDefault
-    let attrsOut : List (String × String) := if resolved then xAttrs else []
+
+    let attrsOut : List (String × String) := []
     return { values := whereSelect cond x y, attrs := attrsOut }
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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,11 +88,8 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
-    let resolved : Bool := keepAttributes.getD globalKeepDefault
-    let attrsOut : List (String × String) := if resolved then xAttrs else []
+
+    let attrsOut : List (String × String) := xAttrs
     return { values := whereSelect cond x y, attrs := attrsOut }
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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,11 +88,9 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
+
     let resolved : Bool := keepAttributes.getD globalKeepDefault
-    let attrsOut : List (String × String) := if resolved then xAttrs else []
+    let attrsOut : List (String × String) := if resolved then [] else xAttrs
     return { values := whereSelect cond x y, attrs := attrsOut }
     -- impl-end
 
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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,10 +88,8 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
-    let resolved : Bool := keepAttributes.getD globalKeepDefault
+
+    let resolved : Bool := keepAttributes.getD true
     let attrsOut : List (String × String) := if resolved then xAttrs else []
     return { values := whereSelect cond x y, attrs := attrsOut }
     -- impl-end
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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,10 +88,8 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
-    let resolved : Bool := keepAttributes.getD globalKeepDefault
+
+    let resolved : Bool := keepAttributes.getD false
     let attrsOut : List (String × String) := if resolved then xAttrs else []
     return { values := whereSelect cond x y, attrs := attrsOut }
     -- impl-end
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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,10 +88,8 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
-    let resolved : Bool := keepAttributes.getD globalKeepDefault
+
+    let resolved : Bool := globalKeepDefault
     let attrsOut : List (String × String) := if resolved then xAttrs else []
     return { values := whereSelect cond x y, attrs := attrsOut }
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,12 +88,10 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
+
     let resolved : Bool := keepAttributes.getD globalKeepDefault
     let attrsOut : List (String × String) := if resolved then xAttrs else []
-    return { values := whereSelect cond x y, attrs := attrsOut }
+    return { values := whereSelect cond y x, attrs := attrsOut }
     -- impl-end
 
 prove_correct selectByCondition by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,12 +88,10 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
+
     let resolved : Bool := keepAttributes.getD globalKeepDefault
     let attrsOut : List (String × String) := if resolved then xAttrs else []
-    return { values := whereSelect cond x y, attrs := attrsOut }
+    return { values := x, attrs := attrsOut }
     -- impl-end
 
 prove_correct selectByCondition by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,12 +88,13 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
+
     let resolved : Bool := keepAttributes.getD globalKeepDefault
     let attrsOut : List (String × String) := if resolved then xAttrs else []
-    return { values := whereSelect cond x y, attrs := attrsOut }
+    let vals : List Int := match cond with
+      | [] => [0]
+      | _  => whereSelect cond x y
+    return { values := vals, attrs := attrsOut }
     -- impl-end
 
 prove_correct selectByCondition by
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The elementwise value-selection performed here is an
@@ -88,11 +88,11 @@
                        then xAttrs else [])
   do
     -- impl-start
-    -- Resolve the keep choice: an explicit per-call choice stands; absent one,
-    -- the ambient default applies. Then keep the source attribute mapping iff
-    -- the resolved choice is to keep, otherwise expose no attributes.
-    let resolved : Bool := keepAttributes.getD globalKeepDefault
-    let attrsOut : List (String × String) := if resolved then xAttrs else []
+
+    let attrsOut : List (String × String) :=
+      match keepAttributes with
+      | some _ => []
+      | none   => if globalKeepDefault then xAttrs else []
     return { values := whereSelect cond x y, attrs := attrsOut }
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The elementwise value-selection performed here is an
--  unchanged library primitive, modeled DEEPLY in the `pure` region as the
--  front-recursive `whereSelect` (an A-reference, validated == the real numeric
--  primitive by axiom_check.py / G-AX), NOT consumed as an axiom. The decision
--  that governs whether the source attribute mapping is carried onto the result
--  is a closed function of two booleans (the per-call choice and the ambient
--  default), modeled directly below; nothing is consumed as an axiom. The
--  ambient default is the result of an unchanged option query, modeled as the
--  boolean input `globalKeepDefault` (an R refinement; cross-language soundness
--  is checked by conformance_check.py / G-CONF).)
-- axioms-end

-- pure-start
/- The elementwise selection: at each cell, take the value from the first
   operand list where the condition holds, otherwise from the second. Defined
   front-recursively over the three aligned cell lists (one unfold per cell).
   This is the unchanged primitive the routine delegates value computation to. -/
def whereSelect : List Bool → List Int → List Int → List Int
  | [],      _,       _       => []
  | _,       [],      _       => []
  | _,       _,       []      => []
  | c :: cs, a :: xs, b :: ys => (if c then a else b) :: whereSelect cs xs ys

@[grind] lemma whereSelect_nil_l (x y : List Int) : whereSelect [] x y = [] := by
  simp [whereSelect]
@[grind] lemma whereSelect_cons (c : Bool) (cs : List Bool)
    (a : Int) (xs : List Int) (b : Int) (ys : List Int) :
    whereSelect (c :: cs) (a :: xs) (b :: ys)
      = (if c then a else b) :: whereSelect cs xs ys := by
  simp [whereSelect]

/- The result carrier: the selected cell values together with the attribute
   mapping the result exposes (an association list; an empty list means no
   attributes). Only the touched fields of the real result object are modeled
   (mapping.md §2). -/
structure WhereResult where
  values : List Int
  attrs  : List (String × String)
deriving Inhabited, DecidableEq

/- The resolved choice of whether the result keeps the source attribute mapping.
   When the call states an explicit choice, that choice stands; when it states
   none, the ambient default applies. -/
@[grind] def keepResolved (choice : Option Bool) (default : Bool) : Bool :=
  choice.getD default
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine two operands cell-by-cell under a boolean condition, returning, for
   each cell, the first operand's value where the condition holds and the second
   operand's value elsewhere, and choosing whether the result carries over the
   attribute mapping of the first selected-from operand.

   Whether the attribute mapping is carried over is decided by the resolved
   choice: an explicit per-call choice stands as given; absent one, an ambient
   default applies. When the resolved choice is to keep, the result exposes the
   attribute mapping of the first selected-from operand (`xAttrs`); otherwise the
   result exposes no attributes (the empty mapping). The cell values do not
   depend on that choice.

   Every input is read-only (none `mut`): the routine reads the condition, the
   two operands, the source attribute mapping and the two flags, and constructs a
   fresh result; it mutates none of them (directive 5). `cond`, `x`, `y` are
   aligned cell lists (equal length). -/
method selectByCondition
    (cond : List Bool) (x : List Int) (y : List Int)
    (xAttrs : List (String × String))
    (keepAttributes : Option Bool) (globalKeepDefault : Bool)
    return (out : WhereResult)
  require cond.length = x.length
  require x.length = y.length
  ensures out.values = whereSelect cond x y
  ensures out.attrs = (if keepResolved keepAttributes globalKeepDefault
                       then xAttrs else [])
  do
    -- impl-start

    let resolved : Bool :=
      match keepAttributes with
      | some b => b
      | none   => globalKeepDefault
    let attrsOut : List (String × String) :=
      if resolved = true then xAttrs else []
    return { values := whereSelect cond x y, attrs := attrsOut }
    -- impl-end

prove_correct selectByCondition by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec pins BOTH output fields via two ensures clauses: out.values = whereSelect cond x y AND out.attrs = if keepResolved keepAttributes globalKeepDefault then xAttrs else []. A verifying impl therefore has zero behavioral freedom (verify => behaviorally identical to gold).

Same-spec confirmed True for all 10 attacks + control via swebench_unified.markers.same_spec (velvet). Verify cmd per file: `bash scripts/lean_verify.sh <file>`. Ran concurrently in batches of <=4.

### Results
- atk_1 (prepatch bug: attrs always []) exit=1, unsolved goal 'ensures_1: out.attrs' when flag truthy.
- atk_2 (attrs always xAttrs) exit=1, out.attrs fails when resolved=false.
- atk_3 (inverted: if resolved then [] else xAttrs) exit=1, out.attrs.
- atk_4 (getD true; None->keep, ignores globalKeepDefault) exit=1, out.attrs binds global on None.
- atk_5 (getD false; None->drop, ignores global) exit=1, out.attrs.
- atk_6 (resolved := globalKeepDefault; ignores explicit per-call choice) exit=1, out.attrs on some b != default.
- atk_7 (values := whereSelect cond y x; value leg swapped) exit=1, out.values.
- atk_8 (values := x; ignore cond, ungrounded value) exit=1, out.values.
- atk_9 (partial-domain: values=[0] on empty cond else whereSelect) exit=1, out.values on empty-cond boundary. (First encoding used return inside method-level match => parse error; rewritten as value-expr match, re-verified exit=1 genuine unsolved goals.)
- atk_10 (control-flow-effect: match keepAttributes, some _ => [] dropping attrs even for some true) exit=1, out.attrs.
- prepatch.lean (real Solution_prepatch.lean, same_spec True) exit=1, unsolved 'ensures_1: out.attrs' — same discriminating clause, reproduced.
- atk_ctrl (structurally-different CORRECT: Option match + `= true` guard) exit=0 verifies => spec non-vacuous.

Step 2 (materialize faithful patch + run_resolve) is VACUOUSLY satisfied: NO wrong impl verified, so there is no verifying-wrong-impl whose patch could fail to resolve. patches={} accordingly.

A-leg / refinement.md audit: Op 1 `whereSelect` is the only A row and is an A-REFERENCE (deep model), not a consumed axiom (axioms region declares none). Correspondence to real callee holds: front-recursive elementwise cond?x:y == np.where/duck_array_ops.where over equal-length int arrays (guaranteed by preconditions cond.length=x.length=y.length); G-AX/axiom_check.py fuzzes 8 boundary + 20000 equal-length arrays. Ops 2,3 = R (Option Bool<->None/True/False; getD models None->globalKeepDefault resolution; G-CONF differential-tests vs gold-patched xr.where), Op 4 = I (record construction). No kind-3 leg. Both output components pinned; no output left unconstrained.

Verdict SOUND: >=5 distinct verifying wrong-impl classes attempted (partial-domain #9, boundary/value #7/#8, control-flow-effect #10, resolution-logic #3/#4/#5/#6, ungrounded #2, prepatch #1); NONE verified, so none breaks the spec. Correct control verifies. A-legs sound.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The elementwise value-selection performed here is an
--  unchanged library primitive, modeled DEEPLY in the `pure` region as the
--  front-recursive `whereSelect` (an A-reference, validated == the real numeric
--  primitive by axiom_check.py / G-AX), NOT consumed as an axiom. The decision
--  that governs whether the source attribute mapping is carried onto the result
--  is a closed function of two booleans (the per-call choice and the ambient
--  default), modeled directly below; nothing is consumed as an axiom. The
--  ambient default is the result of an unchanged option query, modeled as the
--  boolean input `globalKeepDefault` (an R refinement; cross-language soundness
--  is checked by conformance_check.py / G-CONF).)
-- axioms-end

-- pure-start
/- The elementwise selection: at each cell, take the value from the first
   operand list where the condition holds, otherwise from the second. Defined
   front-recursively over the three aligned cell lists (one unfold per cell).
   This is the unchanged primitive the routine delegates value computation to. -/
def whereSelect : List Bool → List Int → List Int → List Int
  | [],      _,       _       => []
  | _,       [],      _       => []
  | _,       _,       []      => []
  | c :: cs, a :: xs, b :: ys => (if c then a else b) :: whereSelect cs xs ys

@[grind] lemma whereSelect_nil_l (x y : List Int) : whereSelect [] x y = [] := by
  simp [whereSelect]
@[grind] lemma whereSelect_cons (c : Bool) (cs : List Bool)
    (a : Int) (xs : List Int) (b : Int) (ys : List Int) :
    whereSelect (c :: cs) (a :: xs) (b :: ys)
      = (if c then a else b) :: whereSelect cs xs ys := by
  simp [whereSelect]

/- The result carrier: the selected cell values together with the attribute
   mapping the result exposes (an association list; an empty list means no
   attributes). Only the touched fields of the real result object are modeled
   (mapping.md §2). -/
structure WhereResult where
  values : List Int
  attrs  : List (String × String)
deriving Inhabited, DecidableEq

/- The resolved choice of whether the result keeps the source attribute mapping.
   When the call states an explicit choice, that choice stands; when it states
   none, the ambient default applies. -/
@[grind] def keepResolved (choice : Option Bool) (default : Bool) : Bool :=
  choice.getD default
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine two operands cell-by-cell under a boolean condition, returning, for
   each cell, the first operand's value where the condition holds and the second
   operand's value elsewhere, and choosing whether the result carries over the
   attribute mapping of the first selected-from operand.

   Whether the attribute mapping is carried over is decided by the resolved
   choice: an explicit per-call choice stands as given; absent one, an ambient
   default applies. When the resolved choice is to keep, the result exposes the
   attribute mapping of the first selected-from operand (`xAttrs`); otherwise the
   result exposes no attributes (the empty mapping). The cell values do not
   depend on that choice.

   Every input is read-only (none `mut`): the routine reads the condition, the
   two operands, the source attribute mapping and the two flags, and constructs a
   fresh result; it mutates none of them (directive 5). `cond`, `x`, `y` are
   aligned cell lists (equal length). -/
method selectByCondition
    (cond : List Bool) (x : List Int) (y : List Int)
    (xAttrs : List (String × String))
    (keepAttributes : Option Bool) (globalKeepDefault : Bool)
    return (out : WhereResult)
  require cond.length = x.length
  require x.length = y.length
  ensures out.values = whereSelect cond x y
  ensures out.attrs = (if keepResolved keepAttributes globalKeepDefault
                       then xAttrs else [])
  do
    -- impl-start

    let resolved : Bool :=
      match keepAttributes with
      | some b => b
      | none   => globalKeepDefault
    let attrsOut : List (String × String) :=
      if resolved = true then xAttrs else []
    return { values := whereSelect cond x y, attrs := attrsOut }
    -- impl-end

prove_correct selectByCondition by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec pins BOTH output fields via two ensures clauses: out.values = whereSelect cond x y AND out.attrs = if keepResolved keepAttributes globalKeepDefault then xAttrs else []. A verifying impl therefore has zero behavioral freedom (verify => behaviorally identical to gold).

Same-spec confirmed True for all 10 attacks + control via swebench_unified.markers.same_spec (velvet). Verify cmd per file: `bash scripts/lean_verify.sh <file>`. Ran concurrently in batches of <=4.

### Results
- atk_1 (prepatch bug: attrs always []) exit=1, unsolved goal 'ensures_1: out.attrs' when flag truthy.
- atk_2 (attrs always xAttrs) exit=1, out.attrs fails when resolved=false.
- atk_3 (inverted: if resolved then [] else xAttrs) exit=1, out.attrs.
- atk_4 (getD true; None->keep, ignores globalKeepDefault) exit=1, out.attrs binds global on None.
- atk_5 (getD false; None->drop, ignores global) exit=1, out.attrs.
- atk_6 (resolved := globalKeepDefault; ignores explicit per-call choice) exit=1, out.attrs on some b != default.
- atk_7 (values := whereSelect cond y x; value leg swapped) exit=1, out.values.
- atk_8 (values := x; ignore cond, ungrounded value) exit=1, out.values.
- atk_9 (partial-domain: values=[0] on empty cond else whereSelect) exit=1, out.values on empty-cond boundary. (First encoding used return inside method-level match => parse error; rewritten as value-expr match, re-verified exit=1 genuine unsolved goals.)
- atk_10 (control-flow-effect: match keepAttributes, some _ => [] dropping attrs even for some true) exit=1, out.attrs.
- prepatch.lean (real Solution_prepatch.lean, same_spec True) exit=1, unsolved 'ensures_1: out.attrs' — same discriminating clause, reproduced.
- atk_ctrl (structurally-different CORRECT: Option match + `= true` guard) exit=0 verifies => spec non-vacuous.

Step 2 (materialize faithful patch + run_resolve) is VACUOUSLY satisfied: NO wrong impl verified, so there is no verifying-wrong-impl whose patch could fail to resolve. patches={} accordingly.

A-leg / refinement.md audit: Op 1 `whereSelect` is the only A row and is an A-REFERENCE (deep model), not a consumed axiom (axioms region declares none). Correspondence to real callee holds: front-recursive elementwise cond?x:y == np.where/duck_array_ops.where over equal-length int arrays (guaranteed by preconditions cond.length=x.length=y.length); G-AX/axiom_check.py fuzzes 8 boundary + 20000 equal-length arrays. Ops 2,3 = R (Option Bool<->None/True/False; getD models None->globalKeepDefault resolution; G-CONF differential-tests vs gold-patched xr.where), Op 4 = I (record construction). No kind-3 leg. Both output components pinned; no output left unconstrained.

Verdict SOUND: >=5 distinct verifying wrong-impl classes attempted (partial-domain #9, boundary/value #7/#8, control-flow-effect #10, resolution-logic #3/#4/#5/#6, ungrounded #2, prepatch #1); NONE verified, so none breaks the spec. Correct control verifies. A-legs sound.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) on velvet pydata__xarray-4687, modeling xarray.core.computation.where at base_commit d3b6aa6. RESULT: FAITHFUL — spec agrees with the real callee everywhere on the modeled domain.

Setup: checked out xarray_src @ base_commit, applied the gold patch (adds keep_attrs param), imported patched xr.where. Compared the Lean spec's two ensures clauses against the real patched callee.

Spec: out.values = whereSelect cond x y; out.attrs = if keepAttributes.getD globalKeepDefault then xAttrs else [].

Checks:
- same_spec(Solution, Solution_prepatch, velvet.language) = True (spec region byte-identical).
- lean_verify Solution.lean exit 0; prepatch (attrs:=[] always) fails with unsolved goal on the attrs ensures — spec genuinely bites.
- Value leg: whereSelect == elementwise np.where on equal-length int lists.
- Attrs leg: 200k fuzzed inputs (None/True/False × {}/{attr:x}/{a,b} × random int arrays k=0..24) — 0 disagreements with the gold-patched oracle.
- CRITICAL EDGE PROBED: conformance_check.py deliberately SKIPS the attrs comparison when len(cond)==0 (comment claims merge_attrs returns None for all-empty operand stack). I did NOT skip it. At this base_commit (xarray 0.15.1) the real xr.where on empty arrays with keep_attrs=True + non-empty x.attrs returns {'attr':'x'} — which AGREES with the spec (out.attrs = xAttrs). So the spec is NOT too strong on the empty case; the conformance skip was over-cautious but harmless, not evidence of drift.
- globalKeepDefault=True path (only reachable via keep_attrs=None under global option keep_attrs=True; conformance always uses default False): swept both empty and non-empty — matches spec.

Declared modeling boundaries (mapping.md), not drift: equal-length precondition (require cond.length=x.length=y.length), 1-D lists only (broadcasting owned by unchanged callee), Int cell values (select is identity/order, never arithmetic). Within that domain the modeled function does not disagree with the real callee on any input I could construct.

No diverging input found. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen, velvet/lean flavor) passes with zero hard failures; spec region byte-identical to prepatch (same_spec=True). Only patched symbol is 'where', already public via the problem_statement ('xr.where'). Spec-view identifiers are all abstracted (selectByCondition, whereSelect, keepAttributes, globalKeepDefault, keepResolved, xAttrs) — none names a patched repo symbol beyond the public 'where'. No gold-edit specifics appear anywhere in the view: no _get_keep_attrs, no apply_ufunc, no keep_attrs= kwarg forwarding, no 'lambda attrs, context: attrs[1]', no merge_attrs/combine_attrs, no xarray/core/computation.py path, no diff markers, no bug/fix narration. The public problem_statement already discloses (a) xr.where drops attrs, (b) attrs should be preservable, and (c) the proposed fix is to add a keep_attrs choice/pass keep_attrs=True to apply_ufunc. The spec's post-conditions (out.attrs = if keepResolved keepAttributes globalKeepDefault then xAttrs else []) encode the required behavior (a legitimate spec obligation), not the Python patch mechanism, and are stated in abstract behavioral prose ('explicit per-call choice stands; absent one an ambient default applies'). The gold diff is not reconstructible from the view beyond what the task already makes public. No leaking line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
