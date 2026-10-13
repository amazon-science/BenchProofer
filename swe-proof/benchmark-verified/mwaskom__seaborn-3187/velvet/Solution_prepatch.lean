import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The numeric tick renderer used to build a brief numeric legend: given the
   renderer as installed, two display-mode switches, and a list of tick
   positions, it returns one printed label per tick.

   `RendererConfig` is an opaque handle for the renderer AS INSTALLED — its own
   presentation settings and the axis interval it is attached to — apart from the
   two switches below, which are what a caller may still change. Nothing here
   inspects the handle; it only appears as an argument to these callees.

   The two switches are independent ways the renderer is *allowed* to abbreviate
   the printed labels by hoisting something shared out of them:
     * `offsetMode`  — when on, a common additive term shared by every tick may be
                       factored out of the labels (so a label prints only each
                       tick's deviation from that shared term);
     * `scaleMode`   — when on, a common multiplicative power-of-ten shared by
                       every tick may be factored out of the labels (so a label
                       prints only the leading digits).
   Whatever the renderer hoists out, it reports SEPARATELY rather than in any
   label: `sharedTerm` is that separately-reported term, and it is the empty
   string exactly when nothing was hoisted out and each label therefore stands on
   its own. This — not the numeric text of a label — is the weakest fact legend
   correctness needs, because a legend has nowhere to display a separately
   reported term: whatever is hoisted out of the labels is simply lost. It is
   also the only fact that is TRUE of every renderer configuration: a renderer
   may legitimately be set up to print typeset or marked-up labels that no
   numeric reading parses at all, yet still hoist nothing.

   This renderer is PARTIAL, and the model says so instead of quietly assuming
   otherwise. For some installations and tick lists it yields no labels at all:
   it fails outright rather than returning, and the failure escapes the region
   modeled here, so no legend is produced for a clause to describe.
   `renders cfg offsetMode scaleMode ticks` is the modeled domain — it holds
   exactly when the renderer, installed as `cfg` and with the two switches set
   as given, RETURNS a label list for `ticks` — and every fact below is stated
   only there, because a fact stated about a call that has no value would be a
   claim about a different function. Measured on the real renderer: with both
   switches off, an installation whose interval spans more than the largest
   representable double yields nothing (interval `(-9e307, 9e307)`, ticks
   `[0.0]` → OverflowError, raised where the renderer takes the base-ten
   magnitude of that span; interval `(-8e307, 8e307)` returns `['0']`), and so
   does any tick list holding a non-finite position. The domain depends on the
   switches as well as on the installation, which is why it takes both: at that
   same wide installation the labels exist with the multiplicative switch ON and
   do not exist with it off. The domain is not a way to duck hard inputs: it
   holds for every installation and tick list the modeled sites actually produce
   (`renders_nonvacuous`; measured over the whole grid G-AX drives, mapping.md
   §3.4).

   Within that domain: with BOTH switches off, no renderer configuration hoists
   anything out (`sharedTerm_none`); and the abbreviation is real rather than
   hypothetical — some configuration and tick list do hoist a term out when the
   switches are on (`sharedTerm_hoists`), so the clause is not idle. The
   renderer emits exactly one label per tick (`renderTicks_length`). The ticks
   are the IEEE-754 double-precision positions the renderer receives. All of
   these facts are checked against the real renderer, over every configuration
   it can be installed with, in axiom_check.py (G-AX). Provenance: mapping.md
   §3. -/
axiom RendererConfig : Type
axiom renderTicks : RendererConfig → Bool → Bool → List Float → List String
axiom sharedTerm : RendererConfig → Bool → Bool → List Float → String
axiom renders : RendererConfig → Bool → Bool → List Float → Prop
axiom renderTicks_length : ∀ (cfg : RendererConfig) (offsetMode scaleMode : Bool)
    (ticks : List Float), renders cfg offsetMode scaleMode ticks →
    (renderTicks cfg offsetMode scaleMode ticks).length = ticks.length
axiom sharedTerm_none : ∀ (cfg : RendererConfig) (ticks : List Float),
    renders cfg false false ticks → sharedTerm cfg false false ticks = ""
axiom sharedTerm_hoists : ∃ (cfg : RendererConfig) (ticks : List Float),
    renders cfg true true ticks ∧ sharedTerm cfg true true ticks ≠ ""

/- An alternative renderer used for logarithmically-spaced ticks. It has no
   shared-term abbreviation modes of its own, so it takes NO switches and hoists
   nothing; on its own domain `rendersLog` — the installations and tick lists for
   which it RETURNS labels rather than failing outright, as above — it, too,
   emits one label per tick (`renderLog_length`). Its domain is genuinely its
   own and wider than the numeric renderer's: measured, it returns
   `['1', '100', '1e4']` at the widest interval a double can describe, where the
   numeric renderer with both switches off returns nothing; it likewise yields
   nothing for a non-finite tick position (mapping.md §3.4).

   It does, however, read the same installation handle as the numeric renderer
   above, and for the same reason: what it prints for a tick is not determined by
   that tick alone. It also consults the interval the renderer is attached to —
   which is the span of the DATA the legend describes, not the span of the ticks
   — and abbreviates a label to a power-of-ten form once that interval is wide
   enough. So one and the same tick list legitimately prints two different label
   lists on two different installations, and a model of this renderer that took
   only the ticks would describe neither: measured, the ticks `[1, 100, 10000]`
   print `['1', '100', '10000']` on an installation spanning `1 … 1e5` and
   `['1', '100', '1e4']` on one spanning `1 … 1.5e5`, and 6 of the 75 tick lists
   the site can produce print more than one label list this way (mapping.md
   §3.2). `renderLog` therefore takes `cfg`, and the legend on a logarithmic axis
   shows THIS renderer's labels for THIS installation, unchanged. Beyond the
   count, its label text is not constrained (a log-spaced label is not a plain
   decimal). Checked in axiom_check.py (G-AX). -/
axiom renderLog : RendererConfig → List Float → List String
axiom rendersLog : RendererConfig → List Float → Prop
axiom renderLog_length : ∀ (cfg : RendererConfig) (ticks : List Float),
    rendersLog cfg ticks → (renderLog cfg ticks).length = ticks.length

/- Both domains are inhabited, on a common installation and a non-empty tick
   list, so neither guard above can be idle by being empty. Measured: an
   installation spanning `1 … 1e5` with ticks `[1, 100, 10000]` returns labels
   from the numeric renderer with both switches off AND from the log renderer
   (mapping.md §3.4). -/
axiom renders_nonvacuous : ∃ (cfg : RendererConfig) (ticks : List Float),
    ticks ≠ [] ∧ renders cfg false false ticks ∧ rendersLog cfg ticks

/- Constructive existence witnesses so each `:|` callee choice elaborates. They
   do NOT weaken verification: under demonic choice the postconditions must still
   hold for EVERY value the choice predicate allows, not only for this witness. -/
noncomputable instance findableEqListStr (v : List String) (n : Lean.Name) :
    Findable (fun e : List String => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- axioms-end

-- pure-start
-- pure-end

noncomputable section

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the labels of a brief numeric legend for a continuous scale spanning a
   list of tick positions `ticks`.

   A continuous scale does not always print its ticks with the numeric renderer
   above. It may be configured to present them some entirely different way, and
   such a renderer has no shared-term abbreviation modes at all: there is
   nothing about it to switch off, and its labels need not be plain decimals.
   `modesAvailable` says which situation this is (read-only; not `mut`), `cfg` is
   the renderer as installed, and `ownLabels` is the labels that renderer
   produces for these ticks on its own — one per tick (`require`), as every such
   renderer emits.

   Desired behavior. When the shared-term modes ARE available, the labels are
   the numeric renderer's own output for EXACTLY these ticks under SOME setting
   of its two modes (`∃ offsetMode scaleMode, labels = renderTicks cfg ...`): the
   routine configures and calls that renderer on the tick list it was given, and
   does not render a different list, nor post-process, pad, truncate or
   substitute what comes back. On top of that, the setting used must hoist
   NOTHING out of the labels (`sharedTerm cfg offsetMode scaleMode ticks = ""`):
   a legend has nowhere to display a separately reported shared term, so a label
   that printed only a deviation from it, or only leading digits, would stand for
   a different (far smaller) quantity than its tick. When the modes are NOT
   available there is nothing to configure, so the legend shows the configured
   renderer's own labels UNCHANGED, and its observable output is pinned to be
   exactly those (`labels = ownLabels`). In both cases the result has one label
   per tick (`labels.length = ticks.length`). `cfg`, `ticks` and `ownLabels` are
   read-only (not `mut`): the routine produces fresh labels and never alters its
   inputs (directive 5).

   Modelled domain. On the arm where the switches exist, the routine is
   described only where the renderer it must call actually yields labels for
   these ticks with both switches off (`require modesAvailable = true → renders
   cfg false false ticks`). That is a restriction on the MODEL, not an
   assumption smuggled into the code: where it fails, the real site yields no
   legend at all — the renderer's failure escapes the modeled region, measured
   at the site itself (mapping.md §3.4) — so there is no label list there for
   any clause below to be about. The other arm calls nothing and is unrestricted.
   -/
method legendLabels (modesAvailable : Bool) (cfg : RendererConfig)
    (ownLabels : List String) (ticks : List Float) return (labels : List String)
  require ownLabels.length = ticks.length
  require modesAvailable = true → renders cfg false false ticks
  ensures labels.length = ticks.length
  ensures modesAvailable = false → labels = ownLabels
  ensures modesAvailable = true → ∃ (offsetMode scaleMode : Bool),
    labels = renderTicks cfg offsetMode scaleMode ticks ∧
    sharedTerm cfg offsetMode scaleMode ticks = ""
  do
    -- impl-start
    if modesAvailable then
      -- PRE-PATCH BUG: the renderer is used as-is, with its shared-term
      -- abbreviation modes left at their defaults (both on). It may then hoist a
      -- term shared by every tick out of the labels and report it separately,
      -- where a legend has nowhere to show it.
      let offsetMode : Bool := true
      let scaleMode : Bool := true
      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
      return labels
    else
      -- No shared-term modes exist on this renderer: nothing is configured and
      -- the legend shows exactly its own labels.
      return ownLabels
    -- impl-end

prove_correct legendLabels by
  loom_solve <;> subst_vars <;>
    first
      | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
      | simp_all [renderTicks_length]

/- Build the (levels, labels) of a brief numeric legend for the classic
   (function-level) plotting interface, where the tick spacing may be linear or
   logarithmic.

   `isLog` selects the renderer (read-only; not `mut`). On a logarithmic axis
   the legend shows the log renderer's labels for these ticks, UNCHANGED — that
   path is not touched, so its observable output is pinned to be exactly what
   that renderer prints for these ticks on THIS installation
   (`labels = renderLog cfg ticks`; the installation is part of what determines
   that text, so a pin that named only the ticks would be a claim about a
   different function). On a LINEAR axis the same two
   requirements as `legendLabels` apply: the labels are the numeric renderer's
   own output for EXACTLY these ticks under SOME setting of its two modes (so
   the renderer is configured and called on the given tick list, not on a padded
   or otherwise different one, and its result is passed through), and that
   setting must hoist nothing out of the labels, so no label stands for a
   different quantity than its tick. In both cases the result has one label per
   tick. `cfg` (the renderer as installed) and `ticks` are read-only.

   Modelled domain. Each arm is described only where the renderer it selects
   actually yields labels for these ticks (`require`s below, one per arm, each at
   the setting that arm uses). Where a renderer yields none the real site yields
   no legend either — its failure escapes the modeled region, measured at the
   site itself (mapping.md §3.4) — so there is nothing there for these clauses to
   be about. The two domains are separate facts because the two renderers'
   domains genuinely differ. -/
method legendEntries (isLog : Bool) (cfg : RendererConfig) (ticks : List Float)
    return (labels : List String)
  require isLog = true → rendersLog cfg ticks
  require isLog = false → renders cfg false false ticks
  ensures labels.length = ticks.length
  ensures isLog = true → labels = renderLog cfg ticks
  ensures isLog = false → ∃ (offsetMode scaleMode : Bool),
    labels = renderTicks cfg offsetMode scaleMode ticks ∧
    sharedTerm cfg offsetMode scaleMode ticks = ""
  do
    -- impl-start
    if isLog then
      let labels :| labels = renderLog cfg ticks
      return labels
    else
      -- PRE-PATCH BUG: shared-term abbreviation modes left at their defaults
      -- (both on) on the linear axis, so a term shared by every tick may be
      -- hoisted out of the labels and reported separately.
      let offsetMode : Bool := true
      let scaleMode : Bool := true
      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
      return labels
    -- impl-end
end

prove_correct legendEntries by
  loom_solve <;> subst_vars <;>
    first
      | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
      | simp_all [renderTicks_length, renderLog_length]
