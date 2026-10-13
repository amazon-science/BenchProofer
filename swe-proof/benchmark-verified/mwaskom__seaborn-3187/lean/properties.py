"""properties.py — G-PBT falsification battery for mwaskom__seaborn-3187 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a positive that legitimately re-proves, inside
the matching ``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with every obligation closed); ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

DEFENDED SURFACE (two structurally-identical total behaviors over one carrier):

  continuousLegendLabels (r : TickRenderer) (ticks : List Int)
      : TickRenderer × List String
  legendEntryLabels (r : TickRenderer) (ticks : List Int)
      : TickRenderer × List String

  A `TickRenderer` is the numeric tick renderer a legend builder MEETS: shared,
  mutable state that arrives already built and is what writes the label text. Its
  `compactionCapable` component says whether it offers a control for the
  COMPACTING mode at all; `compacting` is that mode; `numeralStyle` says whether it
  spells a label as a bare numeral, as against dressing it up for typesetting or
  punctuating it by a regional convention; `convention` carries the rest of what
  governs the text (which sort of renderer it is, and the range of the quantity
  being described). The label text itself is reachable only
  through the OPAQUE `render`, and a label is read back only through the OPAQUE
  `labelValue`. Both call sites are answerable for the same FIVE clauses:

    (W1) MODE OFF WHERE THE CONTROL EXISTS —
         `∀ r', uncompacted r = some r' → writtenFrom = r'`. Where the renderer
         offers the control, the renderer the labels are written from is that
         renderer with the compacting mode off — and with capability, numeral
         style and convention untouched, since `uncompacted` changes nothing else.

    (W2) OTHERWISE UNTOUCHED — `uncompacted r = none → writtenFrom = r`. A
         renderer offering no such control is used exactly as it stands. This is
         the PRESERVATION half, and it is what separates "turn the mode off where
         turning it off is a thing one can do" from "turn it off always". Without
         it the second clause is free and an impl may force a mode onto a renderer
         that has no control for it.

    (T) TEXT GROUNDED IN THAT RENDERER — `labels = render writtenFrom ticks`. The
        legend reports exactly the text the renderer it reports writes, for this
        tick set, in this order. `render` is opaque, so there is no answer key an
        implementation could compose privately instead: any text not obtained from
        that renderer state on that tick list is unequal to it. This clause is
        what makes (W1)/(W2) bite on the OUTPUT rather than only on a component
        nothing else reads.

    (L) LENGTH — `labels.length = ticks.length`: one label per tick.

    (R) READ-BACK — `r.compactionCapable = true → r.numeralStyle = true →
        (∀ t ∈ ticks, t.natAbs ≤ 2^53) → readsBackToTicks labels ticks`: where the
        control is offered, where the renderer spells its labels as bare numerals,
        and across the range a label carries back exactly, every label read back on
        its own recovers the full quantity of the tick it marks. This is the
        property the legend actually needs. It is claimed on a RESTRICTED domain
        because each restriction is a place the real renderer genuinely does not
        deliver the round trip (both measured in axiom_check.py): its numeric
        channel stops representing an integer distinctly past 2^53, and a renderer
        configured to typeset its labels or to punctuate them regionally writes text
        that denotes its quantity by that convention rather than by being read as a
        number — a configuration settled before the renderer is met, which no legend
        builder can undo. An unguarded claim would be false of it. And nothing at
        all is claimed while the compacting mode is still on, because losing exactly
        that is what the compacting mode does.

  The five clauses are not redundant. (R) alone is satisfied by a renderer left
  compacting whose text happens to read back (so (W1) is needed); (W1) alone is
  satisfied by an impl that reports a corrected renderer and writes its labels
  from somewhere else (so (T) is needed); (W1)+(T) alone are satisfied by an impl
  that forces the mode onto a renderer with no control for it (so (W2) is needed);
  and (W1)+(W2)+(T) alone say nothing about whether a label denotes its tick (so
  (R) is needed). Each reject case below is refuted by exactly one of them, which
  is what makes each rejection attributable.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete point, checked to hold of the rival and to FAIL on the frozen solution.

The carrier here is OPAQUE, which changes how a witness must be written and is
the single most important thing to understand about this battery. `render` and
`labelValue` are axioms: no literal input DECIDES a label, so a witness cannot
reduce the goal to arithmetic the way a transparent carrier permits. Two shapes
are used, and which one applies is a property of the clause being attacked:

  * UNCONDITIONED, at a literal renderer state and tick list. Available when the
    violated clause is about the renderer COMPONENT or the LENGTH — those are
    decidable from the record literals and `render_length` alone, with no fact
    about label text required. Used for the (W1), (W2) and (L) lane.

  * CONDITIONED ON THE CARRIER — a single weak hypothesis about one opaque term,
    e.g. `(hc : render r₁ ticks ≠ render r₂ ticks)`. Necessary when the violated
    clause is about the TEXT: two distinct opaque applications are not provably
    unequal, so the refutation is stated at a point where they differ. Each such
    hypothesis is additionally checked NON-VACUOUS — `example <binders> : False`
    must NOT close — because a witness resting on contradictory assumptions would
    prove its refutation from a contradiction and attribute nothing. The gate's
    `consistency_probe` enforces this; every conditioned witness here was also
    checked by hand against that probe.

Every witness was built twice: it ELABORATES against its rival and FAILS against
the frozen solution. No witness names a variant-only declaration, and none uses
`decide` (which cannot reduce an opaque application at all).

AXIOM lane: NOT here. `render`, `labelValue`, `render_length` and
`render_uncompacted_faithful` are consumed callee contracts, and validating them
against the real renderer is G-AX's job (axiom_check.py), which this gate ignores
so that one artifact is never judged twice by two gates with different oracles.
"""
from pathlib import Path

