# P2 adversarial audit — django__django-11133

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closes correct_toBytestring, so no faithful patch could be materialized. The only closing alternative (atk_6b: b.reverse.reverse / b++[]) is extensionally equal to gold and would resolve — not a break.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,10 +44,9 @@
 -- impl-start
 def implementation_toBytestring (charset : List Char) (value : PyValue) :
     List UInt8 := Id.run do
-  -- Byte-sequence-like values are returned as their underlying bytes directly.
   match value with
   | .bytesV b        => return b
-  | .memoryviewV b _ => return b
+  | .memoryviewV _ r => return encode charset r
   | .strV s          => return encode charset s
   | .otherV text     => return encode charset text
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,11 +44,10 @@
 -- impl-start
 def implementation_toBytestring (charset : List Char) (value : PyValue) :
     List UInt8 := Id.run do
-  -- Byte-sequence-like values are returned as their underlying bytes directly.
   match value with
   | .bytesV b        => return b
   | .memoryviewV b _ => return b
-  | .strV s          => return encode charset s
+  | .strV s          => return encode charset (s ++ ['x'])
   | .otherV text     => return encode charset text
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,9 +44,8 @@
 -- impl-start
 def implementation_toBytestring (charset : List Char) (value : PyValue) :
     List UInt8 := Id.run do
-  -- Byte-sequence-like values are returned as their underlying bytes directly.
   match value with
-  | .bytesV b        => return b
+  | .bytesV b        => return b.reverse
   | .memoryviewV b _ => return b
   | .strV s          => return encode charset s
   | .otherV text     => return encode charset text
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,12 +44,11 @@
 -- impl-start
 def implementation_toBytestring (charset : List Char) (value : PyValue) :
     List UInt8 := Id.run do
-  -- Byte-sequence-like values are returned as their underlying bytes directly.
   match value with
   | .bytesV b        => return b
   | .memoryviewV b _ => return b
   | .strV s          => return encode charset s
-  | .otherV text     => return encode charset text
+  | .otherV _        => return []
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,10 +44,9 @@
 -- impl-start
 def implementation_toBytestring (charset : List Char) (value : PyValue) :
     List UInt8 := Id.run do
-  -- Byte-sequence-like values are returned as their underlying bytes directly.
   match value with
   | .bytesV b        => return b
-  | .memoryviewV b _ => return b
+  | .memoryviewV _ _ => return encode charset []
   | .strV s          => return encode charset s
   | .otherV text     => return encode charset text
 -- impl-end
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,11 +44,10 @@
 -- impl-start
 def implementation_toBytestring (charset : List Char) (value : PyValue) :
     List UInt8 := Id.run do
-  -- Byte-sequence-like values are returned as their underlying bytes directly.
   match value with
   | .bytesV b        => return b
   | .memoryviewV b _ => return b
-  | .strV s          => return encode charset s
+  | .strV s          => return encode charset s ++ encode charset s
   | .otherV text     => return encode charset text
 -- impl-end
 
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,10 +44,9 @@
 -- impl-start
 def implementation_toBytestring (charset : List Char) (value : PyValue) :
     List UInt8 := Id.run do
-  -- Byte-sequence-like values are returned as their underlying bytes directly.
   match value with
-  | .bytesV b        => return b
-  | .memoryviewV b _ => return b
+  | .bytesV b        => return b.reverse.reverse
+  | .memoryviewV b _ => return b ++ []
   | .strV s          => return encode charset s
   | .otherV text     => return encode charset text
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- Encoding of a character sequence into a byte sequence under a named output
charset. This is the standard string-to-bytes encoding operation; it is an
UNCHANGED callee here, so only its signature is declared. The proof agent may
add a `_prop` axiom only if a proof step requires one. -/
opaque encode : List Char → List Char → List UInt8
-- axioms-end

-- pure-start
/-- The kinds of input value the coercion must turn into a byte sequence.
* `bytesV b`            — a value that already is a byte sequence `b`.
* `memoryviewV b r`     — a view over an underlying byte sequence `b`; `r` is the
                          value's textual representation (`r` is irrelevant to the
                          intended result and is present only to model the textual
                          rendering some inputs carry).
