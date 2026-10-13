# P2 adversarial audit — pytest-dev__pytest-7324

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -26,36 +26,14 @@
 -- post-conditions-end
 
 -- impl-start
--- identPrefix: the prefix attached to an identifier when it is turned into a
--- name node, so the name node can never collide with a reserved constant.
-def identPrefix : List Char := ['$']
-
--- isReservedConst: the compiler rejects a name node whose identifier is one of
--- the reserved boolean/none constants; modeled deeply as the exact finite set.
-def isReservedConst (id : List Char) : Bool :=
-  id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']
-
 def implementation_resolveIdent
-    (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
-  -- build the name node's identifier from the match-expression identifier
-  let key := identPrefix ++ name
-  -- compiling the name node aborts if its identifier is a reserved constant
-  if isReservedConst key then
-    return none
-  -- consult the matcher with the identifier recovered from the name node
-  return some (matcher (key.drop identPrefix.length))
+    (name : List Char) (matcher : List Char → Bool) : Option Bool :=
+  some (matcher name)
 -- impl-end
 
 -- proof-start
 theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
     problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
   intro name matcher
-  show implementation_resolveIdent name matcher = some (matcher name)
-  unfold implementation_resolveIdent
-  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
-    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
-  rw [if_neg]
-  · rfl
-  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
-      Bool.false_eq_true, not_false_eq_true]
+  rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -26,36 +26,19 @@
 -- post-conditions-end
 
 -- impl-start
--- identPrefix: the prefix attached to an identifier when it is turned into a
--- name node, so the name node can never collide with a reserved constant.
-def identPrefix : List Char := ['$']
-
--- isReservedConst: the compiler rejects a name node whose identifier is one of
--- the reserved boolean/none constants; modeled deeply as the exact finite set.
 def isReservedConst (id : List Char) : Bool :=
   id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']
-
 def implementation_resolveIdent
     (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
-  -- build the name node's identifier from the match-expression identifier
-  let key := identPrefix ++ name
-  -- compiling the name node aborts if its identifier is a reserved constant
+  let key := name
   if isReservedConst key then
     return none
-  -- consult the matcher with the identifier recovered from the name node
-  return some (matcher (key.drop identPrefix.length))
+  return some (matcher key)
 -- impl-end
 
 -- proof-start
 theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
     problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
   intro name matcher
-  show implementation_resolveIdent name matcher = some (matcher name)
-  unfold implementation_resolveIdent
-  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
-    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
-  rw [if_neg]
-  · rfl
-  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
-      Bool.false_eq_true, not_false_eq_true]
+  rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -26,36 +26,16 @@
 -- post-conditions-end
 
 -- impl-start
--- identPrefix: the prefix attached to an identifier when it is turned into a
--- name node, so the name node can never collide with a reserved constant.
-def identPrefix : List Char := ['$']
-
--- isReservedConst: the compiler rejects a name node whose identifier is one of
--- the reserved boolean/none constants; modeled deeply as the exact finite set.
-def isReservedConst (id : List Char) : Bool :=
-  id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']
-
 def implementation_resolveIdent
     (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
-  -- build the name node's identifier from the match-expression identifier
-  let key := identPrefix ++ name
-  -- compiling the name node aborts if its identifier is a reserved constant
-  if isReservedConst key then
+  if name = [] then
     return none
-  -- consult the matcher with the identifier recovered from the name node
-  return some (matcher (key.drop identPrefix.length))
+  return some (matcher name)
 -- impl-end
 
 -- proof-start
 theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
     problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
   intro name matcher
-  show implementation_resolveIdent name matcher = some (matcher name)
-  unfold implementation_resolveIdent
-  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
-    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
-  rw [if_neg]
-  · rfl
-  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
-      Bool.false_eq_true, not_false_eq_true]
+  rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -26,36 +26,14 @@
 -- post-conditions-end
 
 -- impl-start
--- identPrefix: the prefix attached to an identifier when it is turned into a
--- name node, so the name node can never collide with a reserved constant.
-def identPrefix : List Char := ['$']
-
--- isReservedConst: the compiler rejects a name node whose identifier is one of
--- the reserved boolean/none constants; modeled deeply as the exact finite set.
-def isReservedConst (id : List Char) : Bool :=
-  id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']
-
 def implementation_resolveIdent
