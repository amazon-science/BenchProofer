# P2 adversarial audit — sphinx-doc__sphinx-9658

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_0_prepatch.lean`, `atk_1_armorder_typing_first.lean`, `atk_2_no_element_tail.lean`, `atk_3_singlerule_law.lean`, `atk_5_rule1_guard_or.lean`, `atk_6_only_core_a.lean`, `atk_7_no_abbrev_mark.lean`, `atk_8_partial_nonempty.lean`, `atk_9_rule1_py310_branch.lean`, `atk_12_name_is_modulepath.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_4_oracle_echo.lean`, `atk_10_echo_reportedname.lean`, `atk_11_core_before_newtype.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,10 +121,7 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
-    let simpleName := createdName
+    let simpleName : List Char := []
     if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
       return openMark ++ simpleName ++ closeMark
     else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
```

Attack 2 — `atk_1_armorder_typing_first.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,17 +121,12 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
     let simpleName := createdName
-    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
-      return openMark ++ simpleName ++ closeMark
+    if modulePath = abbreviatedNamespace then
+      return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
+               ++ closeMark
     else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
       return openMark ++ simpleName ++ closeMark ++ elementListTail
-    else if modulePath = abbreviatedNamespace then
-      return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
-               ++ closeMark
     else
       return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
     -- impl-end
```

Attack 3 — `atk_2_no_element_tail.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,14 +121,11 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
     let simpleName := createdName
     if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
       return openMark ++ simpleName ++ closeMark
     else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
-      return openMark ++ simpleName ++ closeMark ++ elementListTail
+      return openMark ++ simpleName ++ closeMark
     else if modulePath = abbreviatedNamespace then
       return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
                ++ closeMark
```

Attack 4 — `atk_3_singlerule_law.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,19 +121,8 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
     let simpleName := createdName
-    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
-      return openMark ++ simpleName ++ closeMark
-    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
-      return openMark ++ simpleName ++ closeMark ++ elementListTail
-    else if modulePath = abbreviatedNamespace then
-      return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
-               ++ closeMark
-    else
-      return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
+    return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
     -- impl-end
 
 prove_correct renderReference by
```

Attack 5 — `atk_4_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -121,19 +121,7 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
-    let simpleName := createdName
-    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
-      return openMark ++ simpleName ++ closeMark
-    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
-      return openMark ++ simpleName ++ closeMark ++ elementListTail
-    else if modulePath = abbreviatedNamespace then
-      return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
-               ++ closeMark
-    else
-      return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
+    return renderedReference modulePath createdName
     -- impl-end
 
 prove_correct renderReference by
```

Attack 6 — `atk_5_rule1_guard_or.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,11 +121,8 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
     let simpleName := createdName
-    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
+    if modulePath = abbreviatedNamespace ∨ simpleName = aliasFactoryName then
       return openMark ++ simpleName ++ closeMark
     else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
       return openMark ++ simpleName ++ closeMark ++ elementListTail
```

Attack 7 — `atk_6_only_core_a.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,13 +121,10 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
     let simpleName := createdName
     if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
       return openMark ++ simpleName ++ closeMark
-    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
+    else if modulePath = coreNamespaceA then
       return openMark ++ simpleName ++ closeMark ++ elementListTail
     else if modulePath = abbreviatedNamespace then
       return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
```

Attack 8 — `atk_7_no_abbrev_mark.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,17 +121,13 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
     let simpleName := createdName
     if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
       return openMark ++ simpleName ++ closeMark
     else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
       return openMark ++ simpleName ++ closeMark ++ elementListTail
     else if modulePath = abbreviatedNamespace then
-      return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
-               ++ closeMark
+      return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
     else
       return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
     -- impl-end
```

Attack 9 — `atk_8_partial_nonempty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,11 +121,10 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
     let simpleName := createdName
-    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
+    if simpleName = [] then
+      return openMark ++ modulePath ++ closeMark
+    else if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
       return openMark ++ simpleName ++ closeMark
     else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
       return openMark ++ simpleName ++ closeMark ++ elementListTail
```

Attack 10 — `atk_9_rule1_py310_branch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,12 +121,9 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
     let simpleName := createdName
     if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
-      return openMark ++ simpleName ++ closeMark
+      return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
     else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
       return openMark ++ simpleName ++ closeMark ++ elementListTail
     else if modulePath = abbreviatedNamespace then
```

Attack 11 — `atk_10_echo_reportedname.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -121,13 +121,10 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
-    let simpleName := createdName
-    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
-      return openMark ++ simpleName ++ closeMark
-    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
+    let simpleName := reportedName createdName
+    if modulePath = abbreviatedNamespace ∧ reportedName simpleName = aliasFactoryName then
+      return openMark ++ reportedName simpleName ++ closeMark
+    else if modulePath = coreNamespaceB ∨ modulePath = coreNamespaceA then
       return openMark ++ simpleName ++ closeMark ++ elementListTail
     else if modulePath = abbreviatedNamespace then
       return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
```

Attack 12 — `atk_11_core_before_newtype.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -121,14 +121,11 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
     let simpleName := createdName
-    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
+    if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
+      return openMark ++ simpleName ++ closeMark ++ elementListTail
+    else if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
       return openMark ++ simpleName ++ closeMark
-    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
-      return openMark ++ simpleName ++ closeMark ++ elementListTail
     else if modulePath = abbreviatedNamespace then
       return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
                ++ closeMark
```

Attack 13 — `atk_12_name_is_modulepath.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,10 +121,7 @@
       out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
   do
     -- impl-start
-    -- The placeholder's reported simple name is the name it was created to stand
-    -- for; the rendered reference places that name in the trailing position of
-    -- whichever of the renderer's four rules the module path selects.
-    let simpleName := createdName
+    let simpleName := modulePath
     if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
       return openMark ++ simpleName ++ closeMark
     else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behavior under specification is the rendering of a
--  stand-in placeholder symbol's reference from the data the placeholder carries;
--  it is modeled DEEPLY in the `pure` region below as a total function of its
--  inputs. Nothing outside the modeled rendering is consulted, so there is no
--  `axiom` declaration and no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- A stand-in placeholder symbol is created to stand for a name that could not
   be resolved. It carries two pieces of textual data:
     * `modulePath`  — the dotted module path it lives under;
     * `createdName` — the simple name it was created to stand for.

   The reported simple name of such a placeholder is exactly the name it was
   created to stand for: a placeholder created for a name reports that name, and
   a placeholder created with no name (the bare root placeholder) reports the
   empty name. -/
def reportedName (createdName : List Char) : List Char := createdName

