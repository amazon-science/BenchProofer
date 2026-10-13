# P2 adversarial audit — sphinx-doc__sphinx-9461

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,12 +38,10 @@
 -- impl-start
 def implementation_propertyPrefix
     (isAbstract isClassLevel : Bool) : String := Id.run do
-  let mut words : List String := []
+  -- PREPATCH BUG: seed ["property"], only abstract prepended, class ignored
+  let mut words : List String := ["property"]
   if isAbstract then
-    words := words ++ ["abstract"]
-  if isClassLevel then
-    words := words ++ ["class"]
-  words := words ++ ["property"]
+    words := ["abstract"] ++ words
   return String.intercalate " " words ++ " "
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,11 +38,12 @@
 -- impl-start
 def implementation_propertyPrefix
     (isAbstract isClassLevel : Bool) : String := Id.run do
+  -- ORDER SWAP: class appended before abstract
   let mut words : List String := []
+  if isClassLevel then
+    words := words ++ ["class"]
   if isAbstract then
     words := words ++ ["abstract"]
-  if isClassLevel then
-    words := words ++ ["class"]
   words := words ++ ["property"]
   return String.intercalate " " words ++ " "
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
   let mut words : List String := []
   if isAbstract then
     words := words ++ ["abstract"]
-  if isClassLevel then
+  if !isClassLevel then
     words := words ++ ["class"]
   words := words ++ ["property"]
   return String.intercalate " " words ++ " "
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,8 @@
   if isClassLevel then
     words := words ++ ["class"]
   words := words ++ ["property"]
-  return String.intercalate " " words ++ " "
+  -- BOUNDARY: forget trailing space
+  return String.intercalate " " words
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,11 @@
 -- impl-start
 def implementation_propertyPrefix
     (isAbstract isClassLevel : Bool) : String := Id.run do
+  -- PARTIAL DOMAIN: only handle class word when abstract also set
   let mut words : List String := []
   if isAbstract then
     words := words ++ ["abstract"]
-  if isClassLevel then
+  if isClassLevel && isAbstract then
     words := words ++ ["class"]
   words := words ++ ["property"]
   return String.intercalate " " words ++ " "
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,8 @@
   if isClassLevel then
     words := words ++ ["class"]
   words := words ++ ["property"]
-  return String.intercalate " " words ++ " "
+  -- WRONG SEPARATOR: intercalate with double space
+  return String.intercalate "  " words ++ " "
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,8 @@
     words := words ++ ["abstract"]
   if isClassLevel then
     words := words ++ ["class"]
-  words := words ++ ["property"]
+  -- WRONG BASE WORD
+  words := words ++ ["attribute"]
   return String.intercalate " " words ++ " "
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Behavior: rendering the leading modifier words shown before a documented
read-only attribute. The available modifier toggles are an "abstract" flag and a
"class-level" flag. The rendered text is the present modifier words, in a set
order, followed by the base word, joined by single spaces, with one trailing
space. This module pins exactly which words appear and in what order for every
combination of the two toggles.
-/

-- axioms-start
-- No outside callees are consumed: the behavior is modeled deeply from its
-- inputs (the two boolean toggles), so there are no opaque declarations and no
-- consumed/`_prop` axioms.
-- axioms-end

-- pure-start
/-- The ordered list of words rendered before joining. The optional modifier
words precede the base word in a set order. -/
def prefixWords (isAbstract isClassLevel : Bool) : List String :=
  (if isAbstract then ["abstract"] else []) ++
  (if isClassLevel then ["class"] else []) ++
  ["property"]
-- pure-end

-- post-conditions-start
/-- The rendered prefix is the ordered modifier words joined by single spaces,
with one trailing space appended. Both toggles independently control whether
their word appears, the base word is always present and always last, and the
order is: abstract, then class-level, then base. -/
def problem_spec_propertyPrefix
    (isAbstract isClassLevel : Bool) (result : String) : Prop :=
  result = String.intercalate " " (prefixWords isAbstract isClassLevel) ++ " "
-- post-conditions-end