-    (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
-  -- build the name node's identifier from the match-expression identifier
-  let key := identPrefix ++ name
-  -- compiling the name node aborts if its identifier is a reserved constant
-  if isReservedConst key then
-    return none
-  -- consult the matcher with the identifier recovered from the name node
-  return some (matcher (key.drop identPrefix.length))
+    (name : List Char) (matcher : List Char → Bool) : Option Bool :=
+  some (matcher (name.drop 1))
 -- impl-end
 
 -- proof-start
 theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
     problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
   intro name matcher
-  show implementation_resolveIdent name matcher = some (matcher name)
-  unfold implementation_resolveIdent
-  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
-    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
-  rw [if_neg]
-  · rfl
-  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
-      Bool.false_eq_true, not_false_eq_true]
+  rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -26,36 +26,16 @@
 -- post-conditions-end
 
 -- impl-start
--- identPrefix: the prefix attached to an identifier when it is turned into a
--- name node, so the name node can never collide with a reserved constant.
-def identPrefix : List Char := ['$']
-
--- isReservedConst: the compiler rejects a name node whose identifier is one of
--- the reserved boolean/none constants; modeled deeply as the exact finite set.
-def isReservedConst (id : List Char) : Bool :=
-  id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']
-
 def implementation_resolveIdent
     (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
-  -- build the name node's identifier from the match-expression identifier
-  let key := identPrefix ++ name
-  -- compiling the name node aborts if its identifier is a reserved constant
-  if isReservedConst key then
+  if name = ['x'] then
     return none
-  -- consult the matcher with the identifier recovered from the name node
-  return some (matcher (key.drop identPrefix.length))
+  return some (matcher name)
 -- impl-end
 
 -- proof-start
 theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
     problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
   intro name matcher
-  show implementation_resolveIdent name matcher = some (matcher name)
-  unfold implementation_resolveIdent
-  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
-    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
-  rw [if_neg]
-  · rfl
-  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
-      Bool.false_eq_true, not_false_eq_true]
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -26,36 +26,14 @@
 -- post-conditions-end
 
 -- impl-start
--- identPrefix: the prefix attached to an identifier when it is turned into a
--- name node, so the name node can never collide with a reserved constant.
-def identPrefix : List Char := ['$']
-
--- isReservedConst: the compiler rejects a name node whose identifier is one of
--- the reserved boolean/none constants; modeled deeply as the exact finite set.
-def isReservedConst (id : List Char) : Bool :=
-  id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']
-
 def implementation_resolveIdent
-    (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
-  -- build the name node's identifier from the match-expression identifier
-  let key := identPrefix ++ name
-  -- compiling the name node aborts if its identifier is a reserved constant
-  if isReservedConst key then
-    return none
-  -- consult the matcher with the identifier recovered from the name node
-  return some (matcher (key.drop identPrefix.length))
+    (name : List Char) (matcher : List Char → Bool) : Option Bool :=
+  some (!matcher name)
 -- impl-end
 
 -- proof-start
 theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
     problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
   intro name matcher
-  show implementation_resolveIdent name matcher = some (matcher name)
-  unfold implementation_resolveIdent
-  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
-    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
-  rw [if_neg]
-  · rfl
-  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
-      Bool.false_eq_true, not_false_eq_true]
+  rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -26,23 +26,14 @@
 -- post-conditions-end
 
 -- impl-start
--- identPrefix: the prefix attached to an identifier when it is turned into a
--- name node, so the name node can never collide with a reserved constant.
-def identPrefix : List Char := ['$']
-
--- isReservedConst: the compiler rejects a name node whose identifier is one of
--- the reserved boolean/none constants; modeled deeply as the exact finite set.
+def identPrefix : List Char := []
 def isReservedConst (id : List Char) : Bool :=
   id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']
