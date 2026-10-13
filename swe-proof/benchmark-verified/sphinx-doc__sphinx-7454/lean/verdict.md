# P2 adversarial audit — sphinx-doc__sphinx-7454

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,11 +68,7 @@
 
 -- impl-start
 def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
-  let mut kind := "class"
-  if text = "None".toList then
-    kind := "obj"
-  else
-    kind := "class"
+  let kind := "class"
   return { domain := "py", kind := kind, target := text, label := text }
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,11 +68,11 @@
 
 -- impl-start
 def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
-  let mut kind := "class"
+  let mut kind := "obj"
   if text = "None".toList then
+    kind := "class"
+  else
     kind := "obj"
-  else
-    kind := "class"
   return { domain := "py", kind := kind, target := text, label := text }
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,11 +68,7 @@
 
 -- impl-start
 def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
-  let mut kind := "class"
-  if text = "None".toList then
-    kind := "obj"
-  else
-    kind := "class"
+  let kind := if text.length = 4 then "obj" else "class"
   return { domain := "py", kind := kind, target := text, label := text }
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,12 +68,8 @@
 
 -- impl-start
 def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
-  let mut kind := "class"
-  if text = "None".toList then
-    kind := "obj"
-  else
-    kind := "class"
-  return { domain := "py", kind := kind, target := text, label := text }
+  let kind := if text = "None".toList then "obj" else "class"
+  return { domain := "python", kind := kind, target := text, label := text }
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,12 +68,8 @@
 
 -- impl-start
 def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
-  let mut kind := "class"
-  if text = "None".toList then
-    kind := "obj"
-  else
-    kind := "class"
-  return { domain := "py", kind := kind, target := text, label := text }
+  let kind := if text = "None".toList then "obj" else "class"
+  return { domain := "py", kind := kind, target := [], label := text }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,12 +68,8 @@
 
 -- impl-start
 def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
-  let mut kind := "class"
-  if text = "None".toList then
-    kind := "obj"
-  else
-    kind := "class"
-  return { domain := "py", kind := kind, target := text, label := text }
+  let kind := if text = "None".toList then "obj" else "class"
+  return { domain := "py", kind := kind, target := text, label := text.reverse }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,10 +69,8 @@
 -- impl-start
 def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
   let mut kind := "class"
-  if text = "None".toList then
+  if "None".toList.isPrefixOf text then
     kind := "obj"
-  else
-    kind := "class"
   return { domain := "py", kind := kind, target := text, label := text }
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,13 +67,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
-  let mut kind := "class"
-  if text = "None".toList then
-    kind := "obj"
-  else
-    kind := "class"
-  return { domain := "py", kind := kind, target := text, label := text }
+def implementation_annotationRef (text : List Char) : TypeRef :=
+  { domain := "py",
+    kind := (if text = "None".toList then "obj" else "class"),
+    target := text, label := text }
 -- impl-end
 
 -- proof-start
@@ -82,7 +79,6 @@
       problem_spec_annotationRef text (implementation_annotationRef text) := by
   intro text
   unfold problem_spec_annotationRef implementation_annotationRef
-  by_cases h : text = "None".toList <;>
-    simp only [h, Id.run, if_pos, pure] <;>
-    exact ⟨rfl, rfl, rfl, rfl⟩
+  refine ⟨rfl, rfl, rfl, ?_⟩
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a single type-annotation token as a documentation cross-reference.

When a type annotation in an API signature is turned into documentation, each
bare token of the annotation (a name such as `int`, `List`, or `None`) becomes a
clickable cross-reference into the documentation set. Such a reference carries
four pieces of data:

  * the documentation DOMAIN it resolves in (here always the Python domain,
    `"py"`);
  * the reference KIND, which selects what sort of documented entity the token
    names;
  * the TARGET, the name that is looked up — the token text itself;
  * the visible LABEL shown to the reader — again the token text.

Most tokens name a class-like entity, so their reference kind is the class kind
(`"class"`). The single exception is the token `None`: it does not name a class
but the unique `None` object, so its reference kind is the object kind
(`"obj"`). Both `None` and every other token must yield a cross-reference (so a
`None` annotation is just as clickable as any other) — they differ only in which
kind that reference carries.

So for the token `None` the result is the object-kind reference targeting and
labelled `None`; for any other token `t` the result is the class-kind reference
targeting and labelled `t`. The domain, target, and label are determined by the
token alone; only the kind branches on whether the token is `None`.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Building the
-- cross-reference for a token is spelled out directly below: the four
-- components (domain, kind, target, label) are computed from the token by
-- pure structural data, so there is no opaque repo callee whose behavior the
-- proof must assume.
-- axioms-end

