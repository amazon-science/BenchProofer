# P2 adversarial audit — django__django-11815

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_dquote.lean`, `atk_3_partial.lean`, `atk_4_mergeimports.lean`, `atk_6_payloadleak.lean`, `atk_7_callform.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5_echo.lean`, `atk_8_echo2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no A-reference deep model of an outside callee. The
@@ -104,13 +104,14 @@
   ensures out = (memberReference module className memberName, referenceImports module)
   do
     -- impl-start
-    -- The reference is keyed on the member's symbolic name, quoted and placed in
-    -- subscript form after the qualified type; the supplied payload text and
-    -- payload imports are deliberately unused. The only import emitted is the
-    -- import of the enumeration's defining module.
+    -- Pre-image (buggy) skeleton: the reference is keyed on the member's stored
+    -- PAYLOAD as rendered on its own (call form `module.Class(payloadText)`), and
+    -- the payload's own imports are merged in. The frozen spec pins the result to
+    -- the symbolic-name subscript form with only the module import, so
+    -- prove_correct MUST fail.
     let refString : List Char :=
-      module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
-    let imports : List (List Char) := ["import ".toList ++ module]
+      module ++ ['.'] ++ className ++ ['('] ++ payloadText ++ [')']
+    let imports : List (List Char) := ("import ".toList ++ module) :: payloadImports
     return (refString, imports)
     -- impl-end
 
```

Attack 2 — `atk_2_dquote.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no A-reference deep model of an outside callee. The
@@ -104,12 +104,8 @@
   ensures out = (memberReference module className memberName, referenceImports module)
   do
     -- impl-start
-    -- The reference is keyed on the member's symbolic name, quoted and placed in
-    -- subscript form after the qualified type; the supplied payload text and
-    -- payload imports are deliberately unused. The only import emitted is the
-    -- import of the enumeration's defining module.
     let refString : List Char :=
-      module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
+      module ++ ['.'] ++ className ++ ['['] ++ (['"'] ++ memberName ++ ['"']) ++ [']']
     let imports : List (List Char) := ["import ".toList ++ module]
     return (refString, imports)
     -- impl-end
```

Attack 3 — `atk_3_partial.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no A-reference deep model of an outside callee. The
@@ -104,12 +104,9 @@
   ensures out = (memberReference module className memberName, referenceImports module)
   do
     -- impl-start
-    -- The reference is keyed on the member's symbolic name, quoted and placed in
-    -- subscript form after the qualified type; the supplied payload text and
-    -- payload imports are deliberately unused. The only import emitted is the
-    -- import of the enumeration's defining module.
     let refString : List Char :=
-      module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
+      if memberName = [] then []
+      else module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
     let imports : List (List Char) := ["import ".toList ++ module]
     return (refString, imports)
     -- impl-end
```

Attack 4 — `atk_4_mergeimports.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no A-reference deep model of an outside callee. The
@@ -104,13 +104,9 @@
   ensures out = (memberReference module className memberName, referenceImports module)
   do
     -- impl-start
-    -- The reference is keyed on the member's symbolic name, quoted and placed in
-    -- subscript form after the qualified type; the supplied payload text and
-    -- payload imports are deliberately unused. The only import emitted is the
-    -- import of the enumeration's defining module.
     let refString : List Char :=
       module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
-    let imports : List (List Char) := ["import ".toList ++ module]
+    let imports : List (List Char) := ("import ".toList ++ module) :: payloadImports
     return (refString, imports)
     -- impl-end
 
```

Attack 5 — `atk_5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms and no A-reference deep model of an outside callee. The
@@ -104,14 +104,7 @@
   ensures out = (memberReference module className memberName, referenceImports module)
   do
     -- impl-start
-    -- The reference is keyed on the member's symbolic name, quoted and placed in
-    -- subscript form after the qualified type; the supplied payload text and
-    -- payload imports are deliberately unused. The only import emitted is the
-    -- import of the enumeration's defining module.
-    let refString : List Char :=
-      module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
-    let imports : List (List Char) := ["import ".toList ++ module]
-    return (refString, imports)
+    return (memberReference module className memberName, referenceImports module)
     -- impl-end
 
 prove_correct referenceEnumMember by
