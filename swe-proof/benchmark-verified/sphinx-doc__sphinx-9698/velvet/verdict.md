# P2 adversarial audit — sphinx-doc__sphinx-9698

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees. The index-entry label is built entirely from the
@@ -126,9 +126,9 @@
           let shown := if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner
           match kind with
           | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
-          -- Attribute-style member read through a getter: the bare member name,
-          -- with NO empty call marker, then the parenthesized category.
-          | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
+          -- ATTACK atk_1 (prepatch bug): property emitted WITH the call marker,
+          -- reproducing the pre-fix behaviour. Must FAIL verify (G-DIFF).
+          | .propertyKind   => member ++ "() (".toList  ++ shown ++ " property)".toList
           | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
           | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
       | none =>
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
 -- (No axiomatized callees. The index-entry label is built entirely from the
@@ -129,7 +129,9 @@
           -- Attribute-style member read through a getter: the bare member name,
           -- with NO empty call marker, then the parenthesized category.
           | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
-          | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
+          -- ATTACK atk_2 (partial-domain / over-apply): also drops the call
+          -- marker on staticMethod. Correct on property but wrong here. FAIL.
+          | .staticMethod   => member ++ " (".toList ++ shown ++ " static method)".toList
           | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
       | none =>
           if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
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
 -- (No axiomatized callees. The index-entry label is built entirely from the
@@ -132,8 +132,10 @@
           | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
           | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
       | none =>
+          -- ATTACK atk_3 (boundary / unqualified leg): drop the call marker on
+          -- the bare-name no-module branch. Wrong on inputs like ('bar','').
           if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
-          else name ++ "()".toList
+          else name ++ "".toList
     return out
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
 -- (No axiomatized callees. The index-entry label is built entirely from the
@@ -123,7 +123,10 @@
       | some (owner, member) =>
           -- Prefix the owner with the module name when one is present and module
           -- names are configured to be shown.
-          let shown := if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner
+          -- ATTACK atk_4 (control-flow-effect): module-prefix guard uses ∨
+          -- instead of ∧, so the owner is prefixed whenever a module exists even
+          -- if add_module_names is off. Wrong on (modname≠[], addModuleNames=false).
+          let shown := if modname ≠ [] ∨ addModuleNames then modname ++ ['.'] ++ owner else owner
           match kind with
           | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
           -- Attribute-style member read through a getter: the bare member name,
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The index-entry label is built entirely from the
@@ -123,12 +123,15 @@
       | some (owner, member) =>
           -- Prefix the owner with the module name when one is present and module
           -- names are configured to be shown.
-          let shown := if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner
+          -- ATTACK atk_5 (ungrounded-oracle ECHO): computes the SAME values as
+          -- the frozen spec but written differently — calls the pure helper
+          -- `shownOwner` instead of inlining, and spells the property separator
+          -- as an explicit char list `[' ', '(']` (= " (".toList). Extensionally
+          -- equal to indexText, so it MUST verify; its faithful patch is the gold.
+          let shown := shownOwner modname owner addModuleNames
           match kind with
           | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
-          -- Attribute-style member read through a getter: the bare member name,
-          -- with NO empty call marker, then the parenthesized category.
-          | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
+          | .propertyKind   => member ++ [' ', '('] ++ shown ++ " property)".toList
           | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
           | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
       | none =>
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
 -- (No axiomatized callees. The index-entry label is built entirely from the
@@ -118,19 +118,24 @@
   ensures out = indexText name modname addModuleNames kind
   do
     -- impl-start
+    -- ATTACK atk_6 (verifying echo #2, restructured control flow): factor the
+    -- empty call marker into a `let marker` that is `""` exactly for property and
+    -- `"()"` otherwise, then use ONE shared build for all four qualified arms.
+    -- Extensionally equal to the frozen indexText, so it MUST verify; its
+    -- faithful patch is the gold (verify-but-restructured is not a weakness).
     let out : List Char :=
       match rsplitDot name with
       | some (owner, member) =>
-          -- Prefix the owner with the module name when one is present and module
-          -- names are configured to be shown.
           let shown := if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner
-          match kind with
-          | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
-          -- Attribute-style member read through a getter: the bare member name,
-          -- with NO empty call marker, then the parenthesized category.
-          | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
-          | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
-          | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
+          let cat : List Char := match kind with
+            | .classMethod    => "class method".toList
+            | .propertyKind   => "property".toList
+            | .staticMethod   => "static method".toList
+            | .instanceMethod => "method".toList
+          let marker : List Char := match kind with
+            | .propertyKind => "".toList
+            | _             => "()".toList
+          member ++ marker ++ " (".toList ++ shown ++ " ".toList ++ cat ++ ")".toList
       | none =>
           if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
           else name ++ "()".toList
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
 -- (No axiomatized callees. The index-entry label is built entirely from the
@@ -126,9 +126,9 @@
           let shown := if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner
           match kind with
           | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
-          -- Attribute-style member read through a getter: the bare member name,
-          -- with NO empty call marker, then the parenthesized category.
-          | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
+          -- ATTACK atk_7 (boundary / whitespace): extra space before closing
+          -- paren on the property arm. Character-differs from spec. Must FAIL.
+          | .propertyKind   => member ++ " (".toList   ++ shown ++ " property )".toList
           | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
           | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
       | none =>
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The index-entry label is built entirely from the
--  inputs — a pure per-character string computation modeled in full below.
--  Nothing is delegated to an unchanged callee, so there is no `axiom` and no
--  A-reference. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Which kind of member an index entry is being produced for. A documented
   member can be presented as a class-level member, an instance attribute
   exposed through a getter, a class-shared member, or a plain bound member.
   These four are mutually exclusive here: the kind is the single category the
   member is finally classified under (the caller resolves any overlap by a
   settled precedence before this point — see mapping.md §1). -/
inductive MethodKind where
  | classMethod
  | propertyKind
  | staticMethod
  | instanceMethod
  deriving DecidableEq, Inhabited

/- Split a dotted qualified name at its LAST separator '.', mirroring a
   right-anchored single split. `none` when the name carries no separator at all
   (a bare, unqualified name); otherwise `some (owner, member)` where `member` is
   the trailing component after the final '.' and `owner` is everything before
   it. Front-recursive so each step exposes one leading character: if the tail
   already contains a separator the split lives there and the head joins the
   owner; only when the tail has none does a head '.' become the final
   separator. -/
def rsplitDot : List Char → Option (List Char × List Char)
  | []      => none
  | c :: cs =>
    match rsplitDot cs with
    | some (owner, member) => some (c :: owner, member)
    | none                 => if c = '.' then some ([], cs) else none

/- The qualified owner actually shown in the label: when a module name is present
   and module names are configured to be shown, the owner is prefixed with that
   module name and a separator; otherwise the owner stands alone. -/
def shownOwner (modname owner : List Char) (addModuleNames : Bool) : List Char :=
  if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner

/- The index-entry label for a documented member.

   When the name is qualified (it has an owner and a trailing member component),
   the label names the member and parenthesizes the owner with a category word.
   For a class-level, class-shared, or plain bound member the member is shown as
   a CALL — its name followed by an empty call marker `()`. For a member exposed
   as an attribute through a getter, the member is shown WITHOUT that call marker
   — it is read as a value, not invoked — so only its bare name precedes the
   parenthesized category. This is the one behaviour the issue turns on: that
   attribute-style category, and only it, drops the call marker.

   When the name is unqualified (no owner component), the label is the name shown
   as a call, optionally annotated with the module it lives in. -/
def indexText
    (name modname : List Char) (addModuleNames : Bool) (kind : MethodKind) : List Char :=
  match rsplitDot name with
  | some (owner, member) =>
      let shown := shownOwner modname owner addModuleNames
      match kind with
      | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
      | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
      | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
      | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
  | none =>
      if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
      else name ++ "()".toList

/- Single-step unfold so `loom_solve` can discharge the postcondition by reducing
   the impl expression to the spec. -/
@[grind] lemma indexText_def
    (name modname : List Char) (addModuleNames : Bool) (kind : MethodKind) :
    indexText name modname addModuleNames kind =
      (match rsplitDot name with
       | some (owner, member) =>
           let shown := shownOwner modname owner addModuleNames
           match kind with
           | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
           | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
           | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
           | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
       | none =>
           if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
           else name ++ "()".toList) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the index-entry label for a documented member.

   `name` is the member's qualified name; `modname` is the module it belongs to
   (empty when none applies); `addModuleNames` says whether the module name is
   shown as a prefix; `kind` is the resolved category of the member. All four are
   read-only — none is declared `mut` — and none is altered (directive 5).

   Desired behaviour: a qualified member is labelled by its trailing component and
   its parenthesized owner-plus-category. A member exposed as an attribute through
   a getter is read as a value, so its label carries NO empty call marker `()`
   after the name; every other category is invoked and so keeps that marker. An
   unqualified name is labelled as a call, optionally annotated with its module.
   The result is the fresh label string. -/
method indexEntryText
    (name : List Char) (modname : List Char) (addModuleNames : Bool) (kind : MethodKind)
    return (out : List Char)
  ensures out = indexText name modname addModuleNames kind
  do
    -- impl-start
    let out : List Char :=
      match rsplitDot name with
      | some (owner, member) =>
          -- Prefix the owner with the module name when one is present and module
          -- names are configured to be shown.
          let shown := if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner
          match kind with
          | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
          -- Attribute-style member read through a getter: the bare member name,
          -- with NO empty call marker, then the parenthesized category.
          | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
          | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
          | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
      | none =>
          if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
          else name ++ "()".toList
    return out
    -- impl-end

prove_correct indexEntryText by
  loom_solve
  simp_all [indexText, shownOwner]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Same-spec check True for all 7 attacks + positive control (swebench_unified.markers.same_spec, velvet). All verified with scripts/lean_verify.sh (/ cap 300), run concurrently in two batches of 4.

SPEC SHAPE: postcondition is a TOTAL functional equality `out = indexText name modname addModuleNames kind` with EMPTY precondition — the tightest possible spec. Any verifying impl must be extensionally equal to indexText on ALL inputs. The only break vector is model↔patch infidelity (does indexText match the real patched get_index_text on test-exercised inputs). No axioms => no axiom-soundness break vector.

### ATTACK RESULTS (verify.log):
- atk_1 (prepatch bug reproduced: property arm WITH '()' marker) -> lean_verify EXIT=1 (FAILS verify, unsolved goal is exactly the property arm '(' ':' ')' vs ' '). Confirms prepatch_reproduced=true and G-DIFF discrimination.
- atk_2 (partial-domain / over-apply: also drops '()' on staticMethod) -> EXIT=1 FAIL.
- atk_3 (boundary: unqualified no-module leg emits bare name, dropping '()') -> EXIT=1 FAIL.
- atk_4 (control-flow-effect: module-prefix guard uses OR instead of AND) -> EXIT=1 FAIL.
- atk_7 (boundary/whitespace: extra space before ')' on property arm) -> EXIT=1 FAIL.
- atk_5 (VERIFYING ECHO: extensionally identical to indexText — calls shownOwner helper instead of inlining, spells ' (' as [' ','(']) -> EXIT=0 VERIFIES. Its faithful refined patch is behaviourally the gold. MATERIALIZED (atk_5.patch) and RUN through the official harness run_resolve('sphinx-doc__sphinx-9698', ...): RESOLVED=True COMPLETED=True NOTE='resolved' ATTEMPTS=1 FLAKY=False. => the verifying wrong-impl RESOLVES; NO break.
- atk_6 (verifying-echo attempt: factored the '()' marker into a per-kind `let marker` + one shared build) -> EXIT=1: does NOT verify. loom_solve;simp_all cannot discharge the marker-factored form without a per-`kind` case-split (proof-automation limitation, not a spec issue). Since it does not verify, it imposes no resolve obligation.
- pos_control (exact frozen Solution) -> EXIT=0 VERIFIES.

MODEL-FIDELITY (independent live confirmation, not speculation): ran the bundle's conformance_check.py against the ACTUAL patched worktree source python.py (line 799 = the gold '%s (%s property)'): 'G-CONF OK ... agrees with patch.diff behaviour on 100010 inputs (seed=9698), 0 disagreements' (exit 0). Discrimination check: reverted line 799 to the prepatch '%s() (%s property)' and re-ran -> 'G-CONF FAIL: 5 R/I disagreement(s)' (exit 1) — so the oracle genuinely distinguishes patched from prepatch. The `_(...)` gettext-as-identity modeling is empirically sound under the no-catalog unit-test default.

REFINEMENT.md AUDIT: legs A1-A7 are all R / R+I / I; NO A-legs (no axiomatized callees), NO kind-3 steps — consistent with the source (no `axiom`, no A-reference, G-AX=skip, no axiom_check.py). rsplitDot faithfully mirrors Python name.rsplit('.',1)/ValueError on all edge cases (bare / leading-dot / trailing-dot / deep-dotted); MethodKind<->self.options faithful for the single-flag inputs the F2P test exercises; shownOwner matches the module-prefix join. No correspondence defect found.

CONCLUSION: >=5 attacks run (7 total: 5 distinct wrong impls that correctly FAIL verify + the prepatch reproduction + 1 verifying echo). The ONLY verifying wrong-impl's faithful patch RESOLVES under the official harness. verify=>correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The index-entry label is built entirely from the
--  inputs — a pure per-character string computation modeled in full below.
--  Nothing is delegated to an unchanged callee, so there is no `axiom` and no
--  A-reference. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Which kind of member an index entry is being produced for. A documented
   member can be presented as a class-level member, an instance attribute
   exposed through a getter, a class-shared member, or a plain bound member.
   These four are mutually exclusive here: the kind is the single category the
   member is finally classified under (the caller resolves any overlap by a
   settled precedence before this point — see mapping.md §1). -/
inductive MethodKind where
  | classMethod
  | propertyKind
  | staticMethod
  | instanceMethod
  deriving DecidableEq, Inhabited

/- Split a dotted qualified name at its LAST separator '.', mirroring a
   right-anchored single split. `none` when the name carries no separator at all
   (a bare, unqualified name); otherwise `some (owner, member)` where `member` is
   the trailing component after the final '.' and `owner` is everything before
   it. Front-recursive so each step exposes one leading character: if the tail
   already contains a separator the split lives there and the head joins the
   owner; only when the tail has none does a head '.' become the final
   separator. -/
def rsplitDot : List Char → Option (List Char × List Char)
  | []      => none
  | c :: cs =>
    match rsplitDot cs with
    | some (owner, member) => some (c :: owner, member)
    | none                 => if c = '.' then some ([], cs) else none

/- The qualified owner actually shown in the label: when a module name is present
   and module names are configured to be shown, the owner is prefixed with that
   module name and a separator; otherwise the owner stands alone. -/
def shownOwner (modname owner : List Char) (addModuleNames : Bool) : List Char :=
  if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner

/- The index-entry label for a documented member.

   When the name is qualified (it has an owner and a trailing member component),
   the label names the member and parenthesizes the owner with a category word.
   For a class-level, class-shared, or plain bound member the member is shown as
   a CALL — its name followed by an empty call marker `()`. For a member exposed
   as an attribute through a getter, the member is shown WITHOUT that call marker
   — it is read as a value, not invoked — so only its bare name precedes the
   parenthesized category. This is the one behaviour the issue turns on: that
   attribute-style category, and only it, drops the call marker.

   When the name is unqualified (no owner component), the label is the name shown
   as a call, optionally annotated with the module it lives in. -/
def indexText
    (name modname : List Char) (addModuleNames : Bool) (kind : MethodKind) : List Char :=
  match rsplitDot name with
  | some (owner, member) =>
      let shown := shownOwner modname owner addModuleNames
      match kind with
      | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
      | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
      | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
      | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
  | none =>
      if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
      else name ++ "()".toList

/- Single-step unfold so `loom_solve` can discharge the postcondition by reducing
   the impl expression to the spec. -/
@[grind] lemma indexText_def
    (name modname : List Char) (addModuleNames : Bool) (kind : MethodKind) :
    indexText name modname addModuleNames kind =
      (match rsplitDot name with
       | some (owner, member) =>
           let shown := shownOwner modname owner addModuleNames
           match kind with
           | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
           | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
           | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
           | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
       | none =>
           if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
           else name ++ "()".toList) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the index-entry label for a documented member.

   `name` is the member's qualified name; `modname` is the module it belongs to
   (empty when none applies); `addModuleNames` says whether the module name is
   shown as a prefix; `kind` is the resolved category of the member. All four are
   read-only — none is declared `mut` — and none is altered (directive 5).

   Desired behaviour: a qualified member is labelled by its trailing component and
   its parenthesized owner-plus-category. A member exposed as an attribute through
   a getter is read as a value, so its label carries NO empty call marker `()`
   after the name; every other category is invoked and so keeps that marker. An
   unqualified name is labelled as a call, optionally annotated with its module.
   The result is the fresh label string. -/
method indexEntryText
    (name : List Char) (modname : List Char) (addModuleNames : Bool) (kind : MethodKind)
    return (out : List Char)
  ensures out = indexText name modname addModuleNames kind
  do
    -- impl-start
    let out : List Char :=
      match rsplitDot name with
      | some (owner, member) =>
          -- Prefix the owner with the module name when one is present and module
          -- names are configured to be shown.
          let shown := if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner
          match kind with
          | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
          -- Attribute-style member read through a getter: the bare member name,
          -- with NO empty call marker, then the parenthesized category.
          | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
          | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
          | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
      | none =>
          if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
          else name ++ "()".toList
    return out
    -- impl-end

prove_correct indexEntryText by
  loom_solve
  simp_all [indexText, shownOwner]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Same-spec check True for all 7 attacks + positive control (swebench_unified.markers.same_spec, velvet). All verified with scripts/lean_verify.sh (/ cap 300), run concurrently in two batches of 4.

SPEC SHAPE: postcondition is a TOTAL functional equality `out = indexText name modname addModuleNames kind` with EMPTY precondition — the tightest possible spec. Any verifying impl must be extensionally equal to indexText on ALL inputs. The only break vector is model↔patch infidelity (does indexText match the real patched get_index_text on test-exercised inputs). No axioms => no axiom-soundness break vector.

### ATTACK RESULTS (verify.log):
- atk_1 (prepatch bug reproduced: property arm WITH '()' marker) -> lean_verify EXIT=1 (FAILS verify, unsolved goal is exactly the property arm '(' ':' ')' vs ' '). Confirms prepatch_reproduced=true and G-DIFF discrimination.
- atk_2 (partial-domain / over-apply: also drops '()' on staticMethod) -> EXIT=1 FAIL.
- atk_3 (boundary: unqualified no-module leg emits bare name, dropping '()') -> EXIT=1 FAIL.
- atk_4 (control-flow-effect: module-prefix guard uses OR instead of AND) -> EXIT=1 FAIL.
- atk_7 (boundary/whitespace: extra space before ')' on property arm) -> EXIT=1 FAIL.
- atk_5 (VERIFYING ECHO: extensionally identical to indexText — calls shownOwner helper instead of inlining, spells ' (' as [' ','(']) -> EXIT=0 VERIFIES. Its faithful refined patch is behaviourally the gold. MATERIALIZED (atk_5.patch) and RUN through the official harness run_resolve('sphinx-doc__sphinx-9698', ...): RESOLVED=True COMPLETED=True NOTE='resolved' ATTEMPTS=1 FLAKY=False. => the verifying wrong-impl RESOLVES; NO break.
- atk_6 (verifying-echo attempt: factored the '()' marker into a per-kind `let marker` + one shared build) -> EXIT=1: does NOT verify. loom_solve;simp_all cannot discharge the marker-factored form without a per-`kind` case-split (proof-automation limitation, not a spec issue). Since it does not verify, it imposes no resolve obligation.
- pos_control (exact frozen Solution) -> EXIT=0 VERIFIES.

MODEL-FIDELITY (independent live confirmation, not speculation): ran the bundle's conformance_check.py against the ACTUAL patched worktree source python.py (line 799 = the gold '%s (%s property)'): 'G-CONF OK ... agrees with patch.diff behaviour on 100010 inputs (seed=9698), 0 disagreements' (exit 0). Discrimination check: reverted line 799 to the prepatch '%s() (%s property)' and re-ran -> 'G-CONF FAIL: 5 R/I disagreement(s)' (exit 1) — so the oracle genuinely distinguishes patched from prepatch. The `_(...)` gettext-as-identity modeling is empirically sound under the no-catalog unit-test default.

REFINEMENT.md AUDIT: legs A1-A7 are all R / R+I / I; NO A-legs (no axiomatized callees), NO kind-3 steps — consistent with the source (no `axiom`, no A-reference, G-AX=skip, no axiom_check.py). rsplitDot faithfully mirrors Python name.rsplit('.',1)/ValueError on all edge cases (bare / leading-dot / trailing-dot / deep-dotted); MethodKind<->self.options faithful for the single-flag inputs the F2P test exercises; shownOwner matches the module-prefix join. No correspondence defect found.

CONCLUSION: >=5 attacks run (7 total: 5 distinct wrong impls that correctly FAIL verify + the prepatch reproduction + 1 verifying echo). The ONLY verifying wrong-impl's faithful patch RESOLVES under the official harness. verify=>correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of PyMethod.get_index_text (sphinx/domains/python.py:784), post-patch. same_spec(Solution, Solution_prepatch)=True (spec view byte-identical; only impl differs). Ran a differential test of the spec's indexText model against the REAL patched function body extracted verbatim from the base-commit worktree (confirmed at f050a777... with gold hunk applied: property arm '%s (%s property)' drops the () marker), with gettext _ modeled as identity (correct under the no-catalog test default that test_pymethod_options uses). Result: 0 disagreements over 520 adversarial edge cases (empty name, '.', '..', 'a.', '.a', trailing/leading dots, deep dotted names, dotted/empty modnames) x 4 kinds x amn on/off, PLUS 300,000 fuzzed inputs. Model is total and covers all four MethodKind arms and the none branch, mirroring the real try/except + if/elif chain. Solution.lean verifies (exit 0); Solution_prepatch.lean fails elaboration exactly on the propertyKind arm ('(' :: ')' vs ' '), confirming the spec is non-vacuous and correctly discriminates the single behavioural change. No input found where the modeled function disagrees with the real callee. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage screen over the elided spec view (markers.spec_view, velvet backend); same_spec(Solution, Solution_prepatch)=True confirmed, so the frozen spec is what is judged. Gold edit: in PyMethod.get_index_text, the 'property' arm drops the empty call marker '()' after the member name (`_('%s() (%s property)')` -> `_('%s (%s property)')`). The public problem_statement already discloses this fully and explicitly: 'An index entry with parens was registered for py:method with :property: option. It should not have parens.' and 'An index entry for the property should not have parens.' The spec view's indexText encodes exactly this target behavior — propertyKind => `member ++ " (".toList ++ ...` (NO '()') while class/static/instance keep `"() ("` — which is the correct behavior the public issue demands, not disclosure beyond it. The spec view does NOT reveal any gold-edit specifics absent from the problem_statement: it does not name the repo symbol get_index_text, the file sphinx/domains/python.py, the line numbers, the '%s'-format templates, or the pre-patch string; those file/line/symbol/template bindings live only in mapping.md and refinement.md, which are auditor documents outside the spec view, not part of what G-PANEL-3 screens. The unchanged ambient category words (class method / static method / in-module annotation) and the rsplit/module-prefix modeling are pre-existing function behavior, not the patched edit. Encoding correct target behavior that the public bug report requires is legitimate spec content, not leakage. No spec-view line leaks the gold edit beyond problem_statement (hints_text was empty anyway). Recorded gate blob shows G-LEAK pass and G-PANEL-3 pass, consistent with this finding.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