-- pure-start
/-- A documentation cross-reference for a single annotation token: the domain it
resolves in, the kind of entity it names, the lookup target, and the visible
label. -/
structure TypeRef where
  domain : String
  kind   : String
  target : List Char
  label  : List Char
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The cross-reference is fully pinned to the input token `text`:

  * the domain is always the Python domain `"py"`;
  * the target and the visible label are both exactly the token `text`;
  * the kind is the object kind `"obj"` when the token is `None`, and the class
    kind `"class"` for every other token.

No output component is left free: each of the four components is determined by
`text`, and the kind is forced by whether `text` is the `None` token. -/
def problem_spec_annotationRef (text : List Char) (result : TypeRef) : Prop :=
  result.domain = "py"
    ∧ result.target = text
    ∧ result.label = text
    ∧ result.kind = (if text = "None".toList then "obj" else "class")
-- post-conditions-end

-- impl-start
def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
  let mut kind := "class"
  if text = "None".toList then
    kind := "obj"
  else
    kind := "class"
  return { domain := "py", kind := kind, target := text, label := text }
-- impl-end

-- proof-start
theorem correct_annotationRef :
    ∀ (text : List Char),
      problem_spec_annotationRef text (implementation_annotationRef text) := by
  intro text
  unfold problem_spec_annotationRef implementation_annotationRef
  by_cases h : text = "None".toList <;>
    simp only [h, Id.run, if_pos, pure] <;>
    exact ⟨rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS EXACT/TOTAL: problem_spec_annotationRef fully pins all four TypeRef fields as a function of `text` (domain="py", target=text, label=text, kind = if text="None".toList then "obj" else "class"). No output component is free, so only a behaviorally-correct impl can be proven. No A-legs: meta.json axioms=[], deep_model_references=[], no opaque/axiom decls in Solution.lean; refinement.md marks all ops R/I (op1 R, ops2-5 I), matching the concrete TypeRef record + concrete if. A-leg correspondence therefore vacuous/correct. PYTHONPATH=src; python=python.

SAME-SPEC: all 8 attacks return same_spec=True (impl region edited only; axioms/pure/pre/post byte-identical).

### VERIFICATION (bash scripts/lean_verify.sh <f>; run concurrently in batches of 4):
- atk_1 prepatch bug (partial-domain: kind always "class", never obj for None) => exit 1 (proof fails at line 83 `exact ⟨rfl,rfl,rfl,rfl⟩`, application type mismatch).
- atk_2 inverted branch (obj for non-None, class for None) => exit 1.
- atk_3 boundary (kind obj iff text.length=4; matches "None" and "bool") => exit 1.
- atk_4 wrong domain literal "python" => exit 1.
- atk_5 ungrounded target (target := []) => exit 1.
- atk_6 control-flow-effect on label (label := text.reverse) => exit 1.
- atk_7 control-flow (obj iff "None".isPrefixOf text) => exit 1.
- atk_8 correct echo of the spec branch (gold-equivalent), plain-def form with closing proof => exit 0.
  #print axioms correct_annotationRef => "'correct_annotationRef' does not depend on any axioms" (clean).
  MANDATORY RESOLVE: materialized faithful patch (identical to gold patch.diff) and ran run_resolve('sphinx-doc__sphinx-7454', patch) => RESOLVED=True, COMPLETED=True, note='resolved'.
- positive_control (bundle Solution.lean) => exit 0.

prepatch_reproduced=True: atk_1 encodes the pre-patch make_xref (reftype always 'class'); it does NOT verify against the spec (exit 1), confirming the spec discriminates the F2P bug (assert reftype="obj" for _parse_annotation("None")).

CONCLUSION: The only impl whose correct_ proof closes with clean axioms (atk_8) is behaviorally correct and its faithful patch RESOLVES under the official harness. No same-spec wrong impl closes a clean-axiom proof; all 7 behavioral mutations fail to verify. verify => correct holds here. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

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

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a single type-annotation token as a documentation cross-reference.

When a type annotation in an API signature is turned into documentation, each
bare token of the annotation (a name such as `int`, `List`, or `None`) becomes a
clickable cross-reference into the documentation set. Such a reference carries
four pieces of data:

  * the documentation DOMAIN it resolves in (here always the Python domain,
    `"py"`);
  * the reference KIND, which selects what sort of documented entity the token
    names;
  * the TARGET, the name that is looked up — the token text itself;
  * the visible LABEL shown to the reader — again the token text.

