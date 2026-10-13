# P2 adversarial audit — sphinx-doc__sphinx-9230

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The postcondition `result = extractTypeName arg` is an EXACT functional pin to a total, faithful deep model, so every same-spec verifying impl is provably pointwise-equal to the gold behavior (str.rsplit(None,1)). The one verifying attack (atk_7, ungrounded-oracle echo of extractTypeName) has a faithful patch that RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,11 +57,10 @@
 -- impl-start
 def implementation_paramField (arg : List Char) :
     Option (List Char × List Char) := Id.run do
-  let stripped := dropTrailingSpaces arg
-  let revd := stripped.reverse
-  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
-  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
-  if ty.isEmpty then
+  let s := arg.dropWhile isSpace
+  let ty := s.takeWhile (fun c => !isSpace c)
+  let nm := (s.dropWhile (fun c => !isSpace c)).dropWhile isSpace
+  if ty.isEmpty || nm.isEmpty then
     return none
   return some (ty, nm)
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
   if ty.isEmpty then
     return none
-  return some (ty, nm)
+  return some (nm, ty)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,8 +61,6 @@
   let revd := stripped.reverse
   let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
   let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
-  if ty.isEmpty then
-    return none
   return some (ty, nm)
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
   let stripped := dropTrailingSpaces arg
   let revd := stripped.reverse
   let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
-  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
+  let ty := (revd.dropWhile (fun c => !isSpace c)).reverse
   if ty.isEmpty then
     return none
   return some (ty, nm)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
     Option (List Char × List Char) := Id.run do
   let stripped := dropTrailingSpaces arg
   let revd := stripped.reverse
-  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
+  let nm := (revd.takeWhile (fun c => isSpace c)).reverse
   let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
   if ty.isEmpty then
     return none
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,8 +57,7 @@
 -- impl-start
 def implementation_paramField (arg : List Char) :
     Option (List Char × List Char) := Id.run do
-  let stripped := dropTrailingSpaces arg
-  let revd := stripped.reverse
+  let revd := arg.reverse
   let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
   let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
   if ty.isEmpty then
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -56,24 +56,13 @@
 
 -- impl-start
 def implementation_paramField (arg : List Char) :
-    Option (List Char × List Char) := Id.run do
-  let stripped := dropTrailingSpaces arg
-  let revd := stripped.reverse
-  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
-  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
-  if ty.isEmpty then
-    return none
-  return some (ty, nm)
+    Option (List Char × List Char) :=
+  extractTypeName arg
 -- impl-end
 
 -- proof-start
 theorem correct_paramField : ∀ (arg : List Char),
     problem_spec_paramField arg (implementation_paramField arg) := by
   intro arg
-  unfold problem_spec_paramField implementation_paramField extractTypeName
-  simp only [Id.run]
-  by_cases h : (dropTrailingSpaces
-      ((dropTrailingSpaces arg).reverse.dropWhile (fun c => !isSpace c)).reverse).isEmpty
-  · simp only [h, if_true]; rfl
-  · simp only [h]; rfl
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior: the decomposition of a
-- field-argument string into its type and name is modeled DEEPLY below
-- (`extractTypeName`), so there is no `opaque` callee and no consumed `_prop`
-- axiom here.
-- axioms-end

-- pure-start
/-- The code points a Python `str` whitespace split treats as separators
(exactly the `str.isspace` singletons): `\t \n \v \f \r` (`U+0009`–`U+000D`),
the information separators `U+001C`–`U+001F`, space, `U+0085` (NEL),
`U+00A0` (NBSP), `U+1680`, `U+2000`–`U+200A`, `U+2028`, `U+2029`, `U+202F`,
`U+205F` and `U+3000`. -/
def isSpace (c : Char) : Bool :=
  let n := c.toNat
  (0x09 ≤ n && n ≤ 0x0d) || (0x1c ≤ n && n ≤ 0x20) ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029 ||
  n == 0x202f || n == 0x205f || n == 0x3000

/-- Remove every trailing whitespace character from a character string,
preserving the rest (including any leading or interior whitespace). -/
def dropTrailingSpaces (cs : List Char) : List Char :=
  (cs.reverse.dropWhile isSpace).reverse

/-- Decompose a parameter-field specification of the form `<type> <name>` — where
the *type* part may itself contain interior whitespace — into its type and its
name.

The **name** is the final whitespace-delimited token of the string; the **type**
is the remaining prefix once that token and the whitespace separating it have
been removed (the type keeps its own leading and interior whitespace). Leading
and trailing whitespace of the whole string is not significant.

Returns `none` exactly when the string has fewer than two whitespace-delimited
tokens (so no type/name pair can be formed). -/
def extractTypeName (arg : List Char) : Option (List Char × List Char) :=
  let stripped := dropTrailingSpaces arg
  let revd := stripped.reverse
  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
  if ty.isEmpty then none else some (ty, nm)
