# P2 adversarial audit — django__django-11477

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl closes correct_capture. The spec problem_spec_capture is a TOTAL FUNCTIONAL EQUALITY pinning result to exactly one value per input in BOTH branches: outcome=none ⇒ result=none; outcome=some sc ⇒ result = some (path.drop sc.consumed, (if named.isEmpty then sc.positionalCaptures else []), named) where named = sc.namedCaptures.filter carriesValue. Any impl closing correct_capture is extensionally equal to gold on every input, so its refined patch would resolve exactly as gold. Concrete divergence witnesses (V:=Nat) via diverge.lean (#eval, exit 0): input sc0 = {consumed:=1, namedCaptures:=[(0,some 7),(1,none)], positionalCaptures:=[some 9]}, path='abc' — GOLD required = (['b','c'], [], [(0,some 7)]). atk1(prepatch, unfiltered named)=[(0,some 7),(1,none)]≠gold's [(0,some 7)]; atk4(negated pred)=[(1,none)]; atk3(consumed+1) leftover=['c']≠['b','c']; atk7(reversed) diverges on multi-elem. input sc1={consumed:=0, namedCaptures:=[(0,none)], positionalCaptures:=[some 5]} — GOLD = (['a','b','c'],[some 5],[]); atk5(positional forced [])=[]≠[some 5]; atk6(positional unconditional)=behaves per guard drop; atk2(always none)≠some(...). Every attack's correct_capture fails with a genuine rfl non-closure error (LHS not def-eq RHS), NOT a syntax error.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,8 +80,7 @@
   let some sc := outcome | return none
   let mut named : List (Nat × Option V) := []
   for entry in sc.namedCaptures do
-    if carriesValue entry then
-      named := named ++ [entry]
+    named := named ++ [entry]
   let positional := if named.isEmpty then sc.positionalCaptures else []
   return some (path.drop sc.consumed, positional, named)
 -- impl-end
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,14 +76,8 @@
 -- impl-start
 def implementation_capture {V : Type}
     (path : List Char) (outcome : Option (ScanOutcome V)) :
-    Option (List Char × List (Option V) × List (Nat × Option V)) := Id.run do
-  let some sc := outcome | return none
-  let mut named : List (Nat × Option V) := []
-  for entry in sc.namedCaptures do
-    if carriesValue entry then
-      named := named ++ [entry]
-  let positional := if named.isEmpty then sc.positionalCaptures else []
-  return some (path.drop sc.consumed, positional, named)
+    Option (List Char × List (Option V) × List (Nat × Option V)) :=
+  none
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
     if carriesValue entry then
       named := named ++ [entry]
   let positional := if named.isEmpty then sc.positionalCaptures else []
-  return some (path.drop sc.consumed, positional, named)
+  return some (path.drop (sc.consumed + 1), positional, named)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,7 @@
   let some sc := outcome | return none
   let mut named : List (Nat × Option V) := []
   for entry in sc.namedCaptures do
-    if carriesValue entry then
+    if ! carriesValue entry then
       named := named ++ [entry]
   let positional := if named.isEmpty then sc.positionalCaptures else []
   return some (path.drop sc.consumed, positional, named)
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,8 +82,7 @@
   for entry in sc.namedCaptures do
     if carriesValue entry then
       named := named ++ [entry]
-  let positional := if named.isEmpty then sc.positionalCaptures else []
-  return some (path.drop sc.consumed, positional, named)
+  return some (path.drop sc.consumed, [], named)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,8 +82,7 @@
   for entry in sc.namedCaptures do
     if carriesValue entry then
       named := named ++ [entry]
-  let positional := if named.isEmpty then sc.positionalCaptures else []
-  return some (path.drop sc.consumed, positional, named)
+  return some (path.drop sc.consumed, sc.positionalCaptures, named)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
   let mut named : List (Nat × Option V) := []
   for entry in sc.namedCaptures do
     if carriesValue entry then
-      named := named ++ [entry]
+      named := entry :: named
   let positional := if named.isEmpty then sc.positionalCaptures else []
   return some (path.drop sc.consumed, positional, named)
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Turning the outcome of scanning a path against a route pattern into the data a
caller consumes: the leftover path, the positional captures, and the named
captures.

Scanning either succeeds or fails. On failure there is no outcome at all. On
success the scan exposes three things:

  * how far into the path it reached (the length of the consumed prefix);
  * the NAMED captures, in declaration order, each paired with an OPTIONAL value
    — a named capture whose segment is OPTIONAL and did not participate in the
    scan carries no value (it is absent), while one that did participate carries
    the captured text;
  * the POSITIONAL captures, each likewise an optional value.

The data handed back is built like this:

  * the leftover path is the portion of the path beyond the consumed prefix;
  * the named-capture mapping lists, in order, exactly the named captures that
    actually carry a value — an absent named capture contributes nothing;
  * the positional captures are reported only when the named-capture mapping is
    empty; when at least one named capture carries a value, no positional
    captures are reported.

So an absent optional named capture neither appears in the named mapping nor
contributes a stray entry: it is simply not there.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The scan itself
-- (pattern search over the path) is taken as already performed: its outcome —
-- consumed length, named captures with their optional values, and positional
-- captures — is supplied as input data (`ScanOutcome`). The logic modeled here
-- only reshapes that data, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The outcome of a successful scan of a path against a route pattern.
* `consumed` — the length of the prefix the scan reached (so the leftover path is
  everything beyond it);
* `namedCaptures` — the named captures in declaration order; each is a name
  (modeled as a `Nat` identity — mapping.md gives the name↔`Nat` bijection) paired
  with an OPTIONAL value (`none` when that capture did not participate);
* `positionalCaptures` — the positional captures, each an optional value. -/
structure ScanOutcome (V : Type) where
  consumed : Nat
  namedCaptures : List (Nat × Option V)
  positionalCaptures : List (Option V)

/-- Whether a named capture carries a value (it participated in the scan). -/
def carriesValue {V : Type} (entry : Nat × Option V) : Bool :=
  entry.2.isSome
-- pure-end

-- post-conditions-start
/-- On a failed scan there is no outcome. On a successful scan the result is the
triple of: the leftover path (everything beyond the consumed prefix), the
positional captures (reported only when the named mapping is empty), and the
named mapping (exactly the named captures that carry a value, in order). Every
component is pinned to the input: nothing is invented, reordered, or left
unconstrained, and absent named captures contribute no entry. -/
def problem_spec_capture {V : Type}
    (path : List Char) (outcome : Option (ScanOutcome V))
    (result : Option (List Char × List (Option V) × List (Nat × Option V))) : Prop :=
  outcome.elim
    (result = none)
    (fun sc =>
      let named := sc.namedCaptures.filter carriesValue
      let positional := if named.isEmpty then sc.positionalCaptures else []
      result = some (path.drop sc.consumed, positional, named))
-- post-conditions-end

-- impl-start
def implementation_capture {V : Type}
    (path : List Char) (outcome : Option (ScanOutcome V)) :
    Option (List Char × List (Option V) × List (Nat × Option V)) := Id.run do
  let some sc := outcome | return none
  let mut named : List (Nat × Option V) := []
  for entry in sc.namedCaptures do
    if carriesValue entry then
      named := named ++ [entry]
  let positional := if named.isEmpty then sc.positionalCaptures else []
  return some (path.drop sc.consumed, positional, named)
-- impl-end

-- proof-start
/-- The `forIn`/`mut` loop in `implementation_capture` appends each entry that
`carriesValue` to the accumulator, in order, leaving the rest untouched. So the
whole loop equals the initial accumulator followed by `xs.filter carriesValue`.
Generalized over the accumulator so the cons step's induction hypothesis applies
to the extended accumulator. -/
theorem capture_loop {V : Type} (xs : List (Nat × Option V))
    (init : List (Nat × Option V)) :
    (forIn (m := Id) xs init (fun entry r =>
      (if carriesValue entry then pure (ForInStep.yield (r ++ [entry]))
       else pure (ForInStep.yield r))))
      = init ++ xs.filter carriesValue := by
  induction xs generalizing init with
  | nil => rw [List.forIn_nil, List.filter_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    by_cases h : carriesValue a <;> simp only [h, if_true, ih, List.filter_cons]
    · simp
    · simp

theorem correct_capture {V : Type} :
    ∀ (path : List Char) (outcome : Option (ScanOutcome V)),
      problem_spec_capture path outcome
        (implementation_capture path outcome) := by
  intro path outcome
  unfold problem_spec_capture implementation_capture
  cases outcome with
  | none => rfl
  | some sc =>
    -- The desugared loop body bridges to `capture_loop`'s clean body after
    -- `simp only [bind]`; rewriting it leaves `init = [] ++ filter …` to settle.
    simp only [Option.elim, Id.run, bind, capture_loop]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 same_spec(gold, atk_i, lean)=True for all 7 attacks AND pos_control (verified via swebench_unified.markers.same_spec + get_backend('lean')).

COMMANDS (from project root): bash scripts/lean_verify.sh <file>. Verifications run concurrently as background jobs (≤4 at a time).

### RESULTS (lean_verify.sh exit codes):
- pos_control.lean: exit 0 (verifies, no sorry). #print axioms correct_capture => 'depends on axioms: [propext, Quot.sound]' (clean, no sorryAx). pos_axioms.lean log confirms.
- atk1 (prepatch bug, unfiltered named — no `if carriesValue`): exit 1, rfl fails. Goal shows unfiltered forIn-loop named vs spec's List.filter carriesValue. = prepatch_reproduced.
- atk2 (partial-domain: always `none`): exit 1, rfl fails at :116 (LHS none-ish vs spec some(...)).
- atk3 (boundary: `path.drop (sc.consumed+1)`): exit 1, rfl fails at :122.
- atk4 (control-flow-effect: negated predicate `! carriesValue`): exit 1, rfl fails at :122.
- atk5 (positional forced `[]`, never fallback): exit 1, rfl fails; goal `some(...,[],named)` vs spec `some(...,if named.isEmpty then positionalCaptures else [],named)`.
- atk6 (ungrounded-oracle echo: report `sc.positionalCaptures` unconditionally, drop `named.isEmpty` guard): exit 1, rfl fails at :121.
- atk7 (control-flow-effect: prepend `entry :: named` — reversed order): exit 1, rfl fails at :122.

All 7 failures are semantic (Tactic `rfl` failed: LHS not definitionally equal to RHS), verified via grep — NOT parse/syntax/unknown-ident errors. Since NO wrong impl closes with clean axioms, there is NO materialized patch to resolve-run (patches={}); the resolve step is only mandated for CLOSING clean-axiom impls, of which there are none.

**REFINEMENT.MD AUDIT:** 4 legs tagged R / I / I / R. NO A-tagged (axiom/deep-reference) legs — the axioms-start/end block correctly declares no opaque callee contract consumed: self.regex.search's outcome is supplied as input data (ScanOutcome), the modeled logic only reshapes it (filter named, choose positional, slice path); axiom_check.py is a skip stub, G-AX skips (consistent with mapping.md 'Callee provenance'). No kind-3 (ungrounded oracle) legs — the changed op `{k:v for k,v in groupdict().items() if v is not None}` is deeply modeled as `namedCaptures.filter carriesValue` (leg 2, I) and `args=() if kwargs else groups()` as the `if named.isEmpty then positionalCaptures else []` decision (leg 3, I), both grounded in the input. Legs 1 & 4 are R (Option/tuple type refinements). Correspondence to real callee holds.

**CONCLUSION:** spec is fully pinned (total functional equality), no divergent-but-closing impl exists; verify⇒correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl closes correct_capture. The spec problem_spec_capture is a TOTAL FUNCTIONAL EQUALITY pinning result to exactly one value per input in BOTH branches: outcome=none ⇒ result=none; outcome=some sc ⇒ result = some (path.drop sc.consumed, (if named.isEmpty then sc.positionalCaptures else []), named) where named = sc.namedCaptures.filter carriesValue. Any impl closing correct_capture is extensionally equal to gold on every input, so its refined patch would resolve exactly as gold. Concrete divergence witnesses (V:=Nat) via diverge.lean (#eval, exit 0): input sc0 = {consumed:=1, namedCaptures:=[(0,some 7),(1,none)], positionalCaptures:=[some 9]}, path='abc' — GOLD required = (['b','c'], [], [(0,some 7)]). atk1(prepatch, unfiltered named)=[(0,some 7),(1,none)]≠gold's [(0,some 7)]; atk4(negated pred)=[(1,none)]; atk3(consumed+1) leftover=['c']≠['b','c']; atk7(reversed) diverges on multi-elem. input sc1={consumed:=0, namedCaptures:=[(0,none)], positionalCaptures:=[some 5]} — GOLD = (['a','b','c'],[some 5],[]); atk5(positional forced [])=[]≠[some 5]; atk6(positional unconditional)=behaves per guard drop; atk2(always none)≠some(...). Every attack's correct_capture fails with a genuine rfl non-closure error (LHS not def-eq RHS), NOT a syntax error.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Turning the outcome of scanning a path against a route pattern into the data a
caller consumes: the leftover path, the positional captures, and the named
captures.

Scanning either succeeds or fails. On failure there is no outcome at all. On
success the scan exposes three things:

  * how far into the path it reached (the length of the consumed prefix);
  * the NAMED captures, in declaration order, each paired with an OPTIONAL value
    — a named capture whose segment is OPTIONAL and did not participate in the
    scan carries no value (it is absent), while one that did participate carries
    the captured text;
  * the POSITIONAL captures, each likewise an optional value.

The data handed back is built like this:

  * the leftover path is the portion of the path beyond the consumed prefix;
  * the named-capture mapping lists, in order, exactly the named captures that
    actually carry a value — an absent named capture contributes nothing;
  * the positional captures are reported only when the named-capture mapping is
    empty; when at least one named capture carries a value, no positional
    captures are reported.

So an absent optional named capture neither appears in the named mapping nor
contributes a stray entry: it is simply not there.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The scan itself
-- (pattern search over the path) is taken as already performed: its outcome —
-- consumed length, named captures with their optional values, and positional
-- captures — is supplied as input data (`ScanOutcome`). The logic modeled here
-- only reshapes that data, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The outcome of a successful scan of a path against a route pattern.
* `consumed` — the length of the prefix the scan reached (so the leftover path is
  everything beyond it);
* `namedCaptures` — the named captures in declaration order; each is a name
  (modeled as a `Nat` identity — mapping.md gives the name↔`Nat` bijection) paired
  with an OPTIONAL value (`none` when that capture did not participate);
* `positionalCaptures` — the positional captures, each an optional value. -/
structure ScanOutcome (V : Type) where
  consumed : Nat
  namedCaptures : List (Nat × Option V)
  positionalCaptures : List (Option V)

/-- Whether a named capture carries a value (it participated in the scan). -/
def carriesValue {V : Type} (entry : Nat × Option V) : Bool :=
  entry.2.isSome
-- pure-end

-- post-conditions-start
/-- On a failed scan there is no outcome. On a successful scan the result is the
triple of: the leftover path (everything beyond the consumed prefix), the
positional captures (reported only when the named mapping is empty), and the
named mapping (exactly the named captures that carry a value, in order). Every
component is pinned to the input: nothing is invented, reordered, or left
unconstrained, and absent named captures contribute no entry. -/
def problem_spec_capture {V : Type}
    (path : List Char) (outcome : Option (ScanOutcome V))
    (result : Option (List Char × List (Option V) × List (Nat × Option V))) : Prop :=
  outcome.elim
    (result = none)
    (fun sc =>
      let named := sc.namedCaptures.filter carriesValue
      let positional := if named.isEmpty then sc.positionalCaptures else []
      result = some (path.drop sc.consumed, positional, named))
-- post-conditions-end

-- impl-start
def implementation_capture {V : Type}
    (path : List Char) (outcome : Option (ScanOutcome V)) :
    Option (List Char × List (Option V) × List (Nat × Option V)) := Id.run do
  let some sc := outcome | return none
  let mut named : List (Nat × Option V) := []
  for entry in sc.namedCaptures do
    if carriesValue entry then
      named := named ++ [entry]
  let positional := if named.isEmpty then sc.positionalCaptures else []
  return some (path.drop sc.consumed, positional, named)
-- impl-end

-- proof-start
/-- The `forIn`/`mut` loop in `implementation_capture` appends each entry that
`carriesValue` to the accumulator, in order, leaving the rest untouched. So the
whole loop equals the initial accumulator followed by `xs.filter carriesValue`.
Generalized over the accumulator so the cons step's induction hypothesis applies
to the extended accumulator. -/
theorem capture_loop {V : Type} (xs : List (Nat × Option V))
    (init : List (Nat × Option V)) :
    (forIn (m := Id) xs init (fun entry r =>
      (if carriesValue entry then pure (ForInStep.yield (r ++ [entry]))
       else pure (ForInStep.yield r))))
      = init ++ xs.filter carriesValue := by
  induction xs generalizing init with
  | nil => rw [List.forIn_nil, List.filter_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    by_cases h : carriesValue a <;> simp only [h, if_true, ih, List.filter_cons]
    · simp
    · simp

theorem correct_capture {V : Type} :
    ∀ (path : List Char) (outcome : Option (ScanOutcome V)),
      problem_spec_capture path outcome
        (implementation_capture path outcome) := by
  intro path outcome
  unfold problem_spec_capture implementation_capture
  cases outcome with
  | none => rfl
  | some sc =>
    -- The desugared loop body bridges to `capture_loop`'s clean body after
    -- `simp only [bind]`; rewriting it leaves `init = [] ++ filter …` to settle.
    simp only [Option.elim, Id.run, bind, capture_loop]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 same_spec(gold, atk_i, lean)=True for all 7 attacks AND pos_control (verified via swebench_unified.markers.same_spec + get_backend('lean')).

COMMANDS (from project root): bash scripts/lean_verify.sh <file>. Verifications run concurrently as background jobs (≤4 at a time).

### RESULTS (lean_verify.sh exit codes):
- pos_control.lean: exit 0 (verifies, no sorry). #print axioms correct_capture => 'depends on axioms: [propext, Quot.sound]' (clean, no sorryAx). pos_axioms.lean log confirms.
- atk1 (prepatch bug, unfiltered named — no `if carriesValue`): exit 1, rfl fails. Goal shows unfiltered forIn-loop named vs spec's List.filter carriesValue. = prepatch_reproduced.
- atk2 (partial-domain: always `none`): exit 1, rfl fails at :116 (LHS none-ish vs spec some(...)).
- atk3 (boundary: `path.drop (sc.consumed+1)`): exit 1, rfl fails at :122.
- atk4 (control-flow-effect: negated predicate `! carriesValue`): exit 1, rfl fails at :122.
- atk5 (positional forced `[]`, never fallback): exit 1, rfl fails; goal `some(...,[],named)` vs spec `some(...,if named.isEmpty then positionalCaptures else [],named)`.
- atk6 (ungrounded-oracle echo: report `sc.positionalCaptures` unconditionally, drop `named.isEmpty` guard): exit 1, rfl fails at :121.
- atk7 (control-flow-effect: prepend `entry :: named` — reversed order): exit 1, rfl fails at :122.

All 7 failures are semantic (Tactic `rfl` failed: LHS not definitionally equal to RHS), verified via grep — NOT parse/syntax/unknown-ident errors. Since NO wrong impl closes with clean axioms, there is NO materialized patch to resolve-run (patches={}); the resolve step is only mandated for CLOSING clean-axiom impls, of which there are none.

**REFINEMENT.MD AUDIT:** 4 legs tagged R / I / I / R. NO A-tagged (axiom/deep-reference) legs — the axioms-start/end block correctly declares no opaque callee contract consumed: self.regex.search's outcome is supplied as input data (ScanOutcome), the modeled logic only reshapes it (filter named, choose positional, slice path); axiom_check.py is a skip stub, G-AX skips (consistent with mapping.md 'Callee provenance'). No kind-3 (ungrounded oracle) legs — the changed op `{k:v for k,v in groupdict().items() if v is not None}` is deeply modeled as `namedCaptures.filter carriesValue` (leg 2, I) and `args=() if kwargs else groups()` as the `if named.isEmpty then positionalCaptures else []` decision (leg 3, I), both grounded in the input. Legs 1 & 4 are R (Option/tuple type refinements). Correspondence to real callee holds.

**CONCLUSION:** spec is fully pinned (total functional equality), no divergent-but-closing impl exists; verify⇒correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function: RegexPattern.match (django/urls/resolvers.py:150-159). Verified against the real base-commit repo at e28671187903: git-show confirms the pre-fix body `kwargs = match.groupdict(); args = () if kwargs else match.groups(); return path[match.end():], args, kwargs` and the gold patch is the one-line dict-comprehension filter `{k:v for k,v in match.groupdict().items() if v is not None}` — matches mapping.md/refinement.md verbatim.

Mechanical checks (all pass): lean_verify Solution.lean -> exit 0 (compiles, no sorry); `#print axioms correct_capture` -> [propext, Quot.sound] only (no sorryAx, proof is real); same_spec(Solution, Solution_prepatch, lean-backend) -> True (spec region byte-identical); prepatch -> exit 1 (its correct_capture cannot close: unfiltered `named` != `filter carriesValue`), confirming the spec discriminates gold from prepatch; conformance_check.py -> checked=120008 disagreements=0, status=pass.

Faithfulness of the modeled boundary examined for over-strength/drift:
1. `if match:` truthiness — a re.Match is always truthy; outcome.elim none<->None, some<->Match. OK.
2. The fix: `{k:v ... if v is not None}` <-> namedCaptures.filter carriesValue, carriesValue = v.isSome <-> `v is not None`. Group names distinct => dict<->ordered assoc-list is lossless and order-preserving (groupdict/comprehension preserve declaration order; List.filter preserves order). OK.
3. `args = () if kwargs else groups()` computed on the FILTERED kwargs <-> `if named.isEmpty then positionalCaptures else []` on filtered named; `not kwargs` <-> `named.isEmpty`. OK — this is the exact post-fix behavior where all-absent-named now falls back to positional.
4. `path[match.end():]` <-> path.drop consumed; both clamp to empty when index>=len; per-code-point List Char. OK.
5. groups() carried opaquely as positionalCaptures (incl. None slots) — the patch never touches groups(), so abstracting the unchanged callee's output as input data is faithful, not a divergence. Confirmed via P4 note that Python groups() includes named groups positionally; model reports whatever groups() yields verbatim.
6. regex.search abstracted as input ScanOutcome (consumed/named/positional) — legitimate: unchanged callee, no engine property consumed by the proof; axiom_check.py is a correct skip stub (G-AX skips).

The post-condition is a TOTAL functional equality pinning result exactly per input in both none and some branches — neither too strong nor too weak relative to the real callee. No realizable input found where the Lean model disagrees with the post-patch RegexPattern.match. Verdict: FAITHFUL.

**Modeled function:** RegexPattern.match (django/urls/resolvers.py:150-159). Verified against the real base-commit repo at e28671187903: git-show confirms the pre-fix body `kwargs = match.groupdict(); args = () if kwargs else match.groups(); return path[match.end():], args, kwargs` and the gold patch is the one-line dict-comprehension filter `{k:v for k,v in match.groupdict().items() if v is not None}` — matches mapping.md/refinement.md verbatim.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `kwargs = match.groupdict()` -> `kwargs = {k: v for k, v in match.groupdict().items() if v is not None}` in django/urls/resolvers.py:156 (RegexPattern.match) — drop named captures whose value is None. Public problem_statement already discloses the topic: 'translate_url() creates an incorrect URL when optional named groups are missing' / 'absent optional arguments'.

Checks performed:
1. Mechanical G-LEAK screen (leakage.screen over spec_view, lean flavor, judged against problem_statement, NOT hints_text): PASSED, zero hard_failures.
2. same_spec(patched, prepatch) = True — the spec region (docstring + ScanOutcome + carriesValue + problem_spec_capture) is byte-identical between the fixed and prepatch bundles, so the spec does not differentially encode the edit; only impl/proof differ.
3. Manual review of the spec view:
   - No diff markers, no 'resolvers.py' path, no dotted module path.
   - No spec-view identifier embeds a patched repo symbol (ScanOutcome/carriesValue/namedCaptures/positionalCaptures vs patched match/groupdict/groups/RegexPattern) — abstract Lean names.
   - No gold-patch line reproduced verbatim (spec is abstract Lean over ScanOutcome, never Python/groupdict terms).
   - No narration terms (bug/fix/wrong/incorrectly/regression/previously) in comments; docstring is neutral behavioral prose.

The spec docstring necessarily describes the correct post-fix semantics ('exactly the named captures that actually carry a value — an absent named capture contributes nothing', plus the positional fallback), but that is the intrinsic role of any specification, expressed on a topic already public in problem_statement and done abstractly. It does not disclose the edit's file, line, symbols, concrete diff, or fix-narration, so the concrete gold edit cannot be reconstructed beyond what the public task already states. No leakage beyond problem_statement.

**Gold edit:** `kwargs = match.groupdict()` -> `kwargs = {k: v for k, v in match.groupdict().items() if v is not None}` in django/urls/resolvers.py:156 (RegexPattern.match) — drop named captures whose value is None. Public problem_statement already discloses the topic: 'translate_url() creates an incorrect URL when optional named groups are missing' / 'absent optional arguments'.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
