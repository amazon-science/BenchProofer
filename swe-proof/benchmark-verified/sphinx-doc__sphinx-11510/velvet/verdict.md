# P2 adversarial audit — sphinx-doc__sphinx-11510

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_passthrough.lean`, `atk2_offbyone.lean`, `atk3_notransform.lean`, `atk4_orderswap.lean`, `atk5_partialdomain.lean`, `atk7_diverge.lean`, `atk8_doubletransform.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk6_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_passthrough.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,10 +80,7 @@
       ++ lines.drop (lines.length - 2)
   do
     -- impl-start
-    let content := lines.dropLast.dropLast
-    let text := transform (List.intercalate ['\n'] content)
-    let assembled := splitLines text ++ lines.drop (lines.length - 2)
-    return assembled
+    return lines
     -- impl-end
 
 prove_correct assembleInsertedLines by
```

Attack 2 — `atk2_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,10 +80,9 @@
       ++ lines.drop (lines.length - 2)
   do
     -- impl-start
-    let content := lines.dropLast.dropLast
+    let content := lines.dropLast
     let text := transform (List.intercalate ['\n'] content)
-    let assembled := splitLines text ++ lines.drop (lines.length - 2)
-    return assembled
+    return splitLines text ++ lines.drop (lines.length - 1)
     -- impl-end
 
 prove_correct assembleInsertedLines by
```

Attack 3 — `atk3_notransform.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,9 +81,7 @@
   do
     -- impl-start
     let content := lines.dropLast.dropLast
-    let text := transform (List.intercalate ['\n'] content)
-    let assembled := splitLines text ++ lines.drop (lines.length - 2)
-    return assembled
+    return splitLines (List.intercalate ['\n'] content) ++ lines.drop (lines.length - 2)
     -- impl-end
 
 prove_correct assembleInsertedLines by
```

Attack 4 — `atk4_orderswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,8 +82,7 @@
     -- impl-start
     let content := lines.dropLast.dropLast
     let text := transform (List.intercalate ['\n'] content)
-    let assembled := splitLines text ++ lines.drop (lines.length - 2)
-    return assembled
+    return lines.drop (lines.length - 2) ++ splitLines text
     -- impl-end
 
 prove_correct assembleInsertedLines by
```

Attack 5 — `atk5_partialdomain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,9 +81,11 @@
   do
     -- impl-start
     let content := lines.dropLast.dropLast
-    let text := transform (List.intercalate ['\n'] content)
-    let assembled := splitLines text ++ lines.drop (lines.length - 2)
-    return assembled
+    if content == [] then
+      return lines.drop (lines.length - 2)
+    else
+      let text := transform (List.intercalate ['\n'] content)
+      return splitLines text ++ lines.drop (lines.length - 2)
     -- impl-end
 
 prove_correct assembleInsertedLines by
```

Attack 6 — `atk6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -80,10 +80,8 @@
       ++ lines.drop (lines.length - 2)
   do
     -- impl-start
-    let content := lines.dropLast.dropLast
-    let text := transform (List.intercalate ['\n'] content)
-    let assembled := splitLines text ++ lines.drop (lines.length - 2)
-    return assembled
+    return splitLines (transform (List.intercalate ['\n'] (lines.dropLast.dropLast)))
+      ++ lines.drop (lines.length - 2)
     -- impl-end
 
 prove_correct assembleInsertedLines by
```

Attack 7 — `atk7_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,8 +82,12 @@
     -- impl-start
     let content := lines.dropLast.dropLast
     let text := transform (List.intercalate ['\n'] content)
-    let assembled := splitLines text ++ lines.drop (lines.length - 2)
-    return assembled
+    let rec loopForever (n : Nat) : List (List Char) :=
+      loopForever (n + 1)
+    if text == text then
+      return loopForever 0
+    else
+      return splitLines text ++ lines.drop (lines.length - 2)
     -- impl-end
 
 prove_correct assembleInsertedLines by
