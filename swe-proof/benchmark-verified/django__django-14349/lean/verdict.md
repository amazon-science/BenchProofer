# P2 adversarial audit — django__django-14349

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,9 +61,7 @@
 
 -- impl-start
 def implementation_validateUrl (value : List Char) : Bool := Id.run do
-  if containsForbidden value then
-    return false
-  return structurallyValid value
+  return true
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
 
 -- impl-start
 def implementation_validateUrl (value : List Char) : Bool := Id.run do
-  if containsForbidden value then
+  if value.any (fun c => c == '\t' || c == '\r') then
     return false
   return structurallyValid value
 -- impl-end
@@ -74,5 +74,5 @@
   intro value
   unfold problem_spec_validateUrl implementation_validateUrl
   refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    simp only [Id.run, h, if_true, if_false, Bool.false_eq_true, pure, bind]
+    simp_all [Id.run, containsForbidden]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,8 +61,6 @@
 
 -- impl-start
 def implementation_validateUrl (value : List Char) : Bool := Id.run do
-  if containsForbidden value then
-    return false
   return structurallyValid value
 -- impl-end
 
@@ -74,5 +72,5 @@
   intro value
   unfold problem_spec_validateUrl implementation_validateUrl
   refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    simp only [Id.run, h, if_true, if_false, Bool.false_eq_true, pure, bind]
+    simp_all [Id.run]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
 def implementation_validateUrl (value : List Char) : Bool := Id.run do
   if containsForbidden value then
     return false
-  return structurallyValid value
+  return !structurallyValid value
 -- impl-end
 
 -- proof-start
@@ -74,5 +74,5 @@
   intro value
   unfold problem_spec_validateUrl implementation_validateUrl
   refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    simp only [Id.run, h, if_true, if_false, Bool.false_eq_true, pure, bind]
