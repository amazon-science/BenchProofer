# P2 adversarial audit — django__django-11138

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,8 +60,8 @@
 def implementation_tzConvertSql
     (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do
   let mut field := fieldName
-  if useTz && connTz != tzname then
-    field := convertTzFragment field connTz tzname
+  if useTz then
+    field := convertTzFragment field "UTC" tzname
   return field
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
 def implementation_tzConvertSql
     (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do
   let mut field := fieldName
-  if useTz && connTz != tzname then
+  if useTz then
     field := convertTzFragment field connTz tzname
   return field
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
 def implementation_tzConvertSql
     (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do
   let mut field := fieldName
-  if useTz && connTz != tzname then
+  if useTz && connTz == tzname then
     field := convertTzFragment field connTz tzname
   return field
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,8 +60,7 @@
 def implementation_tzConvertSql
     (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do
   let mut field := fieldName
-  if useTz && connTz != tzname then
-    field := convertTzFragment field connTz tzname
+  field := convertTzFragment field connTz tzname
   return field
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
     (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do
   let mut field := fieldName
   if useTz && connTz != tzname then
-    field := convertTzFragment field connTz tzname
+    field := convertTzFragment field tzname connTz
   return field
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
 def implementation_tzConvertSql
     (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do
   let mut field := fieldName
-  if useTz && connTz != tzname then
+  if connTz != tzname then
     field := convertTzFragment field connTz tzname
   return field
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the SQL expression that presents a stored datetime column in a target
time zone, for a backend that keeps datetimes as naive local values.

The builder is given:

  * a flag saying whether time-zone–aware processing is active at all;
  * the name of the time zone the stored values are recorded in (the source
    time zone of the connection);
  * the name of the target time zone the caller wants the value expressed in;
  * the SQL expression naming the column.

When time-zone–aware processing is active AND the source and target time zones
differ, the column expression is wrapped in a conversion from the source time
zone to the target time zone, producing
`CONVERT_TZ(<column>, '<source>', '<target>')`.

In every other case — time-zone processing inactive, or the source and target
time zones coinciding — the column expression is returned unchanged (no
conversion is emitted, so the value is presented in the time zone it is already
recorded in).
-/

-- axioms-start
-- No unchanged outside callee is consumed: the time-zone flag and the source /
-- target time-zone names enter as plain data, and the only operation performed
-- is the construction of the SQL conversion fragment, modeled directly as string
-- concatenation. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The conversion fragment that re-expresses a column from a source time zone in
a target time zone: `CONVERT_TZ(<column>, '<source>', '<target>')`. -/
def convertTzFragment (fieldName srcTz dstTz : String) : String :=
  "CONVERT_TZ(" ++ fieldName ++ ", '" ++ srcTz ++ "', '" ++ dstTz ++ "')"
-- pure-end

-- post-conditions-start
/-- The produced SQL expression is fully pinned to the inputs:

  * when time-zone processing is active and the source and target time zones
    differ, it is exactly the conversion fragment from the source to the target
    time zone wrapping the original column expression;
  * otherwise it is exactly the original column expression, unchanged.

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_tzConvertSql
    (useTz : Bool) (connTz tzname fieldName : String) (result : String) : Prop :=
  (useTz = true ∧ connTz ≠ tzname →
      result = convertTzFragment fieldName connTz tzname) ∧
  (¬ (useTz = true ∧ connTz ≠ tzname) →
      result = fieldName)
-- post-conditions-end

-- impl-start
def implementation_tzConvertSql
    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do
  let mut field := fieldName
  if useTz && connTz != tzname then
    field := convertTzFragment field connTz tzname
  return field
-- impl-end

-- proof-start
theorem correct_tzConvertSql :
    ∀ (useTz : Bool) (connTz tzname fieldName : String),
      problem_spec_tzConvertSql useTz connTz tzname fieldName
        (implementation_tzConvertSql useTz connTz tzname fieldName) := by
  intro useTz connTz tzname fieldName
  unfold problem_spec_tzConvertSql implementation_tzConvertSql
  simp only [Id.run, bind, pure]
  constructor
  · rintro ⟨hu, hn⟩
    have h : (useTz && connTz != tzname) = true := by
      simp [hu, bne_iff_ne, hn]
    simp [h]
  · intro hcon
    by_cases h : (useTz && connTz != tzname) = true
    · rw [Bool.and_eq_true, bne_iff_ne] at h
      exact absurd h hcon
    · simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_tzConvertSql is a TOTAL functional specification: the two postcondition conjuncts partition the input space on P:=(useTz=true ∧ connTz≠tzname) vs ¬P, each pinning `result` to an exact string (convertTzFragment fieldName connTz tzname / fieldName). Any impl differing on any input yields a false postcondition ⇒ no closing proof possible.

Same-spec: all 6 attacks + positive control return same_spec=True (axioms/pure/pre/post byte-identical; only impl region edited).

Verification (scripts/lean_verify.sh, 300s, run concurrently ≤4):
- pos.lean (gold Solution.lean): EXIT 0 (verifies, no sorry). #print axioms correct_tzConvertSql ⇒ depends on axioms: [propext] (CLEAN).
- atk_1 prepatch bug (literal "UTC" source, no != guard): EXIT 1 — unsolved goals `useTz=true → convertTzFragment fieldName "UTC" tzname = fieldName`.
- atk_2 partial-domain (drop connTz!=tzname guard): EXIT 1.
- atk_3 boundary (flip != → ==): EXIT 1 — unsolved goal `useTz=true → connTz=tzname → convertTzFragment fieldName connTz tzname = fieldName`.
- atk_4 control-flow-effect (convert unconditionally): EXIT 1.
- atk_5 swapped src/dst args (convertTzFragment field tzname connTz): EXIT 1.
- atk_6 ungrounded/flag-drop (guard = connTz!=tzname, ignore useTz): EXIT 1.
All failures are genuine `unsolved goals`/`simp made no progress` proof failures on unprovable symbolic-string equalities — NOT timeouts (124) or syntax errors.

No wrong impl closed with clean axioms ⇒ protocol step 2 (materialize + run faithful patch through run_resolve) is not triggered (patches={}); nothing to falsify.

Refinement audit: 4 legs, all I/R (init=I, guard=R type-refinement Bool/String bijection, %-format→String concat=I, return=I). meta.json axioms=[] and deep_model_references=[] — NO A-legs, so A-leg/deep-model correspondence audit is vacuous. No kind-3 legs. R/I correspondence to the real patched mysql._convert_field_to_tz is covered by the bundle's conformance_check.py (differential test vs live patched method).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the SQL expression that presents a stored datetime column in a target
time zone, for a backend that keeps datetimes as naive local values.

The builder is given:

  * a flag saying whether time-zone–aware processing is active at all;
  * the name of the time zone the stored values are recorded in (the source
    time zone of the connection);
  * the name of the target time zone the caller wants the value expressed in;
  * the SQL expression naming the column.

When time-zone–aware processing is active AND the source and target time zones
differ, the column expression is wrapped in a conversion from the source time
zone to the target time zone, producing
`CONVERT_TZ(<column>, '<source>', '<target>')`.

In every other case — time-zone processing inactive, or the source and target
time zones coinciding — the column expression is returned unchanged (no
conversion is emitted, so the value is presented in the time zone it is already
recorded in).
-/

-- axioms-start
-- No unchanged outside callee is consumed: the time-zone flag and the source /
-- target time-zone names enter as plain data, and the only operation performed
-- is the construction of the SQL conversion fragment, modeled directly as string
-- concatenation. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The conversion fragment that re-expresses a column from a source time zone in
a target time zone: `CONVERT_TZ(<column>, '<source>', '<target>')`. -/
def convertTzFragment (fieldName srcTz dstTz : String) : String :=
  "CONVERT_TZ(" ++ fieldName ++ ", '" ++ srcTz ++ "', '" ++ dstTz ++ "')"
-- pure-end

-- post-conditions-start
/-- The produced SQL expression is fully pinned to the inputs:

  * when time-zone processing is active and the source and target time zones
    differ, it is exactly the conversion fragment from the source to the target
    time zone wrapping the original column expression;
  * otherwise it is exactly the original column expression, unchanged.

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_tzConvertSql
    (useTz : Bool) (connTz tzname fieldName : String) (result : String) : Prop :=
  (useTz = true ∧ connTz ≠ tzname →
      result = convertTzFragment fieldName connTz tzname) ∧
  (¬ (useTz = true ∧ connTz ≠ tzname) →
      result = fieldName)
-- post-conditions-end

-- impl-start
def implementation_tzConvertSql
    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do
  let mut field := fieldName
  if useTz && connTz != tzname then
    field := convertTzFragment field connTz tzname
  return field
-- impl-end

-- proof-start
theorem correct_tzConvertSql :
    ∀ (useTz : Bool) (connTz tzname fieldName : String),
      problem_spec_tzConvertSql useTz connTz tzname fieldName
        (implementation_tzConvertSql useTz connTz tzname fieldName) := by
  intro useTz connTz tzname fieldName
  unfold problem_spec_tzConvertSql implementation_tzConvertSql
  simp only [Id.run, bind, pure]
  constructor
  · rintro ⟨hu, hn⟩
    have h : (useTz && connTz != tzname) = true := by
      simp [hu, bne_iff_ne, hn]
    simp [h]
  · intro hcon
    by_cases h : (useTz && connTz != tzname) = true
    · rw [Bool.and_eq_true, bne_iff_ne] at h
      exact absurd h hcon
    · simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_tzConvertSql is a TOTAL functional specification: the two postcondition conjuncts partition the input space on P:=(useTz=true ∧ connTz≠tzname) vs ¬P, each pinning `result` to an exact string (convertTzFragment fieldName connTz tzname / fieldName). Any impl differing on any input yields a false postcondition ⇒ no closing proof possible.

Same-spec: all 6 attacks + positive control return same_spec=True (axioms/pure/pre/post byte-identical; only impl region edited).

Verification (scripts/lean_verify.sh, 300s, run concurrently ≤4):
- pos.lean (gold Solution.lean): EXIT 0 (verifies, no sorry). #print axioms correct_tzConvertSql ⇒ depends on axioms: [propext] (CLEAN).
- atk_1 prepatch bug (literal "UTC" source, no != guard): EXIT 1 — unsolved goals `useTz=true → convertTzFragment fieldName "UTC" tzname = fieldName`.
- atk_2 partial-domain (drop connTz!=tzname guard): EXIT 1.
- atk_3 boundary (flip != → ==): EXIT 1 — unsolved goal `useTz=true → connTz=tzname → convertTzFragment fieldName connTz tzname = fieldName`.
- atk_4 control-flow-effect (convert unconditionally): EXIT 1.
- atk_5 swapped src/dst args (convertTzFragment field tzname connTz): EXIT 1.
- atk_6 ungrounded/flag-drop (guard = connTz!=tzname, ignore useTz): EXIT 1.
All failures are genuine `unsolved goals`/`simp made no progress` proof failures on unprovable symbolic-string equalities — NOT timeouts (124) or syntax errors.

No wrong impl closed with clean axioms ⇒ protocol step 2 (materialize + run faithful patch through run_resolve) is not triggered (patches={}); nothing to falsify.

Refinement audit: 4 legs, all I/R (init=I, guard=R type-refinement Bool/String bijection, %-format→String concat=I, return=I). meta.json axioms=[] and deep_model_references=[] — NO A-legs, so A-leg/deep-model correspondence audit is vacuous. No kind-3 legs. R/I correspondence to the real patched mysql._convert_field_to_tz is covered by the bundle's conformance_check.py (differential test vs live patched method).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled callee = mysql DatabaseOperations._convert_field_to_tz (the pure str->str representative the problem statement points at; oracle/sqlite are same-predicate siblings, gold patch fixes all three). Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec = True). Solution.lean compiles clean (lean_verify exit 0) and #print axioms correct_tzConvertSql = [propext] only (no sorryAx — genuine proof).

Faithfulness check vs real patched source (verified worktree):
  if settings.USE_TZ and self.connection.timezone_name != tzname:
      field_name = "CONVERT_TZ(%s, '%s', '%s')" % (field_name, self.connection.timezone_name, tzname)
  return field_name

1. Predicate: `useTz = true ∧ connTz ≠ tzname` matches `USE_TZ and timezone_name != tzname` exactly. Bool<->bool, str<->str, `!=`<->`≠` are identity bijections.
2. Wrap fragment: the Python %-format substitutes the three strings with no coercion, producing byte-for-byte `"CONVERT_TZ(" ++ field ++ ", '" ++ connTz ++ "', '" ++ tzname ++ "')"` = convertTzFragment. Identical.
3. Else branch: returns field_name unchanged = spec's `result = fieldName`. Identical.
4. Totality / None concern resolved at source: base/base.py `timezone_name` cached_property returns `settings.TIME_ZONE` (USE_TZ off), 'UTC' (TIME_ZONE is None), or the configured name — a str in every branch. Whenever the wrap actually fires (useTz=True), connTz is a genuine str, so the String model is total-faithful. When useTz=False the output is fieldName regardless of connTz, so no None value is observable.

Spec pins result uniquely in BOTH branches (total functional spec, no free output), so it cannot be too strong relative to the real callee: it equals the callee pointwise. Searched for any diverging (useTz, connTz, tzname, fieldName) — none exists. conformance_check.py could not be executed here (django not in this env) but its shadow is a verbatim transliteration and the equivalence is proven by inspection above. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = Solution.lean (spec `problem_spec_tzConvertSql`, `convertTzFragment`, doc comments). The gold edit has two behavioral components: (1) convert from the *connection's* time zone rather than a hardcoded 'UTC', and (2) skip the conversion entirely when source==target. BOTH are already disclosed explicitly in the PUBLIC problem_statement, not merely hints_text: 'conversion should be from Paris to Paris, instead of UTC to Paris. The conversion should go from the database timezone tz2 to the django app one tz1' and 'when tz1 == tz2, there should be no need to use CONVERT_TZ'. The problem_statement even shows the literal SQL form `CONVERT_TZ(..., 'UTC', 'Europe/Paris')` and links the exact source line. The Solution.lean spec pins result = `CONVERT_TZ(<col>,'<src>','<dst>')` when useTz ∧ src≠tgt, else unchanged — a faithful restatement of behavior fully derivable from the public statement; it reveals nothing beyond it. The gold discriminator (conn tz vs UTC; equal-tz short-circuit) is the *stated problem*, so restating it in the spec is not leakage. Multi-backend/sibling-site detail (oracle/sqlite) that is NOT in the problem_statement lives only in mapping.md/refinement.md, which are not part of the spec view; the modeled mysql spec exposes no such extra. Mechanical lexical G-LEAK screen also passes (hard_failures=[]). No RELAXED_LEAKAGE.md present; not a relaxed bundle. Conclusion: no leak beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