-- impl-start
def implementation_propertyPrefix
    (isAbstract isClassLevel : Bool) : String := Id.run do
  let mut words : List String := []
  if isAbstract then
    words := words ++ ["abstract"]
  if isClassLevel then
    words := words ++ ["class"]
  words := words ++ ["property"]
  return String.intercalate " " words ++ " "
-- impl-end

-- proof-start
theorem correct_propertyPrefix : ∀ (isAbstract isClassLevel : Bool),
    problem_spec_propertyPrefix isAbstract isClassLevel
      (implementation_propertyPrefix isAbstract isClassLevel) := by
  intro isAbstract isClassLevel
  unfold problem_spec_propertyPrefix implementation_propertyPrefix prefixWords
  cases isAbstract <;> cases isClassLevel <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: problem_spec_propertyPrefix pins EXACT string equality (result = String.intercalate " " (prefixWords isAbstract isClassLevel) ++ " ") over a finite, TOTAL, unguarded 2-bool domain. This is the tightest possible spec: any impl that verifies must reproduce the exact oracle string on all 4 inputs, so every behaviorally-distinct impl is mathematically forced to fail closure.

Same_spec: all 7 attacks return True (spec/axioms/pure/post regions byte-identical; only impl region edited). Verified via swebench_unified.markers.same_spec with lean backend.

Verification (scripts/lean_verify.sh, timeout 300, run concurrently in 2 batches of 4):
- pos_control (gold impl): EXIT=0 verifies. #print axioms correct_propertyPrefix => 'does not depend on any axioms' (clean, no sorry).
- atk_1 (prepatch bug: seed ["property"], only abstract prepended, class toggle ignored): EXIT=1, rfl fails on case false.true and true.true. PREPATCH BUG REPRODUCED (renders "property "/"abstract property " instead of "class property "/"abstract class property ").
- atk_2 (order swap: class appended before abstract): EXIT=1, rfl fails on case true.true.
- atk_3 (control-flow-effect: negated guard !isClassLevel): EXIT=1, rfl fails on all 4 cases.
- atk_4 (boundary: drop trailing space): EXIT=1, rfl fails.
- atk_5 (partial-domain: emit class only when isClassLevel && isAbstract): EXIT=1, rfl fails.
- atk_6 (wrong separator: intercalate with double space): EXIT=1, rfl fails.
- atk_7 (ungrounded/wrong base word: "attribute" instead of "property"): EXIT=1, rfl fails.

Covers partial-domain (atk_5), boundary (atk_4), control-flow-effect (atk_3), wrong-value/ungrounded-echo (atk_6, atk_7), ordering (atk_2), and the actual prepatch bug (atk_1) — 7 DISTINCT wrong impls, all same-spec, ALL FAIL to close. Since NO wrong impl produced a closing clean-axiom proof, there is no faithful patch to materialize/resolve; the mandatory resolve step is vacuous (nothing to run). Nothing exhibits verify without correct.

Refinement.md / A-leg audit: mapping.md and refinement.md declare ZERO A-legs and an EMPTY axioms region. The 5 legs are R (steps 2,3: Python 'flag' in self.options membership -> Bool isAbstract/isClassLevel) or I (steps 1,4,5: []-seed, ++["property"], String.intercalate " " ++ " " literal transliterations). No kind-3 leg (no unchanged callee is axiomatized). The modeled routine PyProperty.get_signature_prefix is a pure, total, deterministic 2-bool->string transformation; deep modeling with no opaque dependency is legitimate and §3-compliant (deeply-modeled changed op must not be axiomatized). The empty-axioms claim is honest: the positive-control proof depends on no axioms at all. Non-expressible introspection sites (autodoc/inspect.py) are correctly excluded per §0.7 (would require axiomatizing the very reflection callees under test). No A-correspondence exists to be gamed.

Spec is a sound correctness oracle: verify => correct holds. VERDICT SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

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
Behavior: rendering the leading modifier words shown before a documented
read-only attribute. The available modifier toggles are an "abstract" flag and a
"class-level" flag. The rendered text is the present modifier words, in a set
order, followed by the base word, joined by single spaces, with one trailing
space. This module pins exactly which words appear and in what order for every
combination of the two toggles.
-/

