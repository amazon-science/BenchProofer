# P2 adversarial audit — psf__requests-1142

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,17 +48,10 @@
 def implementation_prepare_content_length
     (method : String) (pre : Option String) (body : Option Nat) :
     Option String := Id.run do
-  -- the header slot starts at its pre-call value; only writes change it
   let mut clen : Option String := pre
   match body with
-  | some n =>
-      -- a body is present: its content length is reported
-      clen := some (toString n)
-  | none =>
-      -- no body: only methods that may carry a payload write a zero length;
-      -- for GET/HEAD nothing is written and the slot retains `pre`
-      if method ≠ "GET" ∧ method ≠ "HEAD" then
-        clen := some "0"
+  | some n => clen := some (toString n)
+  | none => clen := some "0"
   return clen
 -- impl-end
 
@@ -70,18 +63,10 @@
   intro method pre body
   unfold problem_spec_prepare_content_length implementation_prepare_content_length
   cases body with
-  | some n => rfl
+  | some n => first | rfl | (simp_all) | decide
   | none =>
       simp only [Id.run]
       by_cases h : method = "GET" ∨ method = "HEAD"
-      · rw [if_pos h]
-        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
-          rcases h with h | h <;> simp [h]
-        simp only [if_neg h']
-        rfl
-      · rw [if_neg h]
-        push_neg at h
-        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
-        simp only [if_pos h']
-        rfl
+      · rw [if_pos h] <;> first | rfl | simp_all | (try simp [h]) | decide
+      · rw [if_neg h] <;> first | rfl | simp_all | (try push_neg at h) | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,16 +48,11 @@
 def implementation_prepare_content_length
     (method : String) (pre : Option String) (body : Option Nat) :
     Option String := Id.run do
-  -- the header slot starts at its pre-call value; only writes change it
   let mut clen : Option String := pre
   match body with
-  | some n =>
-      -- a body is present: its content length is reported
-      clen := some (toString n)
+  | some n => clen := some (toString n)
   | none =>
-      -- no body: only methods that may carry a payload write a zero length;
-      -- for GET/HEAD nothing is written and the slot retains `pre`
-      if method ≠ "GET" ∧ method ≠ "HEAD" then
+      if method ≠ "GET" then
         clen := some "0"
   return clen
 -- impl-end
@@ -70,18 +65,10 @@
   intro method pre body
   unfold problem_spec_prepare_content_length implementation_prepare_content_length
   cases body with
-  | some n => rfl
+  | some n => first | rfl | (simp_all) | decide
   | none =>
       simp only [Id.run]
       by_cases h : method = "GET" ∨ method = "HEAD"
-      · rw [if_pos h]
-        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
-          rcases h with h | h <;> simp [h]
-        simp only [if_neg h']
-        rfl
-      · rw [if_neg h]
-        push_neg at h
-        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
-        simp only [if_pos h']
-        rfl
+      · rw [if_pos h] <;> first | rfl | simp_all | (try simp [h]) | decide
+      · rw [if_neg h] <;> first | rfl | simp_all | (try push_neg at h) | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,15 +48,10 @@
 def implementation_prepare_content_length
     (method : String) (pre : Option String) (body : Option Nat) :
     Option String := Id.run do
-  -- the header slot starts at its pre-call value; only writes change it
   let mut clen : Option String := pre
   match body with
-  | some n =>
-      -- a body is present: its content length is reported
-      clen := some (toString n)
+  | some n => clen := some (toString (n + 1))
   | none =>
-      -- no body: only methods that may carry a payload write a zero length;
-      -- for GET/HEAD nothing is written and the slot retains `pre`
       if method ≠ "GET" ∧ method ≠ "HEAD" then
         clen := some "0"
   return clen
@@ -70,18 +65,10 @@
   intro method pre body
   unfold problem_spec_prepare_content_length implementation_prepare_content_length
   cases body with
-  | some n => rfl
+  | some n => first | rfl | (simp_all) | decide
   | none =>
       simp only [Id.run]
       by_cases h : method = "GET" ∨ method = "HEAD"
-      · rw [if_pos h]
-        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
-          rcases h with h | h <;> simp [h]
-        simp only [if_neg h']
-        rfl
-      · rw [if_neg h]
-        push_neg at h
-        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
-        simp only [if_pos h']
-        rfl
+      · rw [if_pos h] <;> first | rfl | simp_all | (try simp [h]) | decide
+      · rw [if_neg h] <;> first | rfl | simp_all | (try push_neg at h) | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,17 +48,7 @@
 def implementation_prepare_content_length
     (method : String) (pre : Option String) (body : Option Nat) :
     Option String := Id.run do
-  -- the header slot starts at its pre-call value; only writes change it
-  let mut clen : Option String := pre
-  match body with
-  | some n =>
-      -- a body is present: its content length is reported
-      clen := some (toString n)
-  | none =>
-      -- no body: only methods that may carry a payload write a zero length;
-      -- for GET/HEAD nothing is written and the slot retains `pre`
-      if method ≠ "GET" ∧ method ≠ "HEAD" then
-        clen := some "0"
+  let clen : Option String := pre
   return clen
 -- impl-end
 
@@ -70,18 +60,10 @@
   intro method pre body
   unfold problem_spec_prepare_content_length implementation_prepare_content_length
   cases body with
-  | some n => rfl
+  | some n => first | rfl | (simp_all) | decide
   | none =>
       simp only [Id.run]
       by_cases h : method = "GET" ∨ method = "HEAD"
-      · rw [if_pos h]
-        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
-          rcases h with h | h <;> simp [h]
-        simp only [if_neg h']
-        rfl
-      · rw [if_neg h]
-        push_neg at h
-        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
-        simp only [if_pos h']
-        rfl
+      · rw [if_pos h] <;> first | rfl | simp_all | (try simp [h]) | decide
+      · rw [if_neg h] <;> first | rfl | simp_all | (try push_neg at h) | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,16 +48,11 @@
 def implementation_prepare_content_length
     (method : String) (pre : Option String) (body : Option Nat) :
     Option String := Id.run do
-  -- the header slot starts at its pre-call value; only writes change it
   let mut clen : Option String := pre
   match body with
-  | some n =>
-      -- a body is present: its content length is reported
-      clen := some (toString n)
+  | some n => clen := some (toString n)
   | none =>
-      -- no body: only methods that may carry a payload write a zero length;
-      -- for GET/HEAD nothing is written and the slot retains `pre`
-      if method ≠ "GET" ∧ method ≠ "HEAD" then
+      if method = "GET" ∨ method = "HEAD" then
         clen := some "0"
   return clen
 -- impl-end
@@ -70,18 +65,10 @@
   intro method pre body
   unfold problem_spec_prepare_content_length implementation_prepare_content_length
   cases body with
-  | some n => rfl
+  | some n => first | rfl | (simp_all) | decide
   | none =>
       simp only [Id.run]
       by_cases h : method = "GET" ∨ method = "HEAD"
-      · rw [if_pos h]
-        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
-          rcases h with h | h <;> simp [h]
-        simp only [if_neg h']
-        rfl
-      · rw [if_neg h]
-        push_neg at h
-        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
-        simp only [if_pos h']
-        rfl
+      · rw [if_pos h] <;> first | rfl | simp_all | (try simp [h]) | decide
+      · rw [if_neg h] <;> first | rfl | simp_all | (try push_neg at h) | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,18 +48,10 @@
 def implementation_prepare_content_length
     (method : String) (pre : Option String) (body : Option Nat) :
     Option String := Id.run do
-  -- the header slot starts at its pre-call value; only writes change it
-  let mut clen : Option String := pre
+  let clen : Option String := pre
   match body with
-  | some n =>
-      -- a body is present: its content length is reported
-      clen := some (toString n)
-  | none =>
-      -- no body: only methods that may carry a payload write a zero length;
-      -- for GET/HEAD nothing is written and the slot retains `pre`
-      if method ≠ "GET" ∧ method ≠ "HEAD" then
-        clen := some "0"
-  return clen
+  | some n => return some (toString n)
+  | none => return clen
 -- impl-end
 
 -- proof-start
@@ -70,18 +62,10 @@
   intro method pre body
   unfold problem_spec_prepare_content_length implementation_prepare_content_length
   cases body with
-  | some n => rfl
+  | some n => first | rfl | (simp_all) | decide
   | none =>
       simp only [Id.run]
       by_cases h : method = "GET" ∨ method = "HEAD"
-      · rw [if_pos h]
-        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
-          rcases h with h | h <;> simp [h]
-        simp only [if_neg h']
-        rfl
-      · rw [if_neg h]
-        push_neg at h
-        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
-        simp only [if_pos h']
-        rfl
+      · rw [if_pos h] <;> first | rfl | simp_all | (try simp [h]) | decide
+      · rw [if_neg h] <;> first | rfl | simp_all | (try push_neg at h) | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,15 +48,14 @@
 def implementation_prepare_content_length
     (method : String) (pre : Option String) (body : Option Nat) :
     Option String := Id.run do
-  -- the header slot starts at its pre-call value; only writes change it
   let mut clen : Option String := pre
   match body with
   | some n =>
-      -- a body is present: its content length is reported
-      clen := some (toString n)
+      if n = 0 then
+        pure ()
+      else
+        clen := some (toString n)
   | none =>
-      -- no body: only methods that may carry a payload write a zero length;
-      -- for GET/HEAD nothing is written and the slot retains `pre`
       if method ≠ "GET" ∧ method ≠ "HEAD" then
         clen := some "0"
   return clen
@@ -70,18 +69,10 @@
   intro method pre body
   unfold problem_spec_prepare_content_length implementation_prepare_content_length
   cases body with
-  | some n => rfl
+  | some n => first | rfl | simp_all | decide
   | none =>
       simp only [Id.run]
       by_cases h : method = "GET" ∨ method = "HEAD"
-      · rw [if_pos h]
-        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
-          rcases h with h | h <;> simp [h]
-        simp only [if_neg h']
-        rfl
-      · rw [if_neg h]
-        push_neg at h
-        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
-        simp only [if_pos h']
-        rfl
+      · rw [if_pos h] <;> first | rfl | simp_all | (try simp [h]) | decide
+      · rw [if_neg h] <;> first | rfl | simp_all | (try push_neg at h) | decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior. The body-length
-- computation (whether obtained by querying a seekable stream or by measuring a
-- value) is abstracted to the length itself (a `Nat`) — a type refinement, not a
-- callee — so there is no `opaque` callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is a small,
-- finite case analysis on the body and the request method.
-- pure-end

-- post-conditions-start
/-- Determination of the message-length header for a prepared HTTP request.

Inputs:
* `method` — the (normalized, upper-case) HTTP request method.
* `pre`    — the value held by the message-length header slot *before* the
  call (`none` when the header is absent, e.g. the caller supplied no such
  header).
* `body`   — `some n` when a request body carrying `n` units of content is
  present; `none` when there is no request body.

`result : Option String` is the value held by the message-length header slot
*after* the call, with `none` meaning the header is absent.

Required behavior:
* If a body is present, the header is its content length, rendered in decimal.
* If there is no body, the header is the literal `"0"` for methods that may
  carry a payload; for the `"GET"` and `"HEAD"` methods (which must not
  advertise a zero-length body) the slot is **not written** — it keeps its
  prior value `pre` (in particular the header stays absent when it was
  absent before the call). -/
def problem_spec_prepare_content_length
    (method : String) (pre : Option String) (body : Option Nat)
    (result : Option String) : Prop :=
  match body with
  | some n => result = some (toString n)
  | none   =>
      if method = "GET" ∨ method = "HEAD" then result = pre
      else result = some "0"
-- post-conditions-end

-- impl-start
def implementation_prepare_content_length
    (method : String) (pre : Option String) (body : Option Nat) :
    Option String := Id.run do
  -- the header slot starts at its pre-call value; only writes change it
  let mut clen : Option String := pre
  match body with
  | some n =>
      -- a body is present: its content length is reported
      clen := some (toString n)
  | none =>
      -- no body: only methods that may carry a payload write a zero length;
      -- for GET/HEAD nothing is written and the slot retains `pre`
      if method ≠ "GET" ∧ method ≠ "HEAD" then
        clen := some "0"
  return clen
-- impl-end

-- proof-start
theorem correct_prepare_content_length :
    ∀ (method : String) (pre : Option String) (body : Option Nat),
      problem_spec_prepare_content_length method pre body
        (implementation_prepare_content_length method pre body) := by
  intro method pre body
  unfold problem_spec_prepare_content_length implementation_prepare_content_length
  cases body with
  | some n => rfl
  | none =>
      simp only [Id.run]
      by_cases h : method = "GET" ∨ method = "HEAD"
      · rw [if_pos h]
        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
          rcases h with h | h <;> simp [h]
        simp only [if_neg h']
        rfl
      · rw [if_neg h]
        push_neg at h
        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
        simp only [if_pos h']
        rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_prepare_content_length is a TOTAL, POINTWISE-EXACT function of (method, pre, body): body=some n => result = some(toString n); body=none & method in {GET,HEAD} => result = pre; body=none & else => result = some "0". There is a unique correct result for every input, so a verifying correct_ proof forces extensional equality to gold on the whole modeled domain — no same-spec wrong impl can close. Confirmed empirically.

SAME_SPEC: all 7 attacks + positive control return same_spec=True (spec/axioms/pure/post regions byte-identical; built by splicing only the impl+proof regions).

ATTACKS (all VERIFIED via `bash scripts/lean_verify.sh <f>`; all exit 1 = 'unsolved goals', genuine correctness rejections, NOT syntax errors — each given a strong catch-all proof `first | rfl | simp_all | decide` to maximize its chance): atk_1 (prepatch bug: unconditional "0" on no-body, no GET/HEAD suppression) -> exit 1, unsolved goals @70:6. Diverges: (GET,none,none) impl=some"0" vs spec=pre(none). This is the pre-patch defect; prepatch reproduced. atk_2 (HEAD dropped: suppress only GET) -> exit 1 @72,73. Diverges: (HEAD,none,none) impl=some"0" vs spec=none. atk_3 (off-by-one on body length: toString (n+1)) -> exit 1 @68,72,73. Diverges: (POST,_,some 0) impl=some"1" vs spec=some"0". atk_4 (ungrounded-oracle echo: ignore body, return pre) -> exit 1 @63,68.

Diverges: (POST,none,some 5) impl=none vs spec=some"5". atk_5 (control-flow swap: write "0" for GET/HEAD, retain pre otherwise) -> exit 1 @72,73. Diverges: (GET,none,none) impl=some"0" vs spec=pre. atk_6 (never write "0": no-body always retains pre) -> exit 1 @70:6. Diverges: (POST,none,none) impl=none vs spec=some"0". atk_7 (boundary/partial-domain: body n=0 retains pre) -> exit 1 @72,76,77. Diverges: (POST,none,some 0) impl=pre vs spec=some"0".

POSITIVE CONTROL: positive_control.lean = gold Solution.lean impl, `lean_verify.sh` exit 0; `#print axioms correct_prepare_content_length` => [propext] only (clean, no sorryAx — real proof).

NO CLOSING WRONG IMPL => no resolve run was required by protocol step 2 (that step triggers only for a wrong impl whose proof closes with clean axioms; none did). To confirm the harness+correspondence is live rather than dead (guards against false INCONCLUSIVE/dead-oracle), I RAN run_resolve on the gold patch (= faithful patch of the positive control): resolved=True, completed=True ('resolved'). Gold patch verbatim equals instance.json patch (patch_equals_gold=true).

REFINEMENT AUDIT: legs 1-5 are all R or R/I or I (leg 4 pure I: the discriminating `elif method not in ('GET','HEAD'): '0'`). NO kind-3 (changed-inexpressible). A-legs: NONE — axioms region empty, deep_model_references=[], opaque_callees=[], G-AX=skip. Justified: prepare_content_length invokes no UNCHANGED callee; body.tell()/len(body) both collapse to length n:Nat (genuine type refinement, not a callee). G-CONF (conformance_check.py) realizes BOTH real branches (bytes len + BytesIO seek/tell) and asserts they agree with the shadow: 120018 inputs, 0 disagreements, seed=1142. A-leg attack surface is vacuously safe.

CONCLUSION: verify<=>correct holds — the spec is a bijective pinning of the modeled behavior; every same-spec deviation is caught by lean_verify. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior. The body-length
-- computation (whether obtained by querying a seekable stream or by measuring a
-- value) is abstracted to the length itself (a `Nat`) — a type refinement, not a
-- callee — so there is no `opaque` callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is a small,
-- finite case analysis on the body and the request method.
-- pure-end

-- post-conditions-start
/-- Determination of the message-length header for a prepared HTTP request.

Inputs:
* `method` — the (normalized, upper-case) HTTP request method.
* `pre`    — the value held by the message-length header slot *before* the
  call (`none` when the header is absent, e.g. the caller supplied no such
  header).
* `body`   — `some n` when a request body carrying `n` units of content is
  present; `none` when there is no request body.

`result : Option String` is the value held by the message-length header slot
*after* the call, with `none` meaning the header is absent.

Required behavior:
* If a body is present, the header is its content length, rendered in decimal.
* If there is no body, the header is the literal `"0"` for methods that may
  carry a payload; for the `"GET"` and `"HEAD"` methods (which must not
  advertise a zero-length body) the slot is **not written** — it keeps its
  prior value `pre` (in particular the header stays absent when it was
  absent before the call). -/
def problem_spec_prepare_content_length
    (method : String) (pre : Option String) (body : Option Nat)
    (result : Option String) : Prop :=
  match body with
  | some n => result = some (toString n)
  | none   =>
      if method = "GET" ∨ method = "HEAD" then result = pre
      else result = some "0"
-- post-conditions-end

-- impl-start
def implementation_prepare_content_length
    (method : String) (pre : Option String) (body : Option Nat) :
    Option String := Id.run do
  -- the header slot starts at its pre-call value; only writes change it
  let mut clen : Option String := pre
  match body with
  | some n =>
      -- a body is present: its content length is reported
      clen := some (toString n)
  | none =>
      -- no body: only methods that may carry a payload write a zero length;
      -- for GET/HEAD nothing is written and the slot retains `pre`
      if method ≠ "GET" ∧ method ≠ "HEAD" then
        clen := some "0"
  return clen
-- impl-end

-- proof-start
theorem correct_prepare_content_length :
    ∀ (method : String) (pre : Option String) (body : Option Nat),
      problem_spec_prepare_content_length method pre body
        (implementation_prepare_content_length method pre body) := by
  intro method pre body
  unfold problem_spec_prepare_content_length implementation_prepare_content_length
  cases body with
  | some n => rfl
  | none =>
      simp only [Id.run]
      by_cases h : method = "GET" ∨ method = "HEAD"
      · rw [if_pos h]
        have h' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by
          rcases h with h | h <;> simp [h]
        simp only [if_neg h']
        rfl
      · rw [if_neg h]
        push_neg at h
        have h' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩
        simp only [if_pos h']
        rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_prepare_content_length is a TOTAL, POINTWISE-EXACT function of (method, pre, body): body=some n => result = some(toString n); body=none & method in {GET,HEAD} => result = pre; body=none & else => result = some "0". There is a unique correct result for every input, so a verifying correct_ proof forces extensional equality to gold on the whole modeled domain — no same-spec wrong impl can close. Confirmed empirically.

SAME_SPEC: all 7 attacks + positive control return same_spec=True (spec/axioms/pure/post regions byte-identical; built by splicing only the impl+proof regions).

ATTACKS (all VERIFIED via `bash scripts/lean_verify.sh <f>`; all exit 1 = 'unsolved goals', genuine correctness rejections, NOT syntax errors — each given a strong catch-all proof `first | rfl | simp_all | decide` to maximize its chance): atk_1 (prepatch bug: unconditional "0" on no-body, no GET/HEAD suppression) -> exit 1, unsolved goals @70:6. Diverges: (GET,none,none) impl=some"0" vs spec=pre(none). This is the pre-patch defect; prepatch reproduced. atk_2 (HEAD dropped: suppress only GET) -> exit 1 @72,73. Diverges: (HEAD,none,none) impl=some"0" vs spec=none. atk_3 (off-by-one on body length: toString (n+1)) -> exit 1 @68,72,73. Diverges: (POST,_,some 0) impl=some"1" vs spec=some"0". atk_4 (ungrounded-oracle echo: ignore body, return pre) -> exit 1 @63,68.

Diverges: (POST,none,some 5) impl=none vs spec=some"5". atk_5 (control-flow swap: write "0" for GET/HEAD, retain pre otherwise) -> exit 1 @72,73. Diverges: (GET,none,none) impl=some"0" vs spec=pre. atk_6 (never write "0": no-body always retains pre) -> exit 1 @70:6. Diverges: (POST,none,none) impl=none vs spec=some"0". atk_7 (boundary/partial-domain: body n=0 retains pre) -> exit 1 @72,76,77. Diverges: (POST,none,some 0) impl=pre vs spec=some"0".

POSITIVE CONTROL: positive_control.lean = gold Solution.lean impl, `lean_verify.sh` exit 0; `#print axioms correct_prepare_content_length` => [propext] only (clean, no sorryAx — real proof).

NO CLOSING WRONG IMPL => no resolve run was required by protocol step 2 (that step triggers only for a wrong impl whose proof closes with clean axioms; none did). To confirm the harness+correspondence is live rather than dead (guards against false INCONCLUSIVE/dead-oracle), I RAN run_resolve on the gold patch (= faithful patch of the positive control): resolved=True, completed=True ('resolved'). Gold patch verbatim equals instance.json patch (patch_equals_gold=true).

REFINEMENT AUDIT: legs 1-5 are all R or R/I or I (leg 4 pure I: the discriminating `elif method not in ('GET','HEAD'): '0'`). NO kind-3 (changed-inexpressible). A-legs: NONE — axioms region empty, deep_model_references=[], opaque_callees=[], G-AX=skip. Justified: prepare_content_length invokes no UNCHANGED callee; body.tell()/len(body) both collapse to length n:Nat (genuine type refinement, not a callee). G-CONF (conformance_check.py) realizes BOTH real branches (bytes len + BytesIO seek/tell) and asserts they agree with the shadow: 120018 inputs, 0 disagreements, seed=1142. A-leg attack surface is vacuously safe.

CONCLUSION: verify<=>correct holds — the spec is a bijective pinning of the modeled behavior; every same-spec deviation is caught by lean_verify. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical to Solution_prepatch.lean shadow (same_spec=True). Lean compiles (exit 0), #print axioms = [propext] only (no sorryAx — proof real). G-CONF independent reconstruction: 120018 inputs, seed 1142, 0 disagreements. Faithfulness checked against post-patch prepare_content_length (requests/models.py:388, base 22623bd8): (1) body present -> some(toString n): real always writes str(len)/str(tell()) regardless of method/pre — decimal render matches toString on Nat; empty body b"" maps to some 0 -> "0" since real uses `is not None` not truthiness. (2) body none & non-GET/HEAD -> some "0": matches new elif branch. (3) body none & GET/HEAD -> result=pre: matches 'nothing written, slot retains prior value'; pre is reachable (prepare_headers copies user Content-Length before prepare_body). Method compared against upper-case literals is faithful because prepare_method upper-cases before this call (normalized-verb domain per mapping.md). No over-strong assertion, no drift; the modeled function agrees with the real callee on every reachable input. NOTE: divergence vs the read-only reference Solution.lean is the intended REPAIR (reference asserted result=none on no-body GET/HEAD, dropping a pre-existing header — that was the unfaithful/over-strong version); this bundle fixed it by adding the pre parameter. Only omitted domain is method=None (a domain boundary, not a case where the spec asserts wrong behavior).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. Mechanical screen: leakage.screen(Solution.lean, LeanBackend.language, gold_patch, problem_statement) => passed=True, hard_failures=[]. Changed symbol {'prepare_body'} does not appear in the spec view. Spec region byte-identical to prepatch (same_spec=True), so no attack-variant spec drift. Spec view hash matches meta G-HYGIENE spec_view 9369a984... .

Spec view = imports + empty axioms/pure comments + a behavioral docstring and the pure contract problem_spec_prepare_content_length: body present => result=some(toString n); no body => (method=GET or HEAD => result=pre) else result=some"0". Impl and proof are elided.

Semantic assessment: (1) The spec view reveals nothing about the code-level gold edit -- no diff markers, no file path (requests/models.py), no removed/added lines, no reference to the removed leading unconditional Content-Length='0' or the added trailing elif, no issue numbers, no seek/tell-vs-len branch detail. Those live only in refinement.md/mapping.md, which are NOT consumer-facing. (2) The spec states the CORRECT post-condition (bodyless GET/HEAD => header keeps its prior value, i.e. absent stays absent; else '0'), which is the definitional job of a faithful spec and is exactly the behavior the PUBLIC problem_statement already discloses ('the right behavior is not to add this header automatically in GET requests'). Stating target behavior is not gold-edit leakage; the solver must still synthesize impl+proof. (3) HEAD is named in the spec but not verbatim in problem_statement (it does appear in hints_text). Its inclusion is faithfulness-mandated: the true function prepare_content_length suppresses '0' for BOTH GET and HEAD, so omitting HEAD would make the spec unfaithful/under-specified. This is required-behavior fidelity, not a reconstruction of the diff. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.