```

Attack 8 — `atk8_doubletransform.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,9 +81,8 @@
   do
     -- impl-start
     let content := lines.dropLast.dropLast
-    let text := transform (List.intercalate ['\n'] content)
-    let assembled := splitLines text ++ lines.drop (lines.length - 2)
-    return assembled
+    let text := transform (transform (List.intercalate ['\n'] content))
+    return splitLines text ++ lines.drop (lines.length - 2)
     -- impl-end
 
 prove_correct assembleInsertedLines by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: assembling the inserted lines is a straight-line
-- computation over finite inputs that always terminates and returns, so a
-- diverging implementation must NOT satisfy the spec (partial correctness
-- would admit it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The registered text transform applied while inserting
--  spliced-in content is an ARBITRARY consumer-supplied function — modeled as the
--  universally-quantified parameter `transform`, about which the spec assumes
--  nothing. The downstream consumer of the assembled lines behaves identically on
--  the produced lines, so it is out of frame.)
-- axioms-end

-- pure-start
/- The host language's line-boundary set: LF, VT, FF, CR, FS, GS, RS, NEL,
   LINE SEPARATOR, PARAGRAPH SEPARATOR. -/
def isLineBreak (c : Char) : Bool :=
  c == '\n' || c == '\x0b' || c == '\x0c' || c == '\r' ||
  c == '\x1c' || c == '\x1d' || c == '\x1e' || c == '\x85' ||
  c == '
' || c == '
'

/- Worker: accumulate the current line (reversed) while scanning; a CR
   immediately followed by LF is a single line boundary; a trailing line
   boundary produces no extra empty field. -/
def splitLinesAux : List Char → List Char → List (List Char)
  | cur, [] => if cur == [] then [] else [cur.reverse]
  | cur, '\r' :: '\n' :: rest => cur.reverse :: splitLinesAux [] rest
  | cur, c :: rest =>
    if isLineBreak c then cur.reverse :: splitLinesAux [] rest
    else splitLinesAux (c :: cur) rest

/- Split a character sequence into lines at the host language's line
   boundaries (isLineBreak, with CR-LF a single boundary), dropping the empty
   field a terminating boundary would produce. This is the value-level model
   of the host language's line splitter on ARBITRARY text — total on the full
   character domain, because it is applied to the output of the
   universally-quantified `transform`, which may emit any character:
   `""` ↦ `[]`, `"a\nb"` ↦ `["a","b"]`, `"a\nb\n"` ↦ `["a","b"]`,
   `"\n"` ↦ `[""]`, `"a\r\nb"` ↦ `["a","b"]`, `"a\rb"` ↦ `["a","b"]`.
   See mapping.md §3.1 for the provenance and reference vectors. -/
def splitLines (s : List Char) : List (List Char) :=
  splitLinesAux [] s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assembling the line sequence to hand to the line inserter when separate
   content is being spliced in, while a content transform is registered.

   The trailing two entries of `lines` are structural end-markers introduced by
   the line reader; they carry no document content and MUST survive untouched.
   Everything before them is the document content: it is re-joined into a single
   text, offered to the registered `transform`, and the (possibly rewritten)
   text is split back into lines. The two end-markers are then reattached
   verbatim.

   `transform` and `lines` are read-only inputs (directive 5): neither is `mut`,
   and the two end-markers are pinned unchanged in the postcondition's tail
   (`lines.drop (lines.length - 2)`) — the result's frame outside the content is
   exactly the original markers. This is the behavior an arbitrary registered
   transform must observe on inserted content, for every `transform`. -/
method assembleInsertedLines
    (transform : List Char → List Char) (lines : List (List Char))
    return (out : List (List Char))
  ensures out =
    splitLines (transform (List.intercalate ['\n'] (lines.dropLast.dropLast)))
      ++ lines.drop (lines.length - 2)
  do
    -- impl-start
    let content := lines.dropLast.dropLast
    let text := transform (List.intercalate ['\n'] content)
    let assembled := splitLines text ++ lines.drop (lines.length - 2)
    return assembled
    -- impl-end

