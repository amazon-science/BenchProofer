import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Decide, for one documentable target, whether the documentation builder is told
   to FORCE its inclusion or to leave the default disposition untouched.

   A target is considered only when it carries documentation text and it sits in a
   context where an owning container can be established (a class- or
   exception-bodied context, or a whole compilation unit). For the container
   contexts, ownership is settled by looking the container name up in the scope
   where the target is actually DEFINED — which, when the target as presented is a
   thin wrapper standing in for another object, is the scope of that underlying
   object rather than the wrapper's own scope. A whole-unit context establishes
   ownership unconditionally. Once ownership holds, the target's name decides
   whether one of the enabled inclusion categories (initializer / dunder-special /
   single-underscore-private) forces inclusion.

   No surrounding callee is axiomatized: the decision is computed structurally
   from the target's recorded fields (mapping.md §3). -/

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure branch decision over the recorded fields of one documentable target:
   establish whether an owning container exists (by consulting the scope in which
   the target is genuinely defined), and, if so, classify the target's name into
   an inclusion category gated by the enabled flags. Every observable is computed
   structurally from the target record; nothing is borrowed from an oracle, so
   there is no consumed axiom. The container-name resolution and scope membership
   that the surrounding, unchanged machinery performs are supplied to the model as
   the target's recorded flags/scopes and exercised structurally by the executable
   conformance check (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The context a documentable target appears in. Only the first three establish a
   potential owner (a documentation-text-bearing target is considered there); the
   `wholeUnit` context establishes ownership unconditionally, the two bodied
   contexts must locate an owning container, and `freestanding` (a plain
   function/method/attribute) never reaches the inclusion decision. -/
inductive Context where
  | classBody        -- a class body
  | exceptionBody    -- an exception class body
  | wholeUnit        -- a whole compilation unit
  | freestanding     -- function / method / attribute
  deriving DecidableEq, Inhabited, Repr

/- What the builder is told about one target:
   * `forceInclude` — override the default and document this target;
   * `noOverride`   — leave the default disposition in place. -/
inductive Decision where
  | forceInclude
  | noOverride
  deriving DecidableEq, Inhabited, Repr

/- One documentable target as the decision sees it.
   * `hasDoc`           — the target carries documentation text;
   * `qualifiedName`    — its fully-qualified name (container path '.' leaf);
   * `ownerViaPathWalk` — for a multi-segment container path (resolved by walking
       the unit's attribute chain — machinery the change does not touch), whether
       that walk yields a container that owns the target;
   * `directScope`      — the name→ownership scope of the target object exactly as
       presented;
   * `resolvedScope`    — the name→ownership scope of the object the target stands
       for once any wrapping is seen through (equal to `directScope` when the
       target is presented directly). Each scope maps a container name to whether
       looking it up there yields a container that owns the target's leaf name. -/
structure DocTarget where
  hasDoc           : Bool
  qualifiedName    : List Char
  ownerViaPathWalk : Bool
  directScope      : List (List Char × Bool)
  resolvedScope    : List (List Char × Bool)
  deriving Inhabited, Repr

/- The container path of a qualified name: everything before its last '.'
   (empty when the name has no '.'). Mirrors splitting on the final dot. -/
def containerPath (s : List Char) : List Char :=
  match s.reverse.dropWhile (· != '.') with
  | []          => []
  | _ :: rest   => rest.reverse

/- Whether a qualified container path is itself multi-segment (contains a '.'). -/
def isMultiSegment (s : List Char) : Bool := s.contains '.'

/- Look a container name up in a scope: yields whether that lookup resolves to a
   container owning the target's leaf name (false when the name is absent). -/
def scopeOwns (scope : List (List Char × Bool)) (key : List Char) : Bool :=
  (scope.find? (fun kv => kv.1 == key)).elim false (·.2)

/- Establish ownership for a bodied context against a chosen scope: an empty
   container path establishes no owner; a multi-segment path defers to the
   attribute-chain walk; a single-segment path is looked up in `scope`. -/
def ownerIn (t : DocTarget) (scope : List (List Char × Bool)) : Bool :=
  let cp := containerPath t.qualifiedName
  if cp.isEmpty then false
  else if isMultiSegment cp then t.ownerViaPathWalk
  else scopeOwns scope cp

/- The contexts whose documentation-text-bearing targets are considered. -/
def isConsidered : Context → Bool
  | .classBody     => true
  | .exceptionBody => true
  | .wholeUnit     => true
  | .freestanding  => false

/- The leaf is an initializer. -/
def isInit (name : List Char) : Bool := name == "__init__".toList

/- The leaf is a dunder-special (not the initializer; starts and ends with '__'). -/
def isSpecial (name : List Char) : Bool :=
  !isInit name && ("__".toList).isPrefixOf name && ("__".toList).isSuffixOf name

/- The leaf is single-underscore-private (not init, not special, starts with '_'). -/
def isPrivate (name : List Char) : Bool :=
  !isInit name && !isSpecial name && ("_".toList).isPrefixOf name

/- Whether the target's name lands in an enabled inclusion category. -/
def categoryEnabled (name : List Char) (incInit incSpecial incPrivate : Bool) : Bool :=
  (isSpecial name && incSpecial) || (isPrivate name && incPrivate) || (isInit name && incInit)

/- The decision for one target. A target is examined only when it carries
   documentation text, its name is not the weak-reference slot, and its context is
   considered. For the bodied contexts ownership is established against the scope
   in which the target is genuinely defined (`resolvedScope`); a whole-unit context
   needs no owner. With ownership established, an enabled category for the leaf
   forces inclusion; otherwise the default disposition stands. -/
def inclusionDecision (ctx : Context) (name : List Char) (t : DocTarget)
    (incInit incSpecial incPrivate : Bool) : Decision :=
  if (name != "__weakref__".toList) && t.hasDoc && isConsidered ctx then
    let owner := match ctx with
      | .classBody     => ownerIn t t.resolvedScope
      | .exceptionBody => ownerIn t t.resolvedScope
      | _              => false
    if (ctx == Context.wholeUnit) || owner then
      if categoryEnabled name incInit incSpecial incPrivate then Decision.forceInclude
      else Decision.noOverride
    else Decision.noOverride
  else Decision.noOverride
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this bundle models one method)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether to force inclusion of one documentable `target` or to leave the
   default disposition. `ctx` is the context the target appears in; `name` its leaf
   name; the three flags say which inclusion categories are enabled. The target is
   read-only — none of `ctx`, `name`, `target`, or the flags is `mut`; the decision
   reads them and returns a verdict, mutating nothing it is handed (directive 5). -/
method inclusionDecisionM (ctx : Context) (name : List Char) (target : DocTarget)
    (incInit : Bool) (incSpecial : Bool) (incPrivate : Bool) return (out : Decision)
  ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
  do
    -- impl-start
    if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
      -- Pre-image skeleton: ownership for a bodied context is settled against the
      -- target's OWN presented scope (`directScope`) rather than the scope of the
      -- object it stands for. When the target is a wrapper, that scope does not
      -- contain the owning container, so ownership wrongly fails. The frozen spec
      -- consults the resolved scope, so prove_correct MUST fail.
      let owner := match ctx with
        | Context.classBody     => ownerIn target target.directScope
        | Context.exceptionBody => ownerIn target target.directScope
        | _                     => false
      if (ctx == Context.wholeUnit) || owner then
        if categoryEnabled name incInit incSpecial incPrivate then
          return Decision.forceInclude
        else
          return Decision.noOverride
      else
        return Decision.noOverride
    else
      return Decision.noOverride
    -- impl-end

prove_correct inclusionDecisionM by
  loom_solve
  all_goals simp_all [inclusionDecision]
