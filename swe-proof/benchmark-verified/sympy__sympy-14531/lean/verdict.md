# P2 adversarial audit — sympy__sympy-14531

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
None found. The two postconditions are PINNED TOTAL EQUALITIES: problem_spec_printRelational forces result = relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")" and problem_spec_printLimit forces the exact if/else Limit template, quantified over ALL {Settings Expr}, render, settings, and operands. Any impl observably deviating from gold cannot close (rfl fails). No wrong impl with a clean-axiom closing proof exists, so there is no faithful patch to materialize/resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,11 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printRelational
     {Settings Expr : Type}
-    (render : Settings → Expr → String) (settings _defaultSettings : Settings)
+    (render : Settings → Expr → String) (settings defaultSettings : Settings)
     (relName : String) (lhs rhs : Expr) : String := Id.run do
-  return relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
+  return relName ++ "(" ++ render defaultSettings lhs ++ ", " ++ render defaultSettings rhs ++ ")"
 -- impl-end
 
 -- proof-start
@@ -108,19 +105,16 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printLimit
     {Settings Expr : Type}
-    (render : Settings → Expr → String) (settings _defaultSettings : Settings)
+    (render : Settings → Expr → String) (settings defaultSettings : Settings)
     (dirIsDefault : Bool) (e z z0 dir : Expr) : String := Id.run do
   if dirIsDefault then
-    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
-      ++ render settings z0 ++ ")"
+    return "Limit(" ++ render defaultSettings e ++ ", " ++ render defaultSettings z ++ ", "
+      ++ render defaultSettings z0 ++ ")"
   else
-    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
-      ++ render settings z0 ++ ", dir='" ++ render settings dir ++ "')"
+    return "Limit(" ++ render defaultSettings e ++ ", " ++ render defaultSettings z ++ ", "
+      ++ render defaultSettings z0 ++ ", dir='" ++ render defaultSettings dir ++ "')"
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,11 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printRelational
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
     (relName : String) (lhs rhs : Expr) : String := Id.run do
-  return relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
+  return relName ++ "(" ++ render settings rhs ++ ", " ++ render settings lhs ++ ")"
 -- impl-end
 
 -- proof-start
@@ -108,9 +105,6 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printLimit
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,11 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printRelational
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
     (relName : String) (lhs rhs : Expr) : String := Id.run do
-  return relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
+  return relName ++ "(" ++ render settings lhs ++ "," ++ render settings rhs ++ ")"
 -- impl-end
 
 -- proof-start
@@ -108,9 +105,6 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printLimit
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,9 +63,6 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printRelational
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
@@ -108,19 +105,16 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printLimit
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
     (dirIsDefault : Bool) (e z z0 dir : Expr) : String := Id.run do
   if dirIsDefault then
     return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
-      ++ render settings z0 ++ ")"
+      ++ render settings z0 ++ ", dir='" ++ render settings dir ++ "')"
   else
     return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
-      ++ render settings z0 ++ ", dir='" ++ render settings dir ++ "')"
+      ++ render settings z0 ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,11 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printRelational
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
     (relName : String) (lhs rhs : Expr) : String := Id.run do
-  return relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
+  return "Eq(x, y)"
 -- impl-end
 
 -- proof-start
@@ -108,9 +105,6 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printLimit
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,9 +63,6 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printRelational
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
@@ -108,19 +105,16 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printLimit
     {Settings Expr : Type}
-    (render : Settings → Expr → String) (settings _defaultSettings : Settings)
+    (render : Settings → Expr → String) (settings defaultSettings : Settings)
     (dirIsDefault : Bool) (e z z0 dir : Expr) : String := Id.run do
   if dirIsDefault then
     return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
       ++ render settings z0 ++ ")"
   else
     return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
-      ++ render settings z0 ++ ", dir='" ++ render settings dir ++ "')"
+      ++ render settings z0 ++ ", dir='" ++ render defaultSettings dir ++ "')"
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,11 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printRelational
     {Settings Expr : Type}
