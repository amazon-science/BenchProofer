import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the module-name selection
-- is a pure decision over the executed module's fully-qualified name and its
-- parent package, modeled DEEPLY below (string equality + suffix test + emptiness
-- test) rather than axiomatized. The proof agent may add `_prop` axioms only if it
-- gets genuinely stuck.
-- axioms-end

-- pure-start
/-- A module's fully-qualified name identifies a top-level entry point when it is
exactly the conventional entry-point name, or when it is a submodule whose final
dotted component is that conventional entry-point name. -/
def isMainEntry (moduleName : List Char) : Bool :=
  moduleName == "__main__".toList || (".__main__".toList).isSuffixOf moduleName
-- pure-end

-- post-conditions-start
/-- When a program is relaunched as a module (`-m`), the module name to pass is
chosen from the executed module's own fully-qualified name and the name of its
parent package. If the executed module is an entry-point module AND a parent
package is present, the parent package's name is used; otherwise the module's own
fully-qualified name is used verbatim. The chosen name is the sole output and is
pinned to the inputs in every case. -/
def problem_spec_relaunchModule
    (moduleName parentPackage : List Char) (result : List Char) : Prop :=
  result =
    (if isMainEntry moduleName && !parentPackage.isEmpty then parentPackage
     else moduleName)
-- post-conditions-end

-- impl-start
def implementation_relaunchModule
    (moduleName parentPackage : List Char) : List Char := Id.run do
  if isMainEntry moduleName && !parentPackage.isEmpty then
    return parentPackage
  else
    return moduleName
-- impl-end

-- proof-start
theorem correct_relaunchModule :
    ∀ (moduleName parentPackage : List Char),
    problem_spec_relaunchModule moduleName parentPackage
      (implementation_relaunchModule moduleName parentPackage) := by
  intro moduleName parentPackage
  unfold problem_spec_relaunchModule implementation_relaunchModule
  simp only [Id.run]
  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
    simp only [h, if_true, pure]
-- proof-end
