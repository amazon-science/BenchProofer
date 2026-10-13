import Mathlib
-- imports-end

/-!
Building an implicit cross-reference node for a type name that appears in an
object's info field (the inline type annotations attached to documented
parameters and return values).

When such an annotation is turned into a cross-reference, the reference node it
produces carries the metadata a later resolution step uses to find the target:

  * the reference target (the name being linked to);
  * a marker requesting scope-aware (specific) resolution;
  * the surrounding namespace context — the current module name and the
    enclosing class name — so that an unqualified name is resolved relative to
    where the annotation sits rather than searched for everywhere.

Explicit cross-reference roles already record that surrounding namespace
context. The node built here is expected to record the very same context, so an
unqualified type name resolves the way an explicit reference to the same name
would. We model the namespace context as a `RefContext` (each component is
optional, since either may be absent) and the produced node as an `XrefNode`.

A leading `.` or `~` on the target is a sigil that only affects the link target
and display text, not the namespace context; the target with such a sigil
removed is the reference target.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The surrounding namespace context
-- (module, class) is an INPUT to the modeled node-building step, and every node
-- component the step writes is modeled directly. Hence no `opaque`/`axiom` decls.
-- axioms-end

-- pure-start
/-- The surrounding namespace context in force where an annotation sits: the
current module name and the enclosing class name, each optional (absent when
there is no current module / no enclosing class). -/
structure RefContext where
  module : Option String
  cls    : Option String
deriving DecidableEq, Repr, Inhabited

/-- A cross-reference node. `reftarget` is the name to resolve; `refspecific`
requests scope-aware resolution; `pyModule`/`pyClass` carry the surrounding
namespace context the resolver consults. -/
structure XrefNode where
  reftarget   : String
  refspecific : Bool
  pyModule    : Option String
  pyClass     : Option String
deriving DecidableEq, Repr, Inhabited

/-- Whether the target carries a leading `.` or `~` sigil. -/
def hasSigil (target : String) : Bool :=
  target.startsWith "." || target.startsWith "~"

/-- The reference target: the name with a leading sigil removed, if present. -/
def strippedTarget (target : String) : String :=
  if hasSigil target then target.drop 1 else target
-- pure-end

-- post-conditions-start
/-- The node built for an info-field type annotation, given the surrounding
namespace context `ctx` and the annotation `target`. The node requests
scope-aware resolution, its reference target is the sigil-stripped name, and —
crucially — it records the surrounding namespace context: its module and class
equal the current module and enclosing class. -/
def problem_spec_makeXref
    (ctx : RefContext) (target : String) (result : XrefNode) : Prop :=
  result.refspecific = true ∧
  result.reftarget = strippedTarget target ∧
  result.pyModule = ctx.module ∧
  result.pyClass = ctx.cls
-- post-conditions-end

-- impl-start
def implementation_makeXref (ctx : RefContext) (target : String) : XrefNode :=
  Id.run do
    let mut result : XrefNode :=
      { reftarget := target, refspecific := false, pyModule := none, pyClass := none }
    result := { result with refspecific := true }
    result := { result with pyModule := ctx.module }
    result := { result with pyClass := ctx.cls }
    if hasSigil target then
      result := { result with reftarget := target.drop 1 }
    return result
-- impl-end

-- proof-start
theorem correct_makeXref :
    ∀ (ctx : RefContext) (target : String),
      problem_spec_makeXref ctx target (implementation_makeXref ctx target) := by
  intro ctx target
  unfold problem_spec_makeXref implementation_makeXref strippedTarget
  simp only [Id.run, bind, pure]
  by_cases h : hasSigil target <;> simp [h]
-- proof-end
