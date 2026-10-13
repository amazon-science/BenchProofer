# P2 adversarial audit — sphinx-doc__sphinx-8638

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a fully-pinned pointwise equality (result = strong name :: (some t => text " (" :: xref "class" (emph t) :: text ")" :: text " -- " :: content | none => text " -- " :: content)). Every closing impl is extensionally equal to gold on all inputs; the only closing attack (atk_7) resolves.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
     (name : String) (type? : Option String) (content : List RenderNode) :
     List RenderNode := Id.run do
   -- The configured cross-reference role for a variable NAME (empty: no link).
-  let nameRole : String := ""
+  let nameRole : String := "obj"
   let mut par : List RenderNode := []
   par := par ++ [makeXref nameRole (RenderNode.strong name)]
   match type? with
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,6 @@
 def implementation_renderVariableItem
     (name : String) (type? : Option String) (content : List RenderNode) :
     List RenderNode := Id.run do
-  -- The configured cross-reference role for a variable NAME (empty: no link).
   let nameRole : String := ""
   let mut par : List RenderNode := []
   par := par ++ [makeXref nameRole (RenderNode.strong name)]
@@ -87,8 +86,10 @@
       par := par ++ [RenderNode.text " ("]
       par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
       par := par ++ [RenderNode.text ")"]
-  | none => pure ()
-  par := par ++ [RenderNode.text " -- "]
+      par := par ++ [RenderNode.text " -- "]
+  | none =>
+      -- BUG: forget the separator entirely for the no-type case
+      pure ()
   par := par ++ content
   return par
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,7 +88,7 @@
       par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
       par := par ++ [RenderNode.text ")"]
   | none => pure ()
-  par := par ++ [RenderNode.text " -- "]
+  par := par ++ [RenderNode.text " - "]
   par := par ++ content
   return par
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,17 +78,16 @@
 def implementation_renderVariableItem
     (name : String) (type? : Option String) (content : List RenderNode) :
     List RenderNode := Id.run do
-  -- The configured cross-reference role for a variable NAME (empty: no link).
   let nameRole : String := ""
   let mut par : List RenderNode := []
   par := par ++ [makeXref nameRole (RenderNode.strong name)]
+  par := par ++ [RenderNode.text " -- "]
   match type? with
   | some t =>
       par := par ++ [RenderNode.text " ("]
       par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
       par := par ++ [RenderNode.text ")"]
   | none => pure ()
-  par := par ++ [RenderNode.text " -- "]
   par := par ++ content
   return par
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,14 +78,14 @@
 def implementation_renderVariableItem
     (name : String) (type? : Option String) (content : List RenderNode) :
     List RenderNode := Id.run do
-  -- The configured cross-reference role for a variable NAME (empty: no link).
   let nameRole : String := ""
   let mut par : List RenderNode := []
   par := par ++ [makeXref nameRole (RenderNode.strong name)]
   match type? with
   | some t =>
       par := par ++ [RenderNode.text " ("]
-      par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
+      -- BUG: type role wrong ("obj" not "class")
+      par := par ++ [makeXref "obj" (RenderNode.emph t)]
       par := par ++ [RenderNode.text ")"]
   | none => pure ()
   par := par ++ [RenderNode.text " -- "]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,9 @@
 def implementation_renderVariableItem
     (name : String) (type? : Option String) (content : List RenderNode) :
     List RenderNode := Id.run do
-  -- The configured cross-reference role for a variable NAME (empty: no link).
   let nameRole : String := ""
   let mut par : List RenderNode := []
-  par := par ++ [makeXref nameRole (RenderNode.strong name)]
+  par := par ++ [makeXref nameRole (RenderNode.emph name)]
   match type? with
   | some t =>
       par := par ++ [RenderNode.text " ("]
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -77,20 +77,13 @@
 -- impl-start
 def implementation_renderVariableItem
     (name : String) (type? : Option String) (content : List RenderNode) :