* `strV s`              — a character string `s`.
* `otherV text`         — any other value, whose textual rendering is `text`. -/
inductive PyValue where
  | bytesV      (b : List UInt8)
  | memoryviewV (b : List UInt8) (reprText : List Char)
  | strV        (s : List Char)
  | otherV      (text : List Char)
-- pure-end

-- post-conditions-start
/-- The result is the byte sequence that represents `value` in the output
`charset`:
* a byte-sequence value and a view over a byte sequence both yield exactly those
  underlying bytes, unchanged;
* a character string is encoded into bytes under `charset`;
* any other value is rendered to text and that text is encoded under `charset`. -/
def problem_spec_toBytestring (charset : List Char) (value : PyValue)
    (result : List UInt8) : Prop :=
  match value with
  | .bytesV b        => result = b
  | .memoryviewV b _ => result = b
  | .strV s          => result = encode charset s
  | .otherV text     => result = encode charset text
-- post-conditions-end

-- impl-start
def implementation_toBytestring (charset : List Char) (value : PyValue) :
    List UInt8 := Id.run do
  -- Byte-sequence-like values are returned as their underlying bytes directly.
  match value with
  | .bytesV b        => return b
  | .memoryviewV b _ => return b
  | .strV s          => return encode charset s
  | .otherV text     => return encode charset text
-- impl-end

-- proof-start
theorem correct_toBytestring : ∀ (charset : List Char) (value : PyValue),
    problem_spec_toBytestring charset value
      (implementation_toBytestring charset value) := by
  intro charset value
  cases value <;>
    simp only [problem_spec_toBytestring, implementation_toBytestring, Id.run, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_toBytestring is a TOTAL FUNCTIONAL EQUALITY: each of the 4 PyValue branches pins result to a unique closed expression (=b, =b, =encode charset s, =encode charset text). For every (charset,value) exactly one satisfying result. All attacks confirmed same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (lean backend).

### VERIFICATION (ran concurrently, <=4 background jobs; cmd: bash scripts/lean_verify.sh <file>):
- pos_control (gold impl): EXIT=0; #print axioms correct_toBytestring -> [propext] (clean). Positive control verifies.
- atk_1 PREPATCH BUG (memoryviewV _ r => encode charset r): EXIT=1; also aggressive proof (simp_all/decide/rfl) atk_1_agg EXIT=1. Residual false goal `encode charset reprText = b`. Prepatch bug reproduced.
- atk_2 partial-domain (strV s => encode charset (s++['x'])): EXIT=1; agg EXIT=1.
- atk_3 boundary (bytesV b => b.reverse): EXIT=1; agg EXIT=1.
- atk_4 ungrounded-oracle echo (otherV _ => []): EXIT=1; agg EXIT=1.
- atk_5 (memoryviewV _ _ => encode charset []): EXIT=1; agg EXIT=1. Residual false goal `encode charset [] = b`.
- atk_7 control-flow-effect (strV s => encode charset s ++ encode charset s): EXIT=1; agg EXIT=1.
- atk_6 cosmetic-but-EQUAL distractor (b.reverse.reverse / b++[]): with gold simp-only proof EXIT=1 (lemmas missing), but with stronger proof atk_6b EXIT=0 and #print axioms -> [propext] (clean). This impl is extensionally equal to gold => its faithful patch would RESOLVE => NOT a break. Included to demonstrate closure is possible only for gold-equivalent impls.

No same-spec WRONG impl closes with clean axioms, so the mandatory materialize-faithful-patch+run_resolve obligation is VACUOUS (applies only to closing wrong impls; there are none). verify => correct holds.

A-LEG / axioms audit (focus per instructions): axioms region declares only `opaque encode : List Char -> List Char -> List UInt8` (signature-only, NO _prop axiom). #print axioms on gold and on closing atk_6b both = [propext] only (no sorryAx, no fabricated encode_prop). Cannot inject a false axiom: axioms/pure/pre/post are frozen and compared byte-identically by same_spec (spec_view elides only impl+proof), all attacks confirmed True.

refinement.md audit: 5 rows. Row1 R (PyValue<->4-way isinstance dispatch); rows 2-5 I (identity ops: bytes/memoryview -> underlying bytes = bytes(value) verbatim copy; str/other -> same `encode` applied identically). NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible). A-leg absence is correct: `encode` is UNCHANGED callee used by reflexivity on both sides, so no callee property assumed and G-AX has nothing to validate. Correspondence to real make_bytes @879cc3d holds (mapping.md type bijection verified). Frame discipline intact: unchanged branches pinned identically in spec & impl.