-    (render : Settings → Expr → String) (settings _defaultSettings : Settings)
+    (render : Settings → Expr → String) (settings defaultSettings : Settings)
     (relName : String) (lhs rhs : Expr) : String := Id.run do
-  return relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
+  return relName ++ "(" ++ render settings lhs ++ ", " ++ render defaultSettings rhs ++ ")"
 -- impl-end
 
 -- proof-start
@@ -108,9 +105,6 @@
 -- post-conditions-end
 
 -- impl-start
--- `defaultSettings` is the fixed formatting profile a bare textual conversion
--- would use; the active printer renders every nested subexpression at its OWN
--- active profile `settings`, so `defaultSettings` is not consulted here.
 def implementation_printLimit
     {Settings Expr : Type}
     (render : Settings → Expr → String) (settings _defaultSettings : Settings)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering compound symbolic expressions to their textual form with a configurable
formatting profile — the complete rendering profile: the bundle of display options
together with the rendering context in effect (e.g. whether the fragment is being
produced nested inside an enclosing expression or as a bare top-level conversion),
which together govern, among other things, how rational and floating-point atoms
are spelled.

A printer carries an active formatting profile. Each container-style routine
renders a compound expression by delegating every nested subexpression to the
SAME printer — i.e. to the renderer instantiated at the active profile — and then
splicing the resulting fragments into a constant textual template. Because each
subexpression is rendered at the active profile, the chosen display options
propagate uniformly into every nested position.

Two such routines are modeled:

  * a relational application, rendered as `Name(lhs, rhs)` where `Name` is the
    textual operator tag (an input) and `lhs`, `rhs` are the two operand
    subexpressions;
  * a limit expression `Limit(e, z, z0)` — or, when the approach direction is not
    the default one, `Limit(e, z, z0, dir='…')` — whose components `e`, `z`, `z0`
    (and, in the second shape, the direction `dir`) are the nested subexpressions.

The subexpression renderer itself (turning one subexpression into text at a given
profile) is taken as an arbitrary function of the profile and the subexpression,
so the behavior pinned below is exactly "every nested subexpression is rendered at
the active formatting profile, and the surrounding template text is constant."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The subexpression
-- renderer (turning one subexpression into text given a formatting profile) is
-- modeled as an arbitrary function parameter `render : Settings → Expr → String`:
-- the modeled behavior is solely WHICH formatting profile is handed to that
-- renderer for the nested subexpressions, so the result is pinned for every
-- possible subexpression renderer. Hence the spec needs no `opaque`/`axiom`
-- callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: each rendered output is a constant
-- textual template framing the subexpression-renderer applied to each nested
-- subexpression at the active formatting profile.
-- pure-end

-- post-conditions-start
/-- A relational application is rendered as the operator tag, then the two operand
subexpressions — each rendered at the ACTIVE formatting profile `settings` —
spliced into `Name(lhs, rhs)`.

Frame discipline: the operator tag `relName` and the literal punctuation are
pinned; both operand positions are pinned to the renderer at the active profile,
so no output component is left free. -/
def problem_spec_printRelational
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings : Settings)
    (relName : String) (lhs rhs : Expr) (result : String) : Prop :=
  result = relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
-- post-conditions-end

-- impl-start
def implementation_printRelational
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings _defaultSettings : Settings)
    (relName : String) (lhs rhs : Expr) : String := Id.run do
  return relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
-- impl-end

-- proof-start
theorem correct_printRelational :
    ∀ {Settings Expr : Type}
      (render : Settings → Expr → String) (settings defaultSettings : Settings)
      (relName : String) (lhs rhs : Expr),
      problem_spec_printRelational render settings relName lhs rhs
        (implementation_printRelational render settings defaultSettings relName lhs rhs) := by
  intro Settings Expr render settings defaultSettings relName lhs rhs
  unfold problem_spec_printRelational implementation_printRelational
  rfl
-- proof-end

