# P2 adversarial audit — django__django-11964

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `problem_spec_memberStr m result := result = pyStr m.value` is an exact functional equality that uniquely pins the output as a function of m. No closing-but-non-resolving impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,10 @@
   result = pyStr m.value
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_memberStr (m : EnumMember) : String := Id.run do
-  return pyStr m.value
+  return m.qualifiedName
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,12 @@
   result = pyStr m.value
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_memberStr (m : EnumMember) : String := Id.run do
-  return pyStr m.value
+  match m.value with
+  | .text s => return s
+  | .num _  => return ""
 -- impl-end
 
 -- proof-start
@@ -48,5 +51,5 @@
     problem_spec_memberStr m (implementation_memberStr m) := by
   intro m
   unfold problem_spec_memberStr implementation_memberStr
-  rfl
+  cases m.value <;> simp [pyStr, Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,10 @@
   result = pyStr m.value
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_memberStr (m : EnumMember) : String := Id.run do
-  return pyStr m.value
+  return (pyStr m.value) ++ "!"
 -- impl-end
 
 -- proof-start
@@ -48,5 +49,5 @@
     problem_spec_memberStr m (implementation_memberStr m) := by
   intro m
   unfold problem_spec_memberStr implementation_memberStr
-  rfl
+  simp [Id.run]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,12 @@
   result = pyStr m.value
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_memberStr (m : EnumMember) : String := Id.run do
-  return pyStr m.value
+  match m.value with
+  | .text s => return s
+  | .num _  => return m.qualifiedName
 -- impl-end
 
 -- proof-start
@@ -48,5 +51,5 @@
     problem_spec_memberStr m (implementation_memberStr m) := by
   intro m
   unfold problem_spec_memberStr implementation_memberStr
-  rfl
+  cases m.value <;> simp [pyStr, Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,10 @@
   result = pyStr m.value
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_memberStr (m : EnumMember) : String := Id.run do
-  return pyStr m.value
+  return ""
 -- impl-end
 
 -- proof-start
@@ -48,5 +49,5 @@
     problem_spec_memberStr m (implementation_memberStr m) := by
   intro m
   unfold problem_spec_memberStr implementation_memberStr
-  rfl
+  simp [pyStr, Id.run]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,10 @@
   result = pyStr m.value
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_memberStr (m : EnumMember) : String := Id.run do
-  return pyStr m.value
+  return m.qualifiedName ++ pyStr m.value
 -- impl-end
 
 -- proof-start
@@ -48,5 +49,5 @@
     problem_spec_memberStr m (implementation_memberStr m) := by
   intro m
   unfold problem_spec_memberStr implementation_memberStr
-  rfl
+  simp [Id.run]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,12 @@
   result = pyStr m.value
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_memberStr (m : EnumMember) : String := Id.run do
-  return pyStr m.value
+  match m.value with
+  | .text s => return s
+  | .num n  => return toString (-n)
 -- impl-end
 
 -- proof-start
@@ -48,5 +51,5 @@
     problem_spec_memberStr m (implementation_memberStr m) := by
   intro m
   unfold problem_spec_memberStr implementation_memberStr
-  rfl
+  cases m.value <;> simp [pyStr, Id.run]
 -- proof-end
```

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,9 +38,11 @@
   result = pyStr m.value
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_memberStr (m : EnumMember) : String := Id.run do
-  return pyStr m.value
+  let s := pyStr m.value
+  return s
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The string rendering of an
-- enumerated member's underlying value is modeled DEEPLY (see `pyStr` below)
-- rather than axiomatized, so its standard-library reference (Python's textual
-- conversion of a value) is validated as an A-reference by G-AX. The proof agent
-- may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The underlying value carried by an enumerated member. It is either a textual
value or an integral value (the two value kinds the modeled members use). -/
inductive MemberValue where
  | text : String → MemberValue
  | num  : Int → MemberValue
deriving DecidableEq

/-- Standard textual conversion of a member value: a textual value renders as
itself; an integral value renders as its decimal numeral. -/
def pyStr : MemberValue → String
  | .text s => s
  | .num n  => toString n

/-- An enumerated member, modeling only the fields the behavior touches: a
fully-qualified textual identifier of the member (its owner-qualified name) and
the underlying value it carries. -/
structure EnumMember where
  qualifiedName : String
  value : MemberValue
-- pure-end

-- post-conditions-start
/-- The textual rendering of an enumerated member equals the textual rendering of
its underlying value. -/
def problem_spec_memberStr (m : EnumMember) (result : String) : Prop :=
  result = pyStr m.value
-- post-conditions-end


-- impl-start
def implementation_memberStr (m : EnumMember) : String := Id.run do
  return pyStr m.value
-- impl-end

-- proof-start
theorem correct_memberStr : ∀ m : EnumMember,
    problem_spec_memberStr m (implementation_memberStr m) := by
  intro m
  unfold problem_spec_memberStr implementation_memberStr
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: exact functional equality `result = pyStr m.value`. Any closing impl's output must equal `pyStr m.value` for every m, uniquely determining behavior == gold `str(self.value)`. No axioms consumed (region empty); the changed conversion is modeled DEEPLY as `pyStr` (A-reference), validated by G-AX.

same_spec: all 9 files (atk_1..7, atk_echo, atk_pos) return True vs gold Solution.lean (spec regions lines 1-40 byte-identical; only impl+proof edited).

ATTACK BATTERY (8 same-spec wrong/variant impls + positive control), verified concurrently (≤4 jobs) via `bash scripts/lean_verify.sh <f>`:
- atk_1 (control-flow / prepatch bug: returns m.qualifiedName) -> exit 1, `rfl failed` (free-var inequality). PREPATCH BUG REPRODUCED (matches Solution_prepatch.lean; issue 'MyChoice.FIRST_CHOICE' != 'first').
- atk_2 (partial-domain: correct on .text, returns "" on .num) -> exit 1, unsolved goals.
- atk_3 (boundary: (pyStr m.value) ++ "!") -> exit 1, unsolved goals.
- atk_4 (control-flow-effect: .text->s, .num->qualifiedName) -> exit 1, unsolved goals.
- atk_5 (constant "") -> exit 1, unsolved goals.
- atk_6 (ungrounded-oracle echo: qualifiedName ++ pyStr m.value, extra prefix) -> exit 1, unsolved goals.
- atk_7 (num branch negated: toString (-n)) -> exit 1, unsolved goals.
All 7 failures are GENUINE unsolved/false goals (grep confirmed 'error: rfl failed' / 'error: unsolved goals'), not tactic-syntax errors.

### CLOSERS (only gold-equivalent impls close):
- atk_echo (gold behavior via let-binding: `let s := pyStr m.value; return s`) -> lean_verify exit 0; `#print axioms correct_memberStr` -> 'does not depend on any axioms' (clean).
- atk_pos (positive control, exact gold impl) -> exit 0; clean axioms.

MANDATORY RESOLVE (step 2): atk_echo is the ONLY *attack* that closes with clean axioms => materialized its faithful patch (= gold patch, since it implements `str(self.value)`) and RAN it through the official harness: run_resolve('django__django-11964', echo_patch) -> RESOLVED=True, note='resolved'. A resolving echo is NOT a weakness (per 2026-08-06 G-PANEL-1 / eq policy). No verifying attack has a non-resolving faithful patch => spec NOT broken.

G-AX A-reference audit: `python3 axiom_check.py` -> exit 0, 'G-AX OK: pyStr == str(value) on all probes (seed=11964)'. pyStr(.text s)=s mirrors CPython str(str) (identity); pyStr(.num n)=toString n mirrors CPython str(int) incl negatives/zero/large. Correspondence to real callee `str(self.value)` holds on the modeled int/str domain.

refinement.md audit: 3 legs — row1 R (member<->EnumMember, .value<->MemberValue), row2 A-reference (pyStr == str(self.value), validated by G-AX, NOT axiomatized), row3 I (return). No kind-3 (changed-inexpressible) legs. A-reference correspondence sound.

CONCLUSION: no closing-clean-axiom impl has a materialized faithful patch that fails to resolve. verify => correct holds for this bundle. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `problem_spec_memberStr m result := result = pyStr m.value` is an exact functional equality that uniquely pins the output as a function of m. No closing-but-non-resolving impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The string rendering of an
-- enumerated member's underlying value is modeled DEEPLY (see `pyStr` below)
-- rather than axiomatized, so its standard-library reference (Python's textual
-- conversion of a value) is validated as an A-reference by G-AX. The proof agent
-- may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The underlying value carried by an enumerated member. It is either a textual
value or an integral value (the two value kinds the modeled members use). -/
inductive MemberValue where
  | text : String → MemberValue
  | num  : Int → MemberValue
deriving DecidableEq

/-- Standard textual conversion of a member value: a textual value renders as
itself; an integral value renders as its decimal numeral. -/
def pyStr : MemberValue → String
  | .text s => s
  | .num n  => toString n

/-- An enumerated member, modeling only the fields the behavior touches: a
fully-qualified textual identifier of the member (its owner-qualified name) and
the underlying value it carries. -/
structure EnumMember where
  qualifiedName : String
  value : MemberValue
-- pure-end

-- post-conditions-start
/-- The textual rendering of an enumerated member equals the textual rendering of
its underlying value. -/
def problem_spec_memberStr (m : EnumMember) (result : String) : Prop :=
  result = pyStr m.value
-- post-conditions-end


-- impl-start
def implementation_memberStr (m : EnumMember) : String := Id.run do
  return pyStr m.value
-- impl-end

-- proof-start
theorem correct_memberStr : ∀ m : EnumMember,
    problem_spec_memberStr m (implementation_memberStr m) := by
  intro m
  unfold problem_spec_memberStr implementation_memberStr
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: exact functional equality `result = pyStr m.value`. Any closing impl's output must equal `pyStr m.value` for every m, uniquely determining behavior == gold `str(self.value)`. No axioms consumed (region empty); the changed conversion is modeled DEEPLY as `pyStr` (A-reference), validated by G-AX.

same_spec: all 9 files (atk_1..7, atk_echo, atk_pos) return True vs gold Solution.lean (spec regions lines 1-40 byte-identical; only impl+proof edited).

ATTACK BATTERY (8 same-spec wrong/variant impls + positive control), verified concurrently (≤4 jobs) via `bash scripts/lean_verify.sh <f>`:
- atk_1 (control-flow / prepatch bug: returns m.qualifiedName) -> exit 1, `rfl failed` (free-var inequality). PREPATCH BUG REPRODUCED (matches Solution_prepatch.lean; issue 'MyChoice.FIRST_CHOICE' != 'first').
- atk_2 (partial-domain: correct on .text, returns "" on .num) -> exit 1, unsolved goals.
- atk_3 (boundary: (pyStr m.value) ++ "!") -> exit 1, unsolved goals.
- atk_4 (control-flow-effect: .text->s, .num->qualifiedName) -> exit 1, unsolved goals.
- atk_5 (constant "") -> exit 1, unsolved goals.
- atk_6 (ungrounded-oracle echo: qualifiedName ++ pyStr m.value, extra prefix) -> exit 1, unsolved goals.
- atk_7 (num branch negated: toString (-n)) -> exit 1, unsolved goals.
All 7 failures are GENUINE unsolved/false goals (grep confirmed 'error: rfl failed' / 'error: unsolved goals'), not tactic-syntax errors.

### CLOSERS (only gold-equivalent impls close):
- atk_echo (gold behavior via let-binding: `let s := pyStr m.value; return s`) -> lean_verify exit 0; `#print axioms correct_memberStr` -> 'does not depend on any axioms' (clean).
- atk_pos (positive control, exact gold impl) -> exit 0; clean axioms.

MANDATORY RESOLVE (step 2): atk_echo is the ONLY *attack* that closes with clean axioms => materialized its faithful patch (= gold patch, since it implements `str(self.value)`) and RAN it through the official harness: run_resolve('django__django-11964', echo_patch) -> RESOLVED=True, note='resolved'. A resolving echo is NOT a weakness (per 2026-08-06 G-PANEL-1 / eq policy). No verifying attack has a non-resolving faithful patch => spec NOT broken.

G-AX A-reference audit: `python3 axiom_check.py` -> exit 0, 'G-AX OK: pyStr == str(value) on all probes (seed=11964)'. pyStr(.text s)=s mirrors CPython str(str) (identity); pyStr(.num n)=toString n mirrors CPython str(int) incl negatives/zero/large. Correspondence to real callee `str(self.value)` holds on the modeled int/str domain.

refinement.md audit: 3 legs — row1 R (member<->EnumMember, .value<->MemberValue), row2 A-reference (pyStr == str(self.value), validated by G-AX, NOT axiomatized), row3 I (return). No kind-3 (changed-inexpressible) legs. A-reference correspondence sound.

CONCLUSION: no closing-clean-axiom impl has a materialized faithful patch that fails to resolve. verify => correct holds for this bundle. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real callee): NO defect found. Modeled function is post-patch django.db.models.enums.Choices.__str__(self) = str(self.value) (verified against enums.py, which carries the gold patch). Spec: problem_spec_memberStr m result := (result = pyStr m.value), with pyStr(.text s)=s and pyStr(.num n)=toString n. This is an exact equality mirroring the real callee, not an over-strengthening.

Verification performed:
- lean_verify.sh on Solution.lean: exit 0 (compiles, no sorry).
- #print axioms correct_memberStr => 'does not depend on any axioms' (no sorryAx; proof is genuine, via rfl).
- same_spec(Solution.lean, Solution_prepatch.lean) = True; region_hashes match meta.json exactly (spec_view 59a52c0e...). Spec region byte-identical.
- Empirical real-callee check in django_gold: IntegerChoices members str()==str(value)=decimal; TextChoices members str()==str(value)=identity; MRO (Suit: int before Choices; Year: str before Choices) does NOT bypass Choices.__str__ (bound method Choices.__str__). __empty__ sentinel does not create a member whose str diverges.
- Re-ran conformance_check.py: 120016 inputs, 0 disagreements (shadow str(value) vs independent post-patch enum reconstruction). Re-ran axiom_check.py: pyStr == str(value) on 100k+ probes.
- Lean Int.toString == Python str(int) at boundaries (0, negatives, -1e12, negSucc), including '-' for negatives.

The modeled value domain (text/int) is exactly the two value kinds IntegerChoices/TextChoices carry in the F2P enums; no restriction hides a divergence. The spec pins precisely the real repo output for every input — no diverging input exists. Spec is faithful, not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec(a,p,lean_backend) => True), so the solver-facing spec view is fully pinned.