-    List RenderNode := Id.run do
-  -- The configured cross-reference role for a variable NAME (empty: no link).
-  let nameRole : String := ""
-  let mut par : List RenderNode := []
-  par := par ++ [makeXref nameRole (RenderNode.strong name)]
+    List RenderNode :=
   match type? with
   | some t =>
-      par := par ++ [RenderNode.text " ("]
-      par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
-      par := par ++ [RenderNode.text ")"]
-  | none => pure ()
-  par := par ++ [RenderNode.text " -- "]
-  par := par ++ content
-  return par
+      [RenderNode.strong name, RenderNode.text " (",
+       RenderNode.xref "class" (RenderNode.emph t), RenderNode.text ")",
+       RenderNode.text " -- "] ++ content
+  | none => RenderNode.strong name :: RenderNode.text " -- " :: content
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,6 @@
 def implementation_renderVariableItem
     (name : String) (type? : Option String) (content : List RenderNode) :
     List RenderNode := Id.run do
-  -- The configured cross-reference role for a variable NAME (empty: no link).
   let nameRole : String := ""
   let mut par : List RenderNode := []
   par := par ++ [makeXref nameRole (RenderNode.strong name)]
@@ -90,6 +89,7 @@
   | none => pure ()
   par := par ++ [RenderNode.text " -- "]
   par := par ++ content
+  par := par ++ content  -- BUG: duplicate description
   return par
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering of a single documented-variable info-field item into the inline
node sequence that appears in the field body.

An item carries a name, an optional type token, and a description fragment.
The renderer emits, in order: the name token, then — when a type is present —
a parenthesized type token (linkable via the type cross-reference role), then a
separator, then the description.

A *cross-reference role* is the rule that decides whether a token is wrapped in
a navigable cross-reference or emitted as a plain strong/emphasis token: an
empty role yields a plain token; a non-empty role wraps the plain token in a
cross-reference carrying that role as its reference type.

For a documented variable, the name token must stand on its own — it is not a
navigable cross-reference to anything else — while its type token remains a
class cross-reference. The renderer applies the variable name role and the type
role accordingly.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The role-application helper
-- `makeXref` below is modeled deeply (A-reference, validated against the real
-- callee by G-AX), so no `opaque`/`axiom` declarations are required.
-- axioms-end

-- pure-start

/-- An inline node in the rendered field body. -/
inductive RenderNode where
  | text   : String → RenderNode
  | strong : String → RenderNode
  | emph   : String → RenderNode
  | xref   : String → RenderNode → RenderNode
  deriving DecidableEq, Repr

/-- Apply a cross-reference role to a plain inline token.
An empty role leaves the token plain; a non-empty role wraps it in a
cross-reference whose reference type is the role. Mirrors the unchanged
role-application callee (A-reference; G-AX validated). -/
def makeXref (role : String) (plain : RenderNode) : RenderNode :=
  if role = "" then plain else RenderNode.xref role plain

/-- The cross-reference role applied to a documented variable's TYPE token.
This is unchanged: a type token always links to its class. -/
def variableTypeRole : String := "class"

-- pure-end

-- post-conditions-start
/-- Specification of rendering one documented-variable item.

`name` is the variable name, `type?` the optional type token, `content` the
description fragment. The result must be exactly: a PLAIN strong name token
(the variable name is NOT a navigable cross-reference), followed — only when a
type is present — by `" ("`, the type token rendered as a class cross-reference
over an emphasis token, `")"`, then the separator `" -- "` and the description;
and when no type is present, just the plain name token, separator and
description. Every component is pinned to its input (frame discipline): exact
order, no extra nodes, and the name token carries no cross-reference. -/
def problem_spec_renderVariableItem
    (name : String) (type? : Option String) (content : List RenderNode)
    (result : List RenderNode) : Prop :=
  result =
    RenderNode.strong name ::
      (match type? with
       | some t =>
           RenderNode.text " (" ::
             RenderNode.xref variableTypeRole (RenderNode.emph t) ::
             RenderNode.text ")" :: RenderNode.text " -- " :: content
       | none => RenderNode.text " -- " :: content)