-
 def implementation_resolveIdent
     (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
-  -- build the name node's identifier from the match-expression identifier
   let key := identPrefix ++ name
-  -- compiling the name node aborts if its identifier is a reserved constant
   if isReservedConst key then
     return none
-  -- consult the matcher with the identifier recovered from the name node
   return some (matcher (key.drop identPrefix.length))
 -- impl-end
 
@@ -52,10 +43,5 @@
   intro name matcher
   show implementation_resolveIdent name matcher = some (matcher name)
   unfold implementation_resolveIdent
-  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
-    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
-  rw [if_neg]
-  · rfl
-  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
-      Bool.false_eq_true, not_false_eq_true]
+  simp [identPrefix, isReservedConst, Id.run]
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -26,36 +26,14 @@
 -- post-conditions-end
 
 -- impl-start
--- identPrefix: the prefix attached to an identifier when it is turned into a
--- name node, so the name node can never collide with a reserved constant.
-def identPrefix : List Char := ['$']
-
--- isReservedConst: the compiler rejects a name node whose identifier is one of
--- the reserved boolean/none constants; modeled deeply as the exact finite set.
-def isReservedConst (id : List Char) : Bool :=
-  id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']
-
 def implementation_resolveIdent
-    (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
-  -- build the name node's identifier from the match-expression identifier
-  let key := identPrefix ++ name
-  -- compiling the name node aborts if its identifier is a reserved constant
-  if isReservedConst key then
-    return none
-  -- consult the matcher with the identifier recovered from the name node
-  return some (matcher (key.drop identPrefix.length))
+    (name : List Char) (matcher : List Char → Bool) : Option Bool :=
+  some true
 -- impl-end
 
 -- proof-start
 theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
     problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
   intro name matcher
-  show implementation_resolveIdent name matcher = some (matcher name)
-  unfold implementation_resolveIdent
-  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
-    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
-  rw [if_neg]
-  · rfl
-  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
-      Bool.false_eq_true, not_false_eq_true]
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature. The compilation guard that
-- rejects an identifier colliding with a reserved boolean/none constant is a
-- small, fully-known finite set, so it is modeled DEEPLY (an A-reference,
-- validated by G-AX against the real compiler) rather than axiomatized. The
-- proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
-- No spec-visible helper is required: the contract is stated directly as an
-- input→output relation over the identifier and the matcher.
-- pure-end

-- post-conditions-start
/-- Resolving a single match-expression identifier against a matcher always
succeeds and yields exactly the matcher's verdict on that identifier. The
identifier is consulted verbatim (the matcher sees the original identifier, not
some transformed form), and resolution never aborts — the result is always a
genuine boolean verdict (`some _`), for every identifier and every matcher. -/
def problem_spec_resolveIdent
    (name : List Char) (matcher : List Char → Bool) (result : Option Bool) : Prop :=
  result = some (matcher name)
-- post-conditions-end

-- impl-start
-- identPrefix: the prefix attached to an identifier when it is turned into a
-- name node, so the name node can never collide with a reserved constant.
def identPrefix : List Char := ['$']

-- isReservedConst: the compiler rejects a name node whose identifier is one of
-- the reserved boolean/none constants; modeled deeply as the exact finite set.
def isReservedConst (id : List Char) : Bool :=
  id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']

def implementation_resolveIdent
    (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
  -- build the name node's identifier from the match-expression identifier
  let key := identPrefix ++ name
  -- compiling the name node aborts if its identifier is a reserved constant
  if isReservedConst key then
    return none
  -- consult the matcher with the identifier recovered from the name node
  return some (matcher (key.drop identPrefix.length))
-- impl-end

-- proof-start
theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
    problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
  intro name matcher
  show implementation_resolveIdent name matcher = some (matcher name)
  unfold implementation_resolveIdent
  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
  rw [if_neg]
  · rfl
  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
      Bool.false_eq_true, not_false_eq_true]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: post-condition problem_spec_resolveIdent name matcher result := (result = some (matcher name)), universally quantified over a FREE matcher : List Char -> Bool. This is a TOTAL FUNCTIONAL spec: any verifying impl is forced to be behaviorally `some (matcher name)` for every identifier — no behavioral freedom, no crash allowed. Confirmed structurally: markers._lean_spec_view ELIDES the entire impl region (identPrefix, isReservedConst, implementation_resolveIdent) AND the proof, so same_spec pins ONLY the axioms/pure/pre/post regions. All 8 attacks verified same_spec=True against Solution.lean.