INSTANCE = "mwaskom__seaborn-3187"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Replace exactly one occurrence of a region-body substring. Asserts a
    UNIQUE match so silent drift (Solution.lean edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# FROZEN region bodies (each verified UNIQUE inside Solution.lean at load).
# Every impl reshape / positive reproof lands entirely inside one of these.
# ===========================================================================
_C_IMPL = (
    'noncomputable def implementation_continuousLegendLabels\n'
    '    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n'
    '  -- Where the renderer offers a control for the compacting mode, take it with\n'
    '  -- that mode off; otherwise take it as it stands. Then let that renderer write\n'
    '  -- the whole tick set\'s labels, and report both it and its text.\n'
    '  match uncompacted r with\n'
    '  | some r\' => (r\', render r\' ticks)\n'
    '  | none    => (r, render r ticks)'
)

_C_PROOF = (
    'theorem correct_continuousLegendLabels :\n'
    '    ∀ (r : TickRenderer) (ticks : List Int),\n'
    '      problem_spec_continuousLegendLabels r ticks\n'
    '        (implementation_continuousLegendLabels r ticks) := by\n'
    '  intro r ticks\n'
    '  obtain ⟨cap, comp, style, conv⟩ := r\n'
    '  unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels\n'
    '    uncompacted readsBackToTicks\n'
    '  cases cap with\n'
    '  | true =>\n'
    '    refine ⟨?_, ?_, ?_, ?_, ?_⟩\n'
    '    · intro r\' h; simp only [if_true, Option.some.injEq] at h; simp [← h]\n'
    '    · intro h; simp at h\n'
    '    · simp only [if_true]\n'
    '    · simp only [if_true]; exact render_length _ _\n'
    '    · intro _ hstyle hdom\n'
    '      simp only [if_true]\n'
    '      refine ⟨render_length _ _, ?_⟩\n'
    '      intro i hi\n'
    '      exact render_uncompacted_faithful\n'
    '        { compactionCapable := true, compacting := false, numeralStyle := style,\n'
    '          convention := conv }\n'
    '        ticks rfl rfl hstyle hdom i hi\n'
    '  | false =>\n'
    '    refine ⟨?_, ?_, ?_, ?_, ?_⟩\n'
    '    · intro r\' h; simp at h\n'
    '    · intro _; simp\n'
    '    · simp\n'
    '    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _\n'
    '    · intro h; simp at h\n'
    ''
)

_E_IMPL = (
    'noncomputable def implementation_legendEntryLabels\n'
    '    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n'
    '  -- As at the first site: where the renderer offers a control for the compacting\n'
    '  -- mode, take it with that mode off; otherwise take it as it stands. That\n'
    '  -- renderer writes the labels, and both it and its text are reported.\n'
    '  match uncompacted r with\n'
    '  | some r\' => (r\', render r\' ticks)\n'
    '  | none    => (r, render r ticks)'
)

_E_PROOF = (
    'theorem correct_legendEntryLabels :\n'
    '    ∀ (r : TickRenderer) (ticks : List Int),\n'
    '      problem_spec_legendEntryLabels r ticks\n'
    '        (implementation_legendEntryLabels r ticks) := by\n'
    '  intro r ticks\n'
    '  obtain ⟨cap, comp, style, conv⟩ := r\n'
    '  unfold problem_spec_legendEntryLabels implementation_legendEntryLabels\n'
    '    uncompacted readsBackToTicks\n'
    '  cases cap with\n'
    '  | true =>\n'
    '    refine ⟨?_, ?_, ?_, ?_, ?_⟩\n'
    '    · intro r\' h; simp only [if_true, Option.some.injEq] at h; simp [← h]\n'
    '    · intro h; simp at h\n'
    '    · simp only [if_true]\n'
    '    · simp only [if_true]; exact render_length _ _\n'
    '    · intro _ hstyle hdom\n'
    '      simp only [if_true]\n'
    '      refine ⟨render_length _ _, ?_⟩\n'
    '      intro i hi\n'
    '      exact render_uncompacted_faithful\n'
    '        { compactionCapable := true, compacting := false, numeralStyle := style,\n'
    '          convention := conv }\n'
    '        ticks rfl rfl hstyle hdom i hi\n'
    '  | false =>\n'
    '    refine ⟨?_, ?_, ?_, ?_, ?_⟩\n'
    '    · intro r\' h; simp at h\n'
    '    · intro _; simp\n'
    '    · simp\n'
    '    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _\n'
    '    · intro h; simp at h\n'
    ''
)

# Fail loudly at load if any frozen region drifted (each must appear exactly once).
for _region in (_C_IMPL, _C_PROOF, _E_IMPL, _E_PROOF):
    if _BASE.count(_region) != 1:
        raise AssertionError(f"frozen region not unique / not found:\n{_region[:80]!r}")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-different but CORRECT
# implementations that MUST verify. If a faithful correct impl cannot satisfy
# the frozen obligation, the spec is SPEC-TOO-STRONG. Each replaces BOTH the
# impl region and its matching proof region (the reshaped impl elaborates
# differently, so the obligation is RE-PROVED for the new shape; the
# `theorem correct_*` STATEMENT is kept byte-identical, no new declaration).
# ===========================================================================

# --- pos-continuous-ite: decide the renderer with an `if`, not an `Option`. ---
# The `uncompacted` helper returns an `Option`, and the frozen impl matches on
# it. This positive computes the same renderer with a plain `if` on the
# capability and never mentions `uncompacted` at all — so it cannot be passing by
# echoing the helper the spec is stated over. Same value on every input; the five
# clauses are grounded in the renderer INPUT and in `render`, so a faithful
# correct impl must satisfy them. Must verify (else SPEC-TOO-STRONG).
_C_ITE_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  let writtenFrom := if r.compactionCapable then { r with compacting := false } else r\n"
    "  (writtenFrom, render writtenFrom ticks)"
)
_C_ITE_PROOF = (
    "theorem correct_continuousLegendLabels :\n"
    "    ∀ (r : TickRenderer) (ticks : List Int),\n"
    "      problem_spec_continuousLegendLabels r ticks\n"
    "        (implementation_continuousLegendLabels r ticks) := by\n"
    "  intro r ticks\n"
    "  obtain ⟨cap, comp, style, conv⟩ := r\n"
    "  unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels\n"
    "    uncompacted readsBackToTicks\n"
    "  cases cap with\n"
    "  | true =>\n"
    "    refine ⟨?_, ?_, ?_, ?_, ?_⟩\n"
    "    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]\n"
    "    · intro h; simp at h\n"
    "    · simp only [if_true]\n"
    "    · simp only [if_true]; exact render_length _ _\n"
    "    · intro _ hstyle hdom\n"
    "      simp only [if_true]\n"
    "      refine ⟨render_length _ _, ?_⟩\n"
    "      intro i hi\n"
    "      exact render_uncompacted_faithful\n"
    "        { compactionCapable := true, compacting := false, numeralStyle := style,\n"
    "          convention := conv }\n"
    "        ticks rfl rfl hstyle hdom i hi\n"
    "  | false =>\n"
    "    refine ⟨?_, ?_, ?_, ?_, ?_⟩\n"
    "    · intro r' h; simp at h\n"
    "    · intro _; simp\n"
    "    · simp\n"
    "    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _\n"
    "    · intro h; simp at h\n"
)
POS_C_ITE = _swap(_swap(_BASE, _C_IMPL, _C_ITE_IMPL), _C_PROOF, _C_ITE_PROOF)

