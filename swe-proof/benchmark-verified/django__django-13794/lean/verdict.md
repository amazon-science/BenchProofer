# P2 adversarial audit — django__django-13794

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
None. The postcondition `problem_spec_lazyConcat a b result := result = force a ++ force b` is a total, deterministic functional equality that pins the result uniquely for every (a,b). No same-spec wrong implementation can close its proof. Prepatch bug (atk_1: returns "" when an operand is deferred) leaves the false goal `"" = a ++ b` in the deferred/deferred (and concrete/deferred) case and does NOT verify — exactly the add08/add09/test_lazy_add F2P failures.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,18 +60,13 @@
 
 -- impl-start
 def implementation_lazyConcat (a b : Operand) : String := Id.run do
+  -- prepatch bug: on-demand operand makes concat fail -> filter yields ""
   match a with
-  | .deferred s =>
-      -- left operand is on-demand: force it, then concatenate with the right
-      return s ++ force b
   | .concrete s =>
       match b with
-      | .deferred t =>
-          -- left concrete, right on-demand: force the right and append it
-          return s ++ t
-      | .concrete t =>
-          -- both concrete: ordinary text concatenation
-          return s ++ t
+      | .concrete t => return s ++ t
+      | .deferred _ => return ""
+  | .deferred _ => return ""
 -- impl-end
 
 -- proof-start
@@ -80,5 +75,11 @@
       problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
   intro a b
   unfold problem_spec_lazyConcat implementation_lazyConcat
-  cases a <;> cases b <;> rfl
+  cases a <;> cases b <;>
+    first
+      | rfl
+      | (simp [force])
+      | decide
+      | native_decide
+      | (simp_all [force]; done)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,18 +60,8 @@
 
 -- impl-start
 def implementation_lazyConcat (a b : Operand) : String := Id.run do
-  match a with
-  | .deferred s =>
-      -- left operand is on-demand: force it, then concatenate with the right
-      return s ++ force b
-  | .concrete s =>
-      match b with
-      | .deferred t =>
-          -- left concrete, right on-demand: force the right and append it
-          return s ++ t
-      | .concrete t =>
-          -- both concrete: ordinary text concatenation
-          return s ++ t
+  -- order swap: return force b ++ force a
+  return force b ++ force a
 -- impl-end
 
 -- proof-start
@@ -80,5 +70,11 @@
       problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
   intro a b
   unfold problem_spec_lazyConcat implementation_lazyConcat
-  cases a <;> cases b <;> rfl
+  cases a <;> cases b <;>
+    first
+      | rfl
+      | (simp [force])
+      | decide
+      | native_decide
+      | (simp_all [force]; done)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,17 +61,11 @@
 -- impl-start
 def implementation_lazyConcat (a b : Operand) : String := Id.run do
   match a with
-  | .deferred s =>
-      -- left operand is on-demand: force it, then concatenate with the right
-      return s ++ force b
+  | .deferred s => return s ++ force b
   | .concrete s =>
       match b with
-      | .deferred t =>
-          -- left concrete, right on-demand: force the right and append it
-          return s ++ t
-      | .concrete t =>
-          -- both concrete: ordinary text concatenation
-          return s ++ t
+      | .deferred _ => return s          -- partial-domain bug: drop forced right
+      | .concrete t => return s ++ t
 -- impl-end
 
 -- proof-start
@@ -80,5 +74,11 @@
       problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
   intro a b
   unfold problem_spec_lazyConcat implementation_lazyConcat
-  cases a <;> cases b <;> rfl
+  cases a <;> cases b <;>
+    first
+      | rfl
+      | (simp [force])
+      | decide
+      | native_decide
+      | (simp_all [force]; done)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,18 +60,8 @@
 
 -- impl-start
 def implementation_lazyConcat (a b : Operand) : String := Id.run do
-  match a with
-  | .deferred s =>
-      -- left operand is on-demand: force it, then concatenate with the right
-      return s ++ force b
-  | .concrete s =>
-      match b with
-      | .deferred t =>
-          -- left concrete, right on-demand: force the right and append it
-          return s ++ t
-      | .concrete t =>
-          -- both concrete: ordinary text concatenation
-          return s ++ t
+  -- ungrounded: return only force a
+  return force a
 -- impl-end
 
 -- proof-start
