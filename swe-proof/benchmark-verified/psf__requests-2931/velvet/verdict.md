# P2 adversarial audit — psf__requests-2931

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_native.lean`, `atk_empty.lean`, `atk_cf.lean`, `atk_rev.lean`, `atk_kind.lean`, `atk_diverge2.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No TERMINATING same-spec impl verifies without being value-correct. The postcondition `ensures out = data` is exact structural equality over a DecidableEq `Payload` (kind + content), so loom_solve admits only impls whose returned value is provably `data` — i.e. the identity, which equals the gold hunk-1 behaviour and resolves. All 7 terminating wrong impls (prepatch coercion, native-coerce echo, .text [] boundary, control-flow binary-coerce, octet-reverse, text->binary kind-swap, and divergence-with-WRONG-return atk_diverge2) FAIL to verify (exit 1) on the discriminating clause. The only verifying-wrong impls (atk_diverge, atk_partdiv) deviate SOLELY by non-termination, which is the universal partial-correctness escape, not a refinement-fidelity defect — see notes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only modeled repo callee — the native-string
@@ -55,7 +55,8 @@
   ensures out = data
   do
     -- impl-start
-    return data
+    let r ← pure (toNativeString data)
+    return r
     -- impl-end
 
 prove_correct encodePayload by
```

Attack 2 — `atk_native.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only modeled repo callee — the native-string
@@ -55,7 +55,7 @@
   ensures out = data
   do
     -- impl-start
-    return data
+    return (toNativeString data)
     -- impl-end
 
 prove_correct encodePayload by
```

Attack 3 — `atk_empty.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only modeled repo callee — the native-string
@@ -55,7 +55,7 @@
   ensures out = data
   do
     -- impl-start
-    return data
+    return (.text [])
     -- impl-end
 
 prove_correct encodePayload by
```

Attack 4 — `atk_cf.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only modeled repo callee — the native-string
@@ -55,7 +55,9 @@
   ensures out = data
   do
     -- impl-start
-    return data
+    match data with
+    | .text s => return (.text s)
+    | .binary b => return (toNativeString (.binary b))
     -- impl-end
 
 prove_correct encodePayload by
```

Attack 5 — `atk_rev.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only modeled repo callee — the native-string
@@ -55,7 +55,9 @@
   ensures out = data
   do
     -- impl-start
-    return data
+    match data with
+    | .text s => return (.text s)
+    | .binary b => return (.binary b.reverse)
     -- impl-end
 
 prove_correct encodePayload by
```

Attack 6 — `atk_kind.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only modeled repo callee — the native-string
@@ -55,7 +55,9 @@
   ensures out = data
   do
     -- impl-start
-    return data
+    match data with
+    | .text s => return (.binary (s.map (fun c => UInt8.ofNat c.toNat)))
+    | .binary b => return (.binary b)
     -- impl-end
 
 prove_correct encodePayload by
```

Attack 7 — `atk_diverge2.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only modeled repo callee — the native-string
@@ -55,7 +55,12 @@
   ensures out = data
   do
     -- impl-start
-    return data
+    let mut k := 0
+    while k = 0
+      invariant True
+    do
+      k := k
+    return (.text [])
     -- impl-end
 
 prove_correct encodePayload by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The only modeled repo callee — the native-string
--  coercion `toNativeString` — is modeled DEEPLY in the pure region below and
--  validated `== ` its real counterpart by axiom_check.py (G-AX, A-reference),
--  not consumed as an opaque axiom. The modeled operation itself is
--  specified directly, never axiomatized.)
-- axioms-end

-- pure-start
/- A payload value carried by an HTTP request: either a text payload (a sequence
   of code points) or a binary payload (a sequence of octets). The two are
   DISTINCT carriers — a binary payload is not a text payload — which is exactly
   the property the consumer observes (`isinstance(body, bytes)`). -/
inductive Payload where
  | text (s : List Char)
  | binary (b : List UInt8)
  deriving DecidableEq, Inhabited

/- `toNativeString`: the native-string coercion named in the problem statement.
   On a text payload it is the identity; on a binary payload it yields the text
   payload obtained by decoding each octet to its corresponding code point.
   Deep model (A-reference) of the standard coercion; validated against the real
   callee on its in-domain inputs by axiom_check.py (G-AX). Always yields a TEXT
   payload. -/
def toNativeString : Payload → Payload
  | .text s   => .text s
  | .binary b => .text (b.map (fun u => Char.ofNat u.toNat))

