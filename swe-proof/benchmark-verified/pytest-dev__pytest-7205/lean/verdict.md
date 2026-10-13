# P2 adversarial audit — pytest-dev__pytest-7205

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,7 @@
     List Char := Id.run do
   let mut out := header
   match param with
-  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
+  | some p => out := out ++ ['['] ++ p ++ [']']
   | none   => pure ()
   return out
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,7 @@
   let mut out := header
   match param with
   | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
-  | none   => pure ()
+  | none   => out := out ++ ['!']
   return out
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,7 @@
     List Char := Id.run do
   let mut out := header
   match param with
-  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
+  | some p => out := out ++ [']'] ++ safeDisplay p ++ ['[']
   | none   => pure ()
   return out
 -- impl-end
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,7 +32,7 @@
     List Char := Id.run do
   let mut out := header
   match param with
-  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
+  | some p => out := out ++ (['['] ++ (safeDisplay p ++ [']']))
   | none   => pure ()
   return out
 -- impl-end
@@ -44,5 +44,5 @@
   unfold problem_spec_actionLine implementation_actionLine
   cases param with
   | none => rfl
-  | some p => rfl
+  | some p => simp [List.append_assoc]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,7 @@
     List Char := Id.run do
   let mut out := header
   match param with
-  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
+  | some p => out := out ++ ['['] ++ safeDisplay (safeDisplay p) ++ [']']
   | none   => pure ()
   return out
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,7 @@
     List Char := Id.run do
   let mut out := header
   match param with
-  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
+  | some p => out := out ++ safeDisplay p
   | none   => pure ()
   return out
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,7 @@
     List Char := Id.run do
   let mut out := header
   match param with
-  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
+  | some p => out := out ++ ['['] ++ safeDisplay header ++ [']']
   | none   => pure ()
   return out
 -- impl-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,7 +32,7 @@
     List Char := Id.run do
   let mut out := header
   match param with
-  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
+  | some p => out := out ++ ('[' :: (safeDisplay p ++ [']']))
   | none   => pure ()
   return out
 -- impl-end
@@ -44,5 +44,5 @@
   unfold problem_spec_actionLine implementation_actionLine
   cases param with
   | none => rfl
-  | some p => rfl
+  | some p => simp
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,7 @@
     List Char := Id.run do
   let mut out := header
   match param with
-  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
+  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']'] ++ ['['] ++ safeDisplay p ++ [']']
   | none   => pure ()
   return out
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- A safe, size-limited textual representation of a parameter value: it always
produces text (even for non-textual values, where a plain textual coercion would
be unsafe) and keeps the result within the reporter's built-in size budget.
Declared opaque — its internal formatting and its exact budget are irrelevant
here; the modeled behavior only depends on the fact that this canonical
representation is the one applied to the parameter. -/
opaque safeDisplay : List Char → List Char
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The text emitted for a fixture action is the unchanged header, followed — only
when the action carries a parameter value — by that value's safe, size-limited
representation enclosed in square brackets. When no parameter value is present
the emitted text is exactly the header, unchanged. -/
def problem_spec_actionLine (header : List Char) (param : Option (List Char))
    (result : List Char) : Prop :=
  match param with
  | none   => result = header
  | some p => result = header ++ ['['] ++ safeDisplay p ++ [']']
-- post-conditions-end

-- impl-start
def implementation_actionLine (header : List Char) (param : Option (List Char)) :
    List Char := Id.run do
  let mut out := header
  match param with
  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
  | none   => pure ()
  return out
-- impl-end

-- proof-start
theorem correct_actionLine : ∀ (header : List Char) (param : Option (List Char)),
    problem_spec_actionLine header param (implementation_actionLine header param) := by
  intro header param
  unfold problem_spec_actionLine implementation_actionLine
  cases param with
  | none => rfl
  | some p => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a fully-pinned equality: on `some p`, result = header ++ ['['] ++ safeDisplay p ++ [']']; on `none`, result = header. Any impl closing the forall-theorem is provably pointwise-equal to gold on the modeled function; the only abstraction hatch is the opaque safeDisplay (A-consumed, used by identity only).