prove_correct assembleInsertedLines by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a COMPLETE FUNCTIONAL POSTCONDITION under total correctness with NO axioms: `out = splitLines (transform (intercalate ['\n'] (lines.dropLast.dropLast))) ++ lines.drop (lines.length - 2)` pins `out` exactly as a pure function of (transform, lines), universally quantified over transform. Any verifying, terminating impl is therefore extensionally equal to gold. I attempted genuine falsification anyway with 8 same-spec attacks (all same_spec=True; spec/axioms/pure/pre/post byte-identical). Verifications run concurrently (<=4) via `bash scripts/lean_verify.sh <f>`.

### Results
- atk_pos.lean (positive control, gold impl verbatim): verify exit 0 (VERIFIES).
- atk1_passthrough.lean (prepatch bug, `return lines`): exit 1 (fails) — reproduces the prepatch defect; matches Solution_prepatch.lean G-DIFF.
- atk2_offbyone.lean (boundary: drop only ONE marker, drop(len-1)): exit 1 (fails).
- atk3_notransform.lean (ungrounded: transform never applied, join+split content only): exit 1 (fails).
- atk4_orderswap.lean (control-flow/structure: markers prepended instead of appended): exit 1 (fails).
- atk5_partialdomain.lean (partial-domain: returns only markers when content==[]): exit 1 (fails).
- atk6_echo.lean (ungrounded-oracle echo: returns postcondition RHS verbatim): exit 0 (VERIFIES) — behaviorally identical to gold (inlined RHS).
- atk7_diverge.lean (control-flow-effect: infinite `loopForever` before return): exit 1 (fails) — total-correctness termination proof correctly rejects divergence ('failed to prove termination'), confirming total semantics excludes the divergent class.
- atk8_doubletransform.lean (transform applied twice): exit 1 (fails).

Only atk6_echo (besides the gold positive control) verifies. Per protocol I MATERIALIZED its faithful patch (= gold patch verbatim, since its impl is extensionally identical to gold) and RAN it through the official harness: `run_resolve('sphinx-doc__sphinx-11510', <patch>, run_id='sbu-audit-atk6-echo')` => RESOLVED=True, COMPLETED=True, NOTE='resolved'. The one verifying wrong-impl candidate RESOLVES; no verifying impl whose faithful patch fails to resolve was found. Under the RESOLVED echo policy (per the audit protocol, a resolving echo is NOT a weakness), this is not a spec break.

refinement.md audit (step 3): 8 legs, all R (A1,A2,A5,A6,A8) or I (A3,A4,A7); §C explicitly declares NO kind-3 steps, NO axioms (A-consumed), NO deep-model references (A-reference). meta.json confirms axioms=[], deep_model_references=[], G-AX status=pass/skip. The A-legs' focus of this review is therefore vacuous by construction — the sole arbitrary element (the consumer source-read handler) is a universally-quantified parameter `transform`, strictly stronger than an axiom (must hold for EVERY handler) and needs no soundness check. Correspondence: A2/A5 faithfully model the emit round-trip `arg=[text]; emit('source-read',docname,arg); text=arg[0]` as `text ↦ transform(text)`; docname/path2doc/install-guard correctly out of frame (listener-absent = identity special case). A6 = full CPython str.splitlines model (isLineBreak enumerates the complete boundary set incl. \r\n-as-one; G-CONF 1.8M checks, 0 disagreements). A8 (downstream StateMachine.insert_input identity on observable text) is empirically validated by the passing resolve run above. No correspondence defect found.