```

Attack 6 — `atk_6_payloadleak.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no A-reference deep model of an outside callee. The
@@ -104,12 +104,8 @@
   ensures out = (memberReference module className memberName, referenceImports module)
   do
     -- impl-start
-    -- The reference is keyed on the member's symbolic name, quoted and placed in
-    -- subscript form after the qualified type; the supplied payload text and
-    -- payload imports are deliberately unused. The only import emitted is the
-    -- import of the enumeration's defining module.
     let refString : List Char :=
-      module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
+      module ++ ['.'] ++ className ++ ['('] ++ payloadText ++ [')']
     let imports : List (List Char) := ["import ".toList ++ module]
     return (refString, imports)
     -- impl-end
```

Attack 7 — `atk_7_callform.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no A-reference deep model of an outside callee. The
@@ -104,12 +104,8 @@
   ensures out = (memberReference module className memberName, referenceImports module)
   do
     -- impl-start
-    -- The reference is keyed on the member's symbolic name, quoted and placed in
-    -- subscript form after the qualified type; the supplied payload text and
-    -- payload imports are deliberately unused. The only import emitted is the
-    -- import of the enumeration's defining module.
     let refString : List Char :=
-      module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
+      module ++ ['.'] ++ className ++ ['('] ++ memberName ++ [')']
     let imports : List (List Char) := ["import ".toList ++ module]
     return (refString, imports)
     -- impl-end
```

Attack 8 — `atk_8_echo2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms and no A-reference deep model of an outside callee. The
@@ -104,13 +104,8 @@
   ensures out = (memberReference module className memberName, referenceImports module)
   do
     -- impl-start
-    -- The reference is keyed on the member's symbolic name, quoted and placed in
-    -- subscript form after the qualified type; the supplied payload text and
-    -- payload imports are deliberately unused. The only import emitted is the
-    -- import of the enumeration's defining module.
-    let refString : List Char :=
-      module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
-    let imports : List (List Char) := ["import ".toList ++ module]
+    let refString : List Char := memberReference module className memberName
+    let imports : List (List Char) := referenceImports module
     return (refString, imports)
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
/- No consumed axioms and no A-reference deep model of an outside callee. The
   behaviour under spec is the construction of a textual reference to one member
   of an enumeration, together with the single import that reference needs. It
   is built entirely from concrete string operations over the inputs (the
   defining module name, the enumeration type name, and the member's symbolic
   name) and is modeled DEEPLY in the `pure` region below. The decision of WHICH
   value-rendering routine handles a given value, and the surrounding
   import-collection bookkeeping, are unchanged control flow reached identically
   and are not modeled here — only the reference/import construction is. See
   mapping.md §3 and refinement.md §C. -/
-- axioms-end

-- pure-start
/- A member's symbolic name, rendered as a single quoted token: the name
   surrounded by apostrophes (the name `GOOD` renders as `'GOOD'`). This is the
   member's exact canonical textual representation ONLY on the identifier
   domain (letters, digits, underscore — never a quote, backslash, or other
   special character); the operation below REQUIRES that domain of its
   `memberName` input, so the spec never asserts this rendering outside it. -/
def quotedName (name : List Char) : List Char := ['\''] ++ name ++ ['\'']

/- The identifier alphabet for a member's symbolic name: ASCII letters, ASCII
   digits, and the underscore. On names drawn from this alphabet the canonical
   textual rendering of the name is exactly `quotedName` (single quotes, no
   escaping). -/
def isIdentChar (c : Char) : Bool := c.isAlpha || c.isDigit || c = '_'

/- The textual reference to one member of an enumeration: the qualified
   enumeration type — its defining `module` and type `className`, joined by a
   dot — followed by the member's quoted symbolic name in SUBSCRIPT form, e.g.

       module.Class['NAME']

   Built only from the module name, the type name, and the member's symbolic
   name; the member's stored payload plays no part in the reference. Keying the
   reference on the stable symbolic name (rather than the stored payload) is the
   point: the reference stays valid even when the payload is a value that may be
   rendered differently elsewhere or over time. -/
