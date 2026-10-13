"""properties.py — G-PBT falsification battery for psf__requests-2317 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct nativeToken`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, no ``require`` clause):

  nativeToken (token : List Char) return (out : List Char)
    ensures out = nativeSeq token          -- CONTENT (dominant, grounded)
    ensures out = token                    -- IDENTITY on the carried sequence
    ensures out.length = token.length      -- LENGTH (== not a wrapped rendering)

The method models the native-text coercion of an HTTP method token: the token
arrives either as native text or as a byte string carrying the token's ASCII
values, and the coercion must yield the token's OWN characters — the carried
sequence exactly, of the same length. ``nativeSeq`` is a fully-unfolded,
front-recursive pure ``def`` over the method's OWN argument (the per-character
identity map, ``nativeChar c = [c]``), and ``nativeSeq_id`` proves it equal to
the argument; the ``axioms`` region is empty, so there is no opaque answer key
an impl could echo (directive 8 — the post-image is grounded in the input).

ONE INPUT BINDER: ``token`` (the carried character/byte values). It is FREE, and
its sub-structure — its contents, its per-position characters, and its length —
is what the reject witnesses abuse. There is no ``is_bytes`` binder on this
carrier: the byte/text distinction the sibling carried as a second argument
collapses here because the modeled domain is ASCII, where a byte value equals
the code point of its ASCII decoding, so the single ``List Char`` carrier serves
both forms and the result is INDEPENDENT of how the token arrived (mapping.md
§2). The four reject witnesses drive ``token`` to FOUR distinct input points —
empty and three non-empty tokens with distinct leading characters — so the
manifest demonstrates the post-image's dependence on the token's length and on
each position, not on a single pinned shape (pts = 4).

CARRIER NOTE — WHY WITNESSES ARE LOOP-FREE, AND WHY THE FROZEN IMPL CANNOT BE
THE REFUTATION SUBJECT. The frozen impl is a backward ``while`` loop; its
extracted program compiles to well-founded recursion and does NOT reduce under
kernel ``decide`` (``nativeTokenTester`` gets stuck on the loop — the
``Decidable`` instance does not reduce to isTrue/isFalse against the frozen
solution). Every reject rival below is therefore written LOOP-FREE (a single
closed-form expression), so ITS extracted program reduces and
``nativeTokenTester args = false`` decides against it: half 1 (the witness
ELABORATES against the rival) is a genuine, kernel-checked counterexample.

Half 2 is where the frozen impl is USELESS as a subject, and an earlier revision
of this file got that backwards. It claimed the stuck ``decide`` against gold
made half 2 hold "by construction", i.e. treated the stuck reduction AS the
discrimination. It is the opposite: a failure the kernel never evaluated is
evidence of nothing. Measured, four builds per case with
``scripts/lean_verify.sh`` — against the frozen solution the witness
(``… = false``) and a FORGERY differing only in flipping the claim
(``… = true``, i.e. asserting the rival is CORRECT at that token) fail with the
SAME diagnostic, ``Tactic `decide` failed … did not reduce to `isTrue` or
`isFalse```, the two logs differing only in the echoed claim text. So gold's
exit code carries no information about the claim, and a forged witness would
clear a gold-subject check exactly as loudly as a real one.

Hence every reject case below names an explicit ``witness_reference``: the
``pos-direct-model`` impl — an independently VERIFYING impl of this same frozen
spec (it is this battery's own soundness positive, and the gate re-checks both
that it shares the spec and that it verifies before using it) which is loop-free
and therefore kernel-reducible. Against THAT subject the error tracks the claim,
which is what a discriminator means: the witness fails with ``Tactic `decide`
proved that the proposition nativeTokenTester <tok> = false is false`` (a
semantic refutation of the concrete claim — the kernel evaluated the tester and
got ``true``), while the flipped claim ``… = true`` builds GREEN (exit 0).
Refuting against a verifying impl is sound for the reason gold was meant to be:
an impl the verifier accepts cannot violate its own spec, so a genuine "the spec
is violated at this token" cannot hold there. The reference is named rather than
left to the gate's own positives-fallback so the recorded attestation says WHICH
impl earned each rejection instead of depending on manifest order.

The carrier is fully transparent (tokens are concrete ``List Char`` literals via
``"…".toList``), so no opaque leaf blocks reduction and no conditioning on a
hypothesis is needed — every witness is a concrete literal token, and no
consistency probe is required.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical impls (return the grounded model directly with no
    loop; and keep the backward loop but inline the indexed element read) must
    verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the sibling self-asserts an F2P-shaped token satisfies its
    fractional-permission precondition. This backend has NO ``require`` and no
    permission surface, so that probe is degenerate; the residual admissibility
    risk here is a DEGENERATE post-image. ``admiss-nondegenerate`` discharges an
    in-region ``assert`` at a concrete F2P-shaped method token pinning that the
    modeled coercion yields the token's own characters, length preserved; the
    surrounding impl is kept verbatim so the method's own obligation still
    discharges.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries
    two MANDATORY frame-mutation rivals because the token carrier is held at a
    fractional heap permission (``Acc(.,1/2)``) an impl can illegally overwrite
    (write an element / append to it). Lean/Velvet are referentially
    transparent: ``token`` is an immutable ``List Char`` value declared read-only
    (not ``mut``), there is no heap, no aliasing, no ``Old``, and no permission
    system. There is no read-only input to overwrite and no frame clause to
    violate, so the class has no carrier analogue; NOT ported (fabricating a
    substitute would test nothing).
  * DIVERGENCE / NON-TERMINATION: CLOSED BY THE SEMANTICS, not vacuous and not a
    hole. The sibling carries no such case, so there is nothing to port. "A
    non-terminating impl cannot be written at all" is withdrawn: a rival owns the
    whole impl region, and the frozen body is itself a loop (carrying
    ``decreasing i``), so a diverging rival is writable. It is REJECTED when it is.
    This bundle sets ``set_option loom.semantics.termination "total"``, under which
    a postcondition is claimed of ALL runs, not only terminating ones, so the
    verifier demands a decreasing measure on every loop AND discharges its descent;
    the option cannot drift from the file's ``open TotalCorrectness DemonicChoice``,
    because the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced loop with NO measure is refused at
    the ``method`` declaration
    (``Decreasing annotations are required in total correctness semantics``), and a
    loop that CARRIES a non-decreasing measure
    (``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z``, body
    ``z := z + 1``) is refused on the measure's own goal:
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. No known hole to record.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to a fully-unfolded ``def`` (``nativeSeq``) over the method's own
    argument (and to the argument itself); the ``axioms`` region is empty, so
    there is no answer-key term a wrong impl could echo without doing the work.
    The cheapest correct impl copies the token, which the positive controls do.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (the byte-wrap rendering; the
    dropped final character; a spurious character on the empty token; or a
    corrupted leading character).
"""
from pathlib import Path

