import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A sub-object handled by a composite serializer: an opaque carrier with
   decidable identity. Its only observables here are the text it renders to and
   the entry it leaves in the serializer's declaration registry (`renderSub`);
   its internal structure is irrelevant to the behavior under spec
   (mapping.md §2). -/
structure SubObj where
  id : Nat
deriving Inhabited, DecidableEq

/- ONE rendering step of the ACTIVE serializer, applied to a single sub-object.
   The serializer is STATEFUL as well as configurable, and BOTH halves are
   observable to its caller:

   * `cfg : Bool` selects between two rendering modes (e.g. whether atomic
     numeric literals are printed in one surface form or another). The same
     sub-object can render to DIFFERENT text under different configurations —
     that is the whole point of the configuration.
   * `reg : List Char` is the serializer's DECLARATION REGISTRY: the text it has
     accumulated for the sub-objects it has rendered so far, which the caller
     emits ahead of the composite. Every step extends it.

   One step therefore maps `(cfg, reg, s)` to a PAIR: `.1` is the text `s`
   renders to, `.2` is the registry the serializer carries afterwards. The two
   come from the SAME step and cannot be obtained apart, and a step's text is a
   function of the registry it starts from — so naming the text of a later
   sub-object already commits to the registry left by the earlier ones. That is
   what makes the ORDER of the steps, and the IDENTITY of the serializer that
   takes them, part of what a caller can observe.

   This is an unchanged callee that the composite serializers below dispatch to
   for each of their sub-objects; it is modeled opaquely (an A-reference)
   because the operation under spec does not change WHAT one step does, only
   WHICH serializer takes it — the active one, whose configuration and registry
   are both in play, rather than a throwaway one with default configuration and
   an empty registry. No concrete text and no concrete registry is ever pinned,
   so the proof borrows no soundness from it. Provenance + the executable
   per-step equality check: mapping.md §3 / axiom_check.py (G-AX).

   WHAT AN APPLICATION OF THIS FUNCTION MEANS — read this before refining an
   impl back into code, because it is what the refinement map turns back into
   code. `renderSub cfg reg s` NAMES the step a serializer in state `(cfg, reg)`
   takes on `s`; the state that step leaves is `.2`, and it becomes the
   COMPOSITE's state only where the impl writes it back (`reg := ...`). An
   application whose `.2` is never written back therefore asserts that the
   composite's own serializer did NOT advance, and it materializes as a step on
   a serializer state that is DISCARDED — a probe primed to `(cfg, reg)`, which
   returns the text that step produces and leaves the composite's own state as
   it was — not a step on the composite's own serializer. Only the written-back
   steps are the composite's, and those are what the second `ensures` of each
   method below pins. The rule, and the executable check that validates it
   against the real callee (G-AX check 10), are in mapping.md §2.2. -/
opaque renderSub : Bool → List Char → SubObj → (List Char × List Char)
-- axioms-end

-- pure-start
/- The text one step renders `s` to, starting from registry `reg`. -/
def renderText (cfg : Bool) (reg : List Char) (s : SubObj) : List Char :=
  (renderSub cfg reg s).1

/- The registry the serializer carries after that same step. -/
def renderReg (cfg : Bool) (reg : List Char) (s : SubObj) : List Char :=
  (renderSub cfg reg s).2

/- The serialized form of a binary-tagged composite `tag(a, b)`: the tag,
   followed by its two sub-objects rendered AND SEPARATED inside parentheses.
   Two things are pinned beyond the layout. BOTH sub-objects are rendered under
   the SAME configuration `cfg` that the composite itself is being serialized
   under — the configuration must reach the sub-objects, not be silently dropped
   in favor of a default. And they are rendered by the SAME serializer as the
   composite, in ARGUMENT ORDER: `a`'s step starts from the composite's own
   incoming registry `reg`, and `b`'s step starts from the registry `a`'s step
   left behind (`renderReg cfg reg a`). A serializer that renders `b` first, or
   that renders either sub-object on a throwaway serializer (from an empty
   registry), produces a different second segment. -/
def taggedPair (cfg : Bool) (tag : List Char) (a : SubObj) (b : SubObj)
    (reg : List Char) : List Char :=
  tag ++ "(".toList ++ renderText cfg reg a ++ ", ".toList
      ++ renderText cfg (renderReg cfg reg a) b ++ ")".toList

/- The registry the composite `tag(a, b)` leaves behind: the registry of `reg`
   extended by `a`'s step and then by `b`'s, in that order. Each sub-object is
   rendered exactly ONCE, by the composite's own serializer, so the caller that
   emits this registry ahead of the composite emits the sub-objects' entries in
   the order the composite mentions them. -/
def taggedPairReg (cfg : Bool) (a : SubObj) (b : SubObj)
    (reg : List Char) : List Char :=
  renderReg cfg (renderReg cfg reg a) b

