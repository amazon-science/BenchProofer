# P2 adversarial audit — sphinx-doc__sphinx-8638

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| does not verify against this specification, so the specification excludes it | 1 | `atk_1.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms. The rendering decision that turns a documented field's
@@ -84,11 +84,9 @@
   ensures out.typeNode = RefNode.xref "class".toList typ
   do
     -- impl-start
-    -- The item NAME carries no reference role: it is rendered as plain text and
-    -- never becomes a cross-reference.
-    let nameRole : Option (List Char) := none
-    -- The declared TYPE keeps its class reference role (unchanged), so it stays
-    -- a navigable cross-reference to a class.
+    -- PREPATCH BUG: the NAME still carries the 'obj' reference role, so it is
+    -- rendered as a cross-reference. Must FAIL the name postcondition.
+    let nameRole : Option (List Char) := some "obj".toList
     let typeRole : Option (List Char) := some "class".toList
     let nameNode := crossRefOrText nameRole name
     let typeNode := crossRefOrText typeRole typ
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The rendering decision that turns a documented field's
@@ -84,15 +84,9 @@
   ensures out.typeNode = RefNode.xref "class".toList typ
   do
     -- impl-start
-    -- The item NAME carries no reference role: it is rendered as plain text and
-    -- never becomes a cross-reference.
-    let nameRole : Option (List Char) := none
-    -- The declared TYPE keeps its class reference role (unchanged), so it stays
-    -- a navigable cross-reference to a class.
-    let typeRole : Option (List Char) := some "class".toList
-    let nameNode := crossRefOrText nameRole name
-    let typeNode := crossRefOrText typeRole typ
-    return { nameNode := nameNode, typeNode := typeNode }
+    -- UNGROUNDED-ORACLE ECHO: build the entry directly from the postcondition
+    -- values, bypassing the crossRefOrText decision helper entirely.
+    return { nameNode := RefNode.text name, typeNode := RefNode.xref "class".toList typ }
     -- impl-end
 
 prove_correct renderFieldEntry by
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The rendering decision that turns a documented field's
@@ -84,11 +84,11 @@
   ensures out.typeNode = RefNode.xref "class".toList typ
   do
     -- impl-start
-    -- The item NAME carries no reference role: it is rendered as plain text and
-    -- never becomes a cross-reference.
-    let nameRole : Option (List Char) := none
-    -- The declared TYPE keeps its class reference role (unchanged), so it stays
-    -- a navigable cross-reference to a class.
+    -- EMPTY-ROLE VARIANT: the NAME carries an EMPTY reference role rather than
+    -- no role. crossRefOrText maps `some []` to plain text (matching make_xref's
+    -- `if not rolename` guard), so this verifies against the frozen spec — but
+    -- the faithful patch sets rolename='' instead of removing the kwarg.
+    let nameRole : Option (List Char) := some [];
     let typeRole : Option (List Char) := some "class".toList
     let nameNode := crossRefOrText nameRole name
     let typeNode := crossRefOrText typeRole typ
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The rendering decision that turns a documented field's
@@ -84,15 +84,17 @@
   ensures out.typeNode = RefNode.xref "class".toList typ
   do
     -- impl-start
-    -- The item NAME carries no reference role: it is rendered as plain text and
-    -- never becomes a cross-reference.
-    let nameRole : Option (List Char) := none
-    -- The declared TYPE keeps its class reference role (unchanged), so it stays
-    -- a navigable cross-reference to a class.
-    let typeRole : Option (List Char) := some "class".toList
-    let nameNode := crossRefOrText nameRole name
-    let typeNode := crossRefOrText typeRole typ
-    return { nameNode := nameNode, typeNode := typeNode }
+    -- CONTROL-FLOW-EFFECT: branch on the (excluded-by-require) empty-name case.
+    -- Since `require name ≠ []`, the `else` branch always fires in-domain, so
+    -- the output is identical to gold and this verifies — but the control-flow
+    -- shape differs from the single straight-line gold hunk.
+    if name = [] then
+      return { nameNode := RefNode.xref "obj".toList name,
+               typeNode := RefNode.xref "class".toList typ }
+    else
+      let nameNode := crossRefOrText none name
+      let typeNode := crossRefOrText (some "class".toList) typ
+      return { nameNode := nameNode, typeNode := typeNode }
     -- impl-end
 
 prove_correct renderFieldEntry by
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
 /- No consumed axioms. The rendering decision that turns a documented field's
@@ -84,16 +84,17 @@
   ensures out.typeNode = RefNode.xref "class".toList typ
   do
     -- impl-start
-    -- The item NAME carries no reference role: it is rendered as plain text and
-    -- never becomes a cross-reference.
+    -- BOUNDARY / WRONG-DOMAIN: use the literal 'None' type-role rewrite path.
+    -- The require excludes typ = "None", so within the modeled domain the
+    -- typeRole stays 'class' and this verifies. But the faithful patch would
+    -- ALSO alter the type-role special-casing (an UNCHANGED-by-gold behaviour).
     let nameRole : Option (List Char) := none
-    -- The declared TYPE keeps its class reference role (unchanged), so it stays
-    -- a navigable cross-reference to a class.
-    let typeRole : Option (List Char) := some "class".toList
+    let typeRole : Option (List Char) :=
+      if typ = "None".toList then some "obj".toList else some "class".toList
     let nameNode := crossRefOrText nameRole name
     let typeNode := crossRefOrText typeRole typ
     return { nameNode := nameNode, typeNode := typeNode }
     -- impl-end
 
 prove_correct renderFieldEntry by
-  loom_solve <;> simp [crossRefOrText]
+  loom_solve <;> simp_all [crossRefOrText]
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The rendering decision that turns a documented field's
@@ -84,14 +84,16 @@
   ensures out.typeNode = RefNode.xref "class".toList typ
   do
     -- impl-start
-    -- The item NAME carries no reference role: it is rendered as plain text and
-    -- never becomes a cross-reference.
-    let nameRole : Option (List Char) := none
-    -- The declared TYPE keeps its class reference role (unchanged), so it stays
-    -- a navigable cross-reference to a class.
-    let typeRole : Option (List Char) := some "class".toList
-    let nameNode := crossRefOrText nameRole name
-    let typeNode := crossRefOrText typeRole typ
+    -- WRONG-TYPE-ROLE-VALUE that still satisfies the frozen postcondition:
+    -- the type node is constructed directly as an 'class' xref while the NAME
+    -- role is 'data' (a truthy role) but overridden to text. Actually here we
+    -- pick a DIFFERENT truthy nameRole but then discard it and emit text for the
+    -- NAME, matching the postcondition. The faithful patch would carry rolename
+    -- pointing at a different (still-navigable) role for the name.
+    let nameRole : Option (List Char) := some "data".toList
+    let _unused := crossRefOrText nameRole name
+    let nameNode := RefNode.text name
+    let typeNode := crossRefOrText (some "class".toList) typ
     return { nameNode := nameNode, typeNode := typeNode }
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The rendering decision that turns a documented field's
   argument into a node — emit a cross-reference when a reference role is
   configured for that argument, otherwise emit a plain inline text node — is
   modeled DEEPLY in the `pure` region (`crossRefOrText`). It is the faithful
   model of an UNCHANGED standard inline-rendering helper, validated against the
   real helper by axiom_check.py (G-AX) as a deep-model reference (mapping.md
   §3); there is no module-level `axiom` the proof consumes. -/
-- axioms-end

-- pure-start
/- The two shapes an inline node can take in a rendered documentation field
   entry. `text` is a plain inline node carrying its content verbatim (no
   navigation target attached); `xref` is a pending cross-reference of a given
   reference kind to a target. The only distinction the desired behaviour cares
   about is whether a navigable cross-reference was produced (mapping.md §2). -/
inductive RefNode where
  | text (content : List Char)
  | xref (refkind : List Char) (target : List Char)
  deriving DecidableEq

/- The rendering decision for one argument of a documentation field: if a
   non-empty reference role is configured for that argument, the argument is
   turned into a pending cross-reference of that kind to itself; otherwise it is
   emitted as a plain inline text node with no navigation target. This is the
   standard inline-rendering rule (deep model of an unchanged helper, mapping.md
   §3.1). -/
def crossRefOrText (refrole : Option (List Char)) (target : List Char) : RefNode :=
  match refrole with
  | none   => RefNode.text target
  | some r => if r = [] then RefNode.text target else RefNode.xref r target

/- A plain-name character: a letter, a digit or an underscore. Pins the modeled
   input domain to simple one-word names/types (e.g. `attr`, `int`, `MyClass`).
   Composite type expressions (bracketed/comma/'or'-joined lists of types),
   abbreviation-prefixed targets (leading '.'/'~') and the literal word `None`
   are rendered through unchanged list-splitting / prefix-stripping /
   special-casing machinery that is orthogonal to this change and produces a
   different entry shape, so they are outside the modeled domain (mapping.md
   §2). -/
def isIdentChar (c : Char) : Bool := c.isAlpha || c.isDigit || c = '_'
-- pure-end

/- The observable content of one rendered entry of an info field documenting a
   named item together with its type: the node produced for the item's NAME and
   the node produced for its TYPE. These are the only parts of the entry whose
   shape the desired behaviour constrains (mapping.md §2). -/
structure FieldEntry where
  nameNode : RefNode
  typeNode : RefNode
  deriving DecidableEq

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render one entry of an info field that documents a named item of a class
   together with its declared type — e.g. an entry like "an integer-typed item
   `name`". The modeled domain (the `require` clauses) is an entry whose NAME
   and TYPE are simple one-word identifiers, the TYPE not being the literal
   word `None` (see `isIdentChar`). Desired behaviour: the item NAME must be
   emitted as plain text with NO cross-reference, so that documenting an item
   inside a class never produces a spurious navigation link to an unrelated,
   identically-named item elsewhere in the project; the declared TYPE, by
   contrast, must remain a cross-reference to a class so that the type stays
   navigable. -/
method renderFieldEntry (name : List Char) (typ : List Char) return (out : FieldEntry)
  require name ≠ []
  require ∀ c ∈ name, isIdentChar c
  require typ ≠ []
  require ∀ c ∈ typ, isIdentChar c
  require typ ≠ "None".toList
  ensures out.nameNode = RefNode.text name
  ensures out.typeNode = RefNode.xref "class".toList typ
  do
    -- impl-start
    -- The item NAME carries no reference role: it is rendered as plain text and
    -- never becomes a cross-reference.
    let nameRole : Option (List Char) := none
    -- The declared TYPE keeps its class reference role (unchanged), so it stays
    -- a navigable cross-reference to a class.
    let typeRole : Option (List Char) := some "class".toList
    let nameNode := crossRefOrText nameRole name
    let typeNode := crossRefOrText typeRole typ
    return { nameNode := nameNode, typeNode := typeNode }
    -- impl-end

prove_correct renderFieldEntry by
  loom_solve <;> simp [crossRefOrText]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-8638 (velvet). Scratch: All 6 attacks + positive control are byte-identical spec (same_spec=True via swebench_unified.markers.same_spec, velvet). Verified with `bash scripts/lean_verify.sh <f>` (concurrent, <=4 jobs).

KEY SPEC FACT: renderFieldEntry's two `ensures` FULLY PIN the output (nameNode = text name, typeNode = xref "class" typ) on the entire modeled `require`-domain (non-empty isIdentChar names/types, typ != "None"). So every verifying impl is observationally IDENTICAL to gold in-domain; the discriminating adversarial vector is whether a verifying wrong impl's FAITHFUL refined patch still resolves.

### ATTACKS (verify result):
- atk_1 PREPATCH BUG (nameRole=some "obj") -> lean_verify exit=1, FAILS CLOSED on ensures_1 (goal reduces to False). Correct: reproduces the pre-patch rolename='obj' cross-reference; prepatch_reproduced=true.
- atk_2 ungrounded-oracle echo (returns postcondition values directly, bypasses crossRefOrText) -> exit=0 verifies.
- atk_3 EMPTY-ROLE variant (nameRole=some []) -> exit=0 verifies. THE distinct faithful patch: rolename='' instead of removing the kwarg.
- atk_4 control-flow-effect (branch on excluded name=[] case) -> exit=0 verifies.
- atk_5 boundary/wrong-domain (typeRole special-cases typ="None", excluded by require) -> exit=0 verifies (needed simp_all in the ELIDED proof region; spec bytes unchanged, same_spec still True).
- atk_6 truthy-then-discarded nameRole=some "data" but emits text -> exit=0 verifies.
- atk_pc correct impl (unchanged Solution) -> exit=0 verifies (positive control).

MATERIALIZED FAITHFUL PATCHES + run_resolve (official harness, swebench_unified.harness.run_resolve, timeout=1800):
- patch_gold.diff (remove rolename='obj') = faithful patch for atk_2/atk_4/atk_5/atk_6 (all gold-equivalent in-domain): RESULT resolved=True completed=True note='resolved' flaky=False.
- patch_atk3.diff (rolename='') = faithful patch for atk_3: RESULT resolved=True completed=True note='resolved' flaky=False.
Both git apply --check CLEAN at base_commit (worktree). The atk_3 empty-role patch RESOLVES because Field.make_xref (sphinx/util/docfields.py:63-72) guards with `if not rolename:` — '' is falsy, identical behaviour to None. So the require-domain modeling is FAITHFUL: even the most divergent same-spec faithful patch resolves. No verifying attack's faithful patch fails to resolve => verify DOES imply correct here.

REFINEMENT.MD AUDIT: legs A1/A2 = R (str<->List Char + domain-pinning requires); A3/A4 = R+I (role<->Option, concrete values); A5/A6 = A-reference + I. The A-reference (crossRefOrText deep-models the UNCHANGED Field.make_xref) was confirmed against real source at base_commit: `if not rolename` -> plain text node; truthy role -> pending_xref of that reftype/reftarget. Correspondence HOLDS. No kind-3 (inexpressible-changed-op) legs; the single changed value (NAME role) is modeled deeply (A3/A5), not hidden behind an axiom about the function under change. mapping.md §2 correctly excludes the three unchanged orthogonal behaviours (None type-role rewrite, '.'/'~' prefix strip, delimiter split) via the require clauses.

VERDICT: SOUND. 6 same-spec attacks run; prepatch fails closed; all 5 verifying wrong impls' materialized faithful patches were RUN through the official harness and every one RESOLVED. No verify-but-not-correct witness found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| does not verify against this specification, so the specification excludes it | 1 | `atk_1.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The rendering decision that turns a documented field's
   argument into a node — emit a cross-reference when a reference role is
   configured for that argument, otherwise emit a plain inline text node — is
   modeled DEEPLY in the `pure` region (`crossRefOrText`). It is the faithful
   model of an UNCHANGED standard inline-rendering helper, validated against the
   real helper by axiom_check.py (G-AX) as a deep-model reference (mapping.md
   §3); there is no module-level `axiom` the proof consumes. -/
