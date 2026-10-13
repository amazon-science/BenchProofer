# P2 adversarial audit — pytest-dev__pytest-5809

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,7 @@
     List (String × String) := Id.run do
   let mut params : List (String × String) := []
   params := params ++ [("code", contents)]
-  params := params ++ [("lexer", "text")]
+  params := params ++ [("lexer", "python3")]
   params := params ++ [("expiry", "1week")]
   return params
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,12 +49,8 @@
 
 -- impl-start
 def implementation_buildPasteParams (contents : String) :
-    List (String × String) := Id.run do
-  let mut params : List (String × String) := []
-  params := params ++ [("code", contents)]
-  params := params ++ [("lexer", "text")]
-  params := params ++ [("expiry", "1week")]
-  return params
+    List (String × String) :=
+  [("code", contents), ("lexer", "text"), ("expiry", "2week")]
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,12 +49,11 @@
 
 -- impl-start
 def implementation_buildPasteParams (contents : String) :
-    List (String × String) := Id.run do
-  let mut params : List (String × String) := []
-  params := params ++ [("code", contents)]
-  params := params ++ [("lexer", "text")]
-  params := params ++ [("expiry", "1week")]
-  return params
+    List (String × String) :=
+  if contents = "" then
+    [("code", contents), ("lexer", "python3"), ("expiry", "1week")]
+  else
+    [("code", contents), ("lexer", "text"), ("expiry", "1week")]
 -- impl-end
 
 -- proof-start
@@ -64,5 +63,5 @@
         (implementation_buildPasteParams contents) := by
   intro contents
   unfold problem_spec_buildPasteParams implementation_buildPasteParams
-  rfl
+  split <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,12 +49,8 @@
 
 -- impl-start
 def implementation_buildPasteParams (contents : String) :
-    List (String × String) := Id.run do
-  let mut params : List (String × String) := []
-  params := params ++ [("code", contents)]
-  params := params ++ [("lexer", "text")]
-  params := params ++ [("expiry", "1week")]
-  return params
+    List (String × String) :=
+  [("lexer", "text"), ("code", contents), ("expiry", "1week")]
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,12 +49,8 @@
 
 -- impl-start
 def implementation_buildPasteParams (contents : String) :
-    List (String × String) := Id.run do
-  let mut params : List (String × String) := []
-  params := params ++ [("code", contents)]
-  params := params ++ [("lexer", "text")]
-  params := params ++ [("expiry", "1week")]
-  return params
+    List (String × String) :=
+  [("code", contents), ("lexer", "text"), ("expiry", "1week"), ("format", "json")]
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,12 +49,8 @@
 
 -- impl-start
 def implementation_buildPasteParams (contents : String) :
-    List (String × String) := Id.run do
-  let mut params : List (String × String) := []
-  params := params ++ [("code", contents)]
-  params := params ++ [("lexer", "text")]
-  params := params ++ [("expiry", "1week")]
-  return params
+    List (String × String) :=
+  [("code", contents ++ "!"), ("lexer", "text"), ("expiry", "1week")]
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -50,10 +50,10 @@
 -- impl-start
 def implementation_buildPasteParams (contents : String) :
     List (String × String) := Id.run do
-  let mut params : List (String × String) := []
-  params := params ++ [("code", contents)]
-  params := params ++ [("lexer", "text")]
-  params := params ++ [("expiry", "1week")]
+  let codePair : String × String := ("code", contents)
+  let lexerPair : String × String := ("lexer", "text")
+  let expiryPair : String × String := ("expiry", "1week")
+  let params := [codePair] ++ ([lexerPair] ++ [expiryPair])
   return params
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the request-parameter mapping that is submitted to the remote paste
service when a captured terminal session is uploaded.

The upload is an HTTP form post whose body is the URL-encoding of three named
parameters:

  * `code`    — the captured session text to be pasted, taken verbatim from the
                caller-supplied contents;
  * `lexer`   — the syntax-highlighting language the service should assume for
                the pasted body. The captured terminal output is arbitrary
                console text rather than source in any particular programming
                language, so the language-neutral plain-`text` highlighter is
                requested;
  * `expiry`  — how long the paste is retained, always one week.