def memberReference (module className memberName : List Char) : List Char :=
  module ++ ['.'] ++ className ++ ['['] ++ quotedName memberName ++ [']']

/- The set of imports the reference needs: exactly the import of the
   enumeration's own defining module, and nothing else. The reference names no
   symbol from the member's payload, so it pulls in no payload imports. -/
def referenceImports (module : List Char) : List (List Char) :=
  ["import ".toList ++ module]

@[grind] lemma memberReference_def (module className memberName : List Char) :
    memberReference module className memberName
      = module ++ ['.'] ++ className ++ ['['] ++ quotedName memberName ++ [']'] := rfl

@[grind] lemma referenceImports_def (module : List Char) :
    referenceImports module = ["import ".toList ++ module] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the source-code reference for one member of an enumeration, used when
   that member is emitted into generated source. The reference identifies the
   member by its qualified type and its stable symbolic name.

   Inputs: `module` and `className` name the enumeration's defining module and
   type; `memberName` is the member's symbolic name; `payloadText` and
   `payloadImports` describe the member's stored payload as it would be rendered
   on its own. `payloadText` and `payloadImports` are read-only and MUST NOT
   reach the result: the reference and its imports are pinned to the module,
   type, and symbolic name alone (directive 5 — the payload is a supplied value
   that must not leak into the output). Any implementation that lets the payload
   determine the reference text or the import set fails to verify.

   Domain: the member's symbolic name is REQUIRED to be drawn from the
   identifier alphabet (letters, digits, underscore). Members declared in an
   enumeration's class body always satisfy this — their names are attribute
   names — and on this alphabet the quoted rendering `quotedName` is exactly
   the name's canonical textual representation (single quotes, no escaping).
   The spec makes no claim for names outside this alphabet (e.g. names carrying
   a quote or a backslash, constructible only through the functional
   enumeration API), whose canonical rendering may switch quote style or insert
   escapes.

   Desired behaviour: the reference renders the member by its symbolic name in
   subscript form (`module.Class['NAME']`), and the only import it requires is
   the import of the enumeration's defining module. -/
method referenceEnumMember
    (module : List Char) (className : List Char) (memberName : List Char)
    (payloadText : List Char) (payloadImports : List (List Char))
    return (out : (List Char) × (List (List Char)))
  require ∀ c ∈ memberName, isIdentChar c
  ensures out.1 = memberReference module className memberName
  ensures out.2 = referenceImports module
  ensures out = (memberReference module className memberName, referenceImports module)
  do
    -- impl-start
    -- The reference is keyed on the member's symbolic name, quoted and placed in
    -- subscript form after the qualified type; the supplied payload text and
    -- payload imports are deliberately unused. The only import emitted is the
    -- import of the enumeration's defining module.
    let refString : List Char :=
      module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
    let imports : List (List Char) := ["import ".toList ++ module]
    return (refString, imports)
    -- impl-end

prove_correct referenceEnumMember by
  loom_solve
  all_goals simp_all [memberReference, quotedName, referenceImports]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS OUTPUT-PINNED (three ensures fix out exactly to (memberReference module className memberName, referenceImports module)). same_spec froze axioms/pure/pre/post byte-identical for all 9 files (all True). No axioms/A-legs: axiom_check.py is a G-AX skip stub; refinement.md §C confirms every leg is R or I (A1/A3/A6 R via str↔List Char & (str,set)↔pair bijection; A4/A5 I identical concat/singleton), no kind-3, no consumed axioms, no A-reference deep model — audited consistent.

