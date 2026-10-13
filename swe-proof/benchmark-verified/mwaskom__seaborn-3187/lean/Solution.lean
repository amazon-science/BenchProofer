import Mathlib
-- imports-end

/-!
Numeric tick labels for a legend describing a continuous quantity.

When a legend summarizes a continuous quantity it shows a handful of tick
positions together with a text label for each. The label text is not composed by
the legend builder: it is written by a numeric tick renderer, a piece of shared,
mutable state that arrives already built and is what actually turns a tick
position into a string.

Such a renderer may be in a COMPACTING mode, which is its ordinary default. In
that mode it hoists a magnitude common to the whole tick set out of the
individual labels and writes each tick as a small residual, parking the hoisted
magnitude in a separate string of its own. On an axis that separate string is
drawn next to the ticks, so nothing is lost. A legend has nowhere to put it and
keeps only the per-tick label texts — so labels written by a compacting renderer
read back as residuals rather than as the quantities they are supposed to mark.
Ruling that out is what this specification is about.

Not every renderer can be asked to stop. Whether a given one offers a control for
that mode at all is an intrinsic property of the renderer, exposed here as
`compactionCapable`; it is not something a legend builder may change. A renderer
offering no such control also does no such hoisting, so its labels need no
correcting, and forcing a mode on it is not the builder's business.

Everything else that governs how a renderer writes text is likewise met already
settled, and is carried as two further components of its state. `numeralStyle`
records whether the renderer spells a label as a bare numeral at all: a renderer
may instead be configured to dress its labels up — to typeset them for a
mathematical setting, or to punctuate them by a regional convention — and such a
label is a rendering of the quantity rather than a plain writing of it, so it is
not something a reader recovers a quantity from by reading the text as a number.
`convention` carries the remainder: which sort of renderer it is, and the range of
the quantity it is describing. Neither is a legend builder's to choose: the
renderer is met already configured, and it is that configuration's output the
legend must report.

So what a legend builder is answerable for has three inseparable parts, and the
result is observed as the pair (the renderer state the labels are written from,
the label texts the legend keeps):

  * COMPACTION IS OFF WHERE IT CAN BE TURNED OFF. When the renderer offers the
    control, the labels are written from it with that mode off. The renderer is
    mutable shared state, so which mode it stands in as the labels are written is
    an observable of this operation, not a private detail of it.
  * A RENDERER OFFERING NO SUCH CONTROL IS USED AS IT STANDS. Its mode comes
    through unchanged. This is a preservation claim about the other kind of
    renderer, and it is what distinguishes "turn the mode off where turning it off
    is a thing one can do" from "turn it off always". Either way the capability,
    the numeral style and the convention come through unchanged too: the compacting
    mode is the only component of the renderer's state a legend builder may touch.
  * THE LABELS ARE THAT RENDERER'S OWN. The legend reports exactly the text that
    renderer writes for this tick set, in this order: not text the builder
    composes by some private route, not the text a differently-configured or
    differently-capable renderer would write, and none reordered, dropped or
    duplicated. A renderer settles on ONE way of writing a whole tick set, so a
    tick's label depends on the whole state that renderer stands in and on the
    whole tick set, not on that tick alone.

Together those deliver the property the legend actually needs, stated separately
as a clause of its own: read back on its own, a label recovers the quantity of the
tick it marks. That reading guarantee is claimed exactly where it is the renderer's
to deliver, and no further:

  * where the renderer offers the compaction control, since only there can the
    hoisting be stopped;
  * where the renderer spells its labels as bare numerals, since a label dressed
    up for typesetting or punctuated by a regional convention denotes its quantity
    by that convention and not by being read as a number — no legend builder can
    make such a renderer write plainly, and demanding a plain reading of it would
    be demanding something the renderer does not do;
  * and only across the range of quantities a label can carry back exactly — tick
    positions reach the renderer through a channel that represents an integer
    distinctly only up to 2^53 in magnitude, so past that no renderer could read
    one back whatever mode it stands in.

Nothing whatever is claimed about what a label reads back to while the compacting
mode is still on: losing exactly that is what compacting means.

Two independent places build a legend of this kind. Each meets a renderer already
built, of whichever kind and in whichever mode, and each owes the same guarantee.
The implementations and correctness proofs are supplied separately.
-/

-- axioms-start
/- The numeric tick renderer, and what may be known about the text it writes.