-- axioms-start
-- No outside callees are consumed: the behavior is modeled deeply from its
-- inputs (the two boolean toggles), so there are no opaque declarations and no
-- consumed/`_prop` axioms.
-- axioms-end

-- pure-start
/-- The ordered list of words rendered before joining. The optional modifier
words precede the base word in a set order. -/
def prefixWords (isAbstract isClassLevel : Bool) : List String :=
  (if isAbstract then ["abstract"] else []) ++
  (if isClassLevel then ["class"] else []) ++
  ["property"]
-- pure-end

-- post-conditions-start
/-- The rendered prefix is the ordered modifier words joined by single spaces,
with one trailing space appended. Both toggles independently control whether
their word appears, the base word is always present and always last, and the
order is: abstract, then class-level, then base. -/
def problem_spec_propertyPrefix
    (isAbstract isClassLevel : Bool) (result : String) : Prop :=
  result = String.intercalate " " (prefixWords isAbstract isClassLevel) ++ " "
-- post-conditions-end

-- impl-start
def implementation_propertyPrefix
    (isAbstract isClassLevel : Bool) : String := Id.run do
  let mut words : List String := []
  if isAbstract then
    words := words ++ ["abstract"]
  if isClassLevel then
    words := words ++ ["class"]
  words := words ++ ["property"]
  return String.intercalate " " words ++ " "
-- impl-end

-- proof-start
theorem correct_propertyPrefix : ∀ (isAbstract isClassLevel : Bool),
    problem_spec_propertyPrefix isAbstract isClassLevel
      (implementation_propertyPrefix isAbstract isClassLevel) := by
  intro isAbstract isClassLevel
  unfold problem_spec_propertyPrefix implementation_propertyPrefix prefixWords
  cases isAbstract <;> cases isClassLevel <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: problem_spec_propertyPrefix pins EXACT string equality (result = String.intercalate " " (prefixWords isAbstract isClassLevel) ++ " ") over a finite, TOTAL, unguarded 2-bool domain. This is the tightest possible spec: any impl that verifies must reproduce the exact oracle string on all 4 inputs, so every behaviorally-distinct impl is mathematically forced to fail closure.

Same_spec: all 7 attacks return True (spec/axioms/pure/post regions byte-identical; only impl region edited). Verified via swebench_unified.markers.same_spec with lean backend.

Verification (scripts/lean_verify.sh, timeout 300, run concurrently in 2 batches of 4):
- pos_control (gold impl): EXIT=0 verifies. #print axioms correct_propertyPrefix => 'does not depend on any axioms' (clean, no sorry).
- atk_1 (prepatch bug: seed ["property"], only abstract prepended, class toggle ignored): EXIT=1, rfl fails on case false.true and true.true. PREPATCH BUG REPRODUCED (renders "property "/"abstract property " instead of "class property "/"abstract class property ").
- atk_2 (order swap: class appended before abstract): EXIT=1, rfl fails on case true.true.
- atk_3 (control-flow-effect: negated guard !isClassLevel): EXIT=1, rfl fails on all 4 cases.
- atk_4 (boundary: drop trailing space): EXIT=1, rfl fails.
- atk_5 (partial-domain: emit class only when isClassLevel && isAbstract): EXIT=1, rfl fails.
- atk_6 (wrong separator: intercalate with double space): EXIT=1, rfl fails.
- atk_7 (ungrounded/wrong base word: "attribute" instead of "property"): EXIT=1, rfl fails.

Covers partial-domain (atk_5), boundary (atk_4), control-flow-effect (atk_3), wrong-value/ungrounded-echo (atk_6, atk_7), ordering (atk_2), and the actual prepatch bug (atk_1) — 7 DISTINCT wrong impls, all same-spec, ALL FAIL to close. Since NO wrong impl produced a closing clean-axiom proof, there is no faithful patch to materialize/resolve; the mandatory resolve step is vacuous (nothing to run). Nothing exhibits verify without correct.