-- axioms-end

-- pure-start
/- The two shapes an inline node can take in a rendered documentation field
   entry. `text` is a plain inline node carrying its content verbatim (no
   navigation target attached); `xref` is a pending cross-reference of a given
   reference kind to a target. The only distinction the desired behaviour cares
   about is whether a navigable cross-reference was produced (mapping.md §2). -/
inductive RefNode where
  | text (content : List Char)
  | xref (refkind : List Char) (target : List Char)
  deriving DecidableEq

/- The rendering decision for one argument of a documentation field: if a
   non-empty reference role is configured for that argument, the argument is
   turned into a pending cross-reference of that kind to itself; otherwise it is
   emitted as a plain inline text node with no navigation target. This is the
   standard inline-rendering rule (deep model of an unchanged helper, mapping.md
   §3.1). -/
def crossRefOrText (refrole : Option (List Char)) (target : List Char) : RefNode :=
  match refrole with
  | none   => RefNode.text target
  | some r => if r = [] then RefNode.text target else RefNode.xref r target

/- A plain-name character: a letter, a digit or an underscore. Pins the modeled
   input domain to simple one-word names/types (e.g. `attr`, `int`, `MyClass`).
   Composite type expressions (bracketed/comma/'or'-joined lists of types),
   abbreviation-prefixed targets (leading '.'/'~') and the literal word `None`
   are rendered through unchanged list-splitting / prefix-stripping /
   special-casing machinery that is orthogonal to this change and produces a
   different entry shape, so they are outside the modeled domain (mapping.md
   §2). -/
