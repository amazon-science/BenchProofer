# P2 adversarial audit — astropy__astropy-14539

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-but-wrong impl whose faithful patch could fail to resolve.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- The distinguished failure that escapes the per-column comparison when the
@@ -171,16 +171,8 @@
   ensures out = diffSpec fmt col rows
   do
     -- impl-start
-    -- Classify the column by its format descriptor and route the comparison
-    -- accordingly: a column whose format carries a variable-length marker is
-    -- compared ROW BY ROW; every other column is compared by the generic
-    -- element-wise route. Each route produces the per-row difference verdict when
-    -- it can run on this column's element kind, and otherwise lets the failure
-    -- escape. With every variable-length column — and only those — routed
-    -- row-wise, each column is sent down a route its element kind supports, so
-    -- the comparison always completes.
     let result : Except DiffErr (List Bool) :=
-      if isVLA fmt then
+      if fmt.contains 'P' then
         rowWiseOutcome col rows
       else
         genericOutcome col rows
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
 /- The distinguished failure that escapes the per-column comparison when the
@@ -171,16 +171,8 @@
   ensures out = diffSpec fmt col rows
   do
     -- impl-start
-    -- Classify the column by its format descriptor and route the comparison
-    -- accordingly: a column whose format carries a variable-length marker is
-    -- compared ROW BY ROW; every other column is compared by the generic
-    -- element-wise route. Each route produces the per-row difference verdict when
-    -- it can run on this column's element kind, and otherwise lets the failure
-    -- escape. With every variable-length column — and only those — routed
-    -- row-wise, each column is sent down a route its element kind supports, so
-    -- the comparison always completes.
     let result : Except DiffErr (List Bool) :=
-      if isVLA fmt then
+      if fmt.contains 'Q' || fmt.contains 'P' then
         rowWiseOutcome col rows
       else
         genericOutcome col rows
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
 /- The distinguished failure that escapes the per-column comparison when the
@@ -171,20 +171,7 @@
   ensures out = diffSpec fmt col rows
   do
     -- impl-start
-    -- Classify the column by its format descriptor and route the comparison
-    -- accordingly: a column whose format carries a variable-length marker is
-    -- compared ROW BY ROW; every other column is compared by the generic
-    -- element-wise route. Each route produces the per-row difference verdict when
-    -- it can run on this column's element kind, and otherwise lets the failure
-    -- escape. With every variable-length column — and only those — routed
-    -- row-wise, each column is sent down a route its element kind supports, so
-    -- the comparison always completes.
-    let result : Except DiffErr (List Bool) :=
-      if isVLA fmt then
-        rowWiseOutcome col rows
-      else
-        genericOutcome col rows
-    return result
+    return rowWiseOutcome col rows
     -- impl-end
 
 prove_correct diffVLAColumn by
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
 /- The distinguished failure that escapes the per-column comparison when the
@@ -171,20 +171,7 @@
   ensures out = diffSpec fmt col rows
   do
     -- impl-start
-    -- Classify the column by its format descriptor and route the comparison
-    -- accordingly: a column whose format carries a variable-length marker is
-    -- compared ROW BY ROW; every other column is compared by the generic
-    -- element-wise route. Each route produces the per-row difference verdict when
-    -- it can run on this column's element kind, and otherwise lets the failure
-    -- escape. With every variable-length column — and only those — routed
-    -- row-wise, each column is sent down a route its element kind supports, so
-    -- the comparison always completes.
-    let result : Except DiffErr (List Bool) :=
-      if isVLA fmt then
-        rowWiseOutcome col rows
-      else
-        genericOutcome col rows
-    return result
+    return genericOutcome col rows
     -- impl-end
 
 prove_correct diffVLAColumn by
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
 /- The distinguished failure that escapes the per-column comparison when the
@@ -171,16 +171,8 @@
   ensures out = diffSpec fmt col rows
   do
     -- impl-start
-    -- Classify the column by its format descriptor and route the comparison
-    -- accordingly: a column whose format carries a variable-length marker is
-    -- compared ROW BY ROW; every other column is compared by the generic
-    -- element-wise route. Each route produces the per-row difference verdict when
-    -- it can run on this column's element kind, and otherwise lets the failure
-    -- escape. With every variable-length column — and only those — routed
-    -- row-wise, each column is sent down a route its element kind supports, so
-    -- the comparison always completes.
     let result : Except DiffErr (List Bool) :=