Same_spec: all 9 attacks + pos_control confirmed True via swebench_unified.markers.same_spec (spec regions axioms/pure/post byte-identical; only impl+proof edited).

### VERIFICATION (lean_verify.sh, 300s cap, run concurrently in batches of <=4):
- pos_control (exact gold): EXIT=0; `#print axioms correct_actionLine` => 'does not depend on any axioms'.
- atk_1 (prepatch bug re-encoded: bare p, no safeDisplay): EXIT=1 (goal `... = header++['[']++safeDisplay p++[']']` unclosable) -> prepatch reproduced / G-DIFF confirmed.
- atk_2 (partial-domain: none branch appends '!'): EXIT=1.
- atk_3 (boundary: brackets reversed `]`..`[`): EXIT=1.
- atk_5 (ungrounded-oracle echo: safeDisplay(safeDisplay p)): EXIT=1.
- atk_6 (control-flow-effect: brackets dropped entirely): EXIT=1.
- atk_7 (wrong argument: safeDisplay header instead of p): EXIT=1.
- atk_9 (boundary: bracketed content duplicated): EXIT=1.
  => Every genuinely-divergent impl FAILS to close. The pinned equality catches all behavioral deviations.
- atk_4 (reassociated append: out ++ (['['] ++ (safeDisplay p ++ [']']))): EXIT=0, closes via `simp [List.append_assoc]`; `#print axioms` => [propext, Quot.sound] (clean, no sorryAx, no injected _prop).
- atk_8 (`'[' :: (safeDisplay p ++ [']'])`): EXIT=0, closes via `simp`; `#print axioms` => [propext, Quot.sound] (clean).
  atk_4 and atk_8 are ONLY append-associativity / cons-normalization rewrites of the gold expression => identical List Char => identical Python output => behaviorally IDENTICAL to gold. Not divergent impls.