/- The serialized form of the ternary `Limit(e, z, z0)` composite: the literal
   head, followed by its three sub-objects, comma-separated inside parentheses.
   As with `taggedPair`, every sub-object is rendered under the SAME
   configuration `cfg` the composite is serialized under, by the SAME serializer,
   in argument order: `e` from the composite's incoming registry, `z` from the
   registry `e` left, `z0` from the registry `z` left. -/
def limitTriple (cfg : Bool) (e : SubObj) (z : SubObj) (z0 : SubObj)
    (reg : List Char) : List Char :=
  "Limit(".toList ++ renderText cfg reg e ++ ", ".toList
      ++ renderText cfg (renderReg cfg reg e) z ++ ", ".toList
      ++ renderText cfg (renderReg cfg (renderReg cfg reg e) z) z0
      ++ ")".toList

/- The registry the ternary composite leaves behind: `reg` extended by the three
   steps, each taken exactly once, in argument order. -/
def limitTripleReg (cfg : Bool) (e : SubObj) (z : SubObj) (z0 : SubObj)
    (reg : List Char) : List Char :=
  renderReg cfg (renderReg cfg (renderReg cfg reg e) z) z0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Serialize a binary-tagged composite `tag(a, b)` (a relational or similar
   two-argument head) on the ACTIVE serializer. `cfg` is that serializer's
   configuration; `reg` is its declaration registry, which the step EXTENDS and
   which is therefore `mut`; `tag` is the head token; `a` and `b` are the two
   sub-objects. `cfg`, `tag`, `a`, `b` are read-only; the step builds a fresh
   string and mutates none of them (directive 5).

   Desired behaviour, on both observables at once:

   * `out` is the head token followed by `a` and `b` rendered inside
     parentheses, comma-separated, where each sub-object is rendered under the
     composite's OWN configuration `cfg` and by the composite's OWN serializer,
     `a` first and then `b` — `b`'s text is the one produced from the registry
     `a`'s step left behind.
   * `reg` afterwards is the incoming registry extended by exactly those two
     steps, in that order.

   Both halves are pinned because a caller observes both: it emits `reg` ahead
   of `out`. A serializer that governs the composite but is dropped when
   rendering a sub-object (so the sub-object falls back to a default surface
   form), one that renders the two sub-objects in the other order, one that
   renders either of them on a throwaway serializer (leaving `reg` untouched),
   and one that takes a THIRD step whose result it writes back are each excluded
   by these two clauses together — the second clause pins `reg` afterwards to be
   exactly the two steps, so no written-back step can hide.

   What the two clauses do NOT pin, and no pair of post-images can: an
   application of `renderSub` whose result is never written back. That is not a
   step of this serializer at all (see `renderSub` above) — the composite's
   observable behaviour is unchanged by it, so it materializes as this arm plus a
   discarded probe. refinement.md §F proves that mechanically and measures the
   materialization through the official harness. -/
method printTaggedPair (cfg : Bool) (tag : List Char) (a : SubObj) (b : SubObj)
    (mut reg : List Char) return (out : List Char)
  ensures out = taggedPair cfg tag a b regOld
  ensures reg = taggedPairReg cfg a b regOld
  do
    -- impl-start
    -- One step of the composite's own serializer per sub-object, in argument
    -- order: each step reads the registry the previous one left and extends it.
    let ra := renderSub cfg reg a
    reg := ra.2
    let rb := renderSub cfg reg b
    reg := rb.2
    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
    -- impl-end

prove_correct printTaggedPair by
  loom_solve
  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]

/- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
   `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
   each step extends it); `e`, `z`, `z0` are the three sub-objects, read-only.

   Desired behaviour, on both observables at once: `out` is the literal head
   `Limit(` followed by the three sub-objects rendered comma-separated inside
   parentheses — each under the composite's own configuration `cfg`, by the
   composite's own serializer, in argument order (each step starting from the
   registry the previous step left) — and `reg` afterwards is the incoming
   registry extended by exactly those three steps in that order. Dropping `cfg`
   for any sub-object, reordering the three steps, rendering any of them on a
   throwaway serializer, or taking a FOURTH step whose result is written back are
   each excluded by the two clauses together. As at the binary site, an
   application of `renderSub` whose result is never written back is not a step of
   this serializer (see `renderSub` above, mapping.md §2.2, refinement.md §F). -/
method printLimit (cfg : Bool) (e : SubObj) (z : SubObj) (z0 : SubObj)
    (mut reg : List Char) return (out : List Char)
  ensures out = limitTriple cfg e z z0 regOld
  ensures reg = limitTripleReg cfg e z z0 regOld
  do
    -- impl-start
    -- One step of the composite's own serializer per sub-object, in argument
    -- order: each step reads the registry the previous one left and extends it.
    let re := renderSub cfg reg e
    reg := re.2
    let rz := renderSub cfg reg z
    reg := rz.2
    let rz0 := renderSub cfg reg z0
    reg := rz0.2
    -- Assemble the comma-separated triple.
    return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
        ++ rz0.1 ++ ")".toList
    -- impl-end

prove_correct printLimit by
  loom_solve
  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
