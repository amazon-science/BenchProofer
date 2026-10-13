"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-11510 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, the
``prove_correct`` tactic body — is changed, both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct
assembleInsertedLines`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND the file elaborates with every
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

DEFENDED SURFACE (one modeled method over a per-code-point line carrier):

  assembleInsertedLines (transform : List Char → List Char)
                        (lines    : List (List Char))
      return (out : List (List Char))
    ensures out =
      splitLines (transform (List.intercalate ['\\n'] (lines.dropLast.dropLast)))
        ++ lines.drop (lines.length - 2)                          -- (P) the pin

Desired behaviour: when separate content is spliced into a document while a
content transform is registered, the trailing two entries of the line sequence
are structural end-markers that carry no content and MUST survive untouched;
everything before them is the content — it is re-joined into one text, offered
to the registered ``transform``, and the (possibly rewritten) text is split back
into lines, after which the two end-markers are reattached verbatim. There is
exactly ONE top-level postcondition clause (the equation P), and two input
binders: the arbitrary ``transform`` and the line sequence ``lines``.

CARRIER — the decisive fact of this port, and why every reject clause is
witnessable WITHOUT conditioning. Unlike the sibling ports whose spec is stated
over an OPAQUE axiomatized callee, here ``transform`` is a UNIVERSALLY-QUANTIFIED
PARAMETER, not an axiom, and ``splitLines`` / ``List.intercalate`` /
``dropLast`` / ``drop`` are all computable ``def``s. A witness may therefore
INSTANTIATE ``transform`` at a concrete computable function and the whole pin
reduces by ``decide`` — the entire carrier is transparent. No hypothesis is
needed, so no witness binds anything, so the gate's consistency probe is
trivially satisfied (there are no assumptions that could be jointly
unsatisfiable). Each reject witness states, at a concrete ``transform`` and a
concrete ``lines``, that ``(assembleInsertedLines transform lines).run`` differs
from ``DivM.res`` of the pin's right-hand side; ``simp only
[assembleInsertedLines, NonDetT.run, pure]`` reduces the method to
``DivM.res <the impl's value>`` and ``injection ... ; decide`` settles the list
disequality. The witness ELABORATES against the rival (whose value ≠ the pin)
and FAILS against gold (whose value IS the pin). Verified out-of-band with two
real builds per case (``scripts/lean_verify.sh``): rival EXIT 0, gold EXIT 1.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a
    MANDATORY frame-mutation rival (write through a read-only ``Acc(.,1/2)``
    reference to ``lines``) because its input is held at a fractional heap
    permission an impl can illegally overwrite. Lean and Velvet are
    referentially transparent: ``lines`` and ``transform`` are immutable values,
    this bundle declares NO ``mut`` binder, there is no heap and no aliasing — so
    there is no read-only input to mutate and no substitute probe to build. Not
    fabricated (per the porting map, this class is vacuous here). The nagini
    intent — "the frame outside the content is exactly the original markers" — is
    instead pinned by the pin's own tail ``lines.drop (lines.length - 2)`` and
    attacked by the offer-full / one-marker rivals below.
  * DIVERGENCE / NON-TERMINATION — VACUOUS here (NOT a known hole). This bundle
    runs under ``set_option loom.semantics.termination "total"``, so a diverging
    impl cannot verify: measured by the audit with a real build of a
    ``while true do i := i + 1`` impl, which is REJECTED with "Decreasing
    annotations are required in total correctness semantics", the termination
    obligation being demanded rather than assumed. The sharper shape is refused too,
    which matters because it cannot be dismissed as merely missing the annotation: a
    loop CARRYING a measure that does not decrease
    (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``, body
    ``q := q``) is REJECTED on the measure's own goal - ``case «decreasing_1: q»``,
    residual ``⊢ q < q``. Under ``total`` a postcondition is claimed of ALL runs, not
    only terminating ones, so there is no vacuity to exploit here. The reason is the
    termination semantics, not the mere fact that the frozen impl happens to be
    straight-line: a variant may legitimately introduce a loop. (An earlier version of
    this bullet located the known-hole disposition in an internal findings doc scoped
    to "the ``partial`` bundles". There are none: all 500 velvet bundles set
    ``"total"`` and open ``TotalCorrectness``.)
  * UNGROUNDED-ORACLE ECHO — not applicable. The pin P is grounded in the inputs
    (it is ``splitLines (transform (intercalate content)) ++ markers``, a
    function of the actual ``transform`` and ``lines``, not an answer-key an impl
    could echo), so the only value satisfying P is the honest one. The nagini
    "grounded-oracle honest positive control" argument is carried by pos-inline.

WITNESS PLACEMENT / BINDER VARIATION. The pin has two input binders and both are
varied across the seven reject witnesses:
  * ``transform`` is instantiated at five DISTINCT functions — a two-char
    constant (verbatim, partial, short), a one-char constant (one-marker), the
    IDENTITY (offer-full), a distinct one-char constant (no-transform), and a
    BOUNDARY-EMITTING rewriter ``fun _ => ['a','\\r','b']`` (lf-only-resplit).
    A rival that mishandled only the identity ``transform``, only a rewriting
    one, or only a transform whose output stays inside the newline boundary is
    caught, because all three facets are probed.
  * ``lines`` is varied over a four-entry sequence (body of two content lines),
    two DISTINCT four-entry contents, a two-entry sequence (EMPTY body, the
    ``lines.length = 2`` boundary the absence of a ``require`` admits), and the
    EMPTY sequence (``length = 0``, where the Nat subtraction in
    ``lines.length - 2`` truncates). So the battery attests the pin's dependence
    on the content region, the marker tail, the empty-body sub-domain, AND the
    short sub-domain.

AUDIT ADDITIONS (independent audit of this port; every claim below re-measured
with real builds). The ported battery's seven cases all earned their recorded
outcomes — each reject witness elaborates against its rival and is refuted on
the frozen solution by ``decide`` PROVING the negation false, i.e. by the kernel
evaluating both sides, not by a stuck reduction or an unknown name. Four gaps in
COVERAGE were found and closed:
  * ``rival-lf-only-resplit`` — the pin's re-split operator was unattacked. The
    two shipped region rivals differ from P already at the identity transform, so
    the BOUNDARY SET of the re-split (the property mapping.md §3.1 records as
    load-bearing for faithfulness) was pinned by no case. An LF-only splitter is
    a wrong impl that agrees with P on every newline-only text.
  * ``rival-partial-short-lines`` — the shipped partial rival stops at
    ``length = 2``; lengths 0 and 1, which the absence of a ``require`` also
    admits and where Nat truncation makes P non-trivial, were unprobed.
  * ``pos-take-content`` / ``pos-reverse-markers`` — the two shipped positives
    only permute statement order and local names, both DEFINITIONALLY equal to
    the frozen impl, so neither tested the spec's tolerance for a genuinely
    different SHAPE. These two re-carve each of P's two slices in a
    non-definitional but faithful way, and each needs one slice lemma the frozen
    ``loom_solve`` does not supply — so they are the first positives here that
    could have failed.
No SPEC hole was found: six further hand-written wrong impls (marker tail
prepended, no re-split, empty separator, three markers held out, per-line
transform instead of whole-text, head instead of tail markers) were each
REJECTED by the frozen spec, and an input-shadowing probe (the referentially-
transparent analogue of the nagini frame-mutation rival: rebind ``lines`` to
``[]`` and compute the pin from the shadow) was rejected as well — the spec
quantifies over the original binder, so there is no Lean analogue of the
full-permission hole.

SECOND-AUDIT ADDITIONS (independent re-audit of the above; every exit code below
observed, not predicted). All seven reject witnesses were rebuilt from scratch:
each ELABORATES against its rival (EXIT 0) and FAILS on the frozen solution
(EXIT 1), and every gold-side failure is the plain-evaluation signature ``Tactic
`decide` proved that the proposition ¬<value> = <value> is false`` — the kernel
computing both sides and finding gold equal to the pin. The mandatory FORGERY
pair was run on all seven anyway: a file differing ONLY in flipping ``≠`` to
``=`` (i.e. claiming gold is CORRECT there) fails on gold with ``No goals to be
solved`` — ``simp only`` had already closed the equation — and fails on each
rival with ``failed to synthesize Decidable`` on the rival's own distinct value.
Both errors CHANGE with the claim and differ per side, so gold's exit code
carries real information about the claim and no case is hollow. Confirmed
independently: the positive claim proven by ``simp only`` ALONE elaborates
against gold at all three witness points (EXIT 0), which is the type-revealing
half — gold's value IS the pin by computation.

Two defects were found and FIXED:
  * the ``admissibility`` lane was recorded VACUOUS on reasoning that does not
    hold on a total carrier (see the accounting note below); it is now shipped as
    ``admiss-instance-present-ground``, built and VERIFIED (EXIT 0), with a
    negative control (the pinned marker tail transposed) REJECTED (EXIT 1) so the
    assert is demonstrably not inert.
  * ``rival-lf-only-resplit``'s rationale asserted the wrong intermediate value
    for the split at a carriage return (it claimed a three-element result with an
    empty middle field). Measured by evaluation: ``splitLines ['a','\\r','b'] =
    [['a'],['b']]`` — a lone CR is ONE boundary, and the empty middle field would
    only appear for ``'a','\\n','\\r','b'``. The case's outcome is unaffected (the
    rival keeps the text whole either way) but the prose was false; corrected.

Re-measured and CONFIRMED from the first audit's claims: the divergence class is
genuinely vacuous under ``termination "total"`` (a ``while true`` impl is
REJECTED with "Decreasing annotations are required in total correctness
semantics", EXIT 1, and its witness cannot even be stated — ``injection`` fails
on the unreduced ``forIn Lean.Loop.mk`` term, EXIT 1, so there is nothing
shippable in that lane); the input-shadowing probe is REJECTED with the goal
showing the spec's ``lines`` still bound to the caller's value (EXIT 1); and both
audit-added positives are genuine non-definitional reshapes — each FAILS under
the frozen ``loom_solve`` alone (EXIT 1, ``unsolved goals`` with the residue the
case's own lemma supplies), so neither is a definitional no-op dressed up as a
reshape.

Six NEW wrong impls the battery did not contain were tried against the frozen
spec (attack D) — a CR-LF re-join separator, a space re-join separator, the
transform applied TWICE, the marker tail prepended, markers taken from the HEAD,
and the transform applied per-line — and ALL SIX were REJECTED (EXIT 1), each
with a witness that elaborates on the rival (EXIT 0) and is refuted on gold by
plain evaluation (EXIT 1). No spec hole. Three NEW correct reshapes were tried
(attack E): a reverse/drop/reverse content carving VERIFIES under one slice lemma
(EXIT 0), and a branch-on-length reshape whose two arms are each faithful
VERIFIES once the short arm's two residues are supplied (EXIT 0) — it does NOT
verify under the frozen tactic alone, which is a TACTIC gap, not a spec one, and
is the reason the two audit-added positives legitimately re-prove.

AXIOM lane: DROPPED. There are NO axioms in this bundle (``transform`` is a
parameter, ``meta.json gates.G-AX.status = "skip"``), and the gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-11510"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the four CODE lines of the frozen impl body. Lies
# ---- wholly inside the single -- impl-start / -- impl-end region and is unique
# ---- in Solution.lean (both facts asserted at load by _swap), so each edit
# ---- keeps same_spec by construction and leaves the frozen
# ---- `prove_correct assembleInsertedLines` statement intact.
_IMPL = (
    "    let content := lines.dropLast.dropLast\n"
    "    let text := transform (List.intercalate ['\\n'] content)\n"
    "    let assembled := splitLines text ++ lines.drop (lines.length - 2)\n"
    "    return assembled\n"
)
assert _BASE.count(_IMPL) == 1, "assembleInsertedLines impl region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY assembleInsertedLines's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- the frozen `prove_correct` block. A positive control legitimately
# ---- RE-PROVES (variant_scope requires only that the `prove_correct
# ---- assembleInsertedLines` header survive; the spec header itself lives in the
# ---- spec view and is untouched), which is what lets a reshape whose value
# ---- equality needs a slice lemma be tested at all: rejecting it for a missing
# ---- `simp` lemma would be a TACTIC gap masquerading as SPEC-TOO-STRONG.
_PROOF = "prove_correct assembleInsertedLines by\n  loom_solve\n"
assert _BASE.count(_PROOF) == 1, "prove_correct block drifted from expected text"


