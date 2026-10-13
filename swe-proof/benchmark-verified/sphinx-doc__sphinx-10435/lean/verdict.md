# P2 adversarial audit — sphinx-doc__sphinx-10435

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,12 +72,11 @@
 -- impl-start
 def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
   let mut hl := hlcode
-  hl := replaceAll verbOpen upquoteOpen hl
-  -- get consistent trailer
-  hl := dropLastN 15 (rstripWs hl)
+  hl := replaceAll verbOpen (r"\sphinxcode{\sphinxupquote{".toList) hl
+  hl := dropLastN 14 (rstripWs hl)
   let mut body : List Char := []
   body := body ++ hl
-  body := body ++ closingTail
+  body := body ++ "}}".toList
   return body
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,15 +70,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
-  let mut hl := hlcode
-  hl := replaceAll verbOpen upquoteOpen hl
-  -- get consistent trailer
-  hl := dropLastN 15 (rstripWs hl)
-  let mut body : List Char := []
-  body := body ++ hl
-  body := body ++ closingTail
-  return body
+def implementation_inlineCode (hlcode : List Char) : List Char :=
+  dropLastN 14 (rstripWs (replaceAll verbOpen upquoteOpen hlcode)) ++ closingTail
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,15 +70,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
-  let mut hl := hlcode
-  hl := replaceAll verbOpen upquoteOpen hl
-  -- get consistent trailer
-  hl := dropLastN 15 (rstripWs hl)
-  let mut body : List Char := []
-  body := body ++ hl
-  body := body ++ closingTail
-  return body
+def implementation_inlineCode (hlcode : List Char) : List Char :=
+  dropLastN 15 (rstripWs (replaceAll verbOpen upquoteOpen hlcode)) ++ "}}".toList
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,15 +70,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
-  let mut hl := hlcode
-  hl := replaceAll verbOpen upquoteOpen hl
-  -- get consistent trailer
-  hl := dropLastN 15 (rstripWs hl)
-  let mut body : List Char := []
-  body := body ++ hl
-  body := body ++ closingTail
-  return body
+def implementation_inlineCode (hlcode : List Char) : List Char :=
+  match hlcode with
+  | [] => []
+  | _  => dropLastN 15 (rstripWs (replaceAll verbOpen upquoteOpen hlcode)) ++ closingTail
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,15 +70,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
-  let mut hl := hlcode
-  hl := replaceAll verbOpen upquoteOpen hl
-  -- get consistent trailer
-  hl := dropLastN 15 (rstripWs hl)
-  let mut body : List Char := []
-  body := body ++ hl
-  body := body ++ closingTail
-  return body
+def implementation_inlineCode (hlcode : List Char) : List Char :=
+  dropLastN 16 (rstripWs (replaceAll verbOpen upquoteOpen hlcode)) ++ closingTail
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,20 +70,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
-  let mut hl := hlcode
-  hl := replaceAll verbOpen upquoteOpen hl
-  -- get consistent trailer
-  hl := dropLastN 15 (rstripWs hl)
-  let mut body : List Char := []
-  body := body ++ hl
-  body := body ++ closingTail
-  return body
+def implementation_inlineCode (hlcode : List Char) : List Char :=
+  let a := replaceAll verbOpen upquoteOpen hlcode
+  let b := dropLastN 15 (rstripWs a)
+  b ++ closingTail
 -- impl-end
 
 -- proof-start
 theorem correct_inlineCode : ∀ hlcode : List Char,
     problem_spec_inlineCode hlcode (implementation_inlineCode hlcode) := by
   intro hlcode
-  simp only [problem_spec_inlineCode, implementation_inlineCode, Id.run, List.nil_append, pure]
+  simp only [problem_spec_inlineCode, implementation_inlineCode]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,15 +70,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
-  let mut hl := hlcode
-  hl := replaceAll verbOpen upquoteOpen hl
-  -- get consistent trailer
-  hl := dropLastN 15 (rstripWs hl)
-  let mut body : List Char := []
-  body := body ++ hl
-  body := body ++ closingTail
-  return body
+def implementation_inlineCode (hlcode : List Char) : List Char :=
+  dropLastN 15 (rstripWs hlcode) ++ closingTail
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib

-- imports-end