-      if isVLA fmt then
+      if fmt.contains 'Q' then
         rowWiseOutcome col rows
       else
         genericOutcome col rows
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
 /- The distinguished failure that escapes the per-column comparison when the
@@ -171,16 +171,8 @@
   ensures out = diffSpec fmt col rows
   do
     -- impl-start
-    -- Classify the column by its format descriptor and route the comparison
-    -- accordingly: a column whose format carries a variable-length marker is
-    -- compared ROW BY ROW; every other column is compared by the generic
-    -- element-wise route. Each route produces the per-row difference verdict when
-    -- it can run on this column's element kind, and otherwise lets the failure
-    -- escape. With every variable-length column — and only those — routed
-    -- row-wise, each column is sent down a route its element kind supports, so
-    -- the comparison always completes.
     let result : Except DiffErr (List Bool) :=
-      if isVLA fmt then
+      if col.varLength then
         rowWiseOutcome col rows
       else
         genericOutcome col rows
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
 /- The distinguished failure that escapes the per-column comparison when the
@@ -171,19 +171,10 @@
   ensures out = diffSpec fmt col rows
   do
     -- impl-start
-    -- Classify the column by its format descriptor and route the comparison
-    -- accordingly: a column whose format carries a variable-length marker is
-    -- compared ROW BY ROW; every other column is compared by the generic
-    -- element-wise route. Each route produces the per-row difference verdict when
-    -- it can run on this column's element kind, and otherwise lets the failure
-    -- escape. With every variable-length column — and only those — routed
-    -- row-wise, each column is sent down a route its element kind supports, so
-    -- the comparison always completes.
     let result : Except DiffErr (List Bool) :=
-      if isVLA fmt then
-        rowWiseOutcome col rows
-      else
-        genericOutcome col rows
+      match rows with
+      | [] => Except.ok []
+      | _  => if isVLA fmt then rowWiseOutcome col rows else genericOutcome col rows
     return result
     -- impl-end
 
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
 /- The distinguished failure that escapes the per-column comparison when the
@@ -171,19 +171,11 @@
   ensures out = diffSpec fmt col rows
   do
     -- impl-start
-    -- Classify the column by its format descriptor and route the comparison
-    -- accordingly: a column whose format carries a variable-length marker is
-    -- compared ROW BY ROW; every other column is compared by the generic
-    -- element-wise route. Each route produces the per-row difference verdict when
-    -- it can run on this column's element kind, and otherwise lets the failure
-    -- escape. With every variable-length column — and only those — routed
-    -- row-wise, each column is sent down a route its element kind supports, so
-    -- the comparison always completes.
     let result : Except DiffErr (List Bool) :=
-      if isVLA fmt then
+      if !(isVLA fmt) then
+        genericOutcome col rows
+      else
         rowWiseOutcome col rows
-      else
-        genericOutcome col rows
     return result
     -- impl-end
 
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
 /- The distinguished failure that escapes the per-column comparison when the
@@ -171,20 +171,10 @@
   ensures out = diffSpec fmt col rows
   do
     -- impl-start
-    -- Classify the column by its format descriptor and route the comparison
-    -- accordingly: a column whose format carries a variable-length marker is
-    -- compared ROW BY ROW; every other column is compared by the generic
-    -- element-wise route. Each route produces the per-row difference verdict when
-    -- it can run on this column's element kind, and otherwise lets the failure
-    -- escape. With every variable-length column — and only those — routed
-    -- row-wise, each column is sent down a route its element kind supports, so
-    -- the comparison always completes.
-    let result : Except DiffErr (List Bool) :=
-      if isVLA fmt then
-        rowWiseOutcome col rows
-      else
-        genericOutcome col rows
-    return result
+    let mut x : Nat := 0
+    while true do
+      x := x + 1
+    return genericOutcome col rows
     -- impl-end
 
 prove_correct diffVLAColumn by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The distinguished failure that escapes the per-column comparison when the
   comparison route a column is sent down cannot produce a verdict for it. Two
   shapes of column have a route that cannot complete:

     * a column whose elements are themselves sequences of more than one element,
       compared by the GENERIC element-wise route: the per-row element-wise
       comparison yields, per such row, a multi-element verdict whose overall
       truth value is ambiguous, so the route cannot reduce it to a verdict;
     * a column whose elements are NOT order-comparable as numbers (e.g. text
       elements), compared by the ROW-WISE numeric-closeness route: numeric
       closeness is undefined for such elements, so that route cannot run.

   Either way the comparison fails to complete — exactly the spurious-difference
   symptom the public problem statement reports when a column is sent down a
   route unsuited to its element kind. Modeled explicitly so the spec can pin
   precisely WHEN it does and does NOT occur. Provenance + executable soundness
   check: mapping.md §3 / axiom_check.py (G-AX). -/