-- post-conditions-start
/-- A limit expression is rendered with all of its components — `e`, `z`, `z0`
(and, when the approach direction is not the default, the direction `dir`) — each
rendered at the ACTIVE formatting profile `settings`, spliced into a constant
template. `dirIsDefault` selects between the two textual shapes.

Frame discipline: every component position is pinned to the renderer at the active
profile and the surrounding template text is constant, so no output component is left
free. -/
def problem_spec_printLimit
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings : Settings)
    (dirIsDefault : Bool) (e z z0 dir : Expr) (result : String) : Prop :=
  result =
    (if dirIsDefault then
        "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
          ++ render settings z0 ++ ")"
      else
        "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
          ++ render settings z0 ++ ", dir='" ++ render settings dir ++ "')")
-- post-conditions-end

-- impl-start
def implementation_printLimit
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings _defaultSettings : Settings)
    (dirIsDefault : Bool) (e z z0 dir : Expr) : String := Id.run do
  if dirIsDefault then
    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
      ++ render settings z0 ++ ")"
  else
    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
      ++ render settings z0 ++ ", dir='" ++ render settings dir ++ "')"
-- impl-end

-- proof-start
theorem correct_printLimit :
    ∀ {Settings Expr : Type}
      (render : Settings → Expr → String) (settings defaultSettings : Settings)
      (dirIsDefault : Bool) (e z z0 dir : Expr),
      problem_spec_printLimit render settings dirIsDefault e z z0 dir
        (implementation_printLimit render settings defaultSettings dirIsDefault e z z0 dir) := by
  intro Settings Expr render settings defaultSettings dirIsDefault e z z0 dir
  unfold problem_spec_printLimit implementation_printLimit
  cases dirIsDefault <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: worked only same_spec(Solution.lean, atk_N)=True for all 7 attacks + pos_control (spec_view elides impl+proof regions; binder-name/comment edits inside impl region are invisible to the projection). Verified concurrently (2 batches of 4 via background bash jobs).

COMMAND per file: `bash scripts/lean_verify.sh <path>` from project root.

### Results
- pos_control.lean (== gold impl): EXIT 0 (verifies, no sorry). #print axioms correct_printRelational / correct_printLimit => BOTH 'does not depend on any axioms' (clean). Positive control good.
- atk_1.lean (PREPATCH BUG: render defaultSettings for both routines — the real bug the patch fixes): EXIT 1, rfl failed at proof lines (82 rel, 129 lim). Prepatch reproduced = it does NOT verify, confirming the spec detects the actual bug.
- atk_2.lean (control-flow/order: swap lhs/rhs in relational): EXIT 1, rfl failed :82.
- atk_3.lean (boundary: drop space after comma in relational template): EXIT 1, rfl failed :82.
- atk_4.lean (control-flow-effect: Limit branches flipped — dir template on default branch): EXIT 1, rfl failed :129.
- atk_5.lean (ungrounded-oracle echo: constant "Eq(x, y)" ignoring inputs): EXIT 1, rfl failed :82.
- atk_6.lean (partial-domain: Limit correct on dirIsDefault=true branch, uses render defaultSettings dir on else branch): EXIT 1, rfl failed :129.
- atk_7.lean (partial-domain profile mismatch: relational rhs rendered at defaultSettings, lhs at active): EXIT 1, rfl failed :82.

All 7 same-spec wrong impls FAIL to verify (exit 1, `rfl` failed — the pinned equality postcondition rejects any observable deviation). ZERO wrong impls closed with a clean-axiom proof, so step-2 patch materialization/resolve is vacuous (nothing to run). verify⇒correct holds for this spec.

