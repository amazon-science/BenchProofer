# P2 adversarial audit — django__django-11299

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Prepatch defect (test_simplecol_query): the recursive Query._add_q walk fails to forward the simple_col column-form selector into its nested-group recursive call, so nested AND-group leaves get Col (alias-qualified) instead of SimpleCol (bare) when entered via build_where (simple_col=True). Modeled by atk_1: group branch recurses `assignColumnForms false inner`. On input bare=true, conds=[.group [.atom]], the spec requires columnForms true [.group[.atom]] = [group [atom bare]] but atk_1 yields [group [atom qualified]] — postcondition `result = columnForms bare conds` cannot close (unsolved goals at prove_correct). This is exactly the F2P assertion that Q(num__gt=2, name__isnull=False) | Q(num__lt=F('id')) has SimpleCol leaves inside the AND-group.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -102,7 +102,7 @@
       let tailR ← assignColumnForms bare rest
       return (ResolvedCond.atom (formOf bare)) :: tailR
     | .group inner :: rest =>
-      let innerR ← assignColumnForms bare inner
+      let innerR ← assignColumnForms false inner
       let tailR ← assignColumnForms bare rest
       return (ResolvedCond.group innerR) :: tailR
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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -102,7 +102,7 @@
       let tailR ← assignColumnForms bare rest
       return (ResolvedCond.atom (formOf bare)) :: tailR
     | .group inner :: rest =>
-      let innerR ← assignColumnForms bare inner
+      let innerR ← assignColumnForms true inner
       let tailR ← assignColumnForms bare rest
       return (ResolvedCond.group innerR) :: tailR
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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -100,7 +100,7 @@
     | [] => return []
     | .atom :: rest =>
       let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.atom (formOf bare)) :: tailR
+      return (ResolvedCond.atom ColForm.bare) :: tailR
     | .group inner :: rest =>
       let innerR ← assignColumnForms bare inner
       let tailR ← assignColumnForms bare rest
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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -100,7 +100,7 @@
     | [] => return []
     | .atom :: rest =>
       let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.atom (formOf bare)) :: tailR
+      return (ResolvedCond.atom (formOf (!bare))) :: tailR
     | .group inner :: rest =>
       let innerR ← assignColumnForms bare inner
       let tailR ← assignColumnForms bare rest
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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -101,10 +101,9 @@
     | .atom :: rest =>
       let tailR ← assignColumnForms bare rest
       return (ResolvedCond.atom (formOf bare)) :: tailR
-    | .group inner :: rest =>
-      let innerR ← assignColumnForms bare inner
+    | .group _ :: rest =>
       let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.group innerR) :: tailR
+      return (ResolvedCond.group []) :: tailR
     -- impl-end
   termination_by sizeOf conds
   decreasing_by
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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -96,15 +96,7 @@
   ensures result = columnForms bare conds
   do
     -- impl-start
-    match conds with
-    | [] => return []
-    | .atom :: rest =>
-      let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.atom (formOf bare)) :: tailR
-    | .group inner :: rest =>
-      let innerR ← assignColumnForms bare inner
-      let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.group innerR) :: tailR
+    return []
     -- impl-end
   termination_by sizeOf conds
   decreasing_by
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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -101,10 +101,9 @@
     | .atom :: rest =>
       let tailR ← assignColumnForms bare rest
       return (ResolvedCond.atom (formOf bare)) :: tailR
-    | .group inner :: rest =>
-      let innerR ← assignColumnForms bare inner
+    | .group _ :: rest =>
       let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.group innerR) :: tailR
+      return (ResolvedCond.atom (formOf bare)) :: tailR
     -- impl-end
   termination_by sizeOf conds
   decreasing_by
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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -98,9 +98,8 @@
     -- impl-start
     match conds with
     | [] => return []
-    | .atom :: rest =>
-      let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.atom (formOf bare)) :: tailR
+    | .atom :: _ =>
+      return [ResolvedCond.atom (formOf bare)]
     | .group inner :: rest =>
       let innerR ← assignColumnForms bare inner
       let tailR ← assignColumnForms bare rest
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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -101,10 +101,9 @@
     | .atom :: rest =>
       let tailR ← assignColumnForms bare rest
       return (ResolvedCond.atom (formOf bare)) :: tailR