### ATTACK RESULTS (cmd: `bash scripts/lean_verify.sh <atk_N.lean>`, run concurrently <=4 at a time):
- atk_1 (UNGROUNDED-ORACLE / echo): impl `some (matcher name)` (guard+prefix modeling dropped). VERIFIES, exit=0. `#print axioms correct_resolveIdent` => 'does not depend on any axioms' (CLEAN). This is the ONLY wrong-impl candidate that closes. Its behavior is IDENTICAL to gold (some (matcher name), never crash), so its ONLY faithful refined patch is the gold patch (the $-prefix is the only realization that returns the verdict for True/False/None without crashing compile()). Materialized patch = gold patch; RAN through official harness (run_evaluation, run_id levv7324try1): report.json resolved=true, FAIL_TO_PASS test_valid_idents[True/False/None] all success, all PASS_TO_PASS success. => resolving echo, NOT a break.
- atk_2 (PREPATCH BUG, verbatim key + crash guard): exit=1 (fails to verify) — reproduces the prepatch failure (crashes/returns none on True/False/None, contradicting some (matcher name)).
- atk_3 (PARTIAL-DOMAIN, none on empty name): exit=1 (fails).
- atk_4 (BOUNDARY, matcher on name.drop 1): exit=1 (fails).
- atk_5 (CONTROL-FLOW-EFFECT, none on ['x']): exit=1 (fails).
- atk_6 (UNGROUNDED-ORACLE, some (!matcher name)): exit=1 (fails).
- atk_7 (mis-modeled prefix = [] so guard still fires on reserved): exit=1 (fails).
- atk_8 (constant `some true`, ignores matcher): exit=1 (fails).
Positive control atk_pc (copy of Solution.lean): exit=0 verifies; axioms=[propext] (standard, clean).

EARLY RESOLVE FALSE-NEGATIVES: first two run_resolve calls returned COMPLETED=False ('no report.json — harness error or image pull failure') and one direct run hit docker.errors.ImageNotFound during images.list() — a transient docker-image race under heavy concurrent contention (many sbu-resolve/audit jobs running; the 7324 image IS present locally). Retried; harness completed with resolved=true (✓=1 ✖=0). These were infra flakes, NOT genuine non-resolves.

REFINEMENT.MD AUDIT: rows 1,2 = R (str<->List Char, Callable<->fn; G-CONF territory); row 3 = I (literal '$' prefix); rows 4,5,6,7 = A-reference (prefix-attach, crash guard, prefix-strip, verdict return), all deeply modeled and validated == real ast/compile/eval by G-AX (recorded pass, seed=7324). No A-consumed rows, no kind-3 (changed-inexpressible) rows; meta axioms=[] and opaque_callees=[]. Independently verified the row-5 A-reference correspondence: compile(ast.Expression(ast.Name(id)), mode='eval') raises ValueError at compile time for EXACTLY {True,False,None} and compiles fine for $-prefixed identifiers (NameError only at runtime, resolved via matcher) — so isReservedConst={True,False,None} and identPrefix='$' faithfully model the real callee. Correspondence holds.

CONCLUSION: The spec is a tight total-functional oracle. Every genuinely-wrong impl (partial-domain, boundary, control-flow, negated-oracle, mis-modeled prefix, matcher-ignoring, prepatch) FAILS lean verification. The single closing wrong-impl candidate is a behavioral echo of gold whose faithful patch RESOLVES (executed, confirmed). No verify∧¬resolve witness exists. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature. The compilation guard that
-- rejects an identifier colliding with a reserved boolean/none constant is a
-- small, fully-known finite set, so it is modeled DEEPLY (an A-reference,
-- validated by G-AX against the real compiler) rather than axiomatized. The
-- proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
-- No spec-visible helper is required: the contract is stated directly as an
-- input→output relation over the identifier and the matcher.
-- pure-end