SOUND after 6 distinct same-spec wrong-impl attacks (+2 proof-strength variants each) all fail to close, none breaks it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closes correct_toBytestring, so no faithful patch could be materialized. The only closing alternative (atk_6b: b.reverse.reverse / b++[]) is extensionally equal to gold and would resolve — not a break.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- Encoding of a character sequence into a byte sequence under a named output
charset. This is the standard string-to-bytes encoding operation; it is an
UNCHANGED callee here, so only its signature is declared. The proof agent may
add a `_prop` axiom only if a proof step requires one. -/
opaque encode : List Char → List Char → List UInt8
-- axioms-end

-- pure-start
/-- The kinds of input value the coercion must turn into a byte sequence.
* `bytesV b`            — a value that already is a byte sequence `b`.
* `memoryviewV b r`     — a view over an underlying byte sequence `b`; `r` is the
                          value's textual representation (`r` is irrelevant to the
                          intended result and is present only to model the textual
                          rendering some inputs carry).
* `strV s`              — a character string `s`.
* `otherV text`         — any other value, whose textual rendering is `text`. -/
inductive PyValue where
  | bytesV      (b : List UInt8)
  | memoryviewV (b : List UInt8) (reprText : List Char)
  | strV        (s : List Char)
  | otherV      (text : List Char)
-- pure-end

-- post-conditions-start
/-- The result is the byte sequence that represents `value` in the output
`charset`:
* a byte-sequence value and a view over a byte sequence both yield exactly those
  underlying bytes, unchanged;
* a character string is encoded into bytes under `charset`;
* any other value is rendered to text and that text is encoded under `charset`. -/
def problem_spec_toBytestring (charset : List Char) (value : PyValue)
    (result : List UInt8) : Prop :=
  match value with
  | .bytesV b        => result = b
  | .memoryviewV b _ => result = b
  | .strV s          => result = encode charset s
  | .otherV text     => result = encode charset text
-- post-conditions-end

-- impl-start
def implementation_toBytestring (charset : List Char) (value : PyValue) :
    List UInt8 := Id.run do
  -- Byte-sequence-like values are returned as their underlying bytes directly.
  match value with
  | .bytesV b        => return b
  | .memoryviewV b _ => return b
  | .strV s          => return encode charset s
  | .otherV text     => return encode charset text
-- impl-end

-- proof-start
theorem correct_toBytestring : ∀ (charset : List Char) (value : PyValue),
    problem_spec_toBytestring charset value
      (implementation_toBytestring charset value) := by
  intro charset value
  cases value <;>
    simp only [problem_spec_toBytestring, implementation_toBytestring, Id.run, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_toBytestring is a TOTAL FUNCTIONAL EQUALITY: each of the 4 PyValue branches pins result to a unique closed expression (=b, =b, =encode charset s, =encode charset text). For every (charset,value) exactly one satisfying result. All attacks confirmed same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (lean backend).

### VERIFICATION (ran concurrently, <=4 background jobs; cmd: bash scripts/lean_verify.sh <file>):
- pos_control (gold impl): EXIT=0; #print axioms correct_toBytestring -> [propext] (clean). Positive control verifies.
- atk_1 PREPATCH BUG (memoryviewV _ r => encode charset r): EXIT=1; also aggressive proof (simp_all/decide/rfl) atk_1_agg EXIT=1. Residual false goal `encode charset reprText = b`. Prepatch bug reproduced.
- atk_2 partial-domain (strV s => encode charset (s++['x'])): EXIT=1; agg EXIT=1.
- atk_3 boundary (bytesV b => b.reverse): EXIT=1; agg EXIT=1.
- atk_4 ungrounded-oracle echo (otherV _ => []): EXIT=1; agg EXIT=1.
- atk_5 (memoryviewV _ _ => encode charset []): EXIT=1; agg EXIT=1. Residual false goal `encode charset [] = b`.
- atk_7 control-flow-effect (strV s => encode charset s ++ encode charset s): EXIT=1; agg EXIT=1.
- atk_6 cosmetic-but-EQUAL distractor (b.reverse.reverse / b++[]): with gold simp-only proof EXIT=1 (lemmas missing), but with stronger proof atk_6b EXIT=0 and #print axioms -> [propext] (clean). This impl is extensionally equal to gold => its faithful patch would RESOLVE => NOT a break. Included to demonstrate closure is possible only for gold-equivalent impls.

No same-spec WRONG impl closes with clean axioms, so the mandatory materialize-faithful-patch+run_resolve obligation is VACUOUS (applies only to closing wrong impls; there are none). verify => correct holds.

A-LEG / axioms audit (focus per instructions): axioms region declares only `opaque encode : List Char -> List Char -> List UInt8` (signature-only, NO _prop axiom). #print axioms on gold and on closing atk_6b both = [propext] only (no sorryAx, no fabricated encode_prop). Cannot inject a false axiom: axioms/pure/pre/post are frozen and compared byte-identically by same_spec (spec_view elides only impl+proof), all attacks confirmed True.

refinement.md audit: 5 rows. Row1 R (PyValue<->4-way isinstance dispatch); rows 2-5 I (identity ops: bytes/memoryview -> underlying bytes = bytes(value) verbatim copy; str/other -> same `encode` applied identically). NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible). A-leg absence is correct: `encode` is UNCHANGED callee used by reflexivity on both sides, so no callee property assumed and G-AX has nothing to validate. Correspondence to real make_bytes @879cc3d holds (mapping.md type bijection verified). Frame discipline intact: unchanged branches pinned identically in spec & impl.