-- pure-end

-- post-conditions-start
/-- The result is the type/name decomposition of the field-argument string: the
name is its final whitespace-delimited token and the type is the remaining
prefix, or `none` when no such pair exists. -/
def problem_spec_paramField (arg : List Char)
    (result : Option (List Char × List Char)) : Prop :=
  result = extractTypeName arg
-- post-conditions-end

-- impl-start
def implementation_paramField (arg : List Char) :
    Option (List Char × List Char) := Id.run do
  let stripped := dropTrailingSpaces arg
  let revd := stripped.reverse
  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
  if ty.isEmpty then
    return none
  return some (ty, nm)
-- impl-end

-- proof-start
theorem correct_paramField : ∀ (arg : List Char),
    problem_spec_paramField arg (implementation_paramField arg) := by
  intro arg
  unfold problem_spec_paramField implementation_paramField extractTypeName
  simp only [Id.run]
  by_cases h : (dropTrailingSpaces
      ((dropTrailingSpaces arg).reverse.dropWhile (fun c => !isSpace c)).reverse).isEmpty
  · simp only [h, if_true]; rfl
  · simp only [h]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of sphinx-doc__sphinx-9230 lean bundle. verifier scripts/lean_verify.sh; python python. Scratch same_spec=True confirmed for ALL 7 attacks (swebench_unified.markers.same_spec, lean backend).

SPEC STRUCTURE: postcondition is `result = extractTypeName arg` — an exact functional equality to a TOTAL deep model (extractTypeName). Any verifying same-spec impl must therefore be pointwise-equal to extractTypeName; soundness reduces entirely to the fidelity of the A-legs (isSpace set and extractTypeName==str.rsplit(None,1)).

### A-LEG AUDIT (the focus per instructions):
- isSpace: swept ALL of Unicode (0x0..0x10FFFF, skip surrogates) comparing model isSpace(n) vs Python ("a"+c+"b").split()==['a','b']. 0 mismatches -> whitespace separator set is exact.
- extractTypeName == str.rsplit(None,1): boundary cases (leading/interior/trailing ws, maxsplit edge, empty, all-ws, NBSP/NEL/U+2028/control separators) all match; heavy fuzz 600,000 random inputs over full WS pool: 0 mismatches. Official axiom_check.py (G-AX, 220,030 inputs seed=9230) exit 0; conformance_check.py (G-CONF, 220,026 inputs) exit 0.

refinement.md AUDIT: 6 legs, tags R / A-reference / I only — NO kind-3 (changed-inexpressible). A-reference legs 2-4 model str.rsplit(None,1) deeply and their correspondence to the real callee holds (validated above / by G-AX). axioms region is empty (no opaque callee, no consumed _prop) — consistent with mapping.md.

### ATTACKS (all same_spec=True; commands: `bash scripts/lean_verify.sh <path>`):
- atk_1 prepatch FIRST-split bug (dropLeadingSpaces+takeWhile): CE 'dict(str, str) opc_meta' -> ('dict(str,','str) opc_meta'). exit=1 (does NOT close). Reproduces the prepatch bug.
- atk_2 control-flow-effect, swapped pair some(nm,ty): CE swaps type/name. exit=1.
- atk_3 partial-domain, dropped none-guard (always some): CE 'x' -> ('','x') vs None. exit=1.
- atk_4 boundary, no dropTrailingSpaces on ty (keeps separator ws): CE type 'dict(str, str) '. exit=1.
- atk_5 wrong predicate, name = takeWhile isSpace (empty name): CE name ''. exit=1.
- atk_6 no whole-arg trailing strip (arg.reverse directly): CE '  a b  ' -> ('  a b','') vs ('  a','b'). exit=1.
- atk_7 ungrounded-oracle echo (implementation := extractTypeName arg, proof `intro arg; rfl`): exit=0 VERIFIES. `#print axioms correct_paramField` => 'does not depend on any axioms' (clean). Per protocol materialized its faithful refined patch (byte-identical to gold rsplit patch, since atk_7 == extractTypeName == gold behavior) and RAN official harness: run_resolve('sphinx-doc__sphinx-9230', patch) => completed=True, resolved=True, attempts=1, flaky=False. Patch RESOLVES -> does NOT break spec.

Positive control pos.lean (gold Solution.lean) exit=0; `#print axioms` => [propext] (clean).