inductive DiffErr where
  | ambiguous
  deriving DecidableEq
-- axioms-end

-- pure-start
/- One row of the two columns under comparison, reduced to the two observations
   the per-row comparison depends on:

     * `differs`   — whether this row's contents in the two columns are unequal
                     (the per-row verdict the comparison records);
     * `multiElem` — whether this row holds MORE THAN ONE element. A row of more
                     than one element is what makes the generic element-wise route
                     produce an ambiguous verdict for this row (mapping.md §2).

   A column whose rows are variable-length sequences is carried by `List Row`;
   the only per-row observations that matter to the comparison outcome are these
   two flags. -/
structure Row where
  differs : Bool
  multiElem : Bool
  deriving DecidableEq

/- The two intrinsic per-column observations — properties of the column's actual
   element kind, INDEPENDENT of how the column happens to be routed:

     * `varLength`     — whether the column's elements are themselves
                         variable-length sequences (so a row may hold more than
                         one element). A variable-length column compared by the
                         generic element-wise route on a multi-element row cannot
                         reduce that row to a verdict.
     * `numComparable` — whether the column's elements are comparable by numeric
                         closeness. A column whose elements are not numerically
                         comparable (e.g. text elements) cannot be compared by the
                         row-wise numeric-closeness route at all.

   These are what determine whether a chosen route can complete; the format
   descriptor only chooses the route (mapping.md §2). -/
structure Column where
  varLength : Bool
  numComparable : Bool
  deriving DecidableEq

/- The descriptor characters that mark a column as a variable-length-array
   column: a column is classified variable-length iff its format descriptor
   contains one of these two markers. Deep model (an A-reference, mapping.md
   §3.1) of the variable-length classification the comparison performs on a
   column's format; validated == the real format test by axiom_check.py (G-AX).
   The classification must agree with the column's intrinsic kind (`varLength`)
   so every variable-length column — and only those — is sent row-wise. -/
def isVLA (fmt : List Char) : Bool :=
  fmt.contains 'P' || fmt.contains 'Q'

/- Whether ANY row of the column holds more than one element. Front-recursive so
   a single unfold is available per element (the fold pattern, plan §5.4). -/
def anyMulti : List Row → Bool
  | []      => false
  | r :: rs => r.multiElem || anyMulti rs

/- The per-row difference verdict of the column: the per-row `differs` flag of
   every row, in order. Front-recursive (one unfold per row). This is the verdict
   a route produces when it can complete. -/
def rowResult : List Row → List Bool
  | []      => []
  | r :: rs => r.differs :: rowResult rs

/- The outcome the ROW-WISE numeric-closeness route produces on a column, as
   `Except DiffErr (List Bool)`: it completes with the per-row difference verdict
   when the column's elements are numerically comparable, and otherwise cannot
   run (the failure escapes). It does NOT care about element counts: a
   variable-length, multi-element column is compared one row at a time and so
   always completes when its elements are numerically comparable. -/
def rowWiseOutcome (col : Column) (rows : List Row) : Except DiffErr (List Bool) :=
  if col.numComparable then
    Except.ok (rowResult rows)
  else
    Except.error DiffErr.ambiguous

/- The outcome the GENERIC element-wise route produces on a column: it completes
   with the per-row difference verdict UNLESS the column's elements are
   themselves variable-length sequences AND some row holds more than one element,
   in which case the route cannot reduce that row to a verdict and the failure
   escapes. A column that is not intrinsically variable-length is a regular
   fixed-width block whose element-wise comparison always completes, whatever its
   rows' element counts. -/
def genericOutcome (col : Column) (rows : List Row) : Except DiffErr (List Bool) :=
  if col.varLength && anyMulti rows then
    Except.error DiffErr.ambiguous
  else
    Except.ok (rowResult rows)