SOUND after 6 distinct same-spec wrong-impl attacks (+2 proof-strength variants each) all fail to close, none breaks it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of problem_spec_toBytestring vs real HttpResponseBase.make_bytes (django/http/response.py:223-237 @ post-patch 879cc3d). No diverging input found; spec is not too strong and does not drift. Checks: (1) lean_verify.sh exit 0; #print axioms correct_toBytestring = [propext] only (no sorryAx, real proof). (2) same_spec(Solution, Solution_prepatch)=True with lean LanguageTables — frozen spec region byte-identical, prepatch differs only in impl/proof. (3) All four PyValue constructors map exactly to real make_bytes results: bytesV b => b (bytes(bytes)=b); memoryviewV b _ => b (bytes(memoryview)=underlying bytes, verified incl. cast/int-array/non-contiguous views — the discriminating clause matching F2P b'memoryview'); strV s => encode charset s (real bytes(s.encode(charset)), opaque encode applied identically both sides); otherV text => encode charset text (real str(value).encode(charset)). (4) Independent differential + conformance_check.py: 120009 inputs, 0 disagreements. Spec stays at the correct altitude — str/other branches use the opaque unchanged callee (no over-pinned concrete bytes), bytes/memoryview branches pin = bytes(value). Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: passed=True, no hard_failures) and same_spec(Solution, Solution_prepatch)=True — the frozen spec is stable across the diff. Judged the consumer-facing spec_view (markers.spec_view over Solution.lean), which contains only: the opaque `encode` signature, the 4-way `PyValue` inductive, and the behavioral postcondition `problem_spec_toBytestring` pinning `.memoryviewV b _ => result = b` (memoryview yields its underlying bytes). Impl and proof regions are elided.

The public problem_statement ALREADY fully discloses this behavior: it shows `HttpResponse(memoryview(b"My Content")).content` yielding `b'<memory at 0x...>'` (the textual rendering) and states "I am expecting b'My Content'" (the underlying bytes). So the spec's memoryview→underlying-bytes postcondition is exactly the publicly-stated expected behavior, stated at spec altitude. The spec view does NOT reveal the gold edit MECHANISM beyond the problem_statement: no `isinstance`, no `(bytes, memoryview)` tuple, no mention of the changed line or Python patch structure. The two-field `memoryviewV b r` constructor is construction machinery that makes the pre-patch bug expressible (r = irrelevant textual rendering), not a disclosure of fix code.

The genuinely leak-shaped material — "the added memoryview arm", the verbatim gold patch body, "the discriminating clause" — lives only in refinement.md and mapping.md (auditor derivation docs), which are NOT part of bundle.solution_src()/spec_view and are outside G-PANEL-3 scope (which excludes hints_text-style derivation prose). No line of the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