### PROTOCOL EXECUTION (all via scripts/lean_verify.sh 300, run concurrently ≤4/batch):
- pos_control.lean: EXIT 0 (VERIFIES) — positive control OK.
- atk_1_prepatch.lean (prepatch bug: Class(payloadText) call-form + merged payloadImports): EXIT 1 (fails postconditions) — prepatch reproduced.
- atk_2_dquote.lean (boundary: double-quote token instead of ['\'']): EXIT 1 (fail).
- atk_3_partial.lean (partial-domain: empty-name→[] branch): EXIT 1 (fail).
- atk_4_mergeimports.lean (control-flow-effect: payloadImports merged into import set): EXIT 1 (fail).
- atk_6_payloadleak.lean (payload leak: Class(payloadText) call form): EXIT 1 (fail).
- atk_7_callform.lean (call form of name Class(name) not subscript): EXIT 1 (fail).
- atk_5_echo.lean (ungrounded-oracle echo: return (memberReference…, referenceImports…) verbatim): EXIT 0 (VERIFIES).
- atk_8_echo2.lean (echo variant via let bindings of the pure fns): EXIT 0 (VERIFIES).

Only the two echoes verify, and both return output EXACTLY EQUAL to the gold-pinned format (memberReference/referenceImports). Their faithful refined patch is therefore byte-for-byte the gold patch. Materialized to faithful_patch.diff and RUN through the official harness (run_resolve, timeout 1800): RESOLVED=True, completed=True — FAIL_TO_PASS {test_serialize_class_based_validators, test_serialize_enums} both success, all 44 PASS_TO_PASS success, 0 failures. So the verifying wrong-impls' faithful patches DO resolve.

No verifying impl exists whose faithful patch fails to resolve. verify⇒output-equal-to-gold-format holds because the spec is fully output-pinned. ≥5 distinct wrong impls encoded+verified (6 correctly rejected incl. prepatch; 2 verifying echoes resolved). None breaks the spec. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_dquote.lean`, `atk_3_partial.lean`, `atk_4_mergeimports.lean`, `atk_6_payloadleak.lean`, `atk_7_callform.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5_echo.lean`, `atk_8_echo2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_dquote.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_mergeimports.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_payloadleak.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_callform.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee. The
   behaviour under spec is the construction of a textual reference to one member
   of an enumeration, together with the single import that reference needs. It
   is built entirely from concrete string operations over the inputs (the
   defining module name, the enumeration type name, and the member's symbolic
   name) and is modeled DEEPLY in the `pure` region below. The decision of WHICH
   value-rendering routine handles a given value, and the surrounding
   import-collection bookkeeping, are unchanged control flow reached identically
   and are not modeled here — only the reference/import construction is. See
   mapping.md §3 and refinement.md §C. -/
-- axioms-end

-- pure-start
/- A member's symbolic name, rendered as a single quoted token: the name
   surrounded by apostrophes (the name `GOOD` renders as `'GOOD'`). This is the
   member's exact canonical textual representation ONLY on the identifier
   domain (letters, digits, underscore — never a quote, backslash, or other
   special character); the operation below REQUIRES that domain of its
   `memberName` input, so the spec never asserts this rendering outside it. -/
def quotedName (name : List Char) : List Char := ['\''] ++ name ++ ['\'']

/- The identifier alphabet for a member's symbolic name: ASCII letters, ASCII
   digits, and the underscore. On names drawn from this alphabet the canonical
   textual rendering of the name is exactly `quotedName` (single quotes, no
   escaping). -/
def isIdentChar (c : Char) : Bool := c.isAlpha || c.isDigit || c = '_'

/- The textual reference to one member of an enumeration: the qualified
   enumeration type — its defining `module` and type `className`, joined by a
   dot — followed by the member's quoted symbolic name in SUBSCRIPT form, e.g.

       module.Class['NAME']

   Built only from the module name, the type name, and the member's symbolic
   name; the member's stored payload plays no part in the reference. Keying the
   reference on the stable symbolic name (rather than the stored payload) is the
   point: the reference stays valid even when the payload is a value that may be
   rendered differently elsewhere or over time. -/
def memberReference (module className memberName : List Char) : List Char :=
  module ++ ['.'] ++ className ++ ['['] ++ quotedName memberName ++ [']']