/- The intended outcome of comparing the two columns. The route is chosen by the
   format descriptor: a column classified variable-length (`isVLA fmt`) is
   compared ROW BY ROW; every other column is compared by the GENERIC
   element-wise route. The outcome is then whatever the chosen route produces on
   this column's actual element kind (`rowWiseOutcome` / `genericOutcome`).

   For the comparison to NEVER let a failure escape, the route must match the
   column's element kind: a variable-length column must be sent row-wise (the
   generic route would fail to reduce its multi-element rows), and a column whose
   elements are not numerically comparable must be sent generic (the row-wise
   numeric route cannot run on it). The classification `isVLA fmt` is correct
   exactly when it agrees with the column's intrinsic variable-length kind, so the
   route is faithful to the element kind and the comparison always completes — the
   behavior the public problem statement demands (identical inputs never register
   a difference). Misclassifying a column sends it down a route its element kind
   does not support and the failure escapes. -/
def diffSpec (fmt : List Char) (col : Column) (rows : List Row) :
    Except DiffErr (List Bool) :=
  if isVLA fmt then
    rowWiseOutcome col rows
  else
    genericOutcome col rows
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compare two table columns and report which rows differ.

   Desired behavior: a column is classified by its format descriptor and the
   comparison is routed accordingly. A column classified as a VARIABLE-LENGTH
   column — its format carries a variable-length marker — is compared ROW BY ROW;
   every other column is compared by the generic element-wise route. The chosen
   route must match the column's actual element kind for the comparison to
   complete: the generic route cannot reduce a variable-length column's
   multi-element rows to a verdict, and the row-wise numeric-closeness route
   cannot run on a column whose elements are not numerically comparable. Routing
   every variable-length column — and only those — row-wise sends each column down
   the route its element kind supports, so the comparison always completes and
   identical inputs never register a difference (the behavior the public problem
   statement requires).

   `fmt`, `col`, and `rows` are read-only (none is `mut`): the comparison computes
   a verdict and mutates no input (directive 5). A column's format is modeled by
   its descriptor characters, its intrinsic kind by whether its elements are
   variable-length and numerically comparable, and each row by whether its
   contents differ between the two columns and whether it holds more than one
   element (mapping.md §2). -/
method diffVLAColumn (fmt : List Char) (col : Column) (rows : List Row)
    return (out : Except DiffErr (List Bool))
  ensures out = diffSpec fmt col rows
  do
    -- impl-start
    let result : Except DiffErr (List Bool) :=
      if isVLA fmt then
        rowWiseOutcome col rows
      else
        genericOutcome col rows
    return result
    -- impl-end

prove_correct diffVLAColumn by
  loom_solve
  simp_all [diffSpec]
