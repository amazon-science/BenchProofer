"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7440 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical header) and swaps
in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method, ``registerGlossaryName termText``,
computing the cross-reference key under which a term is recorded in (and later
reported from) the project-wide object registry. There is NO ``require`` clause
(the admitted domain is total over all term texts) and ONE top-level
postcondition clause:

  (1) out = registeredKey termText
        the key is the term's text EXACTLY AS WRITTEN — character-for-character,
        case preserved. ``registeredKey`` is the identity on the term text: a
        fully unfolded function of the method's own single argument, with no
        opaque answer key to echo.

``termText`` is a FREE input; the clause must hold for every value it takes,
which is what makes the partial-domain rivals below refutable at a concrete
point. The single distinguishing operation is per-code-point case folding: the
observable behaviour turns on whether even ONE upper-case ASCII letter of the
term text is rewritten or a position is dropped/duplicated before the key is
recorded, because the failing scenario feeds an upper-case term and asserts the
recorded key is that term unchanged.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because a read-only input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent: every parameter is an
    immutable value (no ``mut`` binder on any input in this bundle), there is no
    heap and no aliasing, so there is no read-only input to mutate and no
    substitute probe to build. Not fabricated. (See the module footer.)
  * UNGROUNDED-ORACLE ECHO — N/A. The single clause is the identity on the
    method's own argument (``registeredKey`` is a concrete ``def`` in the
    ``pure`` region; the ``axioms`` region declares no ``axiom`` — the registry
    round-trip is a G-AX deep-model reference, not a consumed contract). There is
    no opaque wrong value an impl could echo; the positive controls are honest
    cheapest-reshape controls instead.
  * PARTIAL-DOMAIN / VALUE — APPLIES. A rival correct on part of the term-text
    domain but diverging on a sub-domain: folding every ASCII letter (the pre-fix
    behaviour), folding only the leading letter, or dropping the final code
    point. Each attacks the one clause and is refuted where it diverges.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, so a witness reaches the
postcondition through Velvet's own tester machinery (``extract_program_for`` …
``derive_tester_for``): ``registerGlossaryNameTester termText = false`` says the
extracted program's result violates the postcondition at that concrete input.
The frozen impl computes the IDENTITY, so at every input its tester is ``true``
and a ``= false`` statement CANNOT elaborate against gold (the discrimination
half: the ``decide`` proves the proposition false and the witness is rejected).
A wrong rival's tester is ``false`` at an input where it diverges, so ``= false``
elaborates against the rival (the refutation half). Every probed input is a
concrete short ASCII literal so ``decide`` reduces without opaque terms. No
``sorry`` / ``admit`` / ``native_decide`` is used; the discrimination is genuine
(verified during authoring: rival build exit 0, gold build exit != 0, for all
three witnesses).

BINDER / CLAUSE COVERAGE. There is ONE input binder (``termText``) and ONE
clause. The three reject witnesses probe three DISTINCT non-empty term texts,
varying that binder in content and length: ``"aB"`` (a trailing upper-case
letter, lower-case first — where a leading-only fold AGREES with gold, so it is
uniquely the whole-string-fold rival's), ``"Ab"`` (a leading upper-case letter),
and ``"ab"`` (all lower-case, refuting the drop-last rival on length alone). No
two rivals share a refutation point; the near-miss leading-fold rival is given a
point the whole-string-fold rival does not reach.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the object
registry's record/enumerate round-trip is modeled DEEPLY as ``registeredKey``,
an A-reference validated == the real component by axiom_check.py (G-AX), not a
consumed contract). Nothing for this gate to probe; the gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7440"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The single executable line of the frozen impl; it
# ---- lies wholly inside the `-- impl-start` / `-- impl-end` region and is
# ---- unique in the file (both facts asserted at load by _swap). Every reject
# ---- rival and every positive control replaces exactly this line. The
# ---- admissibility case prepends an in-region assert to it.
_IMPL = "    return registeredKey termText\n"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. Below is the frozen script, unique in the file. Only the
# ---- admissibility case retunes it (to also clear its added assert goal).
_PROOF = "prove_correct registerGlossaryName by\n  loom_solve"


