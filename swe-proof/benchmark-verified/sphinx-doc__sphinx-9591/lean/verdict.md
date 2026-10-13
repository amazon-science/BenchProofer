# P2 adversarial audit — sphinx-doc__sphinx-9591

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,8 +68,7 @@
     (typ : String) : List Node := Id.run do
   let mut children : List Node := []
   if typ ≠ "" then
-    let annotations := crossRefParser typ
-    children := mkText ": " :: annotations
+    children := [mkText (": " ++ typ)]
   return children
 -- impl-end
 
@@ -82,8 +81,6 @@
   intro Node mkText crossRefParser typ
   unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [Id.run, if_pos h]
-    rfl
-  · subst h
-    rfl
+  · simp_all [Id.run]
+  · simp_all [Id.run]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,8 +68,7 @@
     (typ : String) : List Node := Id.run do
   let mut children : List Node := []
   if typ ≠ "" then
-    let annotations := crossRefParser typ
-    children := mkText ": " :: annotations
+    children := crossRefParser typ
   return children
 -- impl-end
 
@@ -82,8 +81,6 @@
   intro Node mkText crossRefParser typ
   unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [Id.run, if_pos h]
-    rfl
-  · subst h
-    rfl
+  · simp_all [Id.run]
+  · simp_all [Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,9 +67,8 @@
     (mkText : String → Node) (crossRefParser : String → List Node)
     (typ : String) : List Node := Id.run do
   let mut children : List Node := []
-  if typ ≠ "" then
-    let annotations := crossRefParser typ
-    children := mkText ": " :: annotations
+  if typ = "str" then
+    children := mkText ": " :: crossRefParser typ
   return children
 -- impl-end
 
@@ -82,8 +81,6 @@
   intro Node mkText crossRefParser typ
   unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [Id.run, if_pos h]
-    rfl
-  · subst h
-    rfl
+  · simp_all [Id.run]
+  · simp_all [Id.run]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,9 +67,8 @@
     (mkText : String → Node) (crossRefParser : String → List Node)
     (typ : String) : List Node := Id.run do
   let mut children : List Node := []
-  if typ ≠ "" then
-    let annotations := crossRefParser typ
-    children := mkText ": " :: annotations
+  if typ = "" then
+    children := mkText ": " :: crossRefParser typ
   return children
 -- impl-end
 
@@ -82,8 +81,6 @@
   intro Node mkText crossRefParser typ
   unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [Id.run, if_pos h]
-    rfl
-  · subst h
-    rfl
+  · simp_all [Id.run]
+  · simp_all [Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,8 +68,7 @@
     (typ : String) : List Node := Id.run do
   let mut children : List Node := []
   if typ ≠ "" then
-    let annotations := crossRefParser typ
-    children := mkText ": " :: annotations
+    children := mkText " :" :: crossRefParser typ
   return children
 -- impl-end
 
@@ -82,8 +81,6 @@
   intro Node mkText crossRefParser typ
   unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [Id.run, if_pos h]
-    rfl
-  · subst h
-    rfl
+  · simp_all [Id.run]
+  · simp_all [Id.run]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,8 +68,7 @@
     (typ : String) : List Node := Id.run do
   let mut children : List Node := []
   if typ ≠ "" then
-    let annotations := crossRefParser typ
-    children := mkText ": " :: annotations
+    children := crossRefParser typ ++ [mkText ": "]
   return children
 -- impl-end
 
@@ -82,8 +81,6 @@
   intro Node mkText crossRefParser typ
   unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [Id.run, if_pos h]
-    rfl
-  · subst h
-    rfl
+  · simp_all [Id.run]
+  · simp_all [Id.run]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,8 +68,7 @@
     (typ : String) : List Node := Id.run do
   let mut children : List Node := []
   if typ ≠ "" then
-    let annotations := crossRefParser typ
-    children := mkText ": " :: annotations
+    children := mkText ": " :: mkText ": " :: crossRefParser typ
   return children
 -- impl-end
 
@@ -82,8 +81,6 @@
   intro Node mkText crossRefParser typ
   unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
   refine ⟨fun h => ?_, fun h => ?_⟩
-  · simp only [Id.run, if_pos h]
-    rfl
-  · subst h
-    rfl
+  · simp_all [Id.run]
+  · simp_all [Id.run]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the inline nodes that render a documented property's *type annotation*
in its signature.

When a documented property carries a declared type, the signature gains a small
annotation fragment introduced by a `": "` separator and followed by the rendered
type. There are two ways the type text after the separator can be rendered:

  * as a single, inert run of plain text (the type name is shown but is not made
    navigable), or
  * parsed into a sequence of inline nodes in which type names become
    cross-reference-aware nodes (so a documented type becomes a navigable
    cross-reference).

The behavior pinned below builds the annotation fragment in the second form: the
`": "` separator as its own plain-text node, immediately followed — in order — by
the nodes obtained from parsing the declared type string. When the property
declares no type at all, no annotation fragment is produced.

The type-parsing step itself (turning an annotation string into a list of inline
nodes) is the SAME operation regardless; here it is taken as an arbitrary function
of the type string, so the behavior pinned below is exactly "the separator text
node, then the parsed type nodes, in that order."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Inline nodes are modeled
-- by an arbitrary carrier type `Node` with one known constructor `mkText`
-- (the plain-text-node factory). The annotation-parsing step (turning a type
-- string into a list of inline nodes) is modeled as an arbitrary function
-- parameter `crossRefParser : String → List Node`: the modeled change is solely
-- WHICH children are assembled (and in WHICH order), so the result is pinned for
-- every possible parser. Hence the spec needs no `opaque`/`axiom` callee
-- contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the annotation fragment is the
-- separator text node consed onto the parsed-type node list.
-- pure-end

-- post-conditions-start
/-- The annotation fragment is fully pinned to the inputs:

  * when the property declares a (non-empty) type string, the fragment is exactly
    the `": "` separator as a plain-text node, followed in order by the nodes the
    type-parsing step produces from that string;
  * when no type is declared, no fragment is produced (the empty node list).

No output component is left free: in the present-type case the head is pinned to
the separator text node and the tail to the parser's output, and the empty case
is pinned to the empty list. -/
def problem_spec_propertyTypeAnnotation
    {Node : Type}
    (mkText : String → Node) (crossRefParser : String → List Node)
    (typ : String) (result : List Node) : Prop :=
  (typ ≠ "" → result = mkText ": " :: crossRefParser typ) ∧
  (typ = "" → result = [])
-- post-conditions-end

-- impl-start
def implementation_propertyTypeAnnotation
    {Node : Type}
    (mkText : String → Node) (crossRefParser : String → List Node)
    (typ : String) : List Node := Id.run do
  let mut children : List Node := []
  if typ ≠ "" then
    let annotations := crossRefParser typ
    children := mkText ": " :: annotations
  return children
-- impl-end

-- proof-start
theorem correct_propertyTypeAnnotation :
    ∀ {Node : Type} (mkText : String → Node) (crossRefParser : String → List Node)
      (typ : String),
      problem_spec_propertyTypeAnnotation mkText crossRefParser typ
        (implementation_propertyTypeAnnotation mkText crossRefParser typ) := by
  intro Node mkText crossRefParser typ
  unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [Id.run, if_pos h]
    rfl
  · subst h
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-9591 (lean). Spec problem_spec_propertyTypeAnnotation is a TOTAL, SINGLE-VALUED relation over an arbitrary Node type with only mkText/crossRefParser known: (typ != "" -> result = mkText ": " :: crossRefParser typ) AND (typ = "" -> result = []). Both branches pin result to a unique value on a complete, mutually-exclusive input partition, so any spec-satisfying impl is observationally equal to the gold; there is no slack for a closing-but-non-resolving impl.

Protocol executed All 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (spec/axioms/pure/pre/post byte-identical to Solution.lean; only the impl region edited). Verify cmd for each, run, concurrently in background (<=4 at a time): bash scripts/lean_verify.sh <file>.

Results:
- pos_control.lean (gold impl): exit 0 (verifies, no sorry). axcheck.lean (pos_control + '#print axioms correct_propertyTypeAnnotation') exit 0 -> 'correct_propertyTypeAnnotation does not depend on any axioms' (clean).
- atk_1 (prepatch bug: single inert node [mkText (": " ++ typ)], discards parser): exit 1, unsolved goals. PREPATCH REPRODUCED.
- atk_2 (boundary: drop separator node, return crossRefParser typ): exit 1, unsolved goals.
- atk_3 (partial-domain: correct only when typ="str", else []): exit 1, unsolved goals.
- atk_4 (control-flow-effect: inverted guard, fragment on typ=""): exit 1, unsolved goals.
- atk_5 (divergent separator " :" instead of ": "): exit 1, unsolved goals.
- atk_6 (order: crossRefParser typ ++ [mkText ": "] reversed): exit 1, unsolved goals.
- atk_7 (ungrounded-oracle/duplicate-tail: mkText ": " :: mkText ": " :: crossRefParser typ): exit 1, unsolved goals.

All 7 wrong impls fail proof closure with genuine 'unsolved goals' at the refine branches (lines 84/85), not syntax errors. Because Node/mkText/crossRefParser are universally quantified with no injectivity/length facts available, each deviation (head separator, tail contents/ordering/duplication, guard, domain) leaves a residual equality that is not rfl and unprovable -> no closing proof exists. Since NO wrong impl closes with clean axioms, protocol step 2 (materialize faithful patch + run_resolve) is not triggered for any attack; patches={} accordingly.

refinement.md leg audit: leg1 I (accumulator empty), leg2 R (Python truthiness typ <-> typ != ""), leg3 A-reference (crossRefParser <-> unchanged callee _parse_annotation, universally quantified so proof consumes no property of it -- confirmed by clean #print axioms; G-CONF validates the correspondence against the real callee), leg4 R/I (separator text node prepended, order), leg5 I. All legs are R / A-reference / I. NO kind-3, NO A-consumed (meta.json axioms=[] consistent). The A-reference correspondence to _parse_annotation holds and matches mapping.md and G-CONF (conformance_check.py drives real _parse_annotation + desc_annotation).

Verdict: SOUND -- >=5 distinct attacks (7 total) run, positive control verifies with clean axioms, none breaks the spec; verify => correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the inline nodes that render a documented property's *type annotation*
in its signature.

When a documented property carries a declared type, the signature gains a small
annotation fragment introduced by a `": "` separator and followed by the rendered
type. There are two ways the type text after the separator can be rendered:

  * as a single, inert run of plain text (the type name is shown but is not made
    navigable), or
  * parsed into a sequence of inline nodes in which type names become
    cross-reference-aware nodes (so a documented type becomes a navigable
    cross-reference).

The behavior pinned below builds the annotation fragment in the second form: the
`": "` separator as its own plain-text node, immediately followed — in order — by
the nodes obtained from parsing the declared type string. When the property
declares no type at all, no annotation fragment is produced.

The type-parsing step itself (turning an annotation string into a list of inline
nodes) is the SAME operation regardless; here it is taken as an arbitrary function
of the type string, so the behavior pinned below is exactly "the separator text
node, then the parsed type nodes, in that order."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Inline nodes are modeled
-- by an arbitrary carrier type `Node` with one known constructor `mkText`
-- (the plain-text-node factory). The annotation-parsing step (turning a type
-- string into a list of inline nodes) is modeled as an arbitrary function
-- parameter `crossRefParser : String → List Node`: the modeled change is solely
-- WHICH children are assembled (and in WHICH order), so the result is pinned for
-- every possible parser. Hence the spec needs no `opaque`/`axiom` callee
-- contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the annotation fragment is the
-- separator text node consed onto the parsed-type node list.
-- pure-end

-- post-conditions-start
/-- The annotation fragment is fully pinned to the inputs:

  * when the property declares a (non-empty) type string, the fragment is exactly
    the `": "` separator as a plain-text node, followed in order by the nodes the
    type-parsing step produces from that string;
  * when no type is declared, no fragment is produced (the empty node list).

No output component is left free: in the present-type case the head is pinned to
the separator text node and the tail to the parser's output, and the empty case
is pinned to the empty list. -/
def problem_spec_propertyTypeAnnotation
    {Node : Type}
    (mkText : String → Node) (crossRefParser : String → List Node)
    (typ : String) (result : List Node) : Prop :=
  (typ ≠ "" → result = mkText ": " :: crossRefParser typ) ∧
  (typ = "" → result = [])
-- post-conditions-end

-- impl-start
def implementation_propertyTypeAnnotation
    {Node : Type}
    (mkText : String → Node) (crossRefParser : String → List Node)
    (typ : String) : List Node := Id.run do
  let mut children : List Node := []
  if typ ≠ "" then
    let annotations := crossRefParser typ
    children := mkText ": " :: annotations
  return children
-- impl-end

-- proof-start
theorem correct_propertyTypeAnnotation :
    ∀ {Node : Type} (mkText : String → Node) (crossRefParser : String → List Node)
      (typ : String),
      problem_spec_propertyTypeAnnotation mkText crossRefParser typ
        (implementation_propertyTypeAnnotation mkText crossRefParser typ) := by
  intro Node mkText crossRefParser typ
  unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [Id.run, if_pos h]
    rfl
  · subst h
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-9591 (lean). Spec problem_spec_propertyTypeAnnotation is a TOTAL, SINGLE-VALUED relation over an arbitrary Node type with only mkText/crossRefParser known: (typ != "" -> result = mkText ": " :: crossRefParser typ) AND (typ = "" -> result = []). Both branches pin result to a unique value on a complete, mutually-exclusive input partition, so any spec-satisfying impl is observationally equal to the gold; there is no slack for a closing-but-non-resolving impl.

Protocol executed All 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (spec/axioms/pure/pre/post byte-identical to Solution.lean; only the impl region edited). Verify cmd for each, run, concurrently in background (<=4 at a time): bash scripts/lean_verify.sh <file>.

Results:
- pos_control.lean (gold impl): exit 0 (verifies, no sorry). axcheck.lean (pos_control + '#print axioms correct_propertyTypeAnnotation') exit 0 -> 'correct_propertyTypeAnnotation does not depend on any axioms' (clean).
- atk_1 (prepatch bug: single inert node [mkText (": " ++ typ)], discards parser): exit 1, unsolved goals. PREPATCH REPRODUCED.
- atk_2 (boundary: drop separator node, return crossRefParser typ): exit 1, unsolved goals.
- atk_3 (partial-domain: correct only when typ="str", else []): exit 1, unsolved goals.
- atk_4 (control-flow-effect: inverted guard, fragment on typ=""): exit 1, unsolved goals.
- atk_5 (divergent separator " :" instead of ": "): exit 1, unsolved goals.
- atk_6 (order: crossRefParser typ ++ [mkText ": "] reversed): exit 1, unsolved goals.
- atk_7 (ungrounded-oracle/duplicate-tail: mkText ": " :: mkText ": " :: crossRefParser typ): exit 1, unsolved goals.

All 7 wrong impls fail proof closure with genuine 'unsolved goals' at the refine branches (lines 84/85), not syntax errors. Because Node/mkText/crossRefParser are universally quantified with no injectivity/length facts available, each deviation (head separator, tail contents/ordering/duplication, guard, domain) leaves a residual equality that is not rfl and unprovable -> no closing proof exists. Since NO wrong impl closes with clean axioms, protocol step 2 (materialize faithful patch + run_resolve) is not triggered for any attack; patches={} accordingly.

refinement.md leg audit: leg1 I (accumulator empty), leg2 R (Python truthiness typ <-> typ != ""), leg3 A-reference (crossRefParser <-> unchanged callee _parse_annotation, universally quantified so proof consumes no property of it -- confirmed by clean #print axioms; G-CONF validates the correspondence against the real callee), leg4 R/I (separator text node prepended, order), leg5 I. All legs are R / A-reference / I. NO kind-3, NO A-consumed (meta.json axioms=[] consistent). The A-reference correspondence to _parse_annotation holds and matches mapping.md and G-CONF (conformance_check.py drives real _parse_annotation + desc_annotation).

Verdict: SOUND -- >=5 distinct attacks (7 total) run, positive control verifies with clean axioms, none breaks the spec; verify => correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) verified against the real repo. SPEC REGION: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True — the solver-visible spec view is byte-identical across the buggy and fixed impls; only impl/proof differ. COMPILE+PROOF: scripts/lean_verify.sh exit 0; `#print axioms correct_propertyTypeAnnotation` reports 'does not depend on any axioms' (no sorryAx, genuine proof). FAITHFULNESS TO REAL CALLEE: The modeled fragment is the type-annotation arm of PyProperty.handle_signature. Post-patch real code: `annotations = _parse_annotation(typ, self.env); signode += addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)`. desc_annotation is a docutils FixedTextElement(TextElement); I verified TextElement.__init__ (docutils/nodes.py:1513-1524): with text='' (falsy) NO child is added for the text arg, so the constructed children are exactly [Text(': ')] ++ annotations, in order. This is precisely the spec's non-empty branch `result = mkText ": " :: crossRefParser typ`. The `if typ:` guard (typ = self.options.get('type'), None or a str) is falsy exactly for None/"" and truthy otherwise, matching the spec's typ=""→[] vs typ≠""→fragment split on every input (whitespace-only strings are Python-truthy AND Lean ≠ "", so no divergence). crossRefParser is UNIVERSALLY QUANTIFIED, so the spec holds for every parser; instantiating with the real total _parse_annotation (python.py:110-186, always returns a List — SyntaxError path returns [type_to_xref(annotation, env)]) matches exactly. The spec pins only the framing the patch changed, not the parser's internal node shapes — it is neither stronger than nor weaker than the real behavior on any input. CONFORMANCE: conformance_check.py ran 120017 checks, 0 disagreements (replica mode in this venv; oracle logic mirrors the real desc_annotation construction). No diverging input exists. NOT a defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent leakage/gold-reconstruction audit for sphinx-doc__sphinx-9591 (lean). Public problem_statement discloses: bug title 'Cross-references don't work in property's type annotations', the vocabulary property/type-annotation/cross-referenced, and the before->after behavior (documented type currently NOT navigable; expected TO BE cross-referenced). No hints_text used.

Spec-view scope confirmed: markers.same_spec(Solution, Solution_prepatch) = True (byte-identical spec region: docstring + axioms + pure + post-conditions; only impl/proof are elided and consumer-supplied). Rendered the actual spec_view via the lean backend and screened it against the frozen gold patch + problem_statement (leakage.screen): passed=True, hard_failures=[]. No RELAXED_LEAKAGE.md and relaxed_leakage flag unset, so this is a genuine clean pass (not a deferral).

Gold edit = replace single plain-text node `desc_annotation(typ, ': ' + typ)` with `_parse_annotation(typ, self.env)` output prepended by `nodes.Text(': ')` in sphinx/domains/python.py, PyProperty.handle_signature. No spec-view line leaks it beyond problem_statement:
- Patched file path sphinx/domains/python.py: NOT present.
- Patched symbols handle_signature / PyProperty: NOT present (modeled neutrally as propertyTypeAnnotation, sharing no patched def/class substring).
- Callees _parse_annotation / addnodes.desc_annotation / nodes.Text: described by behavior only (crossRefParser, mkText, 'type-parsing step'), never named.
- No gold-diff line reproduced; no diff markers; no bug/fix narration terms.
- The ': ' separator is user-visible type-annotation display syntax (repro shows `end: Point`), a rendering constant already public, not the fix secret.
- crossRefParser is universally quantified, so the post-condition pins only the child-node FRAMING (separator node, then parser output, in order) — exactly the public behavioral content, not the internal mechanism of the fix. A solver cannot reconstruct the specific gold edit (file/function/callee names) from the spec view; it only learns the public expected behavior.

Concurs with recorded G-PANEL-3 = NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