/- The set of imports the reference needs: exactly the import of the
   enumeration's own defining module, and nothing else. The reference names no
   symbol from the member's payload, so it pulls in no payload imports. -/
def referenceImports (module : List Char) : List (List Char) :=
  ["import ".toList ++ module]

@[grind] lemma memberReference_def (module className memberName : List Char) :
    memberReference module className memberName
      = module ++ ['.'] ++ className ++ ['['] ++ quotedName memberName ++ [']'] := rfl

@[grind] lemma referenceImports_def (module : List Char) :
    referenceImports module = ["import ".toList ++ module] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the source-code reference for one member of an enumeration, used when
   that member is emitted into generated source. The reference identifies the
   member by its qualified type and its stable symbolic name.

   Inputs: `module` and `className` name the enumeration's defining module and
   type; `memberName` is the member's symbolic name; `payloadText` and
   `payloadImports` describe the member's stored payload as it would be rendered
   on its own. `payloadText` and `payloadImports` are read-only and MUST NOT
   reach the result: the reference and its imports are pinned to the module,
   type, and symbolic name alone (directive 5 — the payload is a supplied value
   that must not leak into the output). Any implementation that lets the payload
   determine the reference text or the import set fails to verify.

   Domain: the member's symbolic name is REQUIRED to be drawn from the
   identifier alphabet (letters, digits, underscore). Members declared in an
   enumeration's class body always satisfy this — their names are attribute
   names — and on this alphabet the quoted rendering `quotedName` is exactly
   the name's canonical textual representation (single quotes, no escaping).
   The spec makes no claim for names outside this alphabet (e.g. names carrying
   a quote or a backslash, constructible only through the functional
   enumeration API), whose canonical rendering may switch quote style or insert
   escapes.

   Desired behaviour: the reference renders the member by its symbolic name in
   subscript form (`module.Class['NAME']`), and the only import it requires is
   the import of the enumeration's defining module. -/
method referenceEnumMember
    (module : List Char) (className : List Char) (memberName : List Char)
    (payloadText : List Char) (payloadImports : List (List Char))
    return (out : (List Char) × (List (List Char)))
  require ∀ c ∈ memberName, isIdentChar c
  ensures out.1 = memberReference module className memberName
  ensures out.2 = referenceImports module
  ensures out = (memberReference module className memberName, referenceImports module)
  do
    -- impl-start
    -- The reference is keyed on the member's symbolic name, quoted and placed in
    -- subscript form after the qualified type; the supplied payload text and
    -- payload imports are deliberately unused. The only import emitted is the
    -- import of the enumeration's defining module.
    let refString : List Char :=
      module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']
    let imports : List (List Char) := ["import ".toList ++ module]
    return (refString, imports)
    -- impl-end

prove_correct referenceEnumMember by
  loom_solve
  all_goals simp_all [memberReference, quotedName, referenceImports]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS OUTPUT-PINNED (three ensures fix out exactly to (memberReference module className memberName, referenceImports module)). same_spec froze axioms/pure/pre/post byte-identical for all 9 files (all True). No axioms/A-legs: axiom_check.py is a G-AX skip stub; refinement.md §C confirms every leg is R or I (A1/A3/A6 R via str↔List Char & (str,set)↔pair bijection; A4/A5 I identical concat/singleton), no kind-3, no consumed axioms, no A-reference deep model — audited consistent.

### PROTOCOL EXECUTION (all via scripts/lean_verify.sh 300, run concurrently ≤4/batch):
- pos_control.lean: EXIT 0 (VERIFIES) — positive control OK.
- atk_1_prepatch.lean (prepatch bug: Class(payloadText) call-form + merged payloadImports): EXIT 1 (fails postconditions) — prepatch reproduced.
- atk_2_dquote.lean (boundary: double-quote token instead of ['\'']): EXIT 1 (fail).
- atk_3_partial.lean (partial-domain: empty-name→[] branch): EXIT 1 (fail).
- atk_4_mergeimports.lean (control-flow-effect: payloadImports merged into import set): EXIT 1 (fail).
- atk_6_payloadleak.lean (payload leak: Class(payloadText) call form): EXIT 1 (fail).
- atk_7_callform.lean (call form of name Class(name) not subscript): EXIT 1 (fail).
- atk_5_echo.lean (ungrounded-oracle echo: return (memberReference…, referenceImports…) verbatim): EXIT 0 (VERIFIES).
- atk_8_echo2.lean (echo variant via let bindings of the pure fns): EXIT 0 (VERIFIES).

