"""properties.py — G-PBT falsification manifest for mwaskom__seaborn-3187 (velvet).

A PORT of the nagini sibling's battery onto this backend's carrier, not a new
invention: each case below carries a nagini case's ARGUMENT re-expressed against
the frozen `Solution.lean`. Every variant is built by region surgery inside a
`-- impl-start`/`-- impl-end` body, and every case except ONE additionally keeps
both frozen `prove_correct` tactic bodies byte-identically (asserted at load, not
merely described). `markers.same_spec` therefore holds by construction, and a
rejection is attributable to the contract rather than to a tampered spec or a
relaxed proof script.

The single exception is the soundness positive `pos-alt-path-empty-literal`,
which reshapes an impl in a way the frozen tactic script cannot follow and so
supplies its own script for ONE obligation. That is admissible here and is the
whole point of the case: `variant_scope` pins the obligation's EXISTENCE and its
statement, not its tactic body, so the reshape is checked against the same
contract while being allowed to close it by a different route. It adds no lemma,
axiom, `sorry` or `native_decide` — see the case's own rationale, and the
`_REPROVES` accounting below, which keeps the byte-identity assertion strict for
every other case so a neutered obligation still has nowhere to hide.
Every `expect="reject"` case additionally carries a machine-checked refutation
`witness` (each was built BOTH ways with scripts/lean_verify.sh: it elaborates
against its rival and FAILS against the frozen solution).

DEFENDED SURFACE
----------------
Two contracted methods build the labels of a brief numeric legend from a list of
tick positions, given the renderer AS INSTALLED (`cfg`, an opaque handle):

  legendLabels (modesAvailable : Bool) (cfg : RendererConfig)
              (ownLabels : List String) (ticks : List Float)
              return (labels : List String)
    require ownLabels.length = ticks.length                       (D1)
    require modesAvailable = true → renders cfg false false ticks  (D2)
    ensures labels.length = ticks.length                          (L1)
    ensures modesAvailable = false → labels = ownLabels           (P1)
    ensures modesAvailable = true → ∃ offsetMode scaleMode,
      labels = renderTicks cfg offsetMode scaleMode ticks ∧       (R1)
      sharedTerm cfg offsetMode scaleMode ticks = ""              (N1)

  legendEntries (isLog : Bool) (cfg : RendererConfig) (ticks : List Float)
              return (labels : List String)
    require isLog = true → rendersLog cfg ticks                   (D3)
    require isLog = false → renders cfg false false ticks         (D4)
    ensures labels.length = ticks.length                          (L2)
    ensures isLog = true → labels = renderLog cfg ticks           (G2)
    ensures isLog = false → ∃ offsetMode scaleMode,
      labels = renderTicks cfg offsetMode scaleMode ticks ∧       (R2)
      sharedTerm cfg offsetMode scaleMode ticks = ""              (N2)

Read the clauses adversarially. (L1)/(L2) are pure COUNT facts: one legend entry
per tick, nothing dropped and nothing duplicated. (P1)/(G2) PIN the untouched
paths exactly: on the path a selector routes away from the numeric renderer, the
legend's labels ARE that renderer's own output, so neither substituting a
different renderer nor post-processing its labels is admitted. (R1)/(R2) pin the
numeric paths' CALL: the labels must BE the numeric renderer's output — for
EXACTLY the given tick list, on EXACTLY the installed renderer handle — under
some setting of its two modes. That is deliberately silent about WHICH setting,
but it forbids rendering a DIFFERENT list, post-processing what comes back, or
reading the labels off some other renderer than the one installed. (N1)/(N2) are
the DISPLAY facts and they are conjoined INSIDE the same existential: whichever
setting produced the labels must hoist NOTHING out of them
(`sharedTerm … = ""`), so a label carrying only a deviation from a separately
reported shared term, or only leading digits, is refused. Because (R) and (N)
share one existential, a rival is refuted by showing that NO mode pair both
reproduces its output and hoists nothing — a single witness statement, which is
why the clause table below lists rivals against the pair.

Why the display fact is stated as "nothing was hoisted" rather than as a
numeric read-back of the label text: the renderer chooses ONE shared digit count
for a whole tick list relative to its range, and it may legitimately be
configured to print typeset or marked-up labels that no numeric reading parses
at all — so "each label reads back to its tick" is FALSE of configurations that
are perfectly acceptable for a legend, while "nothing was hoisted out of the
labels" is TRUE of exactly the acceptable ones. mapping.md §1.1/§3 records the
measurements; axiom_check.py (G-AX) re-runs them.

BOTH obligations are selector-dispatched, and the two selectors are NOT the same
question. `isLog` on the second names which of two renderers a spacing chooses,
both reachable there. `modesAvailable` on the FIRST names whether the configured
renderer has the shared-term modes AT ALL: a renderer that lacks them has
nothing to configure and its labels are simply its own, so (R1)/(N1) are not
facts about that path and (P1) is what holds there instead. The two-clause split
is therefore forced by the modeled callee, not a convenience: an unconditional
(R1) would be a claim about renderers that were never called that way, and an
(R1) dropped rather than guarded would leave the numeric path unpinned. Two
rivals hold each side of that guard fixed (see the clause table) so neither value
of `modesAvailable` is a binder every witness pins.

CARRIER — the fact that governs this whole port. `renderTicks`, `sharedTerm` and
`renderLog` are OPAQUE axioms over an OPAQUE renderer handle `RendererConfig`;
the kernel knows only their lengths (`renderTicks_length`, `renderLog_length`),
that both modes off hoist nothing (`sharedTerm_none`), and that some
configuration and tick list DO hoist something when the modes are on
(`sharedTerm_hoists`). Each of those three facts is stated only on the modeled
DOMAIN of the renderer it is about (`renders` for the numeric one, `rendersLog`
for the log one — the installations and tick lists for which it yields labels at
all rather than failing outright), and the domains are themselves opaque
predicates, inhabited by `renders_nonvacuous` and supplied to each obligation by
a `require` per arm (D2/D3/D4). That shape is load-bearing for this battery in
two directions: a rival calling the numeric renderer at a setting the domain
`require` does not cover cannot even reach its COUNT clause, and the length
rewrites the count witnesses use now carry a domain hypothesis of their own
(satisfiable — the predicates are opaque — and screened by the gate's own
`False`-derivation probe like every other witness hypothesis). No concrete label
VALUE is computable and no handle is
constructible, which is exactly what keeps the surface faithful — nothing is
pinned to an answer key an impl could echo. Ticks are `Float`, the IEEE-754
double-precision positions the renderer really receives, so no value-dependent
rival can hide behind a carrier that only sees whole numbers. This dictates how
each clause is attacked:

  * (L1)/(L2) are TRANSPARENT in the length axioms: a rival that drops or
    duplicates entries is refuted by rewriting with `renderTicks_length` and
    closing arithmetically. Those witnesses bind the renderer handle, which no
    impl can construct and no axiom pins, plus the one domain fact that rewrite
    now needs (`renders cfg false false <the witness's own tick list>`) — an
    assumption about an opaque predicate at an opaque handle, so it pins nothing
    and the probe cannot derive False from it.
  * (R1)/(N1)/(R2)/(N2)/(P1)/(G2) reference the opaque terms, so `decide` cannot
    reach them. They are attacked by CONDITIONING ON THE CARRIER: the refutation
    is stated at a point described by a single hypothesis separating the rival's
    output from every admissible rendering (or, for a mode rival, saying that
    every setting reproducing its output hoists something; or, for a pinned path,
    separating the two renderers' outputs). Read the mode rivals' claim:
    *wherever the abbreviating configuration's labels are reproducible only by a
    setting that hoists a shared term, the rival contradicts the postcondition* —
    precisely the sub-domain where the rival is wrong, and a stronger statement
    than any single literal could make. Each hypothesis is a single weak
    assumption about ONE opaque family (or, for the pinned path, about a concrete
    list and its reversal), so the binders are jointly satisfiable; every one was
    run through the gate's own `False`-derivation probe out-of-band and the probe
    FAILED (consistent).
  * `Float` ticks are not decidable literals for the kernel (the arithmetic is
    an opaque extern), so a rival whose guard inspects tick VALUES is refuted at
    an abstract tick list carrying the guard's own outcome as a hypothesis rather
    than at a literal — see weak-modes-off-only-for-whole-number-ticks, the case
    that exists because a whole-number-only rival is exactly what an `Int`
    carrier would have admitted.

ADVERSARIAL READ of the nagini classes on this carrier
-----------------------------------------------------
  * SOUNDNESS positives — APPLY. FOUR structurally different but correct impls
    (mode constants inlined into the render call rather than let-bound; EACH
    obligation's selector guard negated with its two branch bodies exchanged —
    one case per obligation, since both dispatch; and the pinned log path
    special-casing the empty tick list and returning the empty legend
    LITERALLY, which that renderer's own count fact forces to be its output
    there) must verify,
    else the spec is over-fit to the impl's shape (SPEC-TOO-STRONG). All four
    were rebuilt and elaborate. The last is the strongest of them, because it is
    the only one whose reshape the frozen tactic script does NOT follow: it
    therefore separates "the CONTRACT admits this correct impl" from "the frozen
    script happens to close it", which is the distinction a tactic-proof backend
    most easily loses.
  * ADMISSIBILITY — APPLIES, and it is carried by TWO positives, one per
    KIND of `require` this spec states. (i) `ownLabels.length = ticks.length`
    (D1) is a count precondition: the sibling's self-call-on-a-fresh-input probe
    becomes an in-region `assert` that a legitimate renderer's own labels for a
    legitimate tick list satisfy it AND are non-degenerate. (ii) D2/D3/D4 are
    DOMAIN preconditions — the renderer an arm calls must actually yield labels
    for these ticks at the setting that arm uses — and what can be too strong
    about them is not their truth (an opaque predicate has none the kernel can
    see) but their SHAPE: a domain stated at the wrong setting, or on the wrong
    arm, would not reach the call it is supposed to license, and every impl would
    then be rejected for want of a hypothesis rather than for being incorrect.
    `admiss-render-domain-reaches-the-call` asserts the domain fact in-region at
    exactly the point of the call, discharged by the frozen script unaided;
    perturbing the asserted setting to `renders cfg true true ticks` makes the
    case FAIL, and so does the same assert on the arm that calls nothing.
    Whether the domain is inhabited at all by the real renderer is a MEASUREMENT,
    not a verifier question, and it is G-AX's (mapping.md §3.4). Load-bearing by
    measurement in both cases: perturbing the asserted count, or the asserted
    setting, makes the case FAIL.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries TWO MANDATORY
    frame rivals (append to, and store into, a tick list held at a fractional
    heap permission) to trip INSUFFICIENT PERMISSION. This backend is
    referentially transparent: `ticks`, `cfg` and the two selectors are
    immutable values, no binder is `mut`, there is no heap and no aliasing —
    there is no read-only input a rival could write through and no substitute
    probe to build. Not fabricated, per the porting map.
  * DIVERGENCE — APPLIES, and it is SHIPPED as a uniqueness rival
    (``weak-labels-spins-before-rendering``), not disposed of in prose. The
    frozen impl regions are all LOOP-FREE (straight-line ``let`` / ``if`` over
    immutable values), so a diverging rival cannot be obtained by mutating a
    body — it has to bring a loop of its own, which is what that case splices
    ahead of an otherwise gold numeric arm. The rival is refused, and the
    refusal is the SPEC's: this bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics (both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here). Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation. Measured on this bundle with a real
    build: a ``while spin > 0`` prefix whose body is ``spin := spin``, carrying
    a well-typed ``decreasing spin``, is REJECTED on the measure's own goal
    (``case «decreasing_1: spin» ... ⊢ False``, both ``require``s in context).
    Dropping the clause rather than letting it fail is refused even earlier, by
    the elaborator's own check (``Decreasing annotations are required in total
    correctness semantics``), which is why the shipped rival carries the clause:
    an omitted one would test the parser instead of the contract. A ``decreasing``
    measure must be a ``Nat`` — an ``Int`` one fails as a TYPE error
    (``has type ℤ but is expected to have type Option ℕ``) that masks the
    verdict, so the shipped rival uses ``Nat``. Because "the rival does not
    verify" is not on its own attributable to the spec on a tactic-proof
    backend, the case also carries a witness that PROVES the rival's run
    diverges — ``Loop.forIn.loop``'s own fixpoint induction over the flat order
    whose bottom is the diverging value — so it has no result where gold's run
    has one.
  * AXIOM_TESTS — dropped; the axiom lane is G-AX's job (axiom_check.py) and
    this gate ignores them.

CASE-COUNT NOTE. The sibling contracts two byte-identical single-clause-family
functions over one list input; here EACH method carries a renderer selector, a
renderer handle and its own pinned path, so the surface is wider on one axis
(three extra binders, clauses (P1)/(G2) with no sibling counterpart, and a
partial callee whose modeled DOMAIN each arm must be handed) and narrower on
another (no permission lane).
Parity is not the target; the accounting table at the bottom names every sibling
case's disposition.
"""
from pathlib import Path

