import Mathlib
-- imports-end

/-!
Allocating a query alias when registering one join.

A query keeps an ordered registry of joins it has already introduced. Each
registered join is stored under a distinct **alias** (a name), together with a
key describing the join's shape.

The key has two parts:

  * a *base* part — the table, the parent it hangs off, and the relating field;
  * an optional *filter* tag — an extra condition attached to this particular
    join (two joins on the same base relation may carry different filter tags).

Registering a new join either reuses an alias the registry already holds or
allocates a fresh one. An already-registered alias may be reused only when all
three of the following hold of the join it stands for:

  * it is PERMITTED. Permission is governed by a set of aliases supplied with
    the registration whenever the traversal introducing the join is
    multi-valued, or is itself a traversal carrying a restriction of its own;
    failing both circumstances no supplied set governs permission at all and
    every registered alias is permitted;
  * it stands on the SAME BASE relation as the new join;
  * it carries the SAME FILTER tag as the new join — a requirement waived when
    the join is introduced while traversing a relation that carries a
    restriction of its own.

Allocation then proceeds as follows:

  * if one or more aliases may be reused the registry is left unchanged, and the
    alias reused is the new join's own alias when that is itself among them,
    otherwise the most recently registered one;
  * otherwise an alias is allocated and the new join is STORED IN THE REGISTRY
    UNDER IT. The registry is a name-keyed store, so a name holds at most one
    join: storing under a name the registry does not yet hold adds a last entry,
    while storing under a name it already holds replaces that entry's join where
    it already sits — the join that name held on entry is discarded and the
    order of names is unchanged. Nothing constrains the allocated name to be one
    the registry does not already hold.

The consequence that matters: two joins on the same base relation carrying
different filter tags each receive their OWN alias, never a single shared one.
A query attaching two differently-filtered joins to one relation therefore gets
a distinct join for each, rather than only the first with the other dropped.
-/

-- axioms-start
-- No unchanged outside callee contributes a property the specification consumes.
-- The reuse decision (which alias a freshly registered join lands on) and the
-- registry update are modeled DEEPLY over the data — the registry, the
-- permitted-reuse set, and the joins' keys — so there is no `opaque`/`axiom`
-- callee contract here.
-- axioms-end

-- pure-start
/-- An alias (a join name). Modeled as a `Nat` identity; only equality of
aliases is observed. -/
abbrev Alias := Nat

/-- The key of a registered join, restricted to the touched parts:
* `base` — the table / parent / relating-field shape (an injective encoding into
  `Nat`; only equality is observed);
* `filt` — an optional filter tag distinguishing two joins on the same base. -/
structure JoinKey where
  base : Nat
  filt : Option Nat
deriving DecidableEq, Repr

/-- The aliases permission is confined to, taken one circumstance at a time:
* on a traversal carrying a restriction of its own the supplied set governs
  permission;
* on a multi-valued traversal the supplied set likewise governs permission;
* failing both, no set governs (`none`) and every registered alias is
  permitted. -/
def permittedReuse (permittedAliases : List Alias)
    (multiValued restrictedTraversal : Bool) : Option (List Alias) :=
  if restrictedTraversal then some permittedAliases
  else if multiValued then some permittedAliases
  else none

/-- Whether one registered entry may be reused for `newJoin`. Three conditions,
all required:
* PERMISSION — `reuse` names the aliases permission is confined to (`none` =
  every registered alias is permitted);
* the SAME BASE relation;
* the SAME filter tag — waived when the join is introduced while traversing a
  relation that carries a restriction of its own, so where that waiver does not
  apply two joins sharing a base but carrying different filter tags may never be
  reused for one another. -/
def eligible (reuse : Option (List Alias)) (restrictedTraversal : Bool)
    (newJoin : JoinKey) (p : Alias × JoinKey) : Bool :=
  let permitted : Bool := match reuse with
    | none   => true
    | some s => s.contains p.1
  permitted && p.2.base == newJoin.base
            && (restrictedTraversal || p.2.filt == newJoin.filt)

/-- Storing `newJoin` in the registry under the name `a`.

The registry is a NAME-KEYED STORE: a name holds at most one join, so this is
not an unconditional append. Storing under a name the registry does not yet hold
adds a last entry; storing under a name it already holds REPLACES that entry's
join where it already sits, discarding the join that name held on entry and
leaving the order of names unchanged. Nothing constrains the name being
allocated to be one the registry does not already hold, so both cases occur. -/
def registryStore (registry : List (Alias × JoinKey)) (a : Alias) (k : JoinKey)
    : List (Alias × JoinKey) :=
  if registry.any (fun p => p.1 == a) then
    registry.map (fun p => if p.1 == a then (a, k) else p)
  else
    registry ++ [(a, k)]

