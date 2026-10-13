import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   The expensive shared object this lookup hands back is identified, for the
   purpose of this behavior, by the key under which it is stored. That
   key-to-object correspondence (equal keys ⇒ the very same shared object,
   distinct keys ⇒ distinct objects) is the type-only refinement declared in
   refinement.md (R) and mechanically validated against the real lookup by
   conformance_check.py (G-CONF). It is not consumed as a Lean contract here, so
   no `axiom` is introduced. -/
-- axioms-end

-- pure-start
/- The storage key for a request that carries an OPTIONAL identifier. A request
   may omit the identifier (`none`), in which case the ambient default
   identifier is meant; otherwise the request carries the identifier explicitly
   (`some u`). The key is the RESOLVED identifier: an omitted identifier is
   first resolved to the ambient default, so that omitting it and naming the
   default explicitly produce the same key. -/
def lookupKey (requested : Option String) (ambient : String) : String :=
  match requested with
  | none   => ambient
  | some u => u

@[grind] lemma lookupKey_none (ambient : String) :
    lookupKey none ambient = ambient := rfl
@[grind] lemma lookupKey_some (u ambient : String) :
    lookupKey (some u) ambient = u := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Hand back the shared object associated with an optional identifier, stored
   so that repeated requests for the same identifier reuse one object instead of
   rebuilding it.

   The identity of the returned object is modeled by the key under which it is
   stored (mapping.md §2: object identity ⟺ key equality), carried as an
   `Option String`. The required behavior is that this key is the *resolved*
   identifier: a request that omits the identifier (`none`) must resolve to the
   ambient default BEFORE the key is taken, so that it shares its object with an
   explicit request for that same default. Consequently the returned key is
   always a present (`some`) resolved identifier — never the bare absent
   sentinel — and never depends on whether the default was named explicitly or
   left implicit.

   Both inputs are read-only — neither is declared `mut` (directive 5): the
   lookup only reads the requested identifier and the ambient default. -/
method sharedHandle (requested : Option String) (ambient : String)
    return (out : Option String)
  ensures out = some (lookupKey requested ambient)
  do
    -- impl-start
    -- PRE-PATCH (buggy) skeleton: the object's identity is taken from the
    -- request AS RECEIVED — the absent/explicit-default resolution happens only
    -- AFTER identity is fixed, so it does not affect which object is returned.
    -- An omitted identifier therefore yields a DISTINCT object from an explicit
    -- mention of the default.
    return requested
    -- impl-end

prove_correct sharedHandle by
  loom_solve