-    | .group inner :: rest =>
+    | .group inner :: _ =>
       let innerR ← assignColumnForms bare inner
-      let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.group innerR) :: tailR
+      return [ResolvedCond.group innerR]
     -- impl-end
   termination_by sizeOf conds
   decreasing_by
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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -101,10 +101,6 @@
     | .atom :: rest =>
       let tailR ← assignColumnForms bare rest
       return (ResolvedCond.atom (formOf bare)) :: tailR
-    | .group inner :: rest =>
-      let innerR ← assignColumnForms bare inner
-      let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.group innerR) :: tailR
     -- impl-end
   termination_by sizeOf conds
   decreasing_by
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only operation that varies with the column-form
@@ -102,9 +102,8 @@
       let tailR ← assignColumnForms bare rest
       return (ResolvedCond.atom (formOf bare)) :: tailR
     | .group inner :: rest =>
-      let innerR ← assignColumnForms bare inner
-      let tailR ← assignColumnForms bare rest
-      return (ResolvedCond.group innerR) :: tailR
+      let bogus ← assignColumnForms bare (Cond.group inner :: rest)
+      return bogus
     -- impl-end
   termination_by sizeOf conds
   decreasing_by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The only operation that varies with the column-form
--  selection is which column-reference form a single leaf condition receives;
--  that choice is governed ENTIRELY by the column-form selector and is modeled
--  DEEPLY and concretely here (`formOf` / `columnForms`) rather than behind an
--  opaque oracle. Because that deep model stands in for a real, unchanged
--  column-reference operation, its fidelity is checked against that operation
--  by an out-of-band soundness harness; nothing is asserted on faith. The
--  surrounding per-leaf
--  resolution machinery is UNCHANGED and irrelevant to the modeled behavior, so
--  it is abstracted to the resulting column form — a structural value.)
-- axioms-end

-- pure-start
/- The two forms a column reference inside an assembled condition can take: the
   `bare` (unqualified) form, or the table-`qualified` form. Which one a leaf
   condition receives is determined solely by the selector in force when that
   leaf is assembled. -/
inductive ColForm where
  | bare
  | qualified
  deriving DecidableEq, Inhabited

/- A condition as handed to the assembler: either a single leaf condition
   (`atom`), or a nested boolean group of further conditions (`group`). The
   top-level object is always a group; its members may themselves be groups,
   to arbitrary depth. -/
inductive Cond where
  | atom : Cond
  | group : List Cond → Cond
  deriving Inhabited

/- An assembled condition: each leaf now carries the column-reference form it was
   given; the grouping structure is preserved. -/
inductive ResolvedCond where
  | atom : ColForm → ResolvedCond
  | group : List ResolvedCond → ResolvedCond
  deriving Inhabited

/- The column form a leaf receives under a selector: the `bare` (unqualified)
   form exactly when the selector is set, otherwise the `qualified` form. -/
def formOf (bare : Bool) : ColForm :=
  if bare then ColForm.bare else ColForm.qualified

/- The deep model of assembling a forest of conditions under a single selector:
   every leaf — at any nesting depth — receives the column form `formOf bare`,
   and every nested group is assembled under the SAME selector (the selector is
   threaded unchanged into nested groups). Written front-recursively (mutually
   over the forest) so a single unfold is available per recursion step. -/
mutual
def columnForm (bare : Bool) : Cond → ResolvedCond
  | .atom     => ResolvedCond.atom (formOf bare)
  | .group cs => ResolvedCond.group (columnForms bare cs)
def columnForms (bare : Bool) : List Cond → List ResolvedCond
  | []      => []
  | c :: cs => columnForm bare c :: columnForms bare cs
end

@[grind] lemma columnForms_nil (b : Bool) : columnForms b [] = [] := rfl
@[grind] lemma columnForms_cons (b : Bool) (c : Cond) (cs : List Cond) :
    columnForms b (c :: cs) = columnForm b c :: columnForms b cs := rfl
@[grind] lemma columnForm_atom (b : Bool) :
    columnForm b .atom = ResolvedCond.atom (formOf b) := rfl