# --- pos-entry-getd: collapse the `Option` match into `Option.getD`. ---------
# The second site's counterpart, reshaped a different way again: one expression,
# no branch, the fallback supplied by `getD`. Correct on every input and
# re-proved for the new shape. Must verify (else SPEC-TOO-STRONG).
_E_GETD_IMPL = (
    "noncomputable def implementation_legendEntryLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  let writtenFrom := (uncompacted r).getD r\n"
    "  (writtenFrom, render writtenFrom ticks)"
)
_E_GETD_PROOF = (
    "theorem correct_legendEntryLabels :\n"
    "    ∀ (r : TickRenderer) (ticks : List Int),\n"
    "      problem_spec_legendEntryLabels r ticks\n"
    "        (implementation_legendEntryLabels r ticks) := by\n"
    "  intro r ticks\n"
    "  obtain ⟨cap, comp, style, conv⟩ := r\n"
    "  unfold problem_spec_legendEntryLabels implementation_legendEntryLabels\n"
    "    uncompacted readsBackToTicks\n"
    "  cases cap with\n"
    "  | true =>\n"
    "    refine ⟨?_, ?_, ?_, ?_, ?_⟩\n"
    "    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]\n"
    "    · intro h; simp at h\n"
    "    · simp only [if_true, Option.getD_some]\n"
    "    · simp only [if_true, Option.getD_some]; exact render_length _ _\n"
    "    · intro _ hstyle hdom\n"
    "      simp only [if_true, Option.getD_some]\n"
    "      refine ⟨render_length _ _, ?_⟩\n"
    "      intro i hi\n"
    "      exact render_uncompacted_faithful\n"
    "        { compactionCapable := true, compacting := false, numeralStyle := style,\n"
    "          convention := conv }\n"
    "        ticks rfl rfl hstyle hdom i hi\n"
    "  | false =>\n"
    "    refine ⟨?_, ?_, ?_, ?_, ?_⟩\n"
    "    · intro r' h; simp at h\n"
    "    · intro _; simp\n"
    "    · simp\n"
    "    · simp only [Bool.false_eq_true, if_false, Option.getD_none]\n"
    "      exact render_length _ _\n"
    "    · intro h; simp at h\n"
)
POS_E_GETD = _swap(_swap(_BASE, _E_IMPL, _E_GETD_IMPL), _E_PROOF, _E_GETD_PROOF)

# --- adm-nonvacuous: the guarded read-back clause is REACHABLE ---------------
# Clause (R) fires only under two antecedents: the renderer offers the compaction
# control, and every tick lies inside the exactly-representable range. Both are
# restrictions, and if they were jointly unsatisfiable the clause would be
# vacuously true everywhere and pin nothing at all — the PRECOND-TOO-STRONG
# failure. Every clause-(W) and clause-(L) reject case below is refuted without
# clause (R) firing, so nothing else in this battery demonstrates it is live.
#
# So: at a capable renderer over the large-magnitude reporting-shaped tick range
# that motivates the whole behavior, both antecedents HOLD, and the clause
# delivers a real conclusion — every label reads back to its tick. Stated as an
# anonymous `example` inside the impl region: it declares no name, so
# `variant_scope` stays clean and the frozen proof region is untouched.
_C_ADMISS_IMPL = _C_IMPL + (
    "\n\n"
    "-- The read-back clause's three antecedents ADMIT a normal reporting-shaped\n"
    "-- point: a renderer that offers the compaction control and spells its labels\n"
    "-- as bare numerals, over a large-magnitude tick range well inside the\n"
    "-- exactly-representable domain. All three hold there, so the clause is live\n"
    "-- rather than vacuous, and what it yields is the full quantity of every tick.\n"
    "example :\n"
    "    ({ compactionCapable := true, compacting := true,\n"
    "        numeralStyle := true, convention := 3 } : TickRenderer).compactionCapable = true\n"
    "    ∧ ({ compactionCapable := true, compacting := true,\n"
    "         numeralStyle := true, convention := 3 } : TickRenderer).numeralStyle = true\n"
    "    ∧ (∀ t ∈ [(100000000 : Int), 100000001, 100000002],\n"
    "        t.natAbs ≤ 9007199254740992)\n"
    "    ∧ problem_spec_continuousLegendLabels\n"
    "        { compactionCapable := true, compacting := true, numeralStyle := true,\n"
    "          convention := 3 }\n"
    "        [100000000, 100000001, 100000002]\n"
    "        (implementation_continuousLegendLabels\n"
    "          { compactionCapable := true, compacting := true, numeralStyle := true,\n"
    "            convention := 3 }\n"
    "          [100000000, 100000001, 100000002]) := by\n"
    "  refine ⟨rfl, rfl, by decide, ?_⟩\n"
    "  unfold problem_spec_continuousLegendLabels\n"
    "    implementation_continuousLegendLabels uncompacted readsBackToTicks\n"
    "  refine ⟨?_, ?_, ?_, ?_, ?_⟩\n"
    "  · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]\n"
    "  · intro h; simp at h\n"
    "  · simp only [if_true]\n"
    "  · simp only [if_true]; exact render_length _ _\n"
    "  · intro _ hstyle hdom\n"
    "    simp only [if_true]\n"
    "    refine ⟨render_length _ _, ?_⟩\n"
    "    intro i hi\n"
    "    exact render_uncompacted_faithful\n"
    "      { compactionCapable := true, compacting := false, numeralStyle := true,\n"
    "        convention := 3 }\n"
    "      [100000000, 100000001, 100000002] rfl rfl rfl hdom i hi\n"
)
POS_C_ADMISS = _swap(_BASE, _C_IMPL, _C_ADMISS_IMPL)


# ===========================================================================
# UNIQUENESS / REJECT rivals — wrong implementations sharing the frozen spec
# that MUST be rejected. Each edits ONLY the impl region (the frozen proof is
# left in place; against the reshaped impl it no longer closes, so the file does
# not verify). Each carries a refutation witness pinning the violation at one
# concrete point, checked to hold of the rival and to FAIL on the frozen impl.
#
# Organised by WHICH clause refutes them. Every clause carries at least one
# rival of its own, so no clause is only along for the ride.
# ===========================================================================

# ---- clause (W1): use the renderer exactly as it was met ---------------------
# The renderer arrives already built and standing in whatever mode it stands in,
# and this rival writes the labels straight from it, never reaching for the
# compaction control even where one is offered. It is the behavior the whole
# specification exists to rule out: on a renderer that offers the control and
# stands in the compacting mode, the labels the legend keeps are residuals and
# the hoisted magnitude — which on an axis would be drawn beside the ticks — is
# dropped on the floor, so nothing in the legend records it.
#
# A faithful real counterpart takes the tick set through the renderer it was
# handed without asking that renderer to stop hoisting, so a legend describing a
# large-magnitude continuous range shows small residual labels instead of the
# quantities: the assertion that a legend's labels read back to values of the same
# magnitude as the range they describe FAILS, and it would NOT resolve.
_C_ASISFOUND_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  (r, render r ticks)"
)
RIVAL_C_ASISFOUND = _swap(_BASE, _C_IMPL, _C_ASISFOUND_IMPL)

_E_ASISFOUND_IMPL = (
    "noncomputable def implementation_legendEntryLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  (r, render r ticks)"
)
RIVAL_E_ASISFOUND = _swap(_BASE, _E_IMPL, _E_ASISFOUND_IMPL)

# ---- clause (W2): forcing a mode onto a renderer with no control for it -----
# The rival turns the compacting mode off UNCONDITIONALLY, ignoring whether the
# renderer offers a control for it. On a capable renderer it agrees with gold
# exactly; it diverges only on a renderer that offers no such control, where it
# reports a renderer whose mode it had no business setting. This is why (W2) is
# stated as a preservation claim rather than left free: a spec carrying only (W1)
# is satisfied by this rival at every input, since (W1) says nothing at all when
# `uncompacted r = none`.
#
# A faithful real counterpart reaches for a mode control on a renderer of the sort
# that does not carry one, so building a legend for a logarithmically-scaled
# quantity raises instead of producing labels; every existing assertion that
# touches such a legend then errors out rather than comparing labels, so it would
# NOT resolve.
_C_UNCOND_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  let r' := { r with compacting := false }\n"
    "  (r', render r' ticks)"
)
RIVAL_C_UNCOND = _swap(_BASE, _C_IMPL, _C_UNCOND_IMPL)

