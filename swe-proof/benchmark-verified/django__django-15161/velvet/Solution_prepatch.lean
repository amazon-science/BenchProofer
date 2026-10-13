import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The import-path selection is modeled DEEPLY and
--  directly as the function under specification: it is a pure two-way choice
--  between the node's assigned simplified public path and its
--  defining-module-qualified name. There is no unchanged outside callee whose
--  contract the proof must assume — hence no `axiom` and no A-reference deep
--  model of a separate callee.)
-- axioms-end

-- pure-start
-- (No pure helpers required: the result is a direct two-way choice over whether
--  the node carries an assigned simplified public path and is of the exact type
--  that path was assigned to.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The deconstructed import path of an expression node.

   An expression node may be assigned a *simplified* public import path
   (`publicPath = some p`) — the short path under which the node's type is also
   importable. The node also knows its defining module (`definingModule`, the
   fully-qualified package in which its class is actually defined) and its class
   name (`className`).

   The deconstructed import path is:
     * the assigned simplified public path `p`, when the node carries one AND its
       runtime type is exactly the type that path was assigned to
       (`exactType = true`);
     * otherwise the node's own defining module joined by `.` to its class name.

   The second arm governs an un-assigned node, and also a node whose runtime
   type is a *subtype* of an assigned type (its type is not the assigned one, so
   the simplified path does not apply and the longer defining-module path is
   reported). `definingModule`, `className`, `publicPath` are read-only carriers
   (not `mut`); the routine builds a fresh result and mutates none of them
   (directive 5). -/
method deconstructPath
    (definingModule : List Char)
    (className : List Char)
    (publicPath : Option (List Char))
    (exactType : Bool)
    return (out : List Char)
  ensures (publicPath ≠ none ∧ exactType = true) → out = publicPath.getD []
  ensures ¬(publicPath ≠ none ∧ exactType = true) →
    out = definingModule ++ ['.'] ++ className
  do
    -- impl-start
    -- PRE-PATCH (buggy): the node is not assigned a simplified public path, so
    -- the deconstructed path is ALWAYS the long defining-module-qualified name,
    -- even when a simplified public path is available and the type is exact.
    let out : List Char :=
      definingModule ++ ['.'] ++ className
    return out
    -- impl-end

prove_correct deconstructPath by
  loom_solve