prepatch_reproduced=true (atk1 = `return lines` fails verification exactly as Solution_prepatch.lean does). Verdict: SOUND — >=5 distinct attacks (8 total) run, all wrong impls fail verification, the only verifying non-gold candidate's faithful patch resolves under the official harness. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_passthrough.lean`, `atk2_offbyone.lean`, `atk3_notransform.lean`, `atk4_orderswap.lean`, `atk5_partialdomain.lean`, `atk7_diverge.lean`, `atk8_doubletransform.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk6_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_passthrough.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_notransform.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_orderswap.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_partialdomain.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk7_diverge.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_doubletransform.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: assembling the inserted lines is a straight-line
-- computation over finite inputs that always terminates and returns, so a
-- diverging implementation must NOT satisfy the spec (partial correctness
-- would admit it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The registered text transform applied while inserting
--  spliced-in content is an ARBITRARY consumer-supplied function — modeled as the
--  universally-quantified parameter `transform`, about which the spec assumes
--  nothing. The downstream consumer of the assembled lines behaves identically on
--  the produced lines, so it is out of frame.)
-- axioms-end

-- pure-start
/- The host language's line-boundary set: LF, VT, FF, CR, FS, GS, RS, NEL,
   LINE SEPARATOR, PARAGRAPH SEPARATOR. -/
def isLineBreak (c : Char) : Bool :=
  c == '\n' || c == '\x0b' || c == '\x0c' || c == '\r' ||
  c == '\x1c' || c == '\x1d' || c == '\x1e' || c == '\x85' ||
  c == '
' || c == '
'

/- Worker: accumulate the current line (reversed) while scanning; a CR
   immediately followed by LF is a single line boundary; a trailing line
   boundary produces no extra empty field. -/
def splitLinesAux : List Char → List Char → List (List Char)
  | cur, [] => if cur == [] then [] else [cur.reverse]
  | cur, '\r' :: '\n' :: rest => cur.reverse :: splitLinesAux [] rest
  | cur, c :: rest =>
    if isLineBreak c then cur.reverse :: splitLinesAux [] rest
    else splitLinesAux (c :: cur) rest

/- Split a character sequence into lines at the host language's line
   boundaries (isLineBreak, with CR-LF a single boundary), dropping the empty
   field a terminating boundary would produce. This is the value-level model
   of the host language's line splitter on ARBITRARY text — total on the full
   character domain, because it is applied to the output of the
   universally-quantified `transform`, which may emit any character:
   `""` ↦ `[]`, `"a\nb"` ↦ `["a","b"]`, `"a\nb\n"` ↦ `["a","b"]`,
   `"\n"` ↦ `[""]`, `"a\r\nb"` ↦ `["a","b"]`, `"a\rb"` ↦ `["a","b"]`.
   See mapping.md §3.1 for the provenance and reference vectors. -/
def splitLines (s : List Char) : List (List Char) :=
  splitLinesAux [] s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assembling the line sequence to hand to the line inserter when separate
   content is being spliced in, while a content transform is registered.

   The trailing two entries of `lines` are structural end-markers introduced by
   the line reader; they carry no document content and MUST survive untouched.
   Everything before them is the document content: it is re-joined into a single
   text, offered to the registered `transform`, and the (possibly rewritten)
   text is split back into lines. The two end-markers are then reattached
   verbatim.

   `transform` and `lines` are read-only inputs (directive 5): neither is `mut`,
   and the two end-markers are pinned unchanged in the postcondition's tail
   (`lines.drop (lines.length - 2)`) — the result's frame outside the content is
   exactly the original markers. This is the behavior an arbitrary registered
   transform must observe on inserted content, for every `transform`. -/
method assembleInsertedLines
    (transform : List Char → List Char) (lines : List (List Char))
    return (out : List (List Char))
  ensures out =
    splitLines (transform (List.intercalate ['\n'] (lines.dropLast.dropLast)))
      ++ lines.drop (lines.length - 2)
  do
    -- impl-start
    let content := lines.dropLast.dropLast
    let text := transform (List.intercalate ['\n'] content)
    let assembled := splitLines text ++ lines.drop (lines.length - 2)
    return assembled
    -- impl-end