@[grind] lemma columnForm_group (b : Bool) (cs : List Cond) :
    columnForm b (.group cs) = ResolvedCond.group (columnForms b cs) := rfl

/- Arithmetic fact discharging the structural-recursion measure for descent into
   a group member: the member forest is strictly smaller than the whole forest.
   Content-neutral; supplied so the recursive assembler's termination and the
   correctness proof close automatically. -/
@[simp] lemma sizeOf_group_member (inner rest : List Cond) :
    sizeOf inner < 1 + (1 + sizeOf inner) + sizeOf rest := by omega
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble a forest of conditions, giving every leaf condition a column
   reference and preserving the grouping structure. The column-form selector
   `bare` chosen at the top level must reach EVERY leaf, including those inside
   nested groups: a leaf is given `formOf bare`, and descent into a nested group
   carries the SAME selector. `bare` and `conds` are read-only (directive 5);
   the assembler mutates nothing it is handed. -/
method assignColumnForms (bare : Bool) (conds : List Cond) return (result : List ResolvedCond)
  ensures result = columnForms bare conds
  do
    -- impl-start
    match conds with
    | [] => return []
    | .atom :: rest =>
      let tailR ← assignColumnForms bare rest
      return (ResolvedCond.atom (formOf bare)) :: tailR
    | .group inner :: rest =>
      let tailR ← assignColumnForms bare rest
      let innerR ← assignColumnForms bare inner
      return (ResolvedCond.group innerR) :: tailR
    -- impl-end
  termination_by sizeOf conds
  decreasing_by
    all_goals (try simp_wf)
    all_goals omega

prove_correct assignColumnForms
termination_by sizeOf conds
decreasing_by
  all_goals (try simp_wf)
  all_goals omega
by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (A-legs + model↔patch correspondence). Bundle has NO patch.diff on disk (only Solution.lean/_prepatch/mapping.md/refinement.md/meta.json/verdict.md + axiom_check.py/conformance_check.py).

SPEC SHAPE: postcondition is an EXACT functional equality `result = columnForms bare conds` over fully-concrete computable defs (columnForm/columnForms/formOf) — NO opaque oracle to echo. termination_by/decreasing_by on the method live OUTSIDE the impl region, so they are frozen by same_spec and any impl must satisfy `sizeOf conds` termination.

atk_1 prepatch bug (group recurses false): exit 1, unsolved goals at prove_correct.
- atk_2 group recurses literal true: exit 1, unsolved goals.
- atk_3 leaf constant ColForm.bare (ungrounded/echo): exit 1, unsolved goals.
- atk_4 leaf formOf (!bare) inverted: exit 1, unsolved goals.
- atk_5 nested group -> group [] (boundary): exit 1, unsolved goals.
- atk_6 return [] always (degenerate): exit 1, unsolved goals (+ benign unused-termination-hint warning).
- atk_7 treat group as atom, forget structure (control-flow-effect): exit 1, unsolved goals.
- atk_8 atom drops tail recursion, only first leaf (partial-domain): exit 1, unsolved goals.
- atk_9 group drops rest of forest (partial-domain): exit 1, unsolved goals.
- atk_10 NON-EXHAUSTIVE match, omit .group case (partial-correctness vacuity probe): exit 1, Lean totality error 'Missing cases' at method sig.
- atk_11 NON-TERMINATING self-call on same conds (vacuity-via-divergence probe): exit 1, frozen decreasing_by/omega cannot discharge measure.
Gold impl (atk_gold) and structurally-different correct positive control (atk_pos, reordered let bindings in group branch) BOTH verify exit 0 => spec non-vacuous, not accidentally unsatisfiable.

RESOLVE OBLIGATION: NO wrong impl verifies, so there is no faithful refined patch to materialize; run_resolve step (audit_eq §2) is vacuously satisfied — nothing to run, so no INCONCLUSIVE gap. All attacks completed cleanly (no timeouts/contention).