/-- The aliases that may be reused, in registration order. -/
def matchCandidates (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (reuse : Option (List Alias)) (restrictedTraversal : Bool) : List Alias :=
  registry.filterMap (fun p =>
    if eligible reuse restrictedTraversal newJoin p then some p.1 else none)

/-- The allocation outcome for `newJoin` given the permitted-reuse set `reuse`.
`newJoinAlias` is the alias the new join already carries (its own name). When at
least one alias may be reused the registry is left unchanged and:
* if the new join's own alias is itself among them, it is reused (preferred);
* otherwise the most recently registered one is reused.
When none may be reused, `freshAlias` is allocated and the new join is STORED in
the registry under it (`registryStore`): a last entry when the registry does not
already hold that name, a replacement in place when it does. -/
def chooseAlias (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (reuse : Option (List Alias))
    (restrictedTraversal : Bool) : Alias × List (Alias × JoinKey) :=
  let cands := matchCandidates registry newJoin reuse restrictedTraversal
  if cands.isEmpty then
    (freshAlias, registryStore registry freshAlias newJoin)
  else if cands.contains newJoinAlias then
    (newJoinAlias, registry)
  else
    (cands.getLastD freshAlias, registry)

/-- The registration outcome, on EITHER governing regime: the permitted-reuse
set is `permittedReuse`. -/
def registrationOutcome (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
    (multiValued restrictedTraversal : Bool)
    : Alias × List (Alias × JoinKey) :=
  chooseAlias registry newJoin newJoinAlias freshAlias
    (permittedReuse permittedAliases multiValued restrictedTraversal)
    restrictedTraversal
-- pure-end

-- post-conditions-start
/-- The registration outcome for `newJoin`, on BOTH governing regimes.

`result` is exactly `registrationOutcome`: an already-registered alias may be
reused only when it is permitted, stands on the same base relation, and carries
the same filter tag — that last requirement waived where the join is introduced
while traversing a relation carrying a restriction of its own; permission is
governed by `permittedAliases` on such a traversal and on a multi-valued one,
and by nothing at all ("every alias") when neither circumstance holds. Among
the aliases that may be reused the new join's own alias wins if itself among
them, else the most recent one; the registry is left untouched whenever an alias
is reused, and otherwise the new join is STORED under the allocated name in the
name-keyed registry — a last entry when that name is not already held, a
replacement of the join held there, in place, when it is. -/
def problem_spec_addJoin
    (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
    (multiValued : Bool) (restrictedTraversal : Bool)
    (result : Alias × List (Alias × JoinKey)) : Prop :=
  result = registrationOutcome registry newJoin newJoinAlias freshAlias
             permittedAliases multiValued restrictedTraversal
-- post-conditions-end

-- impl-start
def implementation_addJoin
    (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
    (multiValued : Bool) (restrictedTraversal : Bool)
    : Alias × List (Alias × JoinKey) := Id.run do
  -- The aliases permission is confined to: the supplied set only on a
  -- multi-valued traversal, otherwise "every alias permitted" — a traversal
  -- carrying a restriction of its own is not distinguished as a circumstance of
  -- its own, so permission there is NOT confined to the supplied set.
  let reuse : Option (List Alias) :=
    if multiValued then some permittedAliases else none
  -- One single reusability test on every route: the base parts must agree, and
  -- the filter tag is never consulted.
  let mut cands : List Alias := []
  for p in registry do
    let permitted : Bool := match reuse with
      | none   => true
      | some s => s.contains p.1
    if permitted && p.2.base == newJoin.base then
      cands := cands ++ [p.1]
  -- None may be reused: allocate a fresh alias and register the new join.
  if cands.isEmpty then
    return (freshAlias, registry ++ [(freshAlias, newJoin)])
  -- An alias may be reused; the registry is unchanged. Prefer the new join's
  -- own alias if it is itself among them, otherwise the most recent one.
  if cands.contains newJoinAlias then
    return (newJoinAlias, registry)
  return (cands.getLastD freshAlias, registry)
-- impl-end


-- proof-start
theorem correct_addJoin :
    ∀ (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
      (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
      (multiValued : Bool) (restrictedTraversal : Bool),
      problem_spec_addJoin registry newJoin newJoinAlias freshAlias
          permittedAliases multiValued restrictedTraversal
        (implementation_addJoin registry newJoin newJoinAlias freshAlias
          permittedAliases multiValued restrictedTraversal) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