The mapping is fully determined by the contents: the `code` entry carries the
contents unchanged, while `lexer` and `expiry` are the constant values above.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The contents enter as plain data
-- (a `String`); the only operation performed is assembling the three named
-- parameter pairs, modeled directly below. Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the direct
-- assembly of the parameter mapping.
-- pure-end

-- post-conditions-start
/-- The submitted parameter mapping is fully pinned to the input:

  * the `code` entry is exactly the caller-supplied `contents`;
  * the `lexer` entry is the language-neutral `"text"` highlighter;
  * the `expiry` entry is `"1week"`;

and these three pairs, in this order, are the entire mapping — no parameter is
left free and no extra parameter is added. -/
def problem_spec_buildPasteParams
    (contents : String) (result : List (String × String)) : Prop :=
  result = [("code", contents), ("lexer", "text"), ("expiry", "1week")]
-- post-conditions-end

-- impl-start
def implementation_buildPasteParams (contents : String) :
    List (String × String) := Id.run do
  let mut params : List (String × String) := []
  params := params ++ [("code", contents)]
  params := params ++ [("lexer", "text")]
  params := params ++ [("expiry", "1week")]
  return params
-- impl-end

-- proof-start
theorem correct_buildPasteParams :
    ∀ (contents : String),
      problem_spec_buildPasteParams contents
        (implementation_buildPasteParams contents) := by
  intro contents
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total functional equality pinning the output uniquely for every input: problem_spec_buildPasteParams contents result := result = [("code", contents), ("lexer", "text"), ("expiry", "1week")]. Only the `code` pair is contents-dependent; `lexer`/`expiry` are concrete constant literals. Any impl whose correct_ closes is forced extensionally identical to gold on every input, so any faithful refined patch produces the identical params dict and resolves. No slack for a closing-but-non-resolving alternative.

SAME_SPEC: all 8 files (positive + atk_1..7) confirmed same_spec=True via swebench_unified.markers.same_spec (lean). Note _lean_spec_view collapses BOTH impl and proof regions, so impl+proof are freely rewritable while axioms/pure/pre/post stay byte-identical.

### ATTACKS (cmd: bash scripts/lean_verify.sh <f>; from project root):
- atk_1 prepatch bug lexer="python3" (the real bug, rfl): EXIT=1 (does not close; goal [...python3...] != [...text...]). PREPATCH REPRODUCED.
- atk_2 expiry="2week" (rfl): EXIT=1.
- atk_3 partial-domain, empty contents -> lexer="python3" else text (split<;>rfl): EXIT=1.
- atk_4 reordered pairs, lexer before code (rfl): EXIT=1.
- atk_5 extra 4th pair ("format","json") appended (rfl): EXIT=1.
- atk_6 code value mutated contents++"!" (rfl): EXIT=1.
- atk_7 ungrounded-oracle echo: entry-by-entry Id.run assembly, distinct control flow, extensionally == gold (rfl): EXIT=0 VERIFIES. #print axioms correct_buildPasteParams -> 'does not depend on any axioms' (clean, atk_7_ax.lean EXIT=0).

### RESOLVE (swebench_unified.harness.run_resolve, timeout=3600 retries=2):
- INFRA CONTROL gold patch: RESOLVED=True (F2P test_create_new_paste + 3 P2P all pass). run_id sbu-audit-gold-mubtilis. This proves the harness/image work; an initial atk_7 resolve returned 'no report' purely due to image-pull/contention from the running 24-worker lean concurrent runs (docker system df: 247 images, containers exited 137/OOM) — NOT a genuine non-resolve.
- atk_7 faithful patch (materialized above): RESOLVED=True (F2P + 3 P2P all pass). run_id sbu-audit-atk7-mubtilis-v2. Report: patch_successfully_applied=True, resolved=True.

POSITIVE CONTROL: positive.lean (gold Solution.lean copy) EXIT=0, clean axioms.