-- post-conditions-start
/-- Resolving a single match-expression identifier against a matcher always
succeeds and yields exactly the matcher's verdict on that identifier. The
identifier is consulted verbatim (the matcher sees the original identifier, not
some transformed form), and resolution never aborts — the result is always a
genuine boolean verdict (`some _`), for every identifier and every matcher. -/
def problem_spec_resolveIdent
    (name : List Char) (matcher : List Char → Bool) (result : Option Bool) : Prop :=
  result = some (matcher name)
-- post-conditions-end

-- impl-start
-- identPrefix: the prefix attached to an identifier when it is turned into a
-- name node, so the name node can never collide with a reserved constant.
def identPrefix : List Char := ['$']

-- isReservedConst: the compiler rejects a name node whose identifier is one of
-- the reserved boolean/none constants; modeled deeply as the exact finite set.
def isReservedConst (id : List Char) : Bool :=
  id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']

def implementation_resolveIdent
    (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
  -- build the name node's identifier from the match-expression identifier
  let key := identPrefix ++ name
  -- compiling the name node aborts if its identifier is a reserved constant
  if isReservedConst key then
    return none
  -- consult the matcher with the identifier recovered from the name node
  return some (matcher (key.drop identPrefix.length))
-- impl-end

-- proof-start
theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
    problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
  intro name matcher
  show implementation_resolveIdent name matcher = some (matcher name)
  unfold implementation_resolveIdent
  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
  rw [if_neg]
  · rfl
  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
      Bool.false_eq_true, not_false_eq_true]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: post-condition problem_spec_resolveIdent name matcher result := (result = some (matcher name)), universally quantified over a FREE matcher : List Char -> Bool. This is a TOTAL FUNCTIONAL spec: any verifying impl is forced to be behaviorally `some (matcher name)` for every identifier — no behavioral freedom, no crash allowed. Confirmed structurally: markers._lean_spec_view ELIDES the entire impl region (identPrefix, isReservedConst, implementation_resolveIdent) AND the proof, so same_spec pins ONLY the axioms/pure/pre/post regions. All 8 attacks verified same_spec=True against Solution.lean.

### ATTACK RESULTS (cmd: `bash scripts/lean_verify.sh <atk_N.lean>`, run concurrently <=4 at a time):
- atk_1 (UNGROUNDED-ORACLE / echo): impl `some (matcher name)` (guard+prefix modeling dropped). VERIFIES, exit=0. `#print axioms correct_resolveIdent` => 'does not depend on any axioms' (CLEAN). This is the ONLY wrong-impl candidate that closes. Its behavior is IDENTICAL to gold (some (matcher name), never crash), so its ONLY faithful refined patch is the gold patch (the $-prefix is the only realization that returns the verdict for True/False/None without crashing compile()). Materialized patch = gold patch; RAN through official harness (run_evaluation, run_id levv7324try1): report.json resolved=true, FAIL_TO_PASS test_valid_idents[True/False/None] all success, all PASS_TO_PASS success. => resolving echo, NOT a break.
- atk_2 (PREPATCH BUG, verbatim key + crash guard): exit=1 (fails to verify) — reproduces the prepatch failure (crashes/returns none on True/False/None, contradicting some (matcher name)).
- atk_3 (PARTIAL-DOMAIN, none on empty name): exit=1 (fails).
- atk_4 (BOUNDARY, matcher on name.drop 1): exit=1 (fails).
- atk_5 (CONTROL-FLOW-EFFECT, none on ['x']): exit=1 (fails).
- atk_6 (UNGROUNDED-ORACLE, some (!matcher name)): exit=1 (fails).
- atk_7 (mis-modeled prefix = [] so guard still fires on reserved): exit=1 (fails).
- atk_8 (constant `some true`, ignores matcher): exit=1 (fails).
Positive control atk_pc (copy of Solution.lean): exit=0 verifies; axioms=[propext] (standard, clean).

EARLY RESOLVE FALSE-NEGATIVES: first two run_resolve calls returned COMPLETED=False ('no report.json — harness error or image pull failure') and one direct run hit docker.errors.ImageNotFound during images.list() — a transient docker-image race under heavy concurrent contention (many sbu-resolve/audit jobs running; the 7324 image IS present locally). Retried; harness completed with resolved=true (✓=1 ✖=0). These were infra flakes, NOT genuine non-resolves.

