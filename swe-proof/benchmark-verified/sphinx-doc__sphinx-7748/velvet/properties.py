"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7748 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the one ``-- impl-start`` /
``-- impl-end`` span is changed, which the consumer spec view elides — so
``markers.same_spec`` holds and the ``prove_correct collectSignatures``
obligation survives) and swaps in a candidate implementation; it is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates).

DEFENDED SURFACE (one contracted method, one obligation).

  collectSignatures (lines : List LineInfo)   ensures out = collectSigs lines

One input binder, ``lines``, whose elements carry FOUR independent decision
fields plus a payload. The single load-bearing clause pins the WHOLE returned
sequence — order, length and per-position payload — against a front-recursive
fold over that carrier, so the surface a rival can get wrong is the fold's
per-line decision procedure, plus what it carries through:

  * ``blank``  — a blank line ENDS the scan: nothing at or beyond it is
                 collected, and in particular a leading blank yields the empty
                 result regardless of what follows;
  * ``isSig``  — a signature-bearing line is COLLECTED; a line that is neither
                 blank nor signature-bearing is SKIPPED and the scan continues
                 past it;
  * ``cont``   — a collected line whose trailing join marker is present lets
                 collection CARRY ON to the following line; absent, that
                 signature is the LAST one collected;
  * ``sig``    — the payload placed at that position, carried through
                 unmodified, in reading order.

The discriminating behaviour: a leading signature line that bears the join
marker must yield TWO OR MORE signatures, not just the first. That is the whole
content of the change, and it is what the failing tests observe (they render a
documented object whose leading signature line carries the marker and assert the
two-signature rendering; the pre-image behaviour renders one).

ADVERSARIAL READ of the nagini sibling's classes:

  * FRAME-MUTATION (the sibling's #1 class, two mandatory cases) — VACUOUS on
    this backend. It exists on nagini because a read-only input may carry a
    fractional heap permission an implementation can write through, and the
    rejection comes from the permission system. Lean and Velvet are
    referentially transparent: ``lines`` is an immutable value, this method
    declares no ``mut`` binder, there is no heap and no aliasing, so there is no
    read-only input to overwrite and no substitute probe exists. Reported as an
    omission (footer), not fabricated.

  * UNGROUNDED-ORACLE ECHO — N/A, for the same reason the sibling gives. The
    post-image ``collectSigs`` is a total, fully unfolded ``def`` over the
    method's own argument; the ``axioms`` region declares no ``axiom``, so there
    is no opaque answer key an implementation could echo. Hence no wrong-echo
    reject to build; the honest positives below take that slot.

  * PARTIAL-DOMAIN — the heart of this surface, and where the sibling's three
    rivals live. Each rival below is correct on a sub-domain of the carrier and
    diverges off it, and each is refuted at a point INSIDE its own divergence.

  * DIVERGENCE / NON-TERMINATION — genuinely closed here, and for a reason
    specific to this bundle rather than to the backend.
    This bundle sets ``loom.semantics.termination "total"``, under which a
    postcondition is claimed of ALL runs, not only terminating ones, and the verifier
    demands a decreasing measure on every loop. The option cannot drift from the
    file's ``open TotalCorrectness DemonicChoice``, because the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). (An earlier version of this
    bullet cited an internal findings doc for the claim that 401 of 500 velvet bundles
    set ``"partial"``, under which a non-terminating implementation satisfies every
    ``ensures`` clause vacuously and VERIFIES, and called that a known spec hole. That
    cohort is withdrawn: all 500 velvet bundles set ``"total"``.)
    Confirmed by hand here rather than assumed: splicing ``while true do
    pure ()`` ahead of the frozen body is refused with ``error: Decreasing
    annotations are required in total correctness semantics``, and the sharper shape
    that CARRIES a measure which does not decrease
    (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``, body
    ``q := q``) is REJECTED on the measure's own goal - ``case «decreasing_1: q»``,
    residual ``⊢ q < q``. So the class is
    closed by the frozen semantics option, and there is nothing to port and no
    hole to report.

  * CONTROL-FLOW-EFFECT / VALUE-DOUBLE-MASK — N/A exactly as on the sibling.
    The method is a pure value computation with one return and no side-effect
    path invisible to the value abstraction, and the sole clause pins the ENTIRE
    sequence rather than an index-via-value proxy that could drop disagreeing
    positions.

WITNESS MECHANICS (the part with no nagini counterpart). The sibling's rejects
lean on the verifier: Viper discharges the postcondition, so "did not verify"
means the contract fails. Here the obligation is a tactic script, and reshaping
the impl is precisely what a rival does — so a merely-reshaped rival fails to
build identically to a wrong one. Each reject therefore carries a witness that
was SEEN to discriminate.

The witness reaches the ``method`` contract through Velvet's own tester
machinery (``collectSignaturesTester args = false`` says the extracted program
violates the postcondition at that input), checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict.