@@ -80,5 +70,11 @@
       problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
   intro a b
   unfold problem_spec_lazyConcat implementation_lazyConcat
-  cases a <;> cases b <;> rfl
+  cases a <;> cases b <;>
+    first
+      | rfl
+      | (simp [force])
+      | decide
+      | native_decide
+      | (simp_all [force]; done)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,18 +60,7 @@
 
 -- impl-start
 def implementation_lazyConcat (a b : Operand) : String := Id.run do
-  match a with
-  | .deferred s =>
-      -- left operand is on-demand: force it, then concatenate with the right
-      return s ++ force b
-  | .concrete s =>
-      match b with
-      | .deferred t =>
-          -- left concrete, right on-demand: force the right and append it
-          return s ++ t
-      | .concrete t =>
-          -- both concrete: ordinary text concatenation
-          return s ++ t
+  return ""
 -- impl-end
 
 -- proof-start
@@ -80,5 +69,11 @@
       problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
   intro a b
   unfold problem_spec_lazyConcat implementation_lazyConcat
-  cases a <;> cases b <;> rfl
+  cases a <;> cases b <;>
+    first
+      | rfl
+      | (simp [force])
+      | decide
+      | native_decide
+      | (simp_all [force]; done)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,17 +61,11 @@
 -- impl-start
 def implementation_lazyConcat (a b : Operand) : String := Id.run do
   match a with
-  | .deferred s =>
-      -- left operand is on-demand: force it, then concatenate with the right
-      return s ++ force b
+  | .deferred s => return s ++ s ++ force b   -- boundary bug: duplicate forced left
   | .concrete s =>
       match b with
-      | .deferred t =>
-          -- left concrete, right on-demand: force the right and append it
-          return s ++ t
-      | .concrete t =>
-          -- both concrete: ordinary text concatenation
-          return s ++ t
+      | .deferred t => return s ++ t
+      | .concrete t => return s ++ t
 -- impl-end
 
 -- proof-start
@@ -80,5 +74,11 @@
       problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
   intro a b
   unfold problem_spec_lazyConcat implementation_lazyConcat
-  cases a <;> cases b <;> rfl
+  cases a <;> cases b <;>
+    first
+      | rfl
+      | (simp [force])
+      | decide
+      | native_decide
+      | (simp_all [force]; done)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,18 +60,10 @@
 
 -- impl-start
 def implementation_lazyConcat (a b : Operand) : String := Id.run do
-  match a with
-  | .deferred s =>
-      -- left operand is on-demand: force it, then concatenate with the right
-      return s ++ force b
-  | .concrete s =>
-      match b with
-      | .deferred t =>
-          -- left concrete, right on-demand: force the right and append it
-          return s ++ t
-      | .concrete t =>
-          -- both concrete: ordinary text concatenation
-          return s ++ t
+  match a, b with
+  | .deferred s, _ => return s ++ force b
+  | .concrete s, .deferred t => return s ++ t
+  | .concrete s, .concrete t => return t ++ s   -- concrete/concrete swap only
 -- impl-end
 
 -- proof-start
@@ -80,5 +72,11 @@
       problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
   intro a b
   unfold problem_spec_lazyConcat implementation_lazyConcat
-  cases a <;> cases b <;> rfl
+  cases a <;> cases b <;>
+    first
+      | rfl
+      | (simp [force])
+      | decide
+      | native_decide
+      | (simp_all [force]; done)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Binary concatenation of values that may be produced on demand.

Some text values are not held directly but are produced when first needed: such
a value acts as a stand-in (a proxy) for the concrete text it will eventually
yield, and "forcing" it returns that underlying concrete text. The desired
behaviour is that the binary concatenation operator works uniformly whether each
operand is an ordinary concrete text value or one of these on-demand values:
concatenating two operands always yields the concatenation of the underlying
concrete texts, in left-to-right order.

There are three concrete situations the operator must cover, distinguished only
by which operand (if any) is the on-demand one:

* the left operand is on-demand — it is forced and concatenated with the right;
* the left operand is concrete and the right is on-demand — the right is forced
  and appended to the left;
* both operands are concrete — ordinary text concatenation.