REFINEMENT AUDIT: meta.json axioms=[], deep_model_references=[], conf_skip=False. refinement.md legs: #1 empty accumulator (I), #2 code entry String<->str verbatim (R), #3 lexer="text" changed entry (I), #4 expiry (I), #5 return->urlencode (I). No A-consumed / A-reference / kind-3 leg; no opaque/axiom callee in Solution.lean. A-leg correspondence audit is vacuous (nothing to validate); the R/I legs are covered by G-CONF (conformance_check.py op-for-op shadow diff-tested vs real patched create_new_paste over 1e5 fuzzed contents, urlopen stubbed as in F2P test, seed 5809). axiom_check.py is a legitimate skip stub.

CONCLUSION: The only non-gold closing impl (atk_7) is an extensional echo whose faithful patch RESOLVES; all deviating impls fail to close. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the request-parameter mapping that is submitted to the remote paste
service when a captured terminal session is uploaded.

The upload is an HTTP form post whose body is the URL-encoding of three named
parameters:

  * `code`    — the captured session text to be pasted, taken verbatim from the
                caller-supplied contents;
  * `lexer`   — the syntax-highlighting language the service should assume for
                the pasted body. The captured terminal output is arbitrary
                console text rather than source in any particular programming
                language, so the language-neutral plain-`text` highlighter is
                requested;
  * `expiry`  — how long the paste is retained, always one week.

The mapping is fully determined by the contents: the `code` entry carries the
contents unchanged, while `lexer` and `expiry` are the constant values above.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The contents enter as plain data
-- (a `String`); the only operation performed is assembling the three named
-- parameter pairs, modeled directly below. Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the direct
-- assembly of the parameter mapping.
-- pure-end

-- post-conditions-start
/-- The submitted parameter mapping is fully pinned to the input:

  * the `code` entry is exactly the caller-supplied `contents`;
  * the `lexer` entry is the language-neutral `"text"` highlighter;
  * the `expiry` entry is `"1week"`;

and these three pairs, in this order, are the entire mapping — no parameter is
left free and no extra parameter is added. -/
def problem_spec_buildPasteParams
    (contents : String) (result : List (String × String)) : Prop :=
  result = [("code", contents), ("lexer", "text"), ("expiry", "1week")]
-- post-conditions-end

-- impl-start
def implementation_buildPasteParams (contents : String) :
    List (String × String) := Id.run do
  let mut params : List (String × String) := []
  params := params ++ [("code", contents)]
  params := params ++ [("lexer", "text")]
  params := params ++ [("expiry", "1week")]
  return params
-- impl-end

-- proof-start
theorem correct_buildPasteParams :
    ∀ (contents : String),
      problem_spec_buildPasteParams contents
        (implementation_buildPasteParams contents) := by
  intro contents
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total functional equality pinning the output uniquely for every input: problem_spec_buildPasteParams contents result := result = [("code", contents), ("lexer", "text"), ("expiry", "1week")]. Only the `code` pair is contents-dependent; `lexer`/`expiry` are concrete constant literals. Any impl whose correct_ closes is forced extensionally identical to gold on every input, so any faithful refined patch produces the identical params dict and resolves. No slack for a closing-but-non-resolving alternative.

SAME_SPEC: all 8 files (positive + atk_1..7) confirmed same_spec=True via swebench_unified.markers.same_spec (lean). Note _lean_spec_view collapses BOTH impl and proof regions, so impl+proof are freely rewritable while axioms/pure/pre/post stay byte-identical.

### ATTACKS (cmd: bash scripts/lean_verify.sh <f>; from project root):
- atk_1 prepatch bug lexer="python3" (the real bug, rfl): EXIT=1 (does not close; goal [...python3...] != [...text...]). PREPATCH REPRODUCED.
- atk_2 expiry="2week" (rfl): EXIT=1.
- atk_3 partial-domain, empty contents -> lexer="python3" else text (split<;>rfl): EXIT=1.
- atk_4 reordered pairs, lexer before code (rfl): EXIT=1.
- atk_5 extra 4th pair ("format","json") appended (rfl): EXIT=1.
- atk_6 code value mutated contents++"!" (rfl): EXIT=1.
- atk_7 ungrounded-oracle echo: entry-by-entry Id.run assembly, distinct control flow, extensionally == gold (rfl): EXIT=0 VERIFIES. #print axioms correct_buildPasteParams -> 'does not depend on any axioms' (clean, atk_7_ax.lean EXIT=0).