A-LEG AUDIT (refinement.md): all legs are R (dirIsDefault:Bool ↔ str(dir)=="+"), A-reference (render settings <sub> ↔ real nested self._print(<sub>) at active profile), or I (string template splice). NO kind-3 (changed-inexpressible). The A-reference legs are correct: `render` is universally quantified (Settings→Expr→String), so the proof consumes no property of it (no A-consumed / no axiom/opaque contract; axiom_check.py is a skip stub, #print axioms confirms zero axiom dependence). The correspondence render settings· ↔ the real container-nested self._print(sub) at active profile (a _print_level-pre-bumped StrPrinter(settings)._print, distinct from top-level sstr) is documented and differential-tested by G-CONF (conf_skip=false, seed random.Random(14531), N=100000, fuzzing sympy_integers∈{T,F} over rational/float-bearing subexprs so active-vs-default is observable). The single behavioral change (active vs default profile for nested subexprs) is modeled directly as which Settings argument is handed to render — faithful to the gold patch which replaced bare %s/str() interpolation with self._print(). R/I legs mechanically covered by G-CONF as stated.

Verdict SOUND: ≥5 (7) distinct same-spec wrong impls run, none closes, positive control verifies clean, prepatch bug reproduced as non-verifying, A-legs sound.

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
None found. The two postconditions are PINNED TOTAL EQUALITIES: problem_spec_printRelational forces result = relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")" and problem_spec_printLimit forces the exact if/else Limit template, quantified over ALL {Settings Expr}, render, settings, and operands. Any impl observably deviating from gold cannot close (rfl fails). No wrong impl with a clean-axiom closing proof exists, so there is no faithful patch to materialize/resolve.
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
Rendering compound symbolic expressions to their textual form with a configurable
formatting profile — the complete rendering profile: the bundle of display options
together with the rendering context in effect (e.g. whether the fragment is being
produced nested inside an enclosing expression or as a bare top-level conversion),
which together govern, among other things, how rational and floating-point atoms
are spelled.

A printer carries an active formatting profile. Each container-style routine
renders a compound expression by delegating every nested subexpression to the
SAME printer — i.e. to the renderer instantiated at the active profile — and then
splicing the resulting fragments into a constant textual template. Because each
subexpression is rendered at the active profile, the chosen display options
propagate uniformly into every nested position.

Two such routines are modeled:

  * a relational application, rendered as `Name(lhs, rhs)` where `Name` is the
    textual operator tag (an input) and `lhs`, `rhs` are the two operand
    subexpressions;
  * a limit expression `Limit(e, z, z0)` — or, when the approach direction is not
    the default one, `Limit(e, z, z0, dir='…')` — whose components `e`, `z`, `z0`
    (and, in the second shape, the direction `dir`) are the nested subexpressions.

The subexpression renderer itself (turning one subexpression into text at a given
profile) is taken as an arbitrary function of the profile and the subexpression,
so the behavior pinned below is exactly "every nested subexpression is rendered at
the active formatting profile, and the surrounding template text is constant."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The subexpression
-- renderer (turning one subexpression into text given a formatting profile) is
-- modeled as an arbitrary function parameter `render : Settings → Expr → String`:
-- the modeled behavior is solely WHICH formatting profile is handed to that
-- renderer for the nested subexpressions, so the result is pinned for every
-- possible subexpression renderer. Hence the spec needs no `opaque`/`axiom`
-- callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: each rendered output is a constant
-- textual template framing the subexpression-renderer applied to each nested
-- subexpression at the active formatting profile.
-- pure-end

-- post-conditions-start
/-- A relational application is rendered as the operator tag, then the two operand
subexpressions — each rendered at the ACTIVE formatting profile `settings` —
spliced into `Name(lhs, rhs)`.

Frame discipline: the operator tag `relName` and the literal punctuation are
pinned; both operand positions are pinned to the renderer at the active profile,
so no output component is left free. -/
def problem_spec_printRelational
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings : Settings)
    (relName : String) (lhs rhs : Expr) (result : String) : Prop :=
  result = relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
-- post-conditions-end

-- impl-start
def implementation_printRelational
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings _defaultSettings : Settings)
    (relName : String) (lhs rhs : Expr) : String := Id.run do
  return relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
-- impl-end

-- proof-start
theorem correct_printRelational :
    ∀ {Settings Expr : Type}
      (render : Settings → Expr → String) (settings defaultSettings : Settings)
      (relName : String) (lhs rhs : Expr),
      problem_spec_printRelational render settings relName lhs rhs
        (implementation_printRelational render settings defaultSettings relName lhs rhs) := by
  intro Settings Expr render settings defaultSettings relName lhs rhs
  unfold problem_spec_printRelational implementation_printRelational
  rfl
