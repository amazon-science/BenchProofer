# P2 adversarial audit — django__django-14915

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `result = some (valueHash m.val)` is a TOTAL equality and `valueHash` is opaque (no derivable properties), so `correct_choiceValueHash` closes IFF the impl equals `some (valueHash m.val)` for all m — i.e. exactly the gold behavior. Every deviation reduces to an unprovable goal, so NO closing-but-non-resolving impl exists; the `patches` map is therefore empty (nothing closed to materialize).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,10 +59,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
-  -- the digest is the standard digest of the wrapped value; the accompanying
-  -- model object is not consulted
-  return some (valueHash m.val)
+def implementation_choiceValueHash (_m : ChoiceValue) : Option Int := Id.run do
+  -- ATTACK (prepatch bug): no digest supplied, wrapper unhashable
+  return none
 -- impl-end
 
 -- proof-start
@@ -71,5 +70,6 @@
       problem_spec_choiceValueHash m (implementation_choiceValueHash m) := by
   intro m
   unfold problem_spec_choiceValueHash implementation_choiceValueHash
+  simp
   rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,9 +60,10 @@
 
 -- impl-start
 def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
-  -- the digest is the standard digest of the wrapped value; the accompanying
-  -- model object is not consulted
-  return some (valueHash m.val)
+  -- ATTACK (frame violation): digest depends on the model object presence
+  match m.inst with
+  | none => return none
+  | some _ => return some (valueHash m.val)
 -- impl-end
 
 -- proof-start
@@ -71,5 +72,7 @@
       problem_spec_choiceValueHash m (implementation_choiceValueHash m) := by
   intro m
   unfold problem_spec_choiceValueHash implementation_choiceValueHash
-  rfl
+  cases m.inst with
+  | none => simp
+  | some _ => rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,10 +59,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
-  -- the digest is the standard digest of the wrapped value; the accompanying
-  -- model object is not consulted
-  return some (valueHash m.val)
+def implementation_choiceValueHash (_m : ChoiceValue) : Option Int := Id.run do
+  -- ATTACK (ungrounded oracle): constant digest, ignores the input value
+  return some (valueHash 0)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,9 +60,8 @@
 
 -- impl-start
 def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
-  -- the digest is the standard digest of the wrapped value; the accompanying
-  -- model object is not consulted
-  return some (valueHash m.val)
+  -- ATTACK (boundary): unhashable at val = 0, else correct
+  if m.val = 0 then return none else return some (valueHash m.val)
 -- impl-end
 
 -- proof-start
@@ -71,5 +70,5 @@
       problem_spec_choiceValueHash m (implementation_choiceValueHash m) := by
   intro m
   unfold problem_spec_choiceValueHash implementation_choiceValueHash
-  rfl
+  by_cases h : m.val = 0 <;> simp [h]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,9 +60,8 @@
 
 -- impl-start
 def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
-  -- the digest is the standard digest of the wrapped value; the accompanying
-  -- model object is not consulted
-  return some (valueHash m.val)
+  -- ATTACK (transform): digest of a shifted value, not the value itself
+  return some (valueHash (m.val + 1))
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,9 +60,8 @@
 
 -- impl-start
 def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
-  -- the digest is the standard digest of the wrapped value; the accompanying
-  -- model object is not consulted
-  return some (valueHash m.val)
+  -- ATTACK (partial domain): only positive values yield a digest
+  if m.val > 0 then return some (valueHash m.val) else return none
 -- impl-end
 
 -- proof-start
@@ -71,5 +70,5 @@
       problem_spec_choiceValueHash m (implementation_choiceValueHash m) := by
   intro m
   unfold problem_spec_choiceValueHash implementation_choiceValueHash
-  rfl
+  by_cases h : m.val > 0 <;> simp [h]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,9 +60,8 @@
 
 -- impl-start
 def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
-  -- the digest is the standard digest of the wrapped value; the accompanying
-  -- model object is not consulted
-  return some (valueHash m.val)
+  -- ATTACK: returns negated digest
+  return some (- valueHash m.val)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Making a select-widget choice-value wrapper usable as a dictionary key / set
member.

A choice-value wrapper bundles a plain choice value together with the model
object it was produced from. Downstream user code commonly tests membership of
such a wrapper in a mapping or a set (e.g. `if value in {1: [...]}`), which
requires the wrapper to expose a hash digest.

Two facets are pinned here:

  * the wrapper IS usable as a key — obtaining its digest succeeds (it does not
    fail the way an un-keyable object would);
  * the digest is a deterministic function of the wrapped *value* alone — it is
    derived from the plain value and does NOT depend on the accompanying model
    object. Two wrappers that carry the same value therefore share a digest,
    whatever model objects (or absence thereof) they were built from.