prove_correct assembleInsertedLines by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a COMPLETE FUNCTIONAL POSTCONDITION under total correctness with NO axioms: `out = splitLines (transform (intercalate ['\n'] (lines.dropLast.dropLast))) ++ lines.drop (lines.length - 2)` pins `out` exactly as a pure function of (transform, lines), universally quantified over transform. Any verifying, terminating impl is therefore extensionally equal to gold. I attempted genuine falsification anyway with 8 same-spec attacks (all same_spec=True; spec/axioms/pure/pre/post byte-identical). Verifications run concurrently (<=4) via `bash scripts/lean_verify.sh <f>`.

### Results
- atk_pos.lean (positive control, gold impl verbatim): verify exit 0 (VERIFIES).
- atk1_passthrough.lean (prepatch bug, `return lines`): exit 1 (fails) — reproduces the prepatch defect; matches Solution_prepatch.lean G-DIFF.
- atk2_offbyone.lean (boundary: drop only ONE marker, drop(len-1)): exit 1 (fails).
- atk3_notransform.lean (ungrounded: transform never applied, join+split content only): exit 1 (fails).
- atk4_orderswap.lean (control-flow/structure: markers prepended instead of appended): exit 1 (fails).
- atk5_partialdomain.lean (partial-domain: returns only markers when content==[]): exit 1 (fails).
- atk6_echo.lean (ungrounded-oracle echo: returns postcondition RHS verbatim): exit 0 (VERIFIES) — behaviorally identical to gold (inlined RHS).
- atk7_diverge.lean (control-flow-effect: infinite `loopForever` before return): exit 1 (fails) — total-correctness termination proof correctly rejects divergence ('failed to prove termination'), confirming total semantics excludes the divergent class.
- atk8_doubletransform.lean (transform applied twice): exit 1 (fails).

Only atk6_echo (besides the gold positive control) verifies. Per protocol I MATERIALIZED its faithful patch (= gold patch verbatim, since its impl is extensionally identical to gold) and RAN it through the official harness: `run_resolve('sphinx-doc__sphinx-11510', <patch>, run_id='sbu-audit-atk6-echo')` => RESOLVED=True, COMPLETED=True, NOTE='resolved'. The one verifying wrong-impl candidate RESOLVES; no verifying impl whose faithful patch fails to resolve was found. Under the RESOLVED echo policy (per the audit protocol, a resolving echo is NOT a weakness), this is not a spec break.

refinement.md audit (step 3): 8 legs, all R (A1,A2,A5,A6,A8) or I (A3,A4,A7); §C explicitly declares NO kind-3 steps, NO axioms (A-consumed), NO deep-model references (A-reference). meta.json confirms axioms=[], deep_model_references=[], G-AX status=pass/skip. The A-legs' focus of this review is therefore vacuous by construction — the sole arbitrary element (the consumer source-read handler) is a universally-quantified parameter `transform`, strictly stronger than an axiom (must hold for EVERY handler) and needs no soundness check. Correspondence: A2/A5 faithfully model the emit round-trip `arg=[text]; emit('source-read',docname,arg); text=arg[0]` as `text ↦ transform(text)`; docname/path2doc/install-guard correctly out of frame (listener-absent = identity special case). A6 = full CPython str.splitlines model (isLineBreak enumerates the complete boundary set incl. \r\n-as-one; G-CONF 1.8M checks, 0 disagreements). A8 (downstream StateMachine.insert_input identity on observable text) is empirically validated by the passing resolve run above. No correspondence defect found.

prepatch_reproduced=true (atk1 = `return lines` fails verification exactly as Solution_prepatch.lean does). Verdict: SOUND — >=5 distinct attacks (8 total) run, all wrong impls fail verification, the only verifying non-gold candidate's faithful patch resolves under the official harness. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of assembleInsertedLines vs the gold _insert_input (sphinx/directives/other.py, patch.diff). Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True under the velvet backend. Solution.lean verifies (lean_verify.sh exit 0, total correctness, demonic choice).

Modeled postcondition: out = splitLines (transform (intercalate ['\n'] (lines.dropLast.dropLast))) ++ lines.drop (lines.length-2), matching gold dataflow text="\n".join(include_lines[:-2]); emit; include_lines=text.splitlines()+include_lines[-2:].