-- proof-end

-- post-conditions-start
/-- A limit expression is rendered with all of its components — `e`, `z`, `z0`
(and, when the approach direction is not the default, the direction `dir`) — each
rendered at the ACTIVE formatting profile `settings`, spliced into a constant
template. `dirIsDefault` selects between the two textual shapes.

Frame discipline: every component position is pinned to the renderer at the active
profile and the surrounding template text is constant, so no output component is left
free. -/
def problem_spec_printLimit
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings : Settings)
    (dirIsDefault : Bool) (e z z0 dir : Expr) (result : String) : Prop :=
  result =
    (if dirIsDefault then
        "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
          ++ render settings z0 ++ ")"
      else
        "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
          ++ render settings z0 ++ ", dir='" ++ render settings dir ++ "')")
-- post-conditions-end

-- impl-start
def implementation_printLimit
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings _defaultSettings : Settings)
    (dirIsDefault : Bool) (e z z0 dir : Expr) : String := Id.run do
  if dirIsDefault then
    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
      ++ render settings z0 ++ ")"
  else
    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "
      ++ render settings z0 ++ ", dir='" ++ render settings dir ++ "')"
-- impl-end

-- proof-start
theorem correct_printLimit :
    ∀ {Settings Expr : Type}
      (render : Settings → Expr → String) (settings defaultSettings : Settings)
      (dirIsDefault : Bool) (e z z0 dir : Expr),
      problem_spec_printLimit render settings dirIsDefault e z z0 dir
        (implementation_printLimit render settings defaultSettings dirIsDefault e z z0 dir) := by
  intro Settings Expr render settings defaultSettings dirIsDefault e z z0 dir
  unfold problem_spec_printLimit implementation_printLimit
  cases dirIsDefault <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: worked only same_spec(Solution.lean, atk_N)=True for all 7 attacks + pos_control (spec_view elides impl+proof regions; binder-name/comment edits inside impl region are invisible to the projection). Verified concurrently (2 batches of 4 via background bash jobs).

COMMAND per file: `bash scripts/lean_verify.sh <path>` from project root.

### Results
- pos_control.lean (== gold impl): EXIT 0 (verifies, no sorry). #print axioms correct_printRelational / correct_printLimit => BOTH 'does not depend on any axioms' (clean). Positive control good.
- atk_1.lean (PREPATCH BUG: render defaultSettings for both routines — the real bug the patch fixes): EXIT 1, rfl failed at proof lines (82 rel, 129 lim). Prepatch reproduced = it does NOT verify, confirming the spec detects the actual bug.
- atk_2.lean (control-flow/order: swap lhs/rhs in relational): EXIT 1, rfl failed :82.
- atk_3.lean (boundary: drop space after comma in relational template): EXIT 1, rfl failed :82.
- atk_4.lean (control-flow-effect: Limit branches flipped — dir template on default branch): EXIT 1, rfl failed :129.
- atk_5.lean (ungrounded-oracle echo: constant "Eq(x, y)" ignoring inputs): EXIT 1, rfl failed :82.
- atk_6.lean (partial-domain: Limit correct on dirIsDefault=true branch, uses render defaultSettings dir on else branch): EXIT 1, rfl failed :129.
- atk_7.lean (partial-domain profile mismatch: relational rhs rendered at defaultSettings, lhs at active): EXIT 1, rfl failed :82.

All 7 same-spec wrong impls FAIL to verify (exit 1, `rfl` failed — the pinned equality postcondition rejects any observable deviation). ZERO wrong impls closed with a clean-axiom proof, so step-2 patch materialization/resolve is vacuous (nothing to run). verify⇒correct holds for this spec.