-/

-- axioms-start
-- The wrapped value's own digest is computed by the standard, unchanged digest
-- operation for plain values — a deterministic function of the value. It is an
-- UNCHANGED callee the modeled behavior invokes (not the operation under
-- specification), so it is declared `opaque` (signature only) and used
-- identically in the spec and the implementation. The proof consumes no property
-- of it, so no `_prop` axiom is declared here; if the proof agent gets stuck it
-- may add one via the axiom-propose loop.
opaque valueHash : Int → Int
-- axioms-end

-- pure-start
/-- An opaque tag standing for an accompanying model object. Only its presence
or absence is ever observed by the modeled behavior; its content is irrelevant
to the digest, which is exactly the point being specified. -/
opaque ModelInstance : Type

/-- A choice-value wrapper: a plain value `val` together with the model object
`inst` it was produced from (absent when built without one). -/
structure ChoiceValue where
  val : Int
  inst : Option ModelInstance
-- pure-end

-- post-conditions-start
/-- The digest of a choice-value wrapper succeeds and equals the standard digest
of the wrapped value `m.val` alone.

Directive 5 (frame): the result is pinned entirely to `m.val`. The accompanying
model object `m.inst` is a read-only input the result must NOT depend on, so it
does not appear on the right-hand side — hence wrappers sharing a value share a
digest regardless of their model object. The `some` constructor records that the
digest is produced at all (a wrapper that could not be used as a key would have
no digest to report). -/
def problem_spec_choiceValueHash (m : ChoiceValue) (result : Option Int) : Prop :=
  result = some (valueHash m.val)
-- post-conditions-end

-- impl-start
def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
  -- the digest is the standard digest of the wrapped value; the accompanying
  -- model object is not consulted
  return some (valueHash m.val)
-- impl-end

-- proof-start
theorem correct_choiceValueHash :
    ∀ (m : ChoiceValue),
      problem_spec_choiceValueHash m (implementation_choiceValueHash m) := by
  intro m
  unfold problem_spec_choiceValueHash implementation_choiceValueHash
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (byte-identical spec confirmed: same_spec=True for all 7 attacks via swebench_unified.markers.same_spec + get_backend('lean')). Command per file: `bash scripts/lean_verify.sh <file>`, run concurrently in batches of ≤4.

POSITIVE CONTROL: pos_control.lean (gold impl `return some (valueHash m.val)`) -> exit 0 (verifies, no sorry). `#print axioms correct_choiceValueHash` -> 'does not depend on any axioms' (CLEAN, no sorryAx).

7 DISTINCT same-spec wrong impls, all FAIL to close (none has a clean-axiom closing proof, so per protocol NONE required a resolve run):
- atk_1 (prepatch bug, returns `none` = unhashable): exit 1, goal `⊢ False`. Reproduces the exact prepatch TypeError bug.
- atk_2 (frame violation, digest depends on m.inst presence): exit 1, case none goal `⊢ False`.
- atk_3 (ungrounded oracle echo, constant `valueHash 0`): exit 1, `(some (valueHash 0)).run = some (valueHash m.val)` — non-defeq opaque, unprovable.
- atk_4 (boundary, unhashable at val=0): exit 1, case pos goal `⊢ False`.
- atk_5 (transform/off-by-one, `valueHash (m.val+1)`): exit 1, non-defeq opaque equality, unprovable.
- atk_6 (partial domain, only val>0 hashable): exit 1, case neg goal `⊢ False`.
- atk_7 (wrong function of value, `-valueHash m.val`): exit 1, non-defeq opaque equality, unprovable.

Genuine proof-closing attempts were made in each (simp/rfl/cases/by_cases) — the goals are genuinely unprovable, not merely unattempted. verify <=> gold-equivalent behavior; no verify-but-not-resolve impl exists.