One measured constraint shaped the whole battery, and it is the constraint an
earlier revision of this file got WRONG. The frozen impl is a ``while`` loop
under ``loom.semantics.choice "demonic"``; its extracted ``…Exec`` elaborates
through ``Classical.choice``, which the kernel cannot unfold, so ``decide``
against the FROZEN tester is stuck for every claim regardless of truth. Measured
directly here, on the ordinary single-signature carrier: the claim
``…Tester [terminal] = true`` (TRUE of the frozen impl, which verifies) and
``…Tester [terminal] = false`` (its exact negation) both fail with the identical
``fun x x => Decidable.byCases …`` non-reduction. So the frozen side's exit code
carries NO information, and "witness fails on gold" would attest to a refutation
never performed — the gate reports that as ``witness-undecided`` and refuses the
case, which is exactly what it did to the earlier revision's six rejects.

The repair is the documented one: each reject names a ``witness_reference`` —
``_LOOPFREE`` below, a variant that implements the frozen spec CORRECTLY and
loop-freely, so it DOES reduce. Soundness of that substitution is the same
argument gold rested on: a witness says "the spec is violated at this input", and
an implementation the verifier ACCEPTS cannot violate its own spec, so a genuine
witness must fail there. It is checked, not trusted — the gate re-verifies that
the reference shares the frozen spec and verifies before using it — and it is
also shipped as an ``expect="verify"`` case of its own (``pos-loop-free-direct``)
so the battery itself records that loop-freeness is not what any rival is being
rejected for.

Polarity was measured against that reference rather than assumed:
``…Tester [carries-on, terminal] = true`` ELABORATES against it (exit 0) while
``= false`` fails with ``Tactic `decide` proved that the proposition … is
false`` — a real decision, not a stuck term. Every one of the eight witnesses
below was then built twice by hand: exit 0 against its rival, exit 1 against the
reference with a genuine ``decide`` refutation in the log (checked for the
absence of the stuck-reduction message, not merely for a nonzero exit). Each was
additionally checked to be TRUE of its own rival somewhere — ``…Tester = true``
elaborates against the rival at a point where that rival agrees with the
post-image — so no witness is refuting a rival that fails everywhere for an
unrelated reason.

Each rival is additionally written LOOP-FREE — the same wrong decision procedure
expressed as a pipeline over the carrier — so that its own side reduces too. The
rival's wrongness is a property of the decision procedure, not of the loop, so
nothing is lost. No witness binds a hypothesis (every point is a concrete
literal carrier), so the gate's inconsistency probe has nothing to find and no
refutation here rests on assumptions that might not be jointly satisfiable.

WITNESS PLACEMENT. There is one input binder, so binder coverage is a claim about
its FIELDS: no rival is refuted at a point another rival's point could stand in
for. Across the eight witnesses ``blank`` is moved (one point leads with a blank
line, the rest do not), ``isSig`` is moved (one point leads with a line that is
neither blank nor signature-bearing), ``cont`` takes both values in leading
position and both values on the carrier's LAST line, the carrier length takes 1,
2 and 3, the marker-bearing and terminal lines are probed in BOTH orders, and the
``sig`` payload — the one field every decision-procedure rival carries through
correctly — gets a rival of its own. Two near-misses that agree with the
post-image over more of the carrier get their own points rather than sharing one,
so each rationale's sub-domain claim is the one its witness demonstrates.

One placement claim is worth stating precisely, because a weaker version of it
was wrong and cost the battery a case. Varying ``cont`` on the LAST line of a
carrier is not automatically a meaningful variation: flip it on any of the first
seven points and ``collectSigs`` returns the same sequence, because the scan has
already decided to stop (a terminal line ends it) or has run out of lines. So
"``cont`` takes both values in trailing position" was true as a SPELLING and
empty as coverage — the field was moved where the spec cannot see it. The place
the trailing marker IS observable is a carrier whose last line is
marker-bearing AND reached by the scan, which is exactly
``weak-marker-needs-successor``'s point; before that case existed no witness
constrained the spec there, and six of the seven agreed with the post-image on
it. Measured, not argued: flipping the last line's ``cont`` at each of the seven
original points leaves ``collectSigs`` unchanged at all seven.

AXIOM lane: DROPPED. ``meta.axioms == []``; the sibling's own lane is empty for
the same reason, and the gate ignores ``AXIOM_TESTS`` regardless. The single
A-reference (the per-line classification carrier) is what axiom_check.py / G-AX
validate against the real unchanged callees; nothing in that lane belongs here.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7748"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Surgery anchor — the ENTIRE impl body, verbatim. It lies wholly between
# `-- impl-start` and `-- impl-end` and is unique in Solution.lean (the loop's
# invariant text does not recur in the `pure` region), both asserted at load by
# `_swap`. Every variant replaces exactly this text, so `same_spec` holds by
# construction and the `prove_correct collectSignatures` obligation is untouched.
# ---------------------------------------------------------------------------
_LOOP_HEAD = (
    "    let mut out : List Sig := []\n"
    "    let mut i := 0\n"
    "    let mut stopped := false\n"
    "    while i < lines.length ∧ stopped = false\n"
    "      invariant 0 ≤ i ∧ i ≤ lines.length\n"
    "      invariant out ++ (if stopped then [] else collectSigs (lines.drop i))"
    " = collectSigs lines\n"
    "      done_with stopped = true ∨ i = lines.length\n"
    "      decreasing (lines.length - i) + (if stopped then 0 else 1)\n"
    "    do\n"
)