Refinement.md / A-leg audit: mapping.md and refinement.md declare ZERO A-legs and an EMPTY axioms region. The 5 legs are R (steps 2,3: Python 'flag' in self.options membership -> Bool isAbstract/isClassLevel) or I (steps 1,4,5: []-seed, ++["property"], String.intercalate " " ++ " " literal transliterations). No kind-3 leg (no unchanged callee is axiomatized). The modeled routine PyProperty.get_signature_prefix is a pure, total, deterministic 2-bool->string transformation; deep modeling with no opaque dependency is legitimate and §3-compliant (deeply-modeled changed op must not be axiomatized). The empty-axioms claim is honest: the positive-control proof depends on no axioms at all. Non-expressible introspection sites (autodoc/inspect.py) are correctly excluded per §0.7 (would require axiomatizing the very reflection callees under test). No A-correspondence exists to be gamed.

Spec is a sound correctness oracle: verify => correct holds. VERDICT SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sphinx-doc__sphinx-9461 lean bundle. Modeled function: post-patch PyProperty.get_signature_prefix. same_spec(Solution, prepatch)=True via LeanBackend.language tables (spec region byte-identical; only impl+proof differ). Solution.lean compiles (lean_verify exit 0) and `#print axioms correct_propertyPrefix` reports no axiom dependence (real proof, no sorryAx). The post-patch real callee builds prefix=[]; appends 'abstract' iff 'abstractmethod' in options; 'class' iff 'classmethod' in options; then 'property'; returns ' '.join(prefix)+' '. Output depends solely on the two flag-presence predicates; `sig` is genuinely unused (confirmed in base-commit worktree source). The model abstracts these to two Bools — a total bijection over the flag-present predicate. Input domain is exactly 2 booleans (4 combinations), so it is finite and exhaustively coverable. Lean #eval over all 4 inputs yields 'property ', 'abstract property ', 'class property ', 'abstract class property ', matching the post-patch Python exactly. No input exists where the modeled spec disagrees with the real callee; the equality spec accepts precisely the correct output (not over-strong) and does not drift. G-DIFF is legitimately discriminating: prepatch keeps the ['property'] seed and ignores isClassLevel, so it renders 'property '/'abstract property ' instead of 'class property '/'abstract class property ' on isClassLevel=true, failing its carried rfl proof. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged on the CONSUMER SPEC VIEW of Solution.lean (markers.spec_view), against the public problem_statement ONLY (not hints_text; refinement.md/mapping.md are auditor-side, not part of the spec view). Mechanical G-LEAK screen (leakage.screen) PASSES: hard_failures=[], warnings=[]. Manual review confirms:

(1) No diff markers (@@, diff --git, +++, index), no patched file path (sphinx/domains/python.py) or dotted module path in the view.

(2) No gold-patch changed line reproduced (>=8 chars normalized). The gold hunks build ['property']/append('abstract')/append('class') in Python; the spec-view pure/post-condition regions use Lean String.intercalate/List String, which do not textually reproduce any gold line.

(3) Spec-view identifiers (prefixWords, isAbstract, isClassLevel, problem_spec_propertyPrefix, correct/implementation_propertyPrefix) embed NO distinctive patched repo symbol — patch touches PyProperty, PropertyDocumenter, get_signature_prefix, isclassmethod, getdoc, import_object, add_directive_header, handle_signature, is_filtered_inherited_member, ispartial; none appears (verbatim or embedded) in the view. 'propertyPrefix' contains 'property' but 'property' is not a patched def/class symbol.

(4) No narration words (bug/fix/pre-patch/etc.) in any spec-view comment. The docstrings describe behavior abstractly ('leading modifier words', 'abstract flag', 'class-level flag', 'base word') with no reference to sphinx, classmethod/property options, or the edit.

(5) The 'Pre-patch behavior' narration comment lives in the IMPL region of Solution_prepatch.lean, which the spec_view projection ELIDES; same_spec(patched, prepatch)=True, so the discriminating differential is confined to the elided impl region and never reaches the consumer.

Gold-reconstruction: the spec legitimately pins the intended output of modeled site-1 (word ordering abstract<class<property, joined by spaces + trailing space) — the proper, unavoidable content of any spec. It does NOT reveal the multi-file gold edit (option-flag registration, descriptor introspection in autodoc/__init__.py, MRO getdoc walk in util/inspect.py), file/symbol names, or the diff shape. A solver cannot reconstruct the gold patch from this abstract string-building contract. No leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.