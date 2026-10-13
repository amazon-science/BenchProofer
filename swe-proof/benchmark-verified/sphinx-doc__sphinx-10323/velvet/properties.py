"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10323 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct assembleBlock`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method assembling a block of text lines over a
per-line, per-character carrier, ``List (List Char)``):

  assembleBlock (body : List (List Char)) (prefixText : List Char)
      (suffixText : List Char) (indent : Option Nat) return (out : List Char)
    ensures out = joinLines (addSuffix suffixText
                               (addPrefix prefixText (removeIndent indent body)))
                                                             -- the only clause

where the post-image is a TRANSPARENT composition of four spelled-out ``def``s
(directive 8), NOT an opaque answer-key:

  * ``removeIndent indent body`` — remove ``indent`` leading characters from
    every line of ``body`` (identity when ``indent = none``); reduces by
    ``List.map``;
  * ``addPrefix prefixText …`` — put one caller-supplied line before the block
    (nothing when the text is empty);
  * ``addSuffix suffixText …`` — put one caller-supplied line after the block;
  * ``joinLines`` — concatenate the assembled lines into one sequence.

Because the whole clause reduces to a concrete concatenation of the four inputs,
``decide`` computes it and no rival can "echo an oracle" — the only way to
satisfy the clause is to build the exact assembled sequence with the removal
applied to the BODY ALONE and the before/after lines emitted verbatim. The three
per-line transformations stand in for unchanged library routines validated equal
by G-AX (A-references); this gate ignores that lane.

WHAT THE SPEC DEFENDS. The discriminating content of the modeled fix is WHERE the
per-line leading-character removal is applied and WHICH lines are emitted
verbatim: the removal must reach the BODY only, so the caller-supplied
before/after lines keep their own leading whitespace exactly as supplied. That
behaviour is pinned by the whole-sequence equality (the removal is composed
INSIDE the before/after wrapping, applied to ``body`` before either line is
added). The reject rivals attack, in order: apply the removal to the whole
assembled block (the pre-fix order), apply it to the before-line too, drop it
from the body entirely, transpose the before/after lines, a partial-domain rival
that leaves only the FIRST body line untrimmed, and (added by the audit) a rival
that models the per-line removal as a bare drop, losing the retained newline on a
line the removal empties.

AUDIT NOTE (two independent re-derivations, all claims machine-checked). Attack A
found every variant's spec view byte-identical to the frozen one, and the
``method`` header, the whole ``ensures`` line and the entire ``pure`` region
present VERBATIM in every variant. Attack B rebuilt every reject witness twice:
each ELABORATES against its rival (exit 0) and FAILS on gold with
``Tactic `decide` proved that the proposition … is false`` — a plain EVALUATION,
so ``decide`` really did compute the tester on gold. Attack B′ (the forgery test)
then confirmed gold's exit code TRACKS THE CLAIM rather than reporting a carrier
limit: for all six witnesses, flipping the claim to ``= true`` — i.e. asserting
gold is WRONG at that input in the opposite direction — builds against the frozen
solution at exit 0. A claim and its negation get opposite verdicts on gold, which
is what makes the exit code evidence. Attack C confirmed each rival's assembled
sequence differs observably from gold's at its own witness point, by evaluating
both in Lean. Attack D found no hole in the frozen spec across seven wrong impls
(the first audit's two plus five more aimed at the after-line, a doubled removal,
a dropped newline terminator on the before line, a last-line sub-domain, and an
over-applied newline guard — every one REJECTED with ``unsolved goals`` on
``ensures_1``); the first audit's probe also surfaced the newline-preservation
sub-clause pinned by the spec yet demonstrated by NO case, which
``rival-drop-blank-collapse`` now closes. Attack E found no SPEC-TOO-STRONG hole:
three correct reshapes that the frozen ``loom_solve`` does not close on its own
are all PROVABLE once given a tactic body, and the strongest is kept as
``pos-commuted-wrap`` (whose equivalence to the frozen composition was re-checked
by exhaustive enumeration over 560 input tuples, 0 mismatches). The SECOND audit's
own findings were in the omission lane, not the case lane: the admissibility class
had been dropped for a reason the charter names as insufficient, and the
divergence class justified by a claim about the carrier that is false under
either termination semantics. Both are corrected above; a THIRD pass re-ran all
ten cases under both values of ``loom.semantics.termination`` (identical
behaviour) and recorded the ``"partial"`` divergence weakness as an escalation
rather than a battery gap.

