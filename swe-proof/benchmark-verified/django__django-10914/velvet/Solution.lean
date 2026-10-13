import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the default mode is a constant the provider supplies
--  directly, modeled deeply as its numeric value.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The framework supplies a default numeric mode for newly-stored uploaded
   files — the value handed straight to the operating system's chmod call. The
   query returns that default mode. A definite, owner-read/write plus
   group/other-read mode is provided so that stored files have a single,
   predictable permission regardless of how the upload was buffered; the
   provider yields the concrete numeric value (decimal 420, i.e. rw-r--r--),
   never an absent/unset sentinel. The provider takes no input and never
   mutates anything (directive 5). The mode is modeled as a `Nat`. -/
method defaultFileMode return (mode : Nat)
  ensures mode = 420
  do
    -- impl-start
    return 420
    -- impl-end

prove_correct defaultFileMode by
  loom_solve