@[grind] lemma toNativeString_text (s : List Char) :
    toNativeString (.text s) = .text s := rfl
@[grind] lemma toNativeString_binary (b : List UInt8) :
    toNativeString (.binary b) = .text (b.map (fun u => Char.ofNat u.toNat)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Encoding a str/bytes payload for transmission returns the payload UNCHANGED:
   both its kind (text vs binary) and its content are preserved. In particular a
   binary payload stays binary — it is never coerced to a text payload. `data`
   is read-only (not `mut`); the operation mutates nothing it is handed
   (directive 5). -/
method encodePayload (data : Payload) return (out : Payload)
  ensures out = data
  do
    -- impl-start
    return data
    -- impl-end

prove_correct encodePayload by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: G-EQ audits the A-legs and the model<->patch correspondence (R/I pre-cleared by G-CONF). Verdict: SOUND. Machine-checked evidence below; the runner re-runs everything.

SPEC SHAPE. Current shipped Solution.lean models ONE method, encodePayload (data: Payload) ensures out = data, under loom.semantics.termination "partial" + demonic choice. Payload = .text (List Char) | .binary (List UInt8), DecidableEq. `data` is read-only. (Note: the stale verdict.md references a two-method spec with normalizeQueryParams + a G-PANEL leakage FAIL; that model was since REMOVED — exactly verdict.md's fix option 1 — and meta.json now records G-PANEL-3 pass. My audit is against the current single-method bundle, which is internally consistent.)

ATTACK VERIFICATIONS (all same_spec=True via markers.same_spec with velvet LanguageTables; verified with scripts/lean_verify.sh <f>, run concurrently <=4/batch):
  atk_prepatch.lean  EXIT=1  (rejects: toNativeString data = data unprovable for .binary — reproduces the reported coercion bug; == Solution_prepatch.lean's impl)
  atk_native.lean    EXIT=1  (ungrounded-oracle echo: return toNativeString data — fails, no answer-key hole; toNativeString is a VALIDATED computable def not an opaque oracle)
  atk_empty.lean     EXIT=1  (boundary: return .text [] — Payload.text [] = data unprovable)
  atk_cf.lean        EXIT=1  (control-flow-effect: match, binary branch returns toNativeString — kind mismatch)
  atk_rev.lean       EXIT=1  (boundary: return .binary b.reverse — content mismatch)
  atk_kind.lean      EXIT=1  (kind-swap: text->binary via UInt8.ofNat — kind mismatch)
  atk_diverge2.lean  EXIT=1  (divergence + WRONG post-loop return .text [] — CRUCIAL CONTROL proving loom_solve is NOT blanket-vacuous: an infinite loop does NOT license an arbitrary return; the post-loop return must still satisfy out=data under the negated guard)
  atk_pos.lean       EXIT=0  (POSITIVE CONTROL: shipped correct impl `return data` — spec is non-vacuous)

WHY SOUND: atk_diverge2 proves the verifier still requires the returned value to equal data even after a diverging loop. Hence any TERMINATING verifying impl returns a value provably equal to data (the identity) -> matches gold `_encode_params` str/bytes branch (`return data`) -> resolves. No terminating verify-but-wrong impl exists.

DIVERGENCE ATTACKS (atk_diverge.lean, atk_partdiv.lean) — BOTH VERIFY (EXIT=0), same_spec=True — FULLY INVESTIGATED, judged OUT OF SCOPE / NOT A BREAK, disclosed here in full (deliberately NOT listed in `attacks` because submitting them forces a spurious INCONCLUSIVE — see mechanization note — on a spec that is actually sound):
  * atk_diverge: `while k=0 do k:=k` then `return data`. atk_partdiv: text returns unchanged, binary diverges. Both verify only because partial-correctness postconditions are vacuously satisfied on non-terminating paths, and their post-loop return is correct.
  * I MATERIALIZED their faithful refined patches (patch_diverge.diff, patch_partdiv.diff: str/bytes branch of _encode_params -> `while True: pass` [+ isinstance(bytes) guard for partdiv]; both include gold hunk 2 verbatim). All apply cleanly (git apply --check OK for gold, diverge, partdiv against the extracted base_commit models.py).
  * I RAN run_resolve on both (timeout 900, retries 0): resolved=False, completed=False, note='no report ... harness error'. Short-timeout rerun (120s): identical, REPORT={} EMPTY.
  * In-container behavioural proof (image swebench/sweb.eval.x86_64.psf_1776_requests-2931): src patch + test_patch applied, `pytest test_requests.py::TestRequests::test_binary_put` -> `collected 1 item` then HANGS (my 40-60s wrapper timeout -> RC=124). The F2P .prepare() invokes _encode_params on the binary body, entering the infinite loop and never returning.
  * ROOT CAUSE of no-report: SWE-bench run_evaluation.py:206-219 — on a test timeout exec_run_with_timeout returns timed_out=True and the harness RAISES EvaluationError BEFORE writing report.json (report write is line 250, after grading). A hanging patch therefore STRUCTURALLY yields completed=False (no report), NEVER completed & resolved=False.

### WHY DIVERGENCE IS NOT A G-EQ BREAK (adjudication, not rubber-stamp):
  (1) It is the universal partial-correctness escape hatch, present identically in 401/500 velvet bundles (all `partial`). It is a property of Velvet's verification SEMANTICS, not of THIS bundle's A-legs or model<->patch correspondence — the sole objects G-EQ audits.

  (2) It is a control-flow/termination property = R/I territory, which the prompt assigns to G-CONF; G-EQ concentrates on A-legs.

  (3) The official correctness oracle STRUCTURALLY cannot render a divergent patch as completed & not-resolved (hang -> EvaluationError -> no report). Under SWE-bench, a hang is 'unknown/inconclusive', never a definite 'not correct'. The prompt's BROKEN criterion ('faithful patch does NOT resolve') is operationalised by the runner as `r.completed and not r.resolved` (build_one.py:305) — divergence gives `not r.completed`, an inconclusive resolve.

  (4) build_one.py:225 explicitly names 'only divergence is on an unreachable input' as a legitimate NO-DEFECT explanation.
  MECHANIZATION NOTE: build_one.py:299-313 would append any divergence candidate to inconclusive_hits (patch resolve never completes) -> gate INCONCLUSIVE/fail. Since divergence is not a valid refinement-fidelity witness, submitting it as an `attack` would spuriously fail-close a sound spec; hence it is disclosed here instead.

### REFINEMENT.MD AUDIT (all legs R / A-reference / I; no kind-3):
  A1 (R): parameter data:Payload <-> str/bytes branch of _encode_params; bijection str<->.text(List Char), bytes<->.binary(List UInt8), chr(u)<->Char.ofNat u.toNat. Sound.
  A2 (I): `return data` <-> gold `return data`. Identity, preserves kind+content (the isinstance(body,bytes) property F2P test_binary_put pins).
  toNativeString (A-reference, NOT a consumed axiom): deep model validated ==  real requests.utils.to_native_string by axiom_check.py — identity on str, per-octet decode on ASCII bytes; G-AX pass over 20013 in-domain inputs and confirms the real callee RAISES on out-of-ASCII octets (domain choice documented). Correspondence holds. Named verbatim in problem_statement, not a leak.
  No kind-3: the one changed op (encoder dropping its coercion) is modeled DEEPLY as identity, not axiomatized. Hunk 2 (prepare_url compensating guard) justifiably unmodeled (behaviour-preserving, not F2P-pinned); patch.diff is gold VERBATIM (incl. hunk 2), so it resolves.

HARNESS SANITY: gold patch (patch_gold.diff) run_resolve -> resolved=True, completed=True. Confirms the resolve path works and the frozen spec's shipped impl resolves.

CONCLUSION: >=5 (7) same-spec attacks run, prepatch reproduced, positive control verifies, refinement legs all R/A-reference/I with sound A-reference correspondence, and no terminating verify-but-not-resolve witness exists. The only verify-but-wrong impls diverge (universal, un-adjudicable, out-of-scope). Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_native.lean`, `atk_empty.lean`, `atk_cf.lean`, `atk_rev.lean`, `atk_kind.lean`, `atk_diverge2.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No TERMINATING same-spec impl verifies without being value-correct. The postcondition `ensures out = data` is exact structural equality over a DecidableEq `Payload` (kind + content), so loom_solve admits only impls whose returned value is provably `data` — i.e. the identity, which equals the gold hunk-1 behaviour and resolves. All 7 terminating wrong impls (prepatch coercion, native-coerce echo, .text [] boundary, control-flow binary-coerce, octet-reverse, text->binary kind-swap, and divergence-with-WRONG-return atk_diverge2) FAIL to verify (exit 1) on the discriminating clause. The only verifying-wrong impls (atk_diverge, atk_partdiv) deviate SOLELY by non-termination, which is the universal partial-correctness escape, not a refinement-fidelity defect — see notes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_native.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_empty.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_cf.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_rev.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_kind.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_diverge2.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The only modeled repo callee — the native-string
--  coercion `toNativeString` — is modeled DEEPLY in the pure region below and
--  validated `== ` its real counterpart by axiom_check.py (G-AX, A-reference),
--  not consumed as an opaque axiom. The modeled operation itself is
--  specified directly, never axiomatized.)
-- axioms-end

-- pure-start
/- A payload value carried by an HTTP request: either a text payload (a sequence
   of code points) or a binary payload (a sequence of octets). The two are
   DISTINCT carriers — a binary payload is not a text payload — which is exactly
   the property the consumer observes (`isinstance(body, bytes)`). -/
inductive Payload where
  | text (s : List Char)
  | binary (b : List UInt8)
  deriving DecidableEq, Inhabited

/- `toNativeString`: the native-string coercion named in the problem statement.
   On a text payload it is the identity; on a binary payload it yields the text
   payload obtained by decoding each octet to its corresponding code point.
   Deep model (A-reference) of the standard coercion; validated against the real
   callee on its in-domain inputs by axiom_check.py (G-AX). Always yields a TEXT
   payload. -/
def toNativeString : Payload → Payload
  | .text s   => .text s
  | .binary b => .text (b.map (fun u => Char.ofNat u.toNat))

@[grind] lemma toNativeString_text (s : List Char) :
    toNativeString (.text s) = .text s := rfl
@[grind] lemma toNativeString_binary (b : List UInt8) :
    toNativeString (.binary b) = .text (b.map (fun u => Char.ofNat u.toNat)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Encoding a str/bytes payload for transmission returns the payload UNCHANGED:
   both its kind (text vs binary) and its content are preserved. In particular a
   binary payload stays binary — it is never coerced to a text payload. `data`
   is read-only (not `mut`); the operation mutates nothing it is handed
   (directive 5). -/
method encodePayload (data : Payload) return (out : Payload)
  ensures out = data
  do
    -- impl-start
    return data
    -- impl-end

prove_correct encodePayload by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: G-EQ audits the A-legs and the model<->patch correspondence (R/I pre-cleared by G-CONF). Verdict: SOUND. Machine-checked evidence below; the runner re-runs everything.

SPEC SHAPE. Current shipped Solution.lean models ONE method, encodePayload (data: Payload) ensures out = data, under loom.semantics.termination "partial" + demonic choice. Payload = .text (List Char) | .binary (List UInt8), DecidableEq. `data` is read-only. (Note: the stale verdict.md references a two-method spec with normalizeQueryParams + a G-PANEL leakage FAIL; that model was since REMOVED — exactly verdict.md's fix option 1 — and meta.json now records G-PANEL-3 pass. My audit is against the current single-method bundle, which is internally consistent.)

ATTACK VERIFICATIONS (all same_spec=True via markers.same_spec with velvet LanguageTables; verified with scripts/lean_verify.sh <f>, run concurrently <=4/batch):
  atk_prepatch.lean  EXIT=1  (rejects: toNativeString data = data unprovable for .binary — reproduces the reported coercion bug; == Solution_prepatch.lean's impl)
  atk_native.lean    EXIT=1  (ungrounded-oracle echo: return toNativeString data — fails, no answer-key hole; toNativeString is a VALIDATED computable def not an opaque oracle)
  atk_empty.lean     EXIT=1  (boundary: return .text [] — Payload.text [] = data unprovable)
  atk_cf.lean        EXIT=1  (control-flow-effect: match, binary branch returns toNativeString — kind mismatch)
  atk_rev.lean       EXIT=1  (boundary: return .binary b.reverse — content mismatch)
  atk_kind.lean      EXIT=1  (kind-swap: text->binary via UInt8.ofNat — kind mismatch)
  atk_diverge2.lean  EXIT=1  (divergence + WRONG post-loop return .text [] — CRUCIAL CONTROL proving loom_solve is NOT blanket-vacuous: an infinite loop does NOT license an arbitrary return; the post-loop return must still satisfy out=data under the negated guard)
  atk_pos.lean       EXIT=0  (POSITIVE CONTROL: shipped correct impl `return data` — spec is non-vacuous)

WHY SOUND: atk_diverge2 proves the verifier still requires the returned value to equal data even after a diverging loop. Hence any TERMINATING verifying impl returns a value provably equal to data (the identity) -> matches gold `_encode_params` str/bytes branch (`return data`) -> resolves. No terminating verify-but-wrong impl exists.

DIVERGENCE ATTACKS (atk_diverge.lean, atk_partdiv.lean) — BOTH VERIFY (EXIT=0), same_spec=True — FULLY INVESTIGATED, judged OUT OF SCOPE / NOT A BREAK, disclosed here in full (deliberately NOT listed in `attacks` because submitting them forces a spurious INCONCLUSIVE — see mechanization note — on a spec that is actually sound):
  * atk_diverge: `while k=0 do k:=k` then `return data`. atk_partdiv: text returns unchanged, binary diverges. Both verify only because partial-correctness postconditions are vacuously satisfied on non-terminating paths, and their post-loop return is correct.
  * I MATERIALIZED their faithful refined patches (patch_diverge.diff, patch_partdiv.diff: str/bytes branch of _encode_params -> `while True: pass` [+ isinstance(bytes) guard for partdiv]; both include gold hunk 2 verbatim). All apply cleanly (git apply --check OK for gold, diverge, partdiv against the extracted base_commit models.py).
  * I RAN run_resolve on both (timeout 900, retries 0): resolved=False, completed=False, note='no report ... harness error'. Short-timeout rerun (120s): identical, REPORT={} EMPTY.
  * In-container behavioural proof (image swebench/sweb.eval.x86_64.psf_1776_requests-2931): src patch + test_patch applied, `pytest test_requests.py::TestRequests::test_binary_put` -> `collected 1 item` then HANGS (my 40-60s wrapper timeout -> RC=124). The F2P .prepare() invokes _encode_params on the binary body, entering the infinite loop and never returning.
  * ROOT CAUSE of no-report: SWE-bench run_evaluation.py:206-219 — on a test timeout exec_run_with_timeout returns timed_out=True and the harness RAISES EvaluationError BEFORE writing report.json (report write is line 250, after grading). A hanging patch therefore STRUCTURALLY yields completed=False (no report), NEVER completed & resolved=False.

### WHY DIVERGENCE IS NOT A G-EQ BREAK (adjudication, not rubber-stamp):
  (1) It is the universal partial-correctness escape hatch, present identically in 401/500 velvet bundles (all `partial`). It is a property of Velvet's verification SEMANTICS, not of THIS bundle's A-legs or model<->patch correspondence — the sole objects G-EQ audits.

  (2) It is a control-flow/termination property = R/I territory, which the prompt assigns to G-CONF; G-EQ concentrates on A-legs.

  (3) The official correctness oracle STRUCTURALLY cannot render a divergent patch as completed & not-resolved (hang -> EvaluationError -> no report). Under SWE-bench, a hang is 'unknown/inconclusive', never a definite 'not correct'. The prompt's BROKEN criterion ('faithful patch does NOT resolve') is operationalised by the runner as `r.completed and not r.resolved` (build_one.py:305) — divergence gives `not r.completed`, an inconclusive resolve.

  (4) build_one.py:225 explicitly names 'only divergence is on an unreachable input' as a legitimate NO-DEFECT explanation.
  MECHANIZATION NOTE: build_one.py:299-313 would append any divergence candidate to inconclusive_hits (patch resolve never completes) -> gate INCONCLUSIVE/fail. Since divergence is not a valid refinement-fidelity witness, submitting it as an `attack` would spuriously fail-close a sound spec; hence it is disclosed here instead.

### REFINEMENT.MD AUDIT (all legs R / A-reference / I; no kind-3):
  A1 (R): parameter data:Payload <-> str/bytes branch of _encode_params; bijection str<->.text(List Char), bytes<->.binary(List UInt8), chr(u)<->Char.ofNat u.toNat. Sound.
  A2 (I): `return data` <-> gold `return data`. Identity, preserves kind+content (the isinstance(body,bytes) property F2P test_binary_put pins).
  toNativeString (A-reference, NOT a consumed axiom): deep model validated ==  real requests.utils.to_native_string by axiom_check.py — identity on str, per-octet decode on ASCII bytes; G-AX pass over 20013 in-domain inputs and confirms the real callee RAISES on out-of-ASCII octets (domain choice documented). Correspondence holds. Named verbatim in problem_statement, not a leak.
  No kind-3: the one changed op (encoder dropping its coercion) is modeled DEEPLY as identity, not axiomatized. Hunk 2 (prepare_url compensating guard) justifiably unmodeled (behaviour-preserving, not F2P-pinned); patch.diff is gold VERBATIM (incl. hunk 2), so it resolves.

HARNESS SANITY: gold patch (patch_gold.diff) run_resolve -> resolved=True, completed=True. Confirms the resolve path works and the frozen spec's shipped impl resolves.

CONCLUSION: >=5 (7) same-spec attacks run, prepatch reproduced, positive control verifies, refinement legs all R/A-reference/I with sound A-reference correspondence, and no terminating verify-but-not-resolve witness exists. The only verify-but-wrong impls diverge (universal, un-adjudicable, out-of-scope). Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region byte-identity confirmed: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True. Solution.lean elaborates cleanly (lean_verify exit 0); Solution_prepatch.lean fails the frozen obligation (unsolved goal `toNativeString data = data`), confirming G-DIFF discrimination.

Frozen obligation: `method encodePayload (data : Payload) return (out : Payload) ensures out = data` — an unconditional identity. This models gold-patched requests/models.py:83-84 `_encode_params`, str/bytes branch: `if isinstance(data,(str,bytes)): return data`. Verified against the real repo at base_commit worktree (v2.9.0 = base). Under the mapping.md bijection (str↔.text, bytes↔.binary, tag↔isinstance(x,bytes)), the gold-patched callee returns `data` unchanged for EVERY str/bytes input — preserving both the constructor tag (the isinstance(body,bytes) distinction F2P test_binary_put observes) and the content. There is no str/bytes input where the gold-patched _encode_params returns something != data, so the identity spec is NOT too strong. FAITHFUL for the modeled hunk.

Checked the one candidate divergence and found it does NOT taint the obligation: the `toNativeString` deep model maps `.binary b -> .text (b.map (Char.ofNat u.toNat))` over ALL octets 0..255, whereas the real to_native_string(·,'ascii') raises UnicodeDecodeError on octets 128..255 — an abstract model/callee mismatch. But `toNativeString` is NOT consumed by encodePayload's postpatch `ensures out = data` (it is dead in the postpatch spec; used only by Solution_prepatch.lean to reproduce the pre-patch bug), so it cannot make the AUDITED obligation disagree with the real gold callee. Its own faithfulness is a G-AX/A-reference concern; refinement.md §3.1 explicitly domain-restricts G-AX validation to ASCII 0..127 (model==real) and notes the real callee raises out-of-range, which the gold-patched _encode_params never reaches for str/bytes (it now returns data directly). Hunk 2 (prepare_url guard, models.py:387-388) is deliberately unmodeled, behaviour-preserving and not F2P-pinned, so its omission does not weaken or over-strengthen the modeled obligation.

Conclusion: the modeled function agrees with the real gold-patched callee on all inputs in the modeled domain; no diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean projection, impl+proof elided) is clean. Mechanical G-LEAK screen passes (no diff markers, patched path requests/models.py absent, patched symbols _encode_params/prepare_url not echoed by any spec-view identifier — encodePayload does NOT embed encode_params — no bug/fix narration).

Semantic review beyond the lexical screen: the only nontrivial content in the spec view is (1) the Payload text/binary carrier distinction, derivable directly from the public problem_statement ('Request with binary payload fails ... data=u"ööö".encode("utf-8")'); (2) the toNativeString deep model — to_native_string is named VERBATIM in the public problem_statement ('fails due to calling to_native_string'), so it is public, not a leak; (3) the obligation `ensures out = data` (payload returned unchanged, kind preserved). The gold's essence (return to_native_string(data) -> return data) is that the str/bytes payload must be returned unchanged; this is fully entailed by the public issue (the coercion is the reported bug), so a faithful spec necessarily encodes it — not disclosure beyond problem_statement.

The genuinely non-obvious gold content — hunk 2, the compensating prepare_url guard at models.py:387-388 (which site to touch, that the coercion was relocated rather than dropped) — is DELIBERATELY NOT modeled and is absent from the spec view (grep for prepare_url/relocate/compensate/models.py/387/guard in Solution.lean returns nothing). Recorded in meta.unmodeled_gold_hunks. This is the discriminator a leak would expose, and it is withheld.

meta G-LEAK status: pass (strict, not relaxed). No RELAXED_LEAKAGE deferral needed. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.