```

Prepatch bug re-encoded as an attack: `True`.

Spec postcondition is an EXACT functional echo: `ensures out = diffSpec fmt col rows` with fmt/col/rows fully free & independently universally quantified. Any terminating verifying impl is therefore extensionally equal to diffSpec pointwise, whose faithful patch is exactly the gold patch (the changed clause `isVLA fmt = fmt.contains 'P' || fmt.contains 'Q'` deep-models the `elif "P" in col.format or "Q" in col.format` change). PROTOCOL EXECUTED (project root, verifier scripts/lean_verify.sh, same_spec via python).

same_spec: all 9 attacks + pos = True (frozen axioms/pure/pre/post/proof byte-identical).

Verification results (bash scripts/lean_verify.sh <f>):
- pos.lean (gold-equivalent positive control) -> exit 0 (VERIFIES).
- atk_1.lean P-only classifier (== shipped Solution_prepatch.lean, prepatch bug) -> exit 1. Goal: (if 'P'∈fmt then rowWise else generic) = if isVLA fmt then rowWise else generic. PREPATCH REPRODUCED.
- atk_2.lean commuted-|| echo ('Q'||'P') -> exit 1 (unsolved: commuted disjunction not defeq to isVLA under the frozen simp_all).
- atk_3.lean everything row-wise (ungrounded-oracle) -> exit 1 (isVLA fmt=false -> rowWise=generic unprovable; text non-numComparable counterexample).
- atk_4.lean everything generic (ungrounded-oracle) -> exit 1 (isVLA fmt=true -> generic=rowWise unprovable; VLA multi-elem counterexample).
- atk_5.lean Q-only boundary classifier -> exit 1.
- atk_6.lean control-flow-effect: route on intrinsic col.varLength instead of fmt -> exit 1 (fmt and col independent, no defeq).
- atk_7.lean partial-domain: special-case rows=[] to Except.ok [] -> exit 1 (breaks on isVLA & ¬numComparable & []).
- atk_8.lean negated-branch echo (if !isVLA then generic else rowWise) -> exit 1 (frozen simp_all does not normalize the negated split).
- atk_9.lean DIVERGENCE attack (while true do ...; return genericOutcome): under termination=partial + choice=demonic, loom_solve closes the postcondition VACUOUSLY, but the FROZEN proof tail `simp_all [diffSpec]` then errors 'No goals to be solved' -> exit 1. The frozen proof block (part of the same_spec region) defeats the canonical partial-correctness divergence hole for THIS bundle. NO break.

Because NO wrong impl verifies, there are zero faithful patches to materialize; the mandatory resolve step is triggered only by a VERIFYING wrong impl and is therefore vacuously satisfied (patches={}). Gold-patch resolvability is the G-RESOLVE gate's domain.

refinement.md audit: A1-A3=R (str<->List Char; Column{varLength,numComparable}<->numpy dtype kind; Row{differs,multiElem}<->aligned arra/arrb rows). A4-A6=A-reference+I (isVLA deep-models the changed 'P' or 'Q' format test verbatim & is claimed == intrinsic object-dtype varLength; rowWiseOutcome/genericOutcome model the two UNCHANGED numpy routes' observed outcomes; if/else and error/ok splits are concrete I). No A-consumed leg, NO kind-3 (inexpressible-changed-op) leg: the one genuinely changed operation is spelled out (isVLA) rather than hidden behind an axiom about the function under change. A-reference correspondence to real callees (format test, np.allclose row-wise, np.where generic) is coherent; its executable soundness is delegated to G-AX (axiom_check.py facts 2-4), out of G-EQ scope. Route choice is load-bearing in BOTH directions (text column must go generic; VLA multi-elem must go row-wise), so the too-weak 'route-everything-one-way' impls (atk_3/atk_4) are correctly rejected.

Parallelism: attack verifications run as concurrent background bash jobs, batches of 4 (atk_1-4, then atk_5-8+pos), then atk_9; schedule only, pass criteria unchanged.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-but-wrong impl whose faithful patch could fail to resolve.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The distinguished failure that escapes the per-column comparison when the
   comparison route a column is sent down cannot produce a verdict for it. Two
   shapes of column have a route that cannot complete:

     * a column whose elements are themselves sequences of more than one element,
       compared by the GENERIC element-wise route: the per-row element-wise
       comparison yields, per such row, a multi-element verdict whose overall
       truth value is ambiguous, so the route cannot reduce it to a verdict;
     * a column whose elements are NOT order-comparable as numbers (e.g. text
       elements), compared by the ROW-WISE numeric-closeness route: numeric
       closeness is undefined for such elements, so that route cannot run.

   Either way the comparison fails to complete — exactly the spurious-difference
   symptom the public problem statement reports when a column is sent down a
   route unsuited to its element kind. Modeled explicitly so the spec can pin
   precisely WHEN it does and does NOT occur. Provenance + executable soundness
   check: mapping.md §3 / axiom_check.py (G-AX). -/
inductive DiffErr where
  | ambiguous
  deriving DecidableEq
-- axioms-end

-- pure-start
/- One row of the two columns under comparison, reduced to the two observations
   the per-row comparison depends on:

     * `differs`   — whether this row's contents in the two columns are unequal
                     (the per-row verdict the comparison records);
     * `multiElem` — whether this row holds MORE THAN ONE element. A row of more
                     than one element is what makes the generic element-wise route
                     produce an ambiguous verdict for this row (mapping.md §2).

   A column whose rows are variable-length sequences is carried by `List Row`;
   the only per-row observations that matter to the comparison outcome are these
   two flags. -/
structure Row where
  differs : Bool
  multiElem : Bool
  deriving DecidableEq

/- The two intrinsic per-column observations — properties of the column's actual
   element kind, INDEPENDENT of how the column happens to be routed:

     * `varLength`     — whether the column's elements are themselves
                         variable-length sequences (so a row may hold more than
                         one element). A variable-length column compared by the
                         generic element-wise route on a multi-element row cannot
                         reduce that row to a verdict.
     * `numComparable` — whether the column's elements are comparable by numeric
                         closeness. A column whose elements are not numerically
                         comparable (e.g. text elements) cannot be compared by the
                         row-wise numeric-closeness route at all.

   These are what determine whether a chosen route can complete; the format
   descriptor only chooses the route (mapping.md §2). -/
structure Column where
  varLength : Bool
  numComparable : Bool
  deriving DecidableEq

/- The descriptor characters that mark a column as a variable-length-array
   column: a column is classified variable-length iff its format descriptor
   contains one of these two markers. Deep model (an A-reference, mapping.md
   §3.1) of the variable-length classification the comparison performs on a
   column's format; validated == the real format test by axiom_check.py (G-AX).
   The classification must agree with the column's intrinsic kind (`varLength`)
   so every variable-length column — and only those — is sent row-wise. -/
def isVLA (fmt : List Char) : Bool :=
  fmt.contains 'P' || fmt.contains 'Q'

/- Whether ANY row of the column holds more than one element. Front-recursive so
   a single unfold is available per element (the fold pattern, plan §5.4). -/
def anyMulti : List Row → Bool
  | []      => false
  | r :: rs => r.multiElem || anyMulti rs

/- The per-row difference verdict of the column: the per-row `differs` flag of
   every row, in order. Front-recursive (one unfold per row). This is the verdict
   a route produces when it can complete. -/
def rowResult : List Row → List Bool
  | []      => []
  | r :: rs => r.differs :: rowResult rs

/- The outcome the ROW-WISE numeric-closeness route produces on a column, as
   `Except DiffErr (List Bool)`: it completes with the per-row difference verdict
   when the column's elements are numerically comparable, and otherwise cannot
   run (the failure escapes). It does NOT care about element counts: a
   variable-length, multi-element column is compared one row at a time and so
   always completes when its elements are numerically comparable. -/
def rowWiseOutcome (col : Column) (rows : List Row) : Except DiffErr (List Bool) :=
  if col.numComparable then
    Except.ok (rowResult rows)
  else
    Except.error DiffErr.ambiguous

/- The outcome the GENERIC element-wise route produces on a column: it completes
   with the per-row difference verdict UNLESS the column's elements are
   themselves variable-length sequences AND some row holds more than one element,
   in which case the route cannot reduce that row to a verdict and the failure
   escapes. A column that is not intrinsically variable-length is a regular
   fixed-width block whose element-wise comparison always completes, whatever its
   rows' element counts. -/
def genericOutcome (col : Column) (rows : List Row) : Except DiffErr (List Bool) :=
  if col.varLength && anyMulti rows then
    Except.error DiffErr.ambiguous
  else
    Except.ok (rowResult rows)

/- The intended outcome of comparing the two columns. The route is chosen by the
   format descriptor: a column classified variable-length (`isVLA fmt`) is
   compared ROW BY ROW; every other column is compared by the GENERIC
   element-wise route. The outcome is then whatever the chosen route produces on
   this column's actual element kind (`rowWiseOutcome` / `genericOutcome`).

   For the comparison to NEVER let a failure escape, the route must match the
   column's element kind: a variable-length column must be sent row-wise (the
   generic route would fail to reduce its multi-element rows), and a column whose
   elements are not numerically comparable must be sent generic (the row-wise
   numeric route cannot run on it). The classification `isVLA fmt` is correct
   exactly when it agrees with the column's intrinsic variable-length kind, so the
   route is faithful to the element kind and the comparison always completes — the
   behavior the public problem statement demands (identical inputs never register
   a difference). Misclassifying a column sends it down a route its element kind
   does not support and the failure escapes. -/
def diffSpec (fmt : List Char) (col : Column) (rows : List Row) :
    Except DiffErr (List Bool) :=
  if isVLA fmt then
    rowWiseOutcome col rows
  else
    genericOutcome col rows
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compare two table columns and report which rows differ.

   Desired behavior: a column is classified by its format descriptor and the
   comparison is routed accordingly. A column classified as a VARIABLE-LENGTH
   column — its format carries a variable-length marker — is compared ROW BY ROW;
   every other column is compared by the generic element-wise route. The chosen
   route must match the column's actual element kind for the comparison to
   complete: the generic route cannot reduce a variable-length column's
   multi-element rows to a verdict, and the row-wise numeric-closeness route
   cannot run on a column whose elements are not numerically comparable. Routing
   every variable-length column — and only those — row-wise sends each column down
   the route its element kind supports, so the comparison always completes and
   identical inputs never register a difference (the behavior the public problem
   statement requires).

   `fmt`, `col`, and `rows` are read-only (none is `mut`): the comparison computes
   a verdict and mutates no input (directive 5). A column's format is modeled by
   its descriptor characters, its intrinsic kind by whether its elements are
   variable-length and numerically comparable, and each row by whether its
   contents differ between the two columns and whether it holds more than one
   element (mapping.md §2). -/
method diffVLAColumn (fmt : List Char) (col : Column) (rows : List Row)
    return (out : Except DiffErr (List Bool))
  ensures out = diffSpec fmt col rows
  do
    -- impl-start
    let result : Except DiffErr (List Bool) :=
      if isVLA fmt then
        rowWiseOutcome col rows
      else
        genericOutcome col rows
    return result
    -- impl-end

prove_correct diffVLAColumn by
  loom_solve
  simp_all [diffSpec]
```