/- The renderer that turns a symbol into a cross-reference does not treat every
   module path alike. Three module paths are reserved by it, and a placeholder
   living under one of them is rendered by a different rule than the general one.
   These are the reserved paths, and the one reserved simple name. -/
def coreNamespaceA : List Char :=
  ['_', '_', 'b', 'u', 'i', 'l', 't', 'i', 'n', '_', '_']
def coreNamespaceB : List Char := ['b', 'u', 'i', 'l', 't', 'i', 'n', 's']
def abbreviatedNamespace : List Char := ['t', 'y', 'p', 'i', 'n', 'g']
def aliasFactoryName : List Char :=
  ['N', 'e', 'w', 'T', 'y', 'p', 'e', '.', '<', 'l', 'o', 'c', 'a', 'l', 's',
   '>', '.', 'n', 'e', 'w', '_', 't', 'y', 'p', 'e']

/- The constant decorations the renderer places around the symbol text: the role
   marker it opens with, the mark it closes with, the element-list tail it adds
   for a path under a reserved core namespace, and the mark that abbreviates a
   path under the reserved abbreviated namespace. -/
def openMark : List Char := [':', 'p', 'y', ':', 'c', 'l', 'a', 's', 's', ':', '`']
def closeMark : List Char := ['`']
def elementListTail : List Char := ['\\', ' ', '[', ']']
def abbreviationMark : List Char := ['~']

/- The reference the renderer produces for a placeholder, as a function of the
   two pieces of data the placeholder carries. Four rules, tried in this order —
   the renderer consults the module path FIRST and only reaches the general
   dotted rule when the path is none of the reserved ones:

     1. the reserved abbreviated namespace together with the reserved simple
        name: the module path is dropped and only the reported simple name is
        rendered;
     2. a reserved core namespace: the module path is dropped, the reported
        simple name is rendered, and the element-list tail is appended;
     3. the reserved abbreviated namespace with any other simple name: the
        dotted path is rendered behind the abbreviation mark;
     4. any other module path: the dotted path is rendered plainly.

   In every one of the four rules the trailing segment is the reported simple
   name — the name the placeholder was created to stand for — so no rule drops
   it. -/
def renderedReference (modulePath createdName : List Char) : List Char :=
  if modulePath = abbreviatedNamespace ∧ reportedName createdName = aliasFactoryName then
    openMark ++ reportedName createdName ++ closeMark
  else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
    openMark ++ reportedName createdName ++ closeMark ++ elementListTail
  else if modulePath = abbreviatedNamespace then
    openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ reportedName createdName ++ closeMark
  else
    openMark ++ modulePath ++ ['.'] ++ reportedName createdName ++ closeMark

@[grind] lemma reportedName_eq (createdName : List Char) :
    reportedName createdName = createdName := rfl

@[grind] lemma renderedReference_general (modulePath createdName : List Char)
    (hA : modulePath ≠ coreNamespaceA) (hB : modulePath ≠ coreNamespaceB)
    (hT : modulePath ≠ abbreviatedNamespace) :
    renderedReference modulePath createdName
      = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark := by
  simp [renderedReference, reportedName, hA, hB, hT]

@[grind] lemma renderedReference_core (modulePath createdName : List Char)
    (h : modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB) :
    renderedReference modulePath createdName
      = openMark ++ createdName ++ closeMark ++ elementListTail := by
  rcases h with h | h <;> subst h <;>
    simp [renderedReference, reportedName, coreNamespaceA, coreNamespaceB,
          abbreviatedNamespace, aliasFactoryName]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the reference for a stand-in placeholder symbol. The rendering reads
   the placeholder's module path and the name it was created to stand for, and
   follows whichever of the renderer's four rules the module path selects; in
   every rule the trailing segment is the reported simple name, which is exactly
   the name the placeholder was created to stand for. Both inputs are read-only —
   neither is declared `mut` (directive 5): the rendering only reads the module
   path and the creation name and mutates nothing. -/
method renderReference (modulePath : List Char) (createdName : List Char)
    return (out : List Char)
  ensures out = renderedReference modulePath createdName
  ensures modulePath = abbreviatedNamespace → createdName = aliasFactoryName →
      out = openMark ++ createdName ++ closeMark
  ensures (modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB) →
      out = openMark ++ createdName ++ closeMark ++ elementListTail
  ensures modulePath = abbreviatedNamespace → createdName ≠ aliasFactoryName →
      out = openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ createdName
              ++ closeMark
  ensures modulePath ≠ coreNamespaceA → modulePath ≠ coreNamespaceB →
      modulePath ≠ abbreviatedNamespace →
      out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
  do
    -- impl-start
    -- The placeholder's reported simple name is the name it was created to stand
    -- for; the rendered reference places that name in the trailing position of
    -- whichever of the renderer's four rules the module path selects.
    let simpleName := createdName
    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
      return openMark ++ simpleName ++ closeMark
    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
      return openMark ++ simpleName ++ closeMark ++ elementListTail
    else if modulePath = abbreviatedNamespace then
      return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
               ++ closeMark
    else
      return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
    -- impl-end

prove_correct renderReference by
  loom_solve
  <;> intros
  <;> subst_vars
  <;> simp_all [renderedReference, reportedName, coreNamespaceA, coreNamespaceB,
                abbreviatedNamespace, aliasFactoryName]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity), sphinx-doc__sphinx-9658 velvet. VERDICT: SOUND. All work in  13 attacks + positive control, all same_spec TRUE against the shipped Solution.lean (velvet backend); positive control pos_control.lean verifies exit 0; prepatch REPRODUCED.

