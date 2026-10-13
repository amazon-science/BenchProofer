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
-- PRE-PATCH (buggy): nested subexpressions are rendered by a bare textual
-- conversion that uses the fixed `defaultSettings` profile, IGNORING the
-- printer's active profile `settings`. Any non-default display option is lost
-- in the operand positions.
def implementation_printRelational
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings defaultSettings : Settings)
    (relName : String) (lhs rhs : Expr) : String := Id.run do
  return relName ++ "(" ++ render defaultSettings lhs ++ ", " ++ render defaultSettings rhs ++ ")"
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
-- PRE-PATCH (buggy): nested subexpressions are rendered by a bare textual
-- conversion that uses the fixed `defaultSettings` profile, IGNORING the
-- printer's active profile `settings`. Any non-default display option is lost
-- in the component positions.
def implementation_printLimit
    {Settings Expr : Type}
    (render : Settings → Expr → String) (settings defaultSettings : Settings)
    (dirIsDefault : Bool) (e z z0 dir : Expr) : String := Id.run do
  if dirIsDefault then
    return "Limit(" ++ render defaultSettings e ++ ", " ++ render defaultSettings z ++ ", "
      ++ render defaultSettings z0 ++ ")"
  else
    return "Limit(" ++ render defaultSettings e ++ ", " ++ render defaultSettings z ++ ", "
      ++ render defaultSettings z0 ++ ", dir='" ++ render defaultSettings dir ++ "')"
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