In every case the observable result is the concatenation of the two forced
underlying texts. (Historically only the all-concrete case worked and an
on-demand operand made the concatenation fail, so callers that catch the failure
— such as a value-combining template filter — silently produced the empty
string.)
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Forcing an
-- on-demand operand to its underlying text is modeled DIRECTLY (`force` projects
-- the carried underlying text from the operand) — a deep model whose only inputs
-- are the function's own arguments, not an axiomatized oracle. Concatenation is
-- ordinary text append. No `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An operand of the binary concatenation: either an ordinary concrete text
value, or a value produced on demand that stands in for its underlying text. -/
inductive Operand where
  | concrete : String → Operand
  | deferred : String → Operand
deriving Repr, DecidableEq

/-- Forcing an operand to its underlying concrete text: a concrete operand is its
own text; an on-demand operand yields the text it stands in for. -/
def force : Operand → String
  | .concrete s => s
  | .deferred s => s
-- pure-end

-- post-conditions-start
/-- The result of concatenating two operands is the concatenation of their forced
underlying texts, in left-to-right order — regardless of which operands are
on-demand. -/
def problem_spec_lazyConcat (a b : Operand) (result : String) : Prop :=
  result = force a ++ force b
-- post-conditions-end

-- impl-start
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  match a with
  | .deferred s =>
      -- left operand is on-demand: force it, then concatenate with the right
      return s ++ force b
  | .concrete s =>
      match b with
      | .deferred t =>
          -- left concrete, right on-demand: force the right and append it
          return s ++ t
      | .concrete t =>
          -- both concrete: ordinary text concatenation
          return s ++ t
-- impl-end

-- proof-start
theorem correct_lazyConcat :
    ∀ (a b : Operand),
      problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
  intro a b
  unfold problem_spec_lazyConcat implementation_lazyConcat
  cases a <;> cases b <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. verifier python for same_spec. All 7 attacks are same_spec==True (impl region edited only; axioms/pure/pre/post byte-identical).

### EXECUTED RESULTS (cmd: `bash scripts/lean_verify.sh <f>`):
- pos_control (gold impl): EXIT 0 (verifies, no sorry). `#print axioms correct_lazyConcat` => 'does not depend on any axioms' (clean).
- atk_1 prepatch bug (return "" if any operand deferred): EXIT 1, residual `"" = a✝¹ ++ a✝` — prepatch reproduced.
- atk_2 order swap (force b ++ force a): EXIT 1, residual `a✝ ++ a✝¹ = a✝¹ ++ a✝`.
- atk_3 partial-domain (concrete/deferred drops forced right, returns s): EXIT 1, residual `a✝¹ = a✝¹ ++ a✝`.
- atk_4 control-flow (ignore b, return force a): EXIT 1, residual `a✝¹ = a✝¹ ++ a✝`.
- atk_5 ungrounded echo (return ""): EXIT 1, residual `"" = a✝¹ ++ a✝`.
- atk_6 boundary (duplicate forced left in deferred-left): EXIT 1, residual `a✝¹ ++ a✝¹ ++ a✝ = a✝¹ ++ a✝`.
- atk_7 concrete/concrete swap (t ++ s): EXIT 1, residual `a✝ ++ a✝¹ = a✝¹ ++ a✝`.
Each attack got a MAXIMAL closure attempt (`cases a <;> cases b <;> first | rfl | simp[force] | decide | native_decide | (simp_all[force];done)`); all failed with a genuinely false String-equality goal.

No wrong impl closed with clean axioms, so per protocol step 2 there is NO faithful patch to materialize/resolve (patches={}). verify⇒correct holds on this bundle.

REFINEMENT.MD AUDIT: legs are R (deferred-left `s ++ force b` ↔ __add__ `self.__cast()+other`; concrete-left/deferred-right `s ++ t` ↔ __radd__ `other+self.__cast()`) and I (concrete/concrete ordinary append). `force` is a total pure projection on the function's own Operand argument (directive-8 deep model of `self.__cast()`), NOT an axiomatized oracle => NO A-consumed / A-reference / kind-3 legs; axioms region is empty and byte-identical across all attacks. A-leg correspondence trivially holds (there are none); model↔patch correspondence is faithful (three Lean branches = the three Python dispatch paths __add__/__radd__/pre-existing). result-type generalization (int test_lazy_add) noted and consistent — gold patch is type-generic and verbatim.

