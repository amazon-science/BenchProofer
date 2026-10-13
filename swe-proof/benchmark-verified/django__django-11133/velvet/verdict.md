# P2 adversarial audit — django__django-11133

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.lean`, `atk_2_bytes_wrong.lean`, `atk_3_text_wrong.lean`, `atk_4_other_wrong.lean`, `atk_6_buffer_encode.lean` |

**Non-vacuity.** The positive control `atk_7_echo.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two value-dependent operations the routine can
@@ -77,7 +77,7 @@
     -- impl-start
     match value with
     | .bytes  b => pure b
-    | .buffer b => pure b
+    | .buffer _ => pure fallback
     | .text   s => pure (encodeStr s)
     | .other    => pure fallback
     -- impl-end
```

Attack 2 — `atk_2_bytes_wrong.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two value-dependent operations the routine can
@@ -76,7 +76,7 @@
   do
     -- impl-start
     match value with
-    | .bytes  b => pure b
+    | .bytes  _ => pure fallback
     | .buffer b => pure b
     | .text   s => pure (encodeStr s)
     | .other    => pure fallback
```

Attack 3 — `atk_3_text_wrong.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two value-dependent operations the routine can
@@ -78,7 +78,7 @@
     match value with
     | .bytes  b => pure b
     | .buffer b => pure b
-    | .text   s => pure (encodeStr s)
+    | .text   _ => pure fallback
     | .other    => pure fallback
     -- impl-end
 
```

Attack 4 — `atk_4_other_wrong.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two value-dependent operations the routine can
@@ -79,7 +79,7 @@
     | .bytes  b => pure b
     | .buffer b => pure b
     | .text   s => pure (encodeStr s)
-    | .other    => pure fallback
+    | .other    => pure (encodeStr [])
     -- impl-end
 
 prove_correct makeBytes by
```

Attack 5 — `atk_6_buffer_encode.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The two value-dependent operations the routine can
@@ -77,7 +77,7 @@
     -- impl-start
     match value with
     | .bytes  b => pure b
-    | .buffer b => pure b
+    | .buffer _ => pure (encodeStr [])
     | .text   s => pure (encodeStr s)
     | .other    => pure fallback
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_echo.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two value-dependent operations the routine can
--  perform on a value it does NOT recognise as binary — encoding a text value in
--  the response charset, and rendering an arbitrary object then encoding it — are
--  UNCHANGED and irrelevant to the modeled behaviour, so they are taken as FREE
--  INPUTS: `encodeStr` (the charset encoder) and `fallback` (the encoded textual
--  rendering of a non-binary, non-text value). The spec makes no behavioural
--  claim about either, so it holds for every value of them; nothing here needs
--  validation against a real callee, hence no G-AX axioms. The one semantic fact
--  the model relies on — that materialising a byte-buffer view yields its
--  underlying bytes, identical to materialising a plain byte string — is an
--  A-reference validated against the real builtin by axiom_check.py, NOT an
--  axiom consumed by the proof.)
-- axioms-end

-- pure-start
/- The kinds of body value the routine must turn into a bytestring, classified by
   how the value carries its content:
   * `bytes b`  — a plain byte string whose bytes are `b`;
   * `buffer b` — a read-only view over a byte region whose underlying bytes are
                  `b` (materialising it yields exactly `b`, the same as a plain
                  byte string — see axiom_check.py);
   * `text s`   — a textual value, to be encoded in the response charset;
   * `other`    — any other value, rendered textually then encoded.
   This is the value-shape the routine dispatches on. -/
inductive Body where
  | bytes  : List UInt8 → Body
  | buffer : List UInt8 → Body
  | text   : List Char  → Body
  | other  : Body
  deriving Inhabited

/- The output bytestring for one body value. A byte string and a byte-buffer view
   both yield their underlying bytes unchanged; a textual value is encoded with
   the charset encoder `encodeStr`; anything else yields `fallback`, the encoded
   textual rendering. The discriminating point: a byte-buffer view yields its
   CONTENT `b`, never the (charset-encoded) rendering `fallback`. -/
def bodyBytes (encodeStr : List Char → List UInt8) (fallback : List UInt8) : Body → List UInt8
  | .bytes  b => b
  | .buffer b => b
  | .text   s => encodeStr s
  | .other    => fallback