_E_UNCOND_IMPL = (
    "noncomputable def implementation_legendEntryLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  let r' := { r with compacting := false }\n"
    "  (r', render r' ticks)"
)
RIVAL_E_UNCOND = _swap(_BASE, _E_IMPL, _E_UNCOND_IMPL)

# ---- clause (W2), harder: also overwrite the CAPABILITY -----------------------
# `compactionCapable` is an intrinsic property of the renderer, not a setting.
# This rival reports a renderer with the capability itself flipped on, which makes
# `uncompacted` of the REPORTED renderer look well-behaved while the renderer that
# actually arrived offered no control at all. A distinct shape from the rival
# above: it would survive a spec that pinned only the MODE component and left the
# capability free, and such a spec would admit an implementation that misreports
# what sort of renderer it was handed.
_C_FLIPCAP_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  let r' := { r with compactionCapable := true, compacting := false }\n"
    "  (r', render r' ticks)"
)
RIVAL_C_FLIPCAP = _swap(_BASE, _C_IMPL, _C_FLIPCAP_IMPL)

# ---- clause (W1): report the renderer as it ARRIVED --------------------------
# The pair's two halves are pulled apart the other way: the labels are written
# from the corrected renderer (so they read back correctly, and (L) and (R) both
# hold) but the renderer REPORTED is the one as it arrived, still compacting.
# Since the renderer outlives the call and goes on rendering the same axis,
# reporting the uncorrected one is a real divergence, and it is what (W1) pins.
# (T) also refutes it — the reported renderer's text is not the text emitted —
# which is the intended overlap: the two clauses jointly pin the PAIR, so neither
# can be satisfied by relabelling which half is which.
_C_PRESTATE_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  match uncompacted r with\n"
    "  | some r' => (r, render r' ticks)\n"
    "  | none    => (r, render r ticks)"
)
RIVAL_C_PRESTATE = _swap(_BASE, _C_IMPL, _C_PRESTATE_IMPL)

# ---- clause (T): compose the label text privately ---------------------------
# The rival reports the correctly-corrected renderer and produces label text of
# its own instead of the text that renderer writes. Every OTHER clause is
# satisfiable by it: the renderer component is right, the length is right, and on
# a transparent numeric carrier its labels would even read back to the right
# quantities. Closed here by grounding the text in `render`, which is opaque, so
# there is no answer key to reproduce.
#
# A faithful real counterpart stringifies each tick on its own instead of driving
# the whole tick set through the renderer it was handed, so the legend's label text
# stops matching that renderer's rendering of that tick set: the existing
# assertions pinning exact legend label text for a known tick set FAIL, and it
# would NOT resolve — even though every label parses back to the right number.
_C_BYPASS_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  match uncompacted r with\n"
    "  | some r' => (r', ticks.map toString)\n"
    "  | none    => (r, render r ticks)"
)
RIVAL_C_BYPASS = _swap(_BASE, _C_IMPL, _C_BYPASS_IMPL)

_E_BYPASS_IMPL = (
    "noncomputable def implementation_legendEntryLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  match uncompacted r with\n"
    "  | some r' => (r', ticks.map toString)\n"
    "  | none    => (r, render r ticks)"
)
RIVAL_E_BYPASS = _swap(_BASE, _E_IMPL, _E_BYPASS_IMPL)

# ---- clause (T), by a different route: write from a renderer NOT reported -----
# The reported renderer is right and the text does come from a renderer — just not
# from that one. `convention` carries the rest of the renderer's configuration and
# the measured real renderer's text genuinely varies with it, so writing labels
# from a differently-configured renderer than the one reported is a real
# divergence and not a modelling artifact. Distinct from the bypass rival: this one
# DOES route through `render`, so a spec requiring only that the text be SOME
# rendering — rather than that renderer's rendering of that tick set — admits it.
_C_OTHERCONV_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  match uncompacted r with\n"
    "  | some r' => (r', render { r' with convention := r'.convention + 1 } ticks)\n"
    "  | none    => (r, render r ticks)"
)
RIVAL_C_OTHERCONV = _swap(_BASE, _C_IMPL, _C_OTHERCONV_IMPL)

# ---- clause (T): the RIGHT renderer on the WRONG tick set -------------------
# Routed through the reported renderer, right length, but rendering a shifted tick
# set. (T) names the tick list too: the labels must be that renderer's rendering
# OF THESE TICKS. A spec pinning only "the labels are some rendering by the
# reported renderer" admits it, and the legend it produces labels every entry with
# a neighbouring quantity.
_C_SHIFTTICKS_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  match uncompacted r with\n"
    "  | some r' => (r', render r' (ticks.map (fun t => t + 1)))\n"
    "  | none    => (r, render r ticks)"
)
RIVAL_C_SHIFTTICKS = _swap(_BASE, _C_IMPL, _C_SHIFTTICKS_IMPL)

# ---- clause (T): right renderer, right tick set, wrong ORDER ----------------
# The label sequence is reversed. The length is right, every label is genuinely
# that renderer's text for one of these ticks, and on a symmetric tick set it even
# agrees with gold — so this attacks the order-sensitivity of (T). A legend built
# this way pairs each tick position with another tick's label.
_C_REVERSE_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  match uncompacted r with\n"
    "  | some r' => (r', (render r' ticks).reverse)\n"
    "  | none    => (r, render r ticks)"
)
RIVAL_C_REVERSE = _swap(_BASE, _C_IMPL, _C_REVERSE_IMPL)

# ---- clause (L): the empty-tick-list boundary --------------------------------
# Correct on every nonempty tick list; on the empty one it emits a label for a
# tick that is not there. The empty carrier is the one domain point at which the
# label half of every clause-(W) rival above holds vacuously, so without this case
# a battery effectively quantified over nonempty tick lists would pass. Rejected
# by (L) via `render_length`: gold's label list is empty there.
_E_EMPTY_IMPL = (
    "noncomputable def implementation_legendEntryLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  match uncompacted r with\n"
    "  | some r' => (r', if ticks.isEmpty then [\"-\"] else render r' ticks)\n"
    "  | none    => (r, render r ticks)"
)
RIVAL_E_EMPTY = _swap(_BASE, _E_IMPL, _E_EMPTY_IMPL)