VERDICT SOUND: 7 distinct same-spec attacks run (prepatch bug + order + 2 partial-domain/control-flow + ungrounded echo + boundary + concrete-swap); none verifies; positive control verifies clean.

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
None. The postcondition `problem_spec_lazyConcat a b result := result = force a ++ force b` is a total, deterministic functional equality that pins the result uniquely for every (a,b). No same-spec wrong implementation can close its proof. Prepatch bug (atk_1: returns "" when an operand is deferred) leaves the false goal `"" = a ++ b` in the deferred/deferred (and concrete/deferred) case and does NOT verify — exactly the add08/add09/test_lazy_add F2P failures.
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
Binary concatenation of values that may be produced on demand.

Some text values are not held directly but are produced when first needed: such
a value acts as a stand-in (a proxy) for the concrete text it will eventually
yield, and "forcing" it returns that underlying concrete text. The desired
behaviour is that the binary concatenation operator works uniformly whether each
operand is an ordinary concrete text value or one of these on-demand values:
concatenating two operands always yields the concatenation of the underlying
concrete texts, in left-to-right order.

There are three concrete situations the operator must cover, distinguished only
by which operand (if any) is the on-demand one:

* the left operand is on-demand — it is forced and concatenated with the right;
* the left operand is concrete and the right is on-demand — the right is forced
  and appended to the left;
* both operands are concrete — ordinary text concatenation.

In every case the observable result is the concatenation of the two forced
underlying texts. (Historically only the all-concrete case worked and an
on-demand operand made the concatenation fail, so callers that catch the failure
— such as a value-combining template filter — silently produced the empty
string.)
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Forcing an
-- on-demand operand to its underlying text is modeled DIRECTLY (`force` projects
-- the carried underlying text from the operand) — a deep model whose only inputs
-- are the function's own arguments, not an axiomatized oracle. Concatenation is
-- ordinary text append. No `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An operand of the binary concatenation: either an ordinary concrete text
value, or a value produced on demand that stands in for its underlying text. -/
inductive Operand where
  | concrete : String → Operand
  | deferred : String → Operand
deriving Repr, DecidableEq

/-- Forcing an operand to its underlying concrete text: a concrete operand is its
own text; an on-demand operand yields the text it stands in for. -/
def force : Operand → String
  | .concrete s => s
  | .deferred s => s
-- pure-end

-- post-conditions-start
/-- The result of concatenating two operands is the concatenation of their forced
underlying texts, in left-to-right order — regardless of which operands are
on-demand. -/
def problem_spec_lazyConcat (a b : Operand) (result : String) : Prop :=
  result = force a ++ force b
-- post-conditions-end

-- impl-start
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  match a with
  | .deferred s =>
      -- left operand is on-demand: force it, then concatenate with the right
      return s ++ force b
  | .concrete s =>
      match b with
      | .deferred t =>
          -- left concrete, right on-demand: force the right and append it
          return s ++ t
      | .concrete t =>
          -- both concrete: ordinary text concatenation
          return s ++ t
-- impl-end

-- proof-start
theorem correct_lazyConcat :
    ∀ (a b : Operand),
      problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
  intro a b
  unfold problem_spec_lazyConcat implementation_lazyConcat
  cases a <;> cases b <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. verifier python for same_spec. All 7 attacks are same_spec==True (impl region edited only; axioms/pure/pre/post byte-identical).

### EXECUTED RESULTS (cmd: `bash scripts/lean_verify.sh <f>`):
- pos_control (gold impl): EXIT 0 (verifies, no sorry). `#print axioms correct_lazyConcat` => 'does not depend on any axioms' (clean).
- atk_1 prepatch bug (return "" if any operand deferred): EXIT 1, residual `"" = a✝¹ ++ a✝` — prepatch reproduced.
- atk_2 order swap (force b ++ force a): EXIT 1, residual `a✝ ++ a✝¹ = a✝¹ ++ a✝`.
- atk_3 partial-domain (concrete/deferred drops forced right, returns s): EXIT 1, residual `a✝¹ = a✝¹ ++ a✝`.
- atk_4 control-flow (ignore b, return force a): EXIT 1, residual `a✝¹ = a✝¹ ++ a✝`.
- atk_5 ungrounded echo (return ""): EXIT 1, residual `"" = a✝¹ ++ a✝`.
- atk_6 boundary (duplicate forced left in deferred-left): EXIT 1, residual `a✝¹ ++ a✝¹ ++ a✝ = a✝¹ ++ a✝`.
- atk_7 concrete/concrete swap (t ++ s): EXIT 1, residual `a✝ ++ a✝¹ = a✝¹ ++ a✝`.
Each attack got a MAXIMAL closure attempt (`cases a <;> cases b <;> first | rfl | simp[force] | decide | native_decide | (simp_all[force];done)`); all failed with a genuinely false String-equality goal.

