"""properties.py — G-PBT falsification battery for django__django-13112 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over an ASCII code-point sequence
carrier, ``List Char``). The method canonicalizes a model reference:

  normalizeRef (ref : List Char) return (out : List Char)
    require (ref.filter (· = '.')).length ≤ 1     -- ≤ one separator
    require ∀ c ∈ ref, c.toNat < 128              -- ASCII domain (fold is exact)
    ensures out = normalizedRef ref               -- THE load-bearing clause

``normalizedRef`` is a fully unfolded ``def`` in the ``pure`` region — there is
NO opaque answer key to echo. Its shape is a case split on whether the reference
carries the separator (``isQualified``):

  * qualified  -> the prefix before the separator is kept VERBATIM (its case is
    preserved) and only the suffix after it is case-folded;
  * unqualified -> the WHOLE reference is case-folded.

So the single ``ensures`` clause carries two independent behaviours over the one
input binder ``ref``: (a) the case-fold applied to a bare reference / the model
suffix, and (b) the verbatim preservation of the prefix on a qualified
reference. Both must be exercised, and the witnesses below vary ``ref`` across
BOTH arms of the ``isQualified`` split and BOTH sub-parts of the qualified arm
(prefix vs suffix), so no sub-behaviour is left pinned at one value.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS here. The nagini sibling carries this class as
    MANDATORY because its input holds a fractional heap permission an impl can
    illegally overwrite (write the read-only input, return it). Lean and Velvet
    are referentially transparent: ``ref`` is an immutable value, there is no
    ``mut`` binder in this bundle, no heap and no aliasing — so there is no
    read-only input to mutate and no substitute probe to build. Not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class: the post-image is a total,
    fully unfolded function of the method's own input (``normalizedRef`` and its
    helpers ``foldCase``/``isQualified``/``appPart``/``namePart`` are concrete
    ``def``s in the ``pure`` region; the ``axioms`` region is empty), so there is
    no answer key to echo. The nagini sibling notes the same and carries the
    class as its cheapest WRONG echoes; those port directly as reject rivals
    (return the input verbatim / fold everything).
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival correct on part of the reference
    domain but diverging on a sub-domain (a bare name vs a qualified reference;
    the prefix vs the suffix of a qualified reference).

WITNESS PLACEMENT. Each reject rival is refuted at a concrete ``ref`` chosen so
the three points together move the input across the whole modeled structure: a
qualified reference with an upper-case PREFIX, a bare (unqualified) reference,
and a qualified reference with an upper-case SUFFIX. No two rivals fail at the
same point, and the two partial-domain rivals (lower-all, keep-model) are refuted
on the exact sub-domains where they diverge from the frozen solution while
agreeing elsewhere, so their sub-domain claims are machine-checked rather than
asserted.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the transformation is
modeled DEEPLY). There is no axiom-soundness / axiom-containment obligation to
probe here, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13112"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single impl region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap). ----
_IMPL = (
    "    let result : List Char :=\n"
    "      if ref.contains '.' then\n"
    "        (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower\n"
    "      else\n"
    "        ref.map Char.toLower\n"
    "    return result"
)

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. The body below is the frozen script, unique in the file. ----
_PROOF = (
    "prove_correct normalizeRef by\n"
    "  loom_solve\n"
    "  simp only [normalizedRef, isQualified, appPart, namePart, foldCase]"
)

def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_and_proof(new_impl: str, new_proof: str) -> str:
    """Reshape the impl body AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `normalizeRefTester ref = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. Every probed input satisfies both `require` clauses
# ---- (≤1 dot, all ASCII), so the tester reaches the postcondition rather than
# ---- vacuously passing on an excluded input.
_TESTER = (
    "extract_program_for normalizeRef\n"
    "prove_precondition_decidable_for normalizeRef\n"
    "prove_postcondition_decidable_for normalizeRef\n"
    "derive_tester_for normalizeRef\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. The prefix and the case-folded suffix are
    # bound to typed locals ahead of the case split, then assembled in the
    # qualified arm; the decision and the assembled value are unchanged, so
    # the frozen tactic script still closes the (byte-identical) obligation.
    # =====================================================================
    {
        "id": "pos-bind-parts",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    let app : List Char := ref.takeWhile (· ≠ '.')\n"
            "    let folded : List Char := ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower\n"
            "    let result : List Char :=\n"
            "      if ref.contains '.' then\n"
            "        app ++ ['.'] ++ folded\n"
            "      else\n"
            "        ref.map Char.toLower\n"
            "    return result"),
        "rationale": "binding the verbatim prefix and the case-folded suffix to "
                     "typed locals before the qualified/unqualified decision "
                     "leaves the decision and the assembled value identical, so "
                     "`out = normalizedRef ref` still holds on both arms of the "
                     "isQualified split; a correct reshape MUST verify, else "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini sibling's self-call establishes that the
    # precondition ADMITS a normal, F2P-shaped input. This bundle DOES carry
    # `require` clauses (≤1 dot; all-ASCII), so that probe is live here: the
    # case discharges an in-region assertion that the F2P-shaped reference
    # (mixed-case app label, qualified) satisfies BOTH `require` clauses AND
    # that the post-image is non-degenerate there (it demands exactly the
    # prefix-verbatim / suffix-folded normalization, not something an empty or
    # unsatisfiable spec would admit). The assertion is live, not decoration:
    # replacing the claimed normalized form with a wrong one leaves an unsolved
    # `False` goal (verified out-of-band). The frozen body follows the assert,
    # so the method's own `ensures` obligation still discharges; the tactic
    # script is retuned only to also close the added assertion goal.
    # =====================================================================
    {
        "id": "admiss-f2p-precondition-admits",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_and_proof(
            '    assert (with_name_prefix `admiss\n'
            '      (((("MiXedCase.Author".toList).filter (· = \'.\')).length ≤ 1\n'
            '        ∧ ∀ c ∈ ("MiXedCase.Author".toList), c.toNat < 128)\n'
            '       ∧ normalizedRef ("MiXedCase.Author".toList) = "MiXedCase.author".toList))\n'
            + _IMPL,
            "prove_correct normalizeRef by\n"
            "  loom_solve <;>\n"
            "    simp_all [normalizedRef, isQualified, appPart, namePart, foldCase]"),
        "rationale": "the precondition admits the F2P-shaped reference (one "
                     "separator, all ASCII) AND the post-image is non-degenerate "
                     "there: it demands the application prefix verbatim and only "
                     "the model suffix folded ('MiXedCase.Author' -> "
                     "'MiXedCase.author'), not the whole-string fold a "
                     "prepatch/unsatisfiable spec would give. The in-region "
                     "assert must discharge (else PRECOND-TOO-STRONG or an "
                     "unsatisfiable obligation) and the frozen body keeps the "
                     "ensures obligation intact, so the module verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-echo-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # The cheapest wrong echo: return the reference UNCHANGED — no
        # normalization at all (weaker than even the prepatch fold).
        "module": _with_impl("    let result : List Char := ref\n    return result"),
        "refinement": "returning the reference unchanged corresponds to dropping "
                      "the canonicalization entirely (no case fold at all) — "
                      "weaker than the prepatch behaviour. A bare reference like "
                      "'Ab' would stay 'Ab' instead of resolving to its "
                      "case-folded canonical form, so every downstream lookup "
                      "that relies on the canonical (folded) label regresses and "
                      "the failing test still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = normalizedRef ref`: on an unqualified "
                     "reference the post-image folds the whole string, and the "
                     "impl returns it verbatim — they differ whenever the "
                     "reference contains an upper-case letter. Refuted at the "
                     "bare (unqualified) sub-domain.",
        "witness": _TESTER +
                   'example : normalizeRefTester ("Ab".toList) = false := by\n  decide\n',
    },
    {
        "id": "weak-lower-all",
        "kind": "uniqueness",
        "expect": "reject",
        # THE F2P discriminator: fold EVERY code point unconditionally — exactly
        # the prepatch behaviour, which lowers the application prefix too.
        "module": _with_impl(
            "    let result : List Char := ref.map Char.toLower\n    return result"),
        "refinement": "folding the WHOLE reference (including the application "
                      "prefix) is the pre-patch behaviour: a mixed-case "
                      "application label is lowered, producing a lazy reference "
                      "to an application that 'isn't installed' — precisely the "
                      "ValueError the issue reports and the failing test pins. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = normalizedRef ref`: on a QUALIFIED "
                     "reference the post-image keeps the prefix verbatim, and "
                     "the impl folds it — they differ whenever the prefix has an "
                     "upper-case letter (e.g. 'A.b' -> impl 'a.b', post-image "
                     "'A.b'). Refuted on the qualified-PREFIX sub-domain, where "
                     "this rival diverges from gold while agreeing on bare names "
                     "(there gold also folds the whole string).",
        "witness": _TESTER +
                   'example : normalizeRefTester ("A.b".toList) = false := by\n  decide\n',
    },
    {
        "id": "weak-keep-model-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: splits on the separator and keeps the prefix case, but
        # forgets to fold the model suffix — the whole qualified reference is
        # kept verbatim. Correct on bare names (there the frozen fold applies),
        # wrong on any qualified reference with an upper-case suffix.
        "module": _with_impl(
            "    let result : List Char :=\n"
            "      if ref.contains '.' then\n"
            "        ref\n"
            "      else\n"
            "        ref.map Char.toLower\n"
            "    return result"),
        "refinement": "keeping a qualified reference entirely verbatim (prefix "
                      "AND suffix) forgets to case-fold the model suffix, so a "
                      "reference like 'a.B' resolves to 'a.B' instead of 'a.b'. "
                      "The registry expects the model label folded, so the lazy "
                      "reference dangles on the qualified sub-domain — a wrong "
                      "resolution the prepatch-style whole-fold does not share. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = normalizedRef ref`: on a qualified "
                     "reference the post-image folds the suffix, and the impl "
                     "keeps it verbatim — they differ whenever the model suffix "
                     "has an upper-case letter (e.g. 'a.B' -> impl 'a.B', "
                     "post-image 'a.b'). Refuted on the qualified-SUFFIX "
                     "sub-domain, which the lower-all rival (right on the suffix, "
                     "wrong on the prefix) does not subsume.",
        "witness": _TESTER +
                   'example : normalizeRefTester ("a.B".toList) = false := by\n  decide\n',
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals — one of which is a frame-
# mutation probe). This bundle models the SAME single behaviour (the reference
# normalization), so there is no carrier narrowing beyond the frame class; every
# sibling case is accounted for below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder      -> pos-bind-parts                    PORTED
#   admiss-f2p-shaped-input         -> admiss-f2p-precondition-admits    PORTED
#   frame-mut-text                  -> (none)                            VACUOUS
#   weak-echo-input-verbatim        -> weak-echo-verbatim                PORTED
#   weak-prepatch-lower-all         -> weak-lower-all                    PORTED
#   partial-domain-keep-model-name  -> weak-keep-model-name              PORTED
#
# 5 ported, 1 vacuous = 6.
#
# PORTED (positive control): the sibling reorders the two branches of the
#   per-code-point conditional. The exact branch-swap does NOT survive here — the
#   frozen tactic script (`loom_solve; simp only [...]`) is tuned to the frozen
#   guard, and negating it forces a `whnf` heartbeat blow-up (measured). The
#   ARGUMENT — "a structurally different but faithful impl must verify" — is
#   carried by an equivalent reshape that DOES survive the frozen script:
#   binding the verbatim prefix and the folded suffix to typed locals before the
#   same decision. Verified to build.
# PORTED (admissibility): the sibling builds an F2P-shaped input and self-calls
#   to prove the precondition admits it. This bundle has real `require` clauses
#   (≤1 dot; all-ASCII), so the probe is live and is expressed directly as an
#   in-region assertion that the F2P-shaped reference satisfies both `require`
#   clauses AND that the post-image is non-degenerate there. The assert is live
#   (a false normalized-form claim leaves an unsolved `False` goal — verified
#   out-of-band); the frozen body follows it so the ensures obligation still
#   discharges. Verified to build.
# VACUOUS (frame-mutation): the sibling carries this as MANDATORY because `text`
#   holds a fractional heap permission (Acc(...,1/2)) an impl can illegally
#   write. This backend is referentially transparent and this bundle declares no
#   `mut` binder, so `ref` is an immutable value with no heap footprint — there
#   is no read-only input to overwrite and no substitute probe to build. Not
#   fabricated (per the porting map: this class is vacuous on Lean/Velvet).
# PORTED (the three value rivals): the sibling's echo-verbatim, lower-all
#   (prepatch) and keep-model-name rivals port directly onto the single
#   `out = normalizedRef ref` clause. Each carries a machine-checked witness that
#   ELABORATES against the rival and FAILS against the frozen solution (verified
#   with two real builds per case). The three witnesses probe the input binder
#   `ref` at three distinct structural points — a qualified reference with an
#   upper-case PREFIX ('A.b'), a bare unqualified reference ('Ab'), and a
#   qualified reference with an upper-case SUFFIX ('a.B') — so both arms of the
#   isQualified split and both sub-parts of the qualified arm are exercised, and
#   no rival is refuted at the same point as another. The two partial-domain
#   rivals are refuted on the exact sub-domains that separate them from gold
#   (lower-all wrong on the prefix / right on the suffix; keep-model wrong on the
#   suffix / right on bare names), so their sub-domain claims are machine-checked.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the transformation is modeled deeply), so there is nothing to probe.
AXIOM_TESTS = []
