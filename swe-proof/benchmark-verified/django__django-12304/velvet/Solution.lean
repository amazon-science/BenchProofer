import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The constructor's effect is modeled directly: it
--  sets one boolean class flag and leaves the rest of the constructed class
--  untouched. No outside callee's behavior is assumed or pinned.)
-- axioms-end

-- pure-start
/- The observable part of an enumerated-choices class as built by its
   constructor, abstracted to the two observations that matter here:

   - `doNotCallInTemplates` — the boolean class flag a template engine reads to
     decide whether a value that happens to be callable should be invoked with
     no arguments during variable resolution, or left as-is. When this flag is
     true the engine must NOT auto-call the class; when false (the default for
     an arbitrary callable) the engine would call it.
   - `valueToLabel` — the value→label association the constructor builds for the
     class (each enumerated value paired with its display label). It is the rest
     of the constructed state and is what later attribute access on members
     depends on; the construction step under spec must leave it intact.

   Only these touched/observed fields are carried; the bijection to the real
   class object is in mapping.md §2. -/
structure ChoicesClass where
  doNotCallInTemplates : Bool
  valueToLabel : List (Int × List Char)
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The final step of building an enumerated-choices class. The class arrives
   with its value→label association already assembled (`built`); this step
   produces the class as actually published.

   For an enumerated-choices class to be usable as a plain value in a template —
   compared against, or having its members' attributes read — the engine must be
   told NOT to invoke the class (it is callable, and a template engine calls a
   bare callable with no arguments, which here fails). The published class must
   therefore carry `doNotCallInTemplates = true`.

   At the same time this step must not disturb anything else the class already
   holds: the value→label association assembled earlier must survive unchanged,
   so member-attribute access keeps working. `built` is read-only (not `mut`);
   the step constructs the published class from it without mutating it
   (directive 5). The two guarantees together pin the behavior the issue
   demands: the flag is set AND the rest of the construction is preserved. -/
method publishChoicesClass (built : ChoicesClass) return (out : ChoicesClass)
  ensures out.doNotCallInTemplates = true
  ensures out.valueToLabel = built.valueToLabel
  do
    -- impl-start
    return { built with doNotCallInTemplates := true }
    -- impl-end

prove_correct publishChoicesClass by
  loom_solve