# ---- witness preamble. A witness reaches the method's postcondition through
# ---- Velvet's tester machinery; checked in a file whose `prove_correct` block
# ---- has been stripped, so no tactic script can mask the verdict. The tactics
# ---- come from `Velvet.Std` (the frozen import), so nothing extra is needed.
_TESTER = (
    "extract_program_for registerGlossaryName\n"
    "prove_precondition_decidable_for registerGlossaryName\n"
    "prove_postcondition_decidable_for registerGlossaryName\n"
    "derive_tester_for registerGlossaryName\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the byte-identical `prove_correct`
    # header and the frozen tactic script (the clause is a point-wise equality,
    # so no reshape here needs a new lemma or a retuned proof).
    # =====================================================================
    {
        "id": "pos-bind-key-local",
        "kind": "soundness",
        "expect": "verify",
        # Bind the key to a typed local before returning it. Same value flow;
        # the returned value is `registeredKey termText` on every input.
        "module": _swap(
            _BASE, _IMPL,
            "    let key : List Char := registeredKey termText\n"
            "    return key\n"),
        "rationale": "binding the recorded key to a typed local before returning "
                     "it leaves the returned value unchanged, so clause (1) "
                     "`out = registeredKey termText` still discharges; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-inline-identity",
        "kind": "soundness",
        "expect": "verify",
        # Return the argument directly, inlining the identity the key computation
        # denotes. Structurally distinct surface (no reference to the pure def),
        # same value flow; must verify.
        "module": _swap(_BASE, _IMPL, "    return termText\n"),
        "rationale": "returning the term text directly (inlining the identity the "
                     "key computation denotes) yields exactly `registeredKey "
                     "termText`, so clause (1) still holds definitionally; a "
                     "correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY. The method has no `require` clause, so the usual "a normal
    # input satisfies the precondition" probe is vacuous — nothing could exclude
    # an F2P-shaped input. It is re-aimed at the residual admissibility risk on a
    # total domain: that the postcondition is UNSATISFIABLE / DEGENERATE at the
    # interesting point. The case discharges an in-region `assert`, at fully
    # concrete inputs, SYMBOLICALLY establishing that the recorded-key spec is
    # non-degenerate at the discriminating point: for an upper-case term it
    # demands the key be that term unchanged, and it distinguishes that key from
    # the case-folded form. The surrounding impl is kept verbatim so the method's
    # own obligation discharges too; the proof body is retuned only to clear the
    # extra assert goal by `decide` (allowed — the tactic body is elided from the
    # spec view). The assert is live, not decoration: a false claim about the
    # same point leaves an unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-key-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "    assert (with_name_prefix `admiss\n"
                "      (registeredKey \"TERM2\".toList = \"TERM2\".toList ∧\n"
                "       registeredKey \"TERM2\".toList ≠ registeredKey \"term2\".toList))\n"
                + _IMPL),
            _PROOF,
            "prove_correct registerGlossaryName by\n"
            "  loom_solve\n"
            "  simp only [registeredKey]\n"
            "  decide"),
        "rationale": "the recorded-key spec is satisfiable AND non-degenerate at "
                     "the discriminating point: for an upper-case term it demands "
                     "the key be that term unchanged, and it distinguishes that "
                     "key from the case-folded form (so the clause genuinely "
                     "separates the case the fix targets from its pre-fix "
                     "alternative). The in-region assert must discharge (else the "
                     "obligation is unsatisfiable/degenerate at that point); the "
                     "impl is kept verbatim so the ensures clause still discharges "
                     "too, with the tactic body retuned only to clear the assert.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each loop-free (so its extracted program reduces
    # under `decide`) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument for why its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-fold-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Case-fold EVERY ASCII letter of the term text — the pre-fix behaviour.
        # Correct on all-lower-case terms, wrong on any term with an upper-case
        # letter.
        "module": _swap(_BASE, _IMPL, "    return termText.map Char.toLower\n"),
        "refinement": "this IS the pre-fix behaviour: fold the whole term text to "
                      "lower case before recording it. The failing scenario feeds "
                      "an upper-case term and asserts the recorded key is that "
                      "term unchanged; this rival records the lower-cased form, so "
                      "the enumerate step reports the folded key and the assertion "
                      "still fails. It would NOT resolve (it is the original bug).",
        "rationale": "REJECT from clause (1) `out = registeredKey termText`: any "
                     "upper-case ASCII letter is shifted, so the key differs from "
                     "the term text. Refuted at \"aB\" (a trailing upper-case "
                     "letter, lower-case first) — the point where a leading-only "
                     "fold would AGREE with gold, so this rival's witness sits "
                     "where the near-miss weak-fold-first cannot.",
        "witness": _TESTER +
                   'example : registerGlossaryNameTester "aB".toList = false := by\n'
                   "  decide\n",
    },
    {
        "id": "weak-fold-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Case-fold only the FIRST code point, copy the rest verbatim. A NEAR-MISS
        # of weak-fold-all: correct on every term whose leading letter is already
        # lower case (and agrees with weak-fold-all only on single-char upper
        # terms), so it is given a distinct refutation point where it — but not
        # weak-fold-all's witness — is what the spec catches.
        "module": _swap(
            _BASE, _IMPL,
            "    return (termText.take 1).map Char.toLower ++ termText.drop 1\n"),
        "refinement": "folding only the leading letter records a key whose first "
                      "character is lower-cased; for the upper-case failing term "
                      "the enumerate step reports the leading-folded key, not the "
                      "term unchanged, so the assertion still fails. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause (1) `out = registeredKey termText`: the "
                     "leading upper-case letter is shifted while the rest is "
                     "verbatim. Refuted at \"Ab\" (a leading upper-case letter) — "
                     "distinct from weak-fold-all's \"aB\", where this rival "
                     "agrees with gold, so the near-miss is demonstrated on the "
                     "sub-domain it alone abuses.",
        "witness": _TESTER +
                   'example : registerGlossaryNameTester "Ab".toList = false := by\n'
                   "  decide\n",
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the final code point (off-by-one). Correct only on the empty term;
        # wrong on every non-empty term regardless of case, so it is refuted on an
        # ALL-LOWER-CASE term — the sub-domain both fold rivals leave alone,
        # moving the term-text binder to a value neither fold witness reaches.
        "module": _swap(_BASE, _IMPL, "    return termText.dropLast\n"),
        "refinement": "omitting the final code point records a key one character "
                      "short of the term text; the enumerate step reports the "
                      "truncated key, so the assertion pinning the whole term "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from clause (1) `out = registeredKey termText`: the "
                     "key is one code point shorter than the term text on every "
                     "non-empty term. Refuted at \"ab\" (all lower case) — a "
                     "length/content divergence the case-fold rivals cannot "
                     "produce, so the term-text binder is varied to a point "
                     "neither fold witness reaches.",
        "witness": _TESTER +
                   'example : registerGlossaryNameTester "ab".toList = false := by\n'
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals) plus an empty AXIOM lane, all
# against the SINGLE modeled behaviour (the registration-key computation). This
# bundle models that same single behaviour, so the port is close to one-for-one
# on the spec lane.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-reshaped-copy       -> pos-bind-key-local              PORTED
#   admissibility-F2P-TERM2         -> admiss-key-nondegenerate        RE-AIMED
#   frame-mutation-write-input      -> (none)                          VACUOUS
#   partial-fold-first-char         -> weak-fold-first                 PORTED
#   partial-fold-all-prepatch       -> weak-fold-all                   PORTED
#   partial-drop-last               -> weak-drop-last                  PORTED
#
# 4 ported, 1 re-aimed, 1 vacuous. A SECOND soundness positive
# (pos-inline-identity) is added for robustness on the single obligation.
#
# VACUOUS (frame-mutation-write-input): the sibling rejects an impl that WRITES
#   to a read-only 1/2-permission input to satisfy the postcondition vacuously.
#   This backend is referentially transparent and this bundle declares no `mut`
#   binder on any input, so there is no read-only input to overwrite and no
#   substitute probe. Not fabricated (per the porting map: this class is vacuous
#   on Lean/Velvet).
# RE-AIMED (admissibility): the sibling's self-call witnesses that the fractional
#   precondition admits the F2P upper-case term. No method here has a `require`
#   clause, so that probe is vacuous. It is re-aimed at the residual
#   admissibility risk on a total domain — that the recorded-key obligation is
#   unsatisfiable / degenerate at the discriminating point — via an in-region
#   assert that pins the upper-case key verbatim and distinguishes it from the
#   folded form.
#
# CARRIER NOTE. The sibling models the term text as `List[int]` (code points) and
#   its rivals shift code points by +32; here the carrier is `List Char` and the
#   fold is `Char.toLower`, but the adversarial argument is identical (an
#   upper-case ASCII letter must survive verbatim). The frozen impl is the
#   IDENTITY and loop-free, so unlike a fold-based frozen impl the witness
#   discrimination comes from VALUES, not loop-unreducibility: at every input the
#   identity's tester is `true`, so a `= false` witness fails against gold, while
#   a wrong rival's tester is `false` where it diverges, so the same witness
#   elaborates against the rival. Verified during authoring for all three.
#
# COVERAGE. One binder (`termText`), one clause. The three reject witnesses probe
#   three DISTINCT non-empty term texts and vary that binder in content and
#   length: "aB" (weak-fold-all, where a leading-only fold agrees with gold),
#   "Ab" (weak-fold-first, the near-miss's own sub-domain), "ab" (weak-drop-last,
#   all lower case — a length divergence neither fold rival produces). pts = 3
#   distinct input points; no two rivals share a refutation point, and the
#   near-miss weak-fold-first is refuted at a point weak-fold-all does not reach.
#
# AXIOM_TESTS: dropped. The sibling's axiom lane is already empty (no
#   @ContractOnly axioms consumed); the object-registry round-trip is a G-AX
#   deep-model reference (`registeredKey`), not a consumed contract, so there is
#   nothing here for this gate to probe. The gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