CORRESPONDENCE / A-LEG AUDIT: meta axioms=[] (zero consumed axioms). Exactly one A-reference: formOf == django...query._get_col (query.py:71-74). axiom_check.py exercises the LIVE _get_col: simple_col=True->SimpleCol with bare SQL (no alias), simple_col=False->Col with alias-qualified SQL, forms distinct — grounds the formOf bijection against the real callee, not on faith. conformance_check.py (seed 11299, 1e5 fuzz + 7 boundary incl. F2P shape) differential-tests the R/I shadow against the PATCHED _add_q recursion (simple_col forwarded into the group branch) — matches the gold fix. refinement.md A1-A6 all R / A-reference / I; no kind-3, no BLOCKED; A5 (selector threaded unchanged into nested groups) is the discriminating I leg and corresponds to the gold one-liner. All gates in meta pass (G-PBT skip only). Verify=>correct holds for this bundle: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Prepatch defect (test_simplecol_query): the recursive Query._add_q walk fails to forward the simple_col column-form selector into its nested-group recursive call, so nested AND-group leaves get Col (alias-qualified) instead of SimpleCol (bare) when entered via build_where (simple_col=True). Modeled by atk_1: group branch recurses `assignColumnForms false inner`. On input bare=true, conds=[.group [.atom]], the spec requires columnForms true [.group[.atom]] = [group [atom bare]] but atk_1 yields [group [atom qualified]] — postcondition `result = columnForms bare conds` cannot close (unsolved goals at prove_correct). This is exactly the F2P assertion that Q(num__gt=2, name__isnull=False) | Q(num__lt=F('id')) has SimpleCol leaves inside the AND-group.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

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

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The only operation that varies with the column-form
--  selection is which column-reference form a single leaf condition receives;
--  that choice is governed ENTIRELY by the column-form selector and is modeled
--  DEEPLY and concretely here (`formOf` / `columnForms`) rather than behind an
--  opaque oracle. Because that deep model stands in for a real, unchanged
--  column-reference operation, its fidelity is checked against that operation
--  by an out-of-band soundness harness; nothing is asserted on faith. The
--  surrounding per-leaf
--  resolution machinery is UNCHANGED and irrelevant to the modeled behavior, so
--  it is abstracted to the resulting column form — a structural value.)
-- axioms-end

-- pure-start
/- The two forms a column reference inside an assembled condition can take: the
   `bare` (unqualified) form, or the table-`qualified` form. Which one a leaf
   condition receives is determined solely by the selector in force when that
   leaf is assembled. -/
inductive ColForm where
  | bare
  | qualified
  deriving DecidableEq, Inhabited

/- A condition as handed to the assembler: either a single leaf condition
   (`atom`), or a nested boolean group of further conditions (`group`). The
   top-level object is always a group; its members may themselves be groups,
   to arbitrary depth. -/
inductive Cond where
  | atom : Cond
  | group : List Cond → Cond
  deriving Inhabited

/- An assembled condition: each leaf now carries the column-reference form it was
   given; the grouping structure is preserved. -/
inductive ResolvedCond where
  | atom : ColForm → ResolvedCond
  | group : List ResolvedCond → ResolvedCond
  deriving Inhabited

/- The column form a leaf receives under a selector: the `bare` (unqualified)
   form exactly when the selector is set, otherwise the `qualified` form. -/
def formOf (bare : Bool) : ColForm :=
  if bare then ColForm.bare else ColForm.qualified

/- The deep model of assembling a forest of conditions under a single selector:
   every leaf — at any nesting depth — receives the column form `formOf bare`,
   and every nested group is assembled under the SAME selector (the selector is
   threaded unchanged into nested groups). Written front-recursively (mutually
   over the forest) so a single unfold is available per recursion step. -/
mutual
def columnForm (bare : Bool) : Cond → ResolvedCond
  | .atom     => ResolvedCond.atom (formOf bare)
  | .group cs => ResolvedCond.group (columnForms bare cs)
def columnForms (bare : Bool) : List Cond → List ResolvedCond
  | []      => []
  | c :: cs => columnForm bare c :: columnForms bare cs
end

@[grind] lemma columnForms_nil (b : Bool) : columnForms b [] = [] := rfl
@[grind] lemma columnForms_cons (b : Bool) (c : Cond) (cs : List Cond) :
    columnForms b (c :: cs) = columnForm b c :: columnForms b cs := rfl
@[grind] lemma columnForm_atom (b : Bool) :
    columnForm b .atom = ResolvedCond.atom (formOf b) := rfl
