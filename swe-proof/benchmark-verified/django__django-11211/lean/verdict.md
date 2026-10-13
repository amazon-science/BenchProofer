# P2 adversarial audit — django__django-11211

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5b.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl has a closing clean-axiom proof. The only verifying candidate other than the gold impl (atk_5b: double canonicalValue, closed with `cases value <;> rfl`, #print axioms => 'does not depend on any axioms') is behaviorally identical to gold because canonicalValue is idempotent; per protocol its faithful patch (double to_python) was materialized and RAN through run_resolve('django__django-11211') => RESOLVED=True, completed=True, note='resolved'. So the sole closing verifying impl RESOLVES => verify does NOT imply-not correct; spec is NOT broken.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,11 +76,10 @@
 
 -- impl-start
 def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
-  -- First apply the pass-through preparation, then convert the result to its
-  -- canonical identifier shape.
+  -- prepatch: pass-through only, no canonicalising conversion.
   let mut v := value
   v := basePrep v
-  return canonicalValue v
+  return v
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,12 +75,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
-  -- First apply the pass-through preparation, then convert the result to its
-  -- canonical identifier shape.
-  let mut v := value
-  v := basePrep v
-  return canonicalValue v
+def implementation_normalizeKey (value : UuidValue) : UuidValue :=
+  match value with
+  | .absent      => .absent
+  | .canonical _ => .absent
+  | .textual s   => .canonical (decodeHex s)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,12 +75,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
-  -- First apply the pass-through preparation, then convert the result to its
-  -- canonical identifier shape.
-  let mut v := value
-  v := basePrep v
-  return canonicalValue v
+def implementation_normalizeKey (value : UuidValue) : UuidValue :=
+  match value with
+  | .absent      => .absent
+  | .canonical n => .canonical n
+  | .textual []  => .absent
+  | .textual s   => .canonical (decodeHex s)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,12 +75,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
-  -- First apply the pass-through preparation, then convert the result to its
-  -- canonical identifier shape.
-  let mut v := value
-  v := basePrep v
-  return canonicalValue v
+def implementation_normalizeKey (value : UuidValue) : UuidValue :=
+  match value with
+  | .absent      => .canonical 0
+  | .canonical n => .canonical n
+  | .textual s   => .canonical (decodeHex s)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -76,11 +76,9 @@
 
 -- impl-start
 def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
-  -- First apply the pass-through preparation, then convert the result to its
-  -- canonical identifier shape.
   let mut v := value
   v := basePrep v
-  return canonicalValue v
+  return canonicalValue (canonicalValue v)
 -- impl-end
 
 -- proof-start
@@ -89,5 +87,5 @@
       problem_spec_normalizeKey value (implementation_normalizeKey value) := by
   intro value
   unfold problem_spec_normalizeKey implementation_normalizeKey basePrep
-  rfl
+  cases value <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,12 +75,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
-  -- First apply the pass-through preparation, then convert the result to its
-  -- canonical identifier shape.
-  let mut v := value
-  v := basePrep v
-  return canonicalValue v
+def implementation_normalizeKey (value : UuidValue) : UuidValue :=
+  match value with
+  | .absent      => .absent
+  | .canonical n => .canonical n
+  | .textual s   => .canonical (decodeHex (s.drop 1))
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,12 +75,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
-  -- First apply the pass-through preparation, then convert the result to its
-  -- canonical identifier shape.
-  let mut v := value
-  v := basePrep v
-  return canonicalValue v
+def implementation_normalizeKey (value : UuidValue) : UuidValue :=
+  match value with
+  | .absent      => .absent
+  | .canonical n => .canonical n
+  | .textual s   => .canonical (decodeHex s * 16)
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,12 +75,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
-  -- First apply the pass-through preparation, then convert the result to its
-  -- canonical identifier shape.
-  let mut v := value
-  v := basePrep v
-  return canonicalValue v
+def implementation_normalizeKey (value : UuidValue) : UuidValue :=
+  match value with
+  | .absent      => .absent
+  | .canonical n => .canonical n
+  | .textual s   => .textual s
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Preparing a stored identifier value for use as a comparison key.

Some records are keyed by a universally-unique identifier (a 128-bit value). The
same identifier can be carried in more than one shape: as an already-parsed
identifier object, or as a piece of text that spells the identifier out (for
instance the string form that is kept in a free-text column, which may include
separator characters). A value may also be absent.

To decide whether two records refer to the SAME identifier, each candidate value
is first put into a single canonical shape. The behaviour pinned below is that of
that preparation step: it maps every textual spelling of an identifier to the one
canonical identifier it denotes, leaves an already-canonical identifier and an
absent value untouched, and so makes two values that denote the same identifier
compare equal regardless of the shape each arrived in.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a logical axiom. The two helpers the
-- prepared value is built from — the no-op pass-through that precedes the
-- conversion, and the textual→identifier conversion itself — are modeled DEEPLY
-- as the pure functions `basePrep` and `canonicalValue` below (the textual
-- conversion decodes the identifier's hexadecimal digits, ignoring separators).
-- They are deep-model references validated against the real callees by the
-- conformance check, not consumed axioms, so no `opaque`/`axiom` is declared.
-- axioms-end

-- pure-start
/-- A value that may carry an identifier in one of several shapes. -/
inductive UuidValue where
  | absent
  | canonical (n : Nat)
  | textual (s : List Char)
  deriving DecidableEq

/-- Hexadecimal value of a single character, if it is a hex digit
(`0`–`9`, `a`–`f`, `A`–`F`); `none` for any other character. -/
def hexVal? (c : Char) : Option Nat :=
  let n := c.toNat
  if 48 ≤ n ∧ n ≤ 57 then some (n - 48)              -- '0'..'9'
  else if 97 ≤ n ∧ n ≤ 102 then some (n - 97 + 10)   -- 'a'..'f'
  else if 65 ≤ n ∧ n ≤ 70 then some (n - 65 + 10)    -- 'A'..'F'
  else none

/-- Decode the identifier denoted by a textual spelling: accumulate its
hexadecimal digits left to right, ignoring any separator characters. -/
def decodeHex (s : List Char) : Nat :=
  s.foldl (fun acc c => match hexVal? c with
                        | some d => acc * 16 + d
                        | none   => acc) 0

/-- The no-op pass-through applied before conversion (returns its argument). -/
def basePrep (v : UuidValue) : UuidValue := v

/-- The canonical identifier denoted by a value: a textual spelling is decoded to
the identifier it denotes; an already-canonical identifier and an absent value are
returned unchanged. -/
def canonicalValue : UuidValue → UuidValue
  | .absent      => .absent
  | .canonical n => .canonical n
  | .textual s   => .canonical (decodeHex s)
-- pure-end

-- post-conditions-start
/-- The prepared value is fully pinned to the input: it is the canonical
identifier the input denotes. A textual spelling is converted to its canonical
identifier; an already-canonical identifier and an absent value are unchanged. No
output component is left free, so two values denoting the same identifier are
prepared to the SAME canonical value regardless of the shape each arrived in. -/
def problem_spec_normalizeKey (value : UuidValue) (result : UuidValue) : Prop :=
  result = canonicalValue value
-- post-conditions-end

-- impl-start
def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
  let mut v := value
  v := basePrep v
  return canonicalValue v
-- impl-end

-- proof-start
theorem correct_normalizeKey :
    ∀ (value : UuidValue),
      problem_spec_normalizeKey value (implementation_normalizeKey value) := by
  intro value
  unfold problem_spec_normalizeKey implementation_normalizeKey basePrep
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL (all; same_spec=True for every file below vs Solution.lean, confirmed via swebench_unified.markers.same_spec on lean backend). Verify cmd: `bash scripts/lean_verify.sh <file>`. Attacks run concurrently in batches of 4.

### RESULTS (exit code = lean_verify):
- pos.lean (positive control, exact gold impl: return canonicalValue (basePrep v)) => exit 0 VERIFIES.
- atk_1 (prepatch bug: identity, return v, no conversion) => exit 1 does NOT verify. Prepatch reproduced (matches Solution_prepatch.lean impl; the buggy identity leaves textual unconverted, cannot satisfy result = canonicalValue value at textual s).
- atk_2 (partial-domain: match, canonical _ => absent) => exit 1.
- atk_3 (boundary: textual [] => absent, else decode) => exit 1.
- atk_4 (control-flow-effect: absent => canonical 0) => exit 1.
- atk_5 (ungrounded-oracle echo, double canonicalValue, ORIGINAL rfl proof) => exit 1 (rfl not definitionally equal; error shown). Re-encoded as atk_5b with proof `cases value <;> rfl`.
- atk_5b (double canonicalValue, closing proof) => exit 0 VERIFIES; `#print axioms correct_normalizeKey` => 'does not depend on any axioms' (CLEAN, no sorryAx, no propext even). BEHAVIORALLY GOLD (idempotent). Faithful patch materialized (to_python(to_python(super().get_prep_value(value)))) and RUN: run_resolve => RESOLVED=True, completed=True, note='resolved'. active bench swe_bench_verified, supports_docker_oracle=True, resolve_style=swebench.
- atk_6 (drop-first-hex-digit: decodeHex (s.drop 1)) => exit 1.
- atk_7 (x16 shift: decodeHex s * 16) => exit 1.
- atk_8 (textual left unconverted: textual s => textual s) => exit 1.

WHY SOUND (root cause): post-condition problem_spec_normalizeKey is a TOTAL equation result = canonicalValue value with no existential and no underspecified arm over the finite inductive UuidValue. `cases value <;> rfl` closes iff the impl equals canonicalValue at every constructor; any pointwise divergence leaves an unclosable goal at the differing input (confirmed: all 7 genuinely-wrong impls error at exit 1). Hence verify => impl == canonicalValue pointwise => behaviorally gold => resolves. verify does NOT imply-not correct here.

REFINEMENT AUDIT (refinement.md): 2 legs, both acceptable kinds; NO kind-3 (axiomatized-then-consumed). Op#1 `v := basePrep v` tagged I + A-reference: basePrep = Field.get_prep_value (identity pass-through for non-Promise value); deep-modeled as identity; correspondence holds. Op#2 `return canonicalValue v` tagged R + A-reference: canonicalValue/decodeHex = UUIDField.to_python (text->uuid.UUID via uuid.UUID(hex=s).int); deep-modeled; validated by G-CONF (meta.json: 100000 inputs, 0 disagreements deep-model vs REAL patched get_prep_value, seed 11211). axioms=[] and axiom_check.py is a legitimate skip stub (no consumed callee axiom). A-references correspond to the real callees Field.get_prep_value / UUIDField.to_python. A-legs' correspondence holds. Minor doc nit: mapping.md type-bijection line 59 lists urn:uuid: as an example spelling while the G-CONF fuzz-seed section correctly declares urn out-of-domain — documentation inconsistency only, not spec drift (operative domain in conformance_check.py excludes urn forms).

VERDICT: SOUND. >=5 distinct wrong-impl attacks encoded (atk_1 prepatch, atk_2 partial-domain, atk_3 boundary, atk_4 control-flow-effect, atk_6 drop-digit, atk_7 x16, atk_8 no-op-textual) + ungrounded-oracle echo (atk_5b); none of the 7 genuinely-wrong impls verifies; the only closing clean-axiom verifying candidate (atk_5b) is behaviorally gold and its materialized faithful patch RESOLVED under the official harness. verify => correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5b.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl has a closing clean-axiom proof. The only verifying candidate other than the gold impl (atk_5b: double canonicalValue, closed with `cases value <;> rfl`, #print axioms => 'does not depend on any axioms') is behaviorally identical to gold because canonicalValue is idempotent; per protocol its faithful patch (double to_python) was materialized and RAN through run_resolve('django__django-11211') => RESOLVED=True, completed=True, note='resolved'. So the sole closing verifying impl RESOLVES => verify does NOT imply-not correct; spec is NOT broken.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Preparing a stored identifier value for use as a comparison key.

Some records are keyed by a universally-unique identifier (a 128-bit value). The
same identifier can be carried in more than one shape: as an already-parsed
identifier object, or as a piece of text that spells the identifier out (for
instance the string form that is kept in a free-text column, which may include
separator characters). A value may also be absent.

To decide whether two records refer to the SAME identifier, each candidate value
is first put into a single canonical shape. The behaviour pinned below is that of
that preparation step: it maps every textual spelling of an identifier to the one
canonical identifier it denotes, leaves an already-canonical identifier and an
absent value untouched, and so makes two values that denote the same identifier
compare equal regardless of the shape each arrived in.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a logical axiom. The two helpers the
-- prepared value is built from — the no-op pass-through that precedes the
-- conversion, and the textual→identifier conversion itself — are modeled DEEPLY
-- as the pure functions `basePrep` and `canonicalValue` below (the textual
-- conversion decodes the identifier's hexadecimal digits, ignoring separators).
-- They are deep-model references validated against the real callees by the
-- conformance check, not consumed axioms, so no `opaque`/`axiom` is declared.
-- axioms-end

-- pure-start
/-- A value that may carry an identifier in one of several shapes. -/
inductive UuidValue where
  | absent
  | canonical (n : Nat)
  | textual (s : List Char)
  deriving DecidableEq

/-- Hexadecimal value of a single character, if it is a hex digit
(`0`–`9`, `a`–`f`, `A`–`F`); `none` for any other character. -/
def hexVal? (c : Char) : Option Nat :=
  let n := c.toNat
  if 48 ≤ n ∧ n ≤ 57 then some (n - 48)              -- '0'..'9'
  else if 97 ≤ n ∧ n ≤ 102 then some (n - 97 + 10)   -- 'a'..'f'
  else if 65 ≤ n ∧ n ≤ 70 then some (n - 65 + 10)    -- 'A'..'F'
  else none

/-- Decode the identifier denoted by a textual spelling: accumulate its
hexadecimal digits left to right, ignoring any separator characters. -/
def decodeHex (s : List Char) : Nat :=
  s.foldl (fun acc c => match hexVal? c with
                        | some d => acc * 16 + d
                        | none   => acc) 0

/-- The no-op pass-through applied before conversion (returns its argument). -/
def basePrep (v : UuidValue) : UuidValue := v

/-- The canonical identifier denoted by a value: a textual spelling is decoded to
the identifier it denotes; an already-canonical identifier and an absent value are
returned unchanged. -/
def canonicalValue : UuidValue → UuidValue
  | .absent      => .absent
  | .canonical n => .canonical n
  | .textual s   => .canonical (decodeHex s)
-- pure-end

-- post-conditions-start
/-- The prepared value is fully pinned to the input: it is the canonical
identifier the input denotes. A textual spelling is converted to its canonical
identifier; an already-canonical identifier and an absent value are unchanged. No
output component is left free, so two values denoting the same identifier are
prepared to the SAME canonical value regardless of the shape each arrived in. -/
def problem_spec_normalizeKey (value : UuidValue) (result : UuidValue) : Prop :=
  result = canonicalValue value
-- post-conditions-end

-- impl-start
def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
  let mut v := value
  v := basePrep v
  return canonicalValue v
-- impl-end

-- proof-start
theorem correct_normalizeKey :
    ∀ (value : UuidValue),
      problem_spec_normalizeKey value (implementation_normalizeKey value) := by
  intro value
  unfold problem_spec_normalizeKey implementation_normalizeKey basePrep
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL (all; same_spec=True for every file below vs Solution.lean, confirmed via swebench_unified.markers.same_spec on lean backend). Verify cmd: `bash scripts/lean_verify.sh <file>`. Attacks run concurrently in batches of 4.

### RESULTS (exit code = lean_verify):
- pos.lean (positive control, exact gold impl: return canonicalValue (basePrep v)) => exit 0 VERIFIES.
- atk_1 (prepatch bug: identity, return v, no conversion) => exit 1 does NOT verify. Prepatch reproduced (matches Solution_prepatch.lean impl; the buggy identity leaves textual unconverted, cannot satisfy result = canonicalValue value at textual s).
- atk_2 (partial-domain: match, canonical _ => absent) => exit 1.
- atk_3 (boundary: textual [] => absent, else decode) => exit 1.
- atk_4 (control-flow-effect: absent => canonical 0) => exit 1.
- atk_5 (ungrounded-oracle echo, double canonicalValue, ORIGINAL rfl proof) => exit 1 (rfl not definitionally equal; error shown). Re-encoded as atk_5b with proof `cases value <;> rfl`.
- atk_5b (double canonicalValue, closing proof) => exit 0 VERIFIES; `#print axioms correct_normalizeKey` => 'does not depend on any axioms' (CLEAN, no sorryAx, no propext even). BEHAVIORALLY GOLD (idempotent). Faithful patch materialized (to_python(to_python(super().get_prep_value(value)))) and RUN: run_resolve => RESOLVED=True, completed=True, note='resolved'. active bench swe_bench_verified, supports_docker_oracle=True, resolve_style=swebench.
- atk_6 (drop-first-hex-digit: decodeHex (s.drop 1)) => exit 1.
- atk_7 (x16 shift: decodeHex s * 16) => exit 1.
- atk_8 (textual left unconverted: textual s => textual s) => exit 1.

WHY SOUND (root cause): post-condition problem_spec_normalizeKey is a TOTAL equation result = canonicalValue value with no existential and no underspecified arm over the finite inductive UuidValue. `cases value <;> rfl` closes iff the impl equals canonicalValue at every constructor; any pointwise divergence leaves an unclosable goal at the differing input (confirmed: all 7 genuinely-wrong impls error at exit 1). Hence verify => impl == canonicalValue pointwise => behaviorally gold => resolves. verify does NOT imply-not correct here.

REFINEMENT AUDIT (refinement.md): 2 legs, both acceptable kinds; NO kind-3 (axiomatized-then-consumed). Op#1 `v := basePrep v` tagged I + A-reference: basePrep = Field.get_prep_value (identity pass-through for non-Promise value); deep-modeled as identity; correspondence holds. Op#2 `return canonicalValue v` tagged R + A-reference: canonicalValue/decodeHex = UUIDField.to_python (text->uuid.UUID via uuid.UUID(hex=s).int); deep-modeled; validated by G-CONF (meta.json: 100000 inputs, 0 disagreements deep-model vs REAL patched get_prep_value, seed 11211). axioms=[] and axiom_check.py is a legitimate skip stub (no consumed callee axiom). A-references correspond to the real callees Field.get_prep_value / UUIDField.to_python. A-legs' correspondence holds. Minor doc nit: mapping.md type-bijection line 59 lists urn:uuid: as an example spelling while the G-CONF fuzz-seed section correctly declares urn out-of-domain — documentation inconsistency only, not spec drift (operative domain in conformance_check.py excludes urn forms).

VERDICT: SOUND. >=5 distinct wrong-impl attacks encoded (atk_1 prepatch, atk_2 partial-domain, atk_3 boundary, atk_4 control-flow-effect, atk_6 drop-digit, atk_7 x16, atk_8 no-op-textual) + ungrounded-oracle echo (atk_5b); none of the 7 genuinely-wrong impls verifies; the only closing clean-axiom verifying candidate (atk_5b) is behaviorally gold and its materialized faithful patch RESOLVED under the official harness. verify => correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) check for django__django-11211 lean bundle.

Spec: problem_spec_normalizeKey value result := (result = canonicalValue value) — a full functional post-condition pinning output to the deep model canonicalValue. Models UUIDField.get_prep_value (post-patch = to_python(super().get_prep_value(value))).

### Verification
- same_spec(Solution, Solution_prepatch, lean tables) = True (spec region byte-identical; only impl/proof differ — prepatch impl returns v unchanged with a sorry proof, correct G-DIFF shape).
- lean_verify.sh exit 0; #print axioms correct_normalizeKey => 'does not depend on any axioms' (no sorryAx; proof genuine, not fake).
- Deep model differential-tested against the REAL callee worktree (base commit ba72606760; UUIDField has no own get_prep_value at base, so Field.get_prep_value + to_python composed to mirror the gold patch). 200,000 fuzzed inputs over the declared modeled domain (None, uuid.UUID objects, valid spellings str(u)/u.hex/upper/brace-wrapped, plus int=0 and all-f boundaries) => 0 disagreements. Boundary/hand spellings ('0'*32, 'f'*32, hyphenated, brace-wrapped, int=5) all match by uuid.int.

OUT-OF-DOMAIN divergences confirmed but LEGITIMATELY EXCLUDED:
- Invalid strings raise ValidationError in the real callee while canonicalValue/decodeHex returns a decoded number: 'abc'->2748, ''->0, '-'->0, '{abc}'->2748, '{}'->0. urn:uuid: forms also excluded (literal letters embed hex digits).
- These are explicitly documented as out of the modeled domain (mapping.md / refinement.md / conformance_check.py docstring). The UuidValue.textual carrier is bound to 'a str spelling of the identifier' (a VALID spelling), so invalid strings are not modeled inputs. Restriction is well-justified by the actual bug/use case: GFK prefetch (contenttypes/fields.py gfk_key) stores object_pk = str(related.pk), always a valid hyphenated UUID spelling.

Conclusion: within the modeled domain the deep model agrees with the real repo callee on every tested input; the domain restriction is honest and anchored to the real code path, not a device to hide disagreement. The spec is neither too strong nor drifting. No diverging input exists within the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen over the lean spec view) passes: hard_failures=[]. Manual audit confirms no leak beyond the public problem_statement (hints_text excluded per policy).

Gold edit: adds UUIDField.get_prep_value(self,value)= self.to_python(super().get_prep_value(value)) in django/db/models/fields/__init__.py (canonicalize textual UUID spelling to uuid.UUID). problem_statement reveals only the SYMPTOM (prefetch_related over a GFK returns None when the related model's PK is a UUIDField with a CharField object_id); it never names get_prep_value, to_python, UUIDField, the file, or the fix.

Spec-view checks:
- L1: no gold-patch line reproduced (>=8-char normalized); no diff markers (@@, +++, diff --git, index).
- L2: patched file path 'django/db/models/fields/__init__.py' and its dotted module form absent from spec view.
- L2/L5: only distinctive patched symbol is 'get_prep_value'. Spec-view identifiers (UuidValue, basePrep, canonicalValue, decodeHex, hexVal?, normalizeKey, absent/canonical/textual) do NOT embed get_prep_value / to_python / UUIDField / Field. Symbols are abstract/synthetic.
- L3: no narration (bug/fix/patch/regression/previously/...) in any comment or docstring; docstrings describe target behavior only.
- same_spec(Solution.lean, Solution_prepatch.lean)=True: spec region byte-identical, so no impl-specific tightening leaks the edit.

The spec states the required post-condition (result = canonicalValue value: every textual spelling maps to the one canonical identifier it denotes) over a synthetic UuidValue domain. That is a legitimate behavioral specification, not disclosure of the gold edit's localization. A solver must still discover the method/file/callee composition. meta gates G-LEAK/G-PANEL-1/2/3 all recorded pass; no relaxed_leakage flag and no RELAXED_LEAKAGE.md, so no deferral path is in play. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
