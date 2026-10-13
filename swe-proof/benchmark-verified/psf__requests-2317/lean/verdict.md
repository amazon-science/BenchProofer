# P2 adversarial audit — psf__requests-2317

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None survives. The spec `problem_spec_normalizeMethod method result := result = (nativeContent method).map Char.toUpper` is an EXACT element-wise functional equality with no free output components, no A-consumed axioms, and no A-reference oracle (axiom_check.py is a genuine skip stub; Solution.lean contains zero `axiom`/`opaque`/`sorry` declarations — nativeContent and Char.toUpper are concrete total functions). Any same-spec impl whose `correct_normalizeMethod` closes is therefore extensionally equal to gold. The only verifying attack (atk_6) is exactly that — an extensionally-equal echo — and its faithful patch is the gold patch, which RESOLVES.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,9 +70,9 @@
 
 -- impl-start
 def implementation_normalizeMethod (method : PyMethod) : List Char := Id.run do
-  -- Recover the textual content of the supplied token (decoding a byte token to
-  -- its characters), then upper-case it.
-  let mut m := nativeContent method
+  let mut m := match method with
+    | .text cs  => cs
+    | .bytes bs => ['b', '\''] ++ bs.map (fun b => Char.ofNat b.toNat) ++ ['\'']
   m := m.map Char.toUpper
   return m
 -- impl-end
@@ -84,5 +84,5 @@
         (implementation_normalizeMethod method) := by
   intro method
   unfold problem_spec_normalizeMethod implementation_normalizeMethod
-  rfl
+  cases method <;> simp [Id.run, nativeContent]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,10 +70,8 @@
 
 -- impl-start
 def implementation_normalizeMethod (method : PyMethod) : List Char := Id.run do
-  -- Recover the textual content of the supplied token (decoding a byte token to
-  -- its characters), then upper-case it.
-  let mut m := nativeContent method
-  m := m.map Char.toUpper
+  -- returns the native content WITHOUT upper-casing it
+  let m := nativeContent method
   return m
 -- impl-end
 
@@ -84,5 +82,5 @@
         (implementation_normalizeMethod method) := by
   intro method
   unfold problem_spec_normalizeMethod implementation_normalizeMethod
-  rfl
+  cases method <;> simp [Id.run, nativeContent]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,10 +70,10 @@
 
 -- impl-start
 def implementation_normalizeMethod (method : PyMethod) : List Char := Id.run do
-  -- Recover the textual content of the supplied token (decoding a byte token to
-  -- its characters), then upper-case it.
-  let mut m := nativeContent method
-  m := m.map Char.toUpper
+  let mut m : List Char := []
+  match method with
+  | .text cs  => m := cs.map Char.toUpper
+  | .bytes bs => m := bs.map (fun b => Char.ofNat b.toNat)   -- forgot toUpper here
   return m
 -- impl-end
 
@@ -84,5 +84,5 @@
         (implementation_normalizeMethod method) := by
   intro method
   unfold problem_spec_normalizeMethod implementation_normalizeMethod
-  rfl
+  cases method <;> simp [Id.run, nativeContent]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,10 +70,8 @@
 
 -- impl-start
 def implementation_normalizeMethod (method : PyMethod) : List Char := Id.run do
-  -- Recover the textual content of the supplied token (decoding a byte token to
-  -- its characters), then upper-case it.
   let mut m := nativeContent method
-  m := m.map Char.toUpper
+  m := m.map Char.toLower   -- wrong direction of case folding
   return m
 -- impl-end
 
@@ -84,5 +82,5 @@
         (implementation_normalizeMethod method) := by
   intro method
   unfold problem_spec_normalizeMethod implementation_normalizeMethod
-  rfl
+  cases method <;> simp [Id.run, nativeContent]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,10 +70,9 @@
 
 -- impl-start
 def implementation_normalizeMethod (method : PyMethod) : List Char := Id.run do
-  -- Recover the textual content of the supplied token (decoding a byte token to
-  -- its characters), then upper-case it.
   let mut m := nativeContent method
   m := m.map Char.toUpper
+  m := m.reverse            -- corrupts order (identity only on palindromes/empty)
   return m
 -- impl-end
 
@@ -84,5 +83,5 @@
         (implementation_normalizeMethod method) := by
   intro method
   unfold problem_spec_normalizeMethod implementation_normalizeMethod