@[grind] lemma columnForm_group (b : Bool) (cs : List Cond) :
    columnForm b (.group cs) = ResolvedCond.group (columnForms b cs) := rfl

/- Arithmetic fact discharging the structural-recursion measure for descent into
   a group member: the member forest is strictly smaller than the whole forest.
   Content-neutral; supplied so the recursive assembler's termination and the
   correctness proof close automatically. -/
@[simp] lemma sizeOf_group_member (inner rest : List Cond) :
    sizeOf inner < 1 + (1 + sizeOf inner) + sizeOf rest := by omega
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble a forest of conditions, giving every leaf condition a column
   reference and preserving the grouping structure. The column-form selector
   `bare` chosen at the top level must reach EVERY leaf, including those inside
   nested groups: a leaf is given `formOf bare`, and descent into a nested group
   carries the SAME selector. `bare` and `conds` are read-only (directive 5);
   the assembler mutates nothing it is handed. -/
method assignColumnForms (bare : Bool) (conds : List Cond) return (result : List ResolvedCond)
  ensures result = columnForms bare conds
  do
    -- impl-start
    match conds with
    | [] => return []
    | .atom :: rest =>
      let tailR ← assignColumnForms bare rest
      return (ResolvedCond.atom (formOf bare)) :: tailR
    | .group inner :: rest =>
      let tailR ← assignColumnForms bare rest
      let innerR ← assignColumnForms bare inner
      return (ResolvedCond.group innerR) :: tailR
    -- impl-end
  termination_by sizeOf conds
  decreasing_by
    all_goals (try simp_wf)
    all_goals omega

prove_correct assignColumnForms
termination_by sizeOf conds
decreasing_by
  all_goals (try simp_wf)
  all_goals omega
by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (A-legs + model↔patch correspondence). Bundle has NO patch.diff on disk (only Solution.lean/_prepatch/mapping.md/refinement.md/meta.json/verdict.md + axiom_check.py/conformance_check.py).

SPEC SHAPE: postcondition is an EXACT functional equality `result = columnForms bare conds` over fully-concrete computable defs (columnForm/columnForms/formOf) — NO opaque oracle to echo. termination_by/decreasing_by on the method live OUTSIDE the impl region, so they are frozen by same_spec and any impl must satisfy `sizeOf conds` termination.

atk_1 prepatch bug (group recurses false): exit 1, unsolved goals at prove_correct.
- atk_2 group recurses literal true: exit 1, unsolved goals.
- atk_3 leaf constant ColForm.bare (ungrounded/echo): exit 1, unsolved goals.
- atk_4 leaf formOf (!bare) inverted: exit 1, unsolved goals.
- atk_5 nested group -> group [] (boundary): exit 1, unsolved goals.
- atk_6 return [] always (degenerate): exit 1, unsolved goals (+ benign unused-termination-hint warning).
- atk_7 treat group as atom, forget structure (control-flow-effect): exit 1, unsolved goals.
- atk_8 atom drops tail recursion, only first leaf (partial-domain): exit 1, unsolved goals.
- atk_9 group drops rest of forest (partial-domain): exit 1, unsolved goals.
- atk_10 NON-EXHAUSTIVE match, omit .group case (partial-correctness vacuity probe): exit 1, Lean totality error 'Missing cases' at method sig.
- atk_11 NON-TERMINATING self-call on same conds (vacuity-via-divergence probe): exit 1, frozen decreasing_by/omega cannot discharge measure.
Gold impl (atk_gold) and structurally-different correct positive control (atk_pos, reordered let bindings in group branch) BOTH verify exit 0 => spec non-vacuous, not accidentally unsatisfiable.

RESOLVE OBLIGATION: NO wrong impl verifies, so there is no faithful refined patch to materialize; run_resolve step (audit_eq §2) is vacuously satisfied — nothing to run, so no INCONCLUSIVE gap. All attacks completed cleanly (no timeouts/contention).

