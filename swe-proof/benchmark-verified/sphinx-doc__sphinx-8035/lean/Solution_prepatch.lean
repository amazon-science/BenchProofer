import Mathlib
-- imports-end

/-!
Deciding whether a single *private* member should be documented.

When documentation is being generated for all members of a module or class, each
candidate member is examined in turn and a keep/drop decision is made for it.
For a member considered *private* (and only reached here when it is documented,
or when undocumented members are being kept anyway) the decision is governed by
the "private members" selection the user supplied for this run, which takes one
of three shapes:

  * *no selection* — private members are not wanted at all, so the member is
    dropped;
  * *everything* — every private member is wanted, so the member is kept;
  * *an explicit list of names* — only the named private members are wanted, so
    the member is kept exactly when its own name appears in that list (but a
    member that is only present because it was inherited from an ancestor the
    documentation has been told to leave out is still dropped).

If the member is neither documented nor covered by the "keep undocumented
members" setting, it is dropped outright regardless of the selection.

These cases are exhaustive and mutually exclusive, so the decision is fully
determined by the inputs.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads: which of the three shapes the private-members selection takes, whether
-- the member is documented, whether undocumented members are being kept, whether
-- the member's name is among an explicit selection, and whether the member is an
-- inherited member the documentation was told to leave out. Each of these is a
-- directly-supplied observation (a tag, a Bool, or a list membership test), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The "private members" selection supplied for a documentation run, observed
through the only distinction the keep decision makes: no selection at all,
everything, or an explicit list of member names. -/
inductive PrivateMembersOption where
  | disabled
  | all
  | names (ns : List String)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Whether a private member is kept (documented).

`privateMembers` is the supplied selection, `memberName` the member's own name,
`hasDoc` whether the member carries documentation, `undocMembers` whether
undocumented members are being kept this run, and `dropAsInherited` whether the
member is only present because it was inherited from an ancestor the
documentation was told to leave out.

The member is kept only when it is documented (or undocumented members are being
kept): then `disabled` drops it, `all` keeps it, and an explicit list keeps it
exactly when the member's name appears in the list and it is not a dropped
inherited member. When it is neither documented nor covered by the keep-undocumented
setting it is dropped outright. (Directive 5 frame: the result is pinned in every
case, so no decision is left unconstrained.) -/
def problem_spec_keepPrivateMember
    (privateMembers : PrivateMembersOption) (memberName : String)
    (hasDoc undocMembers dropAsInherited : Bool) (result : Bool) : Prop :=
  result =
    (if hasDoc || undocMembers then
        match privateMembers with
        | PrivateMembersOption.disabled => false
        | PrivateMembersOption.all      => true
        | PrivateMembersOption.names ns =>
            if dropAsInherited then false else ns.contains memberName
      else false)
-- post-conditions-end

-- impl-start
def implementation_keepPrivateMember
    (privateMembers : PrivateMembersOption) (memberName : String)
    (hasDoc undocMembers dropAsInherited : Bool) : Bool := Id.run do
  let mut keep := false
  let enabled :=
    match privateMembers with
    | PrivateMembersOption.disabled => false
    | _                             => true
  keep := enabled && (hasDoc || undocMembers)
  return keep
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- pre-patch impl it cannot close: the spec demands that with an explicit name
-- selection only the named members are kept, but this impl keeps EVERY documented
-- private member whenever the selection is present (the old boolean-flag
-- behavior), so the `names`/`dropAsInherited` arms do not reduce by `rfl`.
theorem correct_keepPrivateMember :
    ∀ (privateMembers : PrivateMembersOption) (memberName : String)
      (hasDoc undocMembers dropAsInherited : Bool),
      problem_spec_keepPrivateMember privateMembers memberName
        hasDoc undocMembers dropAsInherited
        (implementation_keepPrivateMember privateMembers memberName
          hasDoc undocMembers dropAsInherited) := by
  intro pm mn hd um di
  unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
  simp only [Id.run]
  split
  · cases pm with
    | disabled => rfl
    | all => rfl
    | names ns => cases di <;> rfl
  · rfl
-- proof-end