_GOLD_STEP = (
    "      let l := lines[i]!\n"
    "      if l.blank then\n"
    "        stopped := true\n"
    "      else\n"
    "        if l.isSig then\n"
    "          out := out ++ [l.sig]\n"
    "          if l.cont then\n"
    "            i := i + 1\n"
    "          else\n"
    "            stopped := true\n"
    "        else\n"
    "          i := i + 1\n"
    "    return out\n"
)

_IMPL = _LOOP_HEAD + _GOLD_STEP

assert _BASE.count(_IMPL) == 1, "impl anchor drift — re-sync _LOOP_HEAD/_GOLD_STEP"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _prefix(extra):
    """Frozen impl body with `extra` spliced in ahead of it (in-region)."""
    return _impl(extra + _IMPL)


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. A correct, loop-free implementation of the frozen spec.
# Its ONLY job is to be an impl the witnesses can be refuted against, because the
# frozen loop's extracted program does not reduce under `decide` and so decides
# neither a true nor a false claim (see WITNESS MECHANICS above). Shared by every
# reject case, so the gate verifies it once. Shipped as `pos-loop-free-direct`
# too, so the battery records on its own that this impl verifies rather than
# asking the reader to take the reference's validity on trust.
# ---------------------------------------------------------------------------
_LOOPFREE = _impl("    return (collectSigs lines)\n")


# ---------------------------------------------------------------------------
# Carrier literals. `_L` is one line of the input carrier; `_S` the payload it
# would contribute. Kept as helpers so each witness point reads as the shape it
# is probing rather than as a wall of record syntax.
# ---------------------------------------------------------------------------
def _L(blank, is_sig, cont, args, retann):
    b = "true" if blank else "false"
    s = "true" if is_sig else "false"
    c = "true" if cont else "false"
    return ("{ blank := %s, isSig := %s, cont := %s, "
            'sig := { args := "%s", retann := "%s" } }' % (b, s, c, args, retann))


def _S(args, retann):
    return '{ args := "%s", retann := "%s" }' % (args, retann)


# A signature-bearing line that CARRIES ON (join marker present).
_CARRIES_A = _L(False, True, True, "a", "ra")
_CARRIES_C = _L(False, True, True, "c", "rc")
# A signature-bearing line that TERMINATES the collection (no join marker).
_TERM_B = _L(False, True, False, "b", "rb")
_TERM_D = _L(False, True, False, "d", "rd")
# A line that is neither blank nor signature-bearing: the scan skips PAST it.
_SKIPPED = _L(False, False, False, "", "")
# A blank line: the scan ENDS here.
_BLANK = _L(True, False, False, "", "")

# Payload literals for the admissibility assert (the only case that names the
# expected payloads rather than only the input shape).
_PAY_A, _PAY_B = _S("a", "ra"), _S("b", "rb")


# ---------------------------------------------------------------------------
# Witness preamble + builder. The spec is a `method` CONTRACT, not a bare
# predicate, so the witness reaches it through Velvet's tester machinery. The
# preamble derives INSTANCES (no `axiom`/`sorry`/`native_decide`), and every
# witness below states its refutation at a CONCRETE literal carrier — nothing is
# conditioned on, so there are no hypotheses that could fail to be jointly
# satisfiable.
# ---------------------------------------------------------------------------
_TESTER = (
    "extract_program_for collectSignatures\n"
    "prove_precondition_decidable_for collectSignatures\n"
    "prove_postcondition_decidable_for collectSignatures\n"
    "derive_tester_for collectSignatures\n\n"
)


def _witness(point):
    return (_TESTER
            + "example : collectSignaturesTester\n"
              f"    {point} = false := by\n  decide\n")


