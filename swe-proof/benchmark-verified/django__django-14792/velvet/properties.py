"""properties.py — G-PBT falsification battery for django__django-14792 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC_TESTS case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region is changed, and that region is elided from the consumer
spec view, so ``markers.same_spec`` holds and the ``prove_correct
resolveZoneLabel`` header survives) and swaps in a candidate implementation; it
is judged by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates — the witness must ELABORATE against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method, TWO input binders, THREE independent
top-level postcondition clauses):

  resolveZoneLabel (shortLabel : Option (List Char)) (fullLabel : List Char)
      return (out : List Char)
    ensures (∀ s, shortLabel = some s → s ≠ [] → out = s)        -- CLAUSE 3
    ensures (shortLabel = none → out = fullLabel)                -- CLAUSE 2
    ensures (∀ s, shortLabel = some s → s = [] → out = fullLabel) -- CLAUSE 1

The three clauses partition the ``shortLabel`` domain into its three
observationally distinct cases and pin ``out`` to EXACTLY one of the two carried
labels in each:

  * CLAUSE 3 (PRESENT AND NON-EMPTY): a short label that carries content wins
    outright — ``out`` is that label, never the full one. This is the
    discriminating clause: the desired behaviour that a descriptor offering a
    distinct short label must be named by it.
  * CLAUSE 2 (ABSENT): no short label at all ⇒ ``out`` is the full label.
  * CLAUSE 1 (PRESENT BUT EMPTY): a short label that carries no content does NOT
    win — it falls through to the full label, exactly as an absent one does. This
    is the emptiness boundary, and it is INDEPENDENT of clause 2: an impl can
    handle absence correctly and still let an empty label through.

Both clauses' right-hand sides are the method's OWN arguments, so the whole
postcondition is GROUNDED in the input binders: there is no opaque answer key, no
axiom (the ``axioms`` region is empty per mapping.md §3), and nothing for a wrong
impl to echo. The unique satisfier is the correct selection, which is why the
positive controls below are cheapest faithful reshapes rather than oracle echoes.

BINDER STRUCTURE (read before judging binder coverage). Two binders, and the
reject witnesses VARY BOTH. ``shortLabel`` takes five distinct values across the
witnesses — ``none``, ``some []``, and ``some s`` at three different non-empty
lengths (1, 2 and 3 characters) — so all three clause domains are probed and no
rival that mishandles only one arity slips past. ``fullLabel`` takes SIX distinct
values, never held fixed, so a rival that ignored it (or returned a constant in
its place) cannot agree with gold at every probed point. Six distinct input
points in all.

(Both counts above are exact and were re-checked mechanically: the six
``fullLabel`` values are pairwise distinct, and the three non-empty
``shortLabel`` arities are 1, 2 and 3.)

THE CARRIER IS FULLY TRANSPARENT. Every leaf is a ``Char`` literal or a ``List``
of them; ``Option``/``List`` equality computes on concrete literals. So each
witness reaches the method CONTRACT (not a bare predicate — the spec is a
``method``'s ``ensures`` triple) through Velvet's own tester machinery
(``extract_program_for`` / ``prove_precondition_decidable_for`` /
``prove_postcondition_decidable_for`` / ``derive_tester_for``):
``resolveZoneLabelTester <shortLabel> <fullLabel> = false`` says the extracted
program's result violates the postcondition at that concrete input, and
``decide`` closes it outright. No witness needs to CONDITION on the carrier, so
no witness binds a hypothesis and there is no joint-satisfiability obligation for
the gate's consistency probe to discharge. No ``sorry``/``admit``/
``native_decide``/``axiom`` appears in any witness.

WHY THE REJECTIONS ARE ATTRIBUTABLE, INDEPENDENTLY OF THE WITNESS. The frozen
impl is a straight-line ``match``/``if`` with no loop, and the frozen proof is a
bare ``loom_solve``, so every reject variant here fails with an explicit unsolved
goal NAMED for the clause it violates (e.g. ``case «ensures_3: (∀ s, shortLabel =
some s → s ≠ [] → out = s)»`` with the two differing sides in the goal) rather
than with a tactic-shape mismatch. Each rival's failing clause was read off its
build and is recorded in its ``rationale``. The ``witness`` is still what the
gate scores; the named goal is corroboration that the SPEC, not the script, is
doing the refuting. Every reject variant keeps the frozen ``prove_correct`` body
VERBATIM, and so does every soundness positive — no case in either of those two
lanes retunes a tactic. The single ``admissibility`` case extends the body by
``all_goals decide``, which is required and is not a retune of what was already
there: its in-region ``assert`` raises a SECOND goal beside the frozen ``ensures``
triple, and the added tactic closes only that goal (measured: with the frozen
body alone the case is exit 1 with ``case «admiss_1: …»`` unsolved and every
frozen clause closed). Its impl is the frozen one verbatim, so the method's own
obligation is still discharged by ``loom_solve``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling makes this lane
    MANDATORY and ships TWO rivals for it, because there BOTH labels are carried
    at a HALF (read-only) heap permission, so an impl that OVERWRITES one of them
    to satisfy the postcondition vacuously must be rejected by the permission
    system. Velvet has no such lane: it is referentially transparent, both labels
    are immutable VALUE parameters, this method declares NO ``mut`` binder, and
    there is no heap and no aliasing — there is no read-only reference to
    overwrite and no store to attempt. No substitute probe is fabricated.
  * DIVERGENCE / NON-TERMINATION — NOT PORTED, and NOT a spec hole: this bundle
    runs under `termination "total"`, so a diverging rival is REJECTED. It is
    unshippable for a WITNESS-side reason only. See the accounting block.
  * UNGROUNDED-ORACLE ECHO — N/A, and the nagini sibling records the same. Every
    clause's right-hand side is one of the method's own arguments, so there is no
    answer-key term to echo.
  * PARTIAL-DOMAIN / VALUE-LEVEL — the heart of the port. Each rival is correct
    on part of the ``shortLabel`` domain and wrong on the part some clause pins,
    and each is refuted at the smallest input exposing that part.
  * AXIOM lane — dropped (G-AX's job; this gate ignores ``AXIOM_TESTS``). The
    nagini sibling's single AXIOM_TEST probes its deep selection model against
    the real callees; mapping.md §3 records zero axioms and zero deep-model
    references here, so there would be nothing to probe even if the gate looked.
"""
from pathlib import Path