-  rfl
+  cases method <;> simp [Id.run, nativeContent]
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,12 +69,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_normalizeMethod (method : PyMethod) : List Char := Id.run do
-  -- Recover the textual content of the supplied token (decoding a byte token to
-  -- its characters), then upper-case it.
-  let mut m := nativeContent method
-  m := m.map Char.toUpper
-  return m
+def implementation_normalizeMethod (method : PyMethod) : List Char :=
+  -- same behavior as gold, written point-free without Id.run
+  (nativeContent method).map (fun c => Char.toUpper c)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing the *method name* of an outgoing HTTP request before the request is
assembled.

A request's method (`GET`, `POST`, …) is supplied by the caller. It may arrive
either as ordinary text or as a raw byte token (some callers encode all of their
arguments to bytes before handing them over). Whatever its incoming form, the
method that is finally stored on the request must:

* carry the **textual content** of the supplied token — i.e. for a byte token the
  bytes are decoded back to their text characters, NOT rendered as some printable
  description of the byte object; and
* be upper-cased (HTTP method tokens are case-insensitive and are canonicalized
  to upper case).

So a method supplied as the byte token for `GET` must be stored as the three
characters `G`, `E`, `T` (upper-cased), exactly as if the caller had passed the
text `"get"`. Rendering the byte token as a printable description of the object
(prefixing/quoting it) would corrupt the method and the request would be directed
at a different resource than the one named.

A supplied method is modeled by its sequence of characters together with a tag
recording whether the caller passed text or a raw byte token. The behavior is
pinned below as an input → output relation on the supplied method; the
implementation and the correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two operations the
-- behavior performs — recovering the textual content of the supplied token and
-- upper-casing it — are modeled DEEPLY (selecting the underlying characters and
-- `List.map Char.toUpper`), so there is no `opaque`/`axiom` callee contract for
-- the proof to consume. Recovering ASCII text from an ASCII byte token and ASCII
-- upper-casing are both total and are exercised end-to-end by the differential
-- check.

/-- A supplied HTTP method: either ordinary text carrying a sequence of
characters (`PyMethod.text`), or a raw byte token carrying a sequence of bytes
(`PyMethod.bytes`) — the form produced by a caller that encodes its arguments
before handing them over. The byte token holds the actual bytes, NOT a
pre-decoded character sequence. -/
inductive PyMethod where
  | text  (chars : List Char)
  | bytes (bytes : List UInt8)
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- The textual content carried by a supplied method, independent of its
incoming form: text passes through unchanged, while a raw byte token is decoded
to its characters one byte at a time (the method tokens of interest are ASCII, so
each byte maps to the character at its code point). -/
def nativeContent : PyMethod → List Char
  | .text cs  => cs
  | .bytes bs => bs.map (fun b => Char.ofNat b.toNat)
-- pure-end

-- post-conditions-start
/-- The stored method is fully pinned to the supplied token: it is the upper-cased
form of the textual content the token carries — for a byte token, the decoded
characters, NOT any printable description of the byte object. The result is pinned
element-wise to the upper-cased input character at each position (and hence to the
same length), leaving no output component free. -/
def problem_spec_normalizeMethod (method : PyMethod) (result : List Char) : Prop :=
  result = (nativeContent method).map Char.toUpper
-- post-conditions-end

-- impl-start
def implementation_normalizeMethod (method : PyMethod) : List Char := Id.run do
  -- Recover the textual content of the supplied token (decoding a byte token to
  -- its characters), then upper-case it.
  let mut m := nativeContent method
  m := m.map Char.toUpper
  return m
-- impl-end

-- proof-start
theorem correct_normalizeMethod :
    ∀ (method : PyMethod),
      problem_spec_normalizeMethod method
        (implementation_normalizeMethod method) := by
  intro method
  unfold problem_spec_normalizeMethod implementation_normalizeMethod
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS (all; same_spec=True for all 6 attacks + positive control, verified via swebench_unified.markers.same_spec against bundle Solution.lean).

Verification command: `bash scripts/lean_verify.sh <file>`. Attacks launched concurrently in 2 batches of ≤4.

Positive control atk_pos (gold impl+proof): exit 0 (verifies, no sorry). #print axioms => 'correct_normalizeMethod' does not depend on any axioms (clean).