def isIdentChar (c : Char) : Bool := c.isAlpha || c.isDigit || c = '_'
-- pure-end

/- The observable content of one rendered entry of an info field documenting a
   named item together with its type: the node produced for the item's NAME and
   the node produced for its TYPE. These are the only parts of the entry whose
   shape the desired behaviour constrains (mapping.md §2). -/
structure FieldEntry where
  nameNode : RefNode
  typeNode : RefNode
  deriving DecidableEq

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render one entry of an info field that documents a named item of a class
   together with its declared type — e.g. an entry like "an integer-typed item
   `name`". The modeled domain (the `require` clauses) is an entry whose NAME
   and TYPE are simple one-word identifiers, the TYPE not being the literal
   word `None` (see `isIdentChar`). Desired behaviour: the item NAME must be
   emitted as plain text with NO cross-reference, so that documenting an item
   inside a class never produces a spurious navigation link to an unrelated,
   identically-named item elsewhere in the project; the declared TYPE, by
   contrast, must remain a cross-reference to a class so that the type stays
   navigable. -/
method renderFieldEntry (name : List Char) (typ : List Char) return (out : FieldEntry)
  require name ≠ []
  require ∀ c ∈ name, isIdentChar c
  require typ ≠ []
  require ∀ c ∈ typ, isIdentChar c
  require typ ≠ "None".toList
  ensures out.nameNode = RefNode.text name
  ensures out.typeNode = RefNode.xref "class".toList typ
  do
    -- impl-start
    -- The item NAME carries no reference role: it is rendered as plain text and
    -- never becomes a cross-reference.
    let nameRole : Option (List Char) := none
    -- The declared TYPE keeps its class reference role (unchanged), so it stays
    -- a navigable cross-reference to a class.
    let typeRole : Option (List Char) := some "class".toList
    let nameNode := crossRefOrText nameRole name
    let typeNode := crossRefOrText typeRole typ
    return { nameNode := nameNode, typeNode := typeNode }
    -- impl-end