Most tokens name a class-like entity, so their reference kind is the class kind
(`"class"`). The single exception is the token `None`: it does not name a class
but the unique `None` object, so its reference kind is the object kind
(`"obj"`). Both `None` and every other token must yield a cross-reference (so a
`None` annotation is just as clickable as any other) — they differ only in which
kind that reference carries.

So for the token `None` the result is the object-kind reference targeting and
labelled `None`; for any other token `t` the result is the class-kind reference
targeting and labelled `t`. The domain, target, and label are determined by the
token alone; only the kind branches on whether the token is `None`.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Building the
-- cross-reference for a token is spelled out directly below: the four
-- components (domain, kind, target, label) are computed from the token by
-- pure structural data, so there is no opaque repo callee whose behavior the
-- proof must assume.
-- axioms-end

-- pure-start
/-- A documentation cross-reference for a single annotation token: the domain it
resolves in, the kind of entity it names, the lookup target, and the visible
label. -/
structure TypeRef where
  domain : String
  kind   : String
  target : List Char
  label  : List Char
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The cross-reference is fully pinned to the input token `text`:

  * the domain is always the Python domain `"py"`;
  * the target and the visible label are both exactly the token `text`;
  * the kind is the object kind `"obj"` when the token is `None`, and the class
    kind `"class"` for every other token.

No output component is left free: each of the four components is determined by
`text`, and the kind is forced by whether `text` is the `None` token. -/
def problem_spec_annotationRef (text : List Char) (result : TypeRef) : Prop :=
  result.domain = "py"
    ∧ result.target = text
    ∧ result.label = text
    ∧ result.kind = (if text = "None".toList then "obj" else "class")
-- post-conditions-end

-- impl-start
def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
  let mut kind := "class"
  if text = "None".toList then
    kind := "obj"
  else
    kind := "class"
  return { domain := "py", kind := kind, target := text, label := text }
-- impl-end

-- proof-start
theorem correct_annotationRef :
    ∀ (text : List Char),
      problem_spec_annotationRef text (implementation_annotationRef text) := by
  intro text
  unfold problem_spec_annotationRef implementation_annotationRef
  by_cases h : text = "None".toList <;>
    simp only [h, Id.run, if_pos, pure] <;>
    exact ⟨rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS EXACT/TOTAL: problem_spec_annotationRef fully pins all four TypeRef fields as a function of `text` (domain="py", target=text, label=text, kind = if text="None".toList then "obj" else "class"). No output component is free, so only a behaviorally-correct impl can be proven. No A-legs: meta.json axioms=[], deep_model_references=[], no opaque/axiom decls in Solution.lean; refinement.md marks all ops R/I (op1 R, ops2-5 I), matching the concrete TypeRef record + concrete if. A-leg correspondence therefore vacuous/correct. PYTHONPATH=src; python=python.

SAME-SPEC: all 8 attacks return same_spec=True (impl region edited only; axioms/pure/pre/post byte-identical).

### VERIFICATION (bash scripts/lean_verify.sh <f>; run concurrently in batches of 4):
- atk_1 prepatch bug (partial-domain: kind always "class", never obj for None) => exit 1 (proof fails at line 83 `exact ⟨rfl,rfl,rfl,rfl⟩`, application type mismatch).
- atk_2 inverted branch (obj for non-None, class for None) => exit 1.
- atk_3 boundary (kind obj iff text.length=4; matches "None" and "bool") => exit 1.
- atk_4 wrong domain literal "python" => exit 1.
- atk_5 ungrounded target (target := []) => exit 1.
- atk_6 control-flow-effect on label (label := text.reverse) => exit 1.
- atk_7 control-flow (obj iff "None".isPrefixOf text) => exit 1.
- atk_8 correct echo of the spec branch (gold-equivalent), plain-def form with closing proof => exit 0.
  #print axioms correct_annotationRef => "'correct_annotationRef' does not depend on any axioms" (clean).
  MANDATORY RESOLVE: materialized faithful patch (identical to gold patch.diff) and ran run_resolve('sphinx-doc__sphinx-7454', patch) => RESOLVED=True, COMPLETED=True, note='resolved'.
- positive_control (bundle Solution.lean) => exit 0.