# ---------------------------------------------------------------------------
# Loop-free rival bodies. `_SCAN` is the sub-scan the post-image performs before
# a blank line ends it; a rival built on top of it gets the blank-line rule right
# and is wrong only about the collection rule, which is what isolates each
# rival's sub-domain.
# ---------------------------------------------------------------------------
_SCAN = "    let scanned := lines.takeWhile (fun l => ! l.blank)\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — CORRECT implementations that MUST verify.
    # If a faithful correct implementation cannot verify, the spec is
    # SPEC-TOO-STRONG. All three keep the frozen `prove_correct` body as-is:
    # `loom_solve` closes each, so no obligation is weakened, no helper lemma is
    # introduced and nothing is assumed.
    # =====================================================================
    {
        "id": "pos-negate-branch-tests",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate BOTH decision tests and swap their arms — the
        # end-the-scan test and the carry-on test. Every line kind reaches the
        # same update with the same values, so `out = collectSigs lines` still
        # holds. This is the port of the sibling's commuted-break positive: there
        # the terminator disjunction was commuted, here the two branch tests are
        # inverted, which is the same "reorder the decision, keep the decision"
        # move on this carrier (the sibling's disjunction is split across two
        # nested tests here, so inverting both is the faithful counterpart).
        "module": _impl(
            _LOOP_HEAD
            + "      let l := lines[i]!\n"
              "      if ! l.blank then\n"
              "        if l.isSig then\n"
              "          out := out ++ [l.sig]\n"
              "          if ! l.cont then\n"
              "            stopped := true\n"
              "          else\n"
              "            i := i + 1\n"
              "        else\n"
              "          i := i + 1\n"
              "      else\n"
              "        stopped := true\n"
              "    return out\n"),
        "rationale": "inverting the end-the-scan test and the carry-on test and "
                     "swapping their arms sends every line kind to the SAME "
                     "update with the SAME values, so the collected sequence is "
                     "unchanged and `out = collectSigs lines` still holds. A "
                     "correct reshape of the decision order must verify, else "
                     "SPEC-TOO-STRONG on branch polarity.",
    },
    {
        "id": "pos-prebind-decision-fields",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: pre-bind all four decision fields AND the payload into locals
        # before branching, then branch on the locals. The port of the sibling's
        # grounded-oracle positive (which pre-bound the terminator booleans into
        # locals and did the identical real work): because the post-image is a
        # fully unfolded function of the argument, there is no echo shortcut — the
        # cheapest faithful implementation still walks the carrier and builds the
        # sequence position by position, which this does.
        "module": _impl(
            _LOOP_HEAD
            + "      let l := lines[i]!\n"
              "      let ends := l.blank\n"
              "      let collected := l.isSig\n"
              "      let carries := l.cont\n"
              "      let payload := l.sig\n"
              "      if ends then\n"
              "        stopped := true\n"
              "      else\n"
              "        if collected then\n"
              "          out := out ++ [payload]\n"
              "          if carries then\n"
              "            i := i + 1\n"
              "          else\n"
              "            stopped := true\n"
              "        else\n"
              "          i := i + 1\n"
              "    return out\n"),
        "rationale": "pre-binding every per-line decision field and the payload "
                     "into locals before branching leaves the decision and the "
                     "appended value identical, so `out = collectSigs lines` "
                     "still holds. Also the grounded-post-image positive: the "
                     "clause is a fully unfolded function of the argument, so no "
                     "echo shortcut exists and the cheapest faithful "
                     "implementation still builds the sequence position by "
                     "position — which this one does. Must verify.",
    },
    {
        "id": "pos-loop-free-direct",
        "kind": "soundness",
        "expect": "verify",
        # The WITNESS REFERENCE, shipped as a case in its own right. Its role in
        # the battery is mechanical rather than adversarial: the frozen loop's
        # extracted program does not reduce under `decide`, so it can decide
        # neither a true nor a false claim and cannot serve as the subject the
        # witnesses are refuted against. This impl can, and every reject below
        # names it as `witness_reference`. Shipping it as an `expect="verify"`
        # case is what makes the substitution auditable from the manifest alone:
        # loop-freeness VERIFIES against this spec, so it is provably not what
        # any rival is being rejected for. (It is not offered as evidence of
        # structural independence — the two positives above carry that; this one
        # deliberately does the least work an impl of this clause can do, which
        # is exactly why it reduces.)
        "module": _LOOPFREE,
        "rationale": "a loop-free implementation of the same clause must verify: "
                     "the sole obligation is `out = collectSigs lines` and this "
                     "returns precisely that, so rejecting it would mean the "
                     "obligation is unprovable of an impl that satisfies it by "
                     "construction. Doubles as the battery's declared "
                     "`witness_reference`, and the gate independently re-checks "
                     "both halves of that role (shares the frozen spec, and "
                     "verifies) before refuting any witness against it.",
    },

    # =====================================================================
    # ADMISSIBILITY — this method has no `require` clause, so the sibling's
    # "a normal input establishes the precondition" probe cannot fail: nothing
    # could exclude the shape the failing tests exercise. It is re-aimed at the
    # residual admissibility risk on a total domain — that the post-image is
    # UNSATISFIABLE or DEGENERATE at the interesting point, since a spec no
    # implementation can meet reads exactly like a spec every implementation
    # meets. The in-region assert is LIVE, not decoration, and this was measured:
    # a variant asserting the PRE-IMAGE claim at the same point instead (that the
    # marker-bearing leading line yields only its own payload) leaves
    # `unsolved goals` at the assert and the file fails to elaborate. The frozen
    # impl is kept verbatim after it, so the method's own obligation still
    # discharges alongside.
    # =====================================================================
    {
        "id": "admiss-marker-run-yields-two",
        "kind": "admissibility",
        "expect": "verify",
        "module": _prefix(
            "    assert (with_name_prefix `assert\n"
            f"      (collectSigs [{_CARRIES_A}, {_TERM_B}]\n"
            f"         = [{_PAY_A}, {_PAY_B}] ∧\n"
            f"       collectSigs [{_TERM_B}] = [{_PAY_B}] ∧\n"
            f"       collectSigs [{_BLANK}, {_TERM_B}] = []))\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "shape the failing tests exercise: a leading "
                     "marker-bearing signature line followed by a terminal one "
                     "demands TWO payloads in reading order — not one — while a "
                     "lone terminal line demands exactly one and a leading blank "
                     "line demands none. All three must discharge in-region "
                     "(else the obligation is unsatisfiable or trivial at the "
                     "interesting point), and the frozen impl is kept verbatim "
                     "so `out = collectSigs lines` discharges alongside them.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected, each with a machine-checked refutation
    # witness at a concrete input and the refinement argument for why its
    # faithful counterpart would NOT resolve the failing tests. Every witness
    # names `_LOOPFREE` as its `witness_reference`, because the frozen loop
    # decides nothing (WITNESS MECHANICS above); each was built by hand against
    # BOTH its rival (must elaborate) and that reference (must fail by a genuine
    # `decide` refutation, not by stuck reduction) before shipping.
    # =====================================================================
    {
        "id": "weak-first-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-IMAGE BEHAVIOUR, and the port of the sibling's `first-only`:
        # collect at most ONE signature, ignoring the join marker entirely.
        # Correct exactly on the sub-domain where the post-image collects one
        # anyway (a leading signature line with no marker, or none at all).
        "module": _impl(_SCAN
                        + "    return (((scanned.filter (fun l => l.isSig)).map "
                          "(fun l => l.sig)).take 1)\n"),
        "refinement": "this is the pre-image code path: stop at the first "
                      "signature found and never honour the join marker, so at "
                      "most one signature is ever produced. The failing tests "
                      "render a documented object whose leading signature line "
                      "carries the marker and assert the resulting TWO-signature "
                      "rendering; this produces one, which is exactly the "
                      "behaviour those tests were added to catch. A faithful "
                      "counterpart that collects only the first signature does "
                      "NOT resolve.",
        "rationale": "REJECT from `out = collectSigs lines`: on a leading "
                     "marker-bearing signature line the post-image carries on "
                     "and collects the following terminal line too, so it "
                     "demands two payloads where this returns one. Refuted at "
                     "that two-line shape — the sub-domain the whole change "
                     "exists for.",
        "witness": _witness(f"[{_CARRIES_A}, {_TERM_B}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-ignore-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS in the opposite direction, and the port of the sibling's
        # `over-collect-all`: collect EVERY signature line the scan reaches,
        # ignoring the join marker. Correct exactly when every collected line
        # carries the marker; wrong as soon as one terminates and further
        # signature lines follow. Given its own point rather than sharing
        # `weak-first-only`'s: at THAT point this rival agrees with the
        # post-image, so sharing would claim a sub-domain never demonstrated.
        "module": _impl(_SCAN
                        + "    return ((scanned.filter (fun l => l.isSig)).map "
                          "(fun l => l.sig))\n"),
        "refinement": "collecting every signature line the scan reaches drops "
                      "the rule that an unmarked signature is the LAST one. On a "
                      "documented object whose leading signature line has no "
                      "join marker but is followed by further signature lines, "
                      "this renders the trailing ones as extra signatures where "
                      "the tests assert only the first — so the rendered block "
                      "is wrong and those assertions fail. A faithful "
                      "counterpart that ignores the marker does NOT resolve; the "
                      "marker gating is precisely what decides how many "
                      "signatures a block contributes.",
        "rationale": "REJECT from `out = collectSigs lines`: a leading TERMINAL "
                     "signature line ends the collection at one payload, but "
                     "this carries on and appends the following marker-bearing "
                     "line's payload too. Refuted at the MIRROR of "
                     "`weak-first-only`'s point — the same two line kinds in the "
                     "opposite order — so the marker field is probed at both "
                     "values in leading position and neither near-miss pins the "
                     "order of the carrier.",
        "witness": _witness(f"[{_TERM_B}, {_CARRIES_A}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-omit-terminal",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of the sibling's `drop-terminator`: collect the marker-bearing
        # lines but OMIT the terminal one, stopping one short. Off-by-one on the
        # tail of every collection, and empty where the post-image demands a
        # single payload.
        "module": _impl(_SCAN
                        + "    return ((scanned.filter "
                          "(fun l => l.isSig && l.cont)).map (fun l => l.sig))\n"),
        "refinement": "the post-image records a signature and THEN decides "
                      "whether to carry on, so the terminal signature IS "
                      "collected. Omitting it renders one too few signatures — "
                      "and none at all for the ordinary single-signature "
                      "docstring, which is the shape most of the passing tests "
                      "rely on. Both the multi-signature assertions and the "
                      "single-signature ones would fail, so a faithful "
                      "counterpart that stops one short does NOT resolve.",
        "rationale": "REJECT from `out = collectSigs lines`: a lone terminal "
                     "signature line demands exactly one payload and this "
                     "returns none. Refuted at a ONE-line carrier — moving the "
                     "list length off the two- and three-line points the other "
                     "rivals use, and probing the degenerate end of the "
                     "collection rule the near-misses above never reach.",
        "witness": _witness(f"[{_TERM_D}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-blank-not-terminal",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the OTHER top-level arm of the fold's decision: treat a blank
        # line as merely skippable instead of as ending the scan. No sibling
        # counterpart — nagini's carrier fed the collection a pre-trimmed run and
        # had no blank-line field at all, so this arm is new surface here. It is
        # also what moves the `blank` field: without it every witness would hold
        # `blank` at false and a rival mishandling a blank line would verify
        # uncaught.
        "module": _impl("    return (collectSigs "
                        "(lines.filter (fun l => ! l.blank)))\n"),
        "refinement": "a blank line ends the scan of a docstring, so nothing at "
                      "or beyond it is collected. Skipping past it instead "
                      "harvests signature-shaped lines out of the prose BELOW "
                      "the blank separator and renders them as signatures of the "
                      "documented object; every test that renders an object "
                      "whose docstring has a blank line followed by such a line "
                      "then gets extra signatures it does not assert. A faithful "
                      "counterpart that does not stop at a blank line does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = collectSigs lines`: a LEADING blank "
                     "line makes the post-image demand the empty sequence "
                     "regardless of what follows, but this skips it and collects "
                     "the following signature line. Refuted at the only point in "
                     "the battery whose leading line is blank, so the "
                     "end-the-scan field is discriminated rather than held fixed.",
        "witness": _witness(f"[{_BLANK}, {_TERM_D}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-nonsig-stops-scan",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the third arm: treat a line that is neither blank nor
        # signature-bearing as ending the scan instead of being skipped past.
        # Also no sibling counterpart, for the same carrier reason — and it is
        # what moves the `isSig` field into leading position.
        "module": _impl("    return (collectSigs "
                        "(lines.takeWhile (fun l => l.blank || l.isSig)))\n"),
        "refinement": "a line that is neither blank nor signature-bearing is "
                      "skipped and the scan continues past it, so a signature "
                      "that appears after such a line is still found. Stopping "
                      "there instead loses it, and the documented object renders "
                      "with no signature at all where the tests assert one — the "
                      "same class of failure as the pre-image bug, reached from a "
                      "different arm of the decision. A faithful counterpart "
                      "that stops at the first non-signature line does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = collectSigs lines`: a leading line that "
                     "is neither blank nor signature-bearing must be skipped, so "
                     "the post-image still collects the following terminal "
                     "signature line, but this stops and returns nothing. "
                     "Refuted at the only point whose leading line is a skipped "
                     "one — moving `isSig` off true in leading position, which "
                     "every other witness holds.",
        "witness": _witness(f"[{_SKIPPED}, {_TERM_B}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER, the one thing the sole clause pins that a count- or set-shaped
        # rival would slip past: collect exactly the right payloads and emit them
        # in reverse. The sibling has no counterpart (its own clause pinned the
        # whole sequence too, but it spent its rivals on the run-length
        # sub-domains); this is the rival that shows the clause is order-faithful
        # and not a multiset proxy.
        "module": _impl("    return ((collectSigs lines).reverse)\n"),
        "refinement": "the collected signatures are rendered in reading order, "
                      "so reversing them renders the multi-signature block with "
                      "its lines transposed. The failing tests assert the exact "
                      "rendered lines in order, so a faithful counterpart that "
                      "emits the collected signatures in reverse does NOT "
                      "resolve even though it finds exactly the right set of "
                      "them.",
        "rationale": "REJECT from `out = collectSigs lines`: the clause pins the "
                     "sequence POSITION-WISE, not as a count or a multiset, so a "
                     "correct-content wrong-order result violates it. Refuted at "
                     "a THREE-line carrier — the shortest length at which "
                     "reversal is observable beyond swapping a pair, and a third "
                     "distinct list length across the battery.",
        "witness": _witness(f"[{_CARRIES_A}, {_CARRIES_C}, {_TERM_B}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-transposed-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # The PAYLOAD field, which every rival above carries through correctly:
        # select exactly the right lines, in the right order, and transpose the
        # two components of each payload. Without this, `sig` is a field no rival
        # was built to abuse — a rival that mishandled only the payload would
        # verify and the battery would never notice, which is the precise failure
        # shape the porting guidance warns about. No sibling counterpart: nagini's
        # per-line value was a single scalar with no internal structure to
        # transpose, so this surface exists only on this carrier.
        "module": _impl("    return ((collectSigs lines).map\n"
                        "      (fun s => { args := s.retann, retann := s.args }))\n"),
        "refinement": "the payload components are extracted from the recognized "
                      "line and carried through untouched; the rendering places "
                      "them in fixed positions. Transposing them renders every "
                      "signature with its argument text and its return "
                      "annotation exchanged, so the exact rendered strings the "
                      "tests assert do not match — for the multi-signature "
                      "fixture and equally for the ordinary single-signature "
                      "ones. A faithful counterpart that swaps the two payload "
                      "components does NOT resolve, even though it selects "
                      "exactly the right lines in exactly the right order.",
        "rationale": "REJECT from `out = collectSigs lines`: the clause pins each "
                     "position's payload, not merely which lines are selected "
                     "and in what order, so a right-lines wrong-payload result "
                     "violates it. Refuted at a two-line marker-then-terminal "
                     "carrier whose payload components are pairwise distinct — "
                     "the only witness in the battery that varies the `sig` "
                     "field rather than the three decision fields, and the one "
                     "that shows the clause is not a line-selection proxy.",
        "witness": _witness(f"[{_CARRIES_C}, {_TERM_D}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-marker-needs-successor",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The one arm of the per-line decision no rival above
        # attacks: a collected line's payload is recorded BEFORE the join marker
        # is consulted, so a marker-bearing line is collected even when nothing
        # follows it to join onto. A rival that reads the marker as a PROMISE of a
        # further signature — collect this line only if a successor exists to
        # carry on to — is wrong exactly there, and correct everywhere else.
        #
        # Why this was a real gap rather than a redundant seventh point: the
        # single-marker-bearing-line carrier is precisely the point six of the
        # seven witnesses above use as their AGREEMENT point (each of those rivals
        # returns the post-image's answer there), so nothing in the battery
        # constrained the spec's verdict on it. Measured: this rival's decision
        # procedure disagrees with the post-image on 40 of the 4681 carriers of
        # length <= 4 and agrees with every other rival's witness point, so none
        # of the seven could stand in for it.
        #
        # Written loop-free like its neighbours so its own side reduces under
        # `decide`; the wrongness is in the decision procedure, not the loop, and
        # this spelling was checked equal to the indexed-loop form on all 37449
        # carriers of length <= 5.
        "module": _impl(
            "    match lines.getLast? with\n"
            "    | some l =>\n"
            "      if l.isSig ∧ l.cont then\n"
            "        return (collectSigs lines.dropLast)\n"
            "      else\n"
            "        return (collectSigs lines)\n"
            "    | none => return (collectSigs lines)\n"),
        "refinement": "a signature line is recorded when it is recognized, and "
                      "only THEN is the join marker consulted to decide whether "
                      "to keep scanning; the marker does not retroactively "
                      "withdraw the signature it was attached to. Treating it as "
                      "a promise that another signature follows drops the last "
                      "signature of any block whose final recognized line still "
                      "carries the marker — the documented object then renders "
                      "with one signature too few, or with none at all when that "
                      "is the only line. A faithful counterpart that requires a "
                      "successor before collecting a marker-bearing line does "
                      "NOT resolve.",
        "rationale": "REJECT from `out = collectSigs lines`: the post-image "
                     "collects a marker-bearing signature line whether or not "
                     "anything follows it, so a lone such line demands exactly "
                     "one payload and this returns none. Refuted at the ONE-line "
                     "marker-bearing carrier — the point six of the seven rivals "
                     "above AGREE with the post-image at, which is why none of "
                     "their witnesses constrains this arm and why the case is "
                     "not redundant with `weak-omit-terminal` (that rival is "
                     "refuted at a lone TERMINAL line and is correct here).",
        "witness": _witness(f"[{_CARRIES_A}]"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING
#
# The sibling battery has 8 SPEC cases (2 soundness positives, 1 admissibility,
# 2 mandatory frame-mutation rivals, 3 partial-domain rivals). This bundle models
# the SAME behaviour — collect a docstring's signatures in reading order under
# the scan rules — as ONE method with ONE obligation, so the value-level cases
# map directly and only the permission-level ones fall away.
#
#   sibling case            -> here                            disposition
#   -----------------------------------------------------------------------
#   pos-commute-break       -> pos-negate-branch-tests          PORTED
#   honest-grounded         -> pos-prebind-decision-fields      PORTED
#   admiss-class-e          -> admiss-marker-run-yields-two     PORTED (re-aimed)
#   frame-mutate-cont       -> (none)                           OMITTED (vacuous)
#   frame-mutate-val        -> (none)                           OMITTED (vacuous)
#   first-only              -> weak-first-only                  PORTED
#   over-collect-all        -> weak-ignore-marker               PORTED
#   drop-terminator         -> weak-omit-terminal               PORTED
#                           -> weak-blank-not-terminal          ADDED
#                           -> weak-nonsig-stops-scan           ADDED
#                           -> weak-reversed-order              ADDED
#                           -> weak-transposed-payload          ADDED
#                           -> weak-marker-needs-successor      ADDED (by audit)
#                           -> pos-loop-free-direct             ADDED (mechanical)
#
# OMITTED (2) — frame-mutate-cont, frame-mutate-val. On nagini BOTH inputs are
#   held at a fractional permission and the rivals write through them, so the
#   rejection comes from the permission system rather than the postcondition.
#   This backend is referentially transparent: `lines` is an immutable value,
#   this method declares no `mut` binder, and there is no heap or aliasing, so
#   there is no read-only input to overwrite. The class collapses on this
#   carrier — not omitted for difficulty, and no substitute fabricated.
#
# RE-AIMED (1) — admiss-class-e. The sibling's probe is that the precondition
#   (`len(cont)==len(val)`, `len>0`) admits the shape the failing tests exercise.
#   This method has no `require` clause, so nothing could reject any input and
#   that probe cannot fail. It is re-aimed at the residual admissibility risk on
#   a total domain — that the post-image is unsatisfiable or degenerate at the
#   interesting point — while keeping the sibling's actual claim (that shape
#   yields TWO signatures, and its first payload is the leading line's) as the
#   live in-region assert. The sibling's second and third conjuncts pin the
#   single-signature and blank-led shapes as well, so the assert also rules out a
#   post-image that is trivially true or trivially empty there.
#
# ADDED (6). The sibling's carrier fed the collection a pair of pre-trimmed
#   parallel streams: a per-line continuation flag and a per-line scalar value.
#   It had NO field for a blank line, none for a line that is neither blank nor
#   signature-bearing, and no internal structure in the value — all three are
#   handled upstream of, or absent from, what nagini modeled. This carrier keeps
#   all four decision fields plus a two-component payload, so surface exists here
#   that had no counterpart there, and each piece of it gets a rival:
#   weak-blank-not-terminal and weak-nonsig-stops-scan for the two extra arms of
#   the fold's decision, weak-transposed-payload for the payload. These three are
#   also what make the field coverage honest — without them every witness would
#   hold `blank` at false and `isSig` at true in leading position and carry every
#   payload through correctly, and a rival mishandling any of the three would
#   verify uncaught, which is exactly the shape of the two real failures this
#   port guidance warns about. weak-reversed-order is added for the remaining
#   thing the sole clause pins and no run-length rival touches: ORDER. It and
#   weak-transposed-payload together are what distinguish a position-wise clause
#   from a line-selection-and-count proxy. weak-marker-needs-successor was added
#   by the AUDIT lane, for the last arm of the per-line decision the original
#   seven left unconstrained: the post-image records a recognized line's payload
#   BEFORE consulting the join marker, so a marker-bearing line is collected even
#   with nothing following it. Six of the original seven rivals return the
#   post-image's own answer at that carrier — it was their shared agreement point
#   — so the spec's verdict there rested on no witness at all. See its case
#   comment for the measurement. pos-loop-free-direct is added for a
#   mechanical reason rather than an adversarial one — it is the declared
#   `witness_reference`, shipped as a case so its verification is on the record.
#
# WITNESS MECHANISM (the one thing with no sibling counterpart, and the thing an
#   earlier revision of this file got wrong). The sibling's rejects need no
#   witness: Viper discharges the postcondition. Here they do, and the frozen
#   impl cannot serve as the discriminator's second half: its `while` loop
#   elaborates through `Classical.choice` under `loom.semantics.choice "demonic"`
#   and `decide` against its extracted tester is stuck for EVERY claim. Measured
#   on the single-terminal-line carrier: `...Tester [terminal] = true` (true of
#   the frozen impl) and `= false` (its negation) both fail with the identical
#   non-reduction, so the frozen exit code carries no information — the earlier
#   revision shipped six witnesses against it and the gate correctly refused all
#   six as `witness-undecided`. Every reject now names `_LOOPFREE` as its
#   `witness_reference`: a correct, loop-free impl of the same spec that DOES
#   reduce (`= true` elaborates against it, `= false` fails with `Tactic `decide`
#   proved that the proposition ... is false`). The gate re-checks that reference
#   shares the frozen spec and verifies before refuting anything against it, and
#   it is shipped as pos-loop-free-direct so the manifest itself records that
#   loop-freeness verifies and is therefore not what any rival is rejected for.
#
# WITNESS DISTINCTNESS (eight rivals, eight distinct points, each SEEN to
#   discriminate — built by hand against its rival, which must and does
#   elaborate, and against the reference, which must and does fail with a genuine
#   `decide` refutation rather than the stuck-reduction message):
#     weak-first-only        [carries-on(a), terminal(b)]           len 2
#     weak-ignore-marker     [terminal(b), carries-on(a)]           len 2, MIRRORED
#     weak-omit-terminal     [terminal(d)]                          len 1
#     weak-blank-not-terminal[blank, terminal(d)]                   len 2, blank=true
#     weak-nonsig-stops-scan [skipped, terminal(b)]                 len 2, isSig=false
#     weak-reversed-order    [carries-on, carries-on, terminal]     len 3
#     weak-transposed-payload[carries-on(c), terminal(d)]           len 2, payload
#     weak-marker-needs-successor [carries-on(a)]                   len 1, cont=true LAST
#   The two near-misses (first-only / ignore-marker) are refuted at MIRROR points
#   rather than sharing one, because at each other's point they agree with the
#   post-image — sharing would claim a sub-domain the manifest never
#   demonstrates. Across the eight, `blank` and `isSig` each take both values in
#   leading position, `cont` takes both values in leading position and both values
#   on the carrier's last line, the carrier length takes 1, 2 and 3, and the
#   payload is varied independently of the decision fields. No field is held at
#   one value by every witness. No witness binds a hypothesis, so none can be
#   `witness-inconsistent`.
#
#   The last row is the audit's addition and the reason the row above it is
#   phrased carefully. Trailing `cont` was previously claimed as covered on the
#   strength of its SPELLING: some points ended in a marker-bearing line, some in
#   a terminal one. But flipping the last line's `cont` at each of the original
#   seven points leaves `collectSigs` unchanged at all seven — the scan has
#   already stopped or run out of lines, so the spec cannot see that field there.
#   The variation was only meaningful once a point existed whose last line is
#   marker-bearing AND reached by the scan, which is what the new case supplies.
#   A coverage report that says a field "varies" is exactly the claim this
#   corrects: two spellings of the same verdict are not two points.
#
# DIVERGENCE LANE: genuinely closed here, and checked rather than assumed. This
#   bundle sets `loom.semantics.termination "total"`, under which a postcondition is
#   claimed of ALL runs and every loop must carry a decreasing measure. (The earlier
#   version of this note called it "one of the 99 of 500" and cited an internal
#   findings doc measuring 401 `partial` bundles that admit a diverging rival; that
#   census is withdrawn, since all 500 velvet bundles now read "total".) Splicing
#   `while true do pure ()` ahead of this impl region is refused with
#   `error: Decreasing annotations are required in total correctness semantics`, and a
#   loop CARRYING a non-decreasing measure (`while q > 0 ... decreasing q`, body
#   `q := q`) is rejected on the measure's own goal -- `case «decreasing_1: q»`,
#   residual `q < q`. So no diverging rival satisfies this spec, and there is neither
#   a case to port nor a hole to report.
#
# AXIOM_TESTS: dropped. `meta.axioms == []` and the sibling's lane is empty for
# the same reason; the gate ignores this list regardless. The single A-reference
# (the per-line classification carrier) is what axiom_check.py / G-AX validate
# against the real unchanged callees.
AXIOM_TESTS = []
