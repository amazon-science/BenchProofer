import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The per-element resolution this operation applies to each
   member of a sequence is modeled as an arbitrary total function `f`; the
   postconditions hold for EVERY `f`, so it needs no contract (it is strictly
   weaker than any concrete callee). The sequence-reconstruction behaviour — the
   only thing this bundle pins — is modeled DEEPLY in the `pure` region, not
   behind an axiom. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The outcome of reconstructing a sequence from its per-element-resolved
   members. Two reconstruction failures are distinguishable: handing the
   sequence's type a single iterable when that type instead requires its
   members as separate positional arguments, and — dually — handing a type
   its members as separate positional arguments when that type instead takes
   exactly one iterable. -/
inductive RebuildErr where
  | iterableNotAccepted
  | positionalNotAccepted
  deriving DecidableEq

/- The observable content of a reconstructed sequence: whether its type requires
   its members supplied positionally (rather than as one iterable), and the
   members themselves in order. These are the only fields the desired behaviour
   constrains (mapping.md §2). -/
structure SeqVal where
  positionalCtor : Bool
  items : List Int
  deriving DecidableEq

/- Reconstruction that supplies the members as separate positional arguments.
   A type that requires its members positionally accepts them, and the
   reconstructed sequence keeps its type and carries the members through in
   order. Any OTHER sequence type's constructor takes its members as one
   iterable, so handing it the members as separate positional arguments fails —
   except in the degenerate no-member case, where nothing is passed and the
   empty sequence is built. -/
def rebuildPositional (positionalCtor : Bool) (items : List Int) :
    Except RebuildErr SeqVal :=
  if positionalCtor || items.isEmpty then
    Except.ok { positionalCtor := positionalCtor, items := items }
  else Except.error .positionalNotAccepted

/- Reconstruction that hands the type a single iterable of the members. This
   succeeds only for a type that accepts an iterable; a type that instead
   requires positional members cannot be reconstructed this way. -/
def rebuildIterable (positionalCtor : Bool) (items : List Int) :
    Except RebuildErr SeqVal :=
  if positionalCtor then Except.error .iterableNotAccepted
  else Except.ok { positionalCtor := positionalCtor, items := items }

/- The desired reconstruction outcome: a sequence whose every member has been
   independently resolved (here by an arbitrary resolver `f`), reconstructed so
   that it ALWAYS succeeds and keeps both its type and its resolved members in
   order — regardless of whether the type requires positional members. -/
def resolvedSeq (positionalCtor : Bool) (items : List Int) (f : Int → Int) :
    Except RebuildErr SeqVal :=
  Except.ok { positionalCtor := positionalCtor, items := items.map f }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the members of a sequence value independently (each via the resolver
   `f`) and reconstruct the sequence. Desired behaviour: reconstruction must
   succeed for EVERY sequence type and preserve the type, even one that requires
   its members supplied as separate positional arguments; the result carries the
   per-member-resolved values in their original order. (`positionalCtor`
   abstracts "this type must receive its members positionally"; `f` abstracts the
   independent per-member resolution — mapping.md §1/§2.) -/
method reconstructSequence (s : SeqVal) (f : Int → Int)
    return (out : Except RebuildErr SeqVal)
  ensures out = resolvedSeq s.positionalCtor s.items f
  do
    -- impl-start
    -- Resolve each member independently (unchanged across the fix).
    let resolved := s.items.map f
    -- Reconstruct preserving the sequence's type. A type requiring positional
    -- members is reconstructed by supplying them positionally; any other type
    -- is reconstructed from the iterable of resolved members.
    let result : Except RebuildErr SeqVal :=
      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
      else rebuildIterable s.positionalCtor resolved
    return result
    -- impl-end

prove_correct reconstructSequence by
  loom_solve
  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
  split_ifs <;> simp_all