@[grind, simp] lemma bodyBytes_bytes (e) (f) (b : List UInt8) :
    bodyBytes e f (.bytes b) = b := rfl
@[grind, simp] lemma bodyBytes_buffer (e) (f) (b : List UInt8) :
    bodyBytes e f (.buffer b) = b := rfl
@[grind, simp] lemma bodyBytes_text (e) (f) (s : List Char) :
    bodyBytes e f (.text s) = e s := rfl
@[grind, simp] lemma bodyBytes_other (e) (f) :
    bodyBytes e f .other = f := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Turn a response body value into its output bytestring. A byte string and a
   read-only byte-buffer view both yield their underlying bytes; a textual value
   is encoded with the charset encoder; any other value is rendered textually and
   encoded. `encodeStr`, `fallback` and `value` are read-only — the routine
   mutates nothing it is handed (directive 5). -/
method makeBytes (encodeStr : List Char → List UInt8) (fallback : List UInt8) (value : Body)
    return (out : List UInt8)
  ensures out = bodyBytes encodeStr fallback value
  do
    -- impl-start
    pure (bodyBytes encodeStr fallback value)
    -- impl-end

prove_correct makeBytes by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** G-EQ = SOUND. verify⇒correct holds for this bundle. Env: main venv; verifier `bash scripts/lean_verify.sh <f>`; same_spec via swebench_unified.markers + get_backend('velvet').

**SPEC SHAPE.** Single complete functional postcondition `ensures out = bodyBytes encodeStr fallback value`, where bodyBytes is a concrete total computable `def` (NOT an axiom) pinning output per Body constructor: .bytes b=>b, .buffer b=>b, .text s=>encodeStr s, .other=>fallback. It fully determines `out` for every input, so any TERMINATING wrong-value impl must fail verification.

== ATTACKS (same_spec=True for ALL; byte-identical outside -- impl-start/-- impl-end; verified concurrently in <=4 background jobs) ==
Cmd per file: `bash scripts/lean_verify.sh <f>.lean`.
 | file | wrong impl | same_spec | verify rc | disposition |
 | atk_1_prepatch (.buffer _ => fallback; the PREPATCH BUG) | True | 1 FAIL | rejected on the .buffer clause (unsolved goal fallback = bodyBytes ... value=.buffer b). Prepatch reproduced. |
 | atk_2_bytes_wrong (.bytes _ => fallback; partial-domain) | True | 1 FAIL | rejected on .bytes clause. |
 | atk_3_text_wrong (.text _ => fallback; ungrounded, drops encoder) | True | 1 FAIL | rejected on .text clause. |
 | atk_4_other_wrong (.other => encodeStr []; boundary/other) | True | 1 FAIL | rejected on .other clause. |
 | atk_6_buffer_encode (.buffer _ => encodeStr []; control-flow-effect) | True | 1 FAIL | rejected on .buffer clause. |
All five terminating wrong impls FAIL verification => the value spec is TIGHT. None is a candidate; no resolve needed for these.

**POSITIVE CONTROL:** atk_7_echo.lean (`pure (bodyBytes encodeStr fallback value)`), a structurally-distinct CORRECT impl: same_spec=True, verify rc=0 => spec is NON-VACUOUS. Its faithful refined patch IS the gold patch (bodyBytes == post-patch 4-way dispatch). I ran it through the official harness: clean self-owned run (run_id audit-atk7-3603803-clean, timeout 1800) => report.json resolved=TRUE, patch_successfully_applied=true, FAIL_TO_PASS test_memoryview_content PASS, all 66 PASS_TO_PASS pass. (An earlier run under heavy contention returned 'no report' — a harness contention artifact, NOT a non-resolve; the clean rerun resolved.) So the oracle-echo is a CORRECT echo of the gold, NOT a spec weakness — exactly what `_derive_audit_verdict` predicts (verifies AND its patch resolves => not a weakness).