CONCLUSION: 6 genuinely-wrong same-spec impls (partial-domain, boundary, control-flow-effect, wrong-predicate, prepatch-bug) all FAIL to close against the exact-pin postcondition; the only verifying attack is a faithful echo whose materialized patch RESOLVES. No verify⇏correct gap found. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The postcondition `result = extractTypeName arg` is an EXACT functional pin to a total, faithful deep model, so every same-spec verifying impl is provably pointwise-equal to the gold behavior (str.rsplit(None,1)). The one verifying attack (atk_7, ungrounded-oracle echo of extractTypeName) has a faithful patch that RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior: the decomposition of a
-- field-argument string into its type and name is modeled DEEPLY below
-- (`extractTypeName`), so there is no `opaque` callee and no consumed `_prop`
-- axiom here.
-- axioms-end

-- pure-start
/-- The code points a Python `str` whitespace split treats as separators
(exactly the `str.isspace` singletons): `\t \n \v \f \r` (`U+0009`–`U+000D`),
the information separators `U+001C`–`U+001F`, space, `U+0085` (NEL),
`U+00A0` (NBSP), `U+1680`, `U+2000`–`U+200A`, `U+2028`, `U+2029`, `U+202F`,
`U+205F` and `U+3000`. -/
def isSpace (c : Char) : Bool :=
  let n := c.toNat
  (0x09 ≤ n && n ≤ 0x0d) || (0x1c ≤ n && n ≤ 0x20) ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029 ||
  n == 0x202f || n == 0x205f || n == 0x3000

/-- Remove every trailing whitespace character from a character string,
preserving the rest (including any leading or interior whitespace). -/
def dropTrailingSpaces (cs : List Char) : List Char :=
  (cs.reverse.dropWhile isSpace).reverse

/-- Decompose a parameter-field specification of the form `<type> <name>` — where
the *type* part may itself contain interior whitespace — into its type and its
name.

The **name** is the final whitespace-delimited token of the string; the **type**
is the remaining prefix once that token and the whitespace separating it have
been removed (the type keeps its own leading and interior whitespace). Leading
and trailing whitespace of the whole string is not significant.

Returns `none` exactly when the string has fewer than two whitespace-delimited
tokens (so no type/name pair can be formed). -/
def extractTypeName (arg : List Char) : Option (List Char × List Char) :=
  let stripped := dropTrailingSpaces arg
  let revd := stripped.reverse
  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
  if ty.isEmpty then none else some (ty, nm)
-- pure-end

-- post-conditions-start
/-- The result is the type/name decomposition of the field-argument string: the
name is its final whitespace-delimited token and the type is the remaining
prefix, or `none` when no such pair exists. -/
def problem_spec_paramField (arg : List Char)
    (result : Option (List Char × List Char)) : Prop :=
  result = extractTypeName arg
-- post-conditions-end

-- impl-start
def implementation_paramField (arg : List Char) :
    Option (List Char × List Char) := Id.run do
  let stripped := dropTrailingSpaces arg
  let revd := stripped.reverse
  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
  if ty.isEmpty then
    return none
  return some (ty, nm)
-- impl-end

-- proof-start
theorem correct_paramField : ∀ (arg : List Char),
    problem_spec_paramField arg (implementation_paramField arg) := by
  intro arg
  unfold problem_spec_paramField implementation_paramField extractTypeName
  simp only [Id.run]
  by_cases h : (dropTrailingSpaces
      ((dropTrailingSpaces arg).reverse.dropWhile (fun c => !isSpace c)).reverse).isEmpty
  · simp only [h, if_true]; rfl
  · simp only [h]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of sphinx-doc__sphinx-9230 lean bundle. verifier scripts/lean_verify.sh; python python. Scratch same_spec=True confirmed for ALL 7 attacks (swebench_unified.markers.same_spec, lean backend).

SPEC STRUCTURE: postcondition is `result = extractTypeName arg` — an exact functional equality to a TOTAL deep model (extractTypeName). Any verifying same-spec impl must therefore be pointwise-equal to extractTypeName; soundness reduces entirely to the fidelity of the A-legs (isSpace set and extractTypeName==str.rsplit(None,1)).

### A-LEG AUDIT (the focus per instructions):
- isSpace: swept ALL of Unicode (0x0..0x10FFFF, skip surrogates) comparing model isSpace(n) vs Python ("a"+c+"b").split()==['a','b']. 0 mismatches -> whitespace separator set is exact.
- extractTypeName == str.rsplit(None,1): boundary cases (leading/interior/trailing ws, maxsplit edge, empty, all-ws, NBSP/NEL/U+2028/control separators) all match; heavy fuzz 600,000 random inputs over full WS pool: 0 mismatches. Official axiom_check.py (G-AX, 220,030 inputs seed=9230) exit 0; conformance_check.py (G-CONF, 220,026 inputs) exit 0.

refinement.md AUDIT: 6 legs, tags R / A-reference / I only — NO kind-3 (changed-inexpressible). A-reference legs 2-4 model str.rsplit(None,1) deeply and their correspondence to the real callee holds (validated above / by G-AX). axioms region is empty (no opaque callee, no consumed _prop) — consistent with mapping.md.

