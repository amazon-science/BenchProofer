import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The downstream value lookup: given a fully resolved name (a concrete sequence
   of code points), it returns the value associated with that name in the current
   environment. It is a function of the resolved name ONLY — two names with the
   same resolved content yield the same value. We pin no specific value (the
   weakest sufficient contract): the spec uses only that the result is determined
   by the resolved name. This callee is unchanged by the behavior under
   specification. Provenance + executable soundness check: mapping.md /
   axiom_check.py (G-AX). -/
axiom resolveName : List Char → List Char
-- axioms-end

-- pure-start
/- The only lookup outcome the desired behavior distinguishes from success: a
   name that reached the lookup without having been resolved to a concrete
   sequence of code points cannot be looked up. -/
inductive LookupErr where
  | unresolvedName
  deriving DecidableEq

/- A name to look up. It may arrive already resolved (a concrete sequence of code
   points), or deferred — a not-yet-forced computation that, when forced, yields
   its content. Both carriers observe the same underlying content; they differ
   only in whether forcing is required before the content can be used as a lookup
   name (mapping.md §2). -/
inductive Name where
  | eager (content : List Char)
  | deferred (content : List Char)

/- The underlying content of a name, regardless of how it arrived. -/
def Name.content : Name → List Char
  | .eager s => s
  | .deferred s => s

/- Whether a name still needs forcing before its content is usable. -/
def Name.isDeferred : Name → Bool
  | .eager _ => false
  | .deferred _ => true

/- Forcing a name to its resolved content. On an already-resolved name this is
   the identity; on a deferred name it performs the pending computation. Total:
   defined for every name, so forcing always succeeds. -/
def force (nm : Name) : List Char := nm.content
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Look up the value associated with a name.

   Desired behavior: the name may be supplied either already resolved or as a
   deferred computation that yields the name when forced. The lookup must depend
   ONLY on the resolved content of the name — a deferred name and an already
   resolved name with the same content must produce the same value — and forcing
   must always succeed, so the lookup never fails on a deferred name. The result
   is therefore exactly the value associated with the forced (resolved) content.

   `nm` is the read-only name to resolve (not `mut`): the routine consumes it and
   never alters it (directive 5). A name is modeled as its content (a `List Char`)
   together with whether it is deferred (mapping.md §2). -/
noncomputable section
method lookupValue (nm : Name) return (out : Except LookupErr (List Char))
  ensures out = Except.ok (resolveName (force nm))
  do
    -- impl-start
    -- PRE-PATCH (buggy): the name is used as a lookup name WITHOUT first forcing
    -- it. An already-resolved name works, but a deferred name cannot be used as a
    -- lookup name in this unforced state, so the lookup fails on it.
    if nm.isDeferred then
      return Except.error LookupErr.unresolvedName
    else
      return Except.ok (resolveName nm.content)
    -- impl-end
end

prove_correct lookupValue by
  loom_solve
