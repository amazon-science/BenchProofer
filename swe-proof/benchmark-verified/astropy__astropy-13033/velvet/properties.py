"""properties.py — G-PBT falsification battery for astropy__astropy-13033 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical header) and swaps
in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over three read-only sequence inputs).

  requiredColumnsError (className required present)
        ensures out = errorMessage className required present

There is ONE method, ONE top-level post-image clause, and NO ``require`` clause
(the admitted domain is total). ``errorMessage`` is a fully unfolded function of
the method's own three arguments: it prepends the class name, renders the
required-name collection and the leading prefix of the present-name collection
each via the display rendering (a one-name collection reads as a quoted scalar,
any other size as the bracketed list), and pluralizes the noun exactly when more
than one name is required. The three inputs — ``className``, ``required``,
``present`` — are FREE: the post-image must hold for every value each takes,
which is what makes the partial-domain rivals below refutable at a concrete
point.

CARRIER NOTE — THE DECIDABLE BOUNDARY. The display rendering delegates the
per-element rendering of a collection of two-or-more names to an ``opaque``
platform leaf (the escaping-aware element renderer, left abstract in the spec
and bound to the real builtin by G-AX). A witness reaches the post-image through
Velvet's tester machinery and closes by ``decide``; ``decide`` reduces the
rendering ONLY where it does not touch that opaque leaf — i.e. on collections of
size ZERO (rendered as the empty bracketed list) or ONE (rendered as the quoted
scalar). Collections of size two-or-more are exactly where the opaque leaf
fires, so no ``decide``-witness can be built there. Every reject witness below
therefore lives at collection length ≤ 1. This is not a weakness of the rivals:
each divergence from the post-image is already observable on the length-≤1
boundary (the empty-list rendering ``[]`` vs the scalar ``'x'`` vs a dropped
prefix), so the length-≤1 witnesses discriminate genuinely. The ONE behaviour
whose divergence is confined to the length-≥2 sub-domain (the plural marker)
cannot be witnessed on this carrier and is reported as an omission below, not
faked.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because an input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent, there is no heap and
    no aliasing, and this bundle declares no ``mut`` binder at all — so there is
    no read-only input to overwrite and no substitute probe to fabricate.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the method's own arguments (``errorMessage`` and its helpers are
    concrete ``def``s in the ``pure`` region; the ``axioms`` region declares one
    ``opaque`` leaf but NO ``axiom``, and the proof never inspects it — there is
    no opaque answer key to echo). So there is no WRONG echo to build; the
    positive controls are honest cheapest-reshape controls instead.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the domain but
    diverging on a sub-domain (the empty-collection boundary; a dropped leading
    name; the found side echoing the required side).
  * FREE-INPUT PRESERVATION — APPLIES: the post-image carries THREE free inputs
    (the class name prefix, the required collection on the expected side, and the
    present prefix on the found side). A rival can get the rendering shape right
    and still drop one of them, so each free input is attacked on its own so its
    witness sits at a value the others do not probe.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. The four reject witnesses sit at four DISTINCT input points
and between them move all three binders off any fixed value: ``className`` takes
both a present name and the empty name; ``required`` takes both the empty
collection and a one-name collection; ``present`` takes both the empty
collection and a one-name collection distinct from ``required``.

AXIOM lane: the ``axioms`` region declares one ``opaque`` leaf but consumes NO
``axiom`` (the proof never uses a contract about it; its binding to the real
builtin is a G-AX obligation, validated executably there). There is no
axiom-soundness obligation for this gate to probe, and the gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-13033"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl body: a single anchor lying wholly inside the impl region
# ---- and unique in the file (both facts asserted at load by _swap). ----
_IMPL_GOLD = (
    "    let found := present.take required.length\n"
    "    let expectedStr := renderColumnList required\n"
    "    let foundStr := renderColumnList found\n"
    "    let plural : List Char := if required.length > 1 then ['s'] else []\n"
    "    let msg := className ++ \" object is invalid - expected \".toList ++ expectedStr\n"
    "      ++ \" as the first column\".toList ++ plural ++ \" but found \".toList ++ foundStr\n"
    "    return msg"
)
assert _IMPL_GOLD in _BASE, "impl anchor drift: requiredColumnsError body not verbatim"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- a positive control that reshapes the impl or an admissibility case that
# ---- adds an in-region assert may retune it without touching the spec or the
# ---- `prove_correct` header). ----
_PROOF_GOLD = (
    "prove_correct requiredColumnsError by\n"
    "  loom_solve\n"
    "  simp_all [errorMessage]"
)
assert _PROOF_GOLD in _BASE, "proof anchor drift"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester
# ---- machinery: `requiredColumnsErrorTester args = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped,
# ---- so no tactic script can mask the verdict. Every argument is a concrete
# ---- length-≤1 literal so `decide` reduces without touching the opaque leaf.
_TESTER = (
    "extract_program_for requiredColumnsError\n"
    "prove_precondition_decidable_for requiredColumnsError\n"
    "prove_postcondition_decidable_for requiredColumnsError\n"
    "derive_tester_for requiredColumnsError\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and the frozen proof
    # script (the post-image is a point-wise equality, so no reshape here needs
    # a new lemma).
    # =====================================================================
    {
        "id": "pos-locals-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the plural marker and the found-prefix render first,
        # the expected render last. Same assembled message, same left-assoc
        # concatenation; the returned value is unchanged.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let plural : List Char := if required.length > 1 then ['s'] else []\n"
            "    let found := present.take required.length\n"
            "    let foundStr := renderColumnList found\n"
            "    let expectedStr := renderColumnList required\n"
            "    let msg := className ++ \" object is invalid - expected \".toList ++ expectedStr\n"
            "      ++ \" as the first column\".toList ++ plural ++ \" but found \".toList ++ foundStr\n"
            "    return msg"),
        "rationale": "reordering the local bindings (plural and the found render "
                     "computed before the expected render) assembles the same "
                     "message, so `out = errorMessage className required present` "
                     "still holds pointwise; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on binding order.",
    },
    {
        "id": "pos-found-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline the present-prefix slice into the found render instead
        # of naming it in a `let`. Same value flow.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let expectedStr := renderColumnList required\n"
            "    let foundStr := renderColumnList (present.take required.length)\n"
            "    let plural : List Char := if required.length > 1 then ['s'] else []\n"
            "    let msg := className ++ \" object is invalid - expected \".toList ++ expectedStr\n"
            "      ++ \" as the first column\".toList ++ plural ++ \" but found \".toList ++ foundStr\n"
            "    return msg"),
        "rationale": "inlining the present-prefix slice into the found render "
                     "leaves the rendered characters unchanged, so the post-image "
                     "is unchanged; a correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method here has a `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous: nothing
    # could exclude an F2P-shaped input. The residual admissibility risk on a
    # total domain is that the post-image is UNSATISFIABLE / DEGENERATE at the
    # interesting point — a spec no impl can meet reads like a spec every impl
    # meets. This case discharges an in-region `assert`, at fully concrete
    # length-≤1 inputs, that the post-image is NON-DEGENERATE: the message for a
    # one-name required collection differs from the message for the empty one
    # (i.e. the rendering really discriminates the one-name case). The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof body is retuned only to clear the extra assert goal
    # by `decide` (allowed — the tactic body is elided from the spec view). The
    # assert is live, not decoration: a false claim about the same point leaves
    # an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-rendering-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                "    assert (with_name_prefix `admiss\n"
                "      (errorMessage \"T\".toList [\"a\".toList] [\"a\".toList]\n"
                "        ≠ errorMessage \"T\".toList [] [\"a\".toList]))\n"
                + _IMPL_GOLD),
            _PROOF_GOLD,
            "prove_correct requiredColumnsError by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [errorMessage]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at a "
                     "concrete F2P-shaped point: the message built for a one-name "
                     "required collection is distinct from the one for the empty "
                     "collection, so the rendering genuinely distinguishes the "
                     "cases the fix cares about. The in-region assert must "
                     "discharge (else an unsatisfiable/degenerate obligation); "
                     "the impl is kept verbatim so the ensures clause discharges "
                     "too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete length-≤1 input (the decidable boundary) and the refinement
    # argument that its faithful real counterpart would NOT resolve the failing
    # test.
    # =====================================================================
    {
        "id": "weak-drops-classname",
        "kind": "uniqueness",
        "expect": "reject",
        # Omits the class-name prefix from the assembled message. Abuses the
        # `className` free input — the only rival that does, so it is what moves
        # `className` off the empty value the other witnesses hold it at.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let found := present.take required.length\n"
            "    let expectedStr := renderColumnList required\n"
            "    let foundStr := renderColumnList found\n"
            "    let plural : List Char := if required.length > 1 then ['s'] else []\n"
            "    let msg := \" object is invalid - expected \".toList ++ expectedStr\n"
            "      ++ \" as the first column\".toList ++ plural ++ \" but found \".toList ++ foundStr\n"
            "    return msg"),
        "refinement": "a counterpart that drops the leading class name emits a "
                      "message beginning \"object is invalid ...\" instead of "
                      "\"TimeSeries object is invalid ...\", so the failing test "
                      "— which asserts the full message including the class name "
                      "— still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = errorMessage className required present`: "
                     "the post-image prepends `className` and the impl omits it, "
                     "so at any present class name the messages differ. Refuted "
                     "at `className = \"T\"`, the only witness that moves the "
                     "class-name binder.",
        "witness": _TESTER +
                   "example : requiredColumnsErrorTester \"T\".toList [] [] "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-first-name-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Renders only the FIRST required / present name as a quoted scalar,
        # regardless of collection size — the pre-patch behaviour. Correct only
        # when exactly one name is required; on the empty collection it renders
        # the quoted empty scalar where the post-image renders the empty
        # bracketed list, and on two-or-more names it names one where the
        # post-image names the whole collection.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let found := present.take required.length\n"
            "    let expectedStr := quoted (required.headD [])\n"
            "    let foundStr := quoted (found.headD [])\n"
            "    let plural : List Char := if required.length > 1 then ['s'] else []\n"
            "    let msg := className ++ \" object is invalid - expected \".toList ++ expectedStr\n"
            "      ++ \" as the first column\".toList ++ plural ++ \" but found \".toList ++ foundStr\n"
            "    return msg"),
        "refinement": "this IS the pre-patch behaviour: name only the first "
                      "required (resp. present) name as a quoted scalar however "
                      "many were required. For the failing scenario (two required "
                      "columns) it reports the first name where the post-image "
                      "reports the whole collection — the misleading first-name "
                      "message the issue is about — so the faithful patch does "
                      "NOT resolve.",
        "rationale": "REJECT from `out = errorMessage className required present`: "
                     "the expected/found sides are the quoted first element, "
                     "which on a collection that is NOT a single name diverges "
                     "from the display rendering. Refuted at the empty collection "
                     "(`required = present = []`), where the impl yields the "
                     "quoted empty scalar and the post-image the empty bracketed "
                     "list — the length-≤1 shadow of the length-≥2 divergence the "
                     "opaque leaf blocks a direct witness of.",
        "witness": _TESTER +
                   "example : requiredColumnsErrorTester [] [] [] "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-drops-first-required",
        "kind": "uniqueness",
        "expect": "reject",
        # Renders the required collection with its FIRST name dropped on the
        # expected side. Abuses the `required` free input: moves it to a
        # one-name collection, where dropping the first name leaves the empty
        # collection (rendered `[]`) instead of the quoted scalar.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let found := present.take required.length\n"
            "    let expectedStr := renderColumnList (required.drop 1)\n"
            "    let foundStr := renderColumnList found\n"
            "    let plural : List Char := if required.length > 1 then ['s'] else []\n"
            "    let msg := className ++ \" object is invalid - expected \".toList ++ expectedStr\n"
            "      ++ \" as the first column\".toList ++ plural ++ \" but found \".toList ++ foundStr\n"
            "    return msg"),
        "refinement": "a counterpart that renders the required collection with "
                      "its leading name dropped omits the first required column "
                      "from the expected side, so the failing test — which pins "
                      "the whole required collection — still fails. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = errorMessage className required present`: "
                     "the expected side must render `required`, and the impl "
                     "renders `required.drop 1`. Refuted at `required = [\"a\"]` "
                     "(present `[]`), where the post-image renders the quoted "
                     "scalar `'a'` and the impl the empty bracketed list `[]`. "
                     "This is the only witness that moves the `required` binder "
                     "to a non-empty value.",
        "witness": _TESTER +
                   "example : requiredColumnsErrorTester [] [\"a\".toList] [] "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-found-echoes-required",
        "kind": "uniqueness",
        "expect": "reject",
        # The found side renders the REQUIRED collection instead of the present
        # prefix. Gets the rendering shape right and corrupts the found side's
        # source. Abuses the `present` free input: it is the only rival whose
        # divergence needs `present` to differ from `required`.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let found := present.take required.length\n"
            "    let expectedStr := renderColumnList required\n"
            "    let foundStr := renderColumnList required\n"
            "    let plural : List Char := if required.length > 1 then ['s'] else []\n"
            "    let msg := className ++ \" object is invalid - expected \".toList ++ expectedStr\n"
            "      ++ \" as the first column\".toList ++ plural ++ \" but found \".toList ++ foundStr\n"
            "    return msg"),
        "refinement": "a counterpart whose found side echoes the required names "
                      "reports the columns that were required as though they were "
                      "the columns present, so the message never shows what was "
                      "actually there — the failing test, which pins the present "
                      "leading columns on the found side, still fails. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = errorMessage className required present`: "
                     "the found side must render the present prefix "
                     "`present.take required.length`, and the impl renders "
                     "`required`. Refuted at `required = [\"a\"]`, "
                     "`present = [\"b\"]`, where the found side must read `'b'` "
                     "and the impl emits `'a'`. This is the only witness that "
                     "moves the `present` binder to a value distinct from "
                     "`required`, so the found side's dependence on `present` is "
                     "observable.",
        "witness": _TESTER +
                   "example : requiredColumnsErrorTester [] [\"a\".toList] [\"b\".toList] "
                   "= false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals) across TWO contracted helper
# functions (render_name_run at "site A", compose_leading_run_report at
# "site B"). This bundle contracts a SINGLE method that assembles the whole
# message, so both sibling sites collapse onto one obligation here and the
# per-site rivals re-aim at the corresponding clause of the one post-image.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder-locals            -> pos-locals-reordered          PORTED
#   admissibility-three-readonly-inputs   -> admiss-rendering-nondegenerate RE-AIMED
#   frame-mutation-write-run              -> (none)                        VACUOUS
#   partial-domain-first-name-only        -> weak-first-name-only          PORTED
#   plural-marker-drop                    -> (none)                        OMITTED (carrier)
#   partial-domain-drop-first-name-helper -> weak-drops-first-required     PORTED
#
# 3 ported, 1 re-aimed, 1 vacuous, 1 omitted = 6.
#
# RE-AIMED (admissibility): the sibling establishes that the three read-only
#   half-permission inputs are usable and a normal return is reachable. This
#   backend has no permissions and no `require` clause, so nothing could exclude
#   a normal input — that probe is vacuous. It is re-aimed at the residual
#   admissibility risk on a total domain: that the post-image is UNSATISFIABLE /
#   DEGENERATE at the interesting point. The case discharges a concrete in-region
#   assert that the message for a one-name required collection differs from the
#   one for the empty collection (the rendering is non-degenerate).
# VACUOUS (frame-mutation-write-run): the sibling writes into a read-only
#   half-permission input to trip INSUFFICIENT PERMISSION. This backend is
#   referentially transparent, has no heap or aliasing, and this bundle declares
#   no `mut` binder — there is no read-only input to overwrite and no substitute
#   probe. Not fabricated.
# OMITTED (plural-marker-drop): the sibling forces the plural marker to empty and
#   is refuted on a multi-name required run. On THIS carrier the plural marker's
#   ONLY divergence from the post-image is at required.length > 1 — exactly the
#   sub-domain where the display rendering routes through the `opaque` per-element
#   leaf, so a `decide`-witness cannot reduce there (confirmed: the tester goal
#   does not reduce to isTrue/isFalse at a length-2 input). The rival is genuinely
#   wrong, but no discriminating witness can be built for it on this carrier, so
#   per the witness rule it is DROPPED rather than shipped witness-less. This is a
#   carrier limitation (the abstraction collapses the witnessable trace of that
#   clause), not a difficulty dodge. The plural clause is therefore the one
#   independent sub-term of the post-image left unattacked; see the coverage note.
#
# ADDED (1, no sibling counterpart): weak-found-echoes-required. The sibling's
#   site-B rivals attack the demanded/plural terms; the symmetric found-side
#   term (rendered from `present`, not `required`) is a binder-coverage gap —
#   without this rival no witness would move the `present` binder off a value
#   trivially derived from `required`, and a rival mishandling only that input
#   would go uncaught. Its faithful counterpart (found side echoing the required
#   names) leaves the failing test failing, and it carries a machine-checked
#   witness at `required=["a"], present=["b"]`.
#
# ADDED (1, binder coverage): weak-drops-classname. The sibling's site-B
#   post-image also prepends the class name (cls_name), but the sibling ships no
#   rival that drops it; here it is the only rival that moves the `className`
#   binder off the empty value, so its witness (className="T") is what varies
#   that binder across the battery.
#
# COVERAGE. Binders moved by the reject witnesses: className {"T", []};
#   required {[], ["a"]}; present {[], ["b"]} — all three varied, pts = 4
#   distinct input points. Independent sub-terms of the post-image attacked:
#   the class-name prefix (weak-drops-classname), the expected render of
#   `required` (weak-first-name-only, weak-drops-first-required), the found
#   render of the present prefix (weak-found-echoes-required). The plural marker
#   is the one sub-term left unattacked, for the carrier reason recorded under
#   OMITTED above — its divergence is not witnessable at the decidable boundary.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (the one `opaque` leaf is a G-AX A-reference, not a consumed
#   contract), so there is nothing here for this gate to probe.
AXIOM_TESTS = []