REFINEMENT.MD AUDIT: rows 1,2 = R (str<->List Char, Callable<->fn; G-CONF territory); row 3 = I (literal '$' prefix); rows 4,5,6,7 = A-reference (prefix-attach, crash guard, prefix-strip, verdict return), all deeply modeled and validated == real ast/compile/eval by G-AX (recorded pass, seed=7324). No A-consumed rows, no kind-3 (changed-inexpressible) rows; meta axioms=[] and opaque_callees=[]. Independently verified the row-5 A-reference correspondence: compile(ast.Expression(ast.Name(id)), mode='eval') raises ValueError at compile time for EXACTLY {True,False,None} and compiles fine for $-prefixed identifiers (NameError only at runtime, resolved via matcher) — so isReservedConst={True,False,None} and identPrefix='$' faithfully model the real callee. Correspondence holds.

CONCLUSION: The spec is a tight total-functional oracle. Every genuinely-wrong impl (partial-domain, boundary, control-flow, negated-oracle, mis-modeled prefix, matcher-ignoring, prepatch) FAILS lean verification. The single closing wrong-impl candidate is a behavioral echo of gold whose faithful patch RESOLVES (executed, confirmed). No verify∧¬resolve witness exists. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pytest-dev__pytest-7324 lean bundle. Modeled function: implementation_resolveIdent (single match-expression identifier resolution). Real callee at base_commit 19ad5889... WITH patch applied lives (verified HEAD + patched not_expr/MatcherAdapter lines).

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, lean) = True — spec region (post-conditions problem_spec_resolveIdent: result = some (matcher name)) is byte-identical across the patch, as required.
2. Solution.lean compiles under scripts/lean_verify.sh (exit 0, no sorry/error). #print axioms correct_resolveIdent => [propext] only; NO sorryAx — the proof is genuine, so the modeled function's contract is really discharged.
3. Faithfulness fuzz of the REAL post-patch Python path (ast.fix_missing_locations(ast.Expression(ast.Name('$'+name, Load))) -> compile(mode='eval') -> eval via the real MatcherAdapter which strips the prefix and consults the matcher) against the model's asserted outcome some(matcher name), over 300,010 inputs drawn from a broad pool: all codepoints 0x00-0x17F, control chars, newline/tab/space, null byte, '$', emoji (U+1F600), Hebrew letters, arrows, and the reserved spellings True/False/None (plus fixed edge cases). Result: 0 divergences. compile() never aborts on any '$'-prefixed name (release build; the reserved-constant guard in the model, isReservedConst key, is provably dead post-prefix exactly as it is unreachable in the real code), and eval always yields bool(matcher(name)).

The spec is NOT too strong: post-patch the real repo resolves every identifier to exactly the matcher's boolean verdict on the original name, never aborting (some (matcher name)). No diverging input exists. The prepatch legitimately fails this spec on {True,False,None} (guard fires -> none), which is the correct discriminator (F2P: test_valid_idents[True/False/None]). Model boundary (Option Bool carrier, deep isReservedConst finite set) faithfully matches the real callee.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (hard_failures=[]); spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True); spec_view correctly elides impl and proof. The gold edit is the IDENT_PREFIX='$' prefix-attach + prefix-strip trick (src/_pytest/mark/expression.py) to avoid crashing compile() on True/False/None. The solver-visible spec view discloses only: (1) the desired contract `result = some (matcher name)` — resolution never aborts and returns the matcher's verdict on the original identifier, and (2) an axioms comment noting compile() rejects identifiers colliding with 'reserved boolean/none constant'. Both are already public: the problem_statement shows the compiler_nameop assertion naming None/True/False and the abort on Expression.compile('False'). The '$' prefix mechanism itself lives entirely in the elided impl region and is nowhere revealed; the hints_text ast.Constant approach satisfies the same contract by a different mechanism, confirming the spec constrains behavior, not the specific gold edit. The docstring phrase 'matcher sees the original identifier, not some transformed form' states the correctness invariant, not the fix. No diff markers, patched file path, gold-patch line, or narration terms present. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