prove_correct renderFieldEntry by
  loom_solve <;> simp [crossRefOrText]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-8638 (velvet). Scratch: All 6 attacks + positive control are byte-identical spec (same_spec=True via swebench_unified.markers.same_spec, velvet). Verified with `bash scripts/lean_verify.sh <f>` (concurrent, <=4 jobs).

KEY SPEC FACT: renderFieldEntry's two `ensures` FULLY PIN the output (nameNode = text name, typeNode = xref "class" typ) on the entire modeled `require`-domain (non-empty isIdentChar names/types, typ != "None"). So every verifying impl is observationally IDENTICAL to gold in-domain; the discriminating adversarial vector is whether a verifying wrong impl's FAITHFUL refined patch still resolves.

### ATTACKS (verify result):
- atk_1 PREPATCH BUG (nameRole=some "obj") -> lean_verify exit=1, FAILS CLOSED on ensures_1 (goal reduces to False). Correct: reproduces the pre-patch rolename='obj' cross-reference; prepatch_reproduced=true.
- atk_2 ungrounded-oracle echo (returns postcondition values directly, bypasses crossRefOrText) -> exit=0 verifies.
- atk_3 EMPTY-ROLE variant (nameRole=some []) -> exit=0 verifies. THE distinct faithful patch: rolename='' instead of removing the kwarg.
- atk_4 control-flow-effect (branch on excluded name=[] case) -> exit=0 verifies.
- atk_5 boundary/wrong-domain (typeRole special-cases typ="None", excluded by require) -> exit=0 verifies (needed simp_all in the ELIDED proof region; spec bytes unchanged, same_spec still True).
- atk_6 truthy-then-discarded nameRole=some "data" but emits text -> exit=0 verifies.
- atk_pc correct impl (unchanged Solution) -> exit=0 verifies (positive control).