### ATTACKS (all same_spec=True; commands: `bash scripts/lean_verify.sh <path>`):
- atk_1 prepatch FIRST-split bug (dropLeadingSpaces+takeWhile): CE 'dict(str, str) opc_meta' -> ('dict(str,','str) opc_meta'). exit=1 (does NOT close). Reproduces the prepatch bug.
- atk_2 control-flow-effect, swapped pair some(nm,ty): CE swaps type/name. exit=1.
- atk_3 partial-domain, dropped none-guard (always some): CE 'x' -> ('','x') vs None. exit=1.
- atk_4 boundary, no dropTrailingSpaces on ty (keeps separator ws): CE type 'dict(str, str) '. exit=1.
- atk_5 wrong predicate, name = takeWhile isSpace (empty name): CE name ''. exit=1.
- atk_6 no whole-arg trailing strip (arg.reverse directly): CE '  a b  ' -> ('  a b','') vs ('  a','b'). exit=1.
- atk_7 ungrounded-oracle echo (implementation := extractTypeName arg, proof `intro arg; rfl`): exit=0 VERIFIES. `#print axioms correct_paramField` => 'does not depend on any axioms' (clean). Per protocol materialized its faithful refined patch (byte-identical to gold rsplit patch, since atk_7 == extractTypeName == gold behavior) and RAN official harness: run_resolve('sphinx-doc__sphinx-9230', patch) => completed=True, resolved=True, attempts=1, flaky=False. Patch RESOLVES -> does NOT break spec.

Positive control pos.lean (gold Solution.lean) exit=0; `#print axioms` => [propext] (clean).

CONCLUSION: 6 genuinely-wrong same-spec impls (partial-domain, boundary, control-flow-effect, wrong-predicate, prepatch-bug) all FAIL to close against the exact-pin postcondition; the only verifying attack is a faithful echo whose materialized patch RESOLVES. No verify⇏correct gap found. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function (extractTypeName / problem_spec_paramField) and the real repo callee (str.rsplit(None, 1) as used at sphinx/util/docfields.py:298-307). Evidence:

1. Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean-tables) = True; spec_view confirms axioms/pure/post-conditions regions unchanged. The prepatch's extractTypeName/spec is identical (bug lives only in the impl region), so the shared spec is the audited object.

2. Lean proof is real: scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). `#print axioms correct_paramField` -> depends only on [propext]; no sorryAx. Proof is definitional (impl Id.run do unfolds to extractTypeName).

3. Model == real callee, verified against actual Python:
   - Whitespace set: isSpace exactly equals Python's str.split(None) separator set over ALL of Unicode (29 code points; lean-only=[], py-only=[], match=True). Includes U+001C-001F, U+0085, U+00A0, U+1680, U+2000-200A, U+2028/9, U+202F, U+205F, U+3000.
   - Semantics: rsplit(None,1) preserves leading/interior whitespace on the type but strips trailing; the model (dropTrailingSpaces only on the type prefix, leading kept) matches. Confirmed on '  dict a' -> ('  dict','a'), ' foo   bar ' -> (' foo','bar'), '  a' -> ValueError->none, '\x85a\x85b' -> ('\x85a','b').
   - Differential test: exhaustive over all strings len<=6 from {a,b,space,U+001C} = 0 mismatches; 500,000 random fuzz over {8 whitespace kinds + a b ( , )}, len 0-8, seed 9230 = 0 mismatches.

The none <-> ValueError(<2 tokens) mapping is exact; the (ty,nm) pair is consumed verbatim downstream (identity), so pinning the pair pins the observable rendering. The spec is neither too strong nor drifted from real repo behavior on any probed input. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (solver-visible projection of Solution.lean) specifies the correct type/name decomposition (name = final whitespace-delimited token; type = remaining prefix with trailing whitespace stripped, interior/leading whitespace preserved), with impl and proof elided. same_spec(Solution.lean, Solution_prepatch.lean)=True, so the spec view is identical with or without the gold patch — structurally incapable of localizing the edit. Mechanical G-LEAK screen passes (no diff markers, no gold-patch line 'fieldarg.split/rsplit(None,1)' reproduced, no patched file path 'sphinx/util/docfields.py', no module path, no echo of patched symbol 'transform', no narration terms). The tokens split/rsplit never appear in the spec view. The 'last token / remaining prefix' semantics is already public in problem_statement: the Expected behavior shows input 'dict(str, str) opc_meta' should render as 'opc_meta (dict(str,str))', which discloses that the name is the final token and the type keeps its interior whitespace. Thus the spec adds nothing beyond the public problem_statement. refinement.md and mapping.md do quote split/rsplit and the gold diff, but those are auditor-internal bundle docs, not the solver-visible spec view that G-PANEL-3 judges. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