-- axioms-start
-- No unchanged callee is consumed as an axiom: the relevant post-processing
-- (a textual rewrite of the highlighter's output) is modeled deeply below.
-- axioms-end

-- pure-start
/-- Newline character used to join LaTeX body fragments. -/
def CR : Char := '\n'

/-- Whitespace predicate matching the characters stripped by default when
trailing whitespace is removed from a string. -/
def isTrailWs (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\n' || c == '\r' ||
  c == (Char.ofNat 0x0b) || c == (Char.ofNat 0x0c)

/-- Remove trailing whitespace from a character sequence. -/
def rstripWs (s : List Char) : List Char := (s.reverse.dropWhile isTrailWs).reverse

/-- Keep all but the last `n` characters of `s` (the value-level slice `s[:-n]`
for `n > 0`; yields the empty sequence when `n ≥ s.length`). -/
def dropLastN (n : Nat) (s : List Char) : List Char := s.take (s.length - n)

/-- Replace every non-overlapping, left-to-right occurrence of a non-empty
pattern `pat` by `rep`. -/
def replaceAll (pat rep : List Char) : List Char → List Char
  | [] => []
  | (c :: cs) =>
    if pat.isPrefixOf (c :: cs) ∧ 0 < pat.length then
      rep ++ replaceAll pat rep ((c :: cs).drop pat.length)
    else
      c :: replaceAll pat rep cs
  termination_by s => s.length
  decreasing_by
    · simp_wf; omega
    · simp_wf

/-- The Verbatim opening emitted by the syntax highlighter. -/
def verbOpen : List Char := r"\begin{Verbatim}[commandchars=\\\{\}]".toList

/-- The constant sequence the Verbatim opening is rewritten to. The trailing `%`
comments out the newline that immediately follows, so it produces no leading
inter-token space in the rendered output. -/
def upquoteOpen : List Char := r"\sphinxcode{\sphinxupquote{%".toList

/-- The trailing closing sequence appended after the highlighted body. The
leading `%` comments out the trailing newline, so no spurious space survives at
the end of the rendered output. -/
def closingTail : List Char := '%' :: CR :: "}}".toList
-- pure-end

-- post-conditions-start
/-- `result` is the exact character sequence emitted for an inline highlighted
code fragment, given the highlighter output `hlcode`.

The emission rewrites the highlighter's opening delimiter to the upquote opening
(whose trailing comment suppresses the following newline), then drops trailing
whitespace together with the 15-character closing-delimiter run that
precedes it (i.e. the newline plus the closing delimiter), and finally appends a
comment-terminated newline followed by the closing braces. Both the leading and
the trailing inter-token newline are thereby comment-suppressed, so the rendered
fragment carries no extra whitespace at either end. -/
def problem_spec_inlineCode (hlcode : List Char) (result : List Char) : Prop :=
  let rewritten := replaceAll verbOpen upquoteOpen hlcode
  let trimmed := dropLastN 15 (rstripWs rewritten)
  result = trimmed ++ closingTail
-- post-conditions-end

-- impl-start
def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
  let mut hl := hlcode
  hl := replaceAll verbOpen upquoteOpen hl
  -- get consistent trailer
  hl := dropLastN 15 (rstripWs hl)
  let mut body : List Char := []
  body := body ++ hl
  body := body ++ closingTail
  return body
-- impl-end

-- proof-start
theorem correct_inlineCode : ∀ hlcode : List Char,
    problem_spec_inlineCode hlcode (implementation_inlineCode hlcode) := by
  intro hlcode
  simp only [problem_spec_inlineCode, implementation_inlineCode, Id.run, List.nil_append, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_inlineCode pins result to the single closed-form value `dropLastN 15 (rstripWs (replaceAll verbOpen upquoteOpen hlcode)) ++ closingTail` (rigid functional equality, zero post-condition slack). Any same-spec impl whose correct_inlineCode closes must be extensionally equal to gold and therefore produces the identical byte sequence.

SAME-SPEC: all 7 attacks confirmed True via swebench_unified.markers.same_spec (spec regions — axioms/pure/pre/post — byte-identical; only impl+proof edited).

COMMANDS: verify = `bash scripts/lean_verify.sh atk_N.lean`; axioms appended `#print axioms correct_inlineCode`; resolve = harness.run_resolve('sphinx-doc__sphinx-10435', <patch>, timeout=1800) under docker (image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-10435:latest).

### Results
- pos_control (gold Solution.lean): exit 0; axioms [propext, Classical.choice, Quot.sound] (clean).
- atk_1 prepatch bug (no %, dropLastN 14, plain '}}'): exit 1, unsolved goals at 85:73. Does NOT close (prepatch reproduced — matches Solution_prepatch.lean which carries sorry).
- atk_2 boundary dropLastN 14: exit 1, unsolved goals (residual `dropLastN 14 ... = dropLastN 15 ...`).
- atk_3 control-flow-effect, append plain "}}" instead of closingTail: exit 1, unsolved goals (`... ++ "}}" = ... ++ "%\n}}"`).
- atk_4 partial-domain ([] => [] else gold): exit 1, deterministic heartbeat timeout at whnf — does NOT close (fails closed; the []-branch diverges from gold on empty input).
- atk_5 boundary dropLastN 16: exit 1, unsolved goals.
- atk_7 omit the replaceAll rewrite: exit 1, unsolved goals.
- atk_6 ungrounded-oracle echo (let-binding form, extensionally identical to gold): exit 0; axioms [propext, Classical.choice, Quot.sound] (clean). REQUIRED resolve run performed: faithful refined patch (== gold three-line edit) RESOLVED=True, completed, patch_successfully_applied=True, FAIL_TO_PASS test_latex_code_role PASS, all 76 PASS_TO_PASS pass, attempts=1, not flaky. Echo of gold that resolves is NOT a weakness (per G-PANEL-1 resolve policy).

CONCLUSION: The only same-spec impl that closes with clean axioms (atk_6) is extensionally the gold value and its materialized faithful patch RESOLVES. No divergent-yet-provable impl exists. verify => correct holds. NOT BROKEN.

REFINEMENT AUDIT: refinement.md legs are all R / A-reference / I — NO A-consumed row (proof consumes no callee axiom; highlighter output hlcode is a free universally-quantified input, not axiomatized), NO kind-3 (all edited ops expressed concretely). A-reference legs: replaceAll↔str.replace (op2, non-overlapping L-to-R), dropLastN 15↔s[:-15] (op3), rstripWs↔str.rstrip (op3), closingTail↔'%'+CR+'}}' (op5) — validated by conformance_check.py G-CONF over 150,004 Pygments-shaped inputs, 0 disagreements. The rstripWs vs str.rstrip Unicode-whitespace divergence is documented off the modeled domain (Pygments LatexFormatter trailing region is always ASCII \n). axiom_check.py correctly status=skip (no consumed callee axioms). Correspondence to real callees (latex.py:1712-1717 @ f1061c012e) holds.

VERDICT: SOUND — ≥5 distinct wrong impls attacked, the sole clean-axiom closer verified to resolve; spec is a tight functional equality.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib

-- imports-end

-- axioms-start
-- No unchanged callee is consumed as an axiom: the relevant post-processing
-- (a textual rewrite of the highlighter's output) is modeled deeply below.
-- axioms-end

-- pure-start
/-- Newline character used to join LaTeX body fragments. -/
def CR : Char := '\n'

/-- Whitespace predicate matching the characters stripped by default when
trailing whitespace is removed from a string. -/
def isTrailWs (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\n' || c == '\r' ||
  c == (Char.ofNat 0x0b) || c == (Char.ofNat 0x0c)

/-- Remove trailing whitespace from a character sequence. -/
def rstripWs (s : List Char) : List Char := (s.reverse.dropWhile isTrailWs).reverse

/-- Keep all but the last `n` characters of `s` (the value-level slice `s[:-n]`
for `n > 0`; yields the empty sequence when `n ≥ s.length`). -/
def dropLastN (n : Nat) (s : List Char) : List Char := s.take (s.length - n)

/-- Replace every non-overlapping, left-to-right occurrence of a non-empty
pattern `pat` by `rep`. -/
def replaceAll (pat rep : List Char) : List Char → List Char
  | [] => []
  | (c :: cs) =>
    if pat.isPrefixOf (c :: cs) ∧ 0 < pat.length then
      rep ++ replaceAll pat rep ((c :: cs).drop pat.length)
    else
      c :: replaceAll pat rep cs
  termination_by s => s.length
  decreasing_by
    · simp_wf; omega
    · simp_wf

/-- The Verbatim opening emitted by the syntax highlighter. -/
def verbOpen : List Char := r"\begin{Verbatim}[commandchars=\\\{\}]".toList

/-- The constant sequence the Verbatim opening is rewritten to. The trailing `%`
comments out the newline that immediately follows, so it produces no leading
inter-token space in the rendered output. -/
def upquoteOpen : List Char := r"\sphinxcode{\sphinxupquote{%".toList

/-- The trailing closing sequence appended after the highlighted body. The
leading `%` comments out the trailing newline, so no spurious space survives at
the end of the rendered output. -/
def closingTail : List Char := '%' :: CR :: "}}".toList
-- pure-end

-- post-conditions-start
/-- `result` is the exact character sequence emitted for an inline highlighted
code fragment, given the highlighter output `hlcode`.

The emission rewrites the highlighter's opening delimiter to the upquote opening
(whose trailing comment suppresses the following newline), then drops trailing
whitespace together with the 15-character closing-delimiter run that
precedes it (i.e. the newline plus the closing delimiter), and finally appends a
comment-terminated newline followed by the closing braces. Both the leading and
the trailing inter-token newline are thereby comment-suppressed, so the rendered
fragment carries no extra whitespace at either end. -/
def problem_spec_inlineCode (hlcode : List Char) (result : List Char) : Prop :=
  let rewritten := replaceAll verbOpen upquoteOpen hlcode
  let trimmed := dropLastN 15 (rstripWs rewritten)
  result = trimmed ++ closingTail
-- post-conditions-end

-- impl-start
def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
  let mut hl := hlcode
  hl := replaceAll verbOpen upquoteOpen hl
  -- get consistent trailer
  hl := dropLastN 15 (rstripWs hl)
  let mut body : List Char := []
  body := body ++ hl
  body := body ++ closingTail
  return body
-- impl-end

-- proof-start
theorem correct_inlineCode : ∀ hlcode : List Char,
    problem_spec_inlineCode hlcode (implementation_inlineCode hlcode) := by
  intro hlcode
  simp only [problem_spec_inlineCode, implementation_inlineCode, Id.run, List.nil_append, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_inlineCode pins result to the single closed-form value `dropLastN 15 (rstripWs (replaceAll verbOpen upquoteOpen hlcode)) ++ closingTail` (rigid functional equality, zero post-condition slack). Any same-spec impl whose correct_inlineCode closes must be extensionally equal to gold and therefore produces the identical byte sequence.

SAME-SPEC: all 7 attacks confirmed True via swebench_unified.markers.same_spec (spec regions — axioms/pure/pre/post — byte-identical; only impl+proof edited).

COMMANDS: verify = `bash scripts/lean_verify.sh atk_N.lean`; axioms appended `#print axioms correct_inlineCode`; resolve = harness.run_resolve('sphinx-doc__sphinx-10435', <patch>, timeout=1800) under docker (image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-10435:latest).

### Results
- pos_control (gold Solution.lean): exit 0; axioms [propext, Classical.choice, Quot.sound] (clean).
- atk_1 prepatch bug (no %, dropLastN 14, plain '}}'): exit 1, unsolved goals at 85:73. Does NOT close (prepatch reproduced — matches Solution_prepatch.lean which carries sorry).
- atk_2 boundary dropLastN 14: exit 1, unsolved goals (residual `dropLastN 14 ... = dropLastN 15 ...`).
- atk_3 control-flow-effect, append plain "}}" instead of closingTail: exit 1, unsolved goals (`... ++ "}}" = ... ++ "%\n}}"`).
- atk_4 partial-domain ([] => [] else gold): exit 1, deterministic heartbeat timeout at whnf — does NOT close (fails closed; the []-branch diverges from gold on empty input).
- atk_5 boundary dropLastN 16: exit 1, unsolved goals.
- atk_7 omit the replaceAll rewrite: exit 1, unsolved goals.
- atk_6 ungrounded-oracle echo (let-binding form, extensionally identical to gold): exit 0; axioms [propext, Classical.choice, Quot.sound] (clean). REQUIRED resolve run performed: faithful refined patch (== gold three-line edit) RESOLVED=True, completed, patch_successfully_applied=True, FAIL_TO_PASS test_latex_code_role PASS, all 76 PASS_TO_PASS pass, attempts=1, not flaky. Echo of gold that resolves is NOT a weakness (per G-PANEL-1 resolve policy).

CONCLUSION: The only same-spec impl that closes with clean axioms (atk_6) is extensionally the gold value and its materialized faithful patch RESOLVES. No divergent-yet-provable impl exists. verify => correct holds. NOT BROKEN.

REFINEMENT AUDIT: refinement.md legs are all R / A-reference / I — NO A-consumed row (proof consumes no callee axiom; highlighter output hlcode is a free universally-quantified input, not axiomatized), NO kind-3 (all edited ops expressed concretely). A-reference legs: replaceAll↔str.replace (op2, non-overlapping L-to-R), dropLastN 15↔s[:-15] (op3), rstripWs↔str.rstrip (op3), closingTail↔'%'+CR+'}}' (op5) — validated by conformance_check.py G-CONF over 150,004 Pygments-shaped inputs, 0 disagreements. The rstripWs vs str.rstrip Unicode-whitespace divergence is documented off the modeled domain (Pygments LatexFormatter trailing region is always ASCII \n). axiom_check.py correctly status=skip (no consumed callee axioms). Correspondence to real callees (latex.py:1712-1717 @ f1061c012e) holds.

VERDICT: SOUND — ≥5 distinct wrong impls attacked, the sole clean-axiom closer verified to resolve; spec is a tight functional equality.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reviewed all four roles and re-ran every baseline. FAITHFUL verdict: the spec matches the real callee on the entire reachable domain.

Operations checked against the real repo (base_commit f1061c012e, worktree, and the gold patch.diff which is the post-patch behavior being modeled):
1. replaceAll verbOpen upquoteOpen <-> str.replace(BEGIN, UPQUOTE): non-overlapping left-to-right — matches exactly (150k fuzz, 0 disagreements).
2. dropLastN 15 <-> s[:-15]: verified across len in {0,1,14,15,16} — take(len-15) == s[:-15] (both '' when len<=15).
3. closingTail = '%'::'\n'::"}}" <-> '%' + CR + '}}' with module CR='\n': identical.
4. rstripWs <-> str.rstrip(): THE ONLY divergence. rstripWs strips only ' \t\n\r\x0b\x0c'; Python str.rstrip() additionally strips 0x1c-0x1f, 0x85, 0xa0, U+2000-200A, U+2028/9, U+202F, U+205F, U+1680, U+3000. They disagree on any string whose trailing region contains those exotic chars (counterexample above).

WHY OFF-DOMAIN / not a defect: hlcode is DEFINED as the output of the Pygments LatexFormatter (highlight_block), which is a free universally-quantified input but whose real range is constrained. I empirically confirmed with the installed Pygments (2.17.2, and 2.20.0 in sphinx8638_venv) that highlighter output ALWAYS ends in '\end{Verbatim}\n' — the trailing region that rstrip() actually inspects is invariably a single ASCII '\n', for every case tested (empty code, single-line, multi-line, the F2P sample, and source code containing exotic trailing whitespace like \xa0/U+2028/U+3000/0x1c — the exotic chars are escaped/absorbed inside the environment before \end{Verbatim}, never left in the trailing region). On this reachable shape rstripWs === str.rstrip(), so all four rows agree. The conformance_check.py (G-CONF) fuzzes exactly this highlighter shape (150,004 inputs) and finds 0 disagreements; its _rstrip_ws even uses the ASCII-only set, matching the Lean model, and still passes because the domain never exercises the difference.

Artifact integrity re-verified:
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- #print axioms correct_inlineCode -> [propext, Classical.choice, Quot.sound] — clean, NO sorryAx (proof is real).
- markers.same_spec(Solution, Solution_prepatch) -> True: spec region frozen/byte-identical; prepatch differs only in impl/proof.
- conformance_check.py -> checked=150004 disagreements=0 exit 0.

The spec is a rigid functional equality pinning result to a single closed form, so it is neither too weak nor too strong on-domain. The rstripWs approximation is a sound modeling boundary explicitly documented in mapping.md and bounded by G-CONF's domain. FAITHFUL.

Counterexample / evidence:

```
For hlcode ending in trailing U+00A0 (e.g. the 16 chars '0123456789abcdef' + '\xa0'), the modeled rstripWs strips only the 6 ASCII whitespace chars (space,\t,\n,\r,\x0b,\x0c) and leaves the \xa0, so dropLastN 15 yields spec result '01%\n}}', whereas the real Python str.rstrip() strips the \xa0 too and yields '0%\n}}'. This is a REAL semantic difference between rstripWs and str.rstrip(), but the input is unreachable (see notes).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the spec_view projection of Solution.lean (consumer-visible artifact; refinement.md/mapping.md/verdict.md are auditor-facing and out of scope). Mechanical leakage.screen() passes with zero hard_failures; same_spec(patched, prepatch)=True so the frozen spec region is the one judged. No diff markers, no patched file path (sphinx/writers/latex.py absent), no echo of the patched repo symbol visit_literal (spec identifiers are inlineCode/upquoteOpen/verbOpen/closingTail/dropLastN/etc.), and no bug/fix narration in comments. Semantically, the two headline components of the gold edit — adding '%' after \sphinxupquote{ and the trailing '%\n}}' — are ALREADY explicitly public in problem_statement, which literally prints both the buggy and the desired markup. The one detail not in problem_statement, dropLastN 15 (the [:-15]), is stated abstractly as 'the 15-character closing-delimiter run (newline plus closing delimiter)' i.e. a specification of correct output, not the before/after diff; it carries no '[:-14]->[:-15]' framing and 15 is derivable from len('\n\end{Verbatim}'). Pinning the correct output is the intended spec design (makes G-EQ tight), not leakage. The spec view does not reveal the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