INSTANCE = "mwaskom__seaborn-3187"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Region surgery with a loud drift check, as in the nagini sibling."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Surgery anchors. Each lies ENTIRELY inside one `-- impl-start`/`-- impl-end`
# region (the last is the elided `prove_correct` tactic body) and each is unique
# in Solution.lean — both facts asserted at load by _swap, so the frozen spec
# view and every `prove_correct` header survive by construction.
# ---------------------------------------------------------------------------

# The first method's numeric-renderer arm only. Both methods dispatch on a
# renderer selector, so their numeric arms are byte-identical at the same indent;
# each anchor therefore carries its OWN arm's leading comment, which makes it
# unique (asserted below). A replacement drops that comment — comments live
# inside the impl region, which the spec view projects out, so no variant can
# perturb the frozen spec text through this.
_LL = (
    "      -- Render with BOTH shared-term abbreviation modes turned off, so nothing\n"
    "      -- is hoisted out of the labels (the only faithful choice for a legend).\n"
    "      let offsetMode : Bool := false\n"
    "      let scaleMode : Bool := false\n"
    "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
    "      return labels\n"
)

# the first method's no-modes arm only (the pinned own-labels path)
_LL_OWN = (
    "      -- No shared-term modes exist on this renderer: nothing is configured and\n"
    "      -- the legend shows exactly its own labels.\n"
    "      return ownLabels\n"
)

# the first method's ENTIRE branch, guard included (for the branch-flip positive)
_LL_BOTH = (
    "    if modesAvailable then\n"
    "      -- Render with BOTH shared-term abbreviation modes turned off, so nothing\n"
    "      -- is hoisted out of the labels (the only faithful choice for a legend).\n"
    "      let offsetMode : Bool := false\n"
    "      let scaleMode : Bool := false\n"
    "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
    "      return labels\n"
    "    else\n"
    "      -- No shared-term modes exist on this renderer: nothing is configured and\n"
    "      -- the legend shows exactly its own labels.\n"
    "      return ownLabels\n"
)

# the second method's linear-path arm only, with its own leading comment (see _LL)
_LE_LINEAR = (
    "      -- Linear axis: render with BOTH shared-term abbreviation modes off so\n"
    "      -- nothing is hoisted out of the labels.\n"
    "      let offsetMode : Bool := false\n"
    "      let scaleMode : Bool := false\n"
    "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
    "      return labels\n"
)

# the second method's alternative-renderer arm only, with its leading comment
_LE_ALT = (
    "      -- Logarithmic axis: the log renderer is used unchanged; the legend\n"
    "      -- shows exactly its labels for this installation.\n"
    "      let labels :| labels = renderLog cfg ticks\n"
    "      return labels\n"
)

# the second method's ENTIRE branch, guard included (for the branch-flip positive)
_LE_BOTH = (
    "    if isLog then\n"
    "      -- Logarithmic axis: the log renderer is used unchanged; the legend\n"
    "      -- shows exactly its labels for this installation.\n"
    "      let labels :| labels = renderLog cfg ticks\n"
    "      return labels\n"
    "    else\n"
    "      -- Linear axis: render with BOTH shared-term abbreviation modes off so\n"
    "      -- nothing is hoisted out of the labels.\n"
    "      let offsetMode : Bool := false\n"
    "      let scaleMode : Bool := false\n"
    "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
    "      return labels\n"
)

for _a in (_LL, _LL_OWN, _LL_BOTH, _LE_LINEAR, _LE_ALT, _LE_BOTH):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"drift: anchor not unique in Solution.lean: {_a!r}")

# Every case below edits an impl region, and every case but ONE leaves both
# `prove_correct` tactic bodies byte-identical, so the frozen proof scripts
# survive verbatim in twenty-three of the twenty-four variants. Asserted rather
# than described, since an admissibility positive that had to relax the frozen
# script would be the first place a neutered obligation could hide.
#
# `_REPROVES` names the sole exception and the ONE obligation it reproves, so the
# exemption is a two-entry whitelist rather than a hole: the other obligation's
# frozen body is still required verbatim even in that case, and every other case
# is still required to keep both. See `pos-alt-path-empty-literal`.
_FROZEN_PROOFS = (
    "prove_correct legendLabels by\n"
    "  loom_solve <;> subst_vars <;>\n"
    "    first\n"
    "      | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)\n"
    "      | simp_all [renderTicks_length]\n",
    "prove_correct legendEntries by\n"
    "  loom_solve <;> subst_vars <;>\n"
    "    first\n"
    "      | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)\n"
    "      | simp_all [renderTicks_length, renderLog_length]\n",
)
for _p in _FROZEN_PROOFS:
    if _BASE.count(_p) != 1:
        raise AssertionError(f"drift: frozen proof body not found: {_p!r}")


# The one case that reproves an obligation, and which obligation it reproves.
# Everything not listed here is held to BOTH frozen bodies, verbatim.
_REPROVES = {"pos-alt-path-empty-literal": _FROZEN_PROOFS[1]}

# The reproved `legendEntries` script. It keeps the frozen script's two
# alternatives VERBATIM and inserts one more between them, for the single goal
# the reshape adds: on the empty tick list the pinned log path must show
# `[] = renderLog cfg ticks`. That follows from the log renderer's own count
# fact on the domain the arm was handed — the `require` gives `rendersLog cfg
# ticks` there, the count fact then forces a length-0 result, and a list of
# length 0 IS the empty list. Nothing about the OTHER renderer is used (the two
# are not interchangeable on the empty list once partiality is modeled: measured,
# at a wide installation the log renderer returns `[]` and the numeric one with
# both switches off returns nothing at all — mapping.md §3.4). No lemma is
# declared, no axiom is added, nothing is assumed.
_LE_PROOF_EMPTY = (
    "prove_correct legendEntries by\n"
    "  loom_solve <;> subst_vars <;>\n"
    "    first\n"
    "      | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)\n"
    "      | (intro _\n"
    "         have hg : rendersLog cfg ticks := by simp_all\n"
    "         have g2 := renderLog_length cfg ticks hg\n"
    "         have ht : ticks = [] := by simp_all\n"
    "         subst ht\n"
    "         simp only [List.length_nil, List.length_eq_zero_iff] at g2\n"
    "         exact g2.symm)\n"
    "      | simp_all [renderTicks_length, renderLog_length]\n"
)


