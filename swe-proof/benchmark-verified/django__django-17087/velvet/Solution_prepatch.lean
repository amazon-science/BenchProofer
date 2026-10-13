import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Constructing the reference is pure structural
--  assembly of name components already in hand — the module path, the chain of
--  enclosing qualifier names, and the member's own name — so no outside callee
--  contract is consumed and nothing is assumed about the environment.)
-- axioms-end

-- pure-start
/- The dotted reference to a member reached through one or more enclosing
   qualifiers.

   A reference is the module path, followed by the FULL chain of enclosing
   qualifier names from outermost to innermost, followed by the member's own
   name. Every enclosing qualifier appears, in order: a member reached through
   several nested qualifiers is named by the whole chain, never by the innermost
   qualifier alone. `clsChain` lists those enclosing qualifier names (outermost
   first); the reference places them between the module path and the member
   name. -/
def referencePath (module : String) (clsChain : List String)
    (memberName : String) : List String :=
  (module :: clsChain) ++ [memberName]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the dotted reference to a member accessed through a non-empty chain of
   enclosing qualifiers, given the module path `module`, the ordered chain of
   enclosing qualifier names `clsChain` (outermost first), and the member's own
   name `memberName`. All three inputs are read-only (none is `mut`; nothing is
   mutated — directive 5).

   The reference is the components `module`, then every qualifier name in
   `clsChain` in order, then `memberName`:

   * it begins with `module` and ends with `memberName`;
   * it contains the ENTIRE enclosing chain `clsChain`, in order, so a member
     nested several qualifiers deep is referenced by the full chain — not by the
     innermost qualifier with the outer ones dropped;
   * consequently it has exactly `clsChain.length + 2` components.

   The discriminating inputs are those whose chain has more than one qualifier:
   there the reference must keep every enclosing qualifier, rather than collapse
   to the innermost one. -/
method buildReference (module : String) (clsChain : List String)
    (memberName : String) return (out : List String)
  require clsChain ≠ []
  ensures out = referencePath module clsChain memberName
  ensures out.length = clsChain.length + 2
  ensures out.head? = some module
  ensures out.getLast? = some memberName
  do
    -- impl-start
    -- Pre-image skeleton: the reference uses ONLY the innermost enclosing
    -- qualifier name (`clsChain.getLast!`), dropping every outer qualifier in
    -- the chain. The frozen spec requires the FULL chain `clsChain`, so for any
    -- chain of length > 1 the result differs from referencePath and
    -- prove_correct MUST fail.
    let out := [module, clsChain.getLast!, memberName]
    return out
    -- impl-end

prove_correct buildReference by
  loom_solve
  all_goals simp_all [referencePath]