Gold edit: add `Choices.__str__` returning `str(self.value)` (django/db/models/enums.py) so str(member) renders the underlying value instead of the inherited Enum.__str__ 'ClassName.NAME'.

The public problem_statement ALREADY fully discloses the required behavior: it shows the failing assertion `'MyChoice.FIRST_CHOICE' != 'first'`, states str(member) must equal the underlying value ('first'), and diagnoses that __str__ doesn't return the value property. Both the buggy pre-patch result ('ClassName.NAME') and the desired result (the value) are literally in the public statement.

Spec-view content vs problem_statement:
- postcondition `problem_spec_memberStr m result := result = pyStr m.value` pins exactly the publicly-stated 'str = underlying value' behavior — derivable directly from the problem_statement's assertion. No leak.
- `EnumMember.qualifiedName` models the pre-patch 'ClassName.NAME' string, which the problem_statement shows verbatim ('MyChoice.FIRST_CHOICE'). No leak.
- `pyStr` (.text s => s ; .num n => toString n) encodes standard CPython str() on str/int — general library semantics, not gold-edit-specific. No leak.
- Nothing in the frozen Solution.lean region names the __str__ method, the Choices class, the file path, or `return str(self.value)`. The gold EDIT itself is not disclosed beyond what problem_statement makes trivially reconstructable.

On refinement.md/mapping.md: these do quote the gold verbatim (`def __str__(self): return str(self.value)`, `Choices.__str__`, django/db/models/enums.py path). But (a) they are construction/audit docs, not the solver-facing spec view, and the mechanical G-LEAK screen (gates/leak.py -> leakage.screen) only screens bundle.solution_src() against problem_statement — not these docs; treating them as leaks would fail every bundle by definition; and (b) even so they reveal nothing the public problem_statement doesn't already make derivable. Per scope, leakage is judged against public problem_statement (NOT hints_text). No leakage found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