+    simp_all [Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
 -- impl-start
 def implementation_validateUrl (value : List Char) : Bool := Id.run do
   if containsForbidden value then
-    return false
+    return true
   return structurallyValid value
 -- impl-end
 
@@ -74,5 +74,5 @@
   intro value
   unfold problem_spec_validateUrl implementation_validateUrl
   refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    simp only [Id.run, h, if_true, if_false, Bool.false_eq_true, pure, bind]
+    simp_all [Id.run]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,9 +61,7 @@
 
 -- impl-start
 def implementation_validateUrl (value : List Char) : Bool := Id.run do
-  if containsForbidden value then
-    return false
-  return structurallyValid value
+  return false
 -- impl-end
 
 -- proof-start
@@ -74,5 +72,5 @@
   intro value
   unfold problem_spec_validateUrl implementation_validateUrl
   refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    simp only [Id.run, h, if_true, if_false, Bool.false_eq_true, pure, bind]
+    simp_all [Id.run]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
 
 -- impl-start
 def implementation_validateUrl (value : List Char) : Bool := Id.run do
-  if containsForbidden value then
+  if value.any (fun c => c == '\t' || c == '\r' || c == '\n' || c == ' ') then
     return false
   return structurallyValid value
 -- impl-end
@@ -74,5 +74,5 @@
   intro value
   unfold problem_spec_validateUrl implementation_validateUrl
   refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    simp only [Id.run, h, if_true, if_false, Bool.false_eq_true, pure, bind]
+    simp_all [Id.run, containsForbidden]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a candidate web address is acceptable.

An address is supplied as a string and must be judged acceptable or not. Two
independent conditions govern acceptance:

  * a structural condition — the address must be well-formed according to the
    usual address grammar (the scheme is among those allowed, the overall shape
    matches, and any embedded host is well-formed); and

  * a safety condition on the raw characters — an address that contains any of a
    designated group of disallowed control characters (a horizontal tab, a
    carriage return, or a line feed) is never acceptable, regardless of how it
    would otherwise be parsed. Such characters can cause the same text to be
    split or interpreted in more than one way, so their mere presence is
    disqualifying.

The desired behavior is therefore: if the address contains any disallowed
control character it is rejected outright; otherwise acceptance is exactly the
verdict of the structural condition. The two conditions together decide every
input, so the verdict is never left free.
-/

-- axioms-start
/-- The structural acceptance condition: it reports whether the address is
well-formed according to the usual address grammar (allowed scheme, overall
shape, embedded host). It is consumed here as an opaque carrier — the behavior
modeled in this bundle is how the raw-character safety condition combines with
the structural verdict, not the internal grammar the structural condition
applies. -/
opaque structurallyValid : List Char → Bool
-- axioms-end

-- pure-start
/-- The raw-character safety test: an address is disqualified when it contains
any of the disallowed control characters (horizontal tab, carriage return, line
feed). This is the set-membership test that disqualifies an address before the
structural condition is even consulted. -/
def containsForbidden (value : List Char) : Bool :=
  value.any (fun c => c == '\t' || c == '\r' || c == '\n')
-- pure-end

-- post-conditions-start
/-- The verdict is fully pinned to the input:

  * when the address contains a disallowed control character, it is rejected
    (the verdict is `false`); and

  * otherwise the verdict is exactly the structural acceptance condition applied
    to the address.

Both cases together determine the verdict for every input, so no part of the
result is left free. -/
def problem_spec_validateUrl (value : List Char) (result : Bool) : Prop :=
  (containsForbidden value = true  → result = false) ∧
  (containsForbidden value = false → result = structurallyValid value)
-- post-conditions-end

-- impl-start
def implementation_validateUrl (value : List Char) : Bool := Id.run do
  if containsForbidden value then
    return false
  return structurallyValid value
-- impl-end

-- proof-start
theorem correct_validateUrl :
    ∀ (value : List Char),
      problem_spec_validateUrl value
        (implementation_validateUrl value) := by
  intro value
  unfold problem_spec_validateUrl implementation_validateUrl
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    simp only [Id.run, h, if_true, if_false, Bool.false_eq_true, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_validateUrl is total AND functional. For every value exactly one of (containsForbidden value = true) / (= false) holds; the first clause pins result=false, the second pins result=structurallyValid value. Every input is uniquely determined, so any impl that verifies is forced extensionally equal to implementation_validateUrl => verify=>correct structurally. No free/underspecified region exists to exploit.

 Used PY=python for same_spec (module swebench_unified only importable from that venv). Verified via `bash scripts/lean_verify.sh <file>`.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True (spec/axioms/pure/pre/post byte-identical; only impl+proof region edited).

### ATTACKS (all distinct, all fail to verify => nothing to resolve-run):
- atk_1 partial-domain, `return true` (ignores guard+structural): exit=1, unsolved goals at proof (containsForbidden=true branch demands result=false).
- atk_2 boundary, guard drops '\n' (checks only \t,\r): exit=1, unsolved goals (value with only '\n' => containsForbidden=true but impl returns structurallyValid).
- atk_3 control-flow-effect = prepatch bug, unconditional `return structurallyValid value`: exit=1, unsolved goals (guard-true clause).
- atk_4 ungrounded-oracle echo, else-branch `!structurallyValid value`: exit=1, unsolved goals (containsForbidden=false clause demands = structurallyValid, not its negation).
- atk_5 verdict-swap on guard branch, `return true` when forbidden present: exit=1, unsolved goals.
- atk_6 constant `false` everywhere (over-rejects safe structurally-valid URLs): exit=1, unsolved goals (containsForbidden=false clause needs structurallyValid value which is not forced false).
- atk_7 over-broad guard also rejects space ' ': exit=1, unsolved goals (value with ' ' has containsForbidden=false but impl returns false).
All failures are genuine `error: unsolved goals` at the theorem, not weak-tactic artifacts; the spec's functionality makes each violation unclosable.

POSITIVE CONTROL: pos_control.lean (= Solution.lean) verifies exit=0. #print axioms correct_validateUrl => depends on axioms: [propext] (CLEAN; opaque `structurallyValid` introduces NO axiom, consistent with meta.json axioms=[] and deep_model_references=[]). axcheck.lean copy with #print axioms appended also exit=0.

PREPATCH: Solution_prepatch.lean (unconditional return structurallyValid value) fails verification exit=1 (type mismatch / rewrite-failed on the containsForbidden=true goal `pure (structurallyValid value) = false`) => real bug reproduced, G-DIFF-style failure as required.

REFINEMENT AUDIT (refinement.md): 3 legs, all R/I, no kind-3.
  leg1 `if containsForbidden` (R): deep def ↔ self.unsafe_chars.intersection(value) truthiness over frozenset('\t\r\n'); NOT axiomatized (it is the op the patch changes).
  leg2 `return false` (R): raised ValidationError ↔ verdict false.
  leg3 `return structurallyValid value` (R): opaque carrier ↔ unchanged rest-of-__call__; A-reference-style correspondence realized/checked by G-CONF (real patched URLValidator with unsafe_chars neutralized to frozenset()).
  NO A-consumed leg: proof closes by case analysis on containsForbidden, consuming no property of structurallyValid; hence no `axiom _prop`, axiom_check.py is a legitimate skip stub, clean #print axioms confirms it. isinstance(str) guard is the type-modeling boundary (List Char already a string) — standard type refinement, not omitted behavior.

SINCE NO WRONG IMPL CLOSES, no faithful patch was materialized/resolve-run (protocol step 2 triggers only for closing clean-axiom proofs; none exist). Verdict SOUND: >=5 (here 7) distinct same-spec wrong impls attacked, none breaks the spec; positive control verifies clean; refinement legs all R/A-reference with holding correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
Deciding whether a candidate web address is acceptable.

An address is supplied as a string and must be judged acceptable or not. Two
independent conditions govern acceptance:

  * a structural condition — the address must be well-formed according to the
    usual address grammar (the scheme is among those allowed, the overall shape
    matches, and any embedded host is well-formed); and

  * a safety condition on the raw characters — an address that contains any of a
    designated group of disallowed control characters (a horizontal tab, a
    carriage return, or a line feed) is never acceptable, regardless of how it
    would otherwise be parsed. Such characters can cause the same text to be
    split or interpreted in more than one way, so their mere presence is
    disqualifying.

The desired behavior is therefore: if the address contains any disallowed
control character it is rejected outright; otherwise acceptance is exactly the
verdict of the structural condition. The two conditions together decide every
input, so the verdict is never left free.
-/

-- axioms-start
/-- The structural acceptance condition: it reports whether the address is
well-formed according to the usual address grammar (allowed scheme, overall
shape, embedded host). It is consumed here as an opaque carrier — the behavior
modeled in this bundle is how the raw-character safety condition combines with
the structural verdict, not the internal grammar the structural condition
applies. -/
opaque structurallyValid : List Char → Bool
-- axioms-end

-- pure-start
/-- The raw-character safety test: an address is disqualified when it contains
any of the disallowed control characters (horizontal tab, carriage return, line
feed). This is the set-membership test that disqualifies an address before the
structural condition is even consulted. -/
def containsForbidden (value : List Char) : Bool :=
  value.any (fun c => c == '\t' || c == '\r' || c == '\n')
-- pure-end

-- post-conditions-start
/-- The verdict is fully pinned to the input:

  * when the address contains a disallowed control character, it is rejected
    (the verdict is `false`); and

  * otherwise the verdict is exactly the structural acceptance condition applied
    to the address.

Both cases together determine the verdict for every input, so no part of the
result is left free. -/
def problem_spec_validateUrl (value : List Char) (result : Bool) : Prop :=
  (containsForbidden value = true  → result = false) ∧
  (containsForbidden value = false → result = structurallyValid value)
-- post-conditions-end

-- impl-start
def implementation_validateUrl (value : List Char) : Bool := Id.run do
  if containsForbidden value then
    return false
  return structurallyValid value
-- impl-end

-- proof-start
theorem correct_validateUrl :
    ∀ (value : List Char),
      problem_spec_validateUrl value
        (implementation_validateUrl value) := by
  intro value
  unfold problem_spec_validateUrl implementation_validateUrl
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    simp only [Id.run, h, if_true, if_false, Bool.false_eq_true, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_validateUrl is total AND functional. For every value exactly one of (containsForbidden value = true) / (= false) holds; the first clause pins result=false, the second pins result=structurallyValid value. Every input is uniquely determined, so any impl that verifies is forced extensionally equal to implementation_validateUrl => verify=>correct structurally. No free/underspecified region exists to exploit.

 Used PY=python for same_spec (module swebench_unified only importable from that venv). Verified via `bash scripts/lean_verify.sh <file>`.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True (spec/axioms/pure/pre/post byte-identical; only impl+proof region edited).

### ATTACKS (all distinct, all fail to verify => nothing to resolve-run):
- atk_1 partial-domain, `return true` (ignores guard+structural): exit=1, unsolved goals at proof (containsForbidden=true branch demands result=false).
- atk_2 boundary, guard drops '\n' (checks only \t,\r): exit=1, unsolved goals (value with only '\n' => containsForbidden=true but impl returns structurallyValid).
- atk_3 control-flow-effect = prepatch bug, unconditional `return structurallyValid value`: exit=1, unsolved goals (guard-true clause).
- atk_4 ungrounded-oracle echo, else-branch `!structurallyValid value`: exit=1, unsolved goals (containsForbidden=false clause demands = structurallyValid, not its negation).
- atk_5 verdict-swap on guard branch, `return true` when forbidden present: exit=1, unsolved goals.
- atk_6 constant `false` everywhere (over-rejects safe structurally-valid URLs): exit=1, unsolved goals (containsForbidden=false clause needs structurallyValid value which is not forced false).
- atk_7 over-broad guard also rejects space ' ': exit=1, unsolved goals (value with ' ' has containsForbidden=false but impl returns false).
All failures are genuine `error: unsolved goals` at the theorem, not weak-tactic artifacts; the spec's functionality makes each violation unclosable.

POSITIVE CONTROL: pos_control.lean (= Solution.lean) verifies exit=0. #print axioms correct_validateUrl => depends on axioms: [propext] (CLEAN; opaque `structurallyValid` introduces NO axiom, consistent with meta.json axioms=[] and deep_model_references=[]). axcheck.lean copy with #print axioms appended also exit=0.

PREPATCH: Solution_prepatch.lean (unconditional return structurallyValid value) fails verification exit=1 (type mismatch / rewrite-failed on the containsForbidden=true goal `pure (structurallyValid value) = false`) => real bug reproduced, G-DIFF-style failure as required.

REFINEMENT AUDIT (refinement.md): 3 legs, all R/I, no kind-3.
  leg1 `if containsForbidden` (R): deep def ↔ self.unsafe_chars.intersection(value) truthiness over frozenset('\t\r\n'); NOT axiomatized (it is the op the patch changes).
  leg2 `return false` (R): raised ValidationError ↔ verdict false.
  leg3 `return structurallyValid value` (R): opaque carrier ↔ unchanged rest-of-__call__; A-reference-style correspondence realized/checked by G-CONF (real patched URLValidator with unsafe_chars neutralized to frozenset()).
  NO A-consumed leg: proof closes by case analysis on containsForbidden, consuming no property of structurallyValid; hence no `axiom _prop`, axiom_check.py is a legitimate skip stub, clean #print axioms confirms it. isinstance(str) guard is the type-modeling boundary (List Char already a string) — standard type refinement, not omitted behavior.

SINCE NO WRONG IMPL CLOSES, no faithful patch was materialized/resolve-run (protocol step 2 triggers only for closing clean-axiom proofs; none exist). Verdict SOUND: >=5 (here 7) distinct same-spec wrong impls attacked, none breaks the spec; positive control verifies clean; refinement legs all R/A-reference with holding correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** django__django-14349 lean bundle. Spec region byte-identical (swebench_unified same_spec via LeanBackend.language = True) between Solution.lean and Solution_prepatch.lean. Solution.lean compiles (lean_verify exit 0, no sorry); #print axioms correct_validateUrl -> [propext] only (no sorryAx, proof is genuine). Faithfulness: gold patch adds unconditional guard `if self.unsafe_chars.intersection(value): raise` with unsafe_chars=frozenset('\t\r\n'). Lean containsForbidden = value.any(c=='\t'||'\r'||'\n') exactly matches. problem_spec_validateUrl clauses (containsForbidden=true -> result=false; false -> result=structurallyValid) exactly mirror real __call__ (guard-hit raises=false, else unchanged tail verdict). Ran bundle conformance_check.py against real PATCHED repo: 100000 inputs, 0 disagreements. Ran independent 300k-input adversarial fuzz over a much broader pool (all other ASCII/Unicode whitespace+control: VT, FF, \x1c-\x1f, \x85, NBSP, ideographic space, NUL, etc.) comparing real repo verdict (guard active) against guard-neutralized structural verdict per the spec predicate: 0 violations. Near-miss whitespace not in {tab,CR,LF} correctly NOT rejected by either spec or repo. Spec is not too strong and does not drift; modeled function agrees with real callee on every tested input. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view does not leak the gold edit beyond the public problem_statement. The problem_statement itself already discloses (a) the exact characters — 'LF, CR and tab characters' — and (b) the exact fix strategy: 'One option is to reject URLs containing the forbidden characters early', which is precisely the gold patch (unsafe_chars = frozenset('\t\r\n') + reject on intersection). The Solution.lean spec (docstring + problem_spec_validateUrl: containsForbidden→reject, else structural verdict) restates only what problem_statement already makes public: the three specific control chars {tab,CR,LF} and the reject-outright behavior. Implementation internals (frozenset/intersection, scheme/regex/IDN/IPv6) are abstracted behind an opaque `structurallyValid` carrier and are NOT exposed. Verification: (1) markers.same_spec(Solution, Solution_prepatch) = True — spec region byte-identical, so the buggy/fixed discriminator lives only in the impl region, not smuggled through a spec diff; (2) lean_verify exit 0, no sorry, `#print axioms correct_validateUrl` = [propext] only (clean, no sorryAx — proof is genuine); (3) mechanical leakage.screen over spec view passes with zero hard_failures. No spec-view line reveals gold specifics beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