RESOLVE (protocol step 2, official run_resolve): both closing impls (atk_4, atk_8) have the SAME faithful materialized patch = the gold patch (the only observable change is applying saferepr; associativity is unobservable in Python str concatenation). Executed run_resolve('pytest-dev__pytest-7205', gold-patch): RESOLVED=True, COMPLETED=True, NOTE='resolved'. (First two attempts returned COMPLETED=False due to a corrupted/dangling docker image entry sha 55e63ac8... breaking swebench's client.images.list() enumeration -- an INFRA fault, not a resolve verdict; target instance image swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-7205 was present. Fixed with `docker image prune -f` (reclaimed 19.42GB / 92 dangling), then enumeration listed 251 images cleanly and the resolve completed True.)

No clean-closing impl has a faithful patch that fails to resolve => verify=>correct holds; verify=/=>correct NOT exhibited.

REFINEMENT.MD AUDIT: rows 1,2,3,5 = I (identical ops: header prefix, present/absent guard, bracket concat, identity return); row 4 = A-consumed (safeDisplay p <- _pytest._io.saferepr.saferepr(cached_param, maxsize=42)); the maxsize budget is correctly absorbed into the opaque symbol (internal detail, not pinned). No A-reference rows, no kind-3 (changed-inexpressible) legs. A-consumed correspondence holds: proof uses only the opaque symbol's syntactic identity (gold proof depends on NO axioms -> confirms no behavioral _prop was injected), and meta.json G-AX passed validating the real saferepr application is total/always-text/never-raises (incl. bytes under -bb, seed 7205). mapping.md callee provenance (saferepr @ src/_pytest/_io/saferepr.py:75-82) matches the real gold patch's newly-called callee `from _pytest._io.saferepr import saferepr` + `saferepr(fixturedef.cached_param, maxsize=42)`.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- A safe, size-limited textual representation of a parameter value: it always
produces text (even for non-textual values, where a plain textual coercion would
be unsafe) and keeps the result within the reporter's built-in size budget.
Declared opaque — its internal formatting and its exact budget are irrelevant
here; the modeled behavior only depends on the fact that this canonical
representation is the one applied to the parameter. -/
opaque safeDisplay : List Char → List Char
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The text emitted for a fixture action is the unchanged header, followed — only
when the action carries a parameter value — by that value's safe, size-limited
representation enclosed in square brackets. When no parameter value is present
the emitted text is exactly the header, unchanged. -/
def problem_spec_actionLine (header : List Char) (param : Option (List Char))
    (result : List Char) : Prop :=
  match param with
  | none   => result = header
  | some p => result = header ++ ['['] ++ safeDisplay p ++ [']']
-- post-conditions-end

-- impl-start
def implementation_actionLine (header : List Char) (param : Option (List Char)) :
    List Char := Id.run do
  let mut out := header
  match param with
  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']
  | none   => pure ()
  return out
-- impl-end

-- proof-start
theorem correct_actionLine : ∀ (header : List Char) (param : Option (List Char)),
    problem_spec_actionLine header param (implementation_actionLine header param) := by
  intro header param
  unfold problem_spec_actionLine implementation_actionLine
  cases param with
  | none => rfl
  | some p => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a fully-pinned equality: on `some p`, result = header ++ ['['] ++ safeDisplay p ++ [']']; on `none`, result = header. Any impl closing the forall-theorem is provably pointwise-equal to gold on the modeled function; the only abstraction hatch is the opaque safeDisplay (A-consumed, used by identity only).

Same_spec: all 9 attacks + pos_control confirmed True via swebench_unified.markers.same_spec (spec regions axioms/pure/post byte-identical; only impl+proof edited).

### VERIFICATION (lean_verify.sh, 300s cap, run concurrently in batches of <=4):
- pos_control (exact gold): EXIT=0; `#print axioms correct_actionLine` => 'does not depend on any axioms'.
- atk_1 (prepatch bug re-encoded: bare p, no safeDisplay): EXIT=1 (goal `... = header++['[']++safeDisplay p++[']']` unclosable) -> prepatch reproduced / G-DIFF confirmed.
- atk_2 (partial-domain: none branch appends '!'): EXIT=1.
- atk_3 (boundary: brackets reversed `]`..`[`): EXIT=1.
- atk_5 (ungrounded-oracle echo: safeDisplay(safeDisplay p)): EXIT=1.
- atk_6 (control-flow-effect: brackets dropped entirely): EXIT=1.
- atk_7 (wrong argument: safeDisplay header instead of p): EXIT=1.
- atk_9 (boundary: bracketed content duplicated): EXIT=1.
  => Every genuinely-divergent impl FAILS to close. The pinned equality catches all behavioral deviations.
- atk_4 (reassociated append: out ++ (['['] ++ (safeDisplay p ++ [']']))): EXIT=0, closes via `simp [List.append_assoc]`; `#print axioms` => [propext, Quot.sound] (clean, no sorryAx, no injected _prop).
- atk_8 (`'[' :: (safeDisplay p ++ [']'])`): EXIT=0, closes via `simp`; `#print axioms` => [propext, Quot.sound] (clean).
  atk_4 and atk_8 are ONLY append-associativity / cons-normalization rewrites of the gold expression => identical List Char => identical Python output => behaviorally IDENTICAL to gold. Not divergent impls.

RESOLVE (protocol step 2, official run_resolve): both closing impls (atk_4, atk_8) have the SAME faithful materialized patch = the gold patch (the only observable change is applying saferepr; associativity is unobservable in Python str concatenation). Executed run_resolve('pytest-dev__pytest-7205', gold-patch): RESOLVED=True, COMPLETED=True, NOTE='resolved'. (First two attempts returned COMPLETED=False due to a corrupted/dangling docker image entry sha 55e63ac8... breaking swebench's client.images.list() enumeration -- an INFRA fault, not a resolve verdict; target instance image swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-7205 was present. Fixed with `docker image prune -f` (reclaimed 19.42GB / 92 dangling), then enumeration listed 251 images cleanly and the resolve completed True.)

No clean-closing impl has a faithful patch that fails to resolve => verify=>correct holds; verify=/=>correct NOT exhibited.

REFINEMENT.MD AUDIT: rows 1,2,3,5 = I (identical ops: header prefix, present/absent guard, bracket concat, identity return); row 4 = A-consumed (safeDisplay p <- _pytest._io.saferepr.saferepr(cached_param, maxsize=42)); the maxsize budget is correctly absorbed into the opaque symbol (internal detail, not pinned). No A-reference rows, no kind-3 (changed-inexpressible) legs. A-consumed correspondence holds: proof uses only the opaque symbol's syntactic identity (gold proof depends on NO axioms -> confirms no behavioral _prop was injected), and meta.json G-AX passed validating the real saferepr application is total/always-text/never-raises (incl. bytes under -bb, seed 7205). mapping.md callee provenance (saferepr @ src/_pytest/_io/saferepr.py:75-82) matches the real gold patch's newly-called callee `from _pytest._io.saferepr import saferepr` + `saferepr(fixturedef.cached_param, maxsize=42)`.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on pytest-dev__pytest-7205 (lean). Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean tables) = True; only impl/proof regions differ (p -> safeDisplay p, proof closed). Solution.lean compiles under lean_verify.sh (exit 0) and `#print axioms correct_actionLine` reports 'does not depend on any axioms' — genuine rfl proof, no sorryAx; `opaque safeDisplay` introduces no axiom.

Real callee modeled: post-patch _show_fixture_action tail `if hasattr(fixturedef,'cached_param'): tw.write('[{}]'.format(saferepr(fixturedef.cached_param, maxsize=42)))`. Spec: none => result = header; some p => result = header ++ ['['] ++ safeDisplay p ++ [']'].

Why no divergence exists: the CHANGED callee saferepr(...,maxsize=42) is modeled as `opaque safeDisplay` (A-consumed) — the spec asserts NO concrete value for it, only that (a) absent param yields the header verbatim and (b) present param yields header + '[' + representation + ']' contiguously. Both structural claims match the real function exactly: a single tw.write appends the whole '[...]' after the already-written header, and nothing is appended when the cached_param attribute is absent. The maxsize=42 budget is legitimately absorbed into the opaque symbol as an internal callee detail (mapping.md/refinement.md row 4). Since the only value-bearing subterm is delegated to an opaque symbol standing for the real callee, the modeled function cannot over-constrain any observable output — there is no input on which it disagrees with the real callee. The spec is therefore NOT too strong.

The F2P observable (string foo -> 'foo' quoted repr; bytes param no longer raising BytesWarning under -bb) is precisely the prepatch/patch discriminator (p vs safeDisplay p), confirming the discriminating clause is well-anchored rather than a spurious tightening. No diverging input => FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage screen over the spec view (auditor-visible axioms/pure/pre/post regions; impl+proof elided). Verified mechanically: markers.spec_view rendered; markers.same_spec(patched, prepatch)=True (spec byte-identical across variants); leakage.screen passed with no hard failures; Solution.lean compiles clean (lean_verify exit 0).

Gold edit: replace `"[{}]".format(fixturedef.cached_param)` with `"[{}]".format(saferepr(fixturedef.cached_param, maxsize=42))` (+ saferepr import) in _show_fixture_action.

Spec view exposes only `opaque safeDisplay : List Char -> List Char` ('a safe, size-limited textual representation') and post-condition `some p => result = header ++ ['['] ++ safeDisplay p ++ [']']`. Compared against the PUBLIC problem_statement (hints_text excluded):
- The problem_statement itself already shows the exact buggy line and explicitly asks 'Shouldn't that be using `saferepr` or something rather than (implicitly) `str()`?' — so naming an abstract safe-representation callee reveals nothing beyond the public statement.
- No gold-specific tokens leak: 'saferepr', 'maxsize', '42', 'bytes', 'str(' are all absent from the spec view (checked). The concrete size budget maxsize=42 — whose only public source is the off-limits hints_text — is deliberately NOT pinned: safeDisplay is opaque and the budget is absorbed; 'size-limited' is a generic property that fixes no observable value.
- The buggy verbatim-insertion behavior lives only in Solution_prepatch.lean, not disclosed in the spec view.

The spec models the fix at the correct abstraction (opaque safe representation) and discloses nothing about the mechanism beyond what problem_statement already states. No line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