-- post-conditions-end

-- impl-start
def implementation_renderVariableItem
    (name : String) (type? : Option String) (content : List RenderNode) :
    List RenderNode := Id.run do
  -- The configured cross-reference role for a variable NAME (empty: no link).
  let nameRole : String := ""
  let mut par : List RenderNode := []
  par := par ++ [makeXref nameRole (RenderNode.strong name)]
  match type? with
  | some t =>
      par := par ++ [RenderNode.text " ("]
      par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
      par := par ++ [RenderNode.text ")"]
  | none => pure ()
  par := par ++ [RenderNode.text " -- "]
  par := par ++ content
  return par
-- impl-end

-- proof-start
theorem correct_renderVariableItem :
    ∀ (name : String) (type? : Option String) (content : List RenderNode),
      problem_spec_renderVariableItem name type? content
        (implementation_renderVariableItem name type? content) := by
  intro name type? content
  unfold problem_spec_renderVariableItem implementation_renderVariableItem
  cases type? with
  | none => rfl
  | some t => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

EXACT-EQUALITY SPEC. same_spec=True for all 8 attacks (checked via swebench_unified.markers.same_spec, lean backend). Positive control (gold Solution.lean) verifies (exit 0) and #print axioms = 'does not depend on any axioms'.

All commands run with; verify = `bash scripts/lean_verify.sh <file>`.

### ATTACKS (all same-spec, impl-region-only edits):
- atk_1 (prepatch bug, nameRole:="obj" -> head becomes xref "obj" (strong name)): exit 1 (rfl fails, goal reduces to xref..=strong.. -> False). PREPATCH REPRODUCED.
- atk_2 (partial-domain: drop " -- " separator on none branch): exit 1.
- atk_3 (boundary: separator " - " instead of " -- "): exit 1.
- atk_4 (control-flow-effect: separator+... reordered before type block): exit 1.
- atk_5 (ungrounded-oracle echo: wrong TYPE role "obj" not "class"): exit 1.
- atk_6 (wrong node kind: name emph instead of strong): exit 1.
- atk_8 (frame violation: content appended twice): exit 1.
- atk_7 (extensionally-equal echo: direct match construction bypassing makeXref/Id.run): exit 0, #print axioms clean ('does not depend on any axioms').

MANDATORY RESOLVE on the ONE closing clean-axiom attack (atk_7): its faithful patch = gold patch (atk_7 is extensionally identical to gold: plain strong name head, type xref "class", pinned separators/order/content). Ran run_resolve('sphinx-doc__sphinx-8638', patch, timeout=1800): RESOLVED=True COMPLETED=True note='resolved'. FAIL_TO_PASS test_info_field_list_var success; all 34 PASS_TO_PASS success; 0 failures. => verify AND correct coincide; no verify=>NOT correct break.

### A-LEG AUDIT (real repo @ base_commit 4b452338f914d4f6b54704222d70ae8a746e3db5, worktree):
- Field.make_xref (sphinx/util/docfields.py): `if not rolename: return contnode or innernode(target,target)` else `pending_xref(reftype=rolename)[innernode]`. Name/type calls pass no contnode -> innernode(target,target) branch. Modeled EXACTLY by makeXref role plain = if role="" then plain else xref role plain. Faithful A-reference (no consumed axiom).
- handle_item (TypedField.make_field): name via make_xrefs(self.rolename, .., literal_strong); if fieldarg in types: Text(' ('), make_xrefs(typerolename='class', .., literal_emphasis), Text(')'); Text(' -- '); content. Single-Text-type branch (len==1 & Text) matches Option String model (F2P scenario); multi-node type `else: par += fieldtype` is faithfully outside modeled domain. can_collapse=True + single item -> handle_item used directly. Op-for-op match.
- python.py:354: pre-patch rolename='obj'; gold drops it -> None (falsy). R-leg "obj"->"" <-> Python None correct.
- refinement.md legs: op#1=R (config bijection), rows 2&4=A-reference (makeXref), rows 2-8 I. A-consumed: none. No kind-3 legs. axiom_check.py = legitimate skip stub (no consumed callee axiom; make_xref is A-reference validated by G-CONF). #print axioms clean on both pos_control and atk_7.