# ---- clause (W1): honor the guarantee only inside part of its domain ---------
# The rival corrects the renderer only when every tick is small, and hands the
# renderer on untouched once any tick is large. Clause (R) is claimed exactly on
# the exactly-representable range and this rival satisfies it THERE — so what
# refutes it is (W1), which carries no magnitude restriction at all. That is the
# point of the case: it demonstrates the domain restriction on (R) did not
# silently narrow the rest of the specification, which is the failure mode a
# guarded clause invites. Large ticks are precisely where a legend needs the
# correction most, so a faithful counterpart would leave exactly the
# large-magnitude legends it is supposed to serve reading back as residuals.
_C_ONLYSMALL_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  if ticks.all (fun t => t.natAbs <= 9007199254740992) then\n"
    "    match uncompacted r with\n"
    "    | some r' => (r', render r' ticks)\n"
    "    | none    => (r, render r ticks)\n"
    "  else\n"
    "    (r, render r ticks)"
)
RIVAL_C_ONLYSMALL = _swap(_BASE, _C_IMPL, _C_ONLYSMALL_IMPL)

# ---- clause (W1): mutate a component that is not the builder's to set --------
# The renderer is correctly uncompacted AND its convention is overwritten, and the
# labels are written from that same overwritten renderer — so (T) is satisfied in
# full and the text really is the reported renderer's own output. Only (W1) rejects
# it, because `uncompacted` leaves the convention alone and (W1) pins the reported
# renderer to `uncompacted`'s result exactly. Without this case a spec could pin
# the mode and the text while leaving an implementation free to reconfigure the
# shared renderer in any other way it liked — and for state that outlives the call
# and keeps rendering the same axis, that is a real divergence.
_E_MUTCONV_IMPL = (
    "noncomputable def implementation_legendEntryLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  match uncompacted r with\n"
    "  | some r' =>\n"
    "    let r'' := { r' with convention := 0 }\n"
    "    (r'', render r'' ticks)\n"
    "  | none    => (r, render r ticks)"
)
RIVAL_E_MUTCONV = _swap(_BASE, _E_IMPL, _E_MUTCONV_IMPL)

# ---- clause (W1): decide whether to act by CONSULTING THE READING ORACLE -----
# The rival renders once with the renderer exactly as met, reads every resulting
# label back, and if they all happen to recover their ticks it keeps that pair and
# leaves the renderer alone; only otherwise does it reach for the control. This is
# the ungrounded-oracle shape, and it is worth a case of its own because it is what
# a specification stated ONLY as a read-back guarantee cannot reject: it satisfies
# (R) at every input by construction, since it checks (R) itself before committing.
# What refutes it is (W1) — a renderer that reads back acceptably while still
# standing in the compacting mode is still reported in that mode, and it goes on
# rendering the same axis afterwards. No real implementation can read its own
# labels back to decide this, so it also shows why (R) alone is not the contract.
_C_ORACLE_IMPL = (
    "noncomputable def implementation_continuousLegendLabels\n"
    "    (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=\n"
    "  let probe := render r ticks\n"
    "  if (List.range ticks.length).all (fun i => labelValue (probe[i]!) == ticks[i]!) then\n"
    "    (r, probe)\n"
    "  else\n"
    "    match uncompacted r with\n"
    "    | some r' => (r', render r' ticks)\n"
    "    | none    => (r, render r ticks)"
)
RIVAL_C_ORACLE = _swap(_BASE, _C_IMPL, _C_ORACLE_IMPL)


# ===========================================================================
# WITNESSES — one per reject case. Each was built TWICE: it elaborates against
# its rival and FAILS against the frozen solution.
#
# The carrier is opaque, so the shape of a witness is dictated by the clause it
# attacks (see the module docstring):
#
#   * UNCONDITIONED, at a literal renderer record and tick list. Available when
#     the violated clause is about the renderer COMPONENT (W1/W2) or the LENGTH
#     (L): those follow from the record literals plus `render_length`, with no
#     fact about label TEXT needed. `simp_all` closes them.
#   * CONDITIONED ON THE CARRIER, under one weak hypothesis about opaque terms,
#     when the violated clause is about the TEXT (T): two distinct opaque
#     applications are not provably unequal, so the refutation is stated at a
#     point where they differ. Each such hypothesis is a single dis-equality
#     between two `render` applications (or between a private composition and a
#     `render` application), which `consistency_probe` cannot derive `False` from
#     — checked by hand against that probe as well.
#
# No witness uses `decide` on a spec clause: `decide` cannot reduce an opaque
# application at all. None names a declaration only a variant has: every witness
# is stated over `problem_spec_*` and `implementation_*`, which the frozen
# solution and every rival both declare.
# ===========================================================================
_CP = "problem_spec_continuousLegendLabels"
_CI = "implementation_continuousLegendLabels"
_EP = "problem_spec_legendEntryLabels"
_EI = "implementation_legendEntryLabels"


def _R(cap, comp, conv, style="true"):
    return ("{ compactionCapable := " + cap + ", compacting := " + comp
            + ", numeralStyle := " + style + ", convention := " + conv + " }")


def _wit(spec, impl, r, ticks, hyp="", tac="  simp_all\n"):
    """`¬ spec r ticks (impl r ticks)`, optionally under one hypothesis."""
    head = f"example {hyp}: ¬ {spec}\n" if hyp else f"example : ¬ {spec}\n"
    return (
        head
        + f"    ({r}) ({ticks})\n"
        + f"    ({impl} ({r}) ({ticks})) := by\n"
        + f"  unfold {spec} {impl} uncompacted readsBackToTicks\n"
        + "  intro h\n"
        + "  obtain ⟨h1, h2, h3, h4, h5⟩ := h\n"
        + tac
    )


# (W1) — a renderer that offers the control and stands in the compacting mode:
# gold reports it with that mode OFF, the rival reports it as met.
_WIT_C_ASISFOUND = _wit(_CP, _CI, _R("true", "true", "7"), "[1, 2]")
_WIT_E_ASISFOUND = _wit(_EP, _EI, _R("true", "true", "7"), "[1, 2]")

# (W2) — a renderer offering NO control: gold uses it exactly as it stands, the
# rival reports it with a mode it had no business setting.
_WIT_C_UNCOND = _wit(_CP, _CI, _R("false", "true", "7"), "[1, 2]")
_WIT_E_UNCOND = _wit(_EP, _EI, _R("false", "true", "7"), "[1, 2]")

# (W2) — same point; here the reported CAPABILITY is wrong as well.
_WIT_C_FLIPCAP = _wit(_CP, _CI, _R("false", "true", "7"), "[1, 2]")

# (W1) — the corrected renderer writes the labels but the one reported is the one
# as it arrived.
_WIT_C_PRESTATE = _wit(_CP, _CI, _R("true", "true", "7"), "[1, 2]")

# (W1) — the convention is overwritten, which `uncompacted` never does.
_WIT_E_MUTCONV = _wit(_EP, _EI, _R("true", "true", "7"), "[1, 2]")

# (W1) — outside the read-back clause's magnitude domain (2^53 + 1), where this
# rival stops correcting the renderer but (W1) still binds.
_WIT_C_ONLYSMALL = _wit(_CP, _CI, _R("true", "true", "7"), "[9007199254740993]")

# (L) — the empty tick list: gold keeps no label, the rival keeps one.
_WIT_E_EMPTY = _wit(_EP, _EI, _R("true", "true", "7"), "[]")