def _modes(off, scale):
    """First method's numeric-renderer arm with the two display-mode constants
    set as given."""
    return _swap(_BASE, _LL,
                 f"      let offsetMode : Bool := {off}\n"
                 f"      let scaleMode : Bool := {scale}\n"
                 "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
                 "      return labels\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different CORRECT impls that
    # MUST verify. If a faithful reshape cannot verify, the spec is over-fit to
    # the impl's shape => SPEC-TOO-STRONG. All were rebuilt out-of-band (exit 0),
    # three of them with the frozen `prove_correct` bodies unchanged.
    # =====================================================================
    {
        "id": "pos-inline-mode-constants",
        "kind": "soundness",
        "expect": "verify",
        # Drop the two named mode locals, pass the constants positionally into
        # the render call, and bind the chosen value to an intermediate local
        # before returning it. Observationally identical to the frozen body.
        "module": _swap(_BASE, _LL,
                        "      let chosen :| chosen = renderTicks cfg false false ticks\n"
                        "      let labels := chosen\n"
                        "      return labels\n"),
        "rationale":
            "PASS SOURCE = L1 ∧ R1 ∧ N1. The two abbreviation switches are "
            "supplied positionally instead of through named locals, and the "
            "chosen value is returned via an intermediate binding — same handle, "
            "same configuration, same result, so the count clause (L1) and the "
            "existential (R1 ∧ N1) discharge from the same axioms and the frozen "
            "tactic body closes it unchanged. A faithful structurally-different "
            "reshape MUST verify; if it cannot, the postcondition is over-fit to "
            "the local shape => SPEC-TOO-STRONG. (Sibling: pos-precomputed-sequence, "
            "whose argument is exactly 'compute the rendering once and drop the "
            "intermediates'.)",
    },
    {
        "id": "pos-branch-guard-flip",
        "kind": "soundness",
        "expect": "verify",
        # Negate the renderer-selection guard and exchange the two arms. Same
        # renderer on the same input in both cases; only the branch order moves.
        "module": _swap(_BASE, _LE_BOTH,
                        "    if !isLog then\n"
                        "      -- Linear axis: render with BOTH shared-term abbreviation modes off so\n"
                        "      -- nothing is hoisted out of the labels.\n"
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      return labels\n"
                        "    else\n"
                        "      -- Logarithmic axis: the log renderer is used unchanged; the legend\n"
                        "      -- shows exactly its labels for this installation.\n"
                        "      let labels :| labels = renderLog cfg ticks\n"
                        "      return labels\n"),
        "rationale":
            "PASS SOURCE = L2 ∧ G2 ∧ (R2 ∧ N2). The renderer-selection guard is "
            "negated and the two arms exchanged, so each selector value still "
            "reaches the same renderer with the same configuration. All three "
            "clauses still discharge (the pinned alternative path G2 on one arm, "
            "the count clause and the existential on the other) and the frozen "
            "tactic body closes it unchanged. Must verify, else the spec is "
            "over-fit to the branch ORDER => SPEC-TOO-STRONG. This is the "
            "sibling's structural-reshape argument applied to the only "
            "control-flow choice this carrier has.",
    },

    {
        "id": "pos-labels-branch-guard-flip",
        "kind": "soundness",
        "expect": "verify",
        # Negate the FIRST method's mode-availability guard and exchange its two
        # arms. Each selector value still reaches the same renderer, so this is
        # observationally identical to the frozen body.
        "module": _swap(_BASE, _LL_BOTH,
                        "    if !modesAvailable then\n"
                        "      -- No shared-term modes exist on this renderer: nothing is configured and\n"
                        "      -- the legend shows exactly its own labels.\n"
                        "      return ownLabels\n"
                        "    else\n"
                        "      -- Render with BOTH shared-term abbreviation modes turned off, so nothing\n"
                        "      -- is hoisted out of the labels (the only faithful choice for a legend).\n"
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      return labels\n"),
        "rationale":
            "PASS SOURCE = L1 ∧ P1 ∧ (R1 ∧ N1). The first method's "
            "mode-availability guard is negated and its two arms exchanged, so "
            "each selector value still reaches the same renderer with the same "
            "configuration. All three clauses still discharge (the pinned "
            "own-labels path P1 on one arm, the count clause and the existential "
            "on the other) and the frozen tactic body closes it unchanged. MUST "
            "verify, else the spec is over-fit to the branch ORDER of the FIRST "
            "obligation => SPEC-TOO-STRONG. The counterpart of "
            "pos-branch-guard-flip on the obligation that also carries a two-way "
            "renderer dispatch.",
    },
    {
        "id": "pos-alt-path-empty-literal",
        "kind": "soundness",
        "expect": "verify",
        # The pinned log path splits on the empty tick list and returns the empty
        # legend LITERALLY there instead of calling the renderer. That renderer
        # emits one label per tick on the domain this arm was handed, so on the
        # empty list its output IS `[]` — the two arms are OBSERVABLY equal, and
        # the impl is faithful, without any claim about the OTHER renderer.
        "module": _swap(
            _swap(_BASE, _LE_ALT,
                  "      if ticks.isEmpty then\n"
                  "        return ([] : List String)\n"
                  "      else\n"
                  "        let labels :| labels = renderLog cfg ticks\n"
                  "        return labels\n"),
            _FROZEN_PROOFS[1], _LE_PROOF_EMPTY),
        "rationale":
            "PASS SOURCE = L2 ∧ G2 ∧ (R2 ∧ N2), and the case exists because it "
            "is the only positive whose reshape the FROZEN tactic script does "
            "not follow. On the empty tick list the log renderer's own count "
            "fact — available there, because the arm's domain `require` (D3) "
            "hands it over — forces a length-0 result, and a list of length 0 IS "
            "the empty list, so returning `[]` outright on that arm is a faithful "
            "impl and (G2) is satisfied by it. This separates two things a "
            "tactic-proof backend otherwise conflates: whether the CONTRACT "
            "admits a correct impl, and whether the frozen script happens to "
            "close it. The contract does; the frozen script leaves "
            "`[] = renderLog cfg ticks` open, so this case supplies a script for "
            "that ONE obligation which keeps the frozen script's own two "
            "alternatives verbatim and adds one that proves the residual goal "
            "from the log count fact and the domain the arm was given — no "
            "lemma, no axiom, no `sorry`, no `native_decide`, and "
            "`legendLabels`'s frozen body untouched. Deliberately NOT the "
            "cross-renderer collapse an earlier revision shipped here (serving "
            "the NUMERIC renderer on the empty arm): once the renderers' modeled "
            "DOMAINS are stated, that impl is no longer faithful — measured, at a "
            "wide installation the log renderer returns `[]` where the numeric "
            "one with both switches off returns nothing at all (mapping.md §3.4) "
            "— so it is not a correct impl to demand the spec admit. MUST "
            "verify: if the spec could not admit an impl that is faithful at "
            "every input, it would be over-fit to the frozen impl's branch "
            "STRUCTURE rather than to its behavior => SPEC-TOO-STRONG. This is "
            "the sibling's structural-reshape argument (pos-precomputed-sequence) "
            "pushed to the one reshape on this carrier "
            "that the frozen script cannot absorb.",
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The spec carries TWO KINDS of `require` —
    # `ownLabels.length = ticks.length` on the first obligation — so the
    # sibling's "a normal input satisfies the precondition" probe has exactly one
    # counterpart. An in-region `assert` states that a legitimate renderer's own
    # labels for a legitimate tick list satisfy it and are non-degenerate. If a
    # legitimate input could not be shown admissible the assert would leave an
    # unsolved goal => PRECOND-TOO-STRONG.
    #
    # It is LOAD-BEARING, and this was measured rather than asserted: perturbing
    # the asserted count to a false value makes the case FAIL, so the assert is
    # discharged by the length fact rather than skipped. It keeps BOTH frozen
    # `prove_correct` bodies BYTE-IDENTICAL.
    #
    # ONE probe rather than three, because the domain `require` an earlier
    # revision of this manifest probed (a float-exact magnitude bound on the
    # ticks) is GONE: the carrier is now the same IEEE-754 double the renderer
    # receives, so no magnitude restriction is stated and there is none to probe.
    # The second obligation carries NO `require`, so it has no admissibility
    # question of its own; a fabricated probe there would assert nothing.
    # =====================================================================
    {
        "id": "admiss-own-labels-length-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _LL,
                        "      assert (with_name_prefix `adm\n"
                        "        ((([\"100000000\", \"100000002.5\", \"100000005\"] : List String)).length =\n"
                        "           ([(100000000.0:Float), (100000002.5:Float), (100000005.0:Float)]).length ∧\n"
                        "         ([(100000000.0:Float), (100000002.5:Float), (100000005.0:Float)]).length = 3))\n"
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      return labels\n"),
        "rationale":
            "the sole modeled precondition (D1) `ownLabels.length = "
            "ticks.length` must ADMIT what a real renderer hands the site: one "
            "label per tick, for the tick positions a real numeric legend draws. "
            "The in-region assert discharges (D1) for a concrete "
            "three-label/three-tick pair at the reported scenario's magnitude "
            "(~1e8, including a half-integral position, so the probed input is "
            "not a whole-number special case) and pins its count at 3, so the "
            "probed input is non-degenerate rather than the empty list that "
            "satisfies every clause vacuously. If it could not discharge => "
            "PRECOND-TOO-STRONG (the site's own renderer output would be "
            "excluded). Load-bearing: perturbing the asserted count 3 -> 4 makes "
            "this case FAIL. The frozen obligation header AND both frozen tactic "
            "bodies are untouched, and L1 ∧ R1 ∧ N1 still discharge. (Sibling: "
            "admiss-self-call-arrived-state-nondefault-convention, the same 'a "
            "legitimate input is admissible' argument.)",
    },

    {
        "id": "admiss-render-domain-reaches-the-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _LL,
                        "      assert (with_name_prefix `adm2 (renders cfg false false ticks))\n"
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      return labels\n"),
        "rationale":
            "the DOMAIN precondition (D2) `modesAvailable = true → renders cfg "
            "false false ticks` must be usable where the routine needs it: at the "
            "call, on the arm that makes it, at the SETTING that arm uses. The "
            "in-region assert states exactly that fact at exactly that point and "
            "is discharged by the frozen tactic script unaided, so the arm's "
            "hypothesis really does license its own call rather than some "
            "neighbouring one. If it could not discharge => PRECOND-TOO-STRONG in "
            "the shape that matters for a partial callee: a domain stated at the "
            "wrong setting or on the wrong arm would reject every impl for want of "
            "a hypothesis, which no rival could distinguish from the spec being "
            "genuinely violated. Load-bearing, measured both ways: perturbing the "
            "asserted setting to `renders cfg true true ticks` makes this case "
            "FAIL (build error: `⊢ renders cfg true true ticks` left open), and so "
            "does asserting it on the no-modes arm, which is handed nothing. The "
            "frozen obligation headers AND both frozen tactic bodies are "
            "untouched, and L1 ∧ R1 ∧ N1 still discharge. Whether the domain is "
            "INHABITED by the real renderer is a measurement rather than a "
            "verifier question and belongs to G-AX (mapping.md §3.4); this case is "
            "only about the guard being where the proof needs it. (Sibling: "
            "admiss-self-call-arrived-state-nondefault-convention, the same 'a "
            "legitimate input is admissible' argument, applied to the "
            "precondition this backend's "
            "partial callee forces.)",
    },

    # =====================================================================
    # UNIQUENESS rivals (expect=reject) — wrong impls sharing the frozen spec.
    # Grouped by the clause each attacks. Every one carries a witness verified
    # BOTH ways out-of-band, and every witness's hypotheses were run through the
    # `False`-derivation probe (all FAILED => consistent).
    #
    # Every witness binds `cfg : RendererConfig`, because the handle is an opaque
    # TYPE with no constructor: there is no literal renderer to state a claim at,
    # so the refutations are stated for an arbitrary installed renderer — which
    # is strictly stronger than picking one.
    # =====================================================================

    # ---- (N1) the display fact of the first method: both switches on ----
    {
        "id": "weak-both-modes-enabled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _modes("true", "true"),
        "refinement":
            "leaving BOTH shared-term abbreviation switches enabled is the "
            "pre-change configuration: the renderer may then hoist a term shared "
            "by every tick out of the labels and report it separately, where a "
            "legend has nowhere to show it, so each label prints only a "
            "deviation from that term or only the leading digits. The failing "
            "examples read every legend label back to a number and assert it "
            "exceeds a threshold four orders of magnitude below the data; with "
            "the abbreviation active the read-back values fall below it and both "
            "assertions stay RED. It would NOT resolve.",
        "rationale":
            "REJECT from N1 (the `sharedTerm … = \"\"` conjunct inside the first "
            "obligation's existential). The rival hands the renderer the "
            "abbreviating configuration, so the only settings that reproduce its "
            "labels are settings that hoist a shared term, and the existential "
            "cannot be satisfied. The renderer is opaque, so the refutation "
            "CONDITIONS on the carrier with exactly that statement: every "
            "setting reproducing the abbreviating output hoists something. If it "
            "verified => SPEC-TOO-WEAK (the whole reported defect admitted). "
            "Abuses the `ticks` binder of the first obligation at a single-tick "
            "input. (Sibling: mode-token-swap, the rival whose rendering is taken "
            "at the mode the spec pins against.)",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool),\n"
            "      renderTicks cfg true true [(5.0:Float)] = renderTicks cfg o s [(5.0:Float)] →\n"
            "        sharedTerm cfg o s [(5.0:Float)] ≠ \"\") :\n"
            "    ¬ (∀ labels, (legendLabels true cfg [\"a\"] [(5.0:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool), labels = renderTicks cfg o s [(5.0:Float)] ∧\n"
            "          sharedTerm cfg o s [(5.0:Float)] = \"\") := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, hs⟩ := hall _ rfl\n"
            "  exact h o s ho hs\n",
    },

    # ---- (N1) ONE switch left on, each independently ----
    {
        "id": "weak-additive-mode-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _modes("true", "false"),
        "refinement":
            "disabling only the multiplicative abbreviation and leaving the "
            "ADDITIVE one enabled is the partial change. It is indistinguishable "
            "from the correct configuration on data with no common additive "
            "term, so it looks right on most legends; but on the reported "
            "scenario — levels sharing a large additive offset — the renderer "
            "hoists that offset out and reports it separately, so each label "
            "prints only its deviation, the read-back values are tiny and the "
            "threshold assertion stays RED. It would NOT resolve.",
        "rationale":
            "REJECT from N1. Attacks the ADDITIVE switch in ISOLATION, so the "
            "battery shows the spec depends on that switch specifically and not "
            "merely on 'some switch is off'. A NEAR-MISS relative to "
            "weak-both-modes-enabled (it agrees with gold on every input with no "
            "shared additive term), so it gets its OWN witness at its own "
            "distinguishing input: a two-tick list at the reported ~1e8 "
            "magnitude with a HALF-INTEGRAL second position, exactly the shape "
            "the failing examples draw. If it verified => SPEC-TOO-WEAK (a "
            "half-change admitted). (Sibling: left-residual-enabled, the "
            "one-abbreviation-still-enabled shape.)",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool),\n"
            "      renderTicks cfg true false [(100000000.0:Float), (100000002.5:Float)] =\n"
            "          renderTicks cfg o s [(100000000.0:Float), (100000002.5:Float)] →\n"
            "        sharedTerm cfg o s [(100000000.0:Float), (100000002.5:Float)] ≠ \"\") :\n"
            "    ¬ (∀ labels, (legendLabels true cfg [\"a\", \"b\"]\n"
            "          [(100000000.0:Float), (100000002.5:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool),\n"
            "          labels = renderTicks cfg o s [(100000000.0:Float), (100000002.5:Float)] ∧\n"
            "          sharedTerm cfg o s [(100000000.0:Float), (100000002.5:Float)] = \"\") := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, hs⟩ := hall _ rfl\n"
            "  exact h o s ho hs\n",
    },
    {
        "id": "weak-multiplicative-mode-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _modes("false", "true"),
        "refinement":
            "the mirror half-change: the additive abbreviation is disabled but "
            "the MULTIPLICATIVE one is left enabled, so the renderer may hoist a "
            "common power-of-ten factor out of the legend and report it "
            "separately while each label prints only its leading digits. On the "
            "reported large-magnitude data the read-back values are then small "
            "mantissas rather than the actual levels, and the threshold "
            "assertion stays RED. It would NOT resolve.",
        "rationale":
            "REJECT from N1. The other half of the switch pair, attacked in "
            "ISOLATION: with this case and weak-additive-mode-only the battery "
            "demonstrates that BOTH switches are independently load-bearing — "
            "the corpus failure mode where two independent toggles exist and "
            "every witness holds one of them fixed. Refuted at a THIRD input "
            "(two ticks at ~1.2e7). If it verified => SPEC-TOO-WEAK.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool),\n"
            "      renderTicks cfg false true [(12340000.0:Float), (12350000.0:Float)] =\n"
            "          renderTicks cfg o s [(12340000.0:Float), (12350000.0:Float)] →\n"
            "        sharedTerm cfg o s [(12340000.0:Float), (12350000.0:Float)] ≠ \"\") :\n"
            "    ¬ (∀ labels, (legendLabels true cfg [\"a\", \"b\"]\n"
            "          [(12340000.0:Float), (12350000.0:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool),\n"
            "          labels = renderTicks cfg o s [(12340000.0:Float), (12350000.0:Float)] ∧\n"
            "          sharedTerm cfg o s [(12340000.0:Float), (12350000.0:Float)] = \"\") := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, hs⟩ := hall _ rfl\n"
            "  exact h o s ho hs\n",
    },

    # ---- (N1) the abbreviation restored on a VALUE-DEPENDENT sub-domain ----
    {
        "id": "weak-modes-off-only-for-whole-number-ticks",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct configuration when every tick is a whole number, the
        # abbreviating one otherwise. This is the rival an integer-only carrier
        # could not have seen at all.
        "module": _swap(_BASE, _LL,
                        "      let whole : Bool := ticks.all (fun t => t == t.floor)\n"
                        "      let offsetMode : Bool := !whole\n"
                        "      let scaleMode : Bool := !whole\n"
                        "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      return labels\n"),
        "refinement":
            "configuring the renderer faithfully only when every tick position "
            "is a whole number, and restoring the abbreviating configuration "
            "otherwise, is the reported defect confined to fractional tick "
            "positions. Whole-number legends look correct; a legend over "
            "fractional levels loses whatever the renderer hoists out. Both "
            "failing examples and the regression suite's own expected legend "
            "text are built on fractional levels (the reported scenario's "
            "positions are not whole numbers, and the regression case's are "
            "0.20/0.22/0.24/…), so those assertions stay RED. It would NOT "
            "resolve.",
        "rationale":
            "REJECT from N1 on the FRACTIONAL sub-domain — the value-dependent "
            "partial-domain attack, and the case that pins the CARRIER. On a "
            "carrier whose ticks were integers this rival would be "
            "indistinguishable from gold INSIDE THE MODEL (its guard would be "
            "true at every modeled input) and would verify while the real "
            "counterpart regresses the suite; the ticks are `Float` — the "
            "IEEE-754 doubles the renderer really receives — precisely so that "
            "this rival is refutable. Strictly harder than "
            "weak-both-modes-enabled: it agrees with gold on the entire "
            "whole-number sub-domain, so a witness at whole-number literals "
            "would NOT discriminate it. Float arithmetic is opaque to the kernel, "
            "so the refutation is stated at an ABSTRACT tick list carrying the "
            "guard's own outcome as a hypothesis — satisfiable, since nothing "
            "forces an abstract tick list to be whole-numbered — rather than at "
            "a literal the kernel cannot evaluate. If it verified => "
            "SPEC-TOO-WEAK (the display fact admitted to be value-dependent, "
            "which is the defect itself). (Sibling: "
            "partial-domain-empty-tick-set, the rival correct only where the "
            "tests happen to look.)",
        "witness":
            "example (cfg : RendererConfig) (own : List String) (ticks : List Float)\n"
            "    (hg : (ticks.all (fun t => t == t.floor)) = false)\n"
            "    (h : ∀ (o s : Bool),\n"
            "      renderTicks cfg true true ticks = renderTicks cfg o s ticks →\n"
            "        sharedTerm cfg o s ticks ≠ \"\") :\n"
            "    ¬ (∀ labels, (legendLabels true cfg own ticks).run = DivM.res labels →\n"
            "        ∃ (o s : Bool), labels = renderTicks cfg o s ticks ∧\n"
            "          sharedTerm cfg o s ticks = \"\") := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, hs⟩ := hall _ rfl\n"
            "  rw [hg, Bool.not_false] at ho\n"
            "  exact h o s ho hs\n",
    },

    # ---- (R1) the wrong ARGUMENT reaches the renderer ----
    {
        "id": "weak-permuted-tick-argument",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct configuration, but the tick list is reversed on the way in.
        "module": _swap(_BASE, _LL,
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks.reverse\n"
                        "      return labels\n"),
        "refinement":
            "configuring the renderer correctly but handing it the tick "
            "positions in the opposite order pairs every label with the wrong "
            "tick. The count is right and each label individually denotes some "
            "real tick's position, so a purely count-based or purely "
            "magnitude-based check would pass; but the legend then labels each "
            "position with another position's number, and the failing examples "
            "compare per-entry label text against the data they were built from, "
            "so they stay RED. It would NOT resolve.",
        "rationale":
            "REJECT from R1 (labels = renderTicks cfg offsetMode scaleMode "
            "ticks) via the ARGUMENT rather than the configuration: the "
            "positional correspondence between labels and ticks. The renderer "
            "derives its shared display decisions from the WHOLE list it is "
            "handed, so a rendering of the reversed list is not a rendering of "
            "the list under ANY mode setting; the refutation states exactly that "
            "and is otherwise value-free. Refuted at an ascending two-tick input "
            "where the permutation is observable. If it verified => "
            "SPEC-TOO-WEAK (the per-index pairing unpinned, so the clause would "
            "only constrain the label MULTISET). Abuses the ORDER of the `ticks` "
            "binder — a facet no other first-method rival touches.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool),\n"
            "      renderTicks cfg false false ([(1.0:Float), (2.0:Float)].reverse) ≠\n"
            "        renderTicks cfg o s [(1.0:Float), (2.0:Float)]) :\n"
            "    ¬ (∀ labels, (legendLabels true cfg [\"a\", \"b\"]\n"
            "          [(1.0:Float), (2.0:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool), labels = renderTicks cfg o s [(1.0:Float), (2.0:Float)] ∧\n"
            "          sharedTerm cfg o s [(1.0:Float), (2.0:Float)] = \"\") := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, _⟩ := hall _ rfl\n"
            "  exact h o s ho\n",
    },

    # ---- (L1) the count clause of the first method, in isolation ----
    {
        "id": "weak-drops-an-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LL,
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let chosen :| chosen = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      let labels := chosen.tail\n"
                        "      return labels\n"),
        "refinement":
            "keeping the correct renderer configuration but discarding the "
            "leading entry yields a legend with fewer entries than there are "
            "tick positions. The surviving entries are all rendered faithfully, "
            "so every per-entry text check passes; the legend simply omits an "
            "entry. The failing examples first assert the legend has entries and "
            "then check every one, and the surrounding legend-content assertions "
            "count entries against the data levels, so an entry-short legend "
            "stays RED. It would NOT resolve.",
        "rationale":
            "REJECT from L1 (labels.length = ticks.length) ALONE — the "
            "existential (R1 ∧ N1) is what this rival leaves nearly intact, so "
            "the case isolates the count clause. Fully TRANSPARENT: the length "
            "axiom pins the renderer's output length to the tick count, so "
            "dropping one entry is refuted by rewriting with that axiom and "
            "closing arithmetically — the witness assumes nothing beyond an "
            "arbitrary renderer handle. If it verified => SPEC-TOO-WEAK (an "
            "entry-short legend admitted). Abuses the LENGTH of the `ticks` "
            "binder at a two-element input. (Sibling: partial-drop-last, whose "
            "argument is the same short legend; the sibling notes its loop bound "
            "leaves the empty input vacuously fine, and the same holds here, so "
            "the witness is stated at a non-empty input.)",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (hd : renders cfg false false [(7.0:Float), (9.0:Float)]) :\n"
            "    ¬ (∀ labels, (legendLabels true cfg [\"a\", \"b\"]\n"
            "          [(7.0:Float), (9.0:Float)]).run = DivM.res labels →\n"
            "        labels.length = ([(7.0:Float), (9.0:Float)]).length) := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  have hlen := renderTicks_length cfg false false [(7.0:Float), (9.0:Float)] hd\n"
            "  have h2 := hall _ rfl\n"
            "  simp only [List.length_tail, hlen] at h2\n"
            "  simp at h2\n",
    },
    {
        "id": "weak-duplicates-entries",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LL,
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let chosen :| chosen = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      let labels := chosen ++ chosen\n"
                        "      return labels\n"),
        "refinement":
            "emitting each entry twice gives a legend with MORE entries than "
            "there are tick positions. Unlike the entry-short rival this one "
            "errs upward, so a spec pinning only a lower bound on the count "
            "would admit it; the rendered legend would list every level twice. "
            "The failing examples' legend-content assertions read the entries "
            "against the data levels, so a doubled legend stays RED. It would "
            "NOT resolve.",
        "rationale":
            "REJECT from L1 in the OPPOSITE direction to weak-drops-an-entry: "
            "too many entries rather than too few. Shipped as a separate rival "
            "because a count clause could be satisfied one-sidedly, and a spec "
            "that only forbade dropping would admit this; together the two "
            "rivals show L1 is a genuine EQUALITY. Transparent via the length "
            "axiom. Refuted at a ONE-element input — the shortest non-empty one, "
            "so the count facet is probed at the boundary as well as in the "
            "middle. If it verified => SPEC-TOO-WEAK.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (hd : renders cfg false false [(7.0:Float)]) :\n"
            "    ¬ (∀ labels, (legendLabels true cfg [\"a\"] [(7.0:Float)]).run = DivM.res labels →\n"
            "        labels.length = ([(7.0:Float)]).length) := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  have hlen := renderTicks_length cfg false false [(7.0:Float)] hd\n"
            "  have h2 := hall _ rfl\n"
            "  simp only [List.length_append, hlen] at h2\n"
            "  simp at h2\n",
    },

    # ---- (R1) the renderer is called on a PADDED list ----
    {
        "id": "weak-labels-pads-the-tick-argument",
        "kind": "uniqueness",
        "expect": "reject",
        # Renders a tick list padded with a sentinel position and returns the
        # prefix. Nothing is hoisted and every label is a plain decimal, so a
        # display-only clause cannot see this; only the call clause can.
        "module": _swap(_BASE, _LL,
                        "      let padded : List Float := ticks ++ [(9007199254740992.0:Float)]\n"
                        "      let raw :| raw = renderTicks cfg false false padded\n"
                        "      return raw.take ticks.length\n"),
        "refinement":
            "the renderer decides how many digits to print, and what to hoist, "
            "by looking at the WHOLE set of positions it is handed relative to "
            "its range, so handing it an extra position it will not display "
            "changes the labels of the ones it will. Padding with a sentinel and "
            "dropping the sentinel's label keeps the abbreviation off — nothing "
            "is hoisted, so the examples under repair still pass — while the "
            "regression suite's own expected legend text for ordinary data "
            "changes: measured in the instance container (matplotlib 3.7.2, both "
            "switches off), the levels 0.20/0.22/0.24/0.26/0.28 render as "
            "['0.20','0.22','0.24','0.26','0.28'] alone and as ['0','0','0','0','0'] "
            "once the sentinel position 9007199254740992 is appended and its label "
            "dropped, so the check goes RED. It would NOT resolve, and the audit "
            "measured exactly that (FAIL_TO_PASS 2/2 pass, one PASS_TO_PASS "
            "regression). The sentinel has to be far from the levels for the "
            "divergence to appear: appending 0.0 to those same levels leaves the "
            "prefix byte-identical (measured), which is why the obligation is "
            "stated over the ARGUMENT rather than over any label text.",
        "rationale":
            "REJECT from R1 (labels = renderTicks cfg offsetMode scaleMode "
            "ticks) — the conjunct that pins the renderer's ARGUMENT and its "
            "result's pass-through, which nothing else in this battery pins on "
            "this obligation. This is the rival that motivated R1: it satisfies "
            "L1, P1 AND N1 in full (both switches are off, so nothing is hoisted "
            "at all), so a spec pinning only the display fact admits it. Refuted "
            "by a witness that reads the clause directly rather than through any "
            "label text. If it verified => SPEC-TOO-WEAK, and demonstrably so: "
            "the materialized counterpart of this exact shape does not resolve.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool),\n"
            "      (renderTicks cfg false false ([(0.2:Float), (0.22:Float)] ++ [(9007199254740992.0:Float)])).take\n"
            "          ([(0.2:Float), (0.22:Float)]).length ≠\n"
            "        renderTicks cfg o s [(0.2:Float), (0.22:Float)]) :\n"
            "    ¬ (∀ labels, (legendLabels true cfg [\"a\", \"b\"]\n"
            "          [(0.2:Float), (0.22:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool), labels = renderTicks cfg o s [(0.2:Float), (0.22:Float)] ∧\n"
            "          sharedTerm cfg o s [(0.2:Float), (0.22:Float)] = \"\") := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, _⟩ := hall _ rfl\n"
            "  exact h o s ho\n",
    },

    # ---- (R1) the labels are read off ANOTHER renderer than the installed one ----
    {
        "id": "weak-labels-uses-another-renderer-handle",
        "kind": "uniqueness",
        "expect": "reject",
        # Right switches, right tick list — but a renderer OTHER than the one
        # installed on the axis. The only handle a rival can name without
        # constructing one is the witness of `sharedTerm_hoists`.
        "module": _swap(_BASE, _LL,
                        "      let other : RendererConfig := sharedTerm_hoists.choose\n"
                        "      let labels :| labels = renderTicks other false false ticks\n"
                        "      return labels\n"),
        "refinement":
            "building the labels from a renderer of its own rather than from the "
            "one already installed on the axis discards every presentation "
            "setting the caller configured — the unit, the format string, the "
            "callable, the date rules — and prints plain decimals instead. "
            "Nothing is hoisted, and there is one label per tick, so the "
            "threshold assertions of the failing examples can pass; every "
            "regression check that pins a CONFIGURED legend's text goes RED. It "
            "would NOT resolve.",
        "rationale":
            "REJECT from R1 through the renderer HANDLE — the binder no other "
            "rival moves, and one the model acquired precisely so that 'which "
            "renderer produced these labels' is part of the observable. The "
            "clause pins the labels to `renderTicks cfg …`, the handle the "
            "method was GIVEN, so rendering with any other handle is refutable "
            "however correct the switches are. Conditioned on one hypothesis "
            "separating the two handles' outputs (they are distinct opaque "
            "applications, so this is satisfiable and the probe cannot derive "
            "False from it). If it verified => SPEC-TOO-WEAK: the spec would "
            "permit reading a legend off a renderer nobody installed, which is "
            "the shape of a second, unreported defect rather than of the one "
            "under repair.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool),\n"
            "      renderTicks sharedTerm_hoists.choose false false [(0.25:Float)] ≠\n"
            "        renderTicks cfg o s [(0.25:Float)]) :\n"
            "    ¬ (∀ labels, (legendLabels true cfg [\"a\"] [(0.25:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool), labels = renderTicks cfg o s [(0.25:Float)] ∧\n"
            "          sharedTerm cfg o s [(0.25:Float)] = \"\") := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, _⟩ := hall _ rfl\n"
            "  exact h o s ho\n",
    },

    # ---- (P1) the first method's pinned no-modes path ----
    {
        "id": "weak-labels-no-modes-path-renumbered",
        "kind": "uniqueness",
        "expect": "reject",
        # The pinned path is post-processed instead of shown unchanged.
        "module": _swap(_BASE, _LL_OWN,
                        "      return ownLabels.reverse\n"),
        "refinement":
            "the path where the configured renderer has no shared-term modes at "
            "all is one the change is supposed to leave alone. Reordering its "
            "labels relabels every legend entry with another position's text "
            "while changing no label's spelling and no entry count, so any check "
            "on the label SET or the entry count still passes; the regression "
            "suite pins that path's per-entry text against its ticks, so those "
            "checks break while the two examples under repair pass — the "
            "instance would NOT resolve.",
        "rationale":
            "REJECT from P1 (modesAvailable = false → labels = ownLabels) — the "
            "clause that PINS the first obligation's untouched path, which no "
            "other rival attacks. On that path there is nothing to configure, so "
            "the only admissible observable is the configured renderer's own "
            "labels VERBATIM; a rival that post-processes them is caught only "
            "because P1 is an equality rather than a permission to emit "
            "something of the right length. Refuted with the guard held at its "
            "NO-MODES value — the only first-method rival to probe that side of "
            "the branch — conditioned on one hypothesis separating the reversed "
            "list from the original. If it verified => SPEC-TOO-WEAK (the "
            "untouched path left free to be rewritten).",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ([\"a\", \"b\"] : List String).reverse ≠ ([\"a\", \"b\"] : List String)) :\n"
            "    ¬ (∀ labels, (legendLabels false cfg [\"a\", \"b\"]\n"
            "          [(1.0:Float), (2.0:Float)]).run = DivM.res labels →\n"
            "        labels = ([\"a\", \"b\"] : List String)) := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  exact h (hall _ rfl)\n",
    },
    {
        "id": "weak-labels-guard-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the guard: the installed renderer's own labels are served on
        # BOTH arms, so the numeric path is never configured at all.
        "module": _swap(_BASE, _LL,
                        "      return ownLabels\n"),
        "refinement":
            "serving the configured renderer's own labels on BOTH paths ignores "
            "the mode-availability guard entirely. The pinned path stays "
            "correct, so half the behavior looks right; on the ordinary numeric "
            "path the renderer is left in its pre-change configuration, so it "
            "may hoist a shared term out of the labels and report it separately, "
            "and the read-back-and-compare assertions of the failing examples "
            "stay RED. It would NOT resolve.",
        "rationale":
            "REJECT from R1 ∧ N1, attacking the `modesAvailable` BINDER itself "
            "rather than a configuration: the rival is correct on the guard's "
            "no-modes value and wrong on the other, so it is refutable only by a "
            "witness that MOVES the guard — which is why this case exists "
            "alongside weak-labels-no-modes-path-renumbered (that one holds the "
            "guard at its no-modes value; this one at its modes-available "
            "value). This is also the rival that would verify if the existential "
            "were guarded by nothing, i.e. if the repair had relaxed it into a "
            "disjunction with P1 instead of a case split. Conditioned on one "
            "hypothesis separating the supplied labels from every rendering of "
            "these ticks. If it verified => SPEC-TOO-WEAK (the guard could be "
            "ignored).",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool), ([\"a\", \"b\"] : List String) ≠\n"
            "      renderTicks cfg o s [(3.0:Float), (4.0:Float)]) :\n"
            "    ¬ (∀ labels, (legendLabels true cfg [\"a\", \"b\"]\n"
            "          [(3.0:Float), (4.0:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool), labels = renderTicks cfg o s [(3.0:Float), (4.0:Float)] ∧\n"
            "          sharedTerm cfg o s [(3.0:Float), (4.0:Float)] = \"\") := by\n"
            "  simp only [legendLabels]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, _⟩ := hall _ rfl\n"
            "  exact h o s ho\n",
    },

    # =====================================================================
    # The SECOND obligation. It has its own clauses (L2, G2, R2, N2) and its own
    # extra input binder (the renderer selector), none of which the first
    # obligation's rivals touch — a rival mishandling only the second method
    # would otherwise go unnoticed entirely.
    # =====================================================================

    # ---- (N2) the display fact on the selected linear path ----
    {
        "id": "weak-entries-modes-enabled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LE_LINEAR,
                        "      let offsetMode : Bool := true\n"
                        "      let scaleMode : Bool := true\n"
                        "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      return labels\n"),
        "refinement":
            "the same pre-change configuration, but on the SECOND legend-building "
            "entry point — the one the other plotting interface uses. Changing "
            "only one of the two entry points leaves the other producing "
            "abbreviated labels, and the two failing examples exercise the two "
            "interfaces separately, so the one covering this path stays RED. It "
            "would NOT resolve.",
        "rationale":
            "REJECT from N2 — the SECOND obligation's display fact, which no "
            "other rival attacks. Also the coverage argument for the two-site "
            "nature of this surface: the first obligation's rivals leave this "
            "method entirely gold, so without this case a one-site change would "
            "verify. Conditioned on one hypothesis about the abbreviating "
            "configuration, refuted with the selector held at the LINEAR value "
            "(the arm the clause guards) at a single-tick input. If it verified "
            "=> SPEC-TOO-WEAK. Abuses both the `isLog` selector (false) and "
            "`ticks`.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool),\n"
            "      renderTicks cfg true true [(42.0:Float)] = renderTicks cfg o s [(42.0:Float)] →\n"
            "        sharedTerm cfg o s [(42.0:Float)] ≠ \"\") :\n"
            "    ¬ (∀ labels, (legendEntries false cfg [(42.0:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool), labels = renderTicks cfg o s [(42.0:Float)] ∧\n"
            "          sharedTerm cfg o s [(42.0:Float)] = \"\") := by\n"
            "  simp only [legendEntries]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, hs⟩ := hall _ rfl\n"
            "  exact h o s ho hs\n",
    },

    # ---- (R2) the second method's renderer-argument clause ----
    {
        "id": "weak-entries-pads-the-tick-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LE_LINEAR,
                        "      let padded : List Float := ticks ++ [(9007199254740992.0:Float)]\n"
                        "      let raw :| raw = renderTicks cfg false false padded\n"
                        "      return raw.take ticks.length\n"),
        "refinement":
            "the same padding shape on the SECOND entry point: the renderer is "
            "handed an extra position it will not display, which changes the "
            "digits it prints for the ones it will, and the sentinel's label is "
            "dropped. Nothing is hoisted, so the threshold assertions pass; the "
            "regression checks that pin this interface's legend text against its "
            "data levels go RED — measured, the same way as on the first site: "
            "0.20/0.22/0.24/0.26/0.28 render as ['0.20','0.22','0.24','0.26','0.28'] "
            "alone and as ['0','0','0','0','0'] once 9007199254740992 is appended. "
            "It would NOT resolve.",
        "rationale":
            "REJECT from R2 — the second obligation's CALL conjunct, which no "
            "other rival on this method attacks (weak-entries-modes-enabled "
            "attacks N2, the count rivals attack L2, and the two pinned-path "
            "rivals attack G2). Without it the second obligation would pin only "
            "'nothing was hoisted' and the right entry count, and this rival "
            "satisfies both. Refuted at the regression suite's own levels "
            "(0.20/0.24) with the selector held at its LINEAR value. If it "
            "verified => SPEC-TOO-WEAK on the second site specifically.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool),\n"
            "      (renderTicks cfg false false ([(0.2:Float), (0.24:Float)] ++ [(9007199254740992.0:Float)])).take\n"
            "          ([(0.2:Float), (0.24:Float)]).length ≠\n"
            "        renderTicks cfg o s [(0.2:Float), (0.24:Float)]) :\n"
            "    ¬ (∀ labels, (legendEntries false cfg [(0.2:Float), (0.24:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool), labels = renderTicks cfg o s [(0.2:Float), (0.24:Float)] ∧\n"
            "          sharedTerm cfg o s [(0.2:Float), (0.24:Float)] = \"\") := by\n"
            "  simp only [legendEntries]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, _⟩ := hall _ rfl\n"
            "  exact h o s ho\n",
    },

    # ---- (G2) the pinned alternative-renderer path ----
    {
        "id": "weak-alt-path-substitutes-renderer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LE_ALT,
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      return labels\n"),
        "refinement":
            "routing the alternative-spacing path through the plain-decimal "
            "renderer changes a path the change is supposed to leave alone. "
            "Labels on that path are not plain decimals, so substituting the "
            "decimal renderer silently rewrites every such legend's text. The "
            "regression suite covers that path's existing label text, so those "
            "checks break even though the two examples under repair pass — a "
            "faithful counterpart resolves the reported defect while breaking "
            "previously-passing behavior, so the instance would NOT resolve.",
        "rationale":
            "REJECT from G2 (isLog = true → labels = renderLog cfg ticks) — the "
            "clause that PINS the untouched path, attacked by no other rival "
            "except through its argument. The clause is an equality between two "
            "opaque terms, so the refutation CONDITIONS on the carrier with a "
            "single hypothesis separating the two renderers' outputs at the "
            "witness input (they are distinct opaque functions, so this is "
            "satisfiable — the probe cannot derive False from it). Refuted with "
            "the selector held at the ALTERNATIVE value. If it verified => "
            "SPEC-TOO-WEAK (the untouched path left free to be rewritten).",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : renderTicks cfg false false [(5.0:Float)] ≠\n"
            "      renderLog cfg [(5.0:Float)]) :\n"
            "    ¬ (∀ labels, (legendEntries true cfg [(5.0:Float)]).run = DivM.res labels →\n"
            "        labels = renderLog cfg [(5.0:Float)]) := by\n"
            "  simp only [legendEntries]\n"
            "  intro hall\n"
            "  exact h (hall _ rfl)\n",
    },

    # ---- (R2 ∧ N2) the selector is ignored ----
    {
        "id": "weak-selector-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LE_LINEAR,
                        "      let labels :| labels = renderLog cfg ticks\n"
                        "      return labels\n"),
        "refinement":
            "using the alternative-spacing renderer on BOTH paths ignores the "
            "selector entirely. The pinned path stays correct, so half the "
            "behavior looks right; the ordinary path now emits that renderer's "
            "labels, which are not the plain decimals this interface's legend "
            "shows, so the read-back-and-compare assertions of the failing "
            "examples stay RED. It would NOT resolve.",
        "rationale":
            "REJECT from R2, attacking the `isLog` BINDER itself rather than a "
            "configuration: the rival is correct on the selector's alternative "
            "value and wrong on the other, so it is refutable only by a witness "
            "that MOVES the selector — which is exactly why this case exists "
            "alongside weak-alt-path-substitutes-renderer (that one holds the "
            "selector at the alternative value; this one at the linear value). "
            "Conditioned on one hypothesis separating the alternative renderer's "
            "output from every rendering of these ticks by the numeric one. If "
            "it verified => SPEC-TOO-WEAK (the selector could be ignored). "
            "Refuted at a two-tick input distinct from the other second-method "
            "witnesses'.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : ∀ (o s : Bool), renderLog cfg [(3.0:Float), (4.0:Float)] ≠\n"
            "      renderTicks cfg o s [(3.0:Float), (4.0:Float)]) :\n"
            "    ¬ (∀ labels, (legendEntries false cfg [(3.0:Float), (4.0:Float)]).run = DivM.res labels →\n"
            "        ∃ (o s : Bool), labels = renderTicks cfg o s [(3.0:Float), (4.0:Float)] ∧\n"
            "          sharedTerm cfg o s [(3.0:Float), (4.0:Float)] = \"\") := by\n"
            "  simp only [legendEntries]\n"
            "  intro hall\n"
            "  obtain ⟨o, s, ho, _⟩ := hall _ rfl\n"
            "  exact h o s ho\n",
    },

    # ---- (G2) the pinned path, attacked through its ARGUMENT ----
    {
        "id": "weak-alt-path-permutes-argument",
        "kind": "uniqueness",
        "expect": "reject",
        # The right renderer on the pinned path, handed the ticks reversed.
        "module": _swap(_BASE, _LE_ALT,
                        "      let labels :| labels = renderLog cfg ticks.reverse\n"
                        "      return labels\n"),
        "refinement":
            "the alternative-spacing path keeps its own renderer but receives "
            "the tick positions in the opposite order, so every entry on that "
            "path is labelled with another position's text. Substituting no "
            "renderer and changing no label's spelling, this passes any check "
            "on the label SET or the entry count and still mislabels a path the "
            "change is supposed to leave alone; the regression suite pins that "
            "path's per-entry text against its ticks, so those checks break "
            "while the two examples under repair pass — the instance would NOT "
            "resolve.",
        "rationale":
            "REJECT from G2 (isLog = true → labels = renderLog cfg ticks) via the "
            "ARGUMENT rather than the renderer, which is the facet "
            "weak-alt-path-substitutes-renderer leaves open: that rival calls a "
            "DIFFERENT renderer, so a spec pinning only 'some call to the right "
            "renderer' would still catch it, while this one calls the RIGHT "
            "renderer on the WRONG list and is caught only because G2 pins the "
            "output to that renderer's value AT THESE TICKS. Verified "
            "non-redundant by build: the substitute-renderer rival's witness "
            "does NOT discriminate this rival. Conditioned on one hypothesis "
            "separating the renderer's output on the permuted list from its "
            "output on the original — they are distinct arguments to an opaque "
            "function, so this is satisfiable and the probe cannot derive False "
            "from it. If it verified => SPEC-TOO-WEAK (G2 would pin only the "
            "renderer's identity, not its argument). Abuses the ORDER of `ticks` "
            "with the selector held at its ALTERNATIVE value — the one "
            "combination no other case reaches.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (h : renderLog cfg ([(1.0:Float), (2.0:Float)]).reverse ≠\n"
            "      renderLog cfg [(1.0:Float), (2.0:Float)]) :\n"
            "    ¬ (∀ labels, (legendEntries true cfg [(1.0:Float), (2.0:Float)]).run = DivM.res labels →\n"
            "        labels = renderLog cfg [(1.0:Float), (2.0:Float)]) := by\n"
            "  simp only [legendEntries]\n"
            "  intro hall\n"
            "  exact h (hall _ rfl)\n",
    },

    # ---- (L2) the second method's count clause ----
    {
        "id": "weak-entries-drops-an-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LE_LINEAR,
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let chosen :| chosen = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      let labels := chosen.tail\n"
                        "      return labels\n"),
        "refinement":
            "the second entry point discarding its leading entry yields a "
            "legend with fewer entries than there are tick positions on the "
            "ordinary path. The surviving entries are all rendered faithfully, "
            "so every per-entry text check passes and only the size is wrong; "
            "the assertions that read this interface's legend entries against "
            "its data levels stay RED. It would NOT resolve.",
        "rationale":
            "REJECT from L2 in the DROP direction, the half "
            "weak-entries-duplicates leaves untested: that rival errs UPWARD, "
            "so a spec pinning only an upper bound on the count would admit "
            "this one, and together the two show L2 is a genuine EQUALITY on "
            "the second obligation exactly as weak-drops-an-entry and "
            "weak-duplicates-entries do on the first. Verified non-redundant by "
            "build: neither the second method's duplicate witness nor the first "
            "method's drop witness discriminates this rival. Transparent via "
            "the length axiom. Refuted at a THREE-element input, the only "
            "witness in the battery at that length. If it verified => "
            "SPEC-TOO-WEAK (an entry-short legend admitted on the second site).",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (hd : renders cfg false false\n"
            "      [(2.0:Float), (4.0:Float), (6.0:Float)]) :\n"
            "    ¬ (∀ labels, (legendEntries false cfg\n"
            "          [(2.0:Float), (4.0:Float), (6.0:Float)]).run = DivM.res labels →\n"
            "        labels.length = ([(2.0:Float), (4.0:Float), (6.0:Float)]).length) := by\n"
            "  simp only [legendEntries]\n"
            "  intro hall\n"
            "  have hlen := renderTicks_length cfg false false\n"
            "    [(2.0:Float), (4.0:Float), (6.0:Float)] hd\n"
            "  have h2 := hall _ rfl\n"
            "  simp only [List.length_tail, hlen] at h2\n"
            "  simp at h2\n",
    },
    {
        "id": "weak-entries-duplicates",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LE_LINEAR,
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let chosen :| chosen = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      let labels := chosen ++ chosen\n"
                        "      return labels\n"),
        "refinement":
            "the second entry point emitting each label twice produces a legend "
            "listing every level twice on the ordinary path. The entries are all "
            "rendered faithfully, so a display-only check passes; the legend is "
            "simply the wrong size, and the assertions that read the interface's "
            "legend entries against its data levels stay RED. It would NOT "
            "resolve.",
        "rationale":
            "REJECT from L2 (labels.length = ticks.length) on the SECOND "
            "obligation — its count clause, which no other rival attacks in the "
            "upward direction (the first obligation's count rivals leave this "
            "method gold). Transparent via the length axiom. With this case "
            "every independent top-level clause of both obligations (L1, R1, N1, "
            "P1, L2, G2, R2, N2) has a rival built against it. If it verified => "
            "SPEC-TOO-WEAK.",
        "witness":
            "example (cfg : RendererConfig)\n"
            "    (hd : renders cfg false false [(7.0:Float)]) :\n"
            "    ¬ (∀ labels, (legendEntries false cfg [(7.0:Float)]).run = DivM.res labels →\n"
            "        labels.length = ([(7.0:Float)]).length) := by\n"
            "  simp only [legendEntries]\n"
            "  intro hall\n"
            "  have hlen := renderTicks_length cfg false false [(7.0:Float)] hd\n"
            "  have h2 := hall _ rfl\n"
            "  simp only [List.length_append, hlen] at h2\n"
            "  simp at h2\n",
    },

    # =====================================================================
    # DIVERGENCE. The sibling's `nonterminating-build` ports HERE, and it is a
    # reject case like any other rather than a class the semantics dispose of in
    # prose. Under `loom.semantics.termination "total"` the verifier discharges
    # a descent obligation, so a spliced spinning loop is genuinely refused; but
    # "the rival does not verify" is exactly the outcome this gate does not
    # accept on its own, so the case carries a witness that discriminates.
    # =====================================================================
    {
        "id": "weak-labels-spins-before-rendering",
        "kind": "uniqueness",
        "expect": "reject",
        # A spinning loop on the numeric arm, AHEAD of an otherwise gold body.
        # The measure is present and well-typed (a `Nat`, as the clause requires)
        # and simply never descends, which is the honest form of this rival: the
        # elaborator refuses a MISSING `decreasing` clause outright, so omitting
        # it would test the parser rather than the contract.
        "module": _swap(_BASE, _LL,
                        "      let mut spin : Nat := 1\n"
                        "      while spin > 0\n"
                        "        invariant spin = 1\n"
                        "        done_with spin = 0\n"
                        "        decreasing spin\n"
                        "      do\n"
                        "        spin := spin\n"
                        "      let offsetMode : Bool := false\n"
                        "      let scaleMode : Bool := false\n"
                        "      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks\n"
                        "      return labels\n"),
        "refinement":
            "a build that never finishes on the ordinary numeric path. Every "
            "value clause is satisfied by the labels it would eventually hand "
            "back — the render call underneath it is gold's — so nothing about "
            "the legend's CONTENT is wrong; the legend is simply never produced. "
            "The failing examples never reach an assertion at all, so they do "
            "not go green. It would NOT resolve.",
        "rationale":
            "REJECT from the TERMINATION obligation, which is the one obligation "
            "in this bundle no value clause can stand in for: L1 ∧ R1 ∧ N1 are "
            "all satisfied on the nose here (the underlying call is byte-for-byte "
            "gold's), and what fails is that the run has no result. This is the "
            "case that shows the obligation is load-bearing rather than implied "
            "by the semantics setting: without it, every `ensures` above could be "
            "discharged by a body that produces no legend. Refuted by a witness "
            "that PROVES the rival's run diverges (`Loop.forIn.loop`'s own "
            "fixpoint induction, at the flat order whose bottom is the diverging "
            "value) and therefore satisfies no result at all, where gold's run "
            "returns one. If it verified => SPEC-TOO-WEAK in its strongest form "
            "(a non-terminating impl admitted, making every other clause "
            "vacuous). (Sibling: nonterminating-build, whose rejection source "
            "there is the explicit termination requirement its loop carries no "
            "measure for.)",
        # Stated as the NEGATION of "some result exists with the right count", so
        # both halves of the discrimination are about the same proposition: the
        # rival has no result to have a count, gold has one and its count is the
        # length fact. The tick list and label list are left ABSTRACT and the
        # arm's own domain fact is assumed, because divergence is a property of
        # the control flow rather than of any particular input — the claim is
        # therefore stronger than one at a literal, and it is the frozen method's
        # own run that it is about.
        "witness":
            "example (cfg : RendererConfig) (own : List String) (ticks : List Float)\n"
            "    (hlen : own.length = ticks.length)\n"
            "    (hren : renders cfg false false ticks) :\n"
            "    ¬ (∃ labels, (legendLabels true cfg own ticks).run = DivM.res labels ∧\n"
            "        labels.length = ticks.length) := by\n"
            "  have spin :\n"
            "      ∀ (f : Unit → Nat → DivM (ForInStep Nat)),\n"
            "        (∀ b, 0 < b → f () b = pure (ForInStep.yield b)) →\n"
            "        Loop.forIn.loop f 1 = DivM.div := by\n"
            "    intro f hf\n"
            "    have h := Loop.forIn.loop.fixpoint_induct f\n"
            "      (motive := fun loop => ∀ b, 0 < b → loop b = DivM.div)\n"
            "      (Lean.Order.admissible_pi_apply\n"
            "        (fun (b : Nat) (x : DivM Nat) => 0 < b → x = DivM.div)\n"
            "        (fun _ => Lean.Order.admissible_flatOrder _ (fun _ => rfl))) ?_\n"
            "    · exact h 1 Nat.one_pos\n"
            "    · intro loop hloop b hb\n"
            "      simp [hf b hb, bind, hloop b hb]\n"
            "  rintro ⟨labels, hrun, hl2⟩\n"
            "  simp only [legendLabels, if_true, forIn, MonadNonDet.rep, NonDetT.repeat,\n"
            "    bind, NonDetT.bind, NonDetT.run, Loop.forIn] at hrun\n"
            "  rw [spin _ (by intro b hb; simp [invariantGadget, onDoneGadget,\n"
            "    decreasingGadget, NonDetT.bind, NonDetT.run, hb])] at hrun\n"
            "  simp at hrun\n",
    },
]


