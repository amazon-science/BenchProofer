import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The authority component is built entirely from the
--  parsed pieces — a pure string computation modeled in full below; nothing is
--  delegated to an unchanged callee. The upstream URL splitter that produces
--  those pieces, and the downstream re-assembler that consumes the result, are
--  exercised end-to-end by the differential conformance check, not axiomatized.)
-- axioms-end

-- pure-start
/- Assemble the authority section of a URL from the pieces a parser hands back.

   A URL's authority is the part between the scheme's `//` and the path
   (`userinfo@host:port`). Two pieces are relevant here:

   * `userinfo` — the optional credentials (user, or user:password) that precede
     an `@` in the authority. Empty when the URL carries no credentials.
   * `base` — the host(:port) portion of the authority. The caller has already
     resolved which parsed slot actually holds it (`fallback` below), since a
     known parser quirk can leave the authority slot empty and stash the value
     in the path slot instead; that resolution is a separate concern reproduced
     verbatim here so the assembly sees the right value.

   The assembled authority must carry the credentials whenever they are present:
   the userinfo, an `@`, then the host portion. With no credentials the host
   portion stands alone. This guarantees that a round-trip through a parser that
   exposes credentials separately does not silently discard them. -/
def assembleAuthority (userinfo base : List Char) : List Char :=
  if userinfo = [] then base
  else userinfo ++ ['@'] ++ base

/- Resolve which parsed slot holds the host portion: normally the authority
   slot, but if a parser left it empty the value lives in the path slot. -/
def authorityBase (authoritySlot fallbackSlot : List Char) : List Char :=
  if authoritySlot = [] then fallbackSlot else authoritySlot

/- Single-step unfolds so `loom_solve` discharges the postconditions. -/
@[grind] lemma assembleAuthority_def (userinfo base : List Char) :
    assembleAuthority userinfo base =
      (if userinfo = [] then base else userinfo ++ ['@'] ++ base) := rfl

@[grind] lemma authorityBase_def (authoritySlot fallbackSlot : List Char) :
    authorityBase authoritySlot fallbackSlot =
      (if authoritySlot = [] then fallbackSlot else authoritySlot) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the authority section of a URL from the slots a parser produced:
   `userinfo` (optional credentials), and the two slots `authoritySlot`/`fallbackSlot`
   among which the host portion may have landed. The result is the authority the
   URL should be re-assembled with. When credentials are present they are kept,
   joined to the host portion by an `@`; when absent the host portion stands
   alone. All three inputs are read-only (none declared `mut`); the builder only
   reads them (directive 5) and returns a fresh authority string. -/
method buildAuthority
    (userinfo : List Char) (authoritySlot : List Char) (fallbackSlot : List Char)
    return (out : List Char)
  ensures out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)
  do
    -- impl-start
    let base : List Char :=
      if authoritySlot = [] then fallbackSlot else authoritySlot
    let out : List Char :=
      if userinfo = [] then base
      else userinfo ++ ['@'] ++ base
    return out
    -- impl-end

prove_correct buildAuthority by
  loom_solve