**STRUCTURAL FINDING THAT FRAMES EVERYTHING.** The frozen postcondition `out = renderedReference modulePath createdName` is a TOTAL FUNCTIONAL EQUALITY over an EMPTY pre-conditions region. So every verifying impl is extensionally identical to the deep model on the whole carrier `List Char x List Char` -- impl latitude is NIL. That means a verify-not-correct witness cannot come from impl freedom at all; the only live break vector is model<->reality (A-leg) infidelity, which is where I concentrated per my assignment.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <path>`, run 4-way concurrent):
- atk_0_prepatch (simpleName := []): exit 1, unsolved goals on ALL FIVE ensures_1..ensures_5 -- matches refinement.md's G-DIFF claim exactly.
- atk_1_armorder_typing_first (rule 3 hoisted above rule 1; attacks leg A5): exit 1 (ensures_4, ensures_5)
- atk_2_no_element_tail (rule 2 drops `\\ []`; attacks A4b): exit 1 (ensures_3, ensures_5)
- atk_3_singlerule_law (plain dotted join on EVERY path -- the old single-rule spec a prior G-PANEL-2 condemned, re-encoded): exit 1 (ensures_2/3/4/5)
- atk_5_rule1_guard_or (guard AND weakened to OR): exit 1 (ensures_1/2/3/5)
- atk_6_only_core_a ('builtins' dropped from rule 2 -- partial domain): exit 1 (ensures_3, ensures_5)
- atk_7_no_abbrev_mark (rule 3 drops '~'; attacks A4c): exit 1 (ensures_2, ensures_5)
- atk_8_partial_nonempty (correct only for nonempty createdName -- partial domain/boundary): exit 1 (ensures_1/2/3/5)
- atk_9_rule1_py310_branch (mis-ported rule 1: the py3.10+ arm that keeps the module path): exit 1 (ensures_4, ensures_5)
- atk_12_name_is_modulepath (ungrounded wrong oracle): exit 1 (all five)
- VERIFY (exit 0): atk_4_oracle_echo (ungrounded-oracle echo: returns renderedReference verbatim), atk_10_echo_reportedname (echo via reportedName indirection + reordered core disjuncts), atk_11_core_before_newtype (rule 2 hoisted above rule 1).

WHY THE THREE VERIFY, AND WHY THEY ARE NOT WITNESSES. equiv.py (54 boundary pairs incl. both reserved core paths, 'typing', near-misses, the reserved alias name and near-misses, empty strings) shows atk_10 and atk_11 are EXTENSIONALLY IDENTICAL to the frozen model: 0 divergences. atk_11's reordering is behaviour-preserving because rules 1 and 2 have DISJOINT guards ('typing' vs '`__builtin__`'/'builtins'), so hoisting rule 2 cannot steal a rule-1 input -- a real but non-discriminating control-flow permutation. atk_4/atk_10 are echoes. So all three ARE the gold rendering.

MANDATORY RESOLVE RUNS (executed, not speculated). Faithful refined patch for all three verifying attacks is the same mechanism (reported simple name := creation name), materialized at patch_A.diff, which coincides with the gold mock.py edit. Cmd: `python do_resolve.py <name> <patch>` calling `run_resolve('sphinx-doc__sphinx-9658', patch, timeout=1800)`.
- patch_A (atk_4/atk_10 shared mechanism): RESOLVED=True COMPLETED=True NOTE=resolved; F2P success ['tests/test_util_typing.py::test_restify_mock'], F2P failure [], P2P 24/24 success, 0 failures. Log: resolve_A.log
- atk_11 (re-run under its own name): RESOLVED=True COMPLETED=True NOTE=resolved; F2P success, P2P 24/24, 0 failures. Log: resolve_atk11.log
So every verifying wrong impl's faithful patch DOES resolve => no verify-not-correct witness.

A-LEG AUDIT (my assigned focus). meta.json axioms=[] and deep_model_references=[]; 0 `axiom` decls in Solution.lean; no sorry/admit/native_decide/Classical.choice. G-AX=skip is therefore correct -- there are NO kind-A contracts to trust. Instead restify's ENTIRE 4-way dispatch is a DEEP MODEL inside the frozen pure region, which moves the whole trust burden onto model<->reality fidelity. Two things had to hold and both do:

(a) The model is genuinely FROZEN, not attacker latitude. Three tampers each flip same_spec to FALSE: probe_tamper_model.lean (rule-4 arm drops the trailing name), probe_tamper_reported.lean (reportedName := []), probe_drop_ensures5.lean (delete ensures_5). So no attacker can weaken the model or the contract while keeping the consumer spec view.

(b) The model AGREES with the REAL patched restify. I built my own probe (fidelity.py) independent of the bundle's conformance_check.py, transliterating the frozen pure region directly, and ran it on the PINNED Python 3.9 (image g9658py39, Python 3.9.25 -- the version matters because isNewType branches on sys.version_info >= (3,10)) with my patched worktree on PYTHONPATH. Result: 696 hand-picked boundary/near-miss pairs (24 module paths x 29 names: both reserved core paths, 'typing', near-misses 'typings'/'`__builtins__`'/'builtin'/'a.typing'/'TYPING'/' typing'/'typing '/'typing.sub'/'sub.typing', the reserved alias name and 5 near-misses, empty strings, dunder names that could collide with the mock's own machinery, backtick/backslash/tilde/bracket/dot/space/newline injections, non-ASCII, 200-char names) + 60000 randomized inputs with reserved paths at weight ~0.30 and near-misses ~0.10 => 0 MISMATCHES, all four rules hit at real weight (1490/12041/4489/42676). Plus the literal F2P walk path (mock(['unknown']) + attribute access) matches the model, and walk-vs-direct cross-validation agrees.

**ONE DISCREPANCY I CHASED DOWN AND CLEARED.** My first probe run reported a walk-vs-direct mismatch at leaf '`__name__`' (walk gave 'sub', direct gave ':py:class:`mockroot9658x.sub.__name__`'). Diagnosed with diag.py: a class ALWAYS has a real `__name__`, so `__getattr__` never fires and getattr(sub,'`__name__`') returns the plain str 'sub' -- no placeholder is produced at all, so that input is OUTSIDE the modeled domain (the model speaks about placeholders). This is a probe artifact, not model infidelity; I restricted the walk leg to placeholder-producing leaves (asserted isinstance(`_MockObject`)) and the rerun is clean. Incidentally this same mechanism independently CONFIRMS mapping.md section 5's pre-patch rule-2 account (pre-patch cls.`__name__` resolves through `__getattr__` to a further placeholder whose repr is its `__display_name__`).

EXTRA FALSIFICATION FROM THE PATCH SIDE (since impl latitude is nil). I asked whether a DIFFERENT mechanism that is faithful on the modeled domain could still fail the harness. Built rival mechanism C (patch_C.diff: only `self.__qualname__ = type(self).__name__` in `__init__`, no `__name__` class attr, no `_make_subclass` change -- a genuinely different edit, 1 hunk vs gold's 3). RESOLVED=True COMPLETED=True, F2P success, P2P 24/24. So the spec's modeled behaviour does not secretly depend on gold's particular mechanism either.

**REFINEMENT.MD LEG AUDIT.** 8 legs, tags: A1=R, A2=R, A3=I, A4a=I+R, A4b=I+R, A4c=I+R, A4d=I+R, A5=I. Every leg is R or I -- NO kind-3 (inexpressible-changed-op), consistent with section C's claim. I checked each A-leg's correspondence against the real callees at base_commit in the git repo: A4a<->typing.py:119-125 isNewType arm with inspect.py:213-223's exact conjunctive test (`__module__`=='typing' AND `__qualname__`=='NewType.<locals>.new_type') -- confirmed, and confirmed the py<3.10 arm at :125 is the one the pinned 3.9 image takes; A4b<->typing.py:133-140 builtins arm incl. the hasattr(`__args__`) sub-branch, and I verified empirically that a placeholder's `__args__` iterates empty so the join is '' and the tail is the constant '\\ []' (this is the one input-independent-constant R step, and it holds on all 12041 rule-2 inputs); A4c/A4d<->`_restify_py37`'s hasattr(`__qualname__`) arm at typing.py:193-196 with the typing sub-branch preceding the else; A5 arm order <-> restify's elif chain order.

The A3 claim that post-patch `__name__` and `__qualname__` are the SAME string (so one modeled reportedName serves rule 2, which reads `__name__`, and rules 1/3/4, which read `__qualname__`) is correct on the patched tree and is what makes the single-function model sound.

**NOTE ON A PRIOR PASS'S STALE-GATE CONCERN:** meta.json now records G-PANEL-2 = pass, so the stale-verdict issue an earlier G-EQ flagged has been cleared; I re-encoded that panel's own counterexample anyway as atk_3_singlerule_law and it is REJECTED (ensures_2/3/4/5), so the repair demonstrably took.

**BOTTOM LINE:** 13 attacks encoded and verified (10 rejected on precisely-named ensures_k goals, 3 verify and are provably the gold rendering), all 3 verifying attacks' faithful patches RUN through the official harness and ALL RESOLVED, deep model empirically faithful to the real restify on 60696 inputs across all four rules on the pinned interpreter, pure region and contracts provably frozen, no axioms and no kind-3 legs. No verify-not-correct witness found. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_0_prepatch.lean`, `atk_1_armorder_typing_first.lean`, `atk_2_no_element_tail.lean`, `atk_3_singlerule_law.lean`, `atk_5_rule1_guard_or.lean`, `atk_6_only_core_a.lean`, `atk_7_no_abbrev_mark.lean`, `atk_8_partial_nonempty.lean`, `atk_9_rule1_py310_branch.lean`, `atk_12_name_is_modulepath.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_4_oracle_echo.lean`, `atk_10_echo_reportedname.lean`, `atk_11_core_before_newtype.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_armorder_typing_first.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2_no_element_tail.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_singlerule_law.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_5_rule1_guard_or.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_only_core_a.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7_no_abbrev_mark.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8_partial_nonempty.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9_rule1_py310_branch.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10_echo_reportedname.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_11_core_before_newtype.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_12_name_is_modulepath.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behavior under specification is the rendering of a
--  stand-in placeholder symbol's reference from the data the placeholder carries;
--  it is modeled DEEPLY in the `pure` region below as a total function of its
--  inputs. Nothing outside the modeled rendering is consulted, so there is no
--  `axiom` declaration and no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- A stand-in placeholder symbol is created to stand for a name that could not
   be resolved. It carries two pieces of textual data:
     * `modulePath`  — the dotted module path it lives under;
     * `createdName` — the simple name it was created to stand for.

   The reported simple name of such a placeholder is exactly the name it was
   created to stand for: a placeholder created for a name reports that name, and
   a placeholder created with no name (the bare root placeholder) reports the
   empty name. -/
def reportedName (createdName : List Char) : List Char := createdName

/- The renderer that turns a symbol into a cross-reference does not treat every
   module path alike. Three module paths are reserved by it, and a placeholder
   living under one of them is rendered by a different rule than the general one.
   These are the reserved paths, and the one reserved simple name. -/
def coreNamespaceA : List Char :=
  ['_', '_', 'b', 'u', 'i', 'l', 't', 'i', 'n', '_', '_']
def coreNamespaceB : List Char := ['b', 'u', 'i', 'l', 't', 'i', 'n', 's']
def abbreviatedNamespace : List Char := ['t', 'y', 'p', 'i', 'n', 'g']
def aliasFactoryName : List Char :=
  ['N', 'e', 'w', 'T', 'y', 'p', 'e', '.', '<', 'l', 'o', 'c', 'a', 'l', 's',
   '>', '.', 'n', 'e', 'w', '_', 't', 'y', 'p', 'e']

/- The constant decorations the renderer places around the symbol text: the role
   marker it opens with, the mark it closes with, the element-list tail it adds
   for a path under a reserved core namespace, and the mark that abbreviates a
   path under the reserved abbreviated namespace. -/
def openMark : List Char := [':', 'p', 'y', ':', 'c', 'l', 'a', 's', 's', ':', '`']
def closeMark : List Char := ['`']
def elementListTail : List Char := ['\\', ' ', '[', ']']
def abbreviationMark : List Char := ['~']

