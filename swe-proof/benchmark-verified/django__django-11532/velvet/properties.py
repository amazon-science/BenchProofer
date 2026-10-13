"""properties.py — G-PBT falsification battery for django__django-11532 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region is changed, and it is elided from the consumer spec view,
so ``markers.same_spec`` holds and the ``prove_correct punycodeDomain``
obligation survives with its header intact) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes
iff (in scope AND the file elaborates with every obligation closed);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled method over a per-code-point host name carrier):

  punycodeDomain (host : List Char) return (out : List Char)
    ensures out = aceEncode host                    -- (Q1) VALUE pin
    ensures ∀ c ∈ out, c.val.toNat < 128            -- (Q2) all-ASCII

The desired behaviour: the host name obtained from the environment is returned
in its ASCII-compatible encoding rather than verbatim, so that it is safe to
embed in a header later rendered with a single-byte (non-Unicode) charset. The
method has NO ``require`` clause, so the admitted input domain is total. There
is exactly ONE input binder, ``host``.

CARRIER — the decisive fact of this port. ``aceEncode : List Char → List Char``
is an OPAQUE axiom; the only property the kernel knows about it is
``aceEncode_ascii`` (its output is all-ASCII). Its value at any concrete input
is unknown, which is exactly what keeps the surface faithful (no concrete
encoded value is pinned — directive 7/8). This governs which nagini cases port
and, crucially, HOW each reject clause is witnessed:

  * (Q2) all-ASCII is TRANSPARENT once the returned value is in hand: a rival
    whose output carries a non-ASCII code point violates Q2 at a concrete input,
    decidable WITHOUT evaluating ``aceEncode``. The raw-passthrough rival
    (return the host verbatim) is refuted this way at a non-ASCII host.
  * (Q1) the value pin references the opaque ``aceEncode host``, so it cannot be
    decided at a literal. It is attacked on TWO facets, one of which needs no
    assumption at all:
      - STRUCTURALLY, with no hypothesis: a rival that returns the encoding plus
        a stray extra code point contradicts ``out = aceEncode host`` by LENGTH
        (``(aceEncode h ++ [c]).length ≠ (aceEncode h).length`` is a theorem
        whatever ``aceEncode h`` is). Nothing about the opaque callee is assumed.
      - by CONDITIONING ON THE CARRIER, for the constant-return rival, whose
        wrongness genuinely is a statement about the callee's value: it
        contradicts Q1 at any host whose encoding differs from the constant,
        stated as one hypothesis over the opaque term. The hypothesis is weak and
        self-satisfiable (checked: ``False`` is not derivable from it), so the
        refuting input genuinely exists.

REDUCTION NOTE (why the witnesses do not simply ``decide``). The frozen impl
chooses its result with ``:|``, which elaborates to ``pickSuchThat`` under
``loom.semantics.choice "demonic"``. A bare ``decide`` against it is STUCK
rather than false — "did not reduce to `isTrue` or `isFalse`" — for EVERY claim,
true or false, so a witness closing that way discriminates nothing (the gate
reports ``witness-undecided``; an earlier revision of this battery was rejected
for exactly that on the Q2 case). The repair is the first of the two documented
routes: state the refutation over a term whose reduction does NOT go through the
choice operator, by rewriting with ``simp only [punycodeDomain, bind,
NonDetT.bind, pickSuchThat, NonDetT.pickSuchThat, NonDetT.run, findableEqList,
pure]`` — the choice's own ``Findable`` instance is in the frozen ``pure``
region, so the chooser reduces to its found value.

WHERE THAT REDUCTION MUST BE APPLIED — the decisive detail, and an earlier
revision of this battery got it wrong. That revision reduced inside an
AUXILIARY ``have`` that pinned THE RIVAL'S returned value
(``have hrun : (punycodeDomain i).run = DivM.res <the rival's answer>``) and
only then rewrote the goal. Against the frozen solution such a ``have`` is
itself unprovable — gold does not return the rival's answer — so gold's build
died IN THE ``have``, before the witness's actual claim was ever elaborated.
Gold's exit code then carried no information about the claim. Measured with real
builds (audit): a FORGERY asserting ``(punycodeDomain i).run ≠ DivM.div`` — the
mere non-divergence of gold's own run, TRUE of gold and no spec violation at all
— elaborated against each rival (EXIT 0) and failed against gold (EXIT 1) with
the BYTE-IDENTICAL first error line as the shipped witness in all three cases,
so the gate would have recorded ``rejected`` for it.

So every witness below applies the reduction TO THE GOAL and binds no
rival-specific auxiliary. The claim is then the only thing gold's build can fail
on, and it does track the claim, checked in both directions per case: the
refutation elaborates on the rival (EXIT 0) and fails on gold (EXIT 1) with a
residue derived from the CLAIM (``hasc : (∀ c ∈ aceEncode ['あ'], c.val.toNat <
128) = True ⊢ False``; ``hlen : True ⊢ False``; ``Eq.symm h2 has type
aceEncode ['h','i'] = aceEncode ['h','i']``, i.e. ``simp`` PROVED gold's
equation), while the FLIPPED claim — drop the ``¬``/``≠``, asserting gold is
CORRECT at that input — now ELABORATES against gold (EXIT 0) instead of failing
identically. That flip pair is the discrimination.

AND IT HAS TO BE TAKEN AT THE POINT WHERE GOLD'S BUILD DIES, not merely at the
top-level claim — the second way a gold-side EXIT 1 goes hollow, and the Q2 case
below was repaired for exactly it. A script can reduce correctly, reach the spec,
and then die in an inner ``by`` block on a side goal the callee's opacity makes
undecidable (here ``'あ' ∈ aceEncode ['あ']``): the top-level flip still
elaborates against gold, so the flip pair LOOKS like a discrimination, while the
error that actually produced the exit code is the same for the side goal and for
its negation (measured: both directions gave the byte-identical ``simp` made no
progress``). Every reject case below is therefore checked by flipping the claim
AND by locating gold's first error: it must sit on the spec itself, with the spec
visibly discharged for gold, not on a subgoal that no build can settle either
way.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    mandatory frame-mutation rivals (write through a read-only fractional
    reference) because its inputs are held at a heap permission an impl can
    illegally overwrite. Lean and Velvet are referentially transparent: ``host``
    is an immutable value, this bundle declares NO ``mut`` binder, there is no
    heap and no aliasing — so there is no read-only input to mutate and no
    substitute probe to build. Not fabricated (per the porting map, this class is
    vacuous here).
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
  * UNGROUNDED-ORACLE ECHO — the nagini sibling's own note frames the fixed-ACE
    return as a PARTIAL-DOMAIN attack (correct on the one input whose encoding
    equals it, wrong elsewhere), NOT a true ungrounded echo, because the value
    pin is grounded in the input via ``aceEncode``. Same here: Q1 pins ``out`` to
    ``aceEncode host`` (the opaque callee's own value, G-AX-validated, not an
    answer-key an impl could echo), so the only value satisfying Q1 is the honest
    one and the positive control is the cheapest faithful reshape. The
    constant-echo rival is carried as the partial-domain attack it is.

WITNESS PLACEMENT. The three reject witnesses move the sole binder ``host``
across THREE distinct points, each applied to ``punycodeDomain`` at a literal so
the probed input is legible — a non-ASCII single-char host
(``['あ']``) for the
transparent Q2 attack, a three-char ASCII host (``['x','y','z']``) for the
unconditioned structural Q1 attack, and a two-char ASCII host (``['h','i']``)
for the conditioned Q1 attack — so ``host`` is genuinely varied in length and in
ASCII-ness, and no rival is refuted at an input another rival already covers.

  Note on the coverage reporter's count: it records ``pts=2``, not 3. That is a
  PARSER limit, not a coverage gap. ``pbt_coverage._spec_args`` returns "
  unreadable" for any witness whose statement carries a ``∀`` before the applied
  spec name, and the Q2 witness states the direct negation ``¬ (∀ c ∈ …, …)`` —
  the very shape that lets the reduction act on the GOAL rather than on a
  rival-pinning ``have`` (see the REDUCTION NOTE), which is what makes gold's
  exit code track the claim. So the reporter reads 2 of the 3 witnesses and the
  third's input point (``['あ']``) is still legible to a human on the line
  above. Trading the honest discriminator for a parseable ``∃`` shape would be
  the wrong repair; the count is advisory and this is the documented reason it
  under-reads here.

Every witness was checked with real builds: each ELABORATES against its rival
and FAILS, by a residue derived from the CLAIM rather than a stuck reduction or
an unprovable auxiliary, against the frozen solution.

AXIOM lane: DROPPED. The ``axioms`` region declares ``aceEncode`` /
``aceEncode_ascii``, but those are G-AX-validated (axiom_check.py runs the real
codec against ``aceEncode_ascii``), not this gate's concern; and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11532"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the two CODE lines of the frozen impl body (the two
# ---- comment lines above them are also inside the region, but anchoring on the
# ---- code keeps the surgery unambiguous). Lies wholly inside the single
# ---- -- impl-start / -- impl-end region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so each edit keeps same_spec by
# ---- construction and leaves the frozen `prove_correct punycodeDomain`
# ---- obligation intact.
_IMPL = (
    "    let out :| out = aceEncode host\n"
    "    return out\n"
)
assert _BASE.count(_IMPL) == 1, "punycodeDomain impl region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY punycodeDomain's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


# The simp set that pins a candidate impl's RETURNED VALUE without going through
# the choice operator's fixpoint. See the module docstring's REDUCTION NOTE: a
# bare `decide` against the frozen `:|` is stuck for every claim, so every
# witness below first reduces the run to a value and then reasons about it.
_REDUCE = ("simp only [punycodeDomain, bind, NonDetT.bind, pickSuchThat,\n"
           "             NonDetT.pickSuchThat, NonDetT.run, findableEqList, pure]")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Ports the nagini
    # `pos-control-acd-reshape` ARGUMENT ("a faithful, structurally-different
    # correct impl is not rejected") onto this carrier: instead of choosing the
    # encoded value and returning it in one step, bind it to an intermediate
    # local and return that. Observationally identical (an extra binding), so
    # both Q1 and Q2 still discharge and the FROZEN proof body closes verbatim
    # (verified out-of-band with a real build, EXIT 0). If it cannot verify, the
    # postcondition is over-fit to the exact return FORM (SPEC-TOO-STRONG).
    # =====================================================================
    {
        "id": "pos-let-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let encoded :| encoded = aceEncode host\n"
            "    let out := encoded\n"
            "    return out\n"),
        "rationale": "PASS SOURCE = Q1 ∧ Q2. Choosing the encoded value into an "
                     "intermediate local `encoded` and returning it (an extra "
                     "binding, same semantics) is observationally identical to "
                     "the direct choose-and-return, so `out = aceEncode host` "
                     "and `∀ c ∈ out, c.val.toNat < 128` both still discharge — "
                     "the frozen `prove_correct` body closes it unchanged. A "
                     "structurally different faithful reshape MUST verify; if it "
                     "cannot, the spec is over-fit to the return FORM "
                     "(SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # POSITIVE CONTROL #2 (soundness) — the DETERMINISTIC reshape. Ports the
    # nagini `pos-control-chn-direct` ARGUMENT ("a genuinely different CALL
    # SHAPE that is correct must verify"), which an earlier revision of this
    # battery wrongly recorded as having no counterpart on this carrier. It
    # does: the frozen impl reaches its answer through the non-deterministic
    # chooser `:|` (`pickSuchThat` under `loom.semantics.choice "demonic"`),
    # and this one applies the encoder face DIRECTLY and returns it, so the
    # choice operator is absent from the impl entirely. That is a strictly
    # bigger structural change than pos-let-reshape (which keeps the chooser
    # and merely adds a binding): it swaps the whole mechanism by which the
    # returned value is produced, from demonic choice to direct application.
    # Verified with a real build (audit, EXIT 0), frozen proof body unchanged.
    # =====================================================================
    {
        "id": "pos-direct-encode",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("    return aceEncode host\n"),
        "rationale": "PASS SOURCE = Q1 ∧ Q2. Returning `aceEncode host` "
                     "directly is the same VALUE the frozen impl chooses, so "
                     "`out = aceEncode host` holds by `rfl` and "
                     "`∀ c ∈ out, c.val.toNat < 128` holds by "
                     "`aceEncode_ascii` — the frozen `prove_correct` body "
                     "closes it unchanged. The reshape is not cosmetic: the "
                     "frozen impl produces its result through the "
                     "non-deterministic chooser `:|` and this one does not use "
                     "the chooser at all, so a spec (or a proof) over-fit to "
                     "the demonic-choice FORM rather than to the returned "
                     "VALUE would reject it. It also pins the direction that "
                     "matters for reading the reject cases: the rivals below "
                     "are refuted for their VALUES, not for abandoning the "
                     "choice operator — this positive abandons the choice "
                     "operator and is accepted. If it cannot verify => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the PRECOND-TOO-STRONG direction. This method carries NO
    # `require`, so "a normal input is admitted" is vacuous AS STATED; the live
    # analogue on a total carrier is the OBLIGATION being unsatisfiable or
    # degenerate at an F2P-shaped input, which this discharges at a concrete
    # non-ASCII host BEFORE the frozen body closes it in general. The claim is a
    # self-closing `have` inside the impl region (elided from the spec view, so
    # same_spec holds) followed by the frozen impl lines VERBATIM, so the frozen
    # `prove_correct` body still discharges the method's own obligation unchanged
    # and no proof-body retune is needed.
    # =====================================================================
    {
        "id": "admiss-postimage-satisfiable-at-f2p-host",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    have hadm : ∃ out : List Char,\n"
            "        out = aceEncode ['漢','字']\n"
            "        ∧ (∀ c ∈ out, c.val.toNat < 128)\n"
            "        ∧ out ≠ ['漢','字'] := by\n"
            "      refine ⟨aceEncode ['漢','字'], rfl,\n"
            "        fun c hc => aceEncode_ascii _ c hc, ?_⟩\n"
            "      intro hbad\n"
            "      have h1 : ∀ c ∈ (['漢','字'] : List Char), c.val.toNat < 128 := by\n"
            "        rw [← hbad]; exact fun c hc => aceEncode_ascii _ c hc\n"
            "      exact absurd (h1 '漢' (by simp)) (by decide)\n"
            + _IMPL),
        "rationale": "PASS SOURCE = Q1 ∧ Q2, discharged JOINTLY at a concrete "
                     "F2P-shaped input before the frozen body closes them in "
                     "general. The admitted domain is total (the pre-conditions "
                     "region is empty), so the residual PRECOND-TOO-STRONG risk "
                     "here is not a rejected input but a post-image that is "
                     "unsatisfiable or DEGENERATE at a normal input. The `have` "
                     "refutes that on three counts at host = ['漢','字'] (a "
                     "two-code-point non-ASCII host, the shape the failing "
                     "example drives): (i) some `out` satisfies the value pin Q1 "
                     "there, so the obligation is not unsatisfiable at a "
                     "non-ASCII host; (ii) that SAME `out` simultaneously "
                     "satisfies Q2, so the two clauses are jointly satisfiable "
                     "and not in conflict at exactly the input where Q2 bites; "
                     "(iii) that `out` is NOT the host verbatim, so the "
                     "post-image is non-degenerate — a spec satisfiable at this "
                     "input only by the unencoded host would admit it in name "
                     "only and would not distinguish the two behaviours at all. "
                     "Conjunct (iii) is LOAD-BEARING, negative-control checked: "
                     "replacing `≠` with `=` FAILS to elaborate (audit build, "
                     "EXIT 1, residue `⊢ aceEncode ['漢','字'] = ['漢','字']`), so "
                     "the `have` is not a tautology any value would satisfy. If "
                     "any of the three could not be established => "
                     "PRECOND-TOO-STRONG / unsatisfiable post-image.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input. They attack the TWO independent postcondition clauses:
    # Q2 (all-ASCII) once, and Q1 (the value pin) on both of its attackable
    # facets — structurally (no assumption) and by conditioning on the carrier.
    # =====================================================================

    # ---- (Q2) the output must be all-ASCII ----
    {
        "id": "weak-raw-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the host name VERBATIM with no encoding — the pre-patch
        # behaviour. Correct only on hosts that are already ASCII; for a
        # non-ASCII host the returned value carries a code point ≥ 128, so it
        # violates Q2 (the all-ASCII clause) directly.
        "module": _impl("    return host\n"),
        "refinement": "returning the host name with no ASCII-compatible encoding "
                      "is exactly the pre-patch behaviour: a non-ASCII host is "
                      "cached and later placed into a header rendered with a "
                      "single-byte charset, which cannot encode it and raises — "
                      "the precise failure the change removes. The failing "
                      "example mocks a non-ASCII host and asserts the header "
                      "carries the ASCII-compatible form; with the raw host "
                      "returned that assertion stays RED. It would NOT resolve.",
        "rationale": "REJECT from Q2 (∀ c ∈ out, c.val.toNat < 128): the rival "
                     "returns `host` unchanged, so at a non-ASCII host the "
                     "output contains a code point ≥ 128 and Q2 is false. "
                     "Refuted at host = ['あ'] (0x3042 = 12354 ≥ 128). The "
                     "witness pins the returned value first (the choice operator "
                     "does not reduce — see REDUCTION NOTE) and then decides Q2 "
                     "on it; the RIVAL side needs no fact about aceEncode at all "
                     "(the value is the literal host, whose sole code point is "
                     "0x3042, and `simp` evaluates it). The refutation is the "
                     "literal NEGATION of Q2 at this input and the reduction is "
                     "applied to THE GOAL, not to a rival-pinning `have` (see the "
                     "REDUCTION NOTE). WHY THE ASCII AXIOM IS SUPPLIED AT THIS "
                     "INPUT — the detail that makes gold's exit code mean "
                     "something, and an earlier revision of this case got it "
                     "wrong. That revision instantiated the reduced Q2 by hand "
                     "(`intro hall; have h1 := hall 'あ' (by simp)`), and against "
                     "gold the inner `by simp` was asked for "
                     "`'あ' ∈ aceEncode ['あ']` — MEMBERSHIP in an opaque axiom's "
                     "output, which no build can settle either way. Gold died "
                     "there with ``simp` made no progress`, and re-measured with "
                     "real builds (audit) the OPPOSITE claim at that same point, "
                     "`'あ' ∉ aceEncode ['あ']` under the same reduction and the "
                     "same `simp`, failed with the BYTE-IDENTICAL message (EXIT 1 "
                     "both ways) — so gold's exit code was decided by the "
                     "callee's opacity, not by the claim, and the pass attested a "
                     "refutation that was never performed. The repair supplies "
                     "the ASCII guarantee AT THE PROBED INPUT as an equation "
                     "`hasc : (∀ c ∈ aceEncode ['あ'], c.val.toNat < 128) = True` "
                     "(proved from `aceEncode_ascii` alone — it mentions no impl, "
                     "so it is a theorem of every module here and is NOT a "
                     "gold-pinning or rival-pinning `have`) and hands it to "
                     "`simp`. Now the two sides fail for opposite, claim-derived "
                     "reasons: on the RIVAL the reduct is `['あ']`, `hasc` does "
                     "not apply, and simp closes ¬Q2 by evaluating 12354 < 128 to "
                     "False (EXIT 0); on GOLD the reduct IS `aceEncode ['あ']`, "
                     "simp rewrites Q2 to `True` by `hasc` and the goal collapses, "
                     "leaving `unsolved goals hasc : (∀ c ∈ aceEncode ['あ'], "
                     "c.val.toNat < 128) = True ⊢ False` (EXIT 1) — the machine "
                     "stating that Q2 HOLDS of gold's returned value at this "
                     "input, which is exactly why the negation cannot be proved "
                     "there. Checked in both directions with real builds: the "
                     "FLIPPED claim (Q2 without the ¬, asserting the output IS "
                     "all-ASCII) carrying the BYTE-IDENTICAL script elaborates "
                     "against gold (EXIT 0, simp closes it through `hasc`) and "
                     "FAILS against the rival (EXIT 1, same "
                     "`hasc … = True ⊢ False` residue), so each side's exit code "
                     "tracks the claim rather than the script. Third build, "
                     "pinning the INPUT as well: the same script at the ASCII "
                     "host ['h'] (with `hasc` about `aceEncode ['h']`) FAILS "
                     "against the rival too (EXIT 1), so the rival-side pass is "
                     "the non-ASCII code point and not the supplied axiom. This "
                     "attacks the all-ASCII clause; the two rivals below attack "
                     "the value pin.",
        # Stated as the direct NEGATION of Q2 at this input, over the returned
        # value projected out of the run. The projection keeps the probed input
        # `['あ']` in applied position where a reader — and pbt_coverage's binder
        # scan — can see WHICH point this rival is refuted at, and stating ¬∀
        # (rather than ∃ over a pre-pinned literal) is what lets the reduction
        # act on the goal so the residue is gold's own Q2.
        #
        # `hasc` is Q2 AT THE PROBED INPUT, as an `= True` equation so `simp`
        # can use it as a rewrite (the bare conditional form `aceEncode_ascii
        # ['あ']` does NOT fire: measured, the flipped claim then also fails
        # against gold, `simp made no progress`, and the case is hollow again).
        # It is proved from the axiom and names no impl, so it is true in every
        # module here — it does not pin either side's returned value; it is what
        # lets gold's build REACH a verdict on the claim instead of stalling on
        # `'あ' ∈ aceEncode ['あ']`, a membership in an opaque term that fails
        # identically for the claim and its negation.
        "witness":
            "example : ¬ (∀ c ∈ (match (punycodeDomain ['あ']).run with\n"
            "                    | DivM.res o => o\n"
            "                    | _ => []), c.val.toNat < 128) := by\n"
            "  " + _REDUCE + "\n"
            "  have hasc : (∀ c ∈ aceEncode ['あ'], c.val.toNat < 128) = True :=\n"
            "    eq_true (aceEncode_ascii ['あ'])\n"
            "  simp [hasc]\n",
    },

    # ---- (Q1) the output must be EXACTLY the encoding — structural attack ----
    {
        "id": "weak-encode-plus-pad",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR MISS: do the encoding, then append one stray ASCII code point.
        # Q2 still holds (the stray point is ASCII and the encoding is ASCII by
        # aceEncode_ascii), and the result agrees with the correct answer on its
        # whole prefix — but it is not the encoding, so Q1 fails. Unlike the
        # constant rival this is refutable with NO assumption about the opaque
        # callee: the two lists differ in LENGTH whatever the encoding is.
        "module": _impl("    return aceEncode host ++ ['x']\n"),
        "refinement": "appending a stray character to the ASCII-compatible "
                      "encoding yields an all-ASCII but WRONG host name, so the "
                      "cached value is one character off from the real host's "
                      "encoding everywhere. The failing example asserts the "
                      "header ends with the encoded host immediately followed by "
                      "the header's closing delimiter; a trailing extra "
                      "character breaks that assertion, so it stays RED. Every "
                      "other place that reads the cached host name would also "
                      "see a corrupted name. It would NOT resolve.",
        "rationale": "REJECT from Q1 (out = aceEncode host): the rival returns "
                     "the encoding with one extra code point, so Q1 is false at "
                     "EVERY input while Q2 (all-ASCII) still holds — the "
                     "sharpest demonstration that Q2 alone cannot carry the "
                     "spec. Refuted at host = ['x','y','z'] (a third, longer "
                     "input point). The witness assumes NOTHING about the opaque "
                     "aceEncode: it pins the returned value, then derives the "
                     "contradiction from LENGTH "
                     "((aceEncode h ++ ['x']).length ≠ (aceEncode h).length is a "
                     "theorem whatever aceEncode h is), so it binds no "
                     "hypothesis and cannot be vacuous. The reduction is applied "
                     "to THE GOAL, not to a rival-pinning `have` (see the "
                     "REDUCTION NOTE), so gold's failure is derived from the "
                     "claim: on gold the reduction closes the equation and the "
                     "length step degenerates, leaving "
                     "`hl : aceEncode ['x','y','z'] = aceEncode ['x','y','z']`, "
                     "`hlen : True` ⊢ `False` — `hlen : True` is the machine "
                     "saying the lengths AGREE for gold, which is the point where "
                     "gold satisfies the pin. Checked in both directions: the "
                     "FLIPPED claim (`=` instead of `≠`, asserting gold is "
                     "correct here) ELABORATES against gold (EXIT 0) rather than "
                     "failing with the same error, so the exit code carries "
                     "information about the claim. This is the NEAR-MISS of the "
                     "battery (it agrees with the correct answer on the whole "
                     "prefix), so it gets its own input rather than sharing the "
                     "constant rival's.",
        "witness":
            "example : (punycodeDomain ['x','y','z']).run\n"
            "    ≠ DivM.res (aceEncode ['x','y','z']) := by\n"
            "  " + _REDUCE + "\n"
            "  intro heq\n"
            "  injection heq with hl\n"
            "  have hlen := congrArg List.length hl\n"
            "  simp at hlen\n",
    },

    # ---- (Q1) the output must be aceEncode host, not a fixed constant ----
    {
        "id": "weak-const-echo",
        "kind": "uniqueness",
        "expect": "reject",
        # Return a FIXED all-ASCII constant regardless of the input. Q2 holds
        # trivially (the constant is ASCII), and the constant is correct on the
        # one input whose encoding equals it — a partial-domain attack — but Q1
        # (`out = aceEncode host`) cannot hold for a host whose encoding differs
        # from the constant.
        "module": _impl(
            "    return ['x', 'n', '-', '-', 'p', '8', 's', '9', '3', '7', 'b']\n"),
        "refinement": "hard-coding one ASCII constant as the encoded host passes "
                      "on the single input whose encoding equals it yet is wrong "
                      "for every other host, so the cached host name used across "
                      "the mail send/idn tests would be the wrong constant string "
                      "rather than the actual host's encoding — those tests read "
                      "the real cached host and would break. It agrees with gold "
                      "only on the witness input, diverging everywhere else — "
                      "verify-not-resolve. It would NOT resolve.",
        "rationale": "REJECT from Q1 (out = aceEncode host): the rival returns a "
                     "fixed constant, so Q1 fails at any host whose encoding "
                     "differs from it. Q2 (all-ASCII) holds and is insufficient. "
                     "Unlike the pad rival above, this rival's wrongness IS a "
                     "statement about the opaque callee's VALUE, so the "
                     "refutation is stated by CONDITIONING on the carrier — the "
                     "hypothesis `aceEncode ['h','i'] ≠ <constant>` describes the "
                     "sub-domain where the rival is wrong (a stronger statement "
                     "than any single literal input could make). ONE hypothesis "
                     "about ONE opaque term: it is weak and self-satisfiable "
                     "(its `False`-derivation probe fails), so the refuting "
                     "input genuinely exists. Refuted at host = ['h','i'], a "
                     "distinct input point from both rivals above. The reduction "
                     "is applied to THE GOAL, not to a rival-pinning `have` (see "
                     "the REDUCTION NOTE), so gold's failure is derived from the "
                     "claim: on gold the reduction PROVES the equation, so `h2` "
                     "comes out as `aceEncode ['h','i'] = aceEncode ['h','i']` "
                     "and the final `exact h h2.symm` is an application type "
                     "mismatch against `h`'s hypothesis — the machine reporting "
                     "that gold's returned value IS the encoding. Checked in both "
                     "directions: the FLIPPED claim (`=` instead of `≠`) "
                     "ELABORATES against gold (EXIT 0) rather than failing with "
                     "the same error, so the exit code tracks the claim.",
        "witness":
            "example (h : aceEncode ['h','i'] ≠\n"
            "    ['x','n','-','-','p','8','s','9','3','7','b']) :\n"
            "    (punycodeDomain ['h','i']).run\n"
            "      ≠ DivM.res (aceEncode ['h','i']) := by\n"
            "  " + _REDUCE + "\n"
            "  intro heq\n"
            "  injection heq with h2\n"
            "  exact h h2.symm\n",
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation, 2 uniqueness rivals) plus a
# 2-case AXIOM lane. This bundle models a NARROWER surface: nagini contracts TWO
# functions (the encoding, and the cached-host routine that composes it), whereas
# velvet models the single purely-functional core `punycodeDomain` (host name →
# its ASCII-compatible encoding). The composition and the delegation collapse
# into one method, and the two functions' identical contracts become the single
# method's two clauses (Q1 value pin, Q2 all-ASCII). Every sibling case is
# accounted for below.
#
#   sibling case (nagini)         -> here
#   -----------------------------------------------------------------------
#   pos-control-acd-reshape       -> pos-let-reshape              PORTED
#   pos-control-chn-direct        -> pos-direct-encode            PORTED
#   admiss-witness-selfcall       -> admiss-postimage-satisfiable-at-f2p-host
#                                                                  RE-AIMED
#   frame-mutate-platform-name    -> (none)                       VACUOUS (no heap)
#   frame-mutate-domain           -> (none)                       VACUOUS (no heap)
#   weak-witness-constant         -> weak-const-echo              PORTED (Q1 cond.)
#   weak-raw-passthrough          -> weak-raw-passthrough         PORTED (Q2)
#   (no sibling)                  -> weak-encode-plus-pad         ADDED (Q1 struct.)
#   (no sibling; see docstring)   -> (none)                  diverge: SPEC-CLOSED
#   AXIOM_TESTS (x2)              -> (none)                       DROPPED (G-AX)
#
# PORTED (2 positives -> 2): the two nagini positives are (a) a local-variable
#   reshape of the encoder and (b) calling the encoder face directly instead of
#   composing via the helper. (a) ports as pos-let-reshape. (b) ports as
#   pos-direct-encode, and an earlier revision of this battery was WRONG to
#   record it as folded for lack of a second call shape: this carrier has no
#   helper/composer pair, but it does have two distinct MECHANISMS for producing
#   the returned value — the frozen impl's non-deterministic chooser `:|`
#   (`pickSuchThat` under demonic choice) versus direct application of the
#   encoder face. pos-direct-encode takes the second, so the choice operator is
#   absent from its impl entirely, which is a strictly larger structural change
#   than pos-let-reshape's extra binding and is the closest analogue of nagini's
#   "different call shape" that this surface admits. Both verify with the frozen
#   proof body unchanged (audit builds, EXIT 0). Keeping both matters for reading
#   the reject lane: it shows the three rivals are refuted for their VALUES and
#   not merely for departing from the frozen impl's choice-operator form.
# RE-AIMED (admissibility): the sibling self-calls on a fresh input shaped like
#   the failing example's host to prove the precondition ADMITS a normal input.
#   This method declares NO `require` clause (the pre-conditions region is empty),
#   so the sibling's case is vacuous AS STATED — but the lane is NOT vacuous, and
#   an earlier revision of this battery wrongly dropped it. The analogue on a
#   total carrier is the obligation being unsatisfiable or DEGENERATE at an
#   F2P-shaped input, and "the frozen prove_correct verifies, so the postcondition
#   is satisfiable by construction" does not discharge it: that argument is about
#   satisfiability SOMEWHERE (in fact at a universally quantified `host`), whereas
#   the risk is joint satisfiability and non-degeneracy AT THE CONCRETE INPUT the
#   change is about — a non-ASCII host, where Q2 is the clause that bites.
#   admiss-postimage-satisfiable-at-f2p-host discharges exactly that by
#   evaluation at host = ['漢','字'], as a self-closing `have` before the frozen
#   obligation is closed verbatim, with a measured negative control on its
#   load-bearing conjunct. Verified with a real build (EXIT 0).
# VACUOUS (frame-mutation x2): the sibling carries these MANDATORY because its
#   read-only inputs are held at a fractional permission an impl can illegally
#   overwrite. This backend is referentially transparent and declares no `mut`
#   binder — the single input `host` is an immutable value with no heap footprint
#   — so there is no read-only field to overwrite and no substitute probe. Not
#   fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# PORTED (2 rivals) + ADDED (1): weak-raw-passthrough ports directly (return the
#   host verbatim → the pre-patch behaviour), refuted on the all-ASCII clause
#   (Q2) at a non-ASCII host. weak-witness-constant ports as weak-const-echo
#   (return the fixed ACE constant), refuted on the value pin (Q1) by
#   CONDITIONING on the opaque aceEncode. weak-encode-plus-pad has no sibling and
#   is ADDED because the ported pair left Q1 attacked only through a hypothesis
#   about the opaque callee: the pad rival refutes Q1 with NO assumption at all
#   (a length argument), and it is the battery's near-miss — all-ASCII, and
#   agreeing with the correct answer on its whole prefix. Each carries a
#   machine-checked witness that ELABORATES against the rival and FAILS against
#   the frozen solution by a real residue rather than a stuck reduction.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   `aceEncode_ascii` against the real codec) and this gate ignores AXIOM_TESTS
#   regardless.
#
# COVERAGE. The sole obligation (`prove_correct punycodeDomain`) is defended
# TWICE (pos-let-reshape keeps the chooser and adds a binding; pos-direct-encode
# drops the chooser altogether), probed for PRECOND-TOO-STRONG in the admissibility lane
# (admiss-postimage-satisfiable-at-f2p-host, at a non-ASCII host), and attacked
# by three reject rivals — so all THREE directions this gate exists to test are
# exercised, not two. BOTH independent
# postcondition clauses are attacked — Q2 (all-ASCII) by weak-raw-passthrough,
# Q1 (value pin) by weak-encode-plus-pad (unconditioned/structural) and by
# weak-const-echo (conditioned on the carrier). The sole input binder `host` is
# varied across the reject witnesses over three distinct points — ['あ'],
# ['x','y','z'], ['h','i'] — differing in length AND in ASCII-ness, and no rival
# is refuted at an input another rival already covers. (The coverage reporter
# counts pts=2: its arg parser skips the Q2 witness because that witness states
# `¬ (∀ ...)`, the shape required for the goal-applied reduction. Parser limit,
# not a coverage gap — see WITNESS PLACEMENT in the docstring.) No
# frame/permission rival is fabricated (that class is vacuous on a
# referentially-transparent carrier); the divergence class is recorded as a spec
# hole above rather than papered over with a substitute.
AXIOM_TESTS = []