# Machine-checked at load, not asserted in prose: every case's variant contains
# both frozen `prove_correct` bodies verbatim, EXCEPT for the single whitelisted
# reproving case, which must still carry the other obligation's frozen body and
# must carry exactly the reproved script this file declares. This is what keeps a
# positive from passing by weakening the script that discharges the obligation it
# claims to test — the exemption cannot be widened silently, because a case not
# in `_REPROVES` is still held to both bodies and the exempt case's replacement
# script is pinned by text.
for _c in SPEC_TESTS:
    _exempt = _REPROVES.get(_c["id"])
    for _p in _FROZEN_PROOFS:
        if _p == _exempt:
            if _c["module"].count(_p) != 0:
                raise AssertionError(
                    f"case {_c['id']}: declares a reproof but keeps the frozen body")
            if _c["module"].count(_LE_PROOF_EMPTY) != 1:
                raise AssertionError(
                    f"case {_c['id']}: reproved script is not the declared one")
            continue
        if _c["module"].count(_p) != 1:
            raise AssertionError(
                f"case {_c['id']}: frozen proof body not preserved verbatim")

# The reproving case may not smuggle in an assumption, and the mechanical
# `variant_scope` check the gate runs is not the only place that should say so.
for _c in SPEC_TESTS:
    if _c["id"] not in _REPROVES:
        continue
    for _tok in ("sorry", "admit", "native_decide", "axiom ", "opaque "):
        if _c["module"].count(_tok) > _BASE.count(_tok):
            raise AssertionError(f"case {_c['id']}: introduces {_tok!r}")