/- The reference the renderer produces for a placeholder, as a function of the
   two pieces of data the placeholder carries. Four rules, tried in this order —
   the renderer consults the module path FIRST and only reaches the general
   dotted rule when the path is none of the reserved ones:

     1. the reserved abbreviated namespace together with the reserved simple
        name: the module path is dropped and only the reported simple name is
        rendered;
     2. a reserved core namespace: the module path is dropped, the reported
        simple name is rendered, and the element-list tail is appended;
     3. the reserved abbreviated namespace with any other simple name: the
        dotted path is rendered behind the abbreviation mark;
     4. any other module path: the dotted path is rendered plainly.

   In every one of the four rules the trailing segment is the reported simple
   name — the name the placeholder was created to stand for — so no rule drops
   it. -/
def renderedReference (modulePath createdName : List Char) : List Char :=
  if modulePath = abbreviatedNamespace ∧ reportedName createdName = aliasFactoryName then
    openMark ++ reportedName createdName ++ closeMark
  else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
    openMark ++ reportedName createdName ++ closeMark ++ elementListTail
  else if modulePath = abbreviatedNamespace then
    openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ reportedName createdName ++ closeMark
  else
    openMark ++ modulePath ++ ['.'] ++ reportedName createdName ++ closeMark

@[grind] lemma reportedName_eq (createdName : List Char) :
    reportedName createdName = createdName := rfl

@[grind] lemma renderedReference_general (modulePath createdName : List Char)
    (hA : modulePath ≠ coreNamespaceA) (hB : modulePath ≠ coreNamespaceB)
    (hT : modulePath ≠ abbreviatedNamespace) :
    renderedReference modulePath createdName
      = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark := by
  simp [renderedReference, reportedName, hA, hB, hT]

