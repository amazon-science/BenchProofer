# P2 adversarial audit — psf__requests-2931

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,10 +27,14 @@
   result = data
 -- post-conditions-end
 
+
 -- impl-start
+def toNativeString : Datum → Datum
+  | .text s   => .text s
+  | .binary b => .text (b.map (fun byte => Char.ofNat byte.toNat))
+
 def implementation_encodeParams (data : Datum) : Datum := Id.run do
-  -- A text or binary payload is handed back as-is.
-  return data
+  return toNativeString data
 -- impl-end
 
 -- proof-start
@@ -38,5 +42,5 @@
     ∀ (data : Datum),
       problem_spec_encodeParams data (implementation_encodeParams data) := by
   intro data
-  rfl
+  cases data <;> simp [problem_spec_encodeParams, implementation_encodeParams, toNativeString, Id.run]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,10 +27,10 @@
   result = data
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_encodeParams (data : Datum) : Datum := Id.run do
-  -- A text or binary payload is handed back as-is.
-  return data
+  return Datum.text []
 -- impl-end
 
 -- proof-start
@@ -38,5 +38,5 @@
     ∀ (data : Datum),
       problem_spec_encodeParams data (implementation_encodeParams data) := by
   intro data
-  rfl
+  cases data <;> simp [problem_spec_encodeParams, implementation_encodeParams, Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,10 +27,12 @@
   result = data
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_encodeParams (data : Datum) : Datum := Id.run do
-  -- A text or binary payload is handed back as-is.
-  return data
+  match data with
+  | .text s   => return .text s
+  | .binary _ => return .text []
 -- impl-end
 
 -- proof-start
@@ -38,5 +40,5 @@
     ∀ (data : Datum),
       problem_spec_encodeParams data (implementation_encodeParams data) := by
   intro data
-  rfl
+  cases data <;> simp [problem_spec_encodeParams, implementation_encodeParams, Id.run]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,10 +27,12 @@
   result = data
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_encodeParams (data : Datum) : Datum := Id.run do
-  -- A text or binary payload is handed back as-is.
-  return data
+  match data with
+  | .text s   => return .text s.reverse
+  | .binary b => return .binary b
 -- impl-end
 
 -- proof-start
@@ -38,5 +40,5 @@
     ∀ (data : Datum),
       problem_spec_encodeParams data (implementation_encodeParams data) := by
   intro data
-  rfl
+  cases data <;> simp [problem_spec_encodeParams, implementation_encodeParams, Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,10 +27,12 @@
   result = data
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_encodeParams (data : Datum) : Datum := Id.run do
-  -- A text or binary payload is handed back as-is.
-  return data
+  let mut r := data
+  r := data
+  return r
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,10 +27,12 @@
   result = data
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_encodeParams (data : Datum) : Datum := Id.run do
-  -- A text or binary payload is handed back as-is.
-  return data
+  match data with
+  | .text s   => return .text s
+  | .binary b => return .binary b
 -- impl-end
 
 -- proof-start
@@ -38,5 +40,5 @@
     ∀ (data : Datum),
       problem_spec_encodeParams data (implementation_encodeParams data) := by
   intro data
-  rfl
+  cases data <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,10 +27,12 @@
   result = data
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_encodeParams (data : Datum) : Datum := Id.run do
-  -- A text or binary payload is handed back as-is.
-  return data
+  match data with
+  | .text _   => return .binary []
+  | .binary b => return .binary b
 -- impl-end
 
 -- proof-start
@@ -38,5 +40,5 @@
     ∀ (data : Datum),
       problem_spec_encodeParams data (implementation_encodeParams data) := by
   intro data
-  rfl
+  cases data <;> simp [problem_spec_encodeParams, implementation_encodeParams, Id.run]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The behavior under spec is
-- a pass-through of a textual-or-binary payload; the modeled branch performs no
-- call. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A request payload that is either a text value (a sequence of characters) or a
binary value (a sequence of bytes). Only these two shapes of the payload domain
are modeled; the constructor records which of the two a value is. -/
inductive Datum where
  | text  (s : List Char)
  | binary (b : List UInt8)
  deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Encoding a payload that is already a text or binary value returns that value
unchanged: both its kind (text vs binary) and its contents are preserved. The
result is pinned to be exactly the input, so an implementation that converts a
binary value into a text value — or alters its contents — cannot satisfy this
predicate. -/
def problem_spec_encodeParams (data : Datum) (result : Datum) : Prop :=
  result = data
-- post-conditions-end


-- impl-start
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  -- A text or binary payload is handed back as-is.
  return data
-- impl-end

-- proof-start
theorem correct_encodeParams :
    ∀ (data : Datum),
      problem_spec_encodeParams data (implementation_encodeParams data) := by
  intro data
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_encodeParams data result := (result = data). This is a TOTAL, EXACT-IDENTITY functional postcondition over Datum (text|binary). It provably forces any closing impl to be extensionally the identity on all of Datum, so verify => extensionally-correct. Adversarial attempt to exhibit a same-spec wrong impl that still closes: FAILED (spec is maximally tight).

SAME_SPEC: all 7 attacks + positive_control are same_spec=True vs Solution.lean (spec regions imports/axioms/pure/post byte-identical; only impl+proof edited). Verified via swebench_unified.markers.same_spec + get_backend('lean').

### VERIFY RESULTS (scripts/lean_verify.sh <f>; exit0=verifies/no-sorry, 1=error, 3=sorry):
- atk_1 prepatch bug (toNativeString: binary->text coercion) => exit 1 (unsolved goals; binary case reduces to `⊢ False`). PREPATCH BUG REPRODUCED (the removed to_native_string coercion cannot satisfy result=data on a binary payload — exactly the F2P test_binary_put failure).
- atk_2 ungrounded-oracle constant .text [] => exit 1.
- atk_3 partial-domain (identity on text, binary->.text []) => exit 1.
- atk_4 content-alteration (reverse text contents) => exit 1.
- atk_7 kind-swap (text->.binary []) => exit 1.
  => All 5 genuinely-wrong impls are REJECTED by the spec. No wrong impl closes.
- atk_5 control-flow-effect echo (mutable var r:=data; return r) => exit 0.
- atk_6 reconstruction echo (match, rebuild each constructor identically) => exit 0.
- pos_control gold `return data` => exit 0.

AXIOMS (#print axioms correct_encodeParams) for EVERY closing proof (atk_5, atk_6, pos_control, and shipped Solution.lean): 'correct_encodeParams' does not depend on any axioms. CLEAN — no propext/Classical/Quot/sorryAx.

ECHO-ATTACK PROTOCOL (plan §4): the only two verifying candidates (atk_5, atk_6) are EXTENSIONALLY `return data` on the str/bytes branch = gold behavior. Their faithful refined patch is therefore the gold patch (materialized at faithful_patch.diff; verified byte-identical to instance.json gold patch). Ran through the official harness: SBU_BENCHMARK=swe_bench_verified; swebench_unified.harness.run_resolve('psf__requests-2931', patch, timeout=1800) => RESOLVED=True (real Docker G-RESOLVE, report.json resolved=true). Both echoes RESOLVE => they are NOT weaknesses (per resolved 2026-08-06 G-PANEL-1/eq echo policy: a same-spec verifying attack fails the gate only if its refined patch does NOT resolve). Neither breaks the spec.

REFINEMENT.MD AUDIT: 1 leg total, tagged I (return data == str/bytes branch return data; Datum is the R-refinement of str/bytes; op is concrete identity on the carrier). ZERO A-consumed / A-reference legs — the modeled post-patch branch calls no unchanged callee; axioms region is empty (confirmed clean by #print axioms). No kind-3 (changed-but-inexpressible): the sole changed op (return the str/bytes payload unchanged) is fully expressible as the identity on Datum; inexpressibility check sound. Hunk 2 (prepare_url compensating coercion) is out of the modeled F2P scope and correctly documented as such in mapping.md (it re-establishes at the URL-params call site the coercion hunk 1 removed from the body path; F2P test_binary_put pins only hunk 1). G-AX skip stub is justified (no consumed callee axioms). A-leg correspondence: N/A (no A-legs).

VERDICT: SOUND. Ran 7 same-spec attacks (>=5 distinct wrong-impl classes: prepatch-bug, ungrounded-oracle constant, partial-domain, content-alteration, kind-swap) + 2 echoes + positive control. Every genuinely-wrong impl FAILS to verify; the only verifying candidates are extensional identities whose materialized faithful (=gold) patch RESOLVES (executed, RESOLVED=True). No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The behavior under spec is
-- a pass-through of a textual-or-binary payload; the modeled branch performs no
-- call. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A request payload that is either a text value (a sequence of characters) or a
binary value (a sequence of bytes). Only these two shapes of the payload domain
are modeled; the constructor records which of the two a value is. -/
inductive Datum where
  | text  (s : List Char)
  | binary (b : List UInt8)
  deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Encoding a payload that is already a text or binary value returns that value
unchanged: both its kind (text vs binary) and its contents are preserved. The
result is pinned to be exactly the input, so an implementation that converts a
binary value into a text value — or alters its contents — cannot satisfy this
predicate. -/
def problem_spec_encodeParams (data : Datum) (result : Datum) : Prop :=
  result = data
-- post-conditions-end


-- impl-start
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  -- A text or binary payload is handed back as-is.
  return data
-- impl-end

-- proof-start
theorem correct_encodeParams :
    ∀ (data : Datum),
      problem_spec_encodeParams data (implementation_encodeParams data) := by
  intro data
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_encodeParams data result := (result = data). This is a TOTAL, EXACT-IDENTITY functional postcondition over Datum (text|binary). It provably forces any closing impl to be extensionally the identity on all of Datum, so verify => extensionally-correct. Adversarial attempt to exhibit a same-spec wrong impl that still closes: FAILED (spec is maximally tight).

SAME_SPEC: all 7 attacks + positive_control are same_spec=True vs Solution.lean (spec regions imports/axioms/pure/post byte-identical; only impl+proof edited). Verified via swebench_unified.markers.same_spec + get_backend('lean').

### VERIFY RESULTS (scripts/lean_verify.sh <f>; exit0=verifies/no-sorry, 1=error, 3=sorry):
- atk_1 prepatch bug (toNativeString: binary->text coercion) => exit 1 (unsolved goals; binary case reduces to `⊢ False`). PREPATCH BUG REPRODUCED (the removed to_native_string coercion cannot satisfy result=data on a binary payload — exactly the F2P test_binary_put failure).
- atk_2 ungrounded-oracle constant .text [] => exit 1.
- atk_3 partial-domain (identity on text, binary->.text []) => exit 1.
- atk_4 content-alteration (reverse text contents) => exit 1.
- atk_7 kind-swap (text->.binary []) => exit 1.
  => All 5 genuinely-wrong impls are REJECTED by the spec. No wrong impl closes.
- atk_5 control-flow-effect echo (mutable var r:=data; return r) => exit 0.
- atk_6 reconstruction echo (match, rebuild each constructor identically) => exit 0.
- pos_control gold `return data` => exit 0.

AXIOMS (#print axioms correct_encodeParams) for EVERY closing proof (atk_5, atk_6, pos_control, and shipped Solution.lean): 'correct_encodeParams' does not depend on any axioms. CLEAN — no propext/Classical/Quot/sorryAx.

ECHO-ATTACK PROTOCOL (plan §4): the only two verifying candidates (atk_5, atk_6) are EXTENSIONALLY `return data` on the str/bytes branch = gold behavior. Their faithful refined patch is therefore the gold patch (materialized at faithful_patch.diff; verified byte-identical to instance.json gold patch). Ran through the official harness: SBU_BENCHMARK=swe_bench_verified; swebench_unified.harness.run_resolve('psf__requests-2931', patch, timeout=1800) => RESOLVED=True (real Docker G-RESOLVE, report.json resolved=true). Both echoes RESOLVE => they are NOT weaknesses (per resolved 2026-08-06 G-PANEL-1/eq echo policy: a same-spec verifying attack fails the gate only if its refined patch does NOT resolve). Neither breaks the spec.

REFINEMENT.MD AUDIT: 1 leg total, tagged I (return data == str/bytes branch return data; Datum is the R-refinement of str/bytes; op is concrete identity on the carrier). ZERO A-consumed / A-reference legs — the modeled post-patch branch calls no unchanged callee; axioms region is empty (confirmed clean by #print axioms). No kind-3 (changed-but-inexpressible): the sole changed op (return the str/bytes payload unchanged) is fully expressible as the identity on Datum; inexpressibility check sound. Hunk 2 (prepare_url compensating coercion) is out of the modeled F2P scope and correctly documented as such in mapping.md (it re-establishes at the URL-params call site the coercion hunk 1 removed from the body path; F2P test_binary_put pins only hunk 1). G-AX skip stub is justified (no consumed callee axioms). A-leg correspondence: N/A (no A-legs).

VERDICT: SOUND. Ran 7 same-spec attacks (>=5 distinct wrong-impl classes: prepatch-bug, ungrounded-oracle constant, partial-domain, content-alteration, kind-swap) + 2 echoes + positive control. Every genuinely-wrong impl FAILS to verify; the only verifying candidates are extensional identities whose materialized faithful (=gold) patch RESOLVES (executed, RESOLVED=True). No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (drift) check: does the modeled function disagree with the real post-patch callee on any input? No.

Setup verified:
- same_spec(Solution.lean, Solution_prepatch.lean) = True: the spec region (Datum inductive + problem_spec_encodeParams `result = data`) is byte-identical between patched and prepatch; the bug lives only in the impl, as it should.
- Solution.lean compiles via lean_verify.sh (exit 0, no sorry) and `#print axioms correct_encodeParams` => 'does not depend on any axioms' (genuine rfl proof, no sorryAx, no _prop axioms). axioms region is legitimately empty (post-patch branch calls nothing).

Model vs real callee:
- Modeled function implementation_encodeParams = identity on Datum (`return data`).
- Real callee = post-patch str/bytes branch of requests.models.RequestEncodingMixin._encode_params: `if isinstance(data, (str, bytes)): return data` (confirmed against worktree requests/models.py @5f7a3a7; base still shows the pre-patch `to_native_string(data)`, patch.diff changes it to `return data`). This is literal identity: str stays str, bytes stays bytes, no coercion.
- Type bijection (mapping.md): Datum.text (List Char) <-> str, Datum.binary (List UInt8) <-> bytes. Every Datum value lies in the str/bytes branch (the exact patched domain), so the spec does NOT over-reach into the unmodeled file-like/iterable/else branches; that domain restriction is legitimate scope, not drift.

Spec-too-strong search: the spec pins result = data (kind + content preserved). The real callee `return data` also preserves kind and content exactly. Checked boundary + representative inputs (text '', binary b'', 'foo'/b'foo', non-ASCII text 'ööö', the F2P non-ASCII bytes 'ööö'.encode(), bytes([0,127,128,255])) and the conformance fuzz domain: ZERO disagreements. No input exists where the identity model diverges from `return data`. The spec is neither too strong (the branch really is exact identity, not a weaker coercion) nor drifted.

Verdict: FAITHFUL — modeled function agrees with the real callee on all inputs over the modeled domain; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view projection of Solution.lean was generated with markers.spec_view and screened with leakage.screen against the frozen problem_statement (hints_text empty). Mechanical screen PASSES (no failures). Semantic gold-reconstruction judgment: the spec view exposes only (a) the `Datum` inductive (text/binary) — an abstracted model of Python str/bytes; (b) postcondition `problem_spec_encodeParams data result := result = data` pinning identity/pass-through; impl and proof both elided. None of this discloses the gold edit beyond the public task. The public problem_statement already states that a binary payload (u"ööö".encode('utf-8')) fails due to `to_native_string` coercion and that it worked in 2.8.1 — i.e. the intended fix (binary body must pass through unchanged) is already implied publicly. The spec view contains NO diff markers, NO reproduced gold-patch lines (`return data`, `to_native_string`), NO patched file/module path (requests/models.py), and NO spec-view identifier or comment naming the patched repo symbols (`to_native_string`, `_encode_params`, `prepare_url`); Lean names are abstracted (encodeParams/Datum). No bug/fix narration in comments. The identity postcondition is the legitimate abstracted formalization of the behavior the public task demands, not a leak. same_spec(Solution.lean, Solution_prepatch.lean)=True confirms the spec is stable across the edit. Symbol/path disclosures in mapping.md and refinement.md are construction artifacts outside the screened consumer spec view. Conclusion: no spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