Only the two echoes verify, and both return output EXACTLY EQUAL to the gold-pinned format (memberReference/referenceImports). Their faithful refined patch is therefore byte-for-byte the gold patch. Materialized to faithful_patch.diff and RUN through the official harness (run_resolve, timeout 1800): RESOLVED=True, completed=True — FAIL_TO_PASS {test_serialize_class_based_validators, test_serialize_enums} both success, all 44 PASS_TO_PASS success, 0 failures. So the verifying wrong-impls' faithful patches DO resolve.

No verifying impl exists whose faithful patch fails to resolve. verify⇒output-equal-to-gold-format holds because the spec is fully output-pinned. ≥5 distinct wrong impls encoded+verified (6 correctly rejected incl. prepatch; 2 verifying echoes resolved). None breaks the spec. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. Real base_commit e02f67ef confirmed; gold patch switches EnumSerializer.serialize to '%s.%s[%r]' % (module, enum_class.__name__, self.value.name) with imports {'import %s' % module}. Spec regions byte-identical to prepatch (same_spec=True, velvet). Solution.lean verifies (exit 0). Crux is the %r->quotedName modeling: spec pins it behind require (forall c in memberName, isIdentChar c). Verified repr(s)=='\''+s+'\'' for every ASCII identifier char, empty string, and 200k random identifier-domain strings (0 mismatches). Proved in Lean that isIdentChar is ASCII-only (non-ASCII letters/digits e.g. e-acute, roman-numeral, arabic-indic digit all return false), so no code point where repr would switch quote style or escape can enter the modeled domain -- the precondition matches (not narrower than) the domain where the model is exact. Full differential test of real patched expression vs model over 300k inputs (module/className over all printable ASCII, memberName over identifier domain): 0 disagreements. module/className are plain %s concat (== ++), payload correctly pinned unused. Spec does not over-claim outside its domain and does not drift from the real callee on any in-domain input. G-CONF independently reports 0/100008 disagreements (seed 11815).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. (1) same_spec(Solution.lean, Solution_prepatch.lean) = True under the velvet backend — spec region byte-identical; prepatch differs only in impl/proof. (2) Mechanical leakage.screen over the spec view passes with zero hard failures. relaxed_leakage is unset, so this is a clean strict pass, not a deferral.

Leakage judged on the CONSUMER spec view only (mapping.md / refinement.md are auditor-only and excluded); hints_text is excluded per mandate. The public problem_statement already discloses the entire discriminating content of the gold fix: it states migrations must use the enum member's NAME not its VALUE, in subscript form, giving the verbatim target Status['GOOD'] (single-quoted symbolic name).

Everything the spec view pins is either stated verbatim in problem_statement or a direct logical consequence of that public fix:
- subscript form module.Class['NAME'] (memberReference) ↔ verbatim Status['GOOD'];
- keying on the symbolic name rather than the serialized payload ↔ 'name not value';
- single-quote rendering ('GOOD') ↔ verbatim in problem_statement;
- payloadText/payloadImports unused, only the defining-module import emitted ↔ direct consequence (a reference that names no payload symbol needs no payload imports; the module import pre-existed).

The spec view leaks NO repo-specific detail beyond problem_statement: it names no repo file, no EnumSerializer, no self.value.name, no %r/repr, no serializer_factory — those Python specifics appear only in hints_text and the auditor docs. The require ∀ c ∈ memberName, isIdentChar c domain condition is an abstract soundness restriction a solver would derive independently, not a disclosure of the %r mechanism. Hence the spec view discloses nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