@[grind] lemma renderedReference_core (modulePath createdName : List Char)
    (h : modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB) :
    renderedReference modulePath createdName
      = openMark ++ createdName ++ closeMark ++ elementListTail := by
  rcases h with h | h <;> subst h <;>
    simp [renderedReference, reportedName, coreNamespaceA, coreNamespaceB,
          abbreviatedNamespace, aliasFactoryName]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the reference for a stand-in placeholder symbol. The rendering reads
   the placeholder's module path and the name it was created to stand for, and
   follows whichever of the renderer's four rules the module path selects; in
   every rule the trailing segment is the reported simple name, which is exactly
   the name the placeholder was created to stand for. Both inputs are read-only —
   neither is declared `mut` (directive 5): the rendering only reads the module
   path and the creation name and mutates nothing. -/
method renderReference (modulePath : List Char) (createdName : List Char)
    return (out : List Char)
  ensures out = renderedReference modulePath createdName
  ensures modulePath = abbreviatedNamespace → createdName = aliasFactoryName →
      out = openMark ++ createdName ++ closeMark
  ensures (modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB) →
      out = openMark ++ createdName ++ closeMark ++ elementListTail
  ensures modulePath = abbreviatedNamespace → createdName ≠ aliasFactoryName →
      out = openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ createdName
              ++ closeMark
  ensures modulePath ≠ coreNamespaceA → modulePath ≠ coreNamespaceB →
      modulePath ≠ abbreviatedNamespace →
      out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
  do
    -- impl-start
    -- The placeholder's reported simple name is the name it was created to stand
    -- for; the rendered reference places that name in the trailing position of
    -- whichever of the renderer's four rules the module path selects.
    let simpleName := createdName
    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
      return openMark ++ simpleName ++ closeMark
    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
      return openMark ++ simpleName ++ closeMark ++ elementListTail
    else if modulePath = abbreviatedNamespace then
      return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
               ++ closeMark
    else
      return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
    -- impl-end

prove_correct renderReference by
  loom_solve
  <;> intros
  <;> subst_vars
  <;> simp_all [renderedReference, reportedName, coreNamespaceA, coreNamespaceB,
                abbreviatedNamespace, aliasFactoryName]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity), sphinx-doc__sphinx-9658 velvet. VERDICT: SOUND. All work in  13 attacks + positive control, all same_spec TRUE against the shipped Solution.lean (velvet backend); positive control pos_control.lean verifies exit 0; prepatch REPRODUCED.

