import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the generated identifier is built purely from its
--  given descriptive label; no other routine is consulted to produce it.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A framework component synthesizes a unique lookup identifier for each
   auto-generated, auto-used helper that wraps a test class's setup/teardown
   routines. The consumer-facing listing of such helpers, by default, omits any
   whose identifier begins with an underscore, surfacing them only under a
   verbose flag. To keep these synthesized helpers out of the default listing,
   the produced identifier must begin with an underscore while otherwise
   carrying its full descriptive label unchanged. Given that descriptive label
   `base`, the routine returns the label with a single leading underscore
   prepended. `base` is a read-only input and is never mutated (directive 5);
   identifiers are modeled per code point as `List Char`. -/
method privatizeName (base : List Char) return (out : List Char)
  ensures out = '_' :: base
  ensures out.head? = some '_'
  do
    -- impl-start
    -- Pre-image skeleton: the descriptive label is returned unchanged, with no
    -- leading underscore. The frozen spec requires a leading '_', so
    -- prove_correct MUST fail.
    return base
    -- impl-end

prove_correct privatizeName by
  loom_solve