INSTANCE = "psf__requests-2317"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the elided impl region and unique in the file
# ---- (both facts asserted at load). Every reject rival and the direct-model
# ---- positive swap on this block.
_IMPL = """    -- impl-start
    let mut result : List Char := []
    let mut i := token.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ token.length
      invariant result = nativeSeq (token.drop i)
      done_with i = 0
      decreasing i
    do
      let c := token[i - 1]!
      result := nativeChar c ++ result
      i := i - 1
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the loop-body step (element read + front-prepend), for the in-loop
# ---- reshape positive. Unique in the file, wholly inside the impl region. ----
_LOOP_STEP = ("      let c := token[i - 1]!\n"
              "      result := nativeChar c ++ result")
assert _BASE.count(_LOOP_STEP) == 1, "loop-step anchor drift"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- correct reshape may retune THIS block; rivals leave it as the flat
# ---- `loom_solve` so the wrong impl leaves the postcondition goal unsolved and
# ---- the rival MODULE fails to build (what expect="reject" needs). The witness,
# ---- not the module build, is what attributes the rejection to the spec.
_PROOF_GOLD = """prove_correct nativeToken by
  loom_solve
  rw [nativeSeq_drop_step token i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the impl is a single expression there is no
# ---- loop invariant to peel, so `loom_solve` alone discharges the equalities
# ---- (for a correct reshape) or leaves the goal unsolved (for the reject
# ---- rivals, whose MODULE build then FAILS — which is the point). Reject rivals
# ---- and the direct-model positive retune the proof to this shape.
_PROOF_FLAT = "prove_correct nativeToken by\n  loom_solve"


def _rewrite_impl(new_block, proof=_PROOF_FLAT):
    """Full variant: whole impl block replaced, proof retuned to the flat shape."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `nativeTokenTester token = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped. Every rival is a
# ---- loop-free expression so `decide` reduces its extracted program, while the
# ---- SAME `decide` gets stuck against the frozen loop-based gold.
def _witness(call):
    return ("extract_program_for nativeToken\n"
            "prove_precondition_decidable_for nativeToken\n"
            "prove_postcondition_decidable_for nativeToken\n"
            "derive_tester_for nativeToken\n\n"
            f"example : {call} = false := by\n  decide\n")


# ---- the refutation SUBJECT for every reject case (see the CARRIER NOTE). The
# ---- frozen loop-based impl cannot serve: its `decide` is stuck for EVERY claim,
# ---- so its exit code says nothing about the claim (measured — the witness and
# ---- the flipped claim fail identically there). This impl returns the grounded
# ---- model directly, so it is loop-free and KERNEL-REDUCIBLE, and it is the
# ---- `pos-direct-model` positive, i.e. an impl this battery independently
# ---- requires to VERIFY against the frozen spec (the gate re-checks both facts).
# ---- Against it the witness is refuted semantically and the flipped claim builds
# ---- green, so the exit code tracks the claim.
_WITNESS_SUBJECT = _rewrite_impl(
    "    -- impl-start\n"
    "    return nativeSeq token\n"
    "    -- impl-end")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Both confirmed with a real build (pos-direct-model with
    # the flat `loom_solve`; pos-inline-elem-read with the frozen loop proof).
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly
        # (no loop at all) — maximally structurally different from the gold
        # backward fold. `out` IS `nativeSeq token`, so the CONTENT clause holds
        # definitionally, `nativeSeq_id` gives IDENTITY, and `nativeSeq` preserves
        # LENGTH; the reproof is a bare `loom_solve` (no loop invariant to peel).
        # Same source as `_WITNESS_SUBJECT`: this positive IS the refutation
        # subject every reject case names, so the gate's check that it verifies is
        # also the check that licenses it as a witness_reference.
        "module": _WITNESS_SUBJECT,
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`nativeSeq token` directly (no loop). `out` IS that model so CONTENT "
            "(`out = nativeSeq token`) holds on the whole domain, `nativeSeq_id` "
            "discharges IDENTITY (`out = token`), and the per-character map "
            "preserves LENGTH; the reproof is the flat `loom_solve`. If this fails "
            "to verify the spec is over-fit to the accumulator-loop code shape "
            "(SPEC-TOO-STRONG). Also the honest no-ungrounded-echo control: "
            "computing the model IS the real work. (Sibling: pos-append-shape — a "
            "different executable accumulation; here the cheapest reshape is a "
            "direct return.)"),
    },
    {
        "id": "pos-inline-elem-read",
        "kind": "soundness",
        "expect": "verify",
        # In-loop reshape: inline the indexed element read into the front-prepend
        # instead of naming it in a `let`. Same backward accumulator loop, same
        # invariants and value flow, so the frozen loop proof still closes verbatim.
        "module": _swap(
            _BASE, _LOOP_STEP,
            "      result := nativeChar token[i - 1]! ++ result"),
        "rationale": (
            "inlining the indexed element read (`token[i-1]!`) into the "
            "front-prepend leaves the backward loop, both invariants and the "
            "assembled value unchanged, so all three ensures clauses still hold "
            "and the frozen proof closes verbatim. A correct executable-shape "
            "variant must verify, else the postcondition is SPEC-TOO-STRONG over "
            "the shape of the loop body. (Sibling: pos-isbytes-split — a "
            "structurally different but identical forward copy; here, with no "
            "`is_bytes` binder, the analogue is an in-loop element-read reshape.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so the sibling's "an
    # F2P-shaped token satisfies the half-permission precondition" probe is
    # degenerate here (every input is admitted). Re-aimed at the residual risk on
    # a total domain: that the post-image is DEGENERATE at the interesting point.
    # This case discharges a live in-region `assert`, at a concrete F2P-shaped
    # method token, that the modeled coercion yields the token's OWN characters
    # (`nativeSeq "GET" = "GET"`) with the length preserved — the exact behaviour
    # the fix demands. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the proof gains a `decide` arm to clear the
    # assert goal (allowed — the tactic body is elided from the spec view). The
    # assert is live: a false claim about the same point leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      nativeSeq \"GET\".toList = \"GET\".toList ∧\n"
                  "      (nativeSeq \"GET\".toList).length = (\"GET\".toList).length))\n"),
            _PROOF_GOLD,
            "prove_correct nativeToken by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [nativeSeq_drop_step token i (by omega) (by omega)]; simp_all)"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "input: a concrete method token must coerce to its OWN characters "
            "(`nativeSeq \"GET\" = \"GET\"`, the token itself, not a wrapped "
            "rendering) with the length preserved. The in-region assert must "
            "discharge (else the obligation is degenerate at the point the fix "
            "cares about); the impl is kept verbatim so the method's own ensures "
            "clauses still verify. (Sibling: admiss-shape, re-aimed from "
            "precondition admissibility to post-image non-degeneracy since this "
            "backend has no `require` and no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong loop-free impls sharing the
    # frozen spec that MUST be rejected, each with a machine-checked refutation
    # witness at a DISTINCT concrete token and the refinement argument that its
    # faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-prepatch-bytes-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gold bug (Solution_prepatch.lean): render the token as its TEXTUAL
        # OBJECT description — the carried characters wrapped with a leading marker
        # character and a surrounding pair of quote characters, a sequence three
        # characters longer than the token.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return 'b' :: '\\'' :: (token ++ ['\\''])\n"
            "    -- impl-end"),
        "refinement": (
            "this IS the pre-change behaviour reproduced by Solution_prepatch.lean: "
            "a byte-carried token is rendered as its five-character textual-object "
            "description (a leading marker character, a surrounding pair of quotes) "
            "instead of the decoded token, a sequence three characters longer than "
            "the token. The unpatched repo sends that literal as the request method "
            "and the server 404s — precisely what test_encoded_methods (r.ok) "
            "rejects — so a faithful counterpart would NOT resolve the F2P."),
        "rationale": (
            "REJECT from the dominant CONTENT clause `out = nativeSeq token` (and "
            "IDENTITY `out = token`, and LENGTH — the wrapped rendering is length "
            "len+3): the token's own characters are demanded, not the wrapped "
            "object. This is the exact G-DIFF behaviour; verifying would be "
            "SPEC-TOO-WEAK (the change is not sensed). Refuted at \"GET\" — a "
            "non-empty method token whose wrapped rendering diverges immediately."),
        "witness": _witness('nativeTokenTester "GET".toList'),
        # The frozen impl's `decide` is stuck for every claim, so it cannot be
        # the refutation subject; refute against the verifying loop-free impl,
        # where the error tracks the claim. See the CARRIER NOTE.
        "witness_reference": _WITNESS_SUBJECT,
    },
    {
        "id": "weak-truncate-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one: copy all but the LAST character (loop bound n-1 modeled as
        # `token.take (len-1)`). Vacuously correct on the empty token and on every
        # prefix, diverging only on the final index.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (token.take (token.length - 1))\n"
            "    -- impl-end"),
        "refinement": (
            "dropping the final character turns GET->GE, PUT->PU — an invalid HTTP "
            "method the server 404s. A real patch truncating the coerced method "
            "fails test_encoded_methods (r.ok) and the redirect/POSTBIN F2P tests "
            "that carry real methods, so it would NOT resolve. PARTIAL-DOMAIN: it "
            "is vacuously correct on the empty token and on every prefix, diverging "
            "only on the last index — a boundary a byte-fuzzer misses."),
        "rationale": (
            "REJECT from CONTENT/IDENTITY (`out = nativeSeq token = token`) and "
            "LENGTH (`out.length = token.length`): the truncation gives length "
            "len-1 != len and drops the final character on any non-empty token. "
            "Verifying would be SPEC-TOO-WEAK on the last-element sub-domain. "
            "Refuted at \"PUT\" — a non-empty token distinct from the other "
            "witnesses, where the dropped final 'T' makes the lists differ."),
        "witness": _witness('nativeTokenTester "PUT".toList'),
        # The frozen impl's `decide` is stuck for every claim, so it cannot be
        # the refutation subject; refute against the verifying loop-free impl,
        # where the error tracks the claim. See the CARRIER NOTE.
        "witness_reference": _WITNESS_SUBJECT,
    },
    {
        "id": "weak-pad-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every NON-EMPTY token, but for the EMPTY token returns a
        # one-character ['G'] instead of []. PARTIAL-DOMAIN on the length-0
        # sub-domain: the LENGTH clause fails (1 != 0) only when the token is empty.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (if token = [] then ['G'] else token)\n"
            "    -- impl-end"),
        "refinement": (
            "emitting a spurious character for the empty token synthesises a "
            "one-character method from an empty token, diverging from the coercion "
            "(which returns the empty token unchanged). A real patch with this "
            "special case would carry a fabricated method where none was supplied, "
            "so it does NOT faithfully implement the coercion and would NOT "
            "resolve. PARTIAL-DOMAIN on len==0 — a boundary the non-empty rivals "
            "never reach."),
        "rationale": (
            "REJECT from the LENGTH clause `out.length = token.length` (and CONTENT "
            "`out = token`): for the empty token the impl returns length 1 != 0 "
            "(and ['G'] != []). It is correct on every non-empty token, so it "
            "isolates the empty-token boundary; verifying would be SPEC-TOO-WEAK "
            "there. Refuted at \"\" (the empty token) — the ONLY witness that "
            "drives `token` to length 0, so it is what makes the length clause "
            "load-bearing on the empty sub-domain."),
        "witness": _witness('nativeTokenTester "".toList'),
        # The frozen impl's `decide` is stuck for every claim, so it cannot be
        # the refutation subject; refute against the verifying loop-free impl,
        # where the error tracks the claim. See the CARRIER NOTE.
        "witness_reference": _WITNESS_SUBJECT,
    },
    {
        "id": "weak-corrupt-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Copy faithfully EXCEPT force the first character to 'G'. For a token
        # whose first character is already 'G' this is the identity; for any other
        # it corrupts index 0 while keeping the length. Isolates the CONTENT
        # clause independent of length.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (match token with | [] => [] | _ :: cs => 'G' :: cs)\n"
            "    -- impl-end"),
        "refinement": (
            "forcing the first character to 'G' corrupts every method whose first "
            "character isn't 'G' (POST->GOST, PUT->GUT). A real patch normalising "
            "the leading character would change the HTTP method sent, failing the "
            "POSTBIN/redirect F2P tests and test_encoded_methods, so it would NOT "
            "resolve. PARTIAL-DOMAIN on the first element (length preserved)."),
        "rationale": (
            "REJECT from CONTENT/IDENTITY (`out = nativeSeq token = token`): the "
            "result's first character is 'G' while `token[0]` is not, so the lists "
            "differ at index 0 even though the LENGTH clause is satisfied. This "
            "isolates the value-level pin (a single mismatched index must be "
            "caught); verifying would be SPEC-TOO-WEAK on index 0. Refuted at "
            "\"POST\" — a non-empty token whose leading 'P' the rival overwrites, "
            "distinct from the other witnesses."),
        "witness": _witness('nativeTokenTester "POST".toList'),
        # The frozen impl's `decide` is stuck for every claim, so it cannot be
        # the refutation subject; refute against the verifying loop-free impl,
        # where the error tracks the claim. See the CARRIER NOTE.
        "witness_reference": _WITNESS_SUBJECT,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (2
# soundness positives, 1 admissibility, 6 uniqueness rivals — 2 of which are the
# MANDATORY frame-mutation rivals) plus an EMPTY AXIOM lane (AXIOM_TESTS = []).
# The sibling models `native_method(content: List[int], is_bytes: bool)` over a
# `List[int]` code-point carrier granted at a FRACTIONAL heap permission
# (`Acc(list_pred(content), 1/2)`), with the result pinned by a verified forward
# `while` loop over a @Pure `ToSeq` prefix helper. This backend models the SAME
# purely-functional core over `List Char` (`nativeSeq`/`nativeChar`, proven
# identity by `nativeSeq_id`) with a backward fold and NO permission surface. The
# `is_bytes` binder collapses (the modeled ASCII domain unifies the byte/text
# forms — mapping.md §2), so there is a single `token` binder here.
#
#   sibling case              kind          -> here                     disposition
#   ------------------------------------------------------------------------------------
#   pos-isbytes-split         soundness     -> pos-inline-elem-read      RE-AIMED (no is_bytes)
#   pos-append-shape          soundness     -> pos-direct-model          PORTED (reshape)
#   admiss-shape              admissibility -> admiss-nondegenerate      RE-AIMED
#   frame-mut-overwrite       uniqueness    -> (none)                    VACUOUS
#   frame-mut-extend          uniqueness    -> (none)                    VACUOUS
#   weak-prepatch-bytes       uniqueness    -> weak-prepatch-bytes-wrap  PORTED (the bug)
#   weak-truncate-last        uniqueness    -> weak-truncate-last        PORTED
#   weak-pad-empty            uniqueness    -> weak-pad-empty            PORTED
#   weak-uppercase-first      uniqueness    -> weak-corrupt-first        PORTED
#   AXIOM_TESTS ([])          axiom         -> (none)                    N/A (G-AX)
#
# 4 uniqueness ported, 1 soundness ported + 1 re-aimed, 1 admissibility re-aimed;
# 2 uniqueness vacuous; axiom lane empty on both sides.
#
# PORTED (the four value-level rivals): weak-prepatch-bytes ->
#   weak-prepatch-bytes-wrap (the exact pre-patch b'...'-wrap, now the whole
#   textual-object rendering since the ASCII carrier is unified; refuted at "GET",
#   the F2P discriminator). weak-truncate-last -> weak-truncate-last (drop the
#   final character; refuted at "PUT"). weak-pad-empty -> weak-pad-empty (spurious
#   character on the empty token; refuted at ""). weak-uppercase-first ->
#   weak-corrupt-first (force the leading character; refuted at "POST").
# RE-AIMED (pos-isbytes-split -> pos-inline-elem-read): the sibling's positive
#   splits on `is_bytes` into two identical copy arms to show the result is
#   independent of the flavour. This carrier has NO `is_bytes` binder (the byte/
#   text distinction collapses on the ASCII domain — mapping.md §2), so an
#   is_bytes split is not expressible; the same "correct executable-shape reshape
#   must verify" content is carried by an in-loop element-read reshape that keeps
#   the backward loop and the frozen proof. pos-append-shape (a different
#   accumulation shape) -> pos-direct-model (the cheapest structural reshape on
#   this backend: return the grounded model directly, no loop).
# RE-AIMED (admiss-shape -> admiss-nondegenerate): the sibling asserts an
#   F2P-shaped token satisfies its half-permission Requires and asserts the shape
#   on the built result. This backend has NO `require` (the operation is total on
#   its carrier) and no permission surface, so the precondition probe is
#   degenerate; the sharper residual risk is a DEGENERATE post-image, so the case
#   is re-aimed to a live in-region assert pinning that the coercion of a concrete
#   method token yields the token's own characters, length preserved.
# VACUOUS (frame-mut-overwrite, frame-mut-extend): the sibling's two MANDATORY
#   frame-mutation rivals write an element of / append to the half-permission
#   `content` input and are rejected for INSUFFICIENT PERMISSION. This backend is
#   referentially transparent: `token` is an immutable `List Char` value declared
#   read-only (not `mut`), there is no heap, no aliasing, no `Old`, and no
#   permission system. There is no read-only input to overwrite and no frame
#   clause to violate, so the class has no carrier analogue. Omitted as a genuine
#   carrier fact, NOT fabricated (porting map: this class is vacuous on a
#   referentially-transparent backend).
# DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and
#   a diverging rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# AXIOM_TESTS: empty on both sides. The sibling records AXIOM_TESTS = [] (no
#   consumed axiom; `to_native_string` is an A-reference deep model validated by
#   axiom_check.py / G-AX). This bundle likewise consumes no `axiom` (the coercion
#   is modeled deeply as `nativeSeq`, an A-reference — meta.json axioms == []), so
#   there is nothing for the axiom lane to probe. This gate ignores AXIOM_TESTS
#   regardless.
#
# BINDER / CLAUSE COVERAGE. The sole input binder `token` (`List Char`) is moved
#   across the four reject witnesses to FOUR distinct input points (pts = 4):
#     * weak-prepatch-bytes-wrap   "GET"    (non-empty; length + content diverge)
#     * weak-truncate-last         "PUT"    (non-empty; final index dropped)
#     * weak-pad-empty             ""       (EMPTY token; length 0 sub-domain)
#     * weak-corrupt-first         "POST"   (non-empty; leading index corrupted)
#   So `token` ranges over {empty, "GET", "PUT", "POST"} — length {0, 3, 4} and
#   distinct leading characters — no single pinned shape. All three top-level
#   ensures clauses are attacked: CONTENT/IDENTITY (`out = nativeSeq token`,
#   `out = token`) by every rival, most sharply by weak-corrupt-first (a single
#   mismatched index with length preserved) and weak-prepatch-bytes-wrap; LENGTH
#   (`out.length = token.length`) by weak-truncate-last (len-1 on non-empty) and
#   weak-pad-empty (len 1 on the empty token). No independent clause is left
#   unattacked and no binder is pinned at a single value across the reject set.
AXIOM_TESTS = []