MATERIALIZED FAITHFUL PATCHES + run_resolve (official harness, swebench_unified.harness.run_resolve, timeout=1800):
- patch_gold.diff (remove rolename='obj') = faithful patch for atk_2/atk_4/atk_5/atk_6 (all gold-equivalent in-domain): RESULT resolved=True completed=True note='resolved' flaky=False.
- patch_atk3.diff (rolename='') = faithful patch for atk_3: RESULT resolved=True completed=True note='resolved' flaky=False.
Both git apply --check CLEAN at base_commit (worktree). The atk_3 empty-role patch RESOLVES because Field.make_xref (sphinx/util/docfields.py:63-72) guards with `if not rolename:` — '' is falsy, identical behaviour to None. So the require-domain modeling is FAITHFUL: even the most divergent same-spec faithful patch resolves. No verifying attack's faithful patch fails to resolve => verify DOES imply correct here.

REFINEMENT.MD AUDIT: legs A1/A2 = R (str<->List Char + domain-pinning requires); A3/A4 = R+I (role<->Option, concrete values); A5/A6 = A-reference + I. The A-reference (crossRefOrText deep-models the UNCHANGED Field.make_xref) was confirmed against real source at base_commit: `if not rolename` -> plain text node; truthy role -> pending_xref of that reftype/reftarget. Correspondence HOLDS. No kind-3 (inexpressible-changed-op) legs; the single changed value (NAME role) is modeled deeply (A3/A5), not hidden behind an axiom about the function under change. mapping.md §2 correctly excludes the three unchanged orthogonal behaviours (None type-role rewrite, '.'/'~' prefix strip, delimiter split) via the require clauses.