Verified legs:
1. splitLines vs CPython str.splitlines(): isLineBreak boundary set is EXACTLY CPython's — checked all 0x110000 codepoints, zero missing/extra (LF/VT/FF/CR/FS/GS/RS/NEL/LS/PS). CR-LF collapsed to one boundary; no trailing empty field on terminating boundary. Exhaustive strings over a 12-char alphabet up to length 4 (0 mismatches) + the mapping's reference vectors reproduce CPython exactly.
2. Slice ops: dropLast.dropLast == [:-2] and drop(length-2) == [-2:] for all list lengths, incl. len 0/1 where Lean Nat-subtraction underflows to 0 (drop 0) and matches Python negative-slice-on-short-list.
3. join: intercalate ['\n'] == "\n".join — exact.
4. Whole-assembly fuzz: 200k random inputs (lists len 0-6, char alphabet incl. all boundary chars, transforms incl. identity/const/append-\r/replace-\n-with-\r/boundary-injecting) — model output equals gold dataflow output on every case, 0 mismatches.

transform is universally quantified with no assumptions (no axiom); this is a superset of realizable source-read net effects, so the spec is not weakened by an over-narrow transform, and not strengthened beyond the gold behavior. No input on which the modeled function disagrees with the real repo callee was found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-verified the accepted relaxed-leakage disposition (relaxed_leakage=true, G-LEAK status "relaxed", RELAXED_LEAKAGE.md present); NOT a rubber-stamp. Findings:

1. same_spec(Solution.lean, Solution_prepatch.lean, velvet tables) = True — spec region byte-identical; the leak lives entirely in the frozen spec view.

2. Core soundness re-run locally: G-VERIFY Solution.lean verifies (lean_verify.sh exit 0); G-DIFF Solution_prepatch.lean (`return lines` pass-through) FAILS prove_correct with unsolved goal `lines = splitLines (transform (intercalate ['\n'] lines.dropLast.dropLast)) ++ drop (len-2) lines` (exit 1). Spec genuinely discriminates the gold from the pre-patch behavior.

3. problem_statement (public) scan: it is a pure symptom report — a consumer source-read handler doing &REPLACE_ME;->REPLACED is not applied to include'd content. 0 occurrences of {marker, 0.18, two lines, [:-2], [-2:], splitlines, join, split, insert_input, StateMachine}. The join/emit/splitlines monkey-patch mechanism appears ONLY in hints_text (excluded from the leakage standard), and even the hint's naive workaround lacks the two-marker strip/reattach refinement.

4. Spec-view lexical scan: no gold tokens (source-read, insert_input, StateMachine, docutils, include_lines) present — the mechanical G-LEAK lexical screen correctly passes. The leak is SEMANTIC: the postcondition `out = splitLines (transform (intercalate ['\n'] (lines.dropLast.dropLast))) ++ lines.drop (lines.length - 2)` plus the docstring 'trailing two entries ... structural end-markers ... MUST survive untouched' encode exactly the gold's `"\n".join(include_lines[:-2])` -> emit -> `text.splitlines() + include_lines[-2:]`.

5. Unavoidability re-derived: the F2P test_include_source_read_event asserts the handler observed EXACTLY the included content minus its two markers, then the markers reattach. A spec weak enough to hide the two-marker frame admits marker-leaking/marker-dropping impls (mutations killed only by this clause); a spec hiding the round-trip admits the prepatch pass-through (G-DIFF must fail). The two-marker frame is a docutils-0.18-internal artifact not derivable from the public PS. Hence PS-only + faithful is impossible; the leak survives full de-narration because it is in executable postcondition structure, not prose.

Conclusion: the disclosed content is precisely the dispositioned (a) round-trip + (b) two-marker facet; no NEW leaking line beyond it, and no broken core gate (all sound). Per gates/_audit.py + RELAXED_LEAKAGE.md recording convention, a properly-dispositioned relaxed leak records as NO-LEAKAGE (pass) + note at the panel_3 layer. Known dispositioned facet re-confirmed; no leak beyond it found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
