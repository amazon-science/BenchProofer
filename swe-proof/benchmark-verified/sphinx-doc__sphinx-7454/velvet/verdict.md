# P2 adversarial audit — sphinx-doc__sphinx-7454

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. Building a single cross-reference for a name in a
@@ -68,11 +68,7 @@
   ensures out.kind = .valueRef ↔ name = "None".toList
   do
     -- impl-start
-    -- The resolution kind dispatches on the name: the `None` singleton denotes a
-    -- value and so resolves as a value reference; every other name resolves as a
-    -- class reference. Domain, target name, and shown label are the same in both
-    -- arms.
-    let kind : RefKind := if name = "None".toList then .valueRef else .classRef
+    let kind : RefKind := .classRef
     let result : TypeReference :=
       { kind   := kind,
         domain := "py".toList,
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
 -- (No axiomatized callees. Building a single cross-reference for a name in a
@@ -68,11 +68,7 @@
   ensures out.kind = .valueRef ↔ name = "None".toList
   do
     -- impl-start
-    -- The resolution kind dispatches on the name: the `None` singleton denotes a
-    -- value and so resolves as a value reference; every other name resolves as a
-    -- class reference. Domain, target name, and shown label are the same in both
-    -- arms.
-    let kind : RefKind := if name = "None".toList then .valueRef else .classRef
+    let kind : RefKind := if name = "None".toList then .classRef else .valueRef
     let result : TypeReference :=
       { kind   := kind,
         domain := "py".toList,
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
 -- (No axiomatized callees. Building a single cross-reference for a name in a
@@ -68,11 +68,7 @@
   ensures out.kind = .valueRef ↔ name = "None".toList
   do
     -- impl-start
-    -- The resolution kind dispatches on the name: the `None` singleton denotes a
-    -- value and so resolves as a value reference; every other name resolves as a
-    -- class reference. Domain, target name, and shown label are the same in both
-    -- arms.
-    let kind : RefKind := if name = "None".toList then .valueRef else .classRef
+    let kind : RefKind := if name = "none".toList then .valueRef else .classRef
     let result : TypeReference :=
       { kind   := kind,
         domain := "py".toList,
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
 -- (No axiomatized callees. Building a single cross-reference for a name in a
@@ -68,14 +68,10 @@
   ensures out.kind = .valueRef ↔ name = "None".toList
   do
     -- impl-start
-    -- The resolution kind dispatches on the name: the `None` singleton denotes a
-    -- value and so resolves as a value reference; every other name resolves as a
-    -- class reference. Domain, target name, and shown label are the same in both
-    -- arms.
     let kind : RefKind := if name = "None".toList then .valueRef else .classRef
     let result : TypeReference :=
       { kind   := kind,
-        domain := "py".toList,
+        domain := "js".toList,
         target := name,
         label  := name }
     return result
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
 -- (No axiomatized callees. Building a single cross-reference for a name in a
@@ -68,11 +68,7 @@
   ensures out.kind = .valueRef ↔ name = "None".toList
   do
     -- impl-start
-    -- The resolution kind dispatches on the name: the `None` singleton denotes a
-    -- value and so resolves as a value reference; every other name resolves as a
-    -- class reference. Domain, target name, and shown label are the same in both
-    -- arms.
-    let kind : RefKind := if name = "None".toList then .valueRef else .classRef
+    let kind : RefKind := .valueRef
     let result : TypeReference :=
       { kind   := kind,
         domain := "py".toList,
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
 -- (No axiomatized callees. Building a single cross-reference for a name in a
@@ -68,16 +68,12 @@
   ensures out.kind = .valueRef ↔ name = "None".toList
   do
     -- impl-start
-    -- The resolution kind dispatches on the name: the `None` singleton denotes a
-    -- value and so resolves as a value reference; every other name resolves as a
-    -- class reference. Domain, target name, and shown label are the same in both
-    -- arms.
     let kind : RefKind := if name = "None".toList then .valueRef else .classRef
     let result : TypeReference :=
       { kind   := kind,
         domain := "py".toList,
         target := name,
-        label  := name }
+        label  := name.reverse }
     return result
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
 -- (No axiomatized callees. Building a single cross-reference for a name in a
@@ -68,11 +68,10 @@
   ensures out.kind = .valueRef ↔ name = "None".toList
   do
     -- impl-start
-    -- The resolution kind dispatches on the name: the `None` singleton denotes a
-    -- value and so resolves as a value reference; every other name resolves as a
-    -- class reference. Domain, target name, and shown label are the same in both
-    -- arms.
-    let kind : RefKind := if name = "None".toList then .valueRef else .classRef
+    let kind : RefKind :=
+      if name = "None".toList then .valueRef
+      else if name = ([] : List Char) then .valueRef
+      else .classRef
     let result : TypeReference :=
       { kind   := kind,
         domain := "py".toList,
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
 -- (No axiomatized callees. Building a single cross-reference for a name in a
@@ -68,15 +68,10 @@
   ensures out.kind = .valueRef ↔ name = "None".toList
   do
     -- impl-start
-    -- The resolution kind dispatches on the name: the `None` singleton denotes a
-    -- value and so resolves as a value reference; every other name resolves as a
-    -- class reference. Domain, target name, and shown label are the same in both
-    -- arms.
-    let kind : RefKind := if name = "None".toList then .valueRef else .classRef
     let result : TypeReference :=
-      { kind   := kind,
+      { kind   := desiredKind name,
         domain := "py".toList,
-        target := name,
+        target := "None".toList,
         label  := name }
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Building a single cross-reference for a name in a
--  type annotation is a pure computation over the name text; the node
--  constructor and the surrounding annotation parser are collapsed into the
--  input name and the result record, and are owed no contract. There is no
--  `axiom` declaration and no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- How a name appearing in a type annotation is to be resolved into a
   documentation link:
     * `classRef` — resolved as a class, the kind used for ordinary type names
                    such as `int`, `List`, or a user-defined class;
     * `valueRef` — resolved as a plain value/object, used for a name that
                    denotes a value rather than a class. -/
inductive RefKind where
  | classRef
  | valueRef
  deriving Inhabited, DecidableEq

/- A resolved cross-reference, reduced to the fields that determine how it links:
   the resolution kind, the documentation domain it resolves in, the target name
   it points at, and the text shown to the reader. -/
structure TypeReference where
  kind   : RefKind
  domain : List Char
  target : List Char
  label  : List Char
  deriving Inhabited, DecidableEq

/- The resolution kind a name should get: the literal name of the singleton
   value `None` denotes a value, so it is resolved as a plain value reference (so
   that it links to that value's documentation); every other name is treated as
   a class reference. -/
def desiredKind (name : List Char) : RefKind :=
  if name = "None".toList then .valueRef else .classRef
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the cross-reference for one name occurring in a type annotation. `name`
   is read-only (not `mut`): the reference is freshly constructed and the input
   name is echoed verbatim into both the target and the shown label (directive 5
   — the input frame is stated exactly in the postconditions). The domain is
   always the Python domain. The resolution kind is the only thing that varies
   with the name: the `None` singleton resolves as a value reference, every other
   name as a class reference, so that `None` links the same way other type names
   do. -/
method referenceForName (name : List Char) return (out : TypeReference)
  ensures out.domain = "py".toList
  ensures out.target = name
  ensures out.label = name
  ensures out.kind = desiredKind name
  ensures name = "None".toList → out.kind = .valueRef
  ensures name ≠ "None".toList → out.kind = .classRef
  ensures out.kind = .valueRef ↔ name = "None".toList
  do
    -- impl-start
    -- The resolution kind dispatches on the name: the `None` singleton denotes a
    -- value and so resolves as a value reference; every other name resolves as a
    -- class reference. Domain, target name, and shown label are the same in both
    -- arms.
    let kind : RefKind := if name = "None".toList then .valueRef else .classRef
    let result : TypeReference :=
      { kind   := kind,
        domain := "py".toList,
        target := name,
        label  := name }
    return result
    -- impl-end

prove_correct referenceForName by
  loom_solve
  simp_all [desiredKind]
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7454 (velvet). The frozen spec fully PINS the output: postconditions determine all four TypeReference fields uniquely — out.domain='py'.toList, out.target=name, out.label=name, out.kind=desiredKind name, plus the redundant implications and the biconditional (out.kind=.valueRef ↔ name='None'.toList) which makes valueRef reachable by None and ONLY None. There is thus NO degree of freedom for a same-spec verifying wrong impl.

A-LEG AUDIT (focus): spec has ZERO `axiom` declarations (grep '^axiom' = 0); axioms-start/end block is empty commentary. mapping.md §3 = 'None' — no A-reference deep model of an outside callee. The one operation that genuinely changed (the reftype dispatch) is modeled DEEPLY via the total pure fn `desiredKind` (spelled-out if/else), NOT hidden behind a callee contract. Correspondence desiredKind name (='valueRef iff name='None') ↔ patch's `if text=='None': reftype='obj' else 'class'` is a finite exact bijection ('class'↔classRef, 'obj'↔valueRef; str↔List Char) with no owed contract. pending_xref/nodes.Text are pure constructors captured structurally by the 4 record fields. refinement.md legs A1..A4 are all R/I (no kind-3); G-AX=skip is correct. Model↔patch correspondence holds.

### ATTACKS (8 distinct, all same_spec=True vs frozen Solution.lean, verified via scripts/lean_verify.sh with timeout 300):
- atk_1 = PREPATCH BUG (kind:=.classRef unconditionally). exit=1, fails ensures_1/_3/_4 — reproduces the gold prepatch failure exactly as refinement.md §A G-DIFF claims. prepatch_reproduced=true.
- atk_2 = control-flow: swapped arms (None→classRef, else→valueRef). exit=1, fails ensures_1/_2/_3/_4.
- atk_3 = boundary/None-lookalike: condition on 'none'.toList (lowercase). exit=1, fails kind clauses (for name='None' gives classRef).
- atk_4 = unchanged-frame violation: domain:='js'.toList. exit=1, fails ensures_7 (out.domain='py'.toList).
- atk_5 = ungrounded: kind:=.valueRef unconditionally. exit=1, fails ensures_1/_2/_4.
- atk_6 = wrong shown-text echo: label:=name.reverse. exit=1, fails ensures_5 (out.label=name).
- atk_7 = partial-domain: valueRef also for empty name. exit=1 (breaks ensures_2/biconditional at name=[]).
- atk_8 = ungrounded-oracle echo: kind:=desiredKind name (correct) but target:='None'.toList constant. exit=1, fails ensures_6 (out.target=name) [and _2/_3 artifact of simp ordering].

Positive control (byte copy of Solution.lean) verifies: exit=0.

RESOLVE STEP: The protocol's mandatory resolve-run applies to every wrong impl THAT VERIFIES. ZERO wrong impls verified — the spec admits no same-spec verifying counterexample — so there is no verifying-wrong-impl patch to materialize/run through run_resolve; patches={}. verify⇒correct holds for this fully-pinned spec. Commands used: `python -c "...same_spec..."` (all True) and `bash scripts/lean_verify.sh <atk>.lean` from project root. Verdict: SOUND — ≥5 (8) distinct attacks run across all failure axes (kind-logic, boundary, control-flow-effect, frame/domain, frame/target, frame/label, partial-domain, ungrounded-oracle); none breaks the spec.

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
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Building a single cross-reference for a name in a
--  type annotation is a pure computation over the name text; the node
--  constructor and the surrounding annotation parser are collapsed into the
--  input name and the result record, and are owed no contract. There is no
--  `axiom` declaration and no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- How a name appearing in a type annotation is to be resolved into a
   documentation link:
     * `classRef` — resolved as a class, the kind used for ordinary type names
                    such as `int`, `List`, or a user-defined class;
     * `valueRef` — resolved as a plain value/object, used for a name that
                    denotes a value rather than a class. -/
inductive RefKind where
  | classRef
  | valueRef
  deriving Inhabited, DecidableEq

/- A resolved cross-reference, reduced to the fields that determine how it links:
   the resolution kind, the documentation domain it resolves in, the target name
   it points at, and the text shown to the reader. -/
structure TypeReference where
  kind   : RefKind
  domain : List Char
  target : List Char
  label  : List Char
  deriving Inhabited, DecidableEq

/- The resolution kind a name should get: the literal name of the singleton
   value `None` denotes a value, so it is resolved as a plain value reference (so
   that it links to that value's documentation); every other name is treated as
   a class reference. -/
def desiredKind (name : List Char) : RefKind :=
  if name = "None".toList then .valueRef else .classRef
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the cross-reference for one name occurring in a type annotation. `name`
   is read-only (not `mut`): the reference is freshly constructed and the input
   name is echoed verbatim into both the target and the shown label (directive 5
   — the input frame is stated exactly in the postconditions). The domain is
   always the Python domain. The resolution kind is the only thing that varies
   with the name: the `None` singleton resolves as a value reference, every other
   name as a class reference, so that `None` links the same way other type names
   do. -/
method referenceForName (name : List Char) return (out : TypeReference)
  ensures out.domain = "py".toList
  ensures out.target = name
  ensures out.label = name
  ensures out.kind = desiredKind name
  ensures name = "None".toList → out.kind = .valueRef
  ensures name ≠ "None".toList → out.kind = .classRef
  ensures out.kind = .valueRef ↔ name = "None".toList
  do
    -- impl-start
    -- The resolution kind dispatches on the name: the `None` singleton denotes a
    -- value and so resolves as a value reference; every other name resolves as a
    -- class reference. Domain, target name, and shown label are the same in both
    -- arms.
    let kind : RefKind := if name = "None".toList then .valueRef else .classRef
    let result : TypeReference :=
      { kind   := kind,
        domain := "py".toList,
        target := name,
        label  := name }
    return result
    -- impl-end

prove_correct referenceForName by
  loom_solve
  simp_all [desiredKind]
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7454 (velvet). The frozen spec fully PINS the output: postconditions determine all four TypeReference fields uniquely — out.domain='py'.toList, out.target=name, out.label=name, out.kind=desiredKind name, plus the redundant implications and the biconditional (out.kind=.valueRef ↔ name='None'.toList) which makes valueRef reachable by None and ONLY None. There is thus NO degree of freedom for a same-spec verifying wrong impl.

A-LEG AUDIT (focus): spec has ZERO `axiom` declarations (grep '^axiom' = 0); axioms-start/end block is empty commentary. mapping.md §3 = 'None' — no A-reference deep model of an outside callee. The one operation that genuinely changed (the reftype dispatch) is modeled DEEPLY via the total pure fn `desiredKind` (spelled-out if/else), NOT hidden behind a callee contract. Correspondence desiredKind name (='valueRef iff name='None') ↔ patch's `if text=='None': reftype='obj' else 'class'` is a finite exact bijection ('class'↔classRef, 'obj'↔valueRef; str↔List Char) with no owed contract. pending_xref/nodes.Text are pure constructors captured structurally by the 4 record fields. refinement.md legs A1..A4 are all R/I (no kind-3); G-AX=skip is correct. Model↔patch correspondence holds.

### ATTACKS (8 distinct, all same_spec=True vs frozen Solution.lean, verified via scripts/lean_verify.sh with timeout 300):
- atk_1 = PREPATCH BUG (kind:=.classRef unconditionally). exit=1, fails ensures_1/_3/_4 — reproduces the gold prepatch failure exactly as refinement.md §A G-DIFF claims. prepatch_reproduced=true.
- atk_2 = control-flow: swapped arms (None→classRef, else→valueRef). exit=1, fails ensures_1/_2/_3/_4.
- atk_3 = boundary/None-lookalike: condition on 'none'.toList (lowercase). exit=1, fails kind clauses (for name='None' gives classRef).
- atk_4 = unchanged-frame violation: domain:='js'.toList. exit=1, fails ensures_7 (out.domain='py'.toList).
- atk_5 = ungrounded: kind:=.valueRef unconditionally. exit=1, fails ensures_1/_2/_4.
- atk_6 = wrong shown-text echo: label:=name.reverse. exit=1, fails ensures_5 (out.label=name).
- atk_7 = partial-domain: valueRef also for empty name. exit=1 (breaks ensures_2/biconditional at name=[]).
- atk_8 = ungrounded-oracle echo: kind:=desiredKind name (correct) but target:='None'.toList constant. exit=1, fails ensures_6 (out.target=name) [and _2/_3 artifact of simp ordering].

Positive control (byte copy of Solution.lean) verifies: exit=0.

RESOLVE STEP: The protocol's mandatory resolve-run applies to every wrong impl THAT VERIFIES. ZERO wrong impls verified — the spec admits no same-spec verifying counterexample — so there is no verifying-wrong-impl patch to materialize/run through run_resolve; patches={}. verify⇒correct holds for this fully-pinned spec. Commands used: `python -c "...same_spec..."` (all True) and `bash scripts/lean_verify.sh <atk>.lean` from project root. Verdict: SOUND — ≥5 (8) distinct attacks run across all failure axes (kind-logic, boundary, control-flow-effect, frame/domain, frame/target, frame/label, partial-domain, ungrounded-oracle); none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec=True with LeanBackend.language tables); Solution.lean verifies (lean_verify.sh exit 0). The modeled function referenceForName/desiredKind is an exact transliteration of the real gold-patched callee make_xref(text) at base_commit aca3f825 (sphinx/domains/python.py, inner fn of _parse_annotation): real does `reftype = 'obj' if text=='None' else 'class'` and returns pending_xref('', nodes.Text(text), refdomain='py', reftype=reftype, reftarget=text). Field-for-field match under the stated str<->List Char and 'class'/'obj'<->classRef/valueRef bijections: kind dispatches identically on name=='None'; domain constant 'py'; target=name (reftarget=text); label=name (nodes.Text(text).astext()==text). The `kind=valueRef <-> name="None"` biconditional exactly mirrors the two-arm branch (no over-constraint). Checked boundary/near-miss inputs ("", "none", "None_", "NoneType", dotted "a.b.c"): model agrees with real make_xref on all. No input exists on which the modeled function disagrees with the real callee. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen passes (rep.passed=True, no hard failures) and same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Semantic review against the SOLVER-VISIBLE problem_statement only (not hints_text): the spec view contains no patched file path (sphinx/domains/python.py), no patched module dotted path, no verbatim gold-patch fragments ('obj'/'class'/reftype/reftype='class'), no patched repo symbol names (make_xref, _parse_annotation, pending_xref), no diff markers, and no bug/fix narration keywords. The spec's discriminating content — the `None` token resolves as a value reference while every other name resolves as a class reference (desiredKind, and the ensures clauses incl. `out.kind = .valueRef ↔ name = None.toList`) — is exactly the behavior the public problem_statement already discloses: it states the bug is that `None` in a type hint is not made a clickable link, that `None` should link to the None singleton's documentation 'regardless of description/signature mode', and contrasts None against ordinary type names like `int`. Pinning correct required behavior is what a faithful spec must do and is not a leak of the gold EDIT. The comment 'so that None links the same way other type names do' restates the problem_statement's Expected behavior, which is public. The abstraction (classRef/valueRef, TypeReference record over List Char) reveals nothing about the actual edit localization or the reftype string swap beyond public knowledge. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