### WRONG IMPLS (each edits ONLY the impl region; axioms/pure/pre/post byte-identical):
- atk_1 PREPATCH BUG (control-flow: bytes token rendered as b'...' repr, `['b','\''] ++ decoded ++ ['\'']`): exit 1. Genuine unsolved goal on `bytes` case: `pure ('B'::'\''::... ) = List.map (Char.toUpper ∘ ...) bytes`. Prepatch reproduced = true (matches Solution_prepatch.lean skeleton; the bug is that byte tokens are not decoded to text).
- atk_2 PARTIAL-DOMAIN (recovers nativeContent but SKIPS upper-casing): exit 1. Unsolved goal: `pure (List.map (fun b => Char.ofNat b.toNat) bytes) = List.map (Char.toUpper ∘ ...) bytes`.
- atk_3 CONTROL-FLOW-EFFECT (upper-cases only the text branch; bytes branch left un-upper-cased): exit 1.
- atk_4 BOUNDARY (Char.toLower instead of toUpper — wrong case-fold direction): exit 1.
- atk_5 BOUNDARY/ORDER (correct normalize then `.reverse` — identity only on empty/palindromes): exit 1.
All five FAIL to close — the exact functional-equality spec rejects each. None reaches a clean-axiom closing proof, so none triggers the resolve obligation.

UNGROUNDED-ORACLE ECHO atk_6 (`(nativeContent method).map (fun c => Char.toUpper c)`, point-free, no Id.run; proof `rfl`): exit 0 (VERIFIES, no sorry). #print axioms correct_normalizeMethod => 'does not depend on any axioms' (CLEAN). Per protocol, materialized its faithful refined patch (extensionally == gold, so = gold patch) and RAN it through the official harness:
  run_resolve('psf__requests-2317', <gold patch>, run_id='sbu-audit-eq-x3zeo9u3-atk6') under SBU_BENCHMARK=swe_bench_verified
  RESULT: RESOLVED=True COMPLETED=True NOTE=resolved (see resolve_atk6.out).
A resolving same-spec echo is NOT a weakness (unified panel_1/eq policy) — it confirms the spec accepts gold-equivalent impls that genuinely fix the bug.

REFINEMENT.MD AUDIT: 3 legs, all R/I — leg 1 (`nativeContent method` ↔ `to_native_string(method)`, the CHANGED line) tagged R, modeled deeply (byte token decoded per-byte via `Char.ofNat ∘ UInt8.toNat`, agreeing with `.decode('ascii')` on the ASCII method-token domain); leg 2 (`m.map Char.toUpper` ↔ `str.upper()`, unchanged callee) tagged R, deep; leg 3 (`return m` ↔ stored req.method) tagged I. NO A-consumed and NO A-reference legs — confirmed against Solution.lean (no axiom/opaque). No kind-3 (changed-inexpressible) leg. axiom_check.py correctly a skip stub. A-leg correspondence obligation is vacuous (no A-legs). Mapping.md binds implementation_normalizeMethod to the method-normalization step of Session.request (sessions.py:428) with a consistent type bijection.

CONCLUSION: verify⇒correct holds here. The only impls that verify are extensionally equal to gold (whose faithful patch resolves); every genuinely-divergent impl (partial-domain, boundary, control-flow-effect, prepatch, order) fails to close. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None survives. The spec `problem_spec_normalizeMethod method result := result = (nativeContent method).map Char.toUpper` is an EXACT element-wise functional equality with no free output components, no A-consumed axioms, and no A-reference oracle (axiom_check.py is a genuine skip stub; Solution.lean contains zero `axiom`/`opaque`/`sorry` declarations — nativeContent and Char.toUpper are concrete total functions). Any same-spec impl whose `correct_normalizeMethod` closes is therefore extensionally equal to gold. The only verifying attack (atk_6) is exactly that — an extensionally-equal echo — and its faithful patch is the gold patch, which RESOLVES.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing the *method name* of an outgoing HTTP request before the request is
assembled.

A request's method (`GET`, `POST`, …) is supplied by the caller. It may arrive
either as ordinary text or as a raw byte token (some callers encode all of their
arguments to bytes before handing them over). Whatever its incoming form, the
method that is finally stored on the request must:

* carry the **textual content** of the supplied token — i.e. for a byte token the
  bytes are decoded back to their text characters, NOT rendered as some printable
  description of the byte object; and
* be upper-cased (HTTP method tokens are case-insensitive and are canonicalized
  to upper case).

