import Mathlib
-- imports-end

/-!
Constructing a callable that carries identity metadata.

A callable carries a bundle of identity attributes (a human-readable name, the
defining module, and a qualified name), and it may record that it transparently
stands in for another callable. Separately from that metadata, a callable is
either self-sufficient — a caller runs it supplying only the arguments of the call
itself — or it still expects the object it belongs to to be handed in first.

Each identity attribute of a callable sits at TWO layers. The callable's own
attribute table may hold an entry for it, and the kind of thing the callable is may
answer for it as well; which of the two a reader of the attribute is answered from
depends on the callable. So what the callable's own table holds and what a reader
observes are two separate facts about it, and they need not agree.

A freshly synthesised callable holds nothing in its own table, and the
general-purpose machinery it is built out of answers for none of these attributes
either, so a reader of any of them observes nothing at all. It is nonetheless
self-sufficient: the object it acts for is already built into it. When such a
callable is meant to act on behalf of an existing one, the existing callable's
identity is transferred onto it — in two
passes, attribute by attribute from what a reader observes on the original, and
then the original's own table laid over the synthesised callable's table as a
whole — so that downstream code inspecting the synthesised callable observes the
original identity; and the callable handed back is still the self-sufficient one,
because callers go on to run it with the arguments of the call alone.

How much identity the original holds, and at which of its layers, is not assumed.
A plain function is observed to hold all three attributes while its own table holds
none of them; a callable that keeps its identity in its own table may hold entries
for only some of them, may hold an entry whose content is nothing in particular,
and may hold an entry that disagrees with what a reader of it observes. The
required behavior is claimed of every callable the step can be handed.
-/

-- axioms-start
-- No opaque callees are consumed: the metadata transfer is modeled deeply in the
-- `pure` region (see `copyIdentity`), so the corresponding library routine is an
-- A-reference validated by axiom_check.py rather than a consumed axiom.
-- axioms-end

-- pure-start
/-- What is held for one identity attribute at one layer.

A layer either holds no entry at all for an attribute, or holds one. When it holds
one, the entry's content need not be text: an entry whose content is nothing in
particular is perfectly ordinary. So `vacant` (no entry) and `filled none` (an
entry holding nothing in particular) are DISTINCT states, and both are distinct
from `filled (some s)` (an entry holding the text `s`). The distinction is
load-bearing: it is presence of the entry, not textual content, that decides
whether this entry is the one handed on when identity is transferred. -/
inductive AttrSlot where
  | vacant
  | filled (content : Option String)
  deriving DecidableEq, Repr

/-- The entry that survives when `src`'s layer is laid over `dst`'s: `src`'s entry
whenever `src` holds one — content and all, whatever that content is — and
otherwise the entry `dst` already held. Holding an entry is what wins here; what
the entry contains is carried along but never consulted. -/
def AttrSlot.overlay : AttrSlot → AttrSlot → AttrSlot
  | .vacant,   dst => dst
  | .filled c, _   => .filled c

/-- One identity attribute of a callable, at both of its layers.

`observed` is what a reader of that attribute on this callable is answered with,
and is `vacant` when the callable has no such attribute at all. `ownEntry` is what
the callable's OWN attribute table holds for it, and is `vacant` when its table
holds no entry for it, in which case a reader is answered by the kind of thing the
callable is.

The two layers can disagree: the kind of thing a callable is may answer for an
attribute ahead of the callable's own table, and then the table's entry is not what
a reader observes — while it is still the entry that table hands on when the table
as a whole is laid over another callable's. For a callable whose readers are
answered from its own table first — which is the case for a freshly synthesised
one — `observed` is `ownEntry` laid over whatever its kind answers for. -/
structure IdentityAttr where
  observed : AttrSlot
  ownEntry : AttrSlot
  deriving DecidableEq, Repr

/-- The identity metadata a callable carries, together with how it can be run.

Each of the three textual fields is one identity attribute at both of its layers
(see `IdentityAttr`). `wrapped` records whether the callable transparently
delegates to another callable. `selfSufficient` records whether a caller can run
the callable supplying only the arguments of the call itself; a callable that still
expects the object it belongs to to be handed in first is not self-sufficient. -/
structure CallableAttrs where
  name           : IdentityAttr
  module         : IdentityAttr
  qualname       : IdentityAttr
  wrapped        : Bool
  selfSufficient : Bool
  deriving DecidableEq, Repr

/-- A freshly synthesised callable. Its own table holds nothing at all, and the
general-purpose machinery it is made of answers for none of the three attributes
either — so a reader of any of them observes nothing, which is precisely the
identity such a callable lacks. It does not yet delegate to any other callable. It
is self-sufficient: the object it acts for is already built into it, so a caller
runs it with the arguments of the call alone. -/
def bareCallable : CallableAttrs :=
  { name     := { observed := .vacant, ownEntry := .vacant },
    module   := { observed := .vacant, ownEntry := .vacant },
    qualname := { observed := .vacant, ownEntry := .vacant },
    wrapped := false, selfSufficient := true }