**STRUCTURAL FINDING THAT FRAMES EVERYTHING.** The frozen postcondition `out = renderedReference modulePath createdName` is a TOTAL FUNCTIONAL EQUALITY over an EMPTY pre-conditions region. So every verifying impl is extensionally identical to the deep model on the whole carrier `List Char x List Char` -- impl latitude is NIL. That means a verify-not-correct witness cannot come from impl freedom at all; the only live break vector is model<->reality (A-leg) infidelity, which is where I concentrated per my assignment.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <path>`, run 4-way concurrent):
- atk_0_prepatch (simpleName := []): exit 1, unsolved goals on ALL FIVE ensures_1..ensures_5 -- matches refinement.md's G-DIFF claim exactly.
- atk_1_armorder_typing_first (rule 3 hoisted above rule 1; attacks leg A5): exit 1 (ensures_4, ensures_5)
- atk_2_no_element_tail (rule 2 drops `\\ []`; attacks A4b): exit 1 (ensures_3, ensures_5)
- atk_3_singlerule_law (plain dotted join on EVERY path -- the old single-rule spec a prior G-PANEL-2 condemned, re-encoded): exit 1 (ensures_2/3/4/5)
- atk_5_rule1_guard_or (guard AND weakened to OR): exit 1 (ensures_1/2/3/5)
- atk_6_only_core_a ('builtins' dropped from rule 2 -- partial domain): exit 1 (ensures_3, ensures_5)
- atk_7_no_abbrev_mark (rule 3 drops '~'; attacks A4c): exit 1 (ensures_2, ensures_5)
- atk_8_partial_nonempty (correct only for nonempty createdName -- partial domain/boundary): exit 1 (ensures_1/2/3/5)
- atk_9_rule1_py310_branch (mis-ported rule 1: the py3.10+ arm that keeps the module path): exit 1 (ensures_4, ensures_5)
- atk_12_name_is_modulepath (ungrounded wrong oracle): exit 1 (all five)
- VERIFY (exit 0): atk_4_oracle_echo (ungrounded-oracle echo: returns renderedReference verbatim), atk_10_echo_reportedname (echo via reportedName indirection + reordered core disjuncts), atk_11_core_before_newtype (rule 2 hoisted above rule 1).

WHY THE THREE VERIFY, AND WHY THEY ARE NOT WITNESSES. equiv.py (54 boundary pairs incl. both reserved core paths, 'typing', near-misses, the reserved alias name and near-misses, empty strings) shows atk_10 and atk_11 are EXTENSIONALLY IDENTICAL to the frozen model: 0 divergences. atk_11's reordering is behaviour-preserving because rules 1 and 2 have DISJOINT guards ('typing' vs '`__builtin__`'/'builtins'), so hoisting rule 2 cannot steal a rule-1 input -- a real but non-discriminating control-flow permutation. atk_4/atk_10 are echoes. So all three ARE the gold rendering.

MANDATORY RESOLVE RUNS (executed, not speculated). Faithful refined patch for all three verifying attacks is the same mechanism (reported simple name := creation name), materialized at patch_A.diff, which coincides with the gold mock.py edit. Cmd: `python do_resolve.py <name> <patch>` calling `run_resolve('sphinx-doc__sphinx-9658', patch, timeout=1800)`.
- patch_A (atk_4/atk_10 shared mechanism): RESOLVED=True COMPLETED=True NOTE=resolved; F2P success ['tests/test_util_typing.py::test_restify_mock'], F2P failure [], P2P 24/24 success, 0 failures. Log: resolve_A.log
- atk_11 (re-run under its own name): RESOLVED=True COMPLETED=True NOTE=resolved; F2P success, P2P 24/24, 0 failures. Log: resolve_atk11.log
So every verifying wrong impl's faithful patch DOES resolve => no verify-not-correct witness.

A-LEG AUDIT (my assigned focus). meta.json axioms=[] and deep_model_references=[]; 0 `axiom` decls in Solution.lean; no sorry/admit/native_decide/Classical.choice. G-AX=skip is therefore correct -- there are NO kind-A contracts to trust. Instead restify's ENTIRE 4-way dispatch is a DEEP MODEL inside the frozen pure region, which moves the whole trust burden onto model<->reality fidelity. Two things had to hold and both do:

(a) The model is genuinely FROZEN, not attacker latitude. Three tampers each flip same_spec to FALSE: probe_tamper_model.lean (rule-4 arm drops the trailing name), probe_tamper_reported.lean (reportedName := []), probe_drop_ensures5.lean (delete ensures_5). So no attacker can weaken the model or the contract while keeping the consumer spec view.

(b) The model AGREES with the REAL patched restify. I built my own probe (fidelity.py) independent of the bundle's conformance_check.py, transliterating the frozen pure region directly, and ran it on the PINNED Python 3.9 (image g9658py39, Python 3.9.25 -- the version matters because isNewType branches on sys.version_info >= (3,10)) with my patched worktree on PYTHONPATH. Result: 696 hand-picked boundary/near-miss pairs (24 module paths x 29 names: both reserved core paths, 'typing', near-misses 'typings'/'`__builtins__`'/'builtin'/'a.typing'/'TYPING'/' typing'/'typing '/'typing.sub'/'sub.typing', the reserved alias name and 5 near-misses, empty strings, dunder names that could collide with the mock's own machinery, backtick/backslash/tilde/bracket/dot/space/newline injections, non-ASCII, 200-char names) + 60000 randomized inputs with reserved paths at weight ~0.30 and near-misses ~0.10 => 0 MISMATCHES, all four rules hit at real weight (1490/12041/4489/42676). Plus the literal F2P walk path (mock(['unknown']) + attribute access) matches the model, and walk-vs-direct cross-validation agrees.

**ONE DISCREPANCY I CHASED DOWN AND CLEARED.** My first probe run reported a walk-vs-direct mismatch at leaf '`__name__`' (walk gave 'sub', direct gave ':py:class:`mockroot9658x.sub.__name__`'). Diagnosed with diag.py: a class ALWAYS has a real `__name__`, so `__getattr__` never fires and getattr(sub,'`__name__`') returns the plain str 'sub' -- no placeholder is produced at all, so that input is OUTSIDE the modeled domain (the model speaks about placeholders). This is a probe artifact, not model infidelity; I restricted the walk leg to placeholder-producing leaves (asserted isinstance(`_MockObject`)) and the rerun is clean. Incidentally this same mechanism independently CONFIRMS mapping.md section 5's pre-patch rule-2 account (pre-patch cls.`__name__` resolves through `__getattr__` to a further placeholder whose repr is its `__display_name__`).

EXTRA FALSIFICATION FROM THE PATCH SIDE (since impl latitude is nil). I asked whether a DIFFERENT mechanism that is faithful on the modeled domain could still fail the harness. Built rival mechanism C (patch_C.diff: only `self.__qualname__ = type(self).__name__` in `__init__`, no `__name__` class attr, no `_make_subclass` change -- a genuinely different edit, 1 hunk vs gold's 3). RESOLVED=True COMPLETED=True, F2P success, P2P 24/24. So the spec's modeled behaviour does not secretly depend on gold's particular mechanism either.

**REFINEMENT.MD LEG AUDIT.** 8 legs, tags: A1=R, A2=R, A3=I, A4a=I+R, A4b=I+R, A4c=I+R, A4d=I+R, A5=I. Every leg is R or I -- NO kind-3 (inexpressible-changed-op), consistent with section C's claim. I checked each A-leg's correspondence against the real callees at base_commit in the git repo: A4a<->typing.py:119-125 isNewType arm with inspect.py:213-223's exact conjunctive test (`__module__`=='typing' AND `__qualname__`=='NewType.<locals>.new_type') -- confirmed, and confirmed the py<3.10 arm at :125 is the one the pinned 3.9 image takes; A4b<->typing.py:133-140 builtins arm incl. the hasattr(`__args__`) sub-branch, and I verified empirically that a placeholder's `__args__` iterates empty so the join is '' and the tail is the constant '\\ []' (this is the one input-independent-constant R step, and it holds on all 12041 rule-2 inputs); A4c/A4d<->`_restify_py37`'s hasattr(`__qualname__`) arm at typing.py:193-196 with the typing sub-branch preceding the else; A5 arm order <-> restify's elif chain order.

The A3 claim that post-patch `__name__` and `__qualname__` are the SAME string (so one modeled reportedName serves rule 2, which reads `__name__`, and rules 1/3/4, which read `__qualname__`) is correct on the patched tree and is what makes the single-function model sound.

**NOTE ON A PRIOR PASS'S STALE-GATE CONCERN:** meta.json now records G-PANEL-2 = pass, so the stale-verdict issue an earlier G-EQ flagged has been cleared; I re-encoded that panel's own counterexample anyway as atk_3_singlerule_law and it is REJECTED (ensures_2/3/4/5), so the repair demonstrably took.

**BOTTOM LINE:** 13 attacks encoded and verified (10 rejected on precisely-named ensures_k goals, 3 verify and are provably the gold rendering), all 3 verifying attacks' faithful patches RUN through the official harness and ALL RESOLVED, deep model empirically faithful to the real restify on 60696 inputs across all four rules on the pinned interpreter, pure region and contracts provably frozen, no axioms and no kind-3 legs. No verify-not-correct witness found. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFUL — no diverging input found. Faithfulness attack on sphinx-doc__sphinx-9658 (velvet). Modeled function: renderReference(modulePath, createdName) : List Char, modeling restify(cls) for a `_MockObject` stand-in placeholder. Reference = worktree at base 232dbe41c with patch.diff APPLIED (confirmed: git diff shows exactly the three gold hunks in sphinx/ext/autodoc/mock.py — `__name__`='' on `_MockObject`, self.`__qualname__`=self.`__name__`, and '`__name__`': name in `_make_subclass`; sphinx/util/typing.py and sphinx/util/inspect.py are byte-unchanged vs base, so restify/isNewType dispatch is legitimately base-commit reference behavior for the unmodeled callees).

**INTEGRITY:** Solution.lean sha256 a6a5772f8d9295... matches the G-CONF/G-GOLD/G-HYGIENE recorded source hashes in meta.json (no post-gate edit). markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet_backend) = True — spec region byte-identical, so the twin differs only in impl (simpleName := [] vs createdName). scripts/lean_verify.sh Solution.lean => EXIT=0 (elaborates, no sorry/admit).

ENVIRONMENT PIN VERIFIED (decisive for rule 1): swebench SPECS_SPHINX['4.3']['python'] == '3.9'; container reports Python 3.9.20. So restify takes the sys.version_info <= (3,10) isNewType arm (':py:class:`%s`' % cls.`__name__`) and the >= (3,7) `_restify_py37` arm — exactly the two branches the model encodes. A spec written against the 3.10+ arm would have been unfaithful here; it is not.

DIFFERENTIAL TESTING against the real patched restify, all inside the pinned image (patch.diff git-applied), shadow = Solution.lean's four-rule dispatch transliterated, oracle = restify(`_make_subclass`(cn, mp)()):
- 868 targeted (module path x name) pairs incl. all reserved paths, near-misses (typings, `__builtins__`, builtin, a.typing, TYPING, Typing), alias near-misses, empty strings, 200-char strings, format-string metachars: 0 disagreements.
- 186 dunder/internal-attribute-collision names (`__name__`, `__qualname__`, `__args__`, `__origin__`, `_name`, `__iter__`, `__getattr__`, `__mro_entries__`, `__sphinx_mock__`, mro, ...) — the sharpest angle, since a name colliding with an attribute restify reads could shadow the dispatch: 0 disagreements.
- 1360 weird/unicode/control-char pairs (newline, tab, backtick, backslash, '\\ []', ':py:class:`', CJK, emoji, zero-width): 0 disagreements. The only 40 'errors' are UnicodeEncodeError on a lone surrogate \ud800, a harness print artifact, not a behavioral disagreement.
- 40,000-case fuzz (seed 424242) + 160,000-case fuzz on an INDEPENDENT seed 20260815 (deliberately not the bundle's pinned 9658, so this is not a replay of G-CONF): 0 disagreements, 0 errors, and all four rules genuinely exercised (rule1=224, rule2=23400, rule3=11501, rule4=124875) — no rule silently untested.

ARM-ORDER / GUARD-EXTENT probed directly, since the spec's ordering is the main place a too-strong spec could hide: isNewType is True exactly for (`__module__`=='typing', `__qualname__`=='NewType.<locals>.new_type'); ('`__builtin__`', ALIAS) and ('builtins', ALIAS) correctly take rule 2 not rule 1 (oracle ':py:class:`NewType.<locals>.new_type`\\ []'); ('typing','x') takes rule 3 not rule 4; ('Typing',ALIAS) and ('a.typing',ALIAS) fall to rule 4. Every crossing matches the model's guard order. Confirmed the earlier guards in restify cannot fire on a placeholder: for a mock, `cls in INVALID_BUILTIN_CLASSES` is False, `cls is None/Ellipsis` False, `isinstance(cls,str)` False, and UnionType/isgenericalias are False — even for the adversarial (struct,'Struct') / (types,'TracebackType') / (builtins,'Ellipsis') / (builtins,'None') inputs designed to trip them. So collapsing restify to four rules is not a narrowing.

RULE-2 CONSTANT JUSTIFIED, NOT ASSUMED: for every rule-2 name tried, hasattr(cls,'`__args__`') is True and list(cls.`__args__`) == [] (via `_MockObject`.`__iter__` -> iter([])), so ', '.join(...) == '' and the element-list tail is the genuine constant '\\ []' — the mapping.md §2 R-refinement holds on the whole modeled domain.

reportedName createdName = createdName VERIFIED at the object level: `_make_subclass`('Foo','unknown.secret') yields class and instance with `__name__` == `__qualname__` == 'Foo', so one modeled reportedName correctly serves rule 2 (reads `__name__`) and rules 1/3/4 (read `__qualname__`). Post-patch these are the same string; pre-patch they were not, which is the delta and correctly NOT charged as a divergence.

REACHABILITY / EMPTY-PRECONDITION CHECK (the strongest candidate defect, and it fails): the spec has an empty pre-conditions region, so it quantifies over ALL List Char. I hunted for a Lean-representable input the real repo cannot honor. The only one found is a NUL in createdName: type() raises ValueError('type name must not contain null characters'), so `_make_subclass` cannot build the placeholder. But this is NOT a faithfulness defect — the input is unreachable through every real access path (getattr walk and getitem walk both raise the same ValueError before restify is ever called), so there is no repo behavior on it for the spec to disagree with; and a NUL in modulePath IS constructible and the model matches exactly (':py:class:`unk\x00nown.Class`'). An unreachable-input vacuity is a domain-width question, not a spec-vs-repo disagreement, and it does not let a wrong impl through: on every reachable input the five ensures pin the output uniquely.

ALTERNATE CONSTRUCTION PATHS all agree: the literal F2P walk (mock([root]) + attribute access) at depths 1-5, `__getitem__` (R.secret[key] incl. key='' and the alias), `__call__`, and the `__new__`/`__mro_entries__` subclassing path. F2P input reproduced exactly: restify(unknown.secret.Class) == ':py:class:`unknown.secret.Class`' == the model's output on ('unknown.secret','Class').

**CONCLUSION:** the modeled function agrees with the real patched callee on every reachable input tested (~203k differential cases across four independent probes plus targeted boundary and dunder-collision suites, all four rules covered, on the correctly-pinned Python 3.9 interpreter). The spec is neither too strong nor drifted: it does not narrow the domain by precondition, it reproduces restify's dispatch and arm order leg by leg rather than folding it into one format, and its per-rule decorations are the real literals. No diverging input exists to cite. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker 3 (leakage / gold-reconstruction), sphinx-doc__sphinx-9658 (velvet). VERDICT: NO-LEAKAGE. All measurements below are MINE, re-derived on the live artifact (Solution.lean sha256 a6a5772f8d9295fe..., matching meta gates.G-LEAK/G-GOLD sources).

**NO RELAXATION CLAIM IN THIS BUNDLE.** Checked explicitly: meta.json has no `relaxed_leakage` key ([k for k in meta if 'relax' in k.lower()] == []) and there is no RELAXED_LEAKAGE.md anywhere under the instance dir (find -iname '*relax*' empty). So this is a plain leakage judgement with no disposition to re-derive or inherit. No file in the bundle addressed me, instructed me how to record, or told me which verdict was honest -- nothing to report on that head.

STALE PRIOR NOTE -- NOT INHERITED. meta gates.G-PANEL-3 carries a recorded NO-LEAKAGE note citing spec_signature sha 378cb825c4d0055b; I measure 438a3384aeac17a2 on the current file, and its G-EQ-era Solution.lean hash (ec4f1453...) differs from the live one (a6a5772f...). The spec was revised after that note (the live spec has five `ensures`, four of them per-rule guarded, where the note's era had two unconditional ones). I therefore re-ran every leg rather than reading the note forward.

**SCOPE.** Consumer exposure is exactly markers.spec_view(Solution.lean): eval/prompts.py:`_spec_block` fences task.spec_view and nothing else; eval/adapter.py:304-320 hard-guards impl AND the `prove_correct` tactic body are elided before exposing (velvet has no `proof` marker region, so the third guard at :317-320 is the one that bites). I confirmed the elision on the live projection: 'let simpleName' and 'loom_solve' are ABSENT from the spec view; ELISION_IMPL and ELISION_PROOF are both present. refinement.md/mapping.md DO quote the gold hunks verbatim (refinement.md:43-58 shows `+ __name__ = ''`, `- self.__qualname__ = ''`, `+ self.__qualname__ = self.__name__`, `+ '__name__': name,`) but are audit-only artifacts, never rendered to a solver -- correctly out of scope.

SPEC-REGION BYTE-IDENTITY (as instructed). markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True. Per-region sha256: axioms 735ef976... and pure 92422721... IDENTICAL across patched/prepatch; spec_view projection IDENTICAL e83f4d38... (matching meta G-HYGIENE region_hashes); only `impl` differs (2af0405d... vs bac50e48...). So the frozen spec carries no patched-vs-prepatch asymmetry that could itself localize the edit.

SCREEN NON-VACUITY (I refused to rubber-stamp the automated pass). leakage.screen(sol, velvet, patch.diff, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[], matching meta G-LEAK (strict, 'spec view clean'). I confirmed patch.diff == instance.json['patch'] byte-for-byte first, so the screen ran against the frozen gold. I then injected eight known leaks at the head of the `pure` region and every one FIRED: gold line `self.__qualname__ = self.__name__` -> L1; `__name__ = ''` -> L1; `'__name__': name,` -> L1; path 'sphinx/ext/autodoc/mock.py' -> L2; '@@' -> L1; identifier embedding 'make_subclass' -> L2/L5; identifier embedding 'MockObject' -> L2/L5; 'fixes the bug ... wrong' -> L3. Guarded symbol set = {MockObject, make_subclass}; changed files = sphinx/ext/autodoc/mock.py. All five rule families demonstrably live on THIS instance.

MANUAL ADVERSARIAL READ (not trusting the lexer), against the solver-visible problem_statement ONLY, never hints_text (hints_text is empty here anyway):
- All four gold changed lines fail whitespace-normalized containment in the spec view.
- Zero repo-symbol echoes for: `_MockObject`, MockObject, make_subclass, `__name__`, `__qualname__`, `__display_name__`, `__sphinx_mock__`, decorator_args, mock.py, restify, stringify, typing.py, attrs, superclass, `__module__`, `__args__`, isNewType, py:class, unknown.secret, test_restify_mock. The spec view names no file, no class, no attribute, and no test.
- `_NARRATION_RE`.findall(spec_view) == []. I also swept a wider pre-state vocabulary beyond the screen's lexicon ('empty string', 'instead of', 'no longer', 'used to', 'hard-coded', 'default', 'currently', 'was', 'missing', 'omit', 'change/changed/now', 'issue', 'edit'). Only benign hits: 'the module path is dropped' (that is the FORWARD spec of rules 1-2, describing what the correct renderer does, not what the old code did wrong) and 'the name it was created to stand for' / 'so no rule drops it' (forward-stated laws). Nothing states or implies a PRE-state -- the spec view never says the trailing name was previously empty, which is the actual gold discriminator.

THE ONE JUDGEMENT CALL -- the reserved-namespace material. The spec view discloses three reserved module paths ('`__builtin__`', 'builtins', 'typing'), a reserved simple name ('NewType.<locals>.new_type'), the ':py:class:`' / '`' / '\\ []' / '~' decorations, and the four-rule dispatch ORDER -- detail that is NOT in problem_statement (which only shows 'torch.nn.' vs 'torch.nn.Module'). I checked whether this localizes the edit and it does not: I extracted a CLEAN tree at base_commit 232dbe41c (`git archive` into a fresh mktemp -d, because the pre-existing * worktree is another panelist's and is dirty on mock.py) and read sphinx/util/typing.py:118-144 and :193-198.

Every one of those four arms -- isNewType, `cls.__module__ in ('__builtin__','builtins')` with the `hasattr(cls,'__args__')` bracket tail, the `__module__ == 'typing'` '~' arm, and the general dotted else -- is PRE-EXISTING code in sphinx/util/typing.py, a file patch.diff does not touch (changed_files == ['sphinx/ext/autodoc/mock.py'] only). So this material describes the untouched OBSERVATION site the specified behavior must agree with; it is repo context any solver can read at base_commit, and it points at util/typing.py, i.e. AWAY from the mock.py edit site.

It is also load-bearing rather than decorative: the gold edit changes the output of all four arms, so a spec that folded them into one dotted format would be false on three of them (which is exactly what the older two-`ensures` spec was failed for under G-PANEL-2).

LOAD-BEARING / DISCRIMINATOR TEST. scripts/lean_verify.sh Solution.lean -> exit 0 (verifies). scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, and the residual goal is exactly `createdName = []` under `if_neg_1`/`if_neg_2` (module path neither core namespace nor 'typing'). So the spec discriminates gold from pre-patch precisely on 'reported simple name = creation name vs the empty string' -- the real gold content -- and it does so via a forward-stated law (`reportedName createdName = createdName`) that never mentions the empty-string pre-state, the attribute pair it lives on, or the file it lives in. That is a spec of correct behavior, not a transcription of the diff.

NOTED, NOT CHARGED (out of this gate's scope, flagged for the record): in spec modes prompts.py:53-57 renders meta.modeled_functions as 'Modeled function(s): renderReference (<-> sphinx.ext.autodoc.mock.`_MockObject` (`__name__`/`__qualname__`) observed via sphinx.util.typing.restify)', which does name the edit's file, class and both changed attributes. That is the harness's sanctioned localization channel (dataset.py:245-262 grants repo_symbol + changed_files to localization modes by definition) and is uniform across all velvet bundles -- it is not a property of THIS spec view, which G-LEAK and this gate screen. The bundle's own repo_location string is even more explicit ('fix at lines 29,44,77') but prompts.py's velvet branch does not render repo_location in the spec block. Separately: meta gates.G-PANEL aggregate is `fail` on G-PANEL-2 (faithfulness), recorded against the older two-unconditional-`ensures` spec; the live five-`ensures` per-rule spec appears to answer that attack, but faithfulness is not my lane and I make no finding on it.

**CONCLUSION:** the spec view reproduces no gold line, no diff marker, no patched path, no patched repo symbol, and no bug/fix or pre-state narration; it is byte-identical between the patched and prepatch bundles; and its only above-problem_statement detail is untouched observation-site behavior that points away from the edit. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