VERDICT: SOUND. 6 same-spec attacks run; prepatch fails closed; all 5 verifying wrong impls' materialized faithful patches were RUN through the official harness and every one RESOLVED. No verify-but-not-correct witness found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) audit for velvet renderFieldEntry vs real PyTypedField('variable',…) rendering @ base_commit 4b452338f.

Spec region byte-identical: same_spec(Solution, Solution_prepatch, velvet)=True; Solution.lean verifies (exit 0).

Spec ensures (domain: name/typ nonempty, all isIdentChar, typ≠"None"):
  out.nameNode = RefNode.text name;  out.typeNode = RefNode.xref "class" typ.

Real callee trace: NAME via make_xrefs(self.rolename=None) → Field.make_xref `if not rolename` → plain literal_strong text (=text name). TYPE via make_xrefs(self.typerolename='class') → PyTypedField.make_xref; the class/'None'→obj special-case is excluded by require typ≠"None", and PyXrefMixin's '.'/'~' prefix-strip + [\[\](),]/or delimiter-split are excluded by isIdentChar (single node) → pending_xref reftype='class' reftarget=typ (=xref "class" typ). Both clauses match.

Empirical: ran the actual base-repo make_xrefs (jinja2<3.1 venv) against the spec ensures over boundary cases + 200k fuzzed inputs from the exact modeled domain ([A-Za-z0-9_]+, None→None_), asserting single-node counts and (kind,reftype,reftarget)/text content. 0 disagreements. The three excluded behaviors are unchanged pre/post patch and lie strictly outside the require domain, so the single-xref model is not too strong. No diverging input found → FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: judged the consumer spec view (swebench_unified.markers.spec_view over Solution.lean under VelvetBackend, impl + prove_correct bodies elided) against the public problem_statement only; mapping.md/refinement.md are audit-side and out of scope.

Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean) = True — the spec region is byte-identical pre/post-patch; only the elided impl differs. Mechanical G-LEAK lexical screen passes (hard_failures: []).

Gold edit: remove `rolename='obj'` from PyTypedField('variable', ...) in sphinx/domains/python.py so the variable NAME renders as plain text (no cross-reference) while the TYPE stays a `class` xref.

Public problem_statement already states the desired behavior explicitly: class/instance variable documentation should NOT be auto-linked to other same-named variables ("That the class variable documentation not be linked to any other").

Spec view content is a generic behavioral abstraction: ensures out.nameNode = RefNode.text name (NAME is plain text, no xref) and ensures out.typeNode = RefNode.xref "class".toList typ (TYPE stays a class xref). The name-not-linked observable is exactly the behavior the problem_statement requests, so restating it is legitimate spec work, not leakage; the type-preservation clause constrains only unchanged behavior and does not reveal the edit (which concerns the NAME role).

Reconstruction check: none of the gold-patch identifiers appear anywhere in the spec view — verified absent: rolename, obj, PyTypedField, make_xref, docfields, python.py, pending_xref, variable, autodoc/apidoc (the only 'diff' substring is inside the word 'different'). The view names no Sphinx internal, file, line, or the removed keyword. A consumer sees the desired node-shape behavior (already implied by the problem_statement) but cannot localize WHICH code to change. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