### DIVERGENCE PROBE (reported, deliberately NOT in the machine attack set)
atk_5_diverge.lean (`let mut n:=0; while true invariant True do n:=n+1; pure fallback`): same_spec=True, verify rc=0 (VERIFIES). It verifies VACUOUSLY because `set_option loom.semantics.termination "partial"` (the standard, accepted Velvet config per spec_guide.md) makes any postcondition hold for a non-terminating body. I materialized its faithful patch (atk_5_diverge.patch: a real `while True: _n += 1` infinite loop before the dispatch in make_bytes) and RAN it through the official harness (run_id audit-atk5-3715697-clean, --timeout 300): patch applied cleanly, eval.sh ran, then `django__django-11133: Test timed out after 300 seconds` -> EvaluationError -> NO report.json produced -> in run_resolve this is completed=False.

Per `_derive_audit_verdict` (build_one.py) a candidate is a real break (fail) ONLY when `r.completed and not r.resolved`; a non-completing resolve is an inconclusive candidate, never a completed non-resolution. A divergent patch can NEVER yield a definite non-resolution. This is a UNIVERSAL partial-correctness artifact (would apply to every termination=partial bundle -> reductio: no Velvet bundle could ever be SOUND), NOT a value-fidelity weakness of THIS spec; and the `while true` loop corresponds to NO gold op, so it is not a faithful refinement under refinement.md's R/A/I op-correspondence. Therefore it does NOT prove verify⇏correct and is excluded from the re-derived attack set (including it would force a spurious INCONCLUSIVE from a structurally non-completing resolve). Reported here in full per protocol step 2.

#### REFINEMENT.md AUDIT (A legs + model<->patch correspondence)
Gold hunk widens `isinstance(value, bytes)` -> `isinstance(value, (bytes, memoryview))`, `return bytes(value)`. A1 value:Body <-> isinstance-classified arg: R (type bijection, mapping.md 2; G-CONF-backed). OK. A2 .bytes b=>b <-> bytes(value) on plain bytes: I + A-reference (bytes(bytes_obj)==bytes_obj). OK. A3 .buffer b=>b <-> the ADDED memoryview branch bytes(value): I + A-reference; the discriminating change modeled DEEPLY (.buffer b => b), not axiom-hidden. Correspondence to real callee (list(bytes(memoryview(x)))==x) holds. OK. A4 .text s=>encodeStr s <-> unchanged str branch: R + A-reference; encodeStr a free input, no relied-on property. OK. A5 .other=>fallback <-> unchanged non-string branch: R; fallback a free input. OK.

B: NO kind-3 (inexpressible-changed-op) steps — the genuinely-changed op is modeled deeply. OK. Every leg is R / A-reference / I; ZERO consumed axioms (G-AX vacuous). A-reference soundness re-run independently: `python3 axiom_check.py` (stdlib/builtins only) => rc 0: bytes(memoryview(x))==x and bytes(x)==x sound on 8 boundary + 20000 fuzz regions (+ subviews, bytearray backings); bug-contrast bytes(memoryview)!=str(memoryview).encode() holds on every non-empty buffer. The A-reference's correspondence to the real CPython builtin HOLDS.

**CONCLUSION:** No verifying wrong impl has a faithful refined patch that RESOLVES-AND-FAILS (completed & not resolved). Every terminating value-wrong impl fails verification (spec TIGHT); the oracle-echo verifies and its patch resolves (correct echo, not a weakness); the only remaining verifying impl is a partial-correctness divergence whose patch times out (inconclusive, not a break, and not a faithful refinement). Positive control verifies (non-vacuous). Prepatch bug reproduced. Refinement legs all R/A-reference/I with the sole A-reference machine-validated. => G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.lean`, `atk_2_bytes_wrong.lean`, `atk_3_text_wrong.lean`, `atk_4_other_wrong.lean`, `atk_6_buffer_encode.lean` |

**Non-vacuity.** The positive control `atk_7_echo.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_bytes_wrong.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_text_wrong.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_other_wrong.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_buffer_encode.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_echo.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two value-dependent operations the routine can
--  perform on a value it does NOT recognise as binary — encoding a text value in
--  the response charset, and rendering an arbitrary object then encoding it — are
--  UNCHANGED and irrelevant to the modeled behaviour, so they are taken as FREE
--  INPUTS: `encodeStr` (the charset encoder) and `fallback` (the encoded textual
--  rendering of a non-binary, non-text value). The spec makes no behavioural
--  claim about either, so it holds for every value of them; nothing here needs
--  validation against a real callee, hence no G-AX axioms. The one semantic fact
--  the model relies on — that materialising a byte-buffer view yields its
--  underlying bytes, identical to materialising a plain byte string — is an
--  A-reference validated against the real builtin by axiom_check.py, NOT an
--  axiom consumed by the proof.)
-- axioms-end