/-- Transfer onto `dst` the identity `src` supplies for ONE attribute, in the two
passes the transfer really makes. First the attribute is placed on `dst` from what
a reader observes on `src`, and nothing is placed when `src` has no such attribute.
Then `src`'s own table entry is laid over that placement, so `src`'s table entry is
the one that survives whenever its table holds one. Both passes write to `dst`'s
own table, and what `dst` is then observed to hold is that table's new entry laid
over whatever `dst`'s kind already answered for. -/
def IdentityAttr.transfer (src dst : IdentityAttr) : IdentityAttr :=
  let entry := src.ownEntry.overlay (src.observed.overlay dst.ownEntry)
  { observed := entry.overlay dst.observed, ownEntry := entry }

/-- Transfer onto `dst` the identity that `src` supplies. Each of the three
attributes is transferred as `IdentityAttr.transfer` describes. After the transfer,
`dst` is recorded as delegating to `src`. The transfer concerns identity only: the
callable handed back is `dst`, so how it can be run stays `dst`'s and is unaffected
by `src`. -/
def copyIdentity (src dst : CallableAttrs) : CallableAttrs :=
  { name           := src.name.transfer dst.name,
    module         := src.module.transfer dst.module,
    qualname       := src.qualname.transfer dst.qualname,
    wrapped        := true,
    selfSufficient := dst.selfSufficient }

/-- The entry a callable whose own table starts out empty ends up holding in that
table for one identity attribute of `src`, once `src`'s identity has been
transferred onto it: `src`'s own table entry whenever `src`'s table holds one — the
same content, whatever that content is — and otherwise what a reader observes on
`src`. Both of `src`'s layers are consulted, and the table layer is the one that
survives, because the table is laid over as a whole after the per-attribute pass
has run. -/
def transferredEntry (src : IdentityAttr) : AttrSlot :=
  src.ownEntry.overlay src.observed
-- pure-end

-- pre-conditions-start
/-- Admissibility: none. The step is defined for every callable it can be handed,
whatever entries that callable holds at either layer and however the callable itself
has to be run. In particular a callable holding entries for only some of the three
attributes is admissible; so is one holding an entry whose content is nothing in
particular; so is one whose own table holds an entry that disagrees with what a
reader of it observes; and so is one that is not runnable on its own until the
object it belongs to is handed in. The claim below is therefore made over the whole
domain rather than over a distinguished part of it. -/
def problem_pre_attachIdentity (_source : CallableAttrs) : Prop := True
-- pre-conditions-end

-- post-conditions-start
/-- The callable bound to act on behalf of `source` must expose `source`'s
identity.

For each identity attribute, the entry the result holds in its OWN table is the
entry `source`'s own table holds whenever `source`'s table holds one — the same
content, whatever that content is, and in particular an entry holding nothing in
particular is handed on as such rather than being treated as no entry at all — and
otherwise what a reader observes on `source`. Where `source` supplies nothing at
either layer, the result's table is left as empty of that attribute as the freshly
synthesised callable's was.

What a reader OBSERVES on the result follows from that table, because what is
handed back is the synthesised callable: its readers are answered from its own
table, and the machinery it is made of answers for none of the three attributes on
its own account. So for each of the three a reader observes exactly the transferred
entry — each is held exactly when `source` supplies it at one of its layers, with
the same content, and none is held at all when `source` supplies nothing. The
result is recorded as delegating to `source`.

Carrying that identity must not cost the result its usability: the result is
self-sufficient, so a caller runs it with the arguments of the call alone rather
than having to hand in the object `source` belongs to. This holds no matter how
`source` itself has to be run, because what is handed back is the synthesised
callable wearing `source`'s identity and never `source`. -/
def problem_spec_attachIdentity (source : CallableAttrs) (result : CallableAttrs) : Prop :=
  result.name.ownEntry = transferredEntry source.name ∧
  result.name.observed = transferredEntry source.name ∧
  result.module.ownEntry = transferredEntry source.module ∧
  result.module.observed = transferredEntry source.module ∧
  result.qualname.ownEntry = transferredEntry source.qualname ∧
  result.qualname.observed = transferredEntry source.qualname ∧
  result.wrapped = true ∧
  result.selfSufficient = true

/-- The obligation: the required behavior holds at EVERY admissible callable.
Stating the quantifier and the admissibility condition here, rather than leaving
them to the proof, is what makes the domain of the claim part of the
specification instead of an artifact of how it happens to be proved. -/
def problem_spec_total_attachIdentity (impl : CallableAttrs → CallableAttrs) : Prop :=
  ∀ source, problem_pre_attachIdentity source →
    problem_spec_attachIdentity source (impl source)
-- post-conditions-end

-- impl-start
/-- Pre-patch behavior: the freshly synthesised callable is returned as-is,
WITHOUT transferring `source`'s identity onto it. The resulting callable holds
none of `source`'s identity — no name, no module and no qualified name at all,
at either of their layers. -/
def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
  let mut bound : CallableAttrs := bareCallable
  return bound
-- impl-end

-- proof-start
theorem correct_attachIdentity :
    problem_spec_total_attachIdentity implementation_attachIdentity := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl (G-DIFF)
-- proof-end