INSTANCE = "django__django-14792"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. `_IMPL` is the WHOLE executable body of resolveZoneLabel together
# with its two marker lines; it lies wholly inside the single impl region the
# spec view elides, and it is unique in Solution.lean (both facts asserted at
# load by _swap / the assert below). Editing only this text keeps
# markers.same_spec True and leaves the `prove_correct resolveZoneLabel`
# obligation byte-identical.
#
# `_PROOF` is the frozen proof body. It is anchored but NEVER swapped: every
# case below — positive controls included — keeps it verbatim. It is asserted
# here so the manifest breaks loudly if the frozen proof ever drifts, which
# would silently change what a "reject" means for the reject cases.
# ---------------------------------------------------------------------------
_IMPL = (
    "    -- impl-start\n"
    "    match shortLabel with\n"
    "    | none => return fullLabel\n"
    "    | some s =>\n"
    "      let out := if s ≠ [] then s else fullLabel\n"
    "      return out\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "resolveZoneLabel impl region drifted from expected text"

_PROOF = "prove_correct resolveZoneLabel by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct resolveZoneLabel body drifted"


def _impl(body: str) -> str:
    """Full Solution.lean with ONLY resolveZoneLabel's impl body replaced.

    The marker lines are re-emitted so the region boundaries are preserved
    exactly; the frozen proof body is left untouched in every case.
    """
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "    -- impl-end")