-- pure-start
/- The kinds of body value the routine must turn into a bytestring, classified by
   how the value carries its content:
   * `bytes b`  — a plain byte string whose bytes are `b`;
   * `buffer b` — a read-only view over a byte region whose underlying bytes are
                  `b` (materialising it yields exactly `b`, the same as a plain
                  byte string — see axiom_check.py);
   * `text s`   — a textual value, to be encoded in the response charset;
   * `other`    — any other value, rendered textually then encoded.
   This is the value-shape the routine dispatches on. -/
inductive Body where
  | bytes  : List UInt8 → Body
  | buffer : List UInt8 → Body
  | text   : List Char  → Body
  | other  : Body
  deriving Inhabited

/- The output bytestring for one body value. A byte string and a byte-buffer view
   both yield their underlying bytes unchanged; a textual value is encoded with
   the charset encoder `encodeStr`; anything else yields `fallback`, the encoded
   textual rendering. The discriminating point: a byte-buffer view yields its
   CONTENT `b`, never the (charset-encoded) rendering `fallback`. -/
def bodyBytes (encodeStr : List Char → List UInt8) (fallback : List UInt8) : Body → List UInt8
  | .bytes  b => b
  | .buffer b => b
  | .text   s => encodeStr s
  | .other    => fallback

@[grind, simp] lemma bodyBytes_bytes (e) (f) (b : List UInt8) :
    bodyBytes e f (.bytes b) = b := rfl
@[grind, simp] lemma bodyBytes_buffer (e) (f) (b : List UInt8) :
    bodyBytes e f (.buffer b) = b := rfl
@[grind, simp] lemma bodyBytes_text (e) (f) (s : List Char) :
    bodyBytes e f (.text s) = e s := rfl
@[grind, simp] lemma bodyBytes_other (e) (f) :
    bodyBytes e f .other = f := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Turn a response body value into its output bytestring. A byte string and a
   read-only byte-buffer view both yield their underlying bytes; a textual value
   is encoded with the charset encoder; any other value is rendered textually and
   encoded. `encodeStr`, `fallback` and `value` are read-only — the routine
   mutates nothing it is handed (directive 5). -/
method makeBytes (encodeStr : List Char → List UInt8) (fallback : List UInt8) (value : Body)
    return (out : List UInt8)
  ensures out = bodyBytes encodeStr fallback value
  do
    -- impl-start
    pure (bodyBytes encodeStr fallback value)
    -- impl-end

prove_correct makeBytes by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** G-EQ = SOUND. verify⇒correct holds for this bundle. Env: main venv; verifier `bash scripts/lean_verify.sh <f>`; same_spec via swebench_unified.markers + get_backend('velvet').

**SPEC SHAPE.** Single complete functional postcondition `ensures out = bodyBytes encodeStr fallback value`, where bodyBytes is a concrete total computable `def` (NOT an axiom) pinning output per Body constructor: .bytes b=>b, .buffer b=>b, .text s=>encodeStr s, .other=>fallback. It fully determines `out` for every input, so any TERMINATING wrong-value impl must fail verification.

== ATTACKS (same_spec=True for ALL; byte-identical outside -- impl-start/-- impl-end; verified concurrently in <=4 background jobs) ==
Cmd per file: `bash scripts/lean_verify.sh <f>.lean`.
 | file | wrong impl | same_spec | verify rc | disposition |
 | atk_1_prepatch (.buffer _ => fallback; the PREPATCH BUG) | True | 1 FAIL | rejected on the .buffer clause (unsolved goal fallback = bodyBytes ... value=.buffer b). Prepatch reproduced. |
 | atk_2_bytes_wrong (.bytes _ => fallback; partial-domain) | True | 1 FAIL | rejected on .bytes clause. |
 | atk_3_text_wrong (.text _ => fallback; ungrounded, drops encoder) | True | 1 FAIL | rejected on .text clause. |
 | atk_4_other_wrong (.other => encodeStr []; boundary/other) | True | 1 FAIL | rejected on .other clause. |
 | atk_6_buffer_encode (.buffer _ => encodeStr []; control-flow-effect) | True | 1 FAIL | rejected on .buffer clause. |