CORRESPONDENCE / A-LEG AUDIT: meta axioms=[] (zero consumed axioms). Exactly one A-reference: formOf == django...query._get_col (query.py:71-74). axiom_check.py exercises the LIVE _get_col: simple_col=True->SimpleCol with bare SQL (no alias), simple_col=False->Col with alias-qualified SQL, forms distinct — grounds the formOf bijection against the real callee, not on faith. conformance_check.py (seed 11299, 1e5 fuzz + 7 boundary incl. F2P shape) differential-tests the R/I shadow against the PATCHED _add_q recursion (simple_col forwarded into the group branch) — matches the gold fix. refinement.md A1-A6 all R / A-reference / I; no kind-3, no BLOCKED; A5 (selector threaded unchanged into nested groups) is the discriminating I leg and corresponds to the gold one-liner. All gates in meta pass (G-PBT skip only). Verify=>correct holds for this bundle: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on velvet django__django-11299. Spec: `ensures result = columnForms bare conds`, with deep model formOf/columnForm/columnForms over Cond/ResolvedCond/ColForm carriers modeling patched Query._add_q. Verified against the REAL repo at base_commit 6866c91b638de5368c18713fa851bfe56253ea55:

1. _get_col (query.py:71-74): `if simple_col: return SimpleCol(...) else target.get_col(alias, field)` — bare vs table-qualified — exactly formOf's `if bare then ColForm.bare else ColForm.qualified`. G-AX (axiom_check.py) exercises the live callee on both selector values and asserts exactly 1 A-reference (_get_col), no consumed axioms.
2. Selector threading is verbatim: simple_col flows unchanged through build_filter -> resolve_lookup_value -> all three _get_col call sites (query.py 1274/1278/1300); patched _add_q forwards simple_col into the recursive Node branch (1339-1341 post-patch), so every leaf at every nesting depth receives formOf(top-level selector). Model threads the SAME `bare` into nested groups — matches.
3. Abstraction is SOUND, not a strengthening: the model folds each leaf to `atom`; the declared observable (mapping.md §3) is which column class the leaf lhs is (SimpleCol vs Col). Unchanged machinery (solve_lookup_type, setup_joins, JoinPromoter votes, negation bookkeeping) does not influence the column form and is legitimately abstracted. Real _add_q additionally prunes empty subclauses (`if child_clause:`) and WhereNode squashing — but this only affects EMPTY groups, which carry zero column-form observations, so no leaf-form divergence can arise. The spec asserts nothing about the unmodeled dimensions, hence is not too strong.
4. G-CONF (conformance_check.py, seed 11299): 200014 checks (7 boundary incl. F2P Q(AND-group)|Q(leaf) shape + deep-nesting fuzz x 2 selectors) vs transliterated patched _add_q recursion — 0 disagreements.
5. same_spec(Solution, Solution_prepatch) = True (spec region byte-identical; only impl differs — prepatch recurses with `false` on nested group, dropping the selector, and correctly fails prove_correct/G-DIFF). Solution.lean verifies via lean_verify.sh (only unreachable-tactic lint warnings).

No input exists where the modeled function disagrees with the real column-form behavior of the patched callee. Spec is a faithful, appropriately-scoped abstraction — neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the actual spec view (impl/proof elided) computed via markers.spec_view for the velvet backend; mechanical leakage.screen passes (no hard failures). Gold edit = forward `simple_col` into the recursive `_add_q` call on group children (query.py:1339-1341) so the top-level selector reaches leaves nested in AND-groups. Independent review of the spec view: (1) no diff markers; (2) the gold changed line `current_negated, allow_joins, split_subq, simple_col)` is not reproduced; (3) patched file path `django/db/models/sql/query.py` / module path absent; (4) the patch's distinctive symbol `_add_q`(->`add_q`) is not embedded in any spec-view identifier (assignColumnForms/columnForm/columnForms/formOf/ColForm/Cond/bare) nor named in any comment; `simple_col`, `SimpleCol`, `Col`, `Node`, `build_where`, `_get_col`, `query.py` appear nowhere in the view; (5) no bug/fix narration in comments. The spec models the behavior abstractly (a column-form selector chosen at the top of the walk must reach every leaf at every nesting depth, threaded unchanged into nested groups) — precisely the discriminator the public problem_statement already discloses (it states nested AND-group leaves wrongly use qualified `Col` while OR leaves use `SimpleCol`, and gives the correct all-unqualified SQL). The spec view reveals no code-level specifics of the gold edit (function name, forwarded argument, diff line, file) beyond what problem_statement makes public. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
