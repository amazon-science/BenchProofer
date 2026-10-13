"""properties.py — G-PBT falsification battery for sympy__sympy-18763 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct renderSubsNotation`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over two read-only sequence inputs).

  renderSubsNotation (body subsList : List Char) return (out : List Char)
      ensures out = subsNotationLatex body subsList          -- THE load-bearing clause

The method assembles the character sequence of the notation for an expression
displayed together with a list of evaluation assignments: the already-rendered
``body`` fragment enclosed in a matched pair of size-adjusting delimiters,
followed by the evaluation bar and the stacked assignment list ``subsList``.
``subsNotationLatex body subsList`` is a total, fully-unfolded pure function of
the method's own two inputs — a left-associated concatenation of five pieces:

    <open>  ++  body  ++  <mid>  ++  subsList  ++  <tail>

where ``<open>``, ``<mid>``, ``<tail>`` are constant literal segments. The
delimiter-enclosure of the body — the open delimiter inside ``<open>`` and the
matching close delimiter inside ``<mid>`` — is the behaviour the fix introduces
(pre-fix the body was emitted with no enclosing pair). The ``axioms`` region is
EMPTY; there is no opaque callee and no answer-key oracle to echo (directive 8 —
the post-image is grounded entirely in the actual inputs), so the whole
computation is transparent list arithmetic and every tester reduces under
``decide`` — no conditioning on an opaque carrier is required anywhere.

TWO input binders, both free; the post-image must hold for every value of each:
  * ``body``     — the rendered inner expression, copied through verbatim between
                   the two delimiters (length AND contents matter);
  * ``subsList`` — the rendered assignment list, copied through verbatim after the
                   evaluation bar (length AND contents matter).
There is NO ``require`` clause; the admitted domain is total, so no witness input
can be vacuously excluded by a precondition.

Independent sub-terms of the one post-image clause, each attacked below:
  * OPEN+CLOSE delimiter enclosure — the matched pair the fix adds around the body
    (the exact pre-fix defect: body emitted bare);
  * CLOSE-delimiter byte — the closing half of the pair must match the opening one;
  * CLOSE-delimiter on the empty-body sub-domain — the pair is UNCONDITIONAL, so a
    rival that skips the close delimiter only when the body is empty is still wrong;
  * BODY copied in full — every character of ``body`` is carried through;
  * SUBSLIST copied in full — every character of ``subsList`` is carried through;
  * TAIL literal — the trailing group-closing segment is present.

ADVERSARIAL READ of the nagini classes (see the footer for the case-by-case
accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries two
    such rivals (writes into the read-only ``body`` / ``cond`` half-permission
    inputs to trip INSUFFICIENT PERMISSION). This backend is referentially
    transparent, has no heap and no aliasing, and this bundle declares no ``mut``
    binder — the two inputs are immutable values with no permission footprint, so
    there is no read-only cell to overwrite and no substitute probe to fabricate.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``subsNotationLatex body subsList`` — a concrete ``def`` over the
    method's own arguments (empty ``axioms`` region; no opaque leaf). The only
    satisfier is the grounded assembly; there is nothing to echo.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. Each rival gets most of the
    assembly right and diverges on one sub-term above.

WITNESS MECHANICS. The frozen impl is LOOP-FREE (one ``++`` chain), so its
extracted tester reduces under ``decide``; each reject rival is likewise a
loop-free expression, so its tester also ``decide``s. Each reject rival therefore
carries a machine-checked refutation ``witness`` — a Velvet tester statement
``renderSubsNotationTester body subsList = false`` at ONE concrete input, checked
in a file whose ``prove_correct`` block has been stripped so no tactic script can
mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (the tester
``decide``s to ``false`` — the rival's output violates the postcondition there)
and FAILS against the frozen solution (gold's tester ``decide``s to ``true``, so
``= false`` is refuted). Every witness input is drawn from the total domain, so
none is vacuously excluded.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references;
the assembly is concrete list concatenation over the inputs. Nothing in the proof
rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-18763"
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
    '    let out : List Char :=\n'
    '      "\\\\left. \\\\left(".toList ++ body\n'
    '        ++ "\\\\right) \\\\right|_{\\\\substack{ ".toList ++ subsList\n'
    '        ++ " }}".toList\n'
    '    return out'
)
assert _BASE.count(_IMPL_GOLD) == 1, "impl anchor drift: renderSubsNotation body not verbatim"

# ---- the frozen proof body (tactic script only; elided from the spec view, so a
# ---- positive control that reshapes the impl or an admissibility case that adds
# ---- an in-region assert may retune it without touching the spec or the
# ---- `prove_correct` header). ----
_PROOF_GOLD = (
    "prove_correct renderSubsNotation by\n"
    "  loom_solve\n"
    "  simp [subsNotationLatex]"
)
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL_GOLD, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (positive controls / admissibility)."""
    return _swap(_impl(new_body), _PROOF_GOLD, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `renderSubsNotationTester body subsList = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict; both the rival and the frozen impl
# ---- are loop-free, so both testers reduce under `decide`.
_TESTER = (
    "extract_program_for renderSubsNotation\n"
    "prove_precondition_decidable_for renderSubsNotation\n"
    "prove_postcondition_decidable_for renderSubsNotation\n"
    "derive_tester_for renderSubsNotation\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Instead of inlining the
    # concatenation, it returns the pure model directly. The obligation IS
    # `out = subsNotationLatex ...`, so the body is definitionally the RHS and
    # `loom_solve` alone closes it (the frozen `simp [subsNotationLatex]` line is
    # dropped because there is no residual goal — verified out-of-band).
    # =====================================================================
    {
        "id": "pos-model-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    return subsNotationLatex body subsList",
            "prove_correct renderSubsNotation by\n  loom_solve"),
        "rationale": "structurally different CORRECT impl: it returns the pure "
                     "assembly model directly rather than inlining the five-piece "
                     "concatenation. Observationally identical on every input, so "
                     "`out = subsNotationLatex body subsList` holds on the whole "
                     "domain. A faithful reshape MUST verify, else the "
                     "postcondition is SPEC-TOO-STRONG (it would reject its own "
                     "model's output). Verified with a real build.",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — bind the three constant literal segments
    # to typed locals first, then concatenate. Identical value flow, different
    # executable shape; the frozen proof closes the byte-identical obligation.
    # This is the direct port of the sibling's local-variable reshape. Verified
    # out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-segments-bound-to-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            '    let openSeg : List Char := "\\\\left. \\\\left(".toList\n'
            '    let midSeg : List Char := "\\\\right) \\\\right|_{\\\\substack{ ".toList\n'
            '    let tailSeg : List Char := " }}".toList\n'
            '    let out : List Char := openSeg ++ body ++ midSeg ++ subsList ++ tailSeg\n'
            '    return out'),
        "rationale": "local-variable reshape: the three constant literal segments "
                     "are bound to typed locals before the concatenation. Identical "
                     "characters in identical left-assoc order, so the post-image is "
                     "unchanged; a correct reshape must verify. Verified with a real "
                     "build.",
    },

    # =====================================================================
    # POSITIVE CONTROL 3 (soundness) — a RIGHT-ASSOCIATED concatenation. The two
    # positives above are each definitionally the frozen right-hand side (one
    # returns the model itself, the other only names the constant segments), so
    # neither actually exercises the post-image up to associativity. This one
    # re-brackets the five pieces to the right, which is EQUAL but not
    # syntactically the frozen left-assoc chain, so it is the first positive whose
    # verification is not immediate from the shape. Verified with a real build,
    # under the FROZEN proof script unchanged (`loom_solve; simp
    # [subsNotationLatex]` closes it — `simp` normalizes append associativity),
    # so no proof retuning is needed.
    # =====================================================================
    {
        "id": "pos-right-associated-assembly",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            '    let out : List Char :=\n'
            '      "\\\\left. \\\\left(".toList ++ (body\n'
            '        ++ ("\\\\right) \\\\right|_{\\\\substack{ ".toList ++ (subsList\n'
            '        ++ " }}".toList)))\n'
            '    return out'),
        "rationale": "associativity reshape: the same five pieces in the same "
                     "order, re-bracketed to the RIGHT instead of the frozen "
                     "left-assoc chain. Character-for-character the same sequence, "
                     "so the post-image holds on the whole domain and a faithful "
                     "reshape must verify, else SPEC-TOO-STRONG. Unlike the two "
                     "positives above it is not the frozen right-hand side by "
                     "definitional unfolding alone, so it is the positive that "
                     "actually tests the clause up to associativity. Verified with "
                     "a real build using the frozen proof script.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require` clause, so the usual "a normal
    # input satisfies the precondition" probe is vacuous: nothing could exclude an
    # F2P-shaped input. The residual admissibility risk on a total domain is that
    # the post-image is DEGENERATE at the interesting point — e.g. if the modeled
    # assembly collapsed the delimiter enclosure to nothing, the obligation would
    # be met by an impl that emits the body bare, and the fix's whole content
    # would be untested. This case discharges an in-region `assert`, at the
    # concrete F2P-shaped input (body "- x + y", subsList "x=1"), that the
    # delimiter-enclosing assembly is NON-DEGENERATE: it differs from the
    # bare-body layout that omits the enclosing pair. The impl is kept verbatim so
    # the method's own obligation still discharges; the proof is retuned only to
    # clear the extra assert goal (`decide`), which is elided from the spec view.
    # The assert is live — a false claim leaves an unsolved goal (verified during
    # authoring).
    # =====================================================================
    {
        "id": "admiss-enclosure-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            '    assert (with_name_prefix `admiss\n'
            '      (subsNotationLatex "- x + y".toList "x=1".toList\n'
            '        ≠ "\\\\left. ".toList ++ "- x + y".toList\n'
            '          ++ " \\\\right|_{\\\\substack{ ".toList ++ "x=1".toList\n'
            '          ++ " }}".toList))\n'
            + _IMPL_GOLD,
            "prove_correct renderSubsNotation by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp [subsNotationLatex]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at a "
                     "concrete F2P-shaped point: the delimiter-enclosing assembly "
                     "for body '- x + y' / assignment 'x=1' is DISTINCT from the "
                     "layout that would emit the body with no enclosing pair, so "
                     "the modeled behaviour genuinely carries the enclosure the fix "
                     "is about (not a constant/empty collapse). The in-region "
                     "assert must discharge (else a degenerate obligation); the "
                     "impl is kept verbatim so the method's own `ensures` "
                     "discharges too. Verified with a real build.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a loop-free
    # expression so its extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-drop-enclosing-pair",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug: the body is dropped into the layout with NO enclosing
        # delimiter pair (open delimiter removed from <open>, close removed from
        # <mid>). Correct on the surrounding pieces; wrong exactly where the fix
        # adds the pair.
        "module": _impl(
            '    let out : List Char :=\n'
            '      "\\\\left. ".toList ++ body\n'
            '        ++ " \\\\right|_{\\\\substack{ ".toList ++ subsList\n'
            '        ++ " }}".toList\n'
            '    return out'),
        "refinement": "this IS the pre-fix behaviour: the body is emitted with no "
                      "enclosing size-adjusting delimiter pair. For the failing "
                      "scenario it renders the body bare between the evaluation "
                      "layout, exactly the un-enclosed rendering the issue reports "
                      "and the failing string-equality test rejects (it demands the "
                      "matched pair around the body). It would NOT resolve.",
        "rationale": "REJECT from `out = subsNotationLatex body subsList` via the "
                     "OPEN+CLOSE enclosure sub-terms: the post-image wraps the body "
                     "in the matched pair, the rival omits both halves, so the "
                     "sequences differ for every input. Verifying would be "
                     "SPEC-TOO-WEAK (the enclosure is unpinned). Refuted at "
                     "body='a', subsList='b'.",
        "witness": _witness('renderSubsNotationTester "a".toList "b".toList'),
    },
    {
        "id": "weak-close-delim-wrong-byte",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: the closing delimiter carries the wrong final byte (the
        # OPENING form where the CLOSING form is required), so the enclosing pair
        # is unmatched. Everything else is correct.
        "module": _impl(
            '    let out : List Char :=\n'
            '      "\\\\left. \\\\left(".toList ++ body\n'
            '        ++ "\\\\right( \\\\right|_{\\\\substack{ ".toList ++ subsList\n'
            '        ++ " }}".toList\n'
            '    return out'),
        "refinement": "emitting the opening delimiter form where the closing form "
                      "is required produces an unmatched enclosing pair — invalid "
                      "notation; the failing string-equality test, which pins the "
                      "exact closing delimiter, still fails. A near-miss whose "
                      "faithful counterpart would NOT resolve (the closing "
                      "delimiter must match the opening one).",
        "rationale": "REJECT from `out = subsNotationLatex body subsList` via the "
                     "CLOSE-delimiter byte, which the post-image pins exactly. "
                     "Refuted at body='', subsList='' — the divergence is in the "
                     "constant <mid> segment, so it shows even at empty inputs.",
        "witness": _witness('renderSubsNotationTester "".toList "".toList'),
    },
    {
        "id": "weak-close-delim-dropped-on-empty-body",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: emits the close delimiter EXCEPT when the body is empty,
        # where it skips it — leaving an unmatched open delimiter. Correct on every
        # non-empty body (so correct on the F2P inputs), wrong on the empty-body
        # sub-domain. Abuses the `body` binder at its empty value.
        "module": _impl(
            '    let midSeg : List Char :=\n'
            '      if body.isEmpty then " \\\\right|_{\\\\substack{ ".toList\n'
            '      else "\\\\right) \\\\right|_{\\\\substack{ ".toList\n'
            '    let out : List Char :=\n'
            '      "\\\\left. \\\\left(".toList ++ body\n'
            '        ++ midSeg ++ subsList\n'
            '        ++ " }}".toList\n'
            '    return out'),
        "refinement": "a faithful counterpart that emits the open delimiter but "
                      "conditionally skips the close delimiter when the inner "
                      "expression is empty produces an unmatched enclosing pair on "
                      "an empty-body substitution — invalid notation, divergent "
                      "from the gold UNCONDITIONAL enclosure. It is correct on the "
                      "non-empty F2P bodies but wrong on the empty-body "
                      "sub-domain, so it does not faithfully implement the "
                      "matched-pair change and would NOT resolve for such an input.",
        "rationale": "REJECT from `out = subsNotationLatex body subsList`: the "
                     "post-image emits the close delimiter UNCONDITIONALLY, for "
                     "ALL bodies including the empty one; the rival drops it there. "
                     "Refuted at body='' (subsList='z') — the only witness that "
                     "moves the `body` binder to its empty value, exactly the "
                     "sub-domain the rival mishandles.",
        "witness": _witness('renderSubsNotationTester "".toList "z".toList'),
    },
    {
        "id": "weak-drop-last-body-char",
        "kind": "uniqueness",
        "expect": "reject",
        # Copies the body with its LAST character dropped. Correct shape and
        # correct on empty/one-char? no — diverges whenever body is non-empty.
        # Abuses the `body` binder's contents.
        "module": _impl(
            '    let out : List Char :=\n'
            '      "\\\\left. \\\\left(".toList ++ body.dropLast\n'
            '        ++ "\\\\right) \\\\right|_{\\\\substack{ ".toList ++ subsList\n'
            '        ++ " }}".toList\n'
            '    return out'),
        "refinement": "dropping the last character of the rendered inner "
                      "expression renders truncated notation (e.g. '- x + ' "
                      "instead of '- x + y'); the failing string-equality test, "
                      "which pins the whole body verbatim, still fails. Not the "
                      "gold verbatim-body behaviour, so it would NOT resolve.",
        "rationale": "REJECT from `out = subsNotationLatex body subsList` via the "
                     "BODY-copied-in-full sub-term: the post-image copies every "
                     "character of `body`, the rival drops the last, so they "
                     "disagree whenever `body` is non-empty. Refuted at body='ab', "
                     "subsList='c' — moves the `body` binder to a two-char value.",
        "witness": _witness('renderSubsNotationTester "ab".toList "c".toList'),
    },
    {
        "id": "weak-drop-subslist",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the `subsList` fragment entirely (the assignment list never
        # appears). Correct on the body-enclosure side; wrong on the found side.
        # This is the ONLY rival that abuses the `subsList` binder, so its witness
        # is what moves `subsList` off a value trivially shared with `body`.
        "module": _impl(
            '    let out : List Char :=\n'
            '      "\\\\left. \\\\left(".toList ++ body\n'
            '        ++ "\\\\right) \\\\right|_{\\\\substack{ ".toList\n'
            '        ++ " }}".toList\n'
            '    return out'),
        "refinement": "a counterpart that omits the rendered assignment list emits "
                      "an evaluation notation with no assignments shown after the "
                      "bar, so the failing string-equality test — which pins the "
                      "assignment list — still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = subsNotationLatex body subsList` via the "
                     "SUBSLIST-copied-in-full sub-term: the post-image includes "
                     "`subsList` between the group open and the tail, the rival "
                     "omits it, so they disagree whenever `subsList` is non-empty. "
                     "Refuted at body='p', subsList='q' — the only witness that "
                     "moves the `subsList` binder to a non-empty value distinct "
                     "from `body`, so the result's dependence on `subsList` is "
                     "observable.",
        "witness": _witness('renderSubsNotationTester "p".toList "q".toList'),
    },
    {
        "id": "weak-drop-tail-segment",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the trailing group-closing literal segment. Correct on everything
        # up to the tail; the stacking group is left unclosed.
        "module": _impl(
            '    let out : List Char :=\n'
            '      "\\\\left. \\\\left(".toList ++ body\n'
            '        ++ "\\\\right) \\\\right|_{\\\\substack{ ".toList ++ subsList\n'
            '    return out'),
        "refinement": "a counterpart that omits the trailing group-closing segment "
                      "leaves the stacking group unclosed — invalid notation; the "
                      "failing string-equality test, which pins the full trailing "
                      "segment, still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = subsNotationLatex body subsList` via the "
                     "TAIL literal sub-term: the post-image appends the trailing "
                     "group-closing segment, the rival drops it, so the sequences "
                     "differ for every input. Refuted at body='m', subsList='n'.",
        "witness": _witness('renderSubsNotationTester "m".toList "n".toList'),
    },
    {
        "id": "weak-tail-dropped-on-empty-subslist",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the OTHER binder. Every rival above that varies a
        # sub-domain conditions on `body`; this one conditions on `subsList`,
        # emitting the trailing group-closing segment EXCEPT when the assignment
        # list is empty, where it skips it. Correct on every non-empty subsList
        # (so correct on the F2P inputs), wrong on the empty-subsList sub-domain.
        "module": _impl(
            '    let tailSeg : List Char :=\n'
            '      if subsList.isEmpty then "".toList else " }}".toList\n'
            '    let out : List Char :=\n'
            '      "\\\\left. \\\\left(".toList ++ body\n'
            '        ++ "\\\\right) \\\\right|_{\\\\substack{ ".toList ++ subsList\n'
            '        ++ tailSeg\n'
            '    return out'),
        "refinement": "a counterpart that closes the stacking group only when the "
                      "assignment list is non-empty leaves the group unclosed for "
                      "an empty assignment list — invalid notation, divergent from "
                      "the gold UNCONDITIONAL tail. It is correct on the non-empty "
                      "F2P assignment lists but wrong on the empty-subsList "
                      "sub-domain, so it does not faithfully implement the assembly "
                      "and would NOT resolve for such an input.",
        "rationale": "REJECT from `out = subsNotationLatex body subsList`: the "
                     "post-image appends the trailing group-closing segment "
                     "UNCONDITIONALLY, for ALL assignment lists including the empty "
                     "one; the rival drops it there. This is the only rival that "
                     "moves the `subsList` binder to its EMPTY value while `body` "
                     "is non-empty — every other sub-domain rival conditions on "
                     "`body` — so without it a rival mishandling only the "
                     "empty-subsList sub-domain would go uncaught. Refuted at "
                     "body='k', subsList=''.",
        "witness": _witness('renderSubsNotationTester "k".toList "".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 2 frame-mutation rivals, 2 partial-domain rivals, 1 drop-delim rival,
# 1 wrong-constant rival, 1 admissibility) plus an EMPTY AXIOM lane. This bundle
# models the SAME purely-functional core — the delimiter-enclosing string
# assembly for an evaluated-at-a-point expression — over `List Char` instead of
# the sibling's List[int] code-point carrier with a `@Pure assembled` grounded
# function. The value surface carries across intact; there is no permission
# surface on this backend.
#
#   sibling case                          -> here                              disposition
#   ------------------------------------------------------------------------------------
#   pos-control-local-reshape             -> pos-segments-bound-to-locals      PORTED
#   (no sibling)                          -> pos-model-direct                  ADDED
#   (no sibling)                          -> pos-right-associated-assembly     ADDED (audit)
#   frame-mutate-body                     -> (none)                            VACUOUS
#   frame-mutate-cond                     -> (none)                            VACUOUS
#   partial-domain-empty-body-drops-close -> weak-close-delim-dropped-on-empty-body PORTED
#   partial-domain-drop-last-body-char    -> weak-drop-last-body-char          PORTED
#   drop-delim-prepatch-bug               -> weak-drop-enclosing-pair          PORTED
#   wrong-close-delim-byte                -> weak-close-delim-wrong-byte        PORTED
#   admissibility-f2p-shaped-input        -> admiss-enclosure-nondegenerate    RE-AIMED
#   (no sibling)                          -> weak-drop-subslist                ADDED
#   (no sibling)                          -> weak-drop-tail-segment            ADDED
#   (no sibling)                          -> weak-tail-dropped-on-empty-subslist ADDED (audit)
#   AXIOM_TESTS ([])                      -> (none)                            DROPPED (G-AX)
#
# All 6 non-frame sibling SPEC cases PORTED/RE-AIMED (1 positive, 2 partial-domain,
# drop-delim, wrong-close, 1 admissibility); 5 cases ADDED for binder/sub-term
# coverage; the two frame rivals are VACUOUS here; the empty axiom lane dropped.
#
# PORTED (positive): the sibling binds each constant code-point segment to a typed
#   local before concatenating — here the constant literal segments are bound to
#   `List Char` locals, then concatenated in the same order (pos-segments-bound-to-
#   locals). Keeps the whole assembly, so the frozen proof closes the byte-identical
#   obligation. Verified out-of-band with a real build.
# ADDED (positive): pos-model-direct returns the pure model `subsNotationLatex`
#   directly. The obligation IS `out = subsNotationLatex ...`, so the body is
#   definitionally the RHS; `loom_solve` closes it (the residual `simp` line is
#   dropped, no goal remains). A second, cheaper correct reshape guarding against
#   SPEC-TOO-STRONG on the assembly shape. NOTE (audit): being definitionally the
#   RHS is exactly what makes this the WEAKEST of the three positives — it cannot
#   fail for any spec that mentions its own model, so it certifies little on its
#   own; pos-segments-bound-to-locals only names the constant segments and is
#   likewise shape-identical after unfolding the `let`s. That is why
#   pos-right-associated-assembly was added: it is the one positive that is equal
#   but NOT syntactically the frozen chain.
# PORTED (rivals): drop-delim -> weak-drop-enclosing-pair (the exact pre-fix bug:
#   body emitted bare, no enclosing pair); wrong-close -> weak-close-delim-wrong-byte
#   (near-miss: closing delimiter carries the opening byte, unmatched pair);
#   partial-empty -> weak-close-delim-dropped-on-empty-body (close delimiter skipped
#   only when the body is empty — correct on the F2P bodies, wrong on the empty-body
#   sub-domain, attacking the `body` binder at its empty value); partial-lastchar ->
#   weak-drop-last-body-char (body copied with its last character dropped). Each
#   carries a machine-checked witness that ELABORATES against the rival and FAILS
#   against gold (two real builds per case).
# RE-AIMED (admissibility): the sibling self-calls on an F2P-shaped input to show the
#   Requires admits it. This backend has NO `require` clause and no permission
#   surface, so nothing could exclude a normal input — that probe is vacuous. It is
#   re-aimed at the residual total-domain admissibility risk: that the post-image is
#   DEGENERATE at the interesting point. The case discharges a concrete in-region
#   assert (at body '- x + y' / assignment 'x=1') that the delimiter-enclosing
#   assembly is DISTINCT from the bare-body layout — i.e. the enclosure the fix adds
#   genuinely appears in the output. Verified with a real build.
# ADDED (weak-drop-subslist): the sibling has no rival that drops the assignment-list
#   fragment; here it is the ONLY rival that abuses the `subsList` binder, so its
#   witness (body='p', subsList='q') is what moves `subsList` off a value trivially
#   shared with `body`. Without it a rival mishandling only the `subsList` input
#   would go uncaught.
# ADDED (weak-drop-tail-segment): attacks the trailing group-closing literal — a
#   sub-term of the post-image the sibling's rivals do not isolate. Included so no
#   independent piece of the assembly is left unattacked.
# VACUOUS (frame-mutate-body, frame-mutate-cond): the sibling writes into the
#   read-only half-permission inputs to trip INSUFFICIENT PERMISSION. This backend
#   is referentially transparent, has no heap or aliasing, and this bundle declares
#   no `mut` binder — both inputs are immutable values with no permission footprint,
#   so there is no read-only cell to overwrite and no substitute probe. Not
#   fabricated (porting map: vacuous here). Re-derived during the audit by building
#   the analogue anyway (`body := ...` in the impl region): it does not elaborate
#   at all — `error: `body` cannot be mutated, only variables declared using
#   `let mut` can be mutated` — so the rival is rejected by the ELABORATOR before
#   any spec obligation is consulted. Its rejection would therefore attest to a
#   syntax rule, not to the spec, and no witness could discriminate it; the class
#   is genuinely inexpressible here rather than merely hard.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references (the assembly is concrete list
#   concatenation), so there is nothing to probe and the gate ignores AXIOM_TESTS
#   regardless.
#
# BINDER / SUB-TERM COVERAGE of the reject witnesses (pts = 7 distinct input points):
#     body     — 'a', '', '', 'ab', 'p', 'm', 'k': empty AND non-empty, one- and
#                two-char, contents varied.
#     subsList — 'b', '', 'z', 'c', 'q', 'n', '': empty AND non-empty, contents varied
#                (weak-drop-subslist is the point where subsList differs from body;
#                weak-tail-dropped-on-empty-subslist is the point where subsList is
#                empty while body is not — the two binders are moved INDEPENDENTLY,
#                so no clause's dependence on one is masked by the other).
#   Every independent sub-term of `out = subsNotationLatex body subsList` is attacked:
#   OPEN+CLOSE enclosure (weak-drop-enclosing-pair), CLOSE-delimiter byte
#   (weak-close-delim-wrong-byte), CLOSE-delimiter on the empty-body sub-domain
#   (weak-close-delim-dropped-on-empty-body), BODY-in-full (weak-drop-last-body-char),
#   SUBSLIST-in-full (weak-drop-subslist), TAIL literal (weak-drop-tail-segment),
#   TAIL on the empty-subsList sub-domain (weak-tail-dropped-on-empty-subslist).
#   No two rivals share an input tuple. Both sub-domain rivals are PARTIAL-domain:
#   each is correct on the F2P-shaped inputs and wrong only off them, so neither is
#   caught by a single well-formed example.
AXIOM_TESTS = []