### RESOLVE (swebench_unified.harness.run_resolve, timeout=3600 retries=2):
- INFRA CONTROL gold patch: RESOLVED=True (F2P test_create_new_paste + 3 P2P all pass). run_id sbu-audit-gold-mubtilis. This proves the harness/image work; an initial atk_7 resolve returned 'no report' purely due to image-pull/contention from the running 24-worker lean concurrent runs (docker system df: 247 images, containers exited 137/OOM) — NOT a genuine non-resolve.
- atk_7 faithful patch (materialized above): RESOLVED=True (F2P + 3 P2P all pass). run_id sbu-audit-atk7-mubtilis-v2. Report: patch_successfully_applied=True, resolved=True.

POSITIVE CONTROL: positive.lean (gold Solution.lean copy) EXIT=0, clean axioms.

REFINEMENT AUDIT: meta.json axioms=[], deep_model_references=[], conf_skip=False. refinement.md legs: #1 empty accumulator (I), #2 code entry String<->str verbatim (R), #3 lexer="text" changed entry (I), #4 expiry (I), #5 return->urlencode (I). No A-consumed / A-reference / kind-3 leg; no opaque/axiom callee in Solution.lean. A-leg correspondence audit is vacuous (nothing to validate); the R/I legs are covered by G-CONF (conformance_check.py op-for-op shadow diff-tested vs real patched create_new_paste over 1e5 fuzzed contents, urlopen stubbed as in F2P test, seed 5809). axiom_check.py is a legitimate skip stub.

CONCLUSION: The only non-gold closing impl (atk_7) is an extensional echo whose faithful patch RESOLVES; all deviating impls fail to close. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for pytest-dev__pytest-5809 (lean). Modeled function: the `params` mapping assembled in create_new_paste (src/_pytest/pastebin.py) post-gold-patch. Verified against the real repo:

1. Gold patch (instance.json) rewrites the mapping to `params = {"code": contents, "lexer": "text", "expiry": "1week"}` — Python 3.7+ dicts preserve insertion order, so the observable ordered pairs are exactly [(code,contents),(lexer,text),(expiry,1week)].
2. Spec `problem_spec_buildPasteParams`: `result = [("code", contents), ("lexer", "text"), ("expiry", "1week")]`. This pins the entire mapping — exactly three pairs, in this order, code carrying contents verbatim, lexer/expiry the two post-patch constants. It matches the real callee on every input `contents`; there is no input where the modeled function disagrees with the real patched behavior. The spec is not too strong: the real post-patch code produces precisely these three entries and nothing else, for all contents. It is not too weak either: it fully determines the result.
3. F2P test test_create_new_paste asserts lexer=text, code=full-paste-contents, expiry=1week in the encoded body — consistent with the spec (urlencode is order/content-faithful on these ascii key/value pairs).
4. same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical; only impl lexer literal differs text vs python3).
5. Lean compiles cleanly: lean_verify.sh exit 0, no sorry; `#print axioms correct_buildPasteParams` => 'does not depend on any axioms' (genuine rfl proof, no sorryAx).

No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (post-conditions region) pins result = [("code", contents), ("lexer", "text"), ("expiry", "1week")] and the docstring explains the language-neutral `text` highlighter. This discloses the gold edit value (lexer -> "text"), BUT that exact fix is already public in the problem_statement itself: 'The call goes through fine if lexer is changed from python3 to text ... the console output of a pytest run ... is not Python code, but arbitrary text.' The problem_statement names both the buggy value (python3) and the fix (text) and the reasoning. The spec view adds nothing beyond it: the prepatch value python3 lives only in the elided impl (Solution_prepatch.lean), not in the spec view, so no bug->fix delta is exposed. same_spec(patched, prepatch) = True confirms the spec region is byte-identical across the two files (only the elided impl literal differs). No line of the spec view reconstructs the gold beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