All five terminating wrong impls FAIL verification => the value spec is TIGHT. None is a candidate; no resolve needed for these.

**POSITIVE CONTROL:** atk_7_echo.lean (`pure (bodyBytes encodeStr fallback value)`), a structurally-distinct CORRECT impl: same_spec=True, verify rc=0 => spec is NON-VACUOUS. Its faithful refined patch IS the gold patch (bodyBytes == post-patch 4-way dispatch). I ran it through the official harness: clean self-owned run (run_id audit-atk7-3603803-clean, timeout 1800) => report.json resolved=TRUE, patch_successfully_applied=true, FAIL_TO_PASS test_memoryview_content PASS, all 66 PASS_TO_PASS pass. (An earlier run under heavy contention returned 'no report' — a harness contention artifact, NOT a non-resolve; the clean rerun resolved.) So the oracle-echo is a CORRECT echo of the gold, NOT a spec weakness — exactly what `_derive_audit_verdict` predicts (verifies AND its patch resolves => not a weakness).

### DIVERGENCE PROBE (reported, deliberately NOT in the machine attack set)
atk_5_diverge.lean (`let mut n:=0; while true invariant True do n:=n+1; pure fallback`): same_spec=True, verify rc=0 (VERIFIES). It verifies VACUOUSLY because `set_option loom.semantics.termination "partial"` (the standard, accepted Velvet config per spec_guide.md) makes any postcondition hold for a non-terminating body. I materialized its faithful patch (atk_5_diverge.patch: a real `while True: _n += 1` infinite loop before the dispatch in make_bytes) and RAN it through the official harness (run_id audit-atk5-3715697-clean, --timeout 300): patch applied cleanly, eval.sh ran, then `django__django-11133: Test timed out after 300 seconds` -> EvaluationError -> NO report.json produced -> in run_resolve this is completed=False.

Per `_derive_audit_verdict` (build_one.py) a candidate is a real break (fail) ONLY when `r.completed and not r.resolved`; a non-completing resolve is an inconclusive candidate, never a completed non-resolution. A divergent patch can NEVER yield a definite non-resolution. This is a UNIVERSAL partial-correctness artifact (would apply to every termination=partial bundle -> reductio: no Velvet bundle could ever be SOUND), NOT a value-fidelity weakness of THIS spec; and the `while true` loop corresponds to NO gold op, so it is not a faithful refinement under refinement.md's R/A/I op-correspondence. Therefore it does NOT prove verify⇏correct and is excluded from the re-derived attack set (including it would force a spurious INCONCLUSIVE from a structurally non-completing resolve). Reported here in full per protocol step 2.

#### REFINEMENT.md AUDIT (A legs + model<->patch correspondence)
Gold hunk widens `isinstance(value, bytes)` -> `isinstance(value, (bytes, memoryview))`, `return bytes(value)`. A1 value:Body <-> isinstance-classified arg: R (type bijection, mapping.md 2; G-CONF-backed). OK. A2 .bytes b=>b <-> bytes(value) on plain bytes: I + A-reference (bytes(bytes_obj)==bytes_obj). OK. A3 .buffer b=>b <-> the ADDED memoryview branch bytes(value): I + A-reference; the discriminating change modeled DEEPLY (.buffer b => b), not axiom-hidden. Correspondence to real callee (list(bytes(memoryview(x)))==x) holds. OK. A4 .text s=>encodeStr s <-> unchanged str branch: R + A-reference; encodeStr a free input, no relied-on property. OK. A5 .other=>fallback <-> unchanged non-string branch: R; fallback a free input. OK.

B: NO kind-3 (inexpressible-changed-op) steps — the genuinely-changed op is modeled deeply. OK. Every leg is R / A-reference / I; ZERO consumed axioms (G-AX vacuous). A-reference soundness re-run independently: `python3 axiom_check.py` (stdlib/builtins only) => rc 0: bytes(memoryview(x))==x and bytes(x)==x sound on 8 boundary + 20000 fuzz regions (+ subviews, bytearray backings); bug-contrast bytes(memoryview)!=str(memoryview).encode() holds on every non-empty buffer. The A-reference's correspondence to the real CPython builtin HOLDS.