CONCLUSION: {impls that close} == {impls extensionally equal to gold} == {impls whose faithful patch resolves}. The single deviating-structure closing impl (atk_7) resolves; all 6 genuinely-wrong impls + prepatch bug fail to close. No closing-but-non-resolving impl exists. verify=>correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a fully-pinned pointwise equality (result = strong name :: (some t => text " (" :: xref "class" (emph t) :: text ")" :: text " -- " :: content | none => text " -- " :: content)). Every closing impl is extensionally equal to gold on all inputs; the only closing attack (atk_7) resolves.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering of a single documented-variable info-field item into the inline
node sequence that appears in the field body.

An item carries a name, an optional type token, and a description fragment.
The renderer emits, in order: the name token, then — when a type is present —
a parenthesized type token (linkable via the type cross-reference role), then a
separator, then the description.

A *cross-reference role* is the rule that decides whether a token is wrapped in
a navigable cross-reference or emitted as a plain strong/emphasis token: an
empty role yields a plain token; a non-empty role wraps the plain token in a
cross-reference carrying that role as its reference type.

For a documented variable, the name token must stand on its own — it is not a
navigable cross-reference to anything else — while its type token remains a
class cross-reference. The renderer applies the variable name role and the type
role accordingly.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The role-application helper
-- `makeXref` below is modeled deeply (A-reference, validated against the real
-- callee by G-AX), so no `opaque`/`axiom` declarations are required.
-- axioms-end

-- pure-start

/-- An inline node in the rendered field body. -/
inductive RenderNode where
  | text   : String → RenderNode
  | strong : String → RenderNode
  | emph   : String → RenderNode
  | xref   : String → RenderNode → RenderNode
  deriving DecidableEq, Repr

/-- Apply a cross-reference role to a plain inline token.
An empty role leaves the token plain; a non-empty role wraps it in a
cross-reference whose reference type is the role. Mirrors the unchanged
role-application callee (A-reference; G-AX validated). -/
def makeXref (role : String) (plain : RenderNode) : RenderNode :=
  if role = "" then plain else RenderNode.xref role plain

/-- The cross-reference role applied to a documented variable's TYPE token.
This is unchanged: a type token always links to its class. -/
def variableTypeRole : String := "class"

-- pure-end

-- post-conditions-start
/-- Specification of rendering one documented-variable item.

`name` is the variable name, `type?` the optional type token, `content` the
description fragment. The result must be exactly: a PLAIN strong name token
(the variable name is NOT a navigable cross-reference), followed — only when a
type is present — by `" ("`, the type token rendered as a class cross-reference
over an emphasis token, `")"`, then the separator `" -- "` and the description;
and when no type is present, just the plain name token, separator and
description. Every component is pinned to its input (frame discipline): exact
order, no extra nodes, and the name token carries no cross-reference. -/
def problem_spec_renderVariableItem
    (name : String) (type? : Option String) (content : List RenderNode)
    (result : List RenderNode) : Prop :=
  result =
    RenderNode.strong name ::
      (match type? with
       | some t =>
           RenderNode.text " (" ::
             RenderNode.xref variableTypeRole (RenderNode.emph t) ::
             RenderNode.text ")" :: RenderNode.text " -- " :: content
       | none => RenderNode.text " -- " :: content)
-- post-conditions-end

-- impl-start
def implementation_renderVariableItem
    (name : String) (type? : Option String) (content : List RenderNode) :
    List RenderNode := Id.run do
  -- The configured cross-reference role for a variable NAME (empty: no link).
  let nameRole : String := ""
  let mut par : List RenderNode := []
  par := par ++ [makeXref nameRole (RenderNode.strong name)]
  match type? with
  | some t =>
      par := par ++ [RenderNode.text " ("]
      par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
      par := par ++ [RenderNode.text ")"]
  | none => pure ()
  par := par ++ [RenderNode.text " -- "]
  par := par ++ content
  return par
-- impl-end

-- proof-start
theorem correct_renderVariableItem :
    ∀ (name : String) (type? : Option String) (content : List RenderNode),
      problem_spec_renderVariableItem name type? content
        (implementation_renderVariableItem name type? content) := by
  intro name type? content
  unfold problem_spec_renderVariableItem implementation_renderVariableItem
  cases type? with
  | none => rfl
  | some t => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

EXACT-EQUALITY SPEC. same_spec=True for all 8 attacks (checked via swebench_unified.markers.same_spec, lean backend). Positive control (gold Solution.lean) verifies (exit 0) and #print axioms = 'does not depend on any axioms'.

All commands run with; verify = `bash scripts/lean_verify.sh <file>`.

### ATTACKS (all same-spec, impl-region-only edits):
- atk_1 (prepatch bug, nameRole:="obj" -> head becomes xref "obj" (strong name)): exit 1 (rfl fails, goal reduces to xref..=strong.. -> False). PREPATCH REPRODUCED.
- atk_2 (partial-domain: drop " -- " separator on none branch): exit 1.
- atk_3 (boundary: separator " - " instead of " -- "): exit 1.
- atk_4 (control-flow-effect: separator+... reordered before type block): exit 1.
- atk_5 (ungrounded-oracle echo: wrong TYPE role "obj" not "class"): exit 1.
- atk_6 (wrong node kind: name emph instead of strong): exit 1.
- atk_8 (frame violation: content appended twice): exit 1.
- atk_7 (extensionally-equal echo: direct match construction bypassing makeXref/Id.run): exit 0, #print axioms clean ('does not depend on any axioms').

MANDATORY RESOLVE on the ONE closing clean-axiom attack (atk_7): its faithful patch = gold patch (atk_7 is extensionally identical to gold: plain strong name head, type xref "class", pinned separators/order/content). Ran run_resolve('sphinx-doc__sphinx-8638', patch, timeout=1800): RESOLVED=True COMPLETED=True note='resolved'. FAIL_TO_PASS test_info_field_list_var success; all 34 PASS_TO_PASS success; 0 failures. => verify AND correct coincide; no verify=>NOT correct break.

### A-LEG AUDIT (real repo @ base_commit 4b452338f914d4f6b54704222d70ae8a746e3db5, worktree):
- Field.make_xref (sphinx/util/docfields.py): `if not rolename: return contnode or innernode(target,target)` else `pending_xref(reftype=rolename)[innernode]`. Name/type calls pass no contnode -> innernode(target,target) branch. Modeled EXACTLY by makeXref role plain = if role="" then plain else xref role plain. Faithful A-reference (no consumed axiom).
- handle_item (TypedField.make_field): name via make_xrefs(self.rolename, .., literal_strong); if fieldarg in types: Text(' ('), make_xrefs(typerolename='class', .., literal_emphasis), Text(')'); Text(' -- '); content. Single-Text-type branch (len==1 & Text) matches Option String model (F2P scenario); multi-node type `else: par += fieldtype` is faithfully outside modeled domain. can_collapse=True + single item -> handle_item used directly. Op-for-op match.
- python.py:354: pre-patch rolename='obj'; gold drops it -> None (falsy). R-leg "obj"->"" <-> Python None correct.
- refinement.md legs: op#1=R (config bijection), rows 2&4=A-reference (makeXref), rows 2-8 I. A-consumed: none. No kind-3 legs. axiom_check.py = legitimate skip stub (no consumed callee axiom; make_xref is A-reference validated by G-CONF). #print axioms clean on both pos_control and atk_7.

CONCLUSION: {impls that close} == {impls extensionally equal to gold} == {impls whose faithful patch resolves}. The single deviating-structure closing impl (atk_7) resolves; all 6 genuinely-wrong impls + prepatch bug fail to close. No closing-but-non-resolving impl exists. verify=>correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution, Solution_prepatch)=True (spec regions byte-identical; prepatch differs only in impl nameRole "obj" vs ""). Solution.lean compiles (lean_verify exit 0), proof correct_renderVariableItem depends on NO axioms (no sorryAx). Faithfulness verified by driving the REAL repo callee TypedField.make_field.handle_item at base_commit 4b452338 with the post-patch variable-field config (rolename=None dropped by gold, typerolename='class', can_collapse=True) and comparing the produced paragraph node list against problem_spec_renderVariableItem: 196 structured edge cases (names×types×contents incl. empty name/type) + 40,000 randomized fuzz cases over adversarial strings (empty, 'obj', unicode, markup chars, whitespace) => 0 divergences. Real callee: not-rolename branch -> plain literal_strong name (spec strong name); type -> pending_xref(reftype='class')[literal_emphasis] (spec xref 'class' (emph t)); ' -- ' separator + content passthrough all match. Modeled domain (single-Text type token, Option String) matches the F2P scenario per mapping.md; the multi-node type else-branch (par += fieldtype) is out of the modeled domain, not a divergence. Spec is not too strong: it pins exactly the post-patch callee output over the modeled domain. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view authenticity confirmed: markers.spec_view(Solution.lean, lean) hashes to b2bd1d54245152a976b2a3632acc25b24ee9be277418bb1ac02a70443c5cbda1, byte-identical to meta.json region_hashes.spec_view; same_spec(Solution,Solution_prepatch)=True and same_spec(self)=True (spec region genuine, differs from prepatch only in impl nameRole). Lexical G-LEAK screen passes (no hard failures). hints_text is empty, so the leakage baseline is problem_statement alone.

Gold edit = drop rolename='obj' from the variable PyTypedField at sphinx/domains/python.py:354 (one-line config removal; runtime effect: variable NAME cross-ref role becomes empty so Field.make_xref emits a plain literal_strong instead of a pending_xref; typerolename='class' unchanged).

Public problem_statement already discloses the SYMPTOM (instance variables 'link to' other same-named variables) and EXPECTED BEHAVIOR ('the class variable documentation not be linked to any other'). No file/line/symbol/mechanism appears in the public statement.

Spec-view reviewed line by line:
- Docstring prose ('the name token must stand on its own — it is not a navigable cross-reference to anything else — while its type token remains a class cross-reference') restates the public expected behavior; the cross-reference/link concept is intrinsic to the bug the public statement frames. Encoding correct behavior is the spec's legitimate job, not a leak.
- RenderNode inductive, makeXref helper, variableTypeRole := "class": abstract Lean model; variableTypeRole names the UNCHANGED type role, not the gold edit.
- problem_spec_renderVariableItem pins the correct output (plain RenderNode.strong name head, no xref). Specifying the correct contract is not disclosing the edit.

Critically ABSENT from the spec view: no sphinx/domains/python.py, no sphinx/util/docfields.py, no doc_field_types, no PyTypedField, no rolename='obj', no line 354, no framing as a config-entry removal. The localization (WHERE to edit; that it is a one-line config deletion) — the genuine solving work — is not revealed beyond the public statement. mapping.md/refinement.md/verdict.md (which DO name python.py:354 and rolename='obj') are NOT part of the spec view shown to a solver.

No spec-view line leaks the gold edit's file/line/symbol/mechanism beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