A-LEG AUDIT (refinement.md): all legs are R (dirIsDefault:Bool ↔ str(dir)=="+"), A-reference (render settings <sub> ↔ real nested self._print(<sub>) at active profile), or I (string template splice). NO kind-3 (changed-inexpressible). The A-reference legs are correct: `render` is universally quantified (Settings→Expr→String), so the proof consumes no property of it (no A-consumed / no axiom/opaque contract; axiom_check.py is a skip stub, #print axioms confirms zero axiom dependence). The correspondence render settings· ↔ the real container-nested self._print(sub) at active profile (a _print_level-pre-bumped StrPrinter(settings)._print, distinct from top-level sstr) is documented and differential-tested by G-CONF (conf_skip=false, seed random.Random(14531), N=100000, fuzzing sympy_integers∈{T,F} over rational/float-bearing subexprs so active-vs-default is observable). The single behavioral change (active vs default profile for nested subexprs) is modeled directly as which Settings argument is handed to render — faithful to the gold patch which replaced bare %s/str() interpolation with self._print(). R/I legs mechanically covered by G-CONF as stated.

Verdict SOUND: ≥5 (7) distinct same-spec wrong impls run, none closes, positive control verifies clean, prepatch bug reproduced as non-verifying, A-legs sound.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift/too-strong) attack on sympy__sympy-14531 lean bundle. RESULTS: (1) same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True — spec/post-condition regions byte-identical; the two files differ only in the impl region (render settings vs render defaultSettings), as intended. (2) Solution.lean compiles via lean_verify.sh (exit 0); #print axioms correct_printRelational / correct_printLimit both report 'does not depend on any axioms' — proofs real, no sorryAx. Conformance against the REAL gold-patched repo (StrPrinter._print_Relational charmap branch + _print_Limit): bundled conformance_check.py = 100000/0 disagreements. (4) Independent adversarial re-fuzz (seed 999999, 300000 inputs, extra atoms pi/oo/exp/log/sqrt(Rational)/large+small Floats/deeper compound nesting) = 0 disagreements. (5) Spec is non-vacuous and correctly captures the fix: sstr(Eq(x,Rational(2,3)),sympy_integers=True)=='Eq(x, S(2)/3)' matches shadow while the default profile yields 'Eq(x, 2/3)', so `render settings ·` genuinely models rendering nested subexpressions at the ACTIVE profile (the gold behavior). The nested-vs-top-level _print_level Float distinction (nested Float(1.5)->'1.5' vs top-level '1.50000000000000') is faithfully reproduced by the _print_level-prebumped shadow, matching real output. The universally-quantified abstract `render : Settings -> Expr -> String` neither over- nor under-constrains: it pins WHICH profile is handed to each nested position and constant template text, which is exactly the modeled routines' behavior. No diverging input found — spec is faithful to the real callee, not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). same_spec(Solution, Solution_prepatch) = True (spec region byte-identical). Semantic review of the solver-visible spec view: (1) No diff markers, no reproduced gold-patch line (no `self._print(...)`), no patched file path (`str.py`) or module path, no bug/fix narration. (2) No verbatim patched repo symbol: gold touches _print_Relational/_print_Limit/etc.; spec identifiers are abstract (printRelational/printLimit), and none of the 11 distinctive patched symbols appear in the spec view. (3) The behavior the spec pins — 'render every nested subexpression at the ACTIVE formatting profile' — is exactly what the PUBLIC problem_statement already describes ('StrPrinter settings are not respected by certain subexpressions'; the Eq and Limit examples with sympy_integers=True are shown verbatim there). Encoding correct behavior abstractly is the spec's legitimate job. (4) The spec models only 2 of the 12 patched _print_* methods (Relational, Limit — the two named/exemplified publicly), disclosing LESS than the gold, not more. (5) Discriminating internals (sympy_integers flag, _print_level nested-context/float trailing-zero detail, fuzz seed 14531) live only in mapping.md/refinement.md (auditor-facing), NOT in the spec view; the docstring abstracts them to generic 'display options ... rational and floating-point atoms'. Nothing in the spec view reveals the gold edit beyond the public problem_statement (hints_text is empty here and was not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