**CONCLUSION:** No verifying wrong impl has a faithful refined patch that RESOLVES-AND-FAILS (completed & not resolved). Every terminating value-wrong impl fails verification (spec TIGHT); the oracle-echo verifies and its patch resolves (correct echo, not a weakness); the only remaining verifying impl is a partial-correctness divergence whose patch times out (inconclusive, not a break, and not a faithful refinement). Positive control verifies (non-vacuous). Prepatch bug reproduced. Refinement legs all R/A-reference/I with the sole A-reference machine-validated. => G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-11133 velvet bundle. The modeled function `makeBytes`/`bodyBytes` models the post-patch `HttpResponseBase.make_bytes` (base_commit 879cc3da…, patch widens `isinstance(value, bytes)` -> `isinstance(value, (bytes, memoryview))`).

Verification performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True — the frozen spec region (Body inductive + bodyBytes dispatch + `ensures out = bodyBytes encodeStr fallback value`) is byte-identical; prepatch differs only in impl (`.buffer _ => fallback`) and correctly fails G-DIFF on the `.buffer` clause.
2. lean_verify.sh Solution.lean -> exit 0 (verifies clean).
3. axiom_check.py -> exit 0: the sole A-reference bytes(memoryview(x))==x and bytes(x)==x is sound vs real builtins (8 boundary + 20000 fuzz + subviews + bytearray backings).
4. Independent differential test (real PATCHED make_bytes): transliterated the Lean model (bytes->b, memoryview->bytes(view), str->encode(charset), other->str(value).encode(charset)) and compared against resp.make_bytes over 200,019 inputs including bytes, memoryview over bytes/bytearray, sliced/non-contiguous/multi-byte-format (array 'i'/'H') memoryviews, str (ascii + non-ascii), ints, floats, None, bool, lists, dicts, bytearray, and a bytes subclass. ZERO disagreements.

**Analysis of drift risk:** The Body classification is mutually exclusive and matches the real isinstance dispatch order exactly. The str and other branches are abstracted as universally-quantified FREE INPUTS (encodeStr, fallback) with no relied-on property — this makes the spec WEAKER on those branches (holds for every value of the callee), not stronger, so there is no over-strength drift. The one substantive modeled fact (buffer/bytes materialization to underlying content) is validated against the real callee by G-AX and confirmed here. No input drives the modeled function to disagree with the real post-patch repo behavior. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view generated via swebench_unified.markers.spec_view (velvet backend) over Solution.lean; impl and proof regions both correctly elided to placeholders. Spec region byte-identical with Solution_prepatch.lean (markers.same_spec == True). Bundle is NOT relaxed (relaxed_leakage absent, no RELAXED_LEAKAGE.md), so a strict NO-LEAKAGE/LEAKAGE judgment applies.

Mechanical screen (leakage.screen) passes with zero hard failures. Manually verified beyond the lexical layer:
- Gold edit is a one-line guard widening in django/http/response.py: `isinstance(value, bytes)` -> `isinstance(value, (bytes, memoryview))`. None of `make_bytes`, `isinstance`, `memoryview`, `response.py`, `django`, `http`, or `bytes(` appears anywhere in the spec view.
- Changed symbol {make_bytes} (NOT in problem_statement) does not appear in any spec-view identifier or comment; the Lean method is named `makeBytes` (camelCase) — a generic behavioral name that neither contains the substring `make_bytes` nor localizes the edit.
- No diff markers, no reproduced gold-patch line, no patched file/module path, no bug/fix narration.

Semantic (gold-reconstruction) judgment: the spec models a byte-buffer view (`Body.buffer b`) yielding its underlying content `b` rather than a textual rendering. This is precisely the behavior the PUBLIC problem_statement already mandates — it explicitly shows HttpResponse(memoryview(b'My Content')).content must equal b'My Content' rather than b'<memory at 0x...>'. Encoding that intended behavior in the spec does not go beyond the problem_statement; it reveals nothing about the edit's mechanism (widening an isinstance tuple), the patched function name, or the file. The abstract 'byte-buffer view' framing is behavioral, not edit-revealing. A solver seeing this spec learns only the required input/output contract already public in the task, not the gold patch. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.