`TickRenderer` is the renderer as a legend builder meets it. `compactionCapable`
says whether it offers a control for the compacting mode at all — an intrinsic
property of the renderer. `compacting` is that mode itself, and it is mutable,
because the mode the labels are written from is part of what a builder is
answerable for. `numeralStyle` says whether the renderer spells a label as a bare
numeral, as against dressing it up for typesetting or punctuating it by a regional
convention; like the capability it is settled before a builder meets the renderer
and is not a builder's to set. `convention` stands for the remainder of what
governs the text: which sort of renderer it is, and the range of the quantity being
described. Both are kept as explicit components because the text genuinely varies
with them, so a renderer's output is a function of its WHOLE state, not of the
compacting mode alone; an abstraction leaving either out would claim more
determinacy than the real renderer has.

`render r ticks` is the text that renderer writes for that tick set, one label per
tick, and `labelValue s` is the quantity a reader recovers from a single label read
back on its own. Both are OPAQUE: no label text is computable here. That is what
keeps the surface faithful — there is no answer key for an implementation to echo
in place of rendering, and the renderer is the only route to a label.

Two facts about the real renderer are CONSUMED, and they are the weakest the
legend guarantee needs:

  * `render_length` — exactly one label per tick, in every mode.
  * `render_uncompacted_faithful` — a renderer that offers the compaction control,
    does not stand in that mode, and spells its labels as bare numerals hoists
    nothing out and dresses nothing up, so each of its labels reads back to the
    full quantity of the tick it describes. Guarded three ways, each because the
    real renderer fails the round trip outside it:
      - `r.numeralStyle = true`, because a renderer configured to typeset its
        labels or to punctuate them regionally writes text that denotes its
        quantity by that convention rather than by being read as a number, so the
        round trip genuinely does not hold there however the compacting mode
        stands; that configuration is settled before the renderer is met and no
        builder can undo it, so an unguarded claim would be false of the real
        renderer at a state it really reaches.
      - `t.natAbs ≤ 9007199254740992` (= 2^53), where the renderer's own numeric
        channel stops representing an integer distinctly: past that a tick is
        snapped to a neighbouring representable quantity before any text is
        written, so the round trip genuinely does not hold there either.

Nothing is assumed about the labels of a renderer standing in the compacting mode,
nor about those of a renderer offering no such control, nor about those of a
renderer that does not spell its labels as bare numerals; two renderers, two modes,
two numeral styles, two conventions or two tick sets need not render alike.
Provenance and the executable soundness
check against the real renderer: mapping.md and axiom_check.py (G-AX). -/
structure TickRenderer where
  compactionCapable : Bool
  compacting : Bool
  numeralStyle : Bool
  convention : Nat
  deriving DecidableEq

axiom render : TickRenderer → List Int → List String
axiom labelValue : String → Int

axiom render_length : ∀ (r : TickRenderer) (ticks : List Int),
    (render r ticks).length = ticks.length

axiom render_uncompacted_faithful : ∀ (r : TickRenderer) (ticks : List Int),
    r.compactionCapable = true → r.compacting = false → r.numeralStyle = true →
    (∀ t ∈ ticks, t.natAbs ≤ 9007199254740992) →
    ∀ (i : Nat), i < ticks.length → labelValue ((render r ticks)[i]!) = ticks[i]!
-- axioms-end

-- pure-start
/-- The renderer the labels must be written from: the same renderer, capability,
numeral style and convention untouched, with the compacting mode off when it offers
a control for that mode; and `none` — nothing to turn off, and nothing a builder
may turn — when it does not. -/
def uncompacted (r : TickRenderer) : Option TickRenderer :=
  if r.compactionCapable then some { r with compacting := false } else none

/-- The reading guarantee over a whole label sequence: one label per tick, and
every label, read back on its own, recovers the full quantity of the tick position
it describes. Stated over the whole sequence because what it rules out is a single
magnitude common to all the ticks being hoisted out of all of them at once. -/
def readsBackToTicks (labels : List String) (ticks : List Int) : Prop :=
  labels.length = ticks.length
  ∧ ∀ (i : Nat), i < ticks.length → labelValue (labels[i]!) = ticks[i]!
-- pure-end
-- post-conditions-start
/-- First site. The result is observed as the pair (the renderer state the labels
are written from, the label texts the legend keeps).

The first two clauses pin `writtenFrom`, split on whether the renderer offers the
compaction control: where it does, the labels are written from it with that mode
off; where it does not, they are written from it exactly as it stands. Either way
the capability, the numeral style and the convention come through untouched, since
none is the builder's to choose — the two clauses together leave the compacting
mode as the only component a builder may have altered.

`labels = render writtenFrom ticks` grounds the legend's text in that very
renderer state: the labels are the ones it writes for this tick set, in this order.

`readsBackToTicks` is the guarantee the legend needs, claimed exactly where it is
the renderer's to deliver: where the renderer offers the compaction control, where
it spells its labels as bare numerals, and across the range of tick quantities a
label carries back exactly. -/
def problem_spec_continuousLegendLabels
    (r : TickRenderer) (ticks : List Int)
    (result : TickRenderer × List String) : Prop :=
  let writtenFrom := result.fst
  let labels := result.snd
  (∀ r', uncompacted r = some r' → writtenFrom = r')
  ∧ (uncompacted r = none → writtenFrom = r)
  ∧ labels = render writtenFrom ticks
  ∧ labels.length = ticks.length
  ∧ (r.compactionCapable = true → r.numeralStyle = true →
      (∀ t ∈ ticks, t.natAbs ≤ 9007199254740992) →
      readsBackToTicks labels ticks)
-- post-conditions-end
-- impl-start
noncomputable def implementation_continuousLegendLabels
    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
  -- Where the renderer offers a control for the compacting mode, take it with
  -- that mode off; otherwise take it as it stands. Then let that renderer write
  -- the whole tick set's labels, and report both it and its text.
  match uncompacted r with
  | some r' => (r', render r' ticks)
  | none    => (r, render r ticks)
-- impl-end
-- proof-start
theorem correct_continuousLegendLabels :
    ∀ (r : TickRenderer) (ticks : List Int),
      problem_spec_continuousLegendLabels r ticks
        (implementation_continuousLegendLabels r ticks) := by
  intro r ticks
  obtain ⟨cap, comp, style, conv⟩ := r
  unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
    uncompacted readsBackToTicks
  cases cap with
  | true =>
    refine ⟨?_, ?_, ?_, ?_, ?_⟩
    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
    · intro h; simp at h
    · simp only [if_true]
    · simp only [if_true]; exact render_length _ _
    · intro _ hstyle hdom
      simp only [if_true]
      refine ⟨render_length _ _, ?_⟩
      intro i hi
      exact render_uncompacted_faithful
        { compactionCapable := true, compacting := false, numeralStyle := style,
          convention := conv }
        ticks rfl rfl hstyle hdom i hi
  | false =>
    refine ⟨?_, ?_, ?_, ?_, ?_⟩
    · intro r' h; simp at h
    · intro _; simp
    · simp
    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
    · intro h; simp at h

-- proof-end
-- post-conditions-start
/-- Second site: the same guarantee owed by the other place a legend of this kind
is built. The renderer is met already built, of whichever kind and in whichever
mode. Where it offers the compaction control the labels are written from it with
that mode off; where it does not, they are written from it exactly as it stands.
Either way the capability, the numeral style and the convention come through
untouched. The labels are that renderer state's own output for
this tick set, in this order, and where the control is offered and the renderer
spells its labels as bare numerals every label reads back to the full quantity of
its tick across the range a label carries back exactly. -/
def problem_spec_legendEntryLabels
    (r : TickRenderer) (ticks : List Int)
    (result : TickRenderer × List String) : Prop :=
  let writtenFrom := result.fst
  let labels := result.snd
  (∀ r', uncompacted r = some r' → writtenFrom = r')
  ∧ (uncompacted r = none → writtenFrom = r)
  ∧ labels = render writtenFrom ticks
  ∧ labels.length = ticks.length
  ∧ (r.compactionCapable = true → r.numeralStyle = true →
      (∀ t ∈ ticks, t.natAbs ≤ 9007199254740992) →
      readsBackToTicks labels ticks)
-- post-conditions-end
-- impl-start
noncomputable def implementation_legendEntryLabels
    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
  -- As at the first site: where the renderer offers a control for the compacting
  -- mode, take it with that mode off; otherwise take it as it stands. That
  -- renderer writes the labels, and both it and its text are reported.
  match uncompacted r with
  | some r' => (r', render r' ticks)
  | none    => (r, render r ticks)
-- impl-end
-- proof-start
theorem correct_legendEntryLabels :
    ∀ (r : TickRenderer) (ticks : List Int),
      problem_spec_legendEntryLabels r ticks
        (implementation_legendEntryLabels r ticks) := by
  intro r ticks
  obtain ⟨cap, comp, style, conv⟩ := r
  unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
    uncompacted readsBackToTicks
  cases cap with
  | true =>
    refine ⟨?_, ?_, ?_, ?_, ?_⟩
    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
    · intro h; simp at h
    · simp only [if_true]
    · simp only [if_true]; exact render_length _ _
    · intro _ hstyle hdom
      simp only [if_true]
      refine ⟨render_length _ _, ?_⟩
      intro i hi
      exact render_uncompacted_faithful
        { compactionCapable := true, compacting := false, numeralStyle := style,
          convention := conv }
        ticks rfl rfl hstyle hdom i hi
  | false =>
    refine ⟨?_, ?_, ?_, ?_, ?_⟩
    · intro r' h; simp at h
    · intro _; simp
    · simp
    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
    · intro h; simp at h

-- proof-end