# (W1), conditioned — the oracle-consulting rival's branch is chosen by an opaque
# read-back, so the refutation is stated on the branch where that check PASSES.
# The hypothesis says only "the labels this renderer writes as met do read back to
# their ticks", which is satisfiable (it is what an already-quiescent renderer
# does) and is exactly the case in which the rival leaves the mode alone.
_WIT_C_ORACLE = _wit(
    _CP, _CI, _R("true", "true", "7"), "[1, 2]",
    hyp=("(hp : (List.range 2).all (fun i =>\n"
         "    labelValue ((render " + _R("true", "true", "7") + " [1, 2])[i]!)\n"
         "      == [1, 2][i]!) = true) "),
)

# (T), conditioned — a privately composed label list differs from the text the
# reported renderer writes.
_WIT_C_BYPASS = _wit(
    _CP, _CI, _R("true", "true", "7"), "[1, 2]",
    hyp=("(hc : [1, 2].map toString\n"
         "    ≠ render " + _R("true", "false", "7") + " [1, 2]) "),
    tac="  simp only [if_true] at h3\n  exact hc h3\n",
)
_WIT_E_BYPASS = _wit(
    _EP, _EI, _R("true", "true", "7"), "[1, 2]",
    hyp=("(hc : [1, 2].map toString\n"
         "    ≠ render " + _R("true", "false", "7") + " [1, 2]) "),
    tac="  simp only [if_true] at h3\n  exact hc h3\n",
)

# (T), conditioned — the text comes from a renderer configured differently from
# the one reported, at a point where those two renderers disagree.
_WIT_C_OTHERCONV = _wit(
    _CP, _CI, _R("true", "true", "7"), "[1, 2]",
    hyp=("(hc : render " + _R("true", "false", "8") + " [1, 2]\n"
         "    ≠ render " + _R("true", "false", "7") + " [1, 2]) "),
)

# (T), conditioned — the right renderer on a shifted tick set, at a point where
# the two tick sets render differently.
_WIT_C_SHIFTTICKS = _wit(
    _CP, _CI, _R("true", "true", "7"), "[1, 2]",
    hyp=("(hc : render " + _R("true", "false", "7") + " [2, 3]\n"
         "    ≠ render " + _R("true", "false", "7") + " [1, 2]) "),
)