So a method supplied as the byte token for `GET` must be stored as the three
characters `G`, `E`, `T` (upper-cased), exactly as if the caller had passed the
text `"get"`. Rendering the byte token as a printable description of the object
(prefixing/quoting it) would corrupt the method and the request would be directed
at a different resource than the one named.

A supplied method is modeled by its sequence of characters together with a tag
recording whether the caller passed text or a raw byte token. The behavior is
pinned below as an input → output relation on the supplied method; the
implementation and the correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two operations the
-- behavior performs — recovering the textual content of the supplied token and
-- upper-casing it — are modeled DEEPLY (selecting the underlying characters and
-- `List.map Char.toUpper`), so there is no `opaque`/`axiom` callee contract for
-- the proof to consume. Recovering ASCII text from an ASCII byte token and ASCII
-- upper-casing are both total and are exercised end-to-end by the differential
-- check.

/-- A supplied HTTP method: either ordinary text carrying a sequence of
characters (`PyMethod.text`), or a raw byte token carrying a sequence of bytes
(`PyMethod.bytes`) — the form produced by a caller that encodes its arguments
before handing them over. The byte token holds the actual bytes, NOT a
pre-decoded character sequence. -/
inductive PyMethod where
  | text  (chars : List Char)
  | bytes (bytes : List UInt8)
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- The textual content carried by a supplied method, independent of its
incoming form: text passes through unchanged, while a raw byte token is decoded
to its characters one byte at a time (the method tokens of interest are ASCII, so
each byte maps to the character at its code point). -/
def nativeContent : PyMethod → List Char
  | .text cs  => cs
  | .bytes bs => bs.map (fun b => Char.ofNat b.toNat)
-- pure-end

-- post-conditions-start
/-- The stored method is fully pinned to the supplied token: it is the upper-cased
form of the textual content the token carries — for a byte token, the decoded
characters, NOT any printable description of the byte object. The result is pinned
element-wise to the upper-cased input character at each position (and hence to the
same length), leaving no output component free. -/
def problem_spec_normalizeMethod (method : PyMethod) (result : List Char) : Prop :=
  result = (nativeContent method).map Char.toUpper
-- post-conditions-end

-- impl-start
def implementation_normalizeMethod (method : PyMethod) : List Char := Id.run do
  -- Recover the textual content of the supplied token (decoding a byte token to
  -- its characters), then upper-case it.
  let mut m := nativeContent method
  m := m.map Char.toUpper
  return m
-- impl-end

-- proof-start
theorem correct_normalizeMethod :
    ∀ (method : PyMethod),
      problem_spec_normalizeMethod method
        (implementation_normalizeMethod method) := by
  intro method
  unfold problem_spec_normalizeMethod implementation_normalizeMethod
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS (all; same_spec=True for all 6 attacks + positive control, verified via swebench_unified.markers.same_spec against bundle Solution.lean).

Verification command: `bash scripts/lean_verify.sh <file>`. Attacks launched concurrently in 2 batches of ≤4.

Positive control atk_pos (gold impl+proof): exit 0 (verifies, no sorry). #print axioms => 'correct_normalizeMethod' does not depend on any axioms (clean).

### WRONG IMPLS (each edits ONLY the impl region; axioms/pure/pre/post byte-identical):
- atk_1 PREPATCH BUG (control-flow: bytes token rendered as b'...' repr, `['b','\''] ++ decoded ++ ['\'']`): exit 1. Genuine unsolved goal on `bytes` case: `pure ('B'::'\''::... ) = List.map (Char.toUpper ∘ ...) bytes`. Prepatch reproduced = true (matches Solution_prepatch.lean skeleton; the bug is that byte tokens are not decoded to text).
- atk_2 PARTIAL-DOMAIN (recovers nativeContent but SKIPS upper-casing): exit 1. Unsolved goal: `pure (List.map (fun b => Char.ofNat b.toNat) bytes) = List.map (Char.toUpper ∘ ...) bytes`.
- atk_3 CONTROL-FLOW-EFFECT (upper-cases only the text branch; bytes branch left un-upper-cased): exit 1.
- atk_4 BOUNDARY (Char.toLower instead of toUpper — wrong case-fold direction): exit 1.
- atk_5 BOUNDARY/ORDER (correct normalize then `.reverse` — identity only on empty/palindromes): exit 1.
All five FAIL to close — the exact functional-equality spec rejects each. None reaches a clean-axiom closing proof, so none triggers the resolve obligation.