Prepatch bug re-encoded as an attack: `True`.

Spec postcondition is an EXACT functional echo: `ensures out = diffSpec fmt col rows` with fmt/col/rows fully free & independently universally quantified. Any terminating verifying impl is therefore extensionally equal to diffSpec pointwise, whose faithful patch is exactly the gold patch (the changed clause `isVLA fmt = fmt.contains 'P' || fmt.contains 'Q'` deep-models the `elif "P" in col.format or "Q" in col.format` change). PROTOCOL EXECUTED (project root, verifier scripts/lean_verify.sh, same_spec via python).

same_spec: all 9 attacks + pos = True (frozen axioms/pure/pre/post/proof byte-identical).

Verification results (bash scripts/lean_verify.sh <f>):
- pos.lean (gold-equivalent positive control) -> exit 0 (VERIFIES).
- atk_1.lean P-only classifier (== shipped Solution_prepatch.lean, prepatch bug) -> exit 1. Goal: (if 'P'∈fmt then rowWise else generic) = if isVLA fmt then rowWise else generic. PREPATCH REPRODUCED.
- atk_2.lean commuted-|| echo ('Q'||'P') -> exit 1 (unsolved: commuted disjunction not defeq to isVLA under the frozen simp_all).
- atk_3.lean everything row-wise (ungrounded-oracle) -> exit 1 (isVLA fmt=false -> rowWise=generic unprovable; text non-numComparable counterexample).
- atk_4.lean everything generic (ungrounded-oracle) -> exit 1 (isVLA fmt=true -> generic=rowWise unprovable; VLA multi-elem counterexample).
- atk_5.lean Q-only boundary classifier -> exit 1.
- atk_6.lean control-flow-effect: route on intrinsic col.varLength instead of fmt -> exit 1 (fmt and col independent, no defeq).
- atk_7.lean partial-domain: special-case rows=[] to Except.ok [] -> exit 1 (breaks on isVLA & ¬numComparable & []).
- atk_8.lean negated-branch echo (if !isVLA then generic else rowWise) -> exit 1 (frozen simp_all does not normalize the negated split).
- atk_9.lean DIVERGENCE attack (while true do ...; return genericOutcome): under termination=partial + choice=demonic, loom_solve closes the postcondition VACUOUSLY, but the FROZEN proof tail `simp_all [diffSpec]` then errors 'No goals to be solved' -> exit 1. The frozen proof block (part of the same_spec region) defeats the canonical partial-correctness divergence hole for THIS bundle. NO break.