def _impl_reproved(body: str, proof: str) -> str:
    """`_impl`, plus a retuned `prove_correct` tactic BODY.

    Used by the admissibility case ALONE. The tactic body lies outside the spec
    view, so retuning it keeps `markers.same_spec` and leaves the
    `prove_correct resolveZoneLabel` header (the obligation itself) intact —
    `variant_scope` checks exactly that. It is needed because an in-region
    `assert` raises a SECOND goal beside the frozen `ensures` triple, and bare
    `loom_solve` does not discharge an assert goal on this carrier: measured
    exit 1 with the assert's own goal (`case «admiss_1: ...»`) left unsolved
    and the frozen clauses all closed. `all_goals decide` closes it, and closes
    nothing else — the method's own obligation is still discharged by
    `loom_solve` exactly as in the frozen file.
    """
    return _swap(_impl(body), _PROOF, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, so the witness reaches
# ---- the postcondition through Velvet's tester machinery rather than by
# ---- stating a bare predicate. `resolveZoneLabelTester <short> <full> = false`
# ---- says the extracted program's result violates the ensures triple at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. The carrier computes
# ---- on literals, so every witness closes by `decide` and binds NO hypothesis.
def _w(short: str, full: str) -> str:
    return (
        "extract_program_for resolveZoneLabel\n"
        "prove_precondition_decidable_for resolveZoneLabel\n"
        "prove_postcondition_decidable_for resolveZoneLabel\n"
        "derive_tester_for resolveZoneLabel\n\n"
        f"example : resolveZoneLabelTester {short} {full} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec (or
    # the obligation) over-constrains the executable FORM: SPEC-TOO-STRONG.
    # All three keep the frozen `prove_correct` body verbatim.
    #
    # These carry the ARGUMENT of the nagini sibling's three positives
    # (branch-reorder, predicate-as-guard, local-variable reshape) onto this
    # carrier. The sibling's shapes do not transliterate literally: its
    # reorder pivots on a `None or len==0` disjunction that this carrier
    # splits structurally, its predicate-as-guard names a @Pure helper that
    # has no counterpart here (the `pure` region is empty), and its
    # typed-locals reshape is not expressible in the `do` block (see the
    # accounting block). What ports is the claim each one makes: a faithful
    # impl with inverted branch polarity, one with a different emptiness test,
    # and one with an entirely different control-flow SHAPE must all verify.
    # =====================================================================

    # Invert the guard polarity: test for the EMPTY label and fall through,
    # instead of testing for content and taking it. Same value mapping, opposite
    # branch order. This is the sibling's branch-reorder argument on this
    # carrier.
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Same selection, opposite guard polarity: test for the EMPTY\n"
            "    -- short label and fall through to the full one, rather than\n"
            "    -- testing for content and taking it.\n"
            "    match shortLabel with\n"
            "    | none => return fullLabel\n"
            "    | some s =>\n"
            "      let out := if s = [] then fullLabel else s\n"
            "      return out\n"),
        "rationale": "PASS SOURCE = all three clauses. `if s = [] then fullLabel "
                     "else s` is the pointwise negation of the frozen guard, so it "
                     "selects the identical label on every (shortLabel, fullLabel): "
                     "clause 3 holds on the non-empty branch, clause 1 on the empty "
                     "branch, clause 2 unchanged. A faithful reshape with inverted "
                     "branch polarity MUST verify; if it cannot, the postcondition "
                     "over-fits the guard's syntactic direction "
                     "(SPEC-TOO-STRONG). Frozen proof body kept verbatim.",
    },

    # A different EMPTINESS TEST (`List.isEmpty`, a Bool-valued decision
    # procedure) in place of the propositional disequality `s ≠ []`, and the
    # absent case handled by `Option.elim` rather than a `match` — so the whole
    # body is one loop-free expression with no pattern match at all.
    {
        "id": "pos-option-elim",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- One loop-free expression, no pattern match: eliminate the\n"
            "    -- optional short label directly, and decide emptiness with the\n"
            "    -- Bool-valued emptiness test instead of a disequality.\n"
            "    let out := shortLabel.elim fullLabel "
            "(fun s => if s.isEmpty then fullLabel else s)\n"
            "    return out\n"),
        "rationale": "PASS SOURCE = all three clauses. Eliminating the option "
                     "directly sends `none` to `fullLabel` (clause 2) and `some s` "
                     "to the emptiness-decided selection; `s.isEmpty = true` iff "
                     "`s = []`, so clause 1 and clause 3 hold exactly as for the "
                     "frozen guard. A structurally different SHAPE (no match, one "
                     "expression, a Bool test rather than a Prop) with identical "
                     "meaning MUST verify, else the clauses constrain the impl's "
                     "form rather than its result. Frozen proof body kept verbatim.",
    },

    # Split the ENTIRE domain in the pattern match itself — three arms, no `if`
    # at all — so the emptiness boundary is decided by the constructor shape of
    # the label rather than by a guard. The most structurally distant faithful
    # shape available on this carrier, and the one that mirrors the spec's own
    # three-clause partition.
    {
        "id": "pos-three-way-split",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Decide all three cases in the pattern match itself — no guard\n"
            "    -- expression at all — so emptiness is settled by the label's\n"
            "    -- constructor shape.\n"
            "    match shortLabel with\n"
            "    | none    => return fullLabel\n"
            "    | some [] => return fullLabel\n"
            "    | some (c :: cs) => return (c :: cs)\n"),
        "rationale": "PASS SOURCE = all three clauses, one per arm. The three arms "
                     "are exactly the three clause domains: absent (clause 2), "
                     "present-but-empty (clause 1), present-with-content (clause 3, "
                     "returning that very label). No `if` is used, so the selection "
                     "is driven purely by the label's constructor shape — the "
                     "furthest faithful shape from the frozen guard on this carrier. "
                     "It MUST verify, else the spec is satisfiable only by the "
                     "frozen form (SPEC-TOO-STRONG). Frozen proof body kept "
                     "verbatim.",
    },

    # =====================================================================
    # ADMISSIBILITY — the third direction this gate tests (PRECOND-TOO-STRONG),
    # and the one the first port of this battery dropped as "vacuous (no
    # precond)". That reason was wrong and is retracted: the analogue on a TOTAL
    # carrier is not "is there a `require` to be too strong" — the
    # `pre-conditions` region is indeed empty — but "is the obligation
    # SATISFIABLE at the inputs that matter". A postcondition no impl can meet at
    # an interesting point reads exactly like a postcondition every impl meets:
    # `loom_solve` closes the frozen method either way, and the six rivals below
    # would all be rejected either way, so nothing else in this battery can tell
    # the two apart.
    #
    # This case settles it by DISCHARGING the three frozen clauses, as an
    # in-region `assert`, at three fully concrete inputs — one per clause domain
    # — with the value each clause demands substituted for `out`:
    #
    #   * PRESENT AND NON-EMPTY, and the two labels DIFFER: short label "+10"
    #     against full label "Etc/GMT-10". The clause triple is satisfied by
    #     `out = "+10"`, and the assert also states `"+10" ≠ "Etc/GMT-10"`, so
    #     the point is NON-DEGENERATE: the satisfier is the short label and it is
    #     provably not the full one. This is the input shape the failing test
    #     turns on, which is why it is the point the assert is stated at.
    #   * ABSENT: no short label at all, full label "Europe/Madrid", satisfied by
    #     `out = "Europe/Madrid"`.
    #   * PRESENT BUT EMPTY: full label "Asia/Tokyo", satisfied by
    #     `out = "Asia/Tokyo"`, plus `"Asia/Tokyo" ≠ []` so the empty branch's
    #     satisfier is not the degenerate empty label.
    #
    # The three clauses are stated JOINTLY at each point (not one clause at a
    # time), so the assert says a single `out` satisfies all three there — the
    # clauses are mutually satisfiable, not merely individually so.
    #
    # The impl is kept VERBATIM after the assert, so the method's own `ensures`
    # obligation still discharges by `loom_solve` and this case is a positive
    # about the SPEC rather than about a new impl. Only the tactic body is
    # retuned (`all_goals decide`), which is elided from the spec view; see
    # `_impl_reproved`.
    #
    # THE ASSERT IS LIVE, not decoration — measured, three ways, each a build
    # that differs from this case in the CLAIM alone and each exit 1 with the
    # `admiss_1` goal unsolved: (a) clause 3 falsified at the first point
    # (`out = "Etc/GMT-10"` where the clause demands the short label); (b) the
    # non-degeneracy falsified (`"+10" = "Etc/GMT-10"`); (c) clause 2 falsified
    # at the absent point (`out = []`). So `decide` is deciding this claim and
    # not merely succeeding.
    # =====================================================================
    {
        "id": "admiss-three-domains-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    -- The clause triple is jointly satisfiable at one concrete input\n"
            "    -- per clause domain, and non-degenerately so at the discriminating\n"
            "    -- one (the satisfier there is the short label, provably distinct\n"
            "    -- from the full label).\n"
            "    assert (with_name_prefix `admiss\n"
            "      (\n"
            "        ((∀ s, (some \"+10\".toList : Option (List Char)) = some s → s ≠ [] → \"+10\".toList = s)\n"
            "          ∧ ((some \"+10\".toList : Option (List Char)) = none → \"+10\".toList = \"Etc/GMT-10\".toList)\n"
            "          ∧ (∀ s, (some \"+10\".toList : Option (List Char)) = some s → s = [] → \"+10\".toList = \"Etc/GMT-10\".toList))\n"
            "        ∧ \"+10\".toList ≠ \"Etc/GMT-10\".toList\n"
            "        ∧\n"
            "        ((∀ s, (none : Option (List Char)) = some s → s ≠ [] → \"Europe/Madrid\".toList = s)\n"
            "          ∧ ((none : Option (List Char)) = none → \"Europe/Madrid\".toList = \"Europe/Madrid\".toList)\n"
            "          ∧ (∀ s, (none : Option (List Char)) = some s → s = [] → \"Europe/Madrid\".toList = \"Europe/Madrid\".toList))\n"
            "        ∧\n"
            "        ((∀ s, (some ([] : List Char) : Option (List Char)) = some s → s ≠ [] → \"Asia/Tokyo\".toList = s)\n"
            "          ∧ ((some ([] : List Char) : Option (List Char)) = none → \"Asia/Tokyo\".toList = \"Asia/Tokyo\".toList)\n"
            "          ∧ (∀ s, (some ([] : List Char) : Option (List Char)) = some s → s = [] → \"Asia/Tokyo\".toList = \"Asia/Tokyo\".toList))\n"
            "        ∧ \"Asia/Tokyo\".toList ≠ ([] : List Char)))\n"
            "    match shortLabel with\n"
            "    | none => return fullLabel\n"
            "    | some s =>\n"
            "      let out := if s ≠ [] then s else fullLabel\n"
            "      return out\n",
            "prove_correct resolveZoneLabel by\n  loom_solve\n  all_goals decide"),
        "rationale": "PRECOND-TOO-STRONG lane. The `pre-conditions` region is "
                     "empty, so there is no `require` clause that could exclude an "
                     "in-domain input; what remains testable on a total carrier is "
                     "whether the OBLIGATION is satisfiable where it matters, and "
                     "this case discharges it by evaluation. The three frozen "
                     "clauses are asserted JOINTLY — one `out` meeting all three — "
                     "at one concrete input per clause domain: present-and-nonempty "
                     "with the two labels DIFFERING (satisfier: the short label, "
                     "and the assert also states it is distinct from the full "
                     "label, so the point is non-degenerate rather than a place "
                     "where both clauses agree trivially), absent (satisfier: the "
                     "full label), and present-but-empty (satisfier: the full "
                     "label, asserted distinct from the empty one). If any of those "
                     "were unsatisfiable the assert leaves an unsolved goal and the "
                     "case fails ⇒ PRECOND-TOO-STRONG, i.e. the postcondition would "
                     "be vacuous at exactly the input the failing test turns on and "
                     "every rejection in this battery would attest to nothing. The "
                     "impl is kept VERBATIM so the method's own obligation still "
                     "discharges by `loom_solve`; only the tactic body is extended "
                     "to clear the extra assert goal.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input, and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test.
    #
    # Together they attack each of the three independent clauses IN ISOLATION
    # (always-full → 3, absent-yields-empty → 2, empty-label-wins → 1) and in
    # COMBINATION (always-short → 1+2, inverted-selection → 1+3), plus one
    # near-miss on a sub-domain of clause 3 (length-threshold). Every reject
    # variant keeps the frozen `prove_correct` body verbatim.
    # =====================================================================

    # ATTACK 1 (THE bug-delta / pre-image). Ignore the short label entirely and
    # always emit the full one. This is the pre-patch shape.
    {
        "id": "weak-always-full",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Ignore the short label entirely; always emit the full one.\n"
            "    return fullLabel\n"),
        "refinement": "this is the pre-image behaviour the change removes: the full "
                      "label is emitted for every descriptor, so a descriptor whose "
                      "short label is a distinct non-empty string is named by the "
                      "wrong text. The failing test tabulates exactly such a "
                      "descriptor and asserts the SHORT label is returned; a patch "
                      "that always returns the full one produces the full text "
                      "instead and FAILS that assertion. It is the very behaviour "
                      "reported as the regression, so it does NOT resolve.",
        "rationale": "REJECT from CLAUSE 3 (∀ s, shortLabel = some s → s ≠ [] → out "
                     "= s): whenever the short label is present, non-empty and "
                     "differs from the full label, `out = fullLabel` contradicts "
                     "`out = s`. The build leaves precisely that clause's goal "
                     "unsolved (`⊢ ∀ s, shortLabel = some s → s ≠ [] → fullLabel = "
                     "s`). Clauses 1 and 2 are satisfied, so this is a clean "
                     "single-clause attack. If it verifies ⇒ SPEC-TOO-WEAK (the spec "
                     "would not sense the pre-image, i.e. G-DIFF would be hollow). "
                     "Refuted at a present, non-empty short label that differs from "
                     "the full label.",
        "witness": _w('(some "+10".toList)', '"Etc/GMT-10".toList'),
    },

    # ATTACK 2 (the mirror blanket impl). Always emit the short label, defaulting
    # to the empty label when it is absent — i.e. never fall back at all. Wrong
    # on BOTH fall-through clauses at once.
    {
        "id": "weak-always-short",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Never fall back: always emit the short label, defaulting to the\n"
            "    -- empty one when it is absent.\n"
            "    return (shortLabel.getD [])\n"),
        "refinement": "emitting the short label unconditionally returns nothing "
                      "usable for a descriptor that offers no short label at all — "
                      "the caller receives an absent/empty text where the failing "
                      "test asserts the descriptor's full name. The test tabulates "
                      "named descriptors whose short label is absent and requires "
                      "the full name; a patch that drops the fall-back returns the "
                      "empty text and FAILS them, so it does NOT resolve. It also "
                      "breaks every existing caller that renders this text.",
        "rationale": "REJECT from CLAUSES 1 AND 2 SIMULTANEOUSLY: on `none` the "
                     "result is `[]`, violating clause 2 (`out = fullLabel`), and on "
                     "`some []` it is `[]`, violating clause 1. The build leaves both "
                     "goals unsolved. Its wrong domain is the UNION of the two "
                     "narrower rivals' below, so it is the blanket no-fall-back "
                     "impl rather than a near-miss; it is refuted here at "
                     "`shortLabel = none` with the full label a distinct named "
                     "string — the exact shape of the named-descriptor row of the "
                     "failing test. If it verifies ⇒ SPEC-TOO-WEAK on the entire "
                     "fall-back behaviour.",
        "witness": _w("none", '"Europe/Madrid".toList'),
    },

    # ATTACK 3 (near-miss, clause 2 in isolation). Handle a present short label
    # exactly as gold does, but on ABSENCE emit the empty label instead of
    # falling back. Correct on the whole `some` domain; wrong only at `none`.
    {
        "id": "weak-absent-yields-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Absence mishandled: emit the empty label instead of falling back\n"
            "    -- to the full one. The present cases are kept exactly as gold.\n"
            "    match shortLabel with\n"
            "    | none => return []\n"
            "    | some s =>\n"
            "      let out := if s ≠ [] then s else fullLabel\n"
            "      return out\n"),
        "refinement": "treating an absent short label as an empty result — rather "
                      "than falling back to the full label — returns empty text for "
                      "every descriptor that offers no short label. The failing test "
                      "tabulates such descriptors and asserts the full name is "
                      "returned; empty text FAILS those rows (and every existing "
                      "caller that renders this text would render nothing), so a "
                      "faithful patch of this shape does NOT resolve.",
        "rationale": "REJECT from CLAUSE 2 (shortLabel = none → out = fullLabel) "
                     "ALONE: at `none` the result is `[]`, not `fullLabel`. The build "
                     "leaves exactly that goal unsolved (`⊢ shortLabel = none → [] = "
                     "fullLabel`); clauses 1 and 3 are untouched and hold. This is a "
                     "NEAR-MISS that agrees with gold on the ENTIRE `some` domain, "
                     "so it is refuted at its ONLY wrong input, `shortLabel = none` "
                     "— and at a DIFFERENT full label from weak-always-short, so the "
                     "two rivals' claims are demonstrated at distinct points. If it "
                     "verifies ⇒ SPEC-TOO-WEAK at the absent branch specifically.",
        "witness": _w("none", '"UTC+10:00".toList'),
    },

    # ATTACK 4 (near-miss, clause 1 in isolation — the emptiness boundary). Fall
    # back correctly when the short label is ABSENT, but let a PRESENT-BUT-EMPTY
    # short label win. Correct everywhere except the empty label.
    {
        "id": "weak-empty-label-wins",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Emptiness boundary dropped: fall back only on ABSENCE, so a\n"
            "    -- present-but-EMPTY short label is emitted as-is.\n"
            "    return (shortLabel.getD fullLabel)\n"),
        "refinement": "distinguishing only present-vs-absent, and not "
                      "carries-content-vs-empty, emits empty text for a descriptor "
                      "whose short label is present but blank, where the intended "
                      "behaviour falls back to the full name. The reference "
                      "behaviour this change restores treats a blank short label as "
                      "carrying no content — the fall-back fires for blank exactly "
                      "as it does for absent — so a patch that only tests presence "
                      "diverges on any descriptor with a blank short label, "
                      "returning empty text where the full name is required. That "
                      "divergence is not the specified behaviour, so it does NOT "
                      "resolve.",
        "rationale": "REJECT from CLAUSE 1 (∀ s, shortLabel = some s → s = [] → out "
                     "= fullLabel) ALONE: at `some []` the result is `[]`, not "
                     "`fullLabel`. The build leaves exactly that goal unsolved; "
                     "clause 2 holds (absence DOES fall back here) and clause 3 "
                     "holds. This is the NEAR-MISS at the emptiness boundary — it "
                     "agrees with gold at every input except `some []` — so it is "
                     "refuted at its ONLY wrong input, `shortLabel = some []`. This "
                     "is what makes clause 1 load-bearing INDEPENDENTLY of clause 2: "
                     "no other rival isolates it. If it verifies ⇒ SPEC-TOO-WEAK at "
                     "the empty-label boundary.",
        "witness": _w("(some ([] : List Char))", '"Asia/Tokyo".toList'),
    },

    # ATTACK 5 (inverted selection). Emit the full label when the short one
    # carries content, and the short one when it is empty — wrong on the whole
    # domain the spec discriminates, in both directions at once.
    {
        "id": "weak-inverted-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Selection inverted: the full label wins when the short one\n"
            "    -- carries content, and the short one is emitted when it is empty.\n"
            "    match shortLabel with\n"
            "    | none => return fullLabel\n"
            "    | some s =>\n"
            "      let out := if s ≠ [] then fullLabel else s\n"
            "      return out\n"),
        "refinement": "inverting the selection returns the full name for exactly the "
                      "descriptors whose short label should have won, and empty text "
                      "for the blank-short-label ones. The failing test's "
                      "discriminating row asserts the short label is returned when "
                      "it carries content; this returns the full name there, so it "
                      "FAILS that row — and it is wrong in the opposite direction on "
                      "the blank rows too. It does NOT resolve.",
        "rationale": "REJECT from CLAUSES 1 AND 3 SIMULTANEOUSLY: the "
                     "present-with-content branch must yield `s` but yields "
                     "`fullLabel` (clause 3), and the empty branch must yield "
                     "`fullLabel` but yields `s` (clause 1). Clause 2 alone is "
                     "satisfied. The build leaves the clause-1 goal unsolved with "
                     "the inverted `if` visible in it. Refuted at a present, "
                     "non-empty short label of length 2 — an arity no other witness "
                     "uses — with its own distinct full label, so this rival's point "
                     "is not shared with weak-always-full's. If it verifies ⇒ SPEC-TOO-WEAK "
                     "(the selection's DIRECTION would be unpinned).",
        "witness": _w('(some "PT".toList)', '"Pacific/Auckland".toList'),
    },

    # ATTACK 6 (near-miss on a sub-domain of clause 3: an emptiness test that is
    # off by one). Require the short label to carry MORE THAN ONE character
    # before it wins. Correct on absence, on the empty label, and on every short
    # label of length ≥ 2 — wrong only for a single-character short label.
    {
        "id": "weak-length-threshold",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Off-by-one emptiness test: require MORE THAN ONE character before\n"
            "    -- the short label wins, instead of merely non-empty.\n"
            "    match shortLabel with\n"
            "    | none => return fullLabel\n"
            "    | some s =>\n"
            "      let out := if 1 < s.length then s else fullLabel\n"
            "      return out\n"),
        "refinement": "raising the content test from non-empty to longer-than-one "
                      "makes a one-character short label fall back to the full name. "
                      "The specified behaviour is that ANY short label carrying "
                      "content wins, so a descriptor whose short label is a single "
                      "character would be named by its full name instead — the same "
                      "class of divergence the change exists to remove, on a "
                      "narrower set of descriptors. A patch with this threshold "
                      "returns the wrong text for those descriptors, so it does NOT "
                      "resolve.",
        "rationale": "REJECT from CLAUSE 3, on a strict SUB-DOMAIN: at `some s` with "
                     "`s.length = 1` the result is `fullLabel`, not `s`. The build "
                     "leaves the clause-3 goal unsolved with the threshold `if` "
                     "visible in it. Clauses 1 and 2 hold, and clause 3 itself holds "
                     "for every short label of length ≥ 2 — so this is the tightest "
                     "near-miss in the battery, and it is what shows clause 3 pins "
                     "the boundary at NON-EMPTY rather than at any larger length. It "
                     "is refuted at the single-character short label, the only "
                     "arity where it is wrong, with its own distinct full label. If "
                     "it verifies ⇒ SPEC-TOO-WEAK on the exact position of the "
                     "content threshold.",
        "witness": _w('(some "Z".toList)', '"Etc/UTC".toList'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling ships 11 SPEC cases (3 soundness positives, 1
# admissibility, 2 frame-mutation rivals, 5 uniqueness rivals) plus 1
# AXIOM_TEST. This bundle models the SAME single operation — select the public
# label for a descriptor offering a possibly-absent, possibly-empty short label
# and an always-present full one — as the `resolveZoneLabel` method with three
# postcondition clauses. Every sibling case is accounted for below.
#
#   sibling case (nagini)   -> here                        disposition
#   -------------------------------------------------------------------------
#   pos-reorder             -> pos-negated-guard           RE-EXPRESSED
#   pos-predicate           -> pos-option-elim             RE-EXPRESSED
#   pos-locals              -> pos-three-way-split         RE-EXPRESSED
#   admiss-bothbranches     -> admiss-three-domains-satisfiable  RE-EXPRESSED
#   frame-mut-short         -> (none)                      VACUOUS (carrier)
#   frame-mut-full          -> (none)                      VACUOUS (carrier)
#   wrong-always-full       -> weak-always-full            PORTED
#   wrong-always-short      -> weak-always-short           PORTED
#   wrong-swap              -> weak-inverted-selection     PORTED
#   wrong-drop-empty        -> weak-empty-label-wins       PORTED
#   wrong-nonterm           -> (none)                      REJECTED, UNWITNESSABLE
#   (no sibling)            -> weak-absent-yields-empty    ADDED (clause 2 solo)
#   (no sibling)            -> weak-length-threshold       ADDED (clause 3 edge)
#   AXIOM_TESTS (1)         -> (none)                      N/A (out of lane)
#
# 10 SPEC cases (3 soundness, 1 admissibility, 6 uniqueness). Case count is
# LOWER than nagini's 11 because two whole classes (frame/permission-mutation,
# two cases) are carrier-vacuous and one (divergence) is spec-holed, not because
# any rival was dropped for being hard.
#
# RE-EXPRESSED (positives). The sibling's three positives make three claims —
#   inverted branch order, the emptiness predicate used directly as the guard,
#   and a local-variable reshape — and all three claims are carried, with the
#   mechanics rewritten for this carrier:
#     * pos-reorder -> pos-negated-guard. The sibling reorders around a single
#       `None or len == 0` disjunction. This carrier splits absence
#       (constructor) from emptiness (list shape) structurally, so the
#       corresponding reshape inverts the GUARD polarity on the emptiness test
#       (`s = []` falling through, instead of `s ≠ []` taking).
#     * pos-predicate -> pos-option-elim. The sibling's guard names a @Pure
#       helper predicate; this bundle's `pure` region is EMPTY (there is no such
#       helper to name — mapping.md §2 states the emptiness test inline), so the
#       claim is carried as a different DECISION PROCEDURE for the same test:
#       the Bool-valued emptiness test under a direct option elimination, with
#       no pattern match anywhere in the body.
#     * pos-locals -> pos-three-way-split. The sibling's shape — bind both
#       fields to typed locals, then select — is NOT expressible in this `do`
#       block: rebinding a parameter to a typed local ahead of the `match`
#       fails to elaborate (`Failed to parse an assertion without names: WPGen`,
#       reproduced on two spellings). That is a Velvet front-end limitation on
#       the impl region, not a spec property, so the claim it makes ("a
#       different DATA SHAPE, identical result, must verify") is carried by the
#       most structurally distant shape this carrier does admit: a three-arm
#       pattern match that decides emptiness by constructor shape with no guard
#       expression at all. Reported here rather than silently reshaped.
#   All three verified EXIT 0 with a real build, with the frozen `prove_correct`
#   body kept VERBATIM in each — no positive control retunes a tactic, so none
#   of them can be passing for a proof-side reason.
#
# LIMIT OF THE POSITIVE LANE (recorded by audit; NOT a spec hole). The three
#   positives all keep the frozen `loom_solve` body, which means the lane
#   certifies "correct AND provable by the frozen script", a strictly stronger
#   property than "correct". TWO further faithful reshapes are observationally
#   identical to gold yet FAIL under the frozen body, both because `loom_solve`
#   does not case-split a `match` whose scrutinee it has already abstracted into
#   an opaque local — the goal keeps an unreduced hypothesis
#   `a : ∀ c cs, i = some (c :: cs) → False` (or the unreduced `match` itself)
#   over an atom `i` it never connects back to `shortLabel`:
#     * WILDCARD ARM IN EXPRESSION POSITION
#       (`let out := match shortLabel with | some (c :: cs) => c :: cs
#         | _ => fullLabel`) — exit 1, unsolved `ensures_3`, the unreduced
#       `match` still in the goal.
#     * WILDCARD ARM IN STATEMENT POSITION
#       (`match shortLabel with | some (c :: cs) => return (c :: cs)
#         | _ => return fullLabel`) — exit 1, unsolved `ensures_3`, with the
#       negative hypothesis over the abstracted atom. This is the same wildcard
#       obstruction one step earlier, and it is what distinguishes both from
#       `pos-three-way-split`, which is shipped and DOES verify as-is: spelling
#       all three arms out explicitly (`none` / `some []` / `some (c :: cs)`)
#       avoids the wildcard entirely.
#   Neither is a spec defect. Both VERIFY once the tactic body is retuned —
#   measured exit 0, expression-position by `rcases shortLabel with _ | ⟨c, cs⟩
#   <;> loom_solve` and by an explicit `cases`/`cases s` nest, statement-position
#   by `loom_solve` followed by `all_goals (intro s hs hne; rcases s with _ |
#   ⟨c, cs⟩ <;> subst_vars <;> simp_all)` — so the postcondition admits both
#   reshapes and only the frozen TACTIC does not. (A third spelling an earlier
#   revision of this note cited for the expression-position case, `cases
#   shortLabel <;> loom_solve` after a `split`, does NOT in fact work: the
#   `split` fires first and `shortLabel` is out of scope by then, exit 1 with
#   `Unknown identifier shortLabel`. Corrected here; the claim it was offered for
#   still holds on the two spellings above.) No case is shipped for either, since
#   a positive control that retunes the proof body would no longer isolate the
#   spec from the script. Recorded so the positive lane is not read as "every
#   faithful reshape verifies as-is".
#
# PORTED (rivals). All FOUR nagini VALUE rivals port 1:1, each with its
#   refinement argument carried over (always-full is the pre-image the failing
#   test rejects; always-short returns nothing usable for a descriptor with no
#   short label; the inverted selection is wrong in both directions; and
#   drop-empty lets a blank short label through where the reference behaviour
#   falls back). Each was confirmed by a real build to fail with an unsolved
#   goal NAMED for the clause it violates, and each carries a witness verified
#   out-of-band with two builds.
#
# ADDED (two rivals with no sibling — carrier widening, not fabrication). The
#   sibling's contract has TWO clauses, keyed on a single @Pure
#   present-and-non-empty predicate, so its absent and empty cases are fused.
#   This carrier splits them into THREE independent clauses, which opens two
#   attack positions the sibling's shape has no room for, and coverage of the
#   surface THIS bundle models requires both:
#     * weak-absent-yields-empty isolates CLAUSE 2 (absence) — correct on the
#       entire `some` domain, wrong only at `none`. Without it, clause 2 is
#       attacked only by weak-always-short, which violates clause 1 at the same
#       time, so no case would attribute a rejection to clause 2 alone.
#     * weak-length-threshold isolates a SUB-DOMAIN of CLAUSE 3 — an emptiness
#       test that is off by one, correct for every short label of length ≥ 2.
#       It is what demonstrates the content threshold sits at NON-EMPTY rather
#       than at some larger length; every other clause-3 rival ignores the short
#       label wholesale and so says nothing about where the boundary is.
#
# RE-EXPRESSED (admissibility) — CORRECTED BY AUDIT. An earlier revision of this
#   manifest shipped NO admissibility case and recorded the lane as "VACUOUS (no
#   precond)", reasoning that the `pre-conditions` region is empty so no
#   precondition could be too strong. The premise is true and the CONCLUSION was
#   wrong, so the case now shipped replaces it and this entry records the
#   retraction rather than hiding it.
#
#   The sibling's `admiss-bothbranches` establishes that the operation's Requires
#   admits a normal F2P-shaped input. On a total carrier with no `require`, the
#   analogue is not "does a guard exclude the input" but "is the OBLIGATION
#   satisfiable at that input" — because a postcondition that is unsatisfiable at
#   the interesting point is indistinguishable, from every other case in this
#   battery, from one that is satisfiable there: `loom_solve` closes the frozen
#   method either way (its impl is a witness only at the inputs the tactic
#   actually reduces), and all six rivals below are rejected either way. So the
#   lane was not vacuous; it was untested.
#
#   The old note's own fallback argument — "the positive controls witness
#   satisfiability across all three clause domains" — does not substitute for it
#   either. A positive control shows some impl closes the WHOLE obligation
#   universally quantified over both binders; it never names a concrete input, so
#   it cannot show the clauses are jointly satisfiable NON-DEGENERATELY at the
#   one input where the two labels differ, which is the point the failing test
#   turns on and the only point where clause 3 has any content beyond clauses 1
#   and 2. `admiss-three-domains-satisfiable` states exactly that, by evaluation,
#   at three concrete inputs (one per clause domain) with the satisfying `out`
#   substituted, and pins the discriminating one to be non-degenerate. Measured
#   exit 0 with the impl kept verbatim; the assert is live, with three
#   claim-flipped controls each exit 1 on the `admiss_1` goal (see the case
#   comment). PRECOND-TOO-STRONG is REACHABLE on this bundle and is now tested.
#
# VACUOUS (frame / permission-mutation). The sibling makes this lane MANDATORY
#   and ships TWO rivals (overwrite the short label with the full one; overwrite
#   the full label with the short one), each of which must be rejected for
#   insufficient permission because both fields are carried at HALF permission —
#   Required AND Ensured read-only. Velvet has no such lane: it is referentially
#   transparent, both labels are immutable value parameters, this method declares
#   NO `mut` binder, and there is no heap and no aliasing. There is no read-only
#   reference to overwrite, no store to attempt, and no permission system to
#   trip. Both cases are therefore VACUOUS by the carrier — no substitute probe
#   is fabricated, per the porting map.
#
# DIVERGENCE / NON-TERMINATION — REJECTED BY THE SPEC, but UNWITNESSABLE on this
#   carrier. CORRECTED BY AUDIT; the previous revision of this block was wrong on
#   its central fact and is retracted in full.
#
#   WHAT IT CLAIMED. That this bundle runs under
#   `set_option loom.semantics.termination "total"`, that a diverging impl
#   therefore satisfies every value clause vacuously, and that the class is a
#   KNOWN SPEC HOLE — reporting an authoring-time build in which
#   `while true do pure ()` followed by `return []` allegedly VERIFIED at exit 0.
#
#   WHAT IS TRUE. Line 4 of the frozen Solution.lean reads
#   `set_option loom.semantics.termination "total"`. The claim was false about
#   the artifact it describes, and it inverted the lane's disposition: under
#   `total` the verifier DOES discharge a termination obligation, so a diverging
#   rival is genuinely rejected and the class is not a hole at all. Re-measured
#   here, two builds, frozen `prove_correct` untouched:
#     * `while true do pure ()` then `return []` (the wrong empty label,
#       contradicting all three clauses) — exit 1, TWO independent errors:
#       `Decreasing annotations are required in total correctness semantics`,
#       and `unsolved goals` on `case «done_1: ¬ true »`.
#     * the SAME diverging loop followed by the frozen selection VERBATIM (so the
#       returned value is correct and divergence is the only defect) — exit 1
#       with the same two errors. The rejection tracks the LOOP, not the value,
#       which is what makes it the termination obligation doing the work.
#   Cross-checked the mechanism: re-adding `set_option loom.linter.errors false`
#   makes BOTH of those impls exit 0. So the obligation is exactly what rejects
#   them, and the earlier "VERIFIES (exit 0 ...)" measurement is most likely that
#   linter-suppressed configuration mistaken for this bundle's.
#
#   WHY NO CASE IS SHIPPED ANYWAY — a WITNESS-side limitation, not a spec one.
#   A reject case on this backend must carry a witness that ELABORATES against
#   the rival, and every witness here closes by `decide` over
#   `resolveZoneLabelTester`. Measured: against ANY loop-bearing impl that tester
#   does not reduce, so the witness build fails on the rival — the half that must
#   succeed — and the case would be recorded `witness-unproven` /
#   `witness-undecided` rather than passing:
#     * diverging rival + tester witness — exit 1, `Tactic decide failed ...
#       did not reduce to isTrue or isFalse`, reduction stuck at the tester.
#       `decide +kernel` — exit 1 likewise.
#     * a TERMINATING loop bearing full `invariant` / `done_with` / `decreasing`
#       annotations and returning `[]` — the rival itself is correctly rejected
#       (exit 1, all THREE `ensures_` goals unsolved), but its tester witness is
#       stuck identically. So loop-freeness of the SPEC is not the issue; a
#       `while` under `loom.semantics.choice "demonic"` elaborates through
#       `Classical.choice`, which the kernel cannot unfold for any claim.
#   `witness_reference` does not rescue it either: the reference replaces the
#   GOLD-side subject, and the failure here is on the RIVAL side.
#   So: the spec is sound on this class (a diverging rival is rejected, and for
#   the termination obligation's own reason), and the class is unshippable for a
#   tooling reason recorded above with its error text. NOT a spec hole, NOT
#   "vacuous", and NOT dropped for being hard.
#
# AXIOM lane (dropped). The sibling ships one AXIOM_TEST probing its deep
#   selection model against the real callees. mapping.md §3 records zero axioms
#   and zero deep-model references for this bundle (the two label observations
#   are the input bijection, not consumed axioms), so there is nothing to probe;
#   and the axiom lane is G-AX's job, which this gate ignores regardless.
#
# CLAUSE / BINDER COVERAGE.
#   OBLIGATION. The sole obligation (`prove_correct resolveZoneLabel`) is
#     DEFENDED by three soundness positives, shown SATISFIABLE at three concrete
#     clause-domain inputs by one admissibility positive, and ATTACKED by six
#     rivals. All three of this gate's lanes are therefore present.
#   CLAUSES. All three independent top-level clauses are attacked, each in
#     ISOLATION by at least one rival — clause 3 by weak-always-full (and on a
#     sub-domain by weak-length-threshold), clause 2 by
#     weak-absent-yields-empty, clause 1 by weak-empty-label-wins — and in
#     combination by weak-always-short (1+2) and weak-inverted-selection (1+3).
#     No clause is defended only by a rival that also violates another, so every
#     clause is independently load-bearing.
#   BINDERS. Both input binders are VARIED across the six reject witnesses
#     (pts = 6 distinct input points):
#       shortLabel: none / none / some [] / some (len 1) / some (len 2) /
#                   some (len 3)          — 5 distinct values, all three clause
#                                           domains, three non-empty arities
#       fullLabel:  "Etc/GMT-10" / "Europe/Madrid" / "UTC+10:00" /
#                   "Asia/Tokyo" / "Pacific/Auckland" / "Etc/UTC"
#                                         — 6 distinct values, never pinned
#     `fullLabel` varying matters specifically: it is the right-hand side of two
#     of the three clauses, so a rival that returned a CONSTANT in its place
#     would agree with gold at every probed point if the binder were held fixed.
#     `shortLabel` varying across three non-empty ARITIES is what lets
#     weak-length-threshold be distinguished from weak-always-full at all.
#     The two witnesses that share `shortLabel = none` (weak-always-short,
#     weak-absent-yields-empty) sit at DIFFERENT `fullLabel` values and make
#     different claims; the overlap on the binder is unavoidable rather than a
#     gap, because weak-absent-yields-empty is a near-miss whose ONLY wrong
#     input is `none`, so its witness cannot be moved to a more discriminating
#     point without ceasing to refute it.
#   CONTENT-PRESERVATION PROBES (audit; no case shipped, all correctly
#     rejected). The six shipped rivals all select the WRONG WHOLE label, so
#     none of them asks whether clause 3 pins the CONTENT of the short label
#     rather than merely its provenance. Four rivals that return a MANGLED short
#     label — `s.reverse`, `s ++ ['!']`, `s.take 1`, and `fullLabel ++ fullLabel`
#     on the absent branch — were built against the frozen spec and every one
#     FAILED (exit 1), each with the expected clause named (`ensures_3` for the
#     first three, `ensures_2` for the fourth). A non-exhaustive `match` that
#     drops the `none` arm is rejected by the front end (`Missing cases: none`),
#     so vacuity by omitted branch is unreachable. Clause 3 therefore pins the
#     short label EXACTLY, not up to content; SPEC-TOO-WEAK not reproduced on any
#     of these five.
#   SECOND AUDIT PASS (independent re-derivation; no case shipped, every probe
#     built for real). Seven further wrong impls, all correctly REJECTED at exit
#     1 with the clause named: `s.take 1` (ensures_3), `s ++ fullLabel`
#     (ensures_3), `s.reverse` (ensures_3), a `'?'` sentinel substituted when the
#     full label is empty — the fullLabel = [] corner that NO shipped witness
#     probes (ensures_1), the same sentinel on the absent branch (ensures_2), a
#     rival that falls back only when the two labels DIFFER (ensures_1 +
#     ensures_3), and the sharpest available SPEC-TOO-WEAK probe: a LITERAL-KEYED
#     dodge whose guard reads `if s = "+10".toList then fullLabel else <frozen
#     selection>`, i.e. gold everywhere EXCEPT at exactly the one input the
#     failing test turns on (ensures_3). A spec that pinned behaviour only "in
#     general" would admit that last one; this spec catches it. A non-exhaustive
#     `match` dropping the `none` arm again hits `Missing cases`. Three further
#     CORRECT reshapes VERIFY at exit 0 under the frozen body VERBATIM —
#     `shortLabel.getD []` collapsed first then guarded, `if s.length = 0`, and a
#     `match` in expression position returning `if s.isEmpty = true then ...` — so
#     the positive lane is not narrower than the three shipped cases suggest.
#     Neither SPEC-TOO-WEAK nor SPEC-TOO-STRONG reproduced on any of the ten.
#     The manifest's two standing tactic-limit claims were also re-measured and
#     both hold: the wildcard arm in statement position FAILS under the frozen
#     body (exit 1, unsolved `ensures_3`) and VERIFIES (exit 0) under the retuned
#     body this file records; and binding a parameter to a typed local ahead of
#     the `match` still fails to elaborate with `Failed to parse an assertion
#     without names: WPGen`, confirming the `pos-locals` inexpressibility claim.
#   WITNESS DISCRIMINATION (verified during authoring with two real
#     `lean_verify.sh` builds per reject case): each witness ELABORATES against
#     its rival (exit 0 — the extracted tester `decide`s to `false` at the probed
#     input) and FAILS against the frozen solution (exit 1 — `decide` proves the
#     same proposition is false, a genuine discriminator rather than a
#     parse/tactic artifact). No witness binds a hypothesis, since the carrier
#     computes on concrete literals, so there is no joint-satisfiability
#     obligation for the gate's consistency probe. No witness contains
#     `sorry`/`admit`/`native_decide`/`axiom`, and no case adds a
#     `theorem`/`lemma` or edits a tactic body.
#   FORGERY CONTROL (second audit pass; attack B′, all six reject cases, 24 builds
#     in total). Each gold-side signature here is a PLAIN EVALUATION — `Tactic
#     decide proved that the proposition resolveZoneLabelTester <input> = false is
#     false` — so it already names the concrete claim rather than reporting a
#     stuck or mistyped term. Confirmed it CARRIES INFORMATION about that claim
#     rather than about the file's shape, by rebuilding each witness with the
#     claim FLIPPED (`= false` → `= true`) and nothing else changed. Every one of
#     the six inverts cleanly, both sides: flipped-vs-gold exit 0 (gold really
#     does return the value the frozen selection demands at that input) and
#     flipped-vs-rival exit 1 with the byte-changed error `... = true is false`.
#     So no case's exit code is a constant: gold's refusal tracks what is
#     asserted, and none of the six is hollow.
AXIOM_TESTS = []