BINDER STRUCTURE (read before judging binder coverage). The postcondition depends
on all FOUR inputs — ``body``, ``prefixText``, ``suffixText``, ``indent``:

  * ``indent`` selects whether the per-line removal fires (``none`` = identity,
    ``some k`` = drop ``k``). The removal-placement rivals differ from gold only
    when ``indent = some k`` with a body line longer than ``k`` and a before/after
    line whose leading run the removal would eat, so they are refuted at
    ``some k``. The transposition rival is independent of the removal, so it is
    refuted at ``indent = none`` — which keeps ``indent`` from being pinned at a
    ``some`` value across the whole battery.
  * ``body`` is the block the removal must reach; ``prefixText`` / ``suffixText``
    are the before/after lines that must stay verbatim. The rivals below vary all
    three across the witness set (bodies of different shapes; before/after lines
    with and without leading whitespace).

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this because its list
    inputs are held at a fractional heap permission (``Acc(.,1/2)``) an impl can
    illegally overwrite. Lean/Velvet are referentially transparent: every input
    here is an immutable value, there is no ``mut`` binder, no heap and no
    aliasing — so there is no read-only input to mutate and no substitute probe.
    Not fabricated (porting map: this class is vacuous here).
  * ADMISSIBILITY — PORTED, re-aimed (see ``admiss-assembled-nondegenerate``).
    An earlier revision of this file recorded the class as VACUOUS because the
    bundle declares no ``require`` clause. That reason is WRONG and the second
    audit replaced it: on a carrier whose precondition region is empty the
    PRECOND-TOO-STRONG analogue is not "a precondition rejects a normal input"
    but "the sole obligation is UNSATISFIABLE, or degenerate, at exactly an
    F2P-shaped input". That is a real question about this spec and it is
    answered by evaluating the post-image at a concrete input of the failing
    scenario's shape, which the case below does. The old reason also claimed
    such a probe "would reduce to the trivial ``joinLines (…) = joinLines (…)``";
    it does not, because the probe pins the post-image against an independently
    written concrete VALUE, and three liveness controls (each falsifying one
    conjunct) were measured to FAIL.
  * DIVERGENCE / NON-TERMINATION: CLOSED BY THE SEMANTICS, not shippable as a
    case, and NOT a spec hole. The nagini sibling carries no ``diverge-*`` /
    ``nonterm-*`` case, so there is no omission in the porting sense. An earlier
    revision justified the class by saying a diverging impl "cannot be written" on
    a referentially transparent carrier. That is FALSE and was measured false: a
    measure-free loop spliced into the impl region elaborates perfectly well. A
    LATER revision then said the disposition "turns entirely on
    ``loom.semantics.termination``", which this battery does not own, and set a
    ``"total"`` reading against a ``"partial"`` reading under which the same rival
    VERIFIES vacuously; it escalated that as a corpus-wide spec weakness. THAT IS
    RETRACTED IN FULL, on two grounds.

    First, the counterfactual has no referent. This bundle's ``Solution.lean``
    reads ``set_option loom.semantics.termination "total"``, as do all 500 velvet
    bundles (0 read ``"partial"``), and every one of them opens
    ``TotalCorrectness``. The two lines cannot disagree, because the ``set_option``
    elaborator ITSELF runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). So there is no ``partial``
    cohort, no prescribed ``partial -> total`` remediation outstanding, and no
    corpus-wide hole to escalate.

    Second, under ``total`` a postcondition is claimed of ALL runs, not only
    terminating ones, so the verifier demands a decreasing measure on every loop
    AND discharges its descent. That is a real obligation, not a syntactic
    formality, and it refuses the rival in BOTH of its shapes. Measured on this
    bundle with the proof reduced to a bare ``loom_solve``:

      - a spliced loop with NO measure is refused at the ``method`` declaration:
        ``error: Decreasing annotations are required in total correctness
        semantics``. The rival file does not elaborate at all, so no ``witness``
        can hold of it (the witness build fails on the RIVAL, the half that must
        succeed). Unshippable as a case for that mechanical reason.
      - the sharper shape, which cannot be dismissed as merely missing the
        annotation, CARRIES a measure that does not decrease
        (``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z``, body
        ``z := z + 1``). It is REJECTED on the measure's OWN goal:
        ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. Here the refusal
        lands at the ``prove_correct`` site rather than the declaration, so the
        rival's module does elaborate once that site is stripped; but the battery's
        witnesses still cannot project it, because the rival's post-image is an
        unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
        ``onDoneGadget`` / ``decreasingGadget``, which the kernel will not
        normalise to a value a tester can decide. So this shape is unshippable too,
        for a witness-channel reason and not because the spec admits the rival.

    Disposition: the spec REJECTS the class, and the battery simply cannot attest
    to that rejection through the concrete-input witness channel this gate
    requires. All ten cases below were re-verified against the frozen ``"total"``
    file (4 verify / 6 reject), so the battery's verdict rests on the semantics the
    corpus actually has.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent composition of
    spelled-out ``def``s over the method inputs, not an axiomatized oracle; the
    ``axioms`` region declares no ``axiom``. The cheapest-render positive control
    stands in for the nagini no-echo control.
  * AXIOM lane (nagini's empty axiom lane) — DROPPED. The three per-line
    transformations are A-references validated by G-AX; this gate ignores
    ``AXIOM_TESTS`` regardless.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``assembleBlockTester body prefixText suffixText indent = false`` says the
extracted program's result violates the postcondition at that concrete input. It
is checked in a file whose ``prove_correct`` block has been stripped (so no
tactic script can mask the verdict) and there are no ``require`` clauses, so every
input reaches the postcondition. ``List (List Char)`` / ``List Char`` literals via
``[…]`` and ``Option Nat`` literals are fully concrete, so ``decide`` settles the
whole equality — no opaque term, no conditioning, no head binders (hence no
consistency obligation). Every witness below was confirmed with two real builds:
it ELABORATES against its rival (``decide`` proves the tester ``= false``) and
FAILS against the frozen solution (``decide`` proves the same proposition is
FALSE — gold's assembled sequence satisfies the clause at that input).
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10323"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The COMPLETE frozen impl body (comments + three-`let`
# ---- assembly); lies wholly inside the single `-- impl-start`/`-- impl-end`
# ---- region and is unique in Solution.lean (both facts asserted at load by
# ---- _swap). Anchoring on the whole body keeps every surgery inside the elided
# ---- region — the `method` header, `ensures`, and the `pure` region are never
# ---- touched, so same_spec holds by construction. ----
_IMPL = (
    "    -- impl-start\n"
    "    -- Indentation removal runs FIRST, on the body alone; only afterwards are the\n"
    "    -- before/after lines added, so they escape the removal.\n"
    "    let trimmed  := removeIndent indent body\n"
    "    let withHead := addPrefix prefixText trimmed\n"
    "    let withTail := addSuffix suffixText withHead\n"
    "    return joinLines withTail\n"
    "    -- impl-end"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble: reach the contract through Velvet's tester machinery.
# ---- The directives declare `assembleBlockTester` inside the witness, so it
# ---- exists on BOTH the rival and the frozen builds (both get the witness
# ---- appended). No `require`, so every input reaches the postcondition. ----
_TESTER = (
    "extract_program_for assembleBlock\n"
    "prove_precondition_decidable_for assembleBlock\n"
    "prove_postcondition_decidable_for assembleBlock\n"
    "derive_tester_for assembleBlock\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


# ---- frozen proof-script anchor. `prove_correct`'s TACTIC BODY is elided by the
# ---- consumer spec view exactly like the impl region, so a variant may supply
# ---- its own script and still satisfy `markers.same_spec` (asserted at load by
# ---- _swap; the `method` header and `ensures` are never touched). This is what
# ---- lets a positive control reshape the impl into a form the frozen
# ---- `loom_solve` alone does not close and still DISCHARGE the obligation ----
_PROOF = "prove_correct assembleBlock by\n  loom_solve"


def _with_impl_and_proof(new_impl: str, new_proof: str) -> str:
    """Solution.lean with the impl body AND the tactic body replaced."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both verified out-of-band with a
    # real build against the frozen `prove_correct … by loom_solve` script.
    # =====================================================================
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        # The three intermediate `let`s are collapsed into two: the removal is
        # bound once, then the before/after wrapping is composed in a single
        # `let` (same composition order `addSuffix (addPrefix (removeIndent …))`),
        # then joined. Every computed value is identical; only the statement
        # layout differs. Ports the nagini pos-control-reshape (which likewise
        # reshapes the executable form while preserving the composition).
        "module": _with_impl(
            "    -- impl-start\n"
            "    let trimmed := removeIndent indent body\n"
            "    let assembled := addSuffix suffixText (addPrefix prefixText trimmed)\n"
            "    return joinLines assembled\n"
            "    -- impl-end"),
        "rationale": "structurally-different (the before/after wrapping bound in "
                     "one intermediate instead of two) but semantically identical "
                     "impl must verify against the whole-sequence equality — the "
                     "composition order removeIndent→addPrefix→addSuffix→joinLines "
                     "is preserved, so every computed value is unchanged. If it "
                     "fails to verify, the spec is over-fit to one statement "
                     "layout => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-cheapest-render",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl satisfying the clause: return the transparent
        # composition directly, with no named intermediates. Because the
        # post-image is a spelled-out `def` composition over the four inputs (not
        # an opaque oracle), this still does the real assembly — there is no wrong
        # echo that verifies. Re-expresses the nagini no-echo (echo-honest)
        # control on a carrier with no @Pure marker to echo.
        "module": _with_impl(
            "    -- impl-start\n"
            "    return joinLines (addSuffix suffixText"
            " (addPrefix prefixText (removeIndent indent body)))\n"
            "    -- impl-end"),
        "rationale": "the cheapest impl satisfying the clause still builds the "
                     "exact assembled sequence, because the post-image is a "
                     "transparent composition of the four inputs — not an "
                     "axiomatized answer key. Demonstrates the spec is NOT "
                     "echo-vulnerable: there is no wrong echo that could verify "
                     "(else this would be a reject case). Must verify.",
    },

    {
        "id": "pos-commuted-wrap",
        "kind": "soundness",
        "expect": "verify",
        # STRONGEST positive control: the before/after wrapping is applied in the
        # OPPOSITE order (`addPrefix` outermost, `addSuffix` innermost) to the
        # composition the clause spells out. The two wrapping stages genuinely
        # commute — one puts a line at the front, the other at the end, and each
        # is guarded by its own empty-text test — so this is a faithful correct
        # impl, but it is NOT definitionally equal to the frozen composition:
        # deciding it needs a case split on the two emptiness guards. Confirmed
        # semantically exact by exhaustive enumeration over 625 input tuples
        # (bodies incl. empty/blank lines, both texts empty and non-empty,
        # `indent` in none/0..3), and the two `let`-bound stages are reversed from
        # every other positive, so this control cannot pass by reducing to the
        # frozen impl's shape.
        #
        # Unlike the other positives it therefore carries its OWN tactic body:
        # the frozen `loom_solve` alone leaves the goal
        # `joinLines (addPrefix p (addSuffix s t)) = joinLines (addSuffix s
        # (addPrefix p t))` unsolved, which is a proof-shape gap and NOT a spec
        # defect — the tactic body is elided by the spec view, so supplying a
        # script is in scope and `same_spec` still holds. This is the case that
        # actually exercises SPEC-TOO-STRONG: it shows the clause admits an impl
        # whose assembly order differs, rather than only impls definitionally
        # equal to the frozen one.
        "module": _with_impl_and_proof(
            "    -- impl-start\n"
            "    let trimmed  := removeIndent indent body\n"
            "    let withTail := addSuffix suffixText trimmed\n"
            "    let withHead := addPrefix prefixText withTail\n"
            "    return joinLines withHead\n"
            "    -- impl-end",
            "prove_correct assembleBlock by\n"
            "  loom_solve\n"
            "  cases hp : prefixText.isEmpty <;> cases hs : suffixText.isEmpty <;>\n"
            "    simp [addPrefix, addSuffix, hp, hs]"),
        "rationale": "a faithful correct impl that applies the two wrapping "
                     "stages in the OPPOSITE order to the one the clause spells "
                     "out (addPrefix outermost instead of innermost). The stages "
                     "commute — each adds one line at a different end under its "
                     "own empty-text guard — so the assembled sequence is "
                     "identical at every input (checked exhaustively over 625 "
                     "tuples), but it is NOT definitionally equal to the frozen "
                     "composition: closing it needs a case split on both "
                     "emptiness guards. Must verify; if it could not be proven at "
                     "all the clause would be over-fit to one association of the "
                     "wrapping => SPEC-TOO-STRONG. Distinct from the other two "
                     "positives, which are definitionally equal to the frozen "
                     "impl and so test only statement layout.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane) — the obligation must be
    # SATISFIABLE, and non-degenerate, at a concrete input shaped like the
    # scenario the failing test exercises.
    # =====================================================================
    {
        "id": "admiss-assembled-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # Added by the second audit. This bundle's pre-conditions region is
        # empty, so there is no `require` for an F2P-shaped input to fail — but
        # that is NOT a reason to drop the lane, it is a reason to re-aim it.
        # On a total carrier the analogue of PRECOND-TOO-STRONG is the sole
        # obligation being unsatisfiable (or degenerate) at exactly the kind of
        # input the failing scenario supplies. So the impl region opens with a
        # `have` that discharges the post-image BY EVALUATION at one concrete
        # tuple of that shape — a three-line body whose last line is a bare
        # separator, a before line and an after line that BOTH carry their own
        # leading whitespace, and a removal amount of 2 — and only then runs the
        # frozen impl body verbatim, so the frozen obligation still closes on
        # its own terms under the frozen `loom_solve`.
        #
        # TWO-SIDED, so a collapsed post-image could not satisfy it:
        #   conjunct 1 pins the assembled value exactly (the body's three lines
        #     each lose 2 leading chars, the emptied separator line KEEPS its
        #     newline, and both caller-supplied lines keep their own leading
        #     whitespace);
        #   conjunct 2 states the assembled value is NOT the one a post-image
        #     that let the removal reach the caller-supplied lines would give —
        #     this is what makes the point non-degenerate at exactly the
        #     sub-domain the failing scenario is about;
        #   conjunct 3 pins the `indent = none` point, where the body must come
        #     through untouched, so a post-image that removed unconditionally
        #     would fail here.
        # Liveness measured, not asserted: three variants each falsifying ONE
        # conjunct were built and each FAILS (exit 1, "`decide` proved that the
        # proposition ... is false"), so the `have` is load-bearing rather than
        # decorative. The real case verifies (exit 0).
        "module": _with_impl(
            "    -- impl-start\n"
            "    have _admissible :\n"
            "        joinLines (addSuffix \"  t\".toList (addPrefix \"    b\".toList\n"
            "            (removeIndent (some 2)\n"
            "              [\"    p q\\n\".toList, \"      r\\n\".toList, \"\\n\".toList])))\n"
            "            = \"    b\\n  p q\\n    r\\n\\n  t\\n\".toList\n"
            "        \u2227 joinLines (addSuffix \"  t\".toList (addPrefix \"    b\".toList\n"
            "            (removeIndent (some 2)\n"
            "              [\"    p q\\n\".toList, \"      r\\n\".toList, \"\\n\".toList])))\n"
            "            \u2260 \"  b\\n  p q\\n    r\\n\\nt\\n\".toList\n"
            "        \u2227 joinLines (addSuffix \"  t\".toList (addPrefix \"    b\".toList\n"
            "            (removeIndent none\n"
            "              [\"    p q\\n\".toList, \"      r\\n\".toList, \"\\n\".toList])))\n"
            "            = \"    b\\n    p q\\n      r\\n\\n  t\\n\".toList := by\n"
            "      decide\n"
            "    let trimmed  := removeIndent indent body\n"
            "    let withHead := addPrefix prefixText trimmed\n"
            "    let withTail := addSuffix suffixText withHead\n"
            "    return joinLines withTail\n"
            "    -- impl-end"),
        "rationale": "PRECOND-TOO-STRONG probe, aimed at what that direction IS "
                     "on a total carrier whose pre-conditions region is empty: "
                     "the sole obligation must be SATISFIABLE and "
                     "NON-DEGENERATE at an input shaped like the failing "
                     "scenario. The `have` discharges the post-image BY "
                     "EVALUATION at a concrete tuple of that shape (a "
                     "three-line body ending in a bare separator, before/after "
                     "lines that both carry leading whitespace, removal amount "
                     "2) before the frozen obligation is closed verbatim. It is "
                     "two-sided: one conjunct pins the assembled value exactly, "
                     "one states it is NOT the value a post-image that let the "
                     "removal reach the caller-supplied lines would give, and "
                     "one pins the no-removal point. A post-image that "
                     "admitted no value at this input, or that collapsed to a "
                     "constant, would fail one of the three. If this could not "
                     "be discharged the obligation would be unsatisfiable at "
                     "exactly the input the failing test exercises => "
                     "PRECOND-TOO-STRONG. The impl body below the `have` is "
                     "byte-identical to the frozen one, so the frozen "
                     "`loom_solve` still discharges the obligation itself; the "
                     "`have` is named with a leading underscore and is never "
                     "used, so it cannot help close it. Re-aimed from the "
                     "nagini `admiss-f2p-shape`, whose "
                     "precondition-admits-an-F2P-input half has no counterpart "
                     "on a require-free carrier.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input (ELABORATES against the rival, FAILS against gold — both
    # halves confirmed out-of-band with real builds) and the refinement argument
    # for why its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "rival-prepatch-trim-all",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix behaviour: add the before/after lines FIRST, then apply the
        # per-line removal to the WHOLE assembled block, so the caller-supplied
        # lines are trimmed too. Its faithful real counterpart is precisely the
        # un-patched pipeline order.
        "module": _with_impl(
            "    -- impl-start\n"
            "    let assembled := addSuffix suffixText (addPrefix prefixText body)\n"
            "    return joinLines (removeIndent indent assembled)\n"
            "    -- impl-end"),
        "refinement": "this is the actual pre-fix ordering — the per-line "
                      "leading-character removal is the LAST stage, so it strips "
                      "the caller-supplied before/after lines after they were "
                      "inserted. Its faithful real counterpart is the un-patched "
                      "read pipeline, which strips the leading whitespace off the "
                      "before line (emitting the fused text the issue reports "
                      "instead of the verbatim line) and so still fails the "
                      "failing test that pins the verbatim before line. It would "
                      "NOT resolve.",
        "rationale": "REJECT from the whole-sequence equality: the post-image "
                     "applies removeIndent to `body` ALONE and emits the "
                     "before/after lines verbatim; the pre-patch order applies it "
                     "to the whole assembled block, so the first assembled line is "
                     "the trimmed before line where the post-image demands it "
                     "verbatim. The rendered sequences differ. If it verified => "
                     "SPEC-TOO-WEAK (admits the un-patched order). Refuted at "
                     "`indent = some 2` with a before line carrying leading "
                     "whitespace.",
        "witness": _witness(
            "assembleBlockTester [[' ', ' ', 'x']] [' ', 'P'] [' ', 'S'] (some 2)"),
    },
    {
        "id": "rival-trim-before-line",
        "kind": "uniqueness",
        "expect": "reject",
        # SHARPEST discriminator: add the before line FIRST, then remove, then add
        # the after line — so the removal reaches the before line (and the body)
        # but not the after line. Correct on the body and the after line; wrong
        # exactly on the before line, which is emitted trimmed instead of verbatim.
        "module": _with_impl(
            "    -- impl-start\n"
            "    let withHead := addPrefix prefixText body\n"
            "    let trimmed := removeIndent indent withHead\n"
            "    return joinLines (addSuffix suffixText trimmed)\n"
            "    -- impl-end"),
        "refinement": "the removal reaches the before line (it is added before the "
                      "removal fires) so its leading whitespace is stripped, while "
                      "the after line stays verbatim. Its faithful real "
                      "counterpart moves only the after-line stage ahead of the "
                      "removal, leaving the removal reaching the before line — it "
                      "still emits the before line with its leading whitespace "
                      "stripped and fails the failing test that pins the verbatim "
                      "before line. It would NOT resolve.",
        "rationale": "REJECT from the whole-sequence equality: the post-image "
                     "emits `prefixText` verbatim (the removal is applied to "
                     "`body` before `addPrefix`); this rival emits the removed "
                     "before line, so the first assembled line differs. Correct on "
                     "the body and after line, wrong on the before line "
                     "(partial-domain within the clause). If it verified => "
                     "SPEC-TOO-WEAK (verbatim-before clause hollow). Refuted at "
                     "`indent = some 1` with a before line carrying leading "
                     "whitespace — a distinct input point and a distinct `indent` "
                     "value from rival-prepatch-trim-all.",
        "witness": _witness(
            "assembleBlockTester [[' ', 'y']] [' ', 'Q'] [' ', 'R'] (some 1)"),
    },
    {
        "id": "rival-no-trim-body",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the per-line removal from the body entirely; the before/after lines
        # are correct. The body is emitted verbatim (un-trimmed) where the
        # post-image demands each of its lines have `indent` leading chars removed.
        "module": _with_impl(
            "    -- impl-start\n"
            "    return joinLines (addSuffix suffixText (addPrefix prefixText body))\n"
            "    -- impl-end"),
        "refinement": "drops the per-line leading-character removal from the body "
                      "entirely. Its faithful real counterpart removes the "
                      "dedent stage from the pipeline, leaving the included body "
                      "un-dedented — it emits the body with its original "
                      "indentation instead of the dedented body and so fails the "
                      "failing test that pins the dedented body. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the whole-sequence equality: the post-image "
                     "applies removeIndent to `body`, so with `indent = some k` "
                     "and a body line longer than `k` the assembled sequence "
                     "differs from the rival's verbatim body. If it verified => "
                     "SPEC-TOO-WEAK (the body-removal unpinned). Refuted at "
                     "`indent = some 2` with a body line of leading whitespace — "
                     "a distinct input point.",
        "witness": _witness(
            "assembleBlockTester [[' ', ' ', 'z']] ['A'] ['B'] (some 2)"),
    },
    {
        "id": "rival-swap-before-after",
        "kind": "uniqueness",
        "expect": "reject",
        # Transpose the before/after lines: the after line is added at the front
        # and the before line at the end. Interior removal correct, but the two
        # caller lines are in the wrong positions. Independent of the removal, so
        # refuted at `indent = none` — the point that varies `indent` off `some`.
        "module": _with_impl(
            "    -- impl-start\n"
            "    let trimmed := removeIndent indent body\n"
            "    return joinLines (addSuffix prefixText (addPrefix suffixText trimmed))\n"
            "    -- impl-end"),
        "refinement": "puts the after line at the front and the before line at the "
                      "end. Its faithful real counterpart transposes the "
                      "before/after stages, so the assembled block leads with the "
                      "after text and trails with the before text — the failing "
                      "test that pins the before line first and the after line "
                      "last still fails. It would NOT resolve.",
        "rationale": "REJECT from the whole-sequence equality: the post-image "
                     "prepends `prefixText` and appends `suffixText`; this rival "
                     "prepends `suffixText` and appends `prefixText`, so the first "
                     "and last assembled lines are swapped. Independent of the "
                     "removal, so refuted at `indent = none` — the witness that "
                     "VARIES `indent` off a `some` value across the battery. If it "
                     "verified => SPEC-TOO-WEAK (line order unpinned).",
        "witness": _witness(
            "assembleBlockTester [[' ', ' ', 'x']] ['P'] ['S'] none"),
    },
    {
        "id": "rival-partial-first-line",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: leave the FIRST body line verbatim while removing from
        # the rest. Correct on every body whose first line is shorter than the
        # removal (or empty), wrong on any block whose first line is longer.
        "module": _with_impl(
            "    -- impl-start\n"
            "    let trimmed := match indent, body with\n"
            "      | some k, l :: ls => l :: ls.map (removeIndentLine k)\n"
            "      | _, _ => removeIndent indent body\n"
            "    return joinLines (addSuffix suffixText (addPrefix prefixText trimmed))\n"
            "    -- impl-end"),
        "refinement": "removes from every body line EXCEPT the first. Its faithful "
                      "real counterpart has an off-by-one in the dedent loop "
                      "(starts at the second line), so the first body line keeps "
                      "its original indentation while the rest are dedented — the "
                      "failing test that pins the dedented first body line still "
                      "fails. It would NOT resolve.",
        "rationale": "partial-domain: pins only body[1:]. REJECT from the "
                     "whole-sequence equality — the post-image removes `indent` "
                     "leading chars from EVERY body line including the first; this "
                     "rival emits body[0] verbatim, so the first body line differs "
                     "on any block whose first line is longer than `indent`. If it "
                     "verified => SPEC-TOO-WEAK (first-line sub-domain unpinned). "
                     "Refuted at `indent = some 1` with a two-line body whose "
                     "first line is longer than 1 — a distinct input point (a "
                     "multi-line body, unlike every other rival).",
        "witness": _witness(
            "assembleBlockTester [['a', 'b', 'c'], ['d', 'e', 'f']] ['P'] ['S'] (some 1)"),
    },
    {
        "id": "rival-drop-blank-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # The per-line removal is a PLAIN drop: it omits the sub-clause that a
        # line emptied by the removal, but which originally ended in a newline,
        # keeps a lone newline. Wrong ONLY on a body line whose whole content is
        # consumed by the removal and which carried a trailing newline — that
        # separator line is collapsed away instead of preserved. Every other line
        # (and both wrapping stages, and `indent = none`) is correct, so this is
        # the narrowest sub-domain in the battery.
        #
        # Added by the audit: the five rivals above all attack WHERE the removal
        # is applied or WHICH lines are emitted, and every one of their witness
        # points is a line strictly longer than `indent`, where a plain drop and
        # the real per-line removal AGREE. So the newline-preservation sub-clause
        # of `removeIndentLine` was pinned by the spec but demonstrated by no
        # case; this rival is refuted exactly there, at a body of one blank
        # separator line with `indent = some 1`.
        "module": _with_impl(
            "    -- impl-start\n"
            "    let trimmed := match indent with\n"
            "      | none   => body\n"
            "      | some k => body.map (fun line => line.drop k)\n"
            "    return joinLines (addSuffix suffixText (addPrefix prefixText trimmed))\n"
            "    -- impl-end"),
        "refinement": "models the per-line removal as a bare suffix-drop, losing "
                      "the case where a line consumed entirely by the removal but "
                      "originally newline-terminated keeps a lone newline. Its "
                      "faithful real counterpart omits that one guard from the "
                      "per-line routine, so a blank separator line inside the "
                      "included body is deleted rather than preserved: the "
                      "assembled text loses a line break and the failing test, "
                      "which pins the body's blank separator, still fails. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the whole-sequence equality: the post-image "
                     "applies `removeIndent`, whose per-line step preserves a "
                     "newline-only remainder, so at a body line that the removal "
                     "empties the post-image demands a retained newline where "
                     "this rival emits nothing. If it verified => SPEC-TOO-WEAK "
                     "(the newline-preservation sub-clause hollow — it is pinned "
                     "by the frozen `def` but was demonstrated by no other case, "
                     "since every other witness uses lines longer than `indent`, "
                     "where a plain drop agrees). Refuted at `indent = some 1` "
                     "with a one-line body that is a bare separator — a distinct "
                     "input point and a body shape no other rival probes.",
        "witness": _witness(
            "assembleBlockTester [['\\n']] ['P'] ['S'] (some 1)"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 echo-honest positive, 1 admissibility, 5 uniqueness rivals) plus an
# empty AXIOM lane. This bundle models the SAME functional core (the assembled
# block over a per-line carrier), so the SPEC lane ports almost directly; the
# permission and precondition classes are vacuous on a referentially-transparent
# carrier with no `require`.
#
#   sibling case                 -> here
#   ---------------------------------------------------------------------
#   pos-control-reshape          -> pos-reshape                 PORTED
#   echo-honest (no-echo)        -> pos-cheapest-render          RE-EXPRESSED
#   admiss-f2p-shape             -> admiss-assembled-nondegenerate  PORTED, RE-AIMED
#                                                                (audit 2; was
#                                                                wrongly VACUOUS)
#   (no sibling)                 -> pos-commuted-wrap            ADDED (audit, attack E)
#   (no sibling)                 -> rival-drop-blank-collapse    ADDED (audit, attack D)
#   rival-prepatch-trim-all      -> rival-prepatch-trim-all      PORTED
#   rival-trim-lead-only         -> rival-trim-before-line       PORTED
#   rival-no-trim-included       -> rival-no-trim-body           PORTED
#   rival-swap-lead-trail        -> rival-swap-before-after      PORTED
#   rival-partial-first-line     -> rival-partial-first-line     PORTED
#   AXIOM_TESTS (empty)          -> (none)                       DROPPED (G-AX lane)
#
# 5 uniqueness rivals ported one-for-one (every postcondition sub-region a nagini
# rival attacked — pre-patch order, the before-line verbatim, the body removal,
# the line order, the first-line sub-domain — is attacked here); 1 soundness
# positive ported; 1 re-expressed; 1 admissibility ported and re-aimed. NONE
# dropped for difficulty. The AUDIT then added two cases with no sibling, for gaps
# the nagini carrier did not have: `rival-drop-blank-collapse` (this carrier's
# per-line removal has a newline-preservation sub-clause the nagini `.drop(n)`
# model lacks entirely, so no sibling rival could attack it) and
# `pos-commuted-wrap` (a correct reshape NOT definitionally equal to the frozen
# impl, which the two ported positives do not supply — both of them reduce to the
# frozen composition, so they test statement layout rather than admissibility of a
# genuinely different assembly order).
#
# RE-EXPRESSED (pos-cheapest-render): nagini's echo-honest control asserts, after
#   the result is fully built, that it equals the @Pure grounded pin, to show no
#   wrong echo verifies. Here the post-image is a transparent `def` composition
#   (no @Pure PSeq to echo), so the equivalent demonstration is the cheapest
#   correct impl — return the composition directly. It verifies (real build), and
#   because the composition reduces to the exact assembled sequence there is no
#   wrong echo that could verify. Same argument, expressed for this carrier.
# PORTED / RE-AIMED (admissibility): the first audit recorded this class as
#   VACUOUS on the ground that the bundle declares no `require` clause. The
#   second audit rejected that reason and landed the case. "The frozen
#   obligation has no precondition" is not a demonstration of vacuity: the
#   analogue on a total carrier is the obligation being unsatisfiable — or
#   degenerate — at exactly an F2P-shaped input, which a positive that
#   discharges the post-image at that concrete input BY EVALUATION, as a `have`,
#   before closing the frozen obligation verbatim, tests directly. It also
#   claimed such a probe "would reduce to `joinLines (…) = joinLines (…)`",
#   which is false: the probe pins the post-image against an independently
#   written concrete VALUE, and the three liveness controls (each falsifying one
#   conjunct) were each measured to FAIL exit 1. See
#   `admiss-assembled-nondegenerate`.
# VACUOUS (frame-mutation): N/A on nagini too here — but the nagini sibling itself
#   documents FRAME-MUTATION as N/A for this instance (all inputs are pure
#   immutable PSeq, no list_pred/Acc), so there is no sibling case to port. On
#   this backend it is doubly vacuous (referentially transparent, no `mut`
#   binder, no heap). No substitute fabricated.
# NOTHING TO SHIP (divergence), for the measured reason rather than the asserted
#   one: the nagini sibling carries no diverge-*/nonterm-* case, so nothing was
#   dropped. The first audit's stated reason — "a diverging impl cannot be
#   written" on a referentially transparent carrier — is FALSE and the second
#   audit measured it false: a measure-free loop spliced into the impl region
#   elaborates fine. The disposition then turns on
#   `loom.semantics.termination`, whose two values INVERT it, so the third audit
#   measured both on this bundle instead of asserting one:
#     "total"   -> rival REFUSED with `error: Decreasing annotations are required
#                  in total correctness semantics` before the `ensures` is ever
#                  consulted. Rejection attributable to the flag, not the spec;
#                  and the rival file does not elaborate at all, so no `witness`
#                  can hold of it (the witness build fails on the RIVAL, the half
#                  that must succeed). Unshippable; no spec hole.
#     "partial" -> the same rival VERIFIES at exit 0 while returning the WRONG
#                  answer (measure-free loop + `return []` builds clean; the
#                  identical `return []` without the loop is rejected `unsolved
#                  goals` under both values). A genuine SPEC weakness, escalated
#                  rather than patched here — an `expect="reject"` case would be
#                  recorded as behaving wrongly.
#   Known corpus-wide finding with remediation already prescribed (`partial` ->
#   `total` plus a `decreasing` measure); not peculiar to this cell. All ten
#   cases were re-run under BOTH values and behave identically, so this
#   battery's verdict does not depend on which is in force.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause depends on all four inputs.
#   The six reject witnesses probe six DISTINCT input tuples:
#     blank    : [['\n']]                      ['P']      ['S']      (some 1)
#     prepatch : [[' ',' ','x']]              [' ','P']  [' ','S']  (some 2)
#     before   : [[' ','y']]                  [' ','Q']  [' ','R']  (some 1)
#     no-trim  : [[' ',' ','z']]              ['A']      ['B']      (some 2)
#     swap     : [[' ',' ','x']]              ['P']      ['S']      none
#     partial  : [['a','b','c'],['d','e','f']] ['P']     ['S']      (some 1)
#   Across them `indent` takes {some 1, some 2, none} — the removal-placement
#   rivals are refuted at `some`, the transposition rival at `none`, so `indent`
#   is not pinned at one value; `body` ranges over single-line, multi-line and
#   blank-separator blocks and over leading-whitespace and plain content;
#   `prefixText` / `suffixText` range over leading-whitespace and plain lines.
#   Every distinct sub-region of the whole-sequence clause a nagini rival attacked
#   is attacked at a distinct input point.
#   The variation is MEANINGFUL, not two spellings of one point: at each witness
#   tuple the rival's assembled sequence was computed and differs from gold's, and
#   the `blank` point is the only one where a bare per-line drop and the frozen
#   per-line removal disagree (at every other point they AGREE, which is precisely
#   why that case had to be added). Each witness was confirmed with two real builds to
#   ELABORATE against its rival (tester `= false` by `decide`) and FAIL against
#   the frozen solution (`decide` proves the same tester proposition is FALSE — a
#   real discriminator, not a tautology).
#
# AXIOM_TESTS: dropped. The three per-line transformations are A-references
# validated by G-AX (axiom_check.py); the G-PBT gate ignores AXIOM_TESTS
# regardless, and the nagini axiom lane is itself empty.
AXIOM_TESTS = []