# (T), conditioned — the right text in the wrong order, at a point where the
# reversal is observable.
_WIT_C_REVERSE = _wit(
    _CP, _CI, _R("true", "true", "7"), "[1, 2]",
    hyp=("(hc : (render " + _R("true", "false", "7") + " [1, 2]).reverse\n"
         "    ≠ render " + _R("true", "false", "7") + " [1, 2]) "),
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — correct impls that MUST verify
    # =====================================================================
    {
        "id": "pos-continuous-ite",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_C_ITE,
        "rationale": "structurally-different but CORRECT first obligation: decide "
        "the renderer to write from with a plain `if` on the capability instead of "
        "matching the `Option` the spec is stated over — this impl never mentions "
        "`uncompacted` at all, so it cannot be passing by echoing the helper. Same "
        "value on every input. The five clauses are grounded in the renderer INPUT "
        "and in the opaque `render`, so any faithful correct impl satisfies them. "
        "Re-proved for the reshaped form with the `correct_` statement kept "
        "byte-identical and no new declaration. Must verify; if not, the "
        "postcondition is SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-entry-getd",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_E_GETD,
        "rationale": "the second obligation's counterpart, reshaped a third way: "
        "the branch collapsed into a single `Option.getD` expression, no `match` "
        "and no `if`. Correct on every input and re-proved for the new shape; "
        "`correct_` statement byte-identical, no new declaration. Must verify "
        "(else SPEC-TOO-STRONG). Defends the second obligation, which the first "
        "positive cannot speak for since each site carries its own postcondition.",
    },
    {
        "id": "adm-continuous-readback-nonvacuous",
        "kind": "admissibility",
        "expect": "verify",
        "module": POS_C_ADMISS,
        "rationale": "ADMISSIBILITY. Clause (R) fires only under two antecedents — "
        "the renderer offers the compaction control, and every tick lies inside the "
        "exactly-representable range — and both are restrictions. Every clause-(W) "
        "and clause-(L) reject case below is refuted WITHOUT (R) firing (several sit "
        "at a non-capable renderer, one sits above the magnitude guard, one at the "
        "empty tick list), so nothing else in this battery demonstrates that (R) is "
        "reachable at all. Were the two antecedents jointly unsatisfiable, (R) would "
        "be vacuously true everywhere and pin nothing: PRECOND-TOO-STRONG. This case "
        "pins a concrete large-magnitude reporting-shaped point — a capable renderer "
        "over three consecutive hundred-million ticks, the very shape that motivates "
        "the behavior — at which BOTH antecedents hold and the clause yields a real "
        "conclusion: every label read back recovers the full quantity of its tick. "
        "Stated as an anonymous `example` inside the impl region, so it declares no "
        "name (variant_scope stays clean) and the frozen proof region is untouched. "
        "Must verify.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "rej-continuous-renderer-as-met",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_ASISFOUND,
        "refinement": "writes the first site's labels straight from the renderer as "
        "it was met, never reaching for the compaction control even where one is "
        "offered. A faithful real counterpart takes the tick set through the "
        "renderer it was handed without asking it to stop hoisting a shared "
        "magnitude out of the labels, so a legend describing a large-magnitude "
        "continuous range shows small residual labels while the hoisted magnitude — "
        "which on an axis is drawn beside the ticks — is kept nowhere. The F2P "
        "assertion that such a legend's labels read back to quantities of the "
        "range's own magnitude FAILS: it would NOT resolve.",
        "rationale": "REJECT from (W1): where the renderer offers the control, the "
        "renderer the labels are written from must be that renderer with the "
        "compacting mode off, and this one is reported in whatever mode it arrived "
        "in. Unconditioned witness at a capable renderer standing in the compacting "
        "mode over `[1, 2]`: the reported renderer's `compacting` component is "
        "`true` where (W1) forces `false`, which the record literals decide with no "
        "fact about label text needed. Gold reports the corrected renderer at that "
        "same point, so the statement fails there.",
        "witness": _WIT_C_ASISFOUND,
    },
    {
        "id": "rej-entry-renderer-as-met",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_E_ASISFOUND,
        "refinement": "the same at the second site: the tick set goes through the "
        "renderer exactly as met. A faithful real counterpart leaves the other place "
        "a legend of this kind is built showing residual labels for a "
        "large-magnitude range, so the assertion covering that site's legend FAILS "
        "and it would NOT resolve. Kept as its own case because each site carries "
        "its own postcondition and a rival correcting only one site must still be "
        "rejected by the other's.",
        "rationale": "REJECT from (W1) at the second obligation. Same unconditioned "
        "witness shape at a capable renderer in the compacting mode.",
        "witness": _WIT_E_ASISFOUND,
    },
    {
        "id": "rej-continuous-mode-forced-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_UNCOND,
        "refinement": "turns the compacting mode off UNCONDITIONALLY, without asking "
        "whether the renderer offers a control for that mode. Agrees with gold at "
        "every capable renderer and diverges only where no such control exists. A "
        "faithful real counterpart reaches for a mode control on a renderer of the "
        "sort that does not carry one, so building a legend for a "
        "logarithmically-scaled quantity raises instead of producing labels; every "
        "existing assertion touching such a legend errors out rather than comparing "
        "labels, so it would NOT resolve.",
        "rationale": "REJECT from (W2): a renderer offering no such control must be "
        "used exactly as it stands. This is the case that shows (W2) is load-bearing "
        "rather than decorative — a spec carrying only (W1) admits this rival at "
        "EVERY input, because (W1) says nothing when `uncompacted r = none`. "
        "Unconditioned witness at a non-capable renderer standing in the compacting "
        "mode: (W2) forces the reported renderer to be that record, and the rival "
        "reports one with `compacting := false`.",
        "witness": _WIT_C_UNCOND,
    },
    {
        "id": "rej-entry-mode-forced-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_E_UNCOND,
        "refinement": "the same at the second site. A faithful real counterpart makes "
        "the other legend-building site raise on a logarithmically-scaled quantity, "
        "so it would NOT resolve.",
        "rationale": "REJECT from (W2) at the second obligation, same unconditioned "
        "witness point.",
        "witness": _WIT_E_UNCOND,
    },
    {
        "id": "rej-continuous-capability-overwritten",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_FLIPCAP,
        "refinement": "reports a renderer with the CAPABILITY itself flipped on as "
        "well as the mode off, so `uncompacted` of the reported renderer looks "
        "well-behaved while the renderer that actually arrived offered no control at "
        "all. A faithful real counterpart both reaches for a control the renderer "
        "does not carry and misreports what sort of renderer it was handed, so the "
        "legend for a logarithmically-scaled quantity is built from a renderer it "
        "was never given: the assertions over that legend FAIL and it would NOT "
        "resolve.",
        "rationale": "REJECT from (W2), and a DISTINCT shape from "
        "`rej-continuous-mode-forced-always`: this rival would survive a spec that "
        "pinned only the mode component and left the capability free, and such a "
        "spec would admit an impl that misreports the kind of renderer it met. "
        "`compactionCapable` is an intrinsic property of the renderer, not a "
        "setting, so (W2) pins the WHOLE record. Unconditioned witness at a "
        "non-capable renderer.",
        "witness": _WIT_C_FLIPCAP,
    },
    {
        "id": "rej-continuous-reports-renderer-as-arrived",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_PRESTATE,
        "refinement": "writes the labels from the corrected renderer but reports the "
        "renderer as it ARRIVED — the pair's two halves pulled apart. Its labels "
        "read back correctly, so a legend built once looks right. A faithful real "
        "counterpart produces the label text from a corrected renderer while leaving "
        "the shared renderer it was handed standing in the compacting mode, and that "
        "renderer outlives the call and goes on rendering the same axis: the "
        "subsequent axis labels, and any second legend drawn from it, come out as "
        "residuals. The assertions that observe the renderer after a legend is built "
        "FAIL, so it would NOT resolve.",
        "rationale": "REJECT from (W1): the reported renderer must be the corrected "
        "one. (T) also refutes it — the reported renderer's own text is not the text "
        "emitted — which is the intended overlap rather than redundancy: (W1) and (T) "
        "jointly pin the PAIR, so neither can be satisfied by relabelling which half "
        "is which. This case is what makes the renderer's post-state an OBSERVABLE "
        "rather than a private detail. Unconditioned witness at a capable renderer in "
        "the compacting mode.",
        "witness": _WIT_C_PRESTATE,
    },
    {
        "id": "rej-continuous-label-text-composed-privately",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_BYPASS,
        "refinement": "reports the correctly-corrected renderer but composes the "
        "label text itself instead of keeping the text that renderer writes. A "
        "faithful real counterpart stringifies each tick on its own rather than "
        "driving the whole tick set through the renderer it was handed; the legend's "
        "labels then no longer match that renderer's rendering of that tick set — "
        "inconsistent decimal widths, no thousands convention, a different notation "
        "at magnitude — so the P2P assertions pinning the exact label text of a "
        "known legend FAIL and it would NOT resolve, even though every label parses "
        "back to the right number.",
        "rationale": "REJECT from (T): the labels must be `render writtenFrom "
        "ticks`. This is the family a spec observing only the DENOTED value cannot "
        "reject — the rival's labels read back exactly right, so (W1), (W2), (L) and "
        "(R) are all satisfied by it. `render` is opaque, so there is no answer key "
        "an impl could reproduce; any text not obtained from that renderer state on "
        "that tick list is simply unequal to it. Witness CONDITIONED on the carrier "
        "— two distinct opaque applications are not provably unequal, so it is "
        "stated under the single weak hypothesis that this private composition "
        "differs from the corrected renderer's text on `[1, 2]`. That hypothesis is "
        "satisfiable (a renderer that writes anything but bare decimal digits "
        "satisfies it, which the real renderer does at scale, with a thousands "
        "separator, or in scientific notation), so `consistency_probe` cannot derive "
        "`False` from it.",
        "witness": _WIT_C_BYPASS,
    },
    {
        "id": "rej-entry-label-text-composed-privately",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_E_BYPASS,
        "refinement": "the same at the second site. A faithful real counterpart makes "
        "the other legend-building site's label text stop matching its renderer's, "
        "so the P2P assertion pinning that legend's exact labels FAILS and it would "
        "NOT resolve.",
        "rationale": "REJECT from (T) at the second obligation, same conditioned "
        "witness shape.",
        "witness": _WIT_E_BYPASS,
    },
    {
        "id": "rej-continuous-text-from-a-renderer-not-reported",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_OTHERCONV,
        "refinement": "reports the right renderer, and the text does come from a "
        "renderer — just not from that one: it is written by one whose remaining "
        "configuration differs. A faithful real counterpart formats the tick set "
        "through a renderer it configured itself rather than the one the axis "
        "carries, so the legend's labels follow a different convention from the axis "
        "they describe (a different notation, or a different range assumption), and "
        "the assertions pinning the legend's exact labels FAIL: it would NOT resolve.",
        "rationale": "REJECT from (T), by a different route than the private-"
        "composition rival: this one DOES route through `render`, so a spec "
        "requiring only that the labels be SOME rendering — rather than the reported "
        "renderer's rendering of this tick set — admits it. The `convention` "
        "component is not a modelling flourish: axiom_check.py obligation 6 measured "
        "the real renderer writing genuinely different text for the same tick set "
        "purely from that part of its configuration (8 of 20 probes), so this is a "
        "real divergence. Witness CONDITIONED on the carrier at a point where the "
        "two renderer states disagree; the hypothesis is one dis-equality between "
        "two `render` applications, satisfiable by that same measurement, so the "
        "consistency probe cannot derive `False`.",
        "witness": _WIT_C_OTHERCONV,
    },
    {
        "id": "rej-continuous-renders-a-shifted-tick-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_SHIFTTICKS,
        "refinement": "routes through the reported renderer, one label per tick, but "
        "renders a SHIFTED tick set. A faithful real counterpart hands the renderer "
        "tick positions that are not the ones the legend is showing, so every entry "
        "is labelled with a neighbouring quantity; the assertions pinning legend "
        "labels for a known tick set FAIL and it would NOT resolve.",
        "rationale": "REJECT from (T): the clause names the tick LIST too — the "
        "labels must be that renderer's rendering OF THESE TICKS. A spec pinning "
        "only 'the labels are some rendering by the reported renderer' admits this. "
        "Witness CONDITIONED at a point where the shifted and unshifted tick sets "
        "render differently; the hypothesis is a single dis-equality between two "
        "`render` applications on different tick lists, which is satisfiable "
        "(distinct quantities get distinct labels — that is what a tick label is "
        "for) so the consistency probe cannot derive `False`.",
        "witness": _WIT_C_SHIFTTICKS,
    },
    {
        "id": "rej-continuous-labels-out-of-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_REVERSE,
        "refinement": "the right renderer, the right tick set, one label per tick — "
        "reversed. A faithful real counterpart pairs each tick position with another "
        "tick's label, so the legend reads backwards; the assertions pinning legend "
        "labels in order FAIL and it would NOT resolve. On a symmetric tick set it "
        "agrees with gold, which is why the case is stated at an asymmetric one.",
        "rationale": "REJECT from (T)'s ORDER-sensitivity: `labels = render "
        "writtenFrom ticks` is an equality of sequences, not of multisets, so no "
        "permutation of the right labels satisfies it. Every other clause is "
        "satisfied by this rival except (R), which it also violates — but only (T) "
        "rejects it OUTSIDE the read-back clause's guarded domain, so the case is "
        "attributable to (T). Witness CONDITIONED at a point where the reversal is "
        "observable (the hypothesis says the label list is not its own reverse, "
        "satisfiable for any two distinct labels), so the consistency probe cannot "
        "derive `False`.",
        "witness": _WIT_C_REVERSE,
    },
    {
        "id": "rej-entry-label-for-a-tick-that-is-not-there",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_E_EMPTY,
        "refinement": "correct on every nonempty tick list; on the empty one it keeps "
        "a label for a tick that is not there. A faithful real counterpart emits a "
        "placeholder entry in a legend whose tick set came back empty, so a legend "
        "that should have no entries has one; the assertion counting a legend's "
        "entries FAILS and it would NOT resolve.",
        "rationale": "REJECT from (L): one label per tick, `render_length` giving "
        "gold the empty label list there. The empty tick list is the one domain "
        "point at which the LABEL half of every clause-(W) rival above holds "
        "vacuously, so without this case a battery effectively quantified over "
        "nonempty tick lists would pass and the length clause would go untested. "
        "Boundary family; unconditioned witness, since the length follows from "
        "`render_length` with no fact about label text needed.",
        "witness": _WIT_E_EMPTY,
    },
    {
        "id": "rej-entry-reconfigures-the-shared-renderer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_E_MUTCONV,
        "refinement": "correctly takes the compaction control AND overwrites the rest "
        "of the renderer's configuration, writing the labels from that same "
        "overwritten renderer — so its text really is the reported renderer's own "
        "output. A faithful real counterpart resets a shared renderer's remaining "
        "configuration while building a legend from it, and since that renderer "
        "outlives the call and keeps rendering the same axis, the axis labels change "
        "too: the assertions that pin the axis's own labels after a legend is built "
        "FAIL and it would NOT resolve.",
        "rationale": "REJECT from (W1) alone: `uncompacted` leaves everything but the "
        "compacting mode alone, and (W1) pins the reported renderer to its result "
        "EXACTLY. (T) is fully satisfied here, and so are (L) and (R), so without "
        "this case a spec could pin the mode and the text while leaving an impl free "
        "to reconfigure the shared renderer in any other way it liked. Unconditioned "
        "witness at a capable renderer: the reported record's `convention` component "
        "differs from the input's, which the literals decide.",
        "witness": _WIT_E_MUTCONV,
    },
    {
        "id": "rej-continuous-corrects-only-small-magnitudes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_ONLYSMALL,
        "refinement": "takes the compaction control only when every tick is small, "
        "and hands the renderer on untouched once any tick is large. A faithful real "
        "counterpart leaves precisely the large-magnitude legends the behavior exists "
        "to serve reading back as residuals, while looking correct on the small ones: "
        "the F2P assertion over a large-magnitude range FAILS and it would NOT "
        "resolve.",
        "rationale": "REJECT from (W1), which carries NO magnitude restriction. This "
        "case exists to demonstrate that the domain restriction on clause (R) did "
        "not silently narrow the rest of the specification — the failure mode a "
        "guarded clause invites. The rival satisfies (R) everywhere (R) is claimed; "
        "it is refuted only outside that guard, by the clauses claimed on the whole "
        "domain. Unconditioned witness one above the guard (2^53 + 1), which is the "
        "same point axiom_check.py obligation 4 measured the real renderer's read-"
        "back genuinely failing at (144 of 144 probes above the guard broke, 0 held), "
        "so the guard is where the real renderer stops being faithful and NOT where "
        "the specification stops binding.",
        "witness": _WIT_C_ONLYSMALL,
    },
    {
        "id": "rej-continuous-consults-the-reading-oracle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_C_ORACLE,
        "refinement": "renders once with the renderer exactly as met, reads every "
        "resulting label back, and if they all happen to recover their ticks keeps "
        "that pair and leaves the renderer alone; only otherwise does it reach for "
        "the control. No real implementation can do this — reading a label back to "
        "the quantity it denotes is not an operation the renderer offers — so a "
        "faithful real counterpart has to approximate the test, and on the tick sets "
        "where its approximation says 'good enough' it leaves the shared renderer "
        "compacting: the F2P assertion over a large-magnitude range FAILS and it "
        "would NOT resolve.",
        "rationale": "REJECT from (W1). This is the ungrounded-oracle family and it "
        "earns a case of its own because it is exactly what a specification stated "
        "ONLY as a read-back guarantee cannot reject: it satisfies (R) at every "
        "input BY CONSTRUCTION, since it evaluates (R) itself before committing. "
        "What refutes it is that (W1) is a claim about the renderer's post-state, "
        "not about the labels — a renderer that reads back acceptably while still "
        "standing in the compacting mode is still reported in that mode, and it goes "
        "on rendering the same axis afterwards. The case is therefore the direct "
        "evidence that (R) alone is not the contract and the renderer's post-state "
        "had to become an observable. Witness CONDITIONED on the branch where the "
        "rival's own check PASSES: the hypothesis says only that the labels this "
        "renderer writes as met do read back to their ticks, which is satisfiable — "
        "it is what an already-quiescent renderer does, and axiom_check.py obligation "
        "6 recorded real renderers writing labels that read back on 3983 of 52571 "
        "observations — so the consistency probe cannot derive `False`.",
        "witness": _WIT_C_ORACLE,
    },
]