prepatch_reproduced=True: atk_1 encodes the pre-patch make_xref (reftype always 'class'); it does NOT verify against the spec (exit 1), confirming the spec discriminates the F2P bug (assert reftype="obj" for _parse_annotation("None")).

CONCLUSION: The only impl whose correct_ proof closes with clean axioms (atk_8) is behaviorally correct and its faithful patch RESOLVES under the official harness. No same-spec wrong impl closes a clean-axiom proof; all 7 behavioral mutations fail to verify. verify => correct holds here. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled callee = post-patch make_xref(text) (inner helper of _parse_annotation, sphinx/domains/python.py:73), viewed as its four pending_xref fields (refdomain, reftype, reftarget, label). Confirmed base_commit source at aca3f825 via git worktree: pre-patch make_xref returns reftype='class' for every token; gold patch branches reftype='obj' iff text=='None'. make_xref is a total, pure function of text.

Spec problem_spec_annotationRef: domain="py" ∧ target=text ∧ label=text ∧ kind=(if text="None".toList then "obj" else "class"). Field-by-field this is an exact transliteration of the real post-patch behavior over the FULL token domain: (1) refdomain='py' always — matches; (2) reftype = 'obj' iff text=='None' using exact string equality, so near-misses none/NONE/Non/Nonee/NoneType all correctly get 'class' (case-sensitive, no prefix relaxation) — matches; (3) reftarget=text verbatim — matches; (4) label = str(nodes.Text(text)) = text verbatim — matches. List Char ↔ str is the per-code-point bijection.

Neither too strong nor too weak: the spec is a full functional characterization — every one of the four output components is pinned as a function of text (nothing left free ⇒ not too weak), and each pinned value is exactly what the real callee emits (nothing over-constrained ⇒ not too strong / no drift). The Lean impl is total over all List Char, matching make_xref's totality over str; no input escapes the spec's coverage.

Searched for a diverging input across the discriminating boundary (None vs near-misses, empty string, dotted/random identifiers, case variants) — none found; on every token the spec's forced fields equal make_xref's output.

Proof rigor: Solution.lean compiles under scripts/lean_verify.sh (exit 0, no sorry) and #print axioms correct_annotationRef = [propext, Quot.sound] — clean, no sorryAx, proof is real. axiom_check.py is a legitimate skip stub (no consumed callee axiom; fields are concrete TypeRef data, None-branch is a concrete if). conformance_check.py binds the shadow to the REAL patched code path via _parse_annotation and differential-tests all four node fields over 1e5 tokens with pinned seed 7454.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction) for sphinx-doc__sphinx-7454 (lean).

Spec view computed via markers.spec_view(Solution.lean, LeanBackend): impl and proof regions are elided (impl-start/proof-start collapse to placeholders); remaining = imports, docstring, axioms note, `TypeRef` structure, and the `problem_spec_annotationRef` post-condition. same_spec(Solution, Solution_prepatch)=True and spec_view equal=True (prepatch differs only in elided impl/proof), so the frozen spec is stable.

Mechanical G-LEAK (leakage.screen over the spec view, judged vs public problem_statement only): PASSED, hard_failures=[]. Consistent with recorded G-LEAK pass. _patch_changed_symbols(gold)=∅ (the gold hunk adds no def/class), so the symbol-collision vector is empty.

Gold-reconstruction check by vector:
- No diff markers, no gold-patch line reproduced. Gold line `reftype = 'obj'` / `refdomain='py', reftype=reftype, reftarget=text` do NOT appear; the spec is written in abstracted vocabulary (`kind`, `domain`, `target`, `label`), not the repo kwargs (`reftype`/`refdomain`/`reftarget`).
- No patched file path (`sphinx/domains/python.py`) or dotted module path in the view.
- No patched repo symbols: `make_xref`, `pending_xref`, `_parse_annotation`, `reftype`, `refdomain` are all abstracted (`annotationRef`/`TypeRef`); none leaks localization.
- No bug/fix narration terms.

The literal values `"obj"`/`"class"`/`"py"` and the `if text = "None" then "obj" else "class"` post-condition are the spec pinning correct OUTPUT behavior — the legitimate purpose of a spec, not edit-localization. The public problem_statement already discloses the entire target behavior (None in a signature type hint must be clickable/link to the None singleton docs, like other tokens such as int do), so the None-vs-other distinction is not information beyond the public task. A solver reading the spec view cannot recover WHERE (file/function `make_xref`) or HOW (the `reftype` kwarg branch edit) — localization is preserved.

Verdict: NO-LEAKAGE. Spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