# Every sibling case ID this file cites — in the accounting table below and in
# the `(Sibling: ...)` note of an individual rationale — must be a case the
# sibling manifest actually declares. An accounting table is the one part of a
# battery that no build can falsify, so a cited ID that does not exist reads as a
# ported argument while attesting to nothing; checked here rather than trusted.
_SIBLING_MANIFEST = (Path(__file__).parent.parent / "nagini" / "properties.py")
if _SIBLING_MANIFEST.exists():
    import re as _re
    _SIBLING_CASES = set(_re.findall(r'"id":\s*"([^"]+)"',
                                     _SIBLING_MANIFEST.read_text()))
    _cited = set(_re.findall(r"\(Sibling:\s*\n?\s*([a-z0-9-]+)",
                             "".join(str(_c.get("rationale", ""))
                                     for _c in SPEC_TESTS)))
    # ...and the left column of the accounting table, which lives in `#`
    # comments, so it is read back out of this file's own source.
    _cited |= set(_re.findall(r"^#\s{3}([a-z][a-z0-9-]{4,})\s+->",
                              Path(__file__).read_text(), _re.MULTILINE))
    _bogus = sorted(n for n in _cited if n not in _SIBLING_CASES)
    if _bogus:
        raise AssertionError(
            f"cites sibling case IDs that do not exist: {_bogus}")


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING
# ===========================================================================
# The sibling ships 20 SPEC cases (2 soundness, 1 admissibility, 17 uniqueness —
# the uniqueness lane including 2 frame-mutation rivals, 1 divergence rival and 1
# admissibility vacuity control) plus a 2-case AXIOM lane. This
# port ships 25 (4 soundness, 2 admissibility, 19 uniqueness). It is LARGER than
# the sibling, but not because parity was chased: the sibling's two modeled
# functions are byte-identical single-list-input twins, whereas here each
# obligation carries a renderer selector, a renderer HANDLE, and a pinned path
# with no sibling counterpart — so the modeled surface genuinely has more
# independent facets to attack. BOTH obligations dispatch on a selector and both
# pin the path their selector routes away from the numeric renderer, so each of
# those two axes carries its own branch-flip positive and its own pinned-path
# rival rather than one shared between them.
#
#   sibling case                      -> here
#   ------------------------------------------------------------------------
#   pos-precomputed-sequence          -> pos-inline-mode-constants     PORTED
#   pos-different-loop-guard          -> pos-branch-guard-flip +
#                                        pos-labels-branch-guard-flip  PORTED (x2)
#   admiss-self-call-arrived-state-nondefault-convention
#                                     -> admiss-own-labels-length-input PORTED
#   admiss-self-call-vacuity-control  -> (none)                        VACUOUS
#   left-residual-enabled             -> weak-additive-mode-only       PORTED
#   render-then-disable               -> weak-multiplicative-mode-only PORTED
#   mode-token-swap                   -> weak-both-modes-enabled       PORTED
#   private-route-raw-tick            -> weak-labels-uses-another-renderer-handle
#                                                                      PORTED
#   convention-echo                   -> weak-labels-guard-ignored     PORTED
#   convention-rewrite                -> weak-labels-no-modes-path-renumbered
#                                                                      PORTED
#   other-tick-set                    -> weak-labels-pads-the-tick-argument +
#                                        weak-entries-pads-the-tick-argument
#                                                                      PORTED (x2)
#   rotated-labels                    -> weak-permuted-tick-argument +
#                                        weak-alt-path-permutes-argument
#                                                                      PORTED (x2)
#   interval-rewrite                  -> weak-alt-path-substitutes-renderer
#                                                                      PORTED
#   other-interval                    -> weak-selector-ignored         PORTED
#   interval-from-ticks               -> weak-entries-modes-enabled     PORTED
#   partial-domain-empty-tick-set     -> weak-modes-off-only-for-whole-number-ticks
#                                                                      PORTED
#   partial-drop-last                 -> weak-drops-an-entry +
#                                        weak-entries-drops-an-entry   PORTED (x2)
#   nonterminating-build              -> weak-labels-spins-before-rendering
#                                                                      PORTED
#   frame-append-to-locs              -> (none)                        VACUOUS
#   frame-store-into-locs             -> (none)                        VACUOUS
#   AXIOM_TESTS (x2)                  -> (none)                        DROPPED
#   (no counterpart)                  -> pos-alt-path-empty-literal    NEW
#   (no counterpart)                  -> admiss-render-domain-reaches-the-call NEW
#   (no counterpart)                  -> weak-duplicates-entries       NEW
#   (no counterpart)                  -> weak-entries-duplicates       NEW
#
# The left column is checked against the sibling manifest at load (see
# `_SIBLING_CASES` below), so a case ID that does not exist there is a load
# error rather than a plausible-looking line of prose.
#
# OMITTED, with reasons:
#
# * admiss-self-call-vacuity-control — VACUOUS on this carrier, and the reason is
#   MEASURED rather than argued. The sibling pairs its admissibility positive
#   with an `Assert(False)` control: if the false assert also verified, the
#   probed call site would be infeasible and the positive would prove nothing.
#   The analogous rival here is the frozen numeric arm with
#   `assert (with_name_prefix `vac False)` spliced ahead of the render call, and
#   it IS rejected — built, exit 1, leaving `case «vac_1: False» ... ⊢ False`
#   open with both `require`s in context, which is exactly the control the
#   sibling wants and it confirms neither admissibility positive is vacuous.
#   What makes it unshippable as a CASE is the witness half: the rival's
#   observable behaviour is gold's (an assert is a proof obligation, not a
#   statement that changes the run), so no claim can hold of it and fail of
#   gold. Measured: the affirmative "some result exists whose count is the tick
#   count" elaborates against BOTH this rival and gold (exit 0 each). A reject
#   case here would therefore attest to a discharge failure rather than to the
#   spec, which is precisely the inference the witness rule exists to forbid.
#   The control is recorded here, with its build, instead of being fabricated as
#   a case; the same evidence is cited in both admissibility rationales as the
#   perturbation that makes them load-bearing.
#
# * The domain-admissibility lane is TWO cases where the sibling has ONE, and the
#   extra case is a consequence of the spec: this backend's callee is PARTIAL, so
#   alongside the sibling's count-style precondition there is a second KIND of
#   `require` — the modeled DOMAIN each arm is handed — whose failure mode is its
#   SHAPE rather than its truth. A domain stated at the wrong setting, or on the
#   arm that calls nothing, would reject every impl for want of a hypothesis, so
#   it gets its own positive (`admiss-render-domain-reaches-the-call`). Ticks are
#   `Float`, the same IEEE-754 doubles the renderer receives, so there is no
#   integer-magnitude boundary to probe; the value-dependence that an
#   integer-only carrier would have hidden is attacked from the other side by
#   weak-modes-off-only-for-whole-number-ticks.
#
# * frame-append-to-locs / frame-store-into-locs — VACUOUS. Both are MANDATORY
#   on the sibling because its tick list is held at a fractional heap permission
#   that a rival can illegally write through, making the postcondition true
#   vacuously; the rejection there comes from the permission system, not the
#   contract. This backend is referentially transparent: `ticks`, `cfg`, `isLog`
#   and `modesAvailable` are immutable values, neither method declares a `mut`
#   binder, and there is no heap and no aliasing — there is no read-only input to
#   mutate, so the class has no counterpart and no substitute probe was
#   fabricated.
#
# * AXIOM_TESTS (x2) — DROPPED per the porting map: the axiom lane belongs to
#   G-AX (axiom_check.py validates the length facts, the both-modes-off
#   no-hoisting fact and its non-vacuity against the real renderer, over every
#   configuration it can be installed with), and this gate ignores AXIOM_TESTS
#   regardless.
#
# * nonterminating-build — PORTED, as weak-labels-spins-before-rendering. The
#   frozen impl regions are LOOP-FREE, so this rival brings a loop of its own
#   rather than mutating a body: a ``while spin > 0`` prefix with body
#   ``spin := spin``, ahead of an otherwise byte-identical gold numeric arm. It
#   carries a well-typed ``decreasing spin`` that simply never descends, which is
#   the honest form here — OMITTING the clause is refused earlier by the
#   elaborator itself (``Decreasing annotations are required in total correctness
#   semantics``), so an omission would test the parser rather than the contract,
#   and an ``Int`` measure fails as a TYPE error (``has type ℤ but is expected to
#   have type Option ℕ``) that masks the verdict. Under
#   ``loom.semantics.termination "total"`` with ``open TotalCorrectness`` a
#   postcondition is claimed of ALL runs, so the loop owes a descent obligation;
#   measured, the rival is REJECTED on the measure's own goal
#   (``case «decreasing_1: spin» ... ⊢ False``, both ``require``s in context).
#   That alone would only say the frozen script cannot follow the rival, so the
#   case carries a witness that PROVES divergence — ``Loop.forIn.loop``'s
#   fixpoint induction (``Lean.Order.admissible_pi_apply`` +
#   ``admissible_flatOrder`` at the flat order whose bottom IS the diverging
#   value) shows the loop's own value is that bottom, hence the run has no result
#   for any label list, where gold's run has one. Built both ways: it elaborates
#   against the rival (exit 0) and fails against gold (exit 1), and the
#   affirmative of the same proposition inverts the pair (gold exit 0, rival exit
#   1), so gold's exit code tracks the claim rather than a tactic mismatch.
#
# * No soundness positive is dropped for want of a proof. Three of the four
#   positives keep both frozen tactic bodies verbatim; the fourth
#   (`pos-alt-path-empty-literal`) reproves `legendEntries` only, by the script
#   pinned in `_LE_PROOF_EMPTY`, and adds no lemma, axiom, `sorry` or
#   `native_decide`. All four were rebuilt (exit 0). BOTH admissibility cases keep
#   BOTH frozen bodies byte-identically: each in-region `assert` is discharged by
#   the frozen script unaided, verified by rebuilding (exit 0) and by perturbing
#   the assert to a FALSE or MISPLACED claim, which makes the case fail — so both
#   asserts are load-bearing.
#
# COVERAGE SELF-AUDIT
# -------------------
# Obligations: BOTH `prove_correct legendLabels` and `prove_correct
# legendEntries` are DEFENDED (pos-inline-mode-constants /
# pos-labels-branch-guard-flip / admiss-own-labels-length-input /
# admiss-render-domain-reaches-the-call for the first;
# pos-branch-guard-flip / pos-alt-path-empty-literal for the second) and
# ATTACKED (eleven rivals on the first, eight on the second). Both `require` KINDS
# and both `prove_correct` obligations therefore carry a positive AND a rival,
# and each obligation carries a branch-flip positive over its OWN selector, so
# neither contract is over-fit to the branch ORDER it happens to be written in.
# The second obligation additionally carries the one positive whose reshape the
# frozen script cannot follow, so on that obligation "the contract admits it" is
# tested independently of "the frozen script closes it".
#
# Clauses: every independent top-level clause has at least one rival built
# against it in ISOLATION —
#   L1 <- weak-drops-an-entry, weak-duplicates-entries (both directions)
#   P1 <- weak-labels-no-modes-path-renumbered (right labels, wrong order)
#   R1 <- weak-labels-pads-the-tick-argument (right handle + faithful
#         configuration, WRONG argument — invisible to L1, P1 and N1 alike),
#         weak-labels-uses-another-renderer-handle (right argument + right
#         configuration, WRONG handle), weak-permuted-tick-argument (the
#         argument's ORDER), weak-labels-guard-ignored (also violates N1)
#   N1 <- weak-both-modes-enabled, weak-additive-mode-only,
#         weak-multiplicative-mode-only,
#         weak-modes-off-only-for-whole-number-ticks
#   L2 <- weak-entries-duplicates, weak-entries-drops-an-entry (both directions)
#   G2 <- weak-alt-path-substitutes-renderer (wrong renderer),
#         weak-alt-path-permutes-argument (right renderer, wrong argument)
#   R2 <- weak-entries-pads-the-tick-argument (wrong argument),
#         weak-selector-ignored (wrong renderer on the linear arm)
#   N2 <- weak-entries-modes-enabled
#
# The two pinned-path clauses are attacked SYMMETRICALLY: (P1) by a rival that
# reorders the labels it is required to pass through (right labels, wrong
# positions — a rival that no count check and no label-SET check would catch),
# and (G2) by both a wrong-renderer and a right-renderer-wrong-argument rival. A
# rival that IGNORES the first selector — serving the untouched path's labels on
# BOTH values, so it is right on one side of the guard and wrong on the other —
# is refuted separately (weak-labels-guard-ignored), which is what pins the
# existential as the CONSEQUENT OF A CASE SPLIT rather than a disjunction: had
# the repair admitted "either a no-hoisting rendering or the renderer's own
# labels", that rival would verify.
#
# The two conjuncts INSIDE each existential are attacked separately, which is
# the accounting the shared quantifier makes easy to fake: a rival violating
# only the CALL conjunct (padding, permuting, another handle) satisfies the
# display conjunct completely — both switches are off, so nothing is hoisted —
# and a rival violating only the DISPLAY conjunct (either switch on) calls the
# right renderer on the right list. Neither family's witness discriminates the
# other's rival (measured), so the conjunction is not carried by one clause
# doing all the work.
#
# Binders: `ticks` is moved across TWELVE distinct witness inputs — [5.0],
# [42.0], [7.0] (twice, on the two methods), [0.25], [7.0,9.0], [1.0,2.0]
# (twice), [3.0,4.0] (twice), [0.2,0.22], [0.2,0.24], [12340000.0,12350000.0],
# [100000000.0,100000002.5], [2.0,4.0,6.0] — varying length (1, 2 and 3),
# magnitude (sub-unit through ~1e8), FRACTIONALITY (whole, one-decimal,
# two-decimal and half-integral positions, the facet an integer carrier could
# not express), and order (the ascending pairs whose permutation is
# observable). One witness leaves `ticks` ABSTRACT and conditions on its guard
# instead, which is the only way to reach a rival whose guard the kernel cannot
# evaluate. `isLog` is moved across BOTH values: held false by
# weak-entries-modes-enabled / weak-entries-pads-the-tick-argument /
# weak-selector-ignored / weak-entries-duplicates / weak-entries-drops-an-entry
# and true by weak-alt-path-substitutes-renderer / weak-alt-path-permutes-
# argument, so neither value is a binder every witness pins. `modesAvailable` is
# likewise moved across BOTH values: held TRUE by the nine rivals on the first
# obligation's numeric arm and FALSE by weak-labels-no-modes-path-renumbered, so
# the pinned side of that guard is probed by a rival of its own rather than only
# by a positive. `cfg` is UNIVERSALLY bound in every witness (the handle has no
# constructor, so a claim about all handles is the only claim available — and it
# is stronger than one about a literal), and it is itself the target of
# weak-labels-uses-another-renderer-handle. The two display-mode switches are
# attacked jointly AND each in isolation (weak-additive-mode-only,
# weak-multiplicative-mode-only), so the corpus failure mode where one of two
# independent toggles is never discriminated does not apply here.
#
# Witnesses: all nineteen were built BOTH required ways with
# scripts/lean_verify.sh — each ELABORATES against its rival (exit 0) and FAILS
# against the frozen solution (exit 1). Every witness binds at least the
# renderer handle, so every one is run through the gate's own `False`-derivation
# probe; the probe FAILED in every case, so no witness rests on contradictory
# assumptions. The two shapes the probe has to clear are (i) "every setting that
# reproduces THIS output hoists something", which is satisfiable because
# `sharedTerm_hoists` says some configuration does hoist and no axiom constrains
# `sharedTerm` at any other argument, and (ii) "this concrete list is not any
# rendering of these ticks", which is satisfiable because `renderTicks` is
# opaque and no axiom pins its VALUES at all. The four count witnesses carry a
# third shape, (iii) "this handle renders this tick list with both switches off"
# — the domain fact their length rewrite consumes — satisfiable because `renders`
# is an opaque predicate that `renders_nonvacuous` says is inhabited and no axiom
# refutes at any argument. The divergence witness carries (iii) together with the
# count precondition at an ABSTRACT tick list, and derives no `False` from them
# for the same reason: both are opaque predicates about an unconstructible handle.
#
# The divergence witness is the one whose claim is not about label VALUES at all:
# it says the rival's run has NO result, proved from the loop combinator's own
# fixpoint induction rather than from any axiom about the renderer. That is why it
# discriminates where a value claim could not — the rival's render call is
# byte-for-byte gold's, so every clause ABOUT the labels holds of it.
#
# Discrimination is not merely two exit codes per case. Each witness's gold-side
# failure was additionally shown to TRACK ITS CLAIM: for every reject case the
# AFFIRMATIVE of exactly the proposition the witness negates was built on both
# sides, and it verifies against gold while failing against the rival — the
# reverse of the witness's own pair. So gold's exit code carries information
# about the claim rather than reflecting a tactic mismatch that any claim would
# hit. On the mode rivals gold's log shows the both-modes-OFF
# existential being closed by
# `⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩` while the rival's
# shows the abbreviating configuration's equation left open; on the argument rivals
# gold's log shows the unpadded/unpermuted call. Neither is a stuck reduction.
# Non-redundancy was measured the same way: no near-miss rival is discriminated
# by another rival's witness. No banned token (sorry / admit / native_decide /
# axiom / opaque) appears in any witness, and no rival introduces a lemma or
# weakens an obligation.
#
# No gold-side failure in this battery matches any of the gate's four
# stuck-reduction screens (checked against all 19 gold logs): no stuck `decide`,
# no `Dependent elimination failed`, no missing `Decidable` instance, no
# `forIn Lean.Loop.mk` unification failure. These obligations are loop-free, and
# no witness asks the kernel to decide a `Float` — the one rival whose guard is
# a float predicate is refuted from a HYPOTHESIS about that guard rather than by
# evaluating it, precisely so that no claim in this battery rests on arithmetic
# the kernel cannot perform.
AXIOM_TESTS = []