UNGROUNDED-ORACLE ECHO atk_6 (`(nativeContent method).map (fun c => Char.toUpper c)`, point-free, no Id.run; proof `rfl`): exit 0 (VERIFIES, no sorry). #print axioms correct_normalizeMethod => 'does not depend on any axioms' (CLEAN). Per protocol, materialized its faithful refined patch (extensionally == gold, so = gold patch) and RAN it through the official harness:
  run_resolve('psf__requests-2317', <gold patch>, run_id='sbu-audit-eq-x3zeo9u3-atk6') under SBU_BENCHMARK=swe_bench_verified
  RESULT: RESOLVED=True COMPLETED=True NOTE=resolved (see resolve_atk6.out).
A resolving same-spec echo is NOT a weakness (unified panel_1/eq policy) — it confirms the spec accepts gold-equivalent impls that genuinely fix the bug.

REFINEMENT.MD AUDIT: 3 legs, all R/I — leg 1 (`nativeContent method` ↔ `to_native_string(method)`, the CHANGED line) tagged R, modeled deeply (byte token decoded per-byte via `Char.ofNat ∘ UInt8.toNat`, agreeing with `.decode('ascii')` on the ASCII method-token domain); leg 2 (`m.map Char.toUpper` ↔ `str.upper()`, unchanged callee) tagged R, deep; leg 3 (`return m` ↔ stored req.method) tagged I. NO A-consumed and NO A-reference legs — confirmed against Solution.lean (no axiom/opaque). No kind-3 (changed-inexpressible) leg. axiom_check.py correctly a skip stub. A-leg correspondence obligation is vacuous (no A-legs). Mapping.md binds implementation_normalizeMethod to the method-normalization step of Session.request (sessions.py:428) with a consistent type bijection.

CONCLUSION: verify⇒correct holds here. The only impls that verify are extensionally equal to gold (whose faithful patch resolves); every genuinely-divergent impl (partial-domain, boundary, control-flow-effect, prepatch, order) fails to close. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the modeled patched normalization to_native_string(method).upper() (sessions.py:428, utils.py:655 @ base 091991b). Within the explicitly documented modeled domain (ASCII HTTP method tokens), the Lean model agrees EXACTLY with the real callee: differential of shadow vs reconstructed to_native_string over 120,030 fuzz cases (both str and bytes forms) => 0 disagreements; exhaustive single-code-point sweep of ASCII 0-127 for both forms => 0 disagreements. Lean compiles (exit 0), proof is real (#print axioms: does not depend on any axioms), spec region byte-identical (same_spec=True, region hashes match meta.json), prepatch buggy skeleton genuinely fails the bytes case so the spec sees the bug. Divergences exist ONLY outside the pinned ASCII domain and are documented in mapping.md's domain note: (1) bytes>=128 -> real raises UnicodeDecodeError while Lean models a total per-byte latin-1 decode; (2) non-ASCII text (e.g. 'ß'->'SS', 'ﬀ'->'FF') -> real str.upper() performs length-changing full-Unicode case folding while Char.toUpper is ASCII-only. The domain restriction is legitimate (HTTP method tokens are ASCII; to_native_string defaults encoding='ascii' making the decode total). No in-domain diverging input exists, so the spec is not too strong. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + PyMethod type + nativeContent + problem_spec_normalizeMethod) describes only behavior already fully public in problem_statement. The problem_statement itself names the exact file/line (requests/sessions.py, `method = builtin_str(method)`), states the precise bug (b'GET' -> "b'GET'", the literal/repr string rather than decoded text), and the 404 consequence with the bytes-token origin. The spec view restates exactly this desired behavior: a byte token's textual content must be decoded to its characters, NOT rendered as a printable description of the byte object. It does NOT name the gold callee `to_native_string` nor the removed `builtin_str`, so it reveals no gold-specific API beyond the public problem_statement. The only extra element (upper-casing) corresponds to the pre-existing unchanged `method.upper()` in the `Request(...)` call, not the gold edit. Lexical G-LEAK screen also passes (hard_failures == []). Verified spec view rendering via swebench_unified.markers.spec_view over the lean backend; impl/proof regions correctly elided. This is the required faithful desired-behavior spec, which necessarily overlaps a problem_statement that itself spells out the fix behaviorally — that overlap is not leakage beyond the public statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