Because NO wrong impl verifies, there are zero faithful patches to materialize; the mandatory resolve step is triggered only by a VERIFYING wrong impl and is therefore vacuously satisfied (patches={}). Gold-patch resolvability is the G-RESOLVE gate's domain.

refinement.md audit: A1-A3=R (str<->List Char; Column{varLength,numComparable}<->numpy dtype kind; Row{differs,multiElem}<->aligned arra/arrb rows). A4-A6=A-reference+I (isVLA deep-models the changed 'P' or 'Q' format test verbatim & is claimed == intrinsic object-dtype varLength; rowWiseOutcome/genericOutcome model the two UNCHANGED numpy routes' observed outcomes; if/else and error/ok splits are concrete I). No A-consumed leg, NO kind-3 (inexpressible-changed-op) leg: the one genuinely changed operation is spelled out (isVLA) rather than hidden behind an axiom about the function under change. A-reference correspondence to real callees (format test, np.allclose row-wise, np.where generic) is coherent; its executable soundness is delegated to G-AX (axiom_check.py facts 2-4), out of G-EQ scope. Route choice is load-bearing in BOTH directions (text column must go generic; VLA multi-elem must go row-wise), so the too-weak 'route-everything-one-way' impls (atk_3/atk_4) are correctly rejected.

Parallelism: attack verifications run as concurrent background bash jobs, batches of 4 (atk_1-4, then atk_5-8+pos), then atk_9; schedule only, pass criteria unchanged.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical: same_spec(Solution, Solution_prepatch, VelvetBackend)=True; prepatch differs only in impl (the P-only classifier), spec-fixed region frozen. Solution.lean verifies (lean_verify exit 0). Verified every modeled route behavior against real numpy 1.26.4: (1) generic np.where(arra!=arrb) raises ValueError iff object-dtype AND multi-element row — confirmed object-multi raises, object-len≤1 completes, non-object fixed-multidim 2J completes with correct diff-set; matches genericOutcome guard (varLength && anyMulti), NOT anyMulti alone. (2) row-wise np.allclose raises DTypePromotionError on text '*A' (¬numComparable), completes on numeric; matches rowWiseOutcome guard (numComparable). (3) isVLA = fmt.contains 'P' || 'Q' is a verbatim transliteration of the real diff.py:1452 test, so any incidental format match is replicated exactly — faithful by construction. (4) Completing generic diff row-set equals {i|differs} (set(np.where[0])). All four isVLA×numComparable×varLength combinations in the modeled domain agree with the real per-column route. The mismatched-sub-array-length crash is a genuine real behavior but lies outside the partial R-bijection's domain (differs is undefined there), so it is a completeness gap, not a too-strong/drift defect. The spec does not over-constrain any modeled input; an implementation mirroring the gold-patched _diff route choice verifies. FAITHFUL.

Counterexample / evidence:

```
N/A — no modeled input exhibits spec/real disagreement.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction audit of the velvet spec view for astropy__astropy-14539.

SPEC-REGION INTEGRITY: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True; spec_signature is byte-identical across pre/post-patch — the spec view does not shift to encode the edit (only the impl region differs). meta G-HYGIENE region hashes present; G-LEAK recorded pass, no relaxed_leakage flag, no RELAXED_LEAKAGE.md.

MECHANICAL SCREEN (leakage.screen): passed, hard_failures=[]. No diff markers; gold changed line `elif "P" in col.format or "Q" in col.format:` is NOT reproduced (normalized-absent from view); patched path astropy/io/fits/diff.py absent; only distinctive changed symbol `diff` does not appear as a spec-view identifier or in comments; no bug/fix/prepatch/previously narration tokens in comments.

SEMANTIC GOLD-RECONSTRUCTION (the real question): The discriminating spec content is isVLA fmt = fmt.contains 'P' || fmt.contains 'Q' plus abstract route-choice prose. Judged against the SOLVER-VISIBLE problem_statement ONLY (not hints_text):
  - The public problem_statement already exposes the VLA angle: reproducer uses format='QD', names 'improper handling of VLAs (variable-length arrays)', and states identical files must never differ. So Q-format VLA involvement is PUBLIC.
  - The hints_text carries the actually-leaky phrasing ('only `P` is handled', the exact diff adding `or "Q" in col.format`). That phrasing is NOT echoed anywhere in the spec view.
  - The spec adds P as a co-marker and describes correct routing (VLA→row-wise, others→generic; element-kind constraints). This is legitimate specification of CORRECT behavior, which every spec necessarily encodes. It does not narrate the repo's prior state, does not say 'add Q' / 'was P-only', does not reference a modified codebase, and does not name the patched function/file.
  - Comments reference the 'public problem statement' symptom abstractly and describe behavior, not the edit.

CONCLUSION: The spec characterizes the correct answer (unavoidable) but does not reconstruct the gold EDIT beyond what the public problem_statement + FITS domain knowledge already supply. No spec-view line leaks the gold edit. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