No wrong impl closed with clean axioms, so per protocol step 2 there is NO faithful patch to materialize/resolve (patches={}). verify⇒correct holds on this bundle.

REFINEMENT.MD AUDIT: legs are R (deferred-left `s ++ force b` ↔ __add__ `self.__cast()+other`; concrete-left/deferred-right `s ++ t` ↔ __radd__ `other+self.__cast()`) and I (concrete/concrete ordinary append). `force` is a total pure projection on the function's own Operand argument (directive-8 deep model of `self.__cast()`), NOT an axiomatized oracle => NO A-consumed / A-reference / kind-3 legs; axioms region is empty and byte-identical across all attacks. A-leg correspondence trivially holds (there are none); model↔patch correspondence is faithful (three Lean branches = the three Python dispatch paths __add__/__radd__/pre-existing). result-type generalization (int test_lazy_add) noted and consistent — gold patch is type-generic and verbatim.

VERDICT SOUND: 7 distinct same-spec attacks run (prepatch bug + order + 2 partial-domain/control-flow + ungrounded echo + boundary + concrete-swap); none verifies; positive control verifies clean.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13794 lean bundle.

SPEC: problem_spec_lazyConcat a b result := result = force a ++ force b, over Operand = concrete String | deferred String, force = identity projection. Models the post-patch binary concatenation `a + b` of the lazy() __proxy__ (gold __add__ / __radd__ added to django/utils/functional.py).

### Checks performed
1. same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True — spec regions (axioms/pure/pre/post) are byte-identical; the modeled function is unchanged between pre/post, only impl+proof differ. Good.
2. Lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry) and `#print axioms correct_lazyConcat` => 'does not depend on any axioms' — genuine proof, no sorryAx, no axiomatized callee.
3. patch.diff == gold verbatim (adds __add__: self.__cast()+other ; __radd__: other+self.__cast()).
4. Real-repo differential: built lazy(lambda:s,str)() proxies at base_commit worktree and exhaustively evaluated a+b over pool {'', 'a', 'string', 'lazy', 'héllo', 'xxx'} x {concrete, deferred}^2 = 144 cases. In EVERY case str(a+b) == force(a)++force(b). 0 mismatches. Dispatch reasoning in refinement/mapping is correct: __proxy__ subclasses Promise (not str), so str.__add__(proxy) returns NotImplemented and Python falls back to proxy.__radd__ — matching the two-branch Lean model.

The spec is exactly satisfied by the real callee on its entire modeled domain; it is neither too strong nor drifted. No diverging input exists. Result-type generalization (int case test_lazy_add) is out of the modeled String domain and does not create disagreement within the domain.

VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical screen (leakage.screen) passes: no diff markers, no gold-patch lines reproduced (>=8 normalized chars), no patched file path (django/utils/functional.py) or dotted module, no spec-view identifier or comment echoing a distinctive patched symbol, and no _NARRATION terms. same_spec(Solution, Solution_prepatch)=True, so the spec view is stable across variants and not tailored to gold.

Manual review of the spec view (docstring + problem_spec_lazyConcat only; impl/proof elided): the public problem_statement already discloses (a) concatenating a string with a lazy string via the `add` template filter, (b) the result is always the empty string, and (c) the TypeError root cause. The spec view describes only the DESIRED behavior abstractly: concatenation of operands each concrete or 'on-demand' (deferred), result = force a ++ force b in all three positional cases. The gold edit's specifics are NOT revealed anywhere in the spec view: no `__add__`/`__radd__`, no `__proxy__`/`__cast`, no forward/reflected-operator naming, no file path. Identifiers are abstract (Operand/force/lazyConcat).

The three-case decomposition (left-deferred / right-deferred / both-concrete) is the inherent semantics of concatenating a proxy in either operand slot — a consequence of the stated problem, not a disclosure of where/how to edit. The parenthetical 'historically only the all-concrete case worked ... callers that catch the failure ... produced the empty string' merely restates the publicly-stated empty-string symptom in behavioral terms; it names no edit and uses no narration keyword. Nothing leaks beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