def _impl_proof(new_impl, new_proof):
    """`_impl(new_impl)` with the frozen tactic body replaced by `new_proof`."""
    return _swap(_impl(new_impl), _PROOF, new_proof)


# ---- witness builder. The spec is a `method` CONTRACT; the witness reaches its
# ---- pin over the method's own `.run`, which `simp only [assembleInsertedLines,
# ---- NonDetT.run, pure]` reduces to `DivM.res <impl value>`. `transform` is a
# ---- parameter (not opaque) and every other operation computes, so the witness
# ---- INSTANTIATES `transform` at a concrete function and `decide` settles the
# ---- resulting list disequality — no hypothesis, hence nothing for the gate's
# ---- consistency probe to find unsatisfiable. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict.
def _witness(fn, lines):
    spec = (f"splitLines (({fn}) (List.intercalate ['\\n'] (({lines}).dropLast.dropLast)))"
            f" ++ ({lines}).drop (({lines}).length - 2)")
    return (
        f"example :\n"
        f"    (assembleInsertedLines ({fn}) ({lines})).run\n"
        f"      ≠ DivM.res ({spec}) := by\n"
        f"  simp only [assembleInsertedLines, NonDetT.run, pure]\n"
        f"  intro heq\n"
        f"  injection heq with h1\n"
        f"  exact absurd h1 (by decide)\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Both keep the FROZEN proof
    # script (`loom_solve`); each verified out-of-band with a real build (EXIT 0).
    # =====================================================================
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the marker tail FIRST, name the content region
        # separately, split the transformed content into its own local, then
        # splice `transformed ++ markers`. Same value on every input as the
        # frozen direct form — porting the nagini `pos-control-reorder` argument
        # ("markers computed first, body given a different local name, same
        # hooked-body ++ markers splice").
        "module": _impl(
            "    let markers := lines.drop (lines.length - 2)\n"
            "    let content := lines.dropLast.dropLast\n"
            "    let transformed := splitLines (transform (List.intercalate ['\\n'] content))\n"
            "    let out := transformed ++ markers\n"
            "    return out\n"),
        "rationale": "PASS SOURCE = the pin P. Computing the marker tail first, "
                     "naming the content region separately, and splicing "
                     "`transformed ++ markers` is observationally identical to the "
                     "direct form, so `out = splitLines (transform (intercalate "
                     "content)) ++ markers` still discharges and the frozen "
                     "`loom_solve` closes it unchanged. A structurally different "
                     "faithful reshape MUST verify; else the spec is over-fit to "
                     "one statement order / local layout (SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the entire assembled value inline in a single `let` and
        # return it, with no intermediate content/text names. Standing in for the
        # nagini grounded-oracle honest positive control: the pin is grounded in
        # the inputs (a function of the actual `transform` and `lines`), so the
        # cheapest honest impl still offers the content region to `transform` —
        # there is no wrong echo that verifies.
        "module": _impl(
            "    let out := splitLines (transform (List.intercalate ['\\n'] (lines.dropLast.dropLast)))\n"
            "                 ++ lines.drop (lines.length - 2)\n"
            "    return out\n"),
        "rationale": "grounded-oracle honest positive control: bind the assembled "
                     "value inline (no intermediate locals) and return it. The "
                     "value flow is identical, so the pin P still discharges and "
                     "the frozen `loom_solve` closes it. The pin is grounded in "
                     "the inputs (not an answer-key), so this is the cheapest "
                     "faithful impl and there is no ungrounded echo that verifies. "
                     "Must verify; else SPEC-TOO-STRONG on result binding.",
    },

    {
        "id": "pos-take-content",
        "kind": "soundness",
        "expect": "verify",
        # Reshape that changes HOW the content region is carved: a length-indexed
        # prefix `lines.take (lines.length - 2)` instead of the two-step
        # `dropLast.dropLast`. Faithful on every input (including the short
        # sequences where Nat subtraction truncates to 0 and both spellings give
        # `[]`), but NOT definitionally equal — `take_take` leaves a `min`
        # residue, so this is a genuine reshape the frozen `loom_solve` alone
        # cannot close. Re-proven with one slice lemma; added by audit because
        # the two shipped positives only permuted statement order and local
        # names, leaving the content-carving spelling undefended.
        "module": _impl_proof(
            "    let content := lines.take (lines.length - 2)\n"
            "    let out := splitLines (transform (List.intercalate ['\\n'] content))\n"
            "                 ++ lines.drop (lines.length - 2)\n"
            "    return out\n",
            "prove_correct assembleInsertedLines by\n"
            "  have key : ∀ l : List (List Char),\n"
            "      List.take (l.length - 2) l = l.dropLast.dropLast := by\n"
            "    intro l\n"
            "    simp [List.dropLast_eq_take, List.take_take]\n"
            "    omega\n"
            "  loom_solve\n"),
        "rationale": "PASS SOURCE = the pin P. Carving the content region as the "
                     "length-indexed prefix `take (length - 2)` rather than "
                     "`dropLast.dropLast` denotes the same list on EVERY input "
                     "(the two agree pointwise, and both collapse to `[]` where "
                     "the Nat subtraction truncates), so P still discharges. The "
                     "equality is not definitional — `take_take` leaves a `min` "
                     "residue `loom_solve` does not discharge — so the case is a "
                     "real reshape and its proof supplies one slice lemma "
                     "(re-proving is in scope; the spec header is untouched). "
                     "Must verify; else SPEC-TOO-STRONG on the content-carving "
                     "spelling.",
    },
    {
        "id": "pos-reverse-markers",
        "kind": "soundness",
        "expect": "verify",
        # Reshape of the OTHER slice: carve the marker tail as
        # `(lines.reverse.take 2).reverse` instead of `drop (length - 2)`.
        # Faithful on every input, again not definitionally equal. Defends the
        # marker-tail spelling, which no shipped case varied.
        "module": _impl_proof(
            "    let content := lines.dropLast.dropLast\n"
            "    let markers := (lines.reverse.take 2).reverse\n"
            "    let out := splitLines (transform (List.intercalate ['\\n'] content)) ++ markers\n"
            "    return out\n",
            "prove_correct assembleInsertedLines by\n"
            "  loom_solve\n"
            "  simp [List.take_reverse]\n"),
        "rationale": "PASS SOURCE = the pin P. Taking the last two entries by "
                     "reversing, taking 2, and reversing back is the same list as "
                     "`drop (length - 2)` on every input (including the short "
                     "sequences, where both give the whole list), so P discharges "
                     "and the marker frame is unchanged. Not definitionally equal, "
                     "so the frozen `loom_solve` needs one `take_reverse` step. "
                     "Must verify; else SPEC-TOO-STRONG on the marker-tail "
                     "spelling — the complement of pos-take-content, so both "
                     "slices in P are now defended as well as attacked.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — added by audit. The port recorded this
    # lane as VACUOUS because the method declares no `require`, but on a TOTAL
    # carrier that is the wrong analogue: what PRECOND-TOO-STRONG becomes here is
    # the obligation being UNSATISFIABLE (or degenerate) at exactly an
    # F2P-shaped input. That is directly testable — discharge the pin at the
    # concrete input BY EVALUATION, as an in-region `assert`, before closing the
    # frozen obligation verbatim — so the class is expressible and was a real gap.
    # =====================================================================
    {
        "id": "admiss-instance-present-ground",
        "kind": "admissibility",
        "expect": "verify",
        # The F2P-shaped input: a content region whose FIRST entry is empty and
        # whose second carries text (the shape a start-offset inclusion produces),
        # plus the two structural end-markers. Three conjuncts, each decided by
        # evaluation:
        #   (a) the content region re-joins to a text with an interior boundary
        #       (so the join leg is non-degenerate at this point);
        #   (b) under the IDENTITY transform the pin's value reconstructs the
        #       original sequence — the round trip is the identity at line
        #       granularity, so the obligation is SATISFIED, not unsatisfiable;
        #   (c) under a REWRITING transform the pin's value differs from (b) and
        #       the two end-markers are still exactly the original tail — so the
        #       obligation is not a constant collapse that every impl meets.
        # The frozen impl body is kept VERBATIM after the assert, so the method's
        # own `ensures` still discharges; only the tactic body gains `decide` for
        # the added assert goal (re-proving is in scope).
        "module": _impl_proof(
            "    assert (with_name_prefix `admiss\n"
            "      (List.intercalate ['\\n'] (([[], ['B'], ['m'], ['n']] : List (List Char)).dropLast.dropLast)\n"
            "         = ['\\n', 'B']\n"
            "       ∧ splitLines ((fun s => s) (List.intercalate ['\\n']\n"
            "             (([[], ['B'], ['m'], ['n']] : List (List Char)).dropLast.dropLast)))\n"
            "           ++ ([[], ['B'], ['m'], ['n']] : List (List Char)).drop\n"
            "               ((([[], ['B'], ['m'], ['n']] : List (List Char))).length - 2)\n"
            "         = [[], ['B'], ['m'], ['n']]\n"
            "       ∧ splitLines ((fun _ => ['a', 'm']) (List.intercalate ['\\n']\n"
            "             (([[], ['B'], ['m'], ['n']] : List (List Char)).dropLast.dropLast)))\n"
            "           ++ ([[], ['B'], ['m'], ['n']] : List (List Char)).drop\n"
            "               ((([[], ['B'], ['m'], ['n']] : List (List Char))).length - 2)\n"
            "         = [['a', 'm'], ['m'], ['n']]))\n"
            + _IMPL,
            "prove_correct assembleInsertedLines by\n"
            "  loom_solve\n"
            "  all_goals decide\n"),
        "rationale": "ADMISSIBILITY on a total carrier: the obligation must be "
                     "SATISFIABLE and non-degenerate at an F2P-shaped input, else "
                     "it is PRECOND-TOO-STRONG in the only sense this backend can "
                     "express (a post-image no impl can meet is indistinguishable "
                     "from one every impl meets, and both would let the gate "
                     "record a pass that attests to nothing). Discharged BY "
                     "EVALUATION as an in-region `assert` at the F2P shape — a "
                     "content region whose first entry is empty and whose second "
                     "carries text, plus the two end-markers — before the frozen "
                     "obligation is closed verbatim. The three conjuncts pin: the "
                     "join leg is non-degenerate there (an interior boundary "
                     "survives); under the IDENTITY transform the pin's value "
                     "reconstructs the input exactly, so the obligation HOLDS at "
                     "this point rather than being unsatisfiable; and under a "
                     "REWRITING transform the value differs while the marker tail "
                     "is still the original two entries, so the obligation is not "
                     "a constant every impl meets. Must verify; else "
                     "PRECOND-TOO-STRONG (the obligation is unsatisfiable or "
                     "degenerate at exactly the input the fix is about). "
                     "NEGATIVE CONTROL (audit, real build): the same case with the "
                     "rewriting conjunct's pinned value perturbed to "
                     "[['a','m'],['n'],['m']] — the two markers transposed — is "
                     "REJECTED (EXIT 1, `decide` proves it false), so the assert "
                     "is doing work rather than being inert.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete (transform, lines) point. They attack the single top-level clause
    # (the pin P) on its distinct facets: whether the content is offered to
    # `transform` AT ALL, WHICH region is offered, how many markers are held out,
    # and the empty-body sub-domain.
    # =====================================================================

    # ---- (P) the content must be offered to `transform` and re-split ----
    {
        "id": "rival-forward-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # The gathered lines are forwarded UNCHANGED — the content is never
        # offered to the transform and never re-split. This is the pre-patch
        # behaviour: `out = lines`.
        "module": _impl(
            "    let out := lines\n"
            "    return out\n"),
        "refinement": "this is the pre-patch behaviour: the spliced-in content "
                      "reaches the parser without being offered to the registered "
                      "content transform at all. Its faithful real counterpart is "
                      "the un-patched flow, which FAILS both failing tests — a "
                      "registered transform never sees the included content, so a "
                      "rewrite it performs never reaches the parsed body and the "
                      "recorded-source assertion stays RED. It would NOT resolve.",
        "rationale": "REJECT from the pin P: forwarding `lines` verbatim yields "
                     "`lines`, but P requires `splitLines (transform (intercalate "
                     "content)) ++ markers`. At a REWRITING transform the two "
                     "differ. Refuted at transform = `fun _ => ['R','E','P']` and "
                     "lines = [['a'],['b'],['m'],['n']]: the rival returns the "
                     "input lines while P's content region becomes the split of "
                     "the constant — distinct lists. If it VERIFIES => "
                     "SPEC-TOO-WEAK (admits the un-patched flow).",
        "witness": _witness("fun _ => ['R','E','P']", "[['a'],['b'],['m'],['n']]"),
    },

    # ---- (P) the transform must actually be APPLIED, not skipped ----
    {
        "id": "rival-no-transform",
        "kind": "uniqueness",
        "expect": "reject",
        # Frames the markers correctly and even re-joins/re-splits the content
        # region, but SKIPS the transform: `splitLines (intercalate content)`
        # instead of `splitLines (transform (intercalate content))`. Correct only
        # for a transform that is the identity on the content; wrong for any
        # rewriting transform.
        "module": _impl(
            "    let content := lines.dropLast.dropLast\n"
            "    let out := splitLines (List.intercalate ['\\n'] content)\n"
            "                 ++ lines.drop (lines.length - 2)\n"
            "    return out\n"),
        "refinement": "re-joining and re-splitting the content while NOT offering "
                      "it to the registered transform leaves the content "
                      "unrewritten. Its faithful real counterpart omits the "
                      "transform step, so a registered rewrite never lands in the "
                      "parsed body — the failing test that asserts the rewritten "
                      "content reaches the output stays RED. It would NOT resolve.",
        "rationale": "REJECT from the pin P: the rival produces `splitLines "
                     "(intercalate content) ++ markers`, but P requires the "
                     "content to pass through `transform` first. These agree only "
                     "when `transform` is the identity on the content. Refuted at "
                     "transform = `fun _ => ['Q']` (a rewriting constant) and "
                     "lines = [['a'],['b'],['x'],['y']] (a DISTINCT point from the "
                     "verbatim rival, varying both binders): the rival keeps the "
                     "original content while P's content region becomes ['Q']. If "
                     "it VERIFIES => SPEC-TOO-WEAK (transform application "
                     "unpinned).",
        "witness": _witness("fun _ => ['Q']", "[['a'],['b'],['x'],['y']]"),
    },

    # ---- (P) the RIGHT region must be offered (markers excluded) ----
    {
        "id": "rival-offer-full-lines",
        "kind": "uniqueness",
        "expect": "reject",
        # Offers the FULL line sequence (markers INCLUDED) to the transform:
        # `intercalate lines` instead of `intercalate content`. The marker tail
        # is still reattached, but the content offered to the transform is wrong.
        "module": _impl(
            "    let out := splitLines (transform (List.intercalate ['\\n'] lines))\n"
            "                 ++ lines.drop (lines.length - 2)\n"
            "    return out\n"),
        "refinement": "offering the FULL sequence (the two structural end-markers "
                      "INCLUDED) to the transform means the markers are joined "
                      "into the offered text and parsed as authored content — the "
                      "exact semantic discriminator. A faithful counterpart that "
                      "drops the markers-excluding slice offers the wrong text, so "
                      "the failing test that checks the exact recorded content "
                      "(markers excluded) stays RED. It would NOT resolve.",
        "rationale": "REJECT from the pin P: P offers `intercalate content` "
                     "(markers excluded) whereas the rival offers `intercalate "
                     "lines` (markers included). Refuted at the IDENTITY transform "
                     "`fun s => s` and lines = [['a'],['b'],['m'],['n']]: under "
                     "identity, P's left part is `splitLines (intercalate "
                     "content)` (two content lines) while the rival's is "
                     "`splitLines (intercalate lines)` (all four joined) — "
                     "distinct lists even for the identity transform, so the "
                     "region choice alone is refuted. If it VERIFIES => "
                     "SPEC-TOO-WEAK (offered region unpinned).",
        "witness": _witness("fun s => s", "[['a'],['b'],['m'],['n']]"),
    },

    # ---- (P) exactly TWO markers held out, not one ----
    {
        "id": "rival-one-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one on the marker count: holds out only the LAST entry from the
        # transform (`dropLast` once; reattach `drop (length - 1)`) instead of the
        # final two. The blank-line marker is offered to the transform and only
        # the trailing marker is reattached.
        "module": _impl(
            "    let content := lines.dropLast\n"
            "    let out := splitLines (transform (List.intercalate ['\\n'] content))\n"
            "                 ++ lines.drop (lines.length - 1)\n"
            "    return out\n"),
        "refinement": "holding out only the LAST entry offers the second "
                      "structural marker to the transform and reattaches only the "
                      "final one, diverging from the required two-marker frame. A "
                      "faithful counterpart using a one-entry slice parses a "
                      "structural marker as content and reattaches the wrong tail, "
                      "so the failing test's marker-exclusion assertion stays RED. "
                      "It would NOT resolve.",
        "rationale": "REJECT from the pin P: P offers `content = dropLast.dropLast` "
                     "and reattaches `drop (length - 2)`; the rival offers "
                     "`dropLast` (one held out) and reattaches `drop (length - 1)`. "
                     "Refuted at transform = `fun _ => ['Z']` and lines = "
                     "[['a'],['b'],['m'],['n']]: the rival's marker tail is one "
                     "entry and its content region is a three-line join, while P's "
                     "tail is two entries — distinct lists. If it VERIFIES => "
                     "SPEC-TOO-WEAK (marker count unpinned).",
        "witness": _witness("fun _ => ['Z']", "[['a'],['b'],['m'],['n']]"),
    },

    # ---- (P) the re-split must use the FULL line-boundary set, not just LF ----
    {
        "id": "rival-lf-only-resplit",
        "kind": "uniqueness",
        "expect": "reject",
        # Offers the right region to the right transform and frames the markers
        # correctly, but re-splits the returned text on the NEWLINE character
        # ALONE (`List.splitOn '\n'`) instead of at every line boundary the host
        # language recognises. Indistinguishable from the frozen impl on any
        # transform whose output contains only LF boundaries — and wrong the
        # moment the transform emits any other boundary character.
        "module": _impl(
            "    let content := lines.dropLast.dropLast\n"
            "    let text := transform (List.intercalate ['\\n'] content)\n"
            "    let out := List.splitOn '\\n' text ++ lines.drop (lines.length - 2)\n"
            "    return out\n"),
        "refinement": "re-splitting the transformed text on the newline character "
                      "alone, rather than at every boundary the host language's "
                      "line splitter recognises, disagrees with the required "
                      "behaviour exactly when the registered transform emits a "
                      "non-newline boundary character. Its faithful real "
                      "counterpart hand-rolls a newline-only split in place of the "
                      "host splitter, so a transform that rewrites content to "
                      "contain any other boundary yields a line sequence the real "
                      "splitter would have divided further — a different parsed "
                      "body. It would NOT resolve for such a transform.",
        "rationale": "REJECT from the pin P: P re-splits with `splitLines`, whose "
                     "boundary set is the host language's full one, while the rival "
                     "uses a newline-only split. The two agree on LF-only text, so "
                     "this facet is invisible to every other rival in this battery "
                     "(all of which differ from P already at the identity or a "
                     "newline-free constant). Refuted at transform = `fun _ => "
                     "['a','\\r','b']` (a rewriting transform emitting a "
                     "CARRIAGE-RETURN boundary, a transform shape no other witness "
                     "uses) and lines = [['p'],['q'],['m'],['n']] (a distinct "
                     "content from every other witness): P's content region becomes "
                     "[['a'],['b']] — the carriage return IS a boundary, so the "
                     "full splitter divides there (measured by evaluation: "
                     "`splitLines ['a','\\r','b'] = [['a'],['b']]`) — while the "
                     "rival's newline-only split keeps ['a','\\r','b'] whole and "
                     "yields [['a','\\r','b']] — distinct lists. "
                     "If it VERIFIES => SPEC-TOO-WEAK (the boundary set of the "
                     "re-split is unpinned, and the spec would admit an "
                     "LF-only splitter that mapping.md §3.1 records as unfaithful).",
        "witness": _witness("fun _ => ['a','\\r','b']", "[['p'],['q'],['m'],['n']]"),
    },

    # ---- (P) the empty-body sub-domain (lines.length = 2) is pinned too ----
    {
        "id": "rival-partial-empty-body",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct whenever the content region is non-empty, but forwards VERBATIM
        # when the content is empty (`lines.length = 2`, the two-markers-only
        # shape the absence of a `require` admits). On that sub-domain it returns
        # `lines` instead of applying the transform to the empty content.
        "module": _impl(
            "    let content := lines.dropLast.dropLast\n"
            "    let out := if content = [] then lines\n"
            "               else splitLines (transform (List.intercalate ['\\n'] content))\n"
            "                      ++ lines.drop (lines.length - 2)\n"
            "    return out\n"),
        "refinement": "correct whenever the content is non-empty but forwarding "
                      "verbatim on an EMPTY content region means the transform is "
                      "never offered the empty content there. A faithful "
                      "counterpart that skips the transform for empty content "
                      "diverges from the always-offer behaviour — observable to a "
                      "transform that records every invocation or rewrites empty "
                      "text — so it would NOT resolve on that sub-domain.",
        "rationale": "REJECT from the pin P on the empty-body sub-domain: at "
                     "lines.length = 2 the content is empty, P requires "
                     "`splitLines (transform (intercalate [])) ++ markers` but the "
                     "rival returns `lines`. Refuted at transform = `fun _ => "
                     "['R','E','P']` and lines = [['m'],['n']] (the empty-body "
                     "boundary, a DISTINCT shorter `lines` from every other "
                     "witness): P's content region becomes the split of the "
                     "constant while the rival returns the two marker lines "
                     "unchanged — distinct lists. If it VERIFIES => SPEC-TOO-WEAK "
                     "(empty-body sub-domain unpinned).",
        "witness": _witness("fun _ => ['R','E','P']", "[['m'],['n']]"),
    },

    # ---- (P) the SHORT sub-domain (lines.length < 2) is pinned too ----
    {
        "id": "rival-partial-short-lines",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every sequence of two or more entries, but forwards VERBATIM
        # when there are FEWER than two. The absence of a `require` admits that
        # sub-domain, and on it the pin is still meaningful because the Nat
        # subtraction in `lines.length - 2` truncates to 0: P then demands
        # `splitLines (transform (intercalate [])) ++ lines`, which is NOT `lines`
        # for a rewriting transform. Added by audit: the shipped empty-body rival
        # stops at length = 2 and leaves lengths 0 and 1 entirely unprobed.
        "module": _impl(
            "    let out := if lines.length < 2 then lines\n"
            "               else splitLines (transform (List.intercalate ['\\n'] (lines.dropLast.dropLast)))\n"
            "                      ++ lines.drop (lines.length - 2)\n"
            "    return out\n"),
        "refinement": "forwarding verbatim when there are fewer than two entries "
                      "means the transform is never offered the content for a "
                      "degenerate sequence. Its faithful real counterpart guards "
                      "the transform step on having at least the two structural "
                      "end-markers present, so for a shorter sequence the "
                      "registered transform is skipped entirely and any rewrite it "
                      "would perform is lost — observable to a transform that "
                      "rewrites or records every invocation. It would NOT resolve "
                      "on that sub-domain.",
        "rationale": "REJECT from the pin P on the SHORT sub-domain the absence of "
                     "any `require` admits. At lines.length < 2 the truncating Nat "
                     "subtraction makes `lines.drop (lines.length - 2) = lines` and "
                     "`lines.dropLast.dropLast = []`, so P demands `splitLines "
                     "(transform (intercalate [])) ++ lines` — which differs from "
                     "the rival's bare `lines` for any transform that rewrites the "
                     "empty text. Refuted at transform = `fun _ => ['R','E','P']` "
                     "and lines = [] (length 0 — the shortest possible input, a "
                     "sub-domain NO other witness reaches: the shipped empty-body "
                     "witness sits at length 2): P prepends the split of the "
                     "constant while the rival returns the empty list — distinct "
                     "lists. If it VERIFIES => SPEC-TOO-WEAK (the short sub-domain "
                     "unpinned).",
        "witness": _witness("fun _ => ['R','E','P']", "([] : List (List Char))"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 1 frame-mutation, 4 uniqueness rivals)
# plus a 2-case AXIOM lane. This bundle models the SAME purely-functional core
# (the assembled line sequence handed to the line inserter for spliced-in
# content), so the map is close, with the frame/permission and axiom classes
# collapsing on this carrier.
#
#   sibling case (nagini)         -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder           -> pos-reorder                   PORTED
#   echo-attempt-honest           -> pos-inline                    PORTED (grounded)
#   admiss-f2p-shape              -> admiss-instance-present-ground PORTED BY AUDIT
#   frame-mutate-lines            -> (none)                        VACUOUS (no heap)
#   rival-forward-verbatim        -> rival-forward-verbatim        PORTED
#   rival-offer-full-lines        -> rival-offer-full-lines        PORTED
#   rival-one-marker              -> rival-one-marker              PORTED
#   partial-domain-empty-body     -> rival-partial-empty-body      PORTED
#   (no sibling)                  -> rival-no-transform            ADDED (transform binder)
#   (no sibling)                  -> rival-lf-only-resplit         ADDED BY AUDIT (splitter)
#   (no sibling)                  -> rival-partial-short-lines     ADDED BY AUDIT (short domain)
#   (no sibling)                  -> pos-take-content              ADDED BY AUDIT (content slice)
#   (no sibling)                  -> pos-reverse-markers           ADDED BY AUDIT (marker slice)
#   AXIOM_TESTS (x2)              -> (none)                        DROPPED (G-AX/no axioms)
#
# PORTED (2 positives): pos-reorder is the nagini statement-reorder positive;
#   pos-inline carries the nagini grounded-oracle honest control — the pin is a
#   function of the actual inputs (not an answer-key), so the cheapest honest
#   impl still applies `transform` to the modeled content region and there is no
#   verifying echo. Both keep the frozen `loom_solve` (verified, EXIT 0). Both are
#   DEFINITIONALLY equal to the frozen impl, which is why the audit added two
#   non-definitional positives beside them: a positive the frozen tactic closes
#   automatically cannot detect over-fitting, since nothing about it could have
#   failed. Kept anyway (they are the faithful port of the sibling's cases, and a
#   definitional reshape is still a real statement-order/binding probe).
# PORTED BY AUDIT (admissibility): the port recorded this lane VACUOUS on the
#   ground that the method declares no `require`, so "there is no precondition an
#   input could violate", and that the frozen `prove_correct` verifying already
#   shows the post-image is satisfiable. The AUDIT rejects both halves of that
#   reasoning. "No require" is not the right analogue on a TOTAL carrier: what
#   PRECOND-TOO-STRONG becomes here is the obligation being unsatisfiable — or
#   satisfiable but DEGENERATE — at exactly an F2P-shaped input, and that is
#   directly testable by discharging the pin at the concrete input BY EVALUATION.
#   Nor does the frozen proof cover it: `prove_correct` establishes the pin for
#   ALL inputs symbolically, which says nothing about whether the value at the
#   F2P shape is the one the fix is about (a spec whose pin collapsed to a
#   constant there would verify identically). So the lane was a real gap and is
#   now shipped as admiss-instance-present-ground, discharged at the F2P shape
#   with a negative control (perturbing the pinned value REJECTS, EXIT 1) proving
#   the assert is not inert.
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because its
#   read-only `lines` is held at `Acc(.,1/2)` an impl can illegally overwrite.
#   This backend is referentially transparent and declares no `mut` binder — both
#   inputs are immutable values with no heap footprint — so there is no read-only
#   field to overwrite and no substitute probe. Not fabricated. The nagini
#   intent (the marker frame is preserved) is instead pinned by the pin's tail
#   and attacked by rival-offer-full-lines / rival-one-marker.
#   AUDIT CONFIRMATION (real build): the closest expressible analogue — an impl
#   that SHADOWS the input (`let lines := []`) and computes the pin from the
#   shadow, the functional stand-in for overwriting a read-only reference — is
#   REJECTED, with the goal showing the spec's `lines` still bound to the
#   caller's value (`... intercalate [].dropLast.dropLast ... = ... intercalate
#   lines.dropLast.dropLast ...`). So the class is vacuous because a shadow
#   cannot reach the spec's binder, not merely because no `mut` is declared. Not
#   shipped as a case: a rival that is rejected for referring to the wrong value
#   attests to Lean's scoping, not to this spec.
# VACUOUS (divergence): the sibling here has no divergence case, and on this
#   `total`-termination bundle a diverging impl cannot verify — measured by the
#   audit with a real build of a `while true do i := i + 1` impl, REJECTED with
#   "Decreasing annotations are required in total correctness semantics". So the
#   class is CLOSED BY THE SEMANTICS. A loop CARRYING a non-decreasing measure is
#   refused as well (`while q > 0 ... decreasing q`, body `q := q`: rejected on
#   `case «decreasing_1: q»`, residual `q < q`), so this is not merely the
#   missing-annotation linter. The earlier reference to a `partial`-mode known hole in
#   an internal findings doc is withdrawn: all 500 velvet bundles read "total".
# ADDED (rival-no-transform): a rival with no direct sibling that skips the
#   transform APPLICATION while framing the markers and re-splitting correctly.
#   It attacks the `transform` binder specifically (refutable only at a rewriting
#   transform), sharpening the "content must actually pass through `transform`"
#   facet of the pin that the verbatim rival attacks only jointly with the
#   re-split.
# AXIOM_TESTS: dropped. There are no axioms in this bundle (`transform` is a
#   universally-quantified parameter, not an axiomatized callee;
#   `meta.json gates.G-AX.status = "skip"`) and the gate ignores AXIOM_TESTS
#   regardless.
#
# COVERAGE. The sole obligation (`prove_correct assembleInsertedLines`) is
# defended (four soundness positives plus one admissibility positive, which
# discharges the pin BY EVALUATION at an F2P-shaped input so the obligation is
# attested SATISFIABLE and non-degenerate exactly where the fix lives) and
# attacked (seven reject rivals). The single
# top-level postcondition clause (the pin P) is attacked on every distinct facet:
# whether the content is offered to `transform` at all (verbatim), whether the
# transform is applied (no-transform), WHICH region is offered (offer-full), how
# many markers are held out (one-marker), which SPLITTER re-splits the returned
# text (lf-only-resplit), the empty-body sub-domain (partial-empty-body), and the
# short sub-domain where the Nat subtraction truncates (partial-short-lines). Both
# of P's slices are additionally DEFENDED by a non-definitional faithful reshape
# (pos-take-content re-carves the content region, pos-reverse-markers the marker
# tail), so each slice is now probed from both sides. BOTH input binders are
# varied across the reject witnesses: `transform` over five distinct functions
# (the IDENTITY, three constants, and a boundary-emitting rewriter, so an
# identity-only, rewriting-only, or newline-only mishandling is caught) and
# `lines` over two distinct four-entry sequences, the two-entry empty-body
# boundary, and the empty sequence. Every reject witness was checked with two real
# builds: it ELABORATES against its rival (EXIT 0) and FAILS against the frozen
# solution (EXIT 1) — and on the frozen side the failure is `decide` PROVING the
# negation false, i.e. the kernel evaluated both sides and found gold equal to the
# pin, so no witness passes for a syntactic reason. No frame/permission or
# divergence rival is fabricated (both classes are vacuous on this
# referentially-transparent, total-termination carrier, each demonstrated with a
# real build above rather than asserted).
AXIOM_TESTS = []