A-LEG / refinement.md AUDIT: One op (#1), tagged R + A-reference. No I ops, no kind-3. The R leg (Option carrier: hashable->some, unhashable->none) is mechanically covered. The A-reference `valueHash` = unchanged builtin `hash(self.value)` — the proof consumes no property of it (spec equates result syntactically to `valueHash m.val`), so it is correctly an A-reference, NOT a consumed axiom, and NO dead `axiom` is shipped (confirmed: positive control depends on NO axioms). A-reference correspondence to the real callee (hash(wrapper)==hash(value), independent of inst) is validated by the bundle's axiom_check.py per prior verdict.md role-3 (50014 inputs, exit 0 on the patched worktree). Legs clean.

Note: bundle final_status is 'blocked' on its own recorded G-AX fail, which prior verdict.md attributes to an in-container patch-application infra bug (axiom_check ran against pre-patch callee); this does not affect the G-EQ refinement-fidelity verdict here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `result = some (valueHash m.val)` is a TOTAL equality and `valueHash` is opaque (no derivable properties), so `correct_choiceValueHash` closes IFF the impl equals `some (valueHash m.val)` for all m — i.e. exactly the gold behavior. Every deviation reduces to an unprovable goal, so NO closing-but-non-resolving impl exists; the `patches` map is therefore empty (nothing closed to materialize).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Making a select-widget choice-value wrapper usable as a dictionary key / set
member.

A choice-value wrapper bundles a plain choice value together with the model
object it was produced from. Downstream user code commonly tests membership of
such a wrapper in a mapping or a set (e.g. `if value in {1: [...]}`), which
requires the wrapper to expose a hash digest.

Two facets are pinned here:

  * the wrapper IS usable as a key — obtaining its digest succeeds (it does not
    fail the way an un-keyable object would);
  * the digest is a deterministic function of the wrapped *value* alone — it is
    derived from the plain value and does NOT depend on the accompanying model
    object. Two wrappers that carry the same value therefore share a digest,
    whatever model objects (or absence thereof) they were built from.
-/

-- axioms-start
-- The wrapped value's own digest is computed by the standard, unchanged digest
-- operation for plain values — a deterministic function of the value. It is an
-- UNCHANGED callee the modeled behavior invokes (not the operation under
-- specification), so it is declared `opaque` (signature only) and used
-- identically in the spec and the implementation. The proof consumes no property
-- of it, so no `_prop` axiom is declared here; if the proof agent gets stuck it
-- may add one via the axiom-propose loop.
opaque valueHash : Int → Int
-- axioms-end

-- pure-start
/-- An opaque tag standing for an accompanying model object. Only its presence
or absence is ever observed by the modeled behavior; its content is irrelevant
to the digest, which is exactly the point being specified. -/
opaque ModelInstance : Type

/-- A choice-value wrapper: a plain value `val` together with the model object
`inst` it was produced from (absent when built without one). -/
structure ChoiceValue where
  val : Int
  inst : Option ModelInstance
-- pure-end

-- post-conditions-start
/-- The digest of a choice-value wrapper succeeds and equals the standard digest
of the wrapped value `m.val` alone.

Directive 5 (frame): the result is pinned entirely to `m.val`. The accompanying
model object `m.inst` is a read-only input the result must NOT depend on, so it
does not appear on the right-hand side — hence wrappers sharing a value share a
digest regardless of their model object. The `some` constructor records that the
digest is produced at all (a wrapper that could not be used as a key would have
no digest to report). -/
def problem_spec_choiceValueHash (m : ChoiceValue) (result : Option Int) : Prop :=
  result = some (valueHash m.val)
-- post-conditions-end

-- impl-start
def implementation_choiceValueHash (m : ChoiceValue) : Option Int := Id.run do
  -- the digest is the standard digest of the wrapped value; the accompanying
  -- model object is not consulted
  return some (valueHash m.val)
-- impl-end

-- proof-start
theorem correct_choiceValueHash :
    ∀ (m : ChoiceValue),
      problem_spec_choiceValueHash m (implementation_choiceValueHash m) := by
  intro m
  unfold problem_spec_choiceValueHash implementation_choiceValueHash
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (byte-identical spec confirmed: same_spec=True for all 7 attacks via swebench_unified.markers.same_spec + get_backend('lean')). Command per file: `bash scripts/lean_verify.sh <file>`, run concurrently in batches of ≤4.

POSITIVE CONTROL: pos_control.lean (gold impl `return some (valueHash m.val)`) -> exit 0 (verifies, no sorry). `#print axioms correct_choiceValueHash` -> 'does not depend on any axioms' (CLEAN, no sorryAx).

7 DISTINCT same-spec wrong impls, all FAIL to close (none has a clean-axiom closing proof, so per protocol NONE required a resolve run):
- atk_1 (prepatch bug, returns `none` = unhashable): exit 1, goal `⊢ False`. Reproduces the exact prepatch TypeError bug.
- atk_2 (frame violation, digest depends on m.inst presence): exit 1, case none goal `⊢ False`.
- atk_3 (ungrounded oracle echo, constant `valueHash 0`): exit 1, `(some (valueHash 0)).run = some (valueHash m.val)` — non-defeq opaque, unprovable.
- atk_4 (boundary, unhashable at val=0): exit 1, case pos goal `⊢ False`.
- atk_5 (transform/off-by-one, `valueHash (m.val+1)`): exit 1, non-defeq opaque equality, unprovable.
- atk_6 (partial domain, only val>0 hashable): exit 1, case neg goal `⊢ False`.
- atk_7 (wrong function of value, `-valueHash m.val`): exit 1, non-defeq opaque equality, unprovable.

Genuine proof-closing attempts were made in each (simp/rfl/cases/by_cases) — the goals are genuinely unprovable, not merely unattempted. verify <=> gold-equivalent behavior; no verify-but-not-resolve impl exists.

A-LEG / refinement.md AUDIT: One op (#1), tagged R + A-reference. No I ops, no kind-3. The R leg (Option carrier: hashable->some, unhashable->none) is mechanically covered. The A-reference `valueHash` = unchanged builtin `hash(self.value)` — the proof consumes no property of it (spec equates result syntactically to `valueHash m.val`), so it is correctly an A-reference, NOT a consumed axiom, and NO dead `axiom` is shipped (confirmed: positive control depends on NO axioms). A-reference correspondence to the real callee (hash(wrapper)==hash(value), independent of inst) is validated by the bundle's axiom_check.py per prior verdict.md role-3 (50014 inputs, exit 0 on the patched worktree). Legs clean.

Note: bundle final_status is 'blocked' on its own recorded G-AX fail, which prior verdict.md attributes to an in-container patch-application infra bug (axiom_check ran against pre-patch callee); this does not affect the G-EQ refinement-fidelity verdict here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Role: faithfulness-break (spec-too-strong / drift). MECHANICAL CHECKS ALL PASS: (1) Solution.lean compiles via scripts/lean_verify.sh, exit 0, no sorry. (2) `#print axioms correct_choiceValueHash` => 'does not depend on any axioms' (real proof, not sorryAx). (3) markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True (spec region byte-identical; only impl/proof regions differ).

REAL REPO CONFIRMED: @ base, django/forms/models.py:1169-1170 post-patch adds `def __hash__(self): return hash(self.value)` to ModelChoiceIteratorValue (which defines value-based __eq__ at 1172-1175).

SPEC: problem_spec_choiceValueHash m result := result = some (valueHash m.val); valueHash : Int -> Int opaque (= builtin hash on the int value); m.inst : Option ModelInstance opaque.

FAITHFULNESS across the modeled domain (m.val : Int, m.inst : Option ModelInstance):
1. Hashability (`some _` always): real post-patch __hash__ is always defined and value is an int (model pk) => hash() never raises TypeError. Spec always yields `some`. Match on every input.
2. Frame / independence from m.inst: real __hash__ reads only self.value, never self.instance (F2P assertion hash(value_1)==hash(ModelChoiceIteratorValue(pk,None)) confirms). Spec RHS omits m.inst entirely. Match.
3. Digest value: routed through opaque valueHash m.val, used identically in spec and impl; numeric hash(int) is NOT pinned (opaque) so no over-strong numeric constraint. Match.

Searched for a diverging input: (a) a value where real hash() raises but spec says `some` -> none, CPython ints are always hashable; (b) an input where inst changes the real digest but spec ignores it -> none, inst never read; (c) an input where the spec over-constrains the digest -> none, digest left opaque. The Int-only domain for val is a documented, faithful representation choice (mapping.md/refinement.md scope val to a model pk int), not a drift. No diverging input exists. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over the lean spec view) PASSES: no diff markers, no reproduced gold-patch line, no patched file/module path, no narration keyword, no spec-view identifier or comment embedding a patched repo symbol. Semantic review confirms NO leakage beyond the public problem_statement:

- problem_statement already reveals the full required behavior: 'ModelChoiceIteratorValue is not hashable' / 'TypeError: unhashable type' and the object being used as a dict key / set member (`value in {1: [...]}`). Making it hashable is therefore public.
- The only patched def/class symbol extracted from the gold patch is `hash` (from `__hash__`, underscores stripped), which is already public via 'hashable'/'unhashable' in the problem statement — the screen correctly skips it.
- Spec-view uses neutral, non-localizing names (`ChoiceValue`, `valueHash`, `problem_spec_choiceValueHash`); none reproduces the gold line `return hash(self.value)` nor names `ModelChoiceIteratorValue` or the file `django/forms/models.py`.
- The docstring's substantive refinement (digest depends on the wrapped value alone, not the model object) is derivable from public facts — the class visibly defines `__eq__` by value and Python requires `__hash__` consistency with `__eq__` — not lifted from the hidden hints_text (`def __hash__(self): return hash(self.value)`).
- Comments are abstract behavior descriptions; no bug/fix/patch narration, no pre/post-patch language.

Spec region byte-identity: markers.same_spec is available and the spec view projects cleanly (impl/proof elided), consistent with a well-formed spec region. No line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
