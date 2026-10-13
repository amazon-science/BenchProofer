"""properties.py — G-PBT falsification battery for django__django-11749 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct selectForwarded`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

================================  DEFENDED SURFACE  ==========================

ONE contracted method over a list of declared-option observations:

  selectForwarded (options : List OptionView) return (out : List Bool)
    ensures out = forwardedAll options                          -- the WHOLE pin

An ``OptionView`` records the three observations that decide whether one
declared option's supplied value must be forwarded for re-parsing:
``supplied`` (the caller provided a value for it), ``individuallyRequired``
(it is required on its own), and ``inRequiredGroup`` (it belongs to a mutually
exclusive group that is itself required). The per-option verdict is the pure,
fully-unfolded

  forwarded a = a.supplied && (a.individuallyRequired || a.inRequiredGroup)

and the whole verdict list is the front-recursive fold ``forwardedAll``
(``forwardedAll (a :: rest) = forwarded a :: forwardedAll rest``). Both are
TRANSPARENT ``def``s over the method's own input — there is NO opaque answer key
in the load-bearing clause, so pinning ``out = forwardedAll options`` is
grounded, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. The single ``ensures`` (``out = forwardedAll
options``) is the whole impl-constraining surface: it fixes, at every position,
which options are forwarded and in what order, as a function of the three
observations of each option. Every uniqueness rival attacks it. The
DISCRIMINATING content of the fix (and of the sole FAIL_TO_PASS scenario) lives
on the sub-domain ``supplied ∧ inRequiredGroup ∧ ¬individuallyRequired``: an
option that is provided and belongs to a required mutually exclusive group but
is not individually required MUST be forwarded. The pre-image verdict
``a.supplied && a.individuallyRequired`` drops exactly that case (the headline
``weak-prepatch-predicate`` rival).

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's MANDATORY
    ``uniq-frame-mutate`` rival writes through a read-only (``Acc(.,1/2)``)
    reference to the input list and is rejected for INSUFFICIENT PERMISSION.
    Lean and Velvet are referentially transparent: the input is an immutable
    value, this bundle declares NO ``mut`` binder on any input, and there is no
    heap, aliasing, or permission system to subvert. There is no read-only input
    to overwrite, so the class is vacuous. No substitute probe is fabricated
    (see footer). The sibling's "held read-only" obligation is here structurally
    guaranteed by the ABSENCE of ``mut``, which the frozen spec already encodes.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. The post-image ``forwardedAll
    options`` is a transparent fold over the method's own argument; there is no
    answer key to echo. The honest cheapest CORRECT impl (``return forwardedAll
    options``) is carried as a POSITIVE control instead — it doubles as proof the
    spec is not echo-vulnerable, since any WRONG per-option verdict fails
    ``out = forwardedAll options``.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against the single
    ``ensures``. A rival can compute the wrong per-option verdict on a
    sub-domain (drop the required-group disjunct — the pre-image; over-forward
    every provided option; forward on obligation without requiring the value was
    provided; forward everything; forward nothing) or forward the right set in a
    truncated list shape (skip the first declared option).
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS MECHANICS on this carrier — READ THE LIMITATION BEFORE TRUSTING A
REJECTION. The spec is a ``method`` CONTRACT, not a bare predicate, so a witness
reaches it through Velvet's own tester machinery: ``selectForwardedTester <input>
= false`` says the extracted program's result violates the method's
postcondition at that concrete input, checked in a file whose ``prove_correct``
block has been stripped (no tactic script can mask the verdict). Each reject
rival is written LOOP-FREE (a ``List.map`` per-option verdict, a ``match`` on the
head, a ``reverse``), so ITS extracted program kernel-reduces and ``decide``
settles the refutation. The carrier is a concrete ``OptionView`` record of Bools,
so every input is a ground decidable literal. No witness binds a hypothesis, so
no consistency probe is needed. No ``sorry`` / ``admit`` / ``native_decide`` /
``axiom``.

  KNOWN WEAKNESS OF THE GOLD-SIDE HALF (measured, documented here so no reader
  over-reads a rejection). The gate's discrimination check requires the witness
  to FAIL against the frozen solution, and reads that failure as "gold satisfies
  the spec here". On THIS carrier it is not that. The frozen impl is a backward
  ``while`` fold whose extracted program is well-founded recursion the kernel
  does not reduce, so on gold ``decide`` reports *"did not reduce to isTrue or
  isFalse ... reduction got stuck"* — an UNDECIDED reduction, not a refuted
  claim. Measured directly: ``#eval selectForwardedTester <input>`` returns
  ``true`` on the frozen solution at all six witness points (and at the two
  remaining rows of the observation matrix), so gold really does satisfy the
  postcondition everywhere these witnesses look; but the compiler's ``#eval``
  establishes that, not the kernel, and ``decide`` / ``rfl`` / ``simp`` all get
  stuck on gold. So the gold-side exit code is driven by the frozen impl's
  LOOP SHAPE, and a merely-reshaped loop-free CORRECT rival would fail the same
  build for the same stuck reason.

  WHAT MAKES THE REJECTIONS ATTRIBUTABLE ANYWAY. Two things, both machine-checked
  in-file rather than argued:

  1. Every witness now states the post-image value at its own input FIRST
     (``example : forwardedAll <input> = <value> := by decide``). That equation
     is about the transparent spec fold ONLY — it is independent of any impl,
     it elaborates in both builds, and it is what the rival's tester line
     contradicts. So the pair (spec value here IS v; this impl's tester says the
     postcondition is violated here) is a complete counterexample recorded in
     the witness itself, and no longer depends on reading gold's exit code.
  2. The rival-side half is genuinely discriminating on its own: the tester line
     is proven ``= false``, i.e. ``decide`` reduced the rival's extracted program
     and found the postcondition FALSE. A correct loop-free reshape does not pass
     that half — measured: the ``weak-prepatch-predicate`` witness built against
     the CORRECT loop-free impl ``return (forwardedAll options)`` fails with
     *"decide proved that the proposition ... = false is false"*, the opposite
     verdict. That is the check the stuck gold build cannot supply, and it is why
     each rival below is additionally required to be loop-free.

(All builds re-run out of band with scripts/lean_verify.sh: for each reject case
the witness exits 0 against its rival and 1 against the frozen solution; each
rival's wrongness at its own witness point is independently confirmed by
``<rival's pure output> ≠ forwardedAll <input> := by decide``, which elaborates
against the frozen solution.)

AXIOM lane: EMPTY. ``meta.json axioms == []`` and ``deep_model_references == []``
— the change is pure selection logic modeled deeply (the spelled-out
``forwarded`` + ``forwardedAll`` fold), no ``@ContractOnly`` oracle. Nothing for
G-AX; the gate ignores ``AXIOM_TESTS`` regardless. ``AXIOM_TESTS = []``.
"""
from pathlib import Path

INSTANCE = "django__django-11749"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the method's impl region (between
# -- impl-start and -- impl-end) or inside the prove_correct tactic body, and
# each is unique in Solution.lean; both facts are asserted at load by _swap.
# Editing only these keeps markers.same_spec True and the prove_correct
# statement byte-identical (the spec view elides both regions).
# ---------------------------------------------------------------------------
_IMPL = (
    "    let mut result : List Bool := []\n"
    "    let mut i := options.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ options.length\n"
    "      invariant result = forwardedAll (options.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let a := options[i - 1]!\n"
    "      result := forwarded a :: result\n"
    "      i := i - 1\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start marker drifted"

# The frozen proof, verbatim. A loop-free correct reshape retunes THIS block
# (elided from the spec view) to a bare loom_solve, since the residual goal no
# longer needs the backward-fold step lemma. Loop-keeping variants and rivals
# leave it as-is — the rejection is carried by the witness, not the tactic.
_PROOF = (
    "prove_correct selectForwarded by\n"
    "  loom_solve\n"
    "  rw [forwardedAll_drop_step options i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

_PROOF_BARE = "prove_correct selectForwarded by\n  loom_solve"

# A loop-free reshape whose residual goal is NOT closed by `loom_solve` alone:
# `List.map f options = forwardedAll options` needs the list induction that
# aligns the two recursions. Retuning the (spec-view-elided) proof to this is
# what a faithful correct impl of a different shape legitimately does — the
# `pos-control-direct` variant, by contrast, discharges its goal by
# `rfl`-grade unfolding, so it exercises much less.
_PROOF_INDUCT = (
    "prove_correct selectForwarded by\n"
    "  loom_solve\n"
    "  induction options with\n"
    "  | nil => rfl\n"
    "  | cons a rest ih => simp [forwardedAll_cons, ih]"
)

# Same, plus unfolding `forwarded` — needed when the impl INLINES the per-option
# disjunction instead of calling the spec's own predicate.
_PROOF_INDUCT_UNFOLD = (
    "prove_correct selectForwarded by\n"
    "  loom_solve\n"
    "  induction options with\n"
    "  | nil => rfl\n"
    "  | cons a rest ih => simp [forwardedAll_cons, forwarded, ih]"
)


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for a loop-free correct reshape
    whose residual goal no longer needs the backward-fold step lemma)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


def _map(mapexpr):
    """A loop-free rival: compute the per-option verdict with a `List.map`.
    Being loop-free its extracted `…Exec` reduces under `decide`, so its witness
    discriminates; gold's `while`-loop `…Exec` stays stuck."""
    return _impl(f"    return (options.map (fun a => {mapexpr}))")


# ---- OptionView literal builder + witness. The postcondition IS decidable and
# ---- the carrier is a ground record of Bools, so the tester + `decide` path
# ---- settles each rival at a concrete input. Checked in a file whose
# ---- prove_correct block is stripped, so no tactic script can mask the verdict.
def _ov(s, ir, ig):
    return ("{ supplied := %s, individuallyRequired := %s, inRequiredGroup := %s }"
            % (s, ir, ig))


def _witness(inp, gold):
    """A refutation witness at one concrete input, in two machine-checked parts.

    `gold` is the post-image value the frozen spec fold demands at `inp`. The
    first `example` pins it by `decide` on the TRANSPARENT fold alone — no impl
    is involved, so it elaborates in both the rival build and the gold build and
    cannot be an artifact of either. The second `example` says this variant's
    extracted program violates the postcondition at that same input.

    Stating the post-image explicitly is what keeps the rejection attributable.
    The gate's gold-side half is weak on this carrier (the frozen `while` fold's
    extracted program does not kernel-reduce, so `decide` on gold reports STUCK
    rather than refuted — see the module docstring), so the counterexample has to
    be legible from the witness itself: "the spec demands `gold` here, and this
    impl is proven to violate the postcondition here."
    """
    return (
        "extract_program_for selectForwarded\n"
        "prove_precondition_decidable_for selectForwarded\n"
        "prove_postcondition_decidable_for selectForwarded\n"
        "derive_tester_for selectForwarded\n\n"
        "-- the post-image the FROZEN spec fold demands at this input. About\n"
        "-- `forwardedAll` only, so it holds in both builds and is what the\n"
        "-- tester line below contradicts.\n"
        f"example : forwardedAll ({inp}) = {gold} := by decide\n\n"
        "-- this variant's extracted program violates the postcondition there.\n"
        f"example : selectForwardedTester ({inp}) = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the whole verdict list DIRECTLY via the transparent
        # fold, no per-option loop. The ensures is literally `out = forwardedAll
        # options`, so this is the cheapest HONEST correct impl — and, since
        # `forwardedAll options` is GROUNDED in the argument (not an opaque answer
        # key), it doubles as proof the spec is not echo-vulnerable (any WRONG
        # per-option verdict fails `out = forwardedAll options`). The loop is
        # gone, so the frozen proof's backward-fold step is unneeded and the
        # residual goal closes under `loom_solve` alone.
        "module": _impl_reproved(
            "    return (forwardedAll options)", _PROOF_BARE),
        "rationale": (
            "the post-image `forwardedAll options` is GROUNDED in the input (a "
            "total front-recursive fold, no opaque answer key), so `return "
            "forwardedAll options` is the honest cheapest CORRECT impl; the "
            "ensures is literally `out = forwardedAll options`, so it MUST verify, "
            "else SPEC-TOO-STRONG. Re-expresses the nagini pos-control-helper (its "
            "@Pure `forward(a)` consulted inside the fold) as the loop-free "
            "grounded-oracle control, showing the spec is not echo-vulnerable."
        ),
    },
    {
        "id": "pos-control-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold but bind the per-option verdict
        # to a typed local `v` before prepending it. Same value flow
        # (`v = forwarded a`), different control shape; the frozen proof still
        # closes unchanged (the loop invariant and step lemma are untouched).
        "module": _impl(
            "    let mut result : List Bool := []\n"
            "    let mut i := options.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ options.length\n"
            "      invariant result = forwardedAll (options.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let a := options[i - 1]!\n"
            "      let v := forwarded a\n"
            "      result := v :: result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": (
            "a correct impl with a DIFFERENT executable shape (bind the per-option "
            "verdict to a typed local before prepending it) must verify; the value "
            "flow is unchanged (`v = forwarded a`) so the ensures still discharges "
            "and the frozen loop proof closes as-is. Ports the nagini "
            "pos-control-local; if it fails => SPEC-TOO-STRONG (over-fit to the "
            "inline-prepend code form)."
        ),
    },
    {
        "id": "pos-control-inlined-map",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: SPELL OUT the per-option disjunction inline and apply it with a
        # `List.map`, rather than calling the spec's own `forwarded` predicate.
        # This is the positive control with real content: unlike
        # `pos-control-direct` (whose body IS the post-image term, so its residual
        # goal closes by unfolding) this impl's goal is
        # `List.map (fun a => a.supplied && (...)) options = forwardedAll options`
        # — two differently-shaped recursions that must be aligned by induction,
        # and the per-option verdict must be shown equal to `forwarded` rather
        # than being it syntactically. If a spec can only be discharged by an impl
        # that literally names its own post-image, it is over-fit; this case is
        # what rules that out.
        "module": _impl_reproved(
            "    return (options.map (fun a => a.supplied && "
            "(a.individuallyRequired || a.inRequiredGroup)))",
            _PROOF_INDUCT_UNFOLD),
        "rationale": (
            "a faithful CORRECT impl that neither calls `forwardedAll` nor calls "
            "`forwarded` — it inlines the per-option disjunction and maps it — must "
            "verify, else SPEC-TOO-STRONG (the spec would be dischargeable only by "
            "an impl that echoes its own post-image term). Strictly stronger as a "
            "soundness probe than pos-control-direct: the residual goal is an "
            "alignment of two different recursions (`List.map` vs the "
            "front-recursive fold) plus an unfold of `forwarded`, closed by list "
            "induction rather than by definitional unfolding. Measured: verifies "
            "(exit 0); the SAME impl with `loom_solve` alone leaves the goal "
            "`List.map ... = forwardedAll options` unsolved, so the case is live."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-f2p-shaped-input. That case
    # established the read-only fractional-permission precondition on an
    # F2P-shaped input. This method carries NO `require` clause (the
    # pre-conditions region is empty), so nothing could exclude a normal input
    # and the classic "a normal input is admitted" probe is vacuous. Re-aimed at
    # the residual admissibility risk on a total domain: that the post-image is
    # not DEGENERATE at the interesting point. The variant discharges an
    # in-region `assert` (inside the impl region, elided from the spec view)
    # pinning the three F2P-discriminating verdicts at concrete OptionViews; the
    # impl is kept verbatim so the method's own ensures still discharges. The
    # assert is live (a false claim about the same points leaves an unsolved goal
    # — verified out of band). MUST verify, else PRECOND-TOO-STRONG / degenerate.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_START,
            _IMPL_START
            + "    assert (with_name_prefix `assert\n"
            "      (forwarded { supplied := true, individuallyRequired := false, "
            "inRequiredGroup := true } = true ∧\n"
            "       forwarded { supplied := true, individuallyRequired := true, "
            "inRequiredGroup := false } = true ∧\n"
            "       forwarded { supplied := false, individuallyRequired := true, "
            "inRequiredGroup := true } = false))\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "points: a provided option in a required mutually exclusive group but "
            "not individually required IS forwarded (the fix's discriminating "
            "sub-domain), a provided individually-required option IS forwarded, "
            "and a mandatory option whose value was NOT provided is NOT forwarded. "
            "The in-region assert must discharge (else the obligation is "
            "degenerate); the impl is kept verbatim so selectForwarded's own "
            "ensures still verifies. Re-aimed from the nagini "
            "admiss-f2p-shaped-input, whose read-only-precondition half has no "
            "counterpart on this referentially-transparent carrier."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each loop-free (so its tester kernel-reduces) with a
    # machine-checked refutation witness at a concrete input and the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P. All
    # attack the single ensures; the three per-option binders (supplied,
    # individuallyRequired, inRequiredGroup) and the list shape are varied across
    # the witnesses.
    # =====================================================================
    {
        "id": "weak-prepatch-predicate",
        "kind": "uniqueness",
        "expect": "reject",
        # THE bug: the pre-image verdict `supplied ∧ individuallyRequired`,
        # dropping the required-group disjunct. Correct wherever the option is
        # individually required; WRONG on the sub-domain
        # `supplied ∧ inRequiredGroup ∧ ¬individuallyRequired`.
        "module": _map("a.supplied && a.individuallyRequired"),
        "refinement": (
            "this is the pre-image verdict: a supplied option is forwarded only "
            "when it is individually required, so an option that is provided and "
            "belongs to a required mutually exclusive group but is not itself "
            "required is NOT forwarded. Its faithful real counterpart is the "
            "un-patched selection, which the sole FAIL_TO_PASS scenario (a "
            "provided member of a required mutually exclusive group whose members "
            "are each individually optional) observes: the value is never threaded "
            "through and the required-group check fails. It would NOT resolve — "
            "this is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from the ensures `out = forwardedAll options`: `forwarded` "
            "forwards a supplied required-group member even when it is not "
            "individually required, so a rival dropping the required-group "
            "disjunct diverges from the post-image on that sub-domain. Refuted at "
            "input `[supplied ∧ inRequiredGroup ∧ ¬individuallyRequired]`. If it "
            "verified => SPEC-TOO-WEAK (admits the bug)."
        ),
        "witness": _witness(f"[{_ov('true', 'false', 'true')}]", "[true]"),
    },
    {
        "id": "weak-over-forward",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward EVERY provided option (verdict = supplied alone, dropping the
        # obligation disjunct). Over-forwards on the sub-domain
        # `supplied ∧ ¬individuallyRequired ∧ ¬inRequiredGroup` — a provided but
        # non-mandatory option argparse does not require.
        "module": _map("a.supplied"),
        "refinement": (
            "forwarding every provided option over-threads optional caller-"
            "supplied values that argument re-parsing does not require, changing "
            "what the parser sees and the computed defaults. A faithful real "
            "counterpart regresses the pre-existing command-call scenarios that "
            "pass optional keyword arguments (a provided non-mandatory option is "
            "pushed into re-parsing), so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the ensures: `forwarded` excludes a provided option that "
            "is neither individually required nor in a required group, but this "
            "rival forwards it, so the verdict list gains a spurious `true`. "
            "Refuted at input `[supplied ∧ ¬individuallyRequired ∧ "
            "¬inRequiredGroup]` — moving inRequiredGroup off the value the "
            "prepatch rival probes it at. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(f"[{_ov('true', 'false', 'false')}]", "[false]"),
    },
    {
        "id": "weak-drop-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward on obligation WITHOUT requiring the value was provided (verdict
        # = individuallyRequired ∨ inRequiredGroup, dropping `supplied`). Diverges
        # on `(individuallyRequired ∨ inRequiredGroup) ∧ ¬supplied`.
        "module": _map("a.individuallyRequired || a.inRequiredGroup"),
        "refinement": (
            "forwarding a mandatory option whose value the caller did NOT provide "
            "would look up an absent value at re-parse time — the selection is "
            "gated on the value being provided precisely to avoid this. A faithful "
            "real counterpart raises on legitimate calls that omit a mandatory "
            "option (the parser reports it as required and errors), so it would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the ensures: `forwarded` excludes a mandatory option "
            "whose value was not provided, but this rival forwards it. Refuted at "
            "input `[¬supplied ∧ individuallyRequired]` — moving the supplied "
            "binder to false, a value no other rival's witness holds it at. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(f"[{_ov('false', 'true', 'false')}]", "[false]"),
    },
    {
        "id": "weak-forward-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward EVERYTHING unconditionally (constant `true` verdict) — the
        # analogue of the nagini identity rival (return the whole declared list
        # unfiltered). Diverges on any option that is not forwardable.
        "module": _map("true"),
        "refinement": (
            "forwarding every declared option unconditionally threads values for "
            "options the caller never provided and for non-mandatory options, "
            "corrupting argument re-parsing broadly. A faithful real counterpart "
            "(drop the selection guard, forward every option) breaks the "
            "command-call scenarios on any input carrying a non-forwardable "
            "option, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the ensures: the constant-`true` verdict equals "
            "`forwardedAll options` only when every option is forwardable, which "
            "is not generally true. Refuted at input `[¬supplied ∧ "
            "¬individuallyRequired ∧ ¬inRequiredGroup]` — a wholly non-mandatory "
            "unprovided option, where the spec demands `false`. Ports the nagini "
            "uniq-identity. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(f"[{_ov('false', 'false', 'false')}]", "[false]"),
    },
    {
        "id": "weak-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The trivial cheapest wrong impl — forward NOTHING (return the empty
        # verdict list). Diverges on any input with a forwardable option.
        "module": _impl("    return []"),
        "refinement": (
            "forwarding nothing corresponds to deleting the selection entirely: "
            "no mandatory or required-group option is ever threaded through, so "
            "argument re-parsing reports missing required arguments. Both the F2P "
            "and the pre-existing required-argument scenarios fail, so a faithful "
            "real counterpart would NOT resolve. Supporting near-miss for the "
            "headline selection weakness."
        ),
        "rationale": (
            "REJECT from the ensures: for any input with a forwardable option "
            "`forwardedAll options` is non-empty, so the empty verdict list cannot "
            "satisfy the equality. Refuted at input `[supplied ∧ "
            "individuallyRequired ∧ inRequiredGroup]` (a fully forwardable option), "
            "whose gold verdict is `[true]` but the length differs. Ports the "
            "nagini uniq-empty."
        ),
        "witness": _witness(f"[{_ov('true', 'true', 'true')}]", "[true]"),
    },
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip the FIRST declared option (compute the verdict over the tail only).
        # Correct per-option verdict, wrong list SHAPE: whenever the first
        # declared option is forwardable its verdict is dropped and the whole list
        # is shifted.
        "module": _impl(
            "    return (match options with\n"
            "      | [] => []\n"
            "      | _ :: rest => rest.map forwarded)"),
        "refinement": (
            "skipping the first declared option corresponds to a selection that "
            "iterates the declared options from the second onward. If that first "
            "option is a provided mandatory one its value is never threaded "
            "through and re-parsing reports it missing; a faithful real "
            "counterpart fails whenever the first declared option is a supplied "
            "required (or required-group) option, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the ensures `out = forwardedAll options`: `forwardedAll` "
            "pins the WHOLE list including the head, so dropping the first "
            "declared option's verdict shortens/shifts the result. Refuted at a "
            "TWO-element input `[forwardable, non-forwardable]` — varying the list "
            "SHAPE binder (length/order), the only binder the single-option rivals "
            "hold fixed. If it verified => SPEC-TOO-WEAK (list-shape incomplete)."
        ),
        "witness": _witness(
            f"[{_ov('true', 'true', 'false')}, {_ov('false', 'false', 'false')}]",
            "[true, false]"),
    },

    # =====================================================================
    # ADDED BY AUDIT — rivals aimed at what the ported six leave unattacked.
    # The six ported witnesses probe six of the eight rows of the
    # (supplied, individuallyRequired, inRequiredGroup) matrix; the rows
    # `¬supplied ∧ individuallyRequired ∧ inRequiredGroup` and
    # `¬supplied ∧ ¬individuallyRequired ∧ inRequiredGroup` were unprobed, and
    # NO ported rival attacked ORDER (they attack the verdict function and the
    # list LENGTH, but every one of them is order-preserving, so a spec that
    # pinned only the multiset of verdicts would have passed the whole battery).
    # =====================================================================
    {
        "id": "weak-mutex-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward on required-group membership ALONE: drop BOTH the `supplied`
        # conjunct and the `individuallyRequired` disjunct. Wrong in two
        # directions at once, and in particular wrong at
        # `¬supplied ∧ ¬individuallyRequired ∧ inRequiredGroup` — a row no ported
        # witness holds `inRequiredGroup` true at while `supplied` is false.
        "module": _map("a.inRequiredGroup"),
        "refinement": (
            "keying the decision on required-group membership alone forwards a "
            "group member whose value the caller never provided (an absent value "
            "is looked up at re-parse time) while silently dropping an option that "
            "is provided and individually required. A faithful real counterpart "
            "breaks both the mandatory-option scenarios and the ordinary "
            "command-call scenarios, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the ensures: `forwarded` requires the value to have been "
            "provided AND some obligation to hold, so keying on the group "
            "membership alone diverges. Refuted at input `[¬supplied ∧ "
            "¬individuallyRequired ∧ inRequiredGroup]`, a matrix row NO ported "
            "witness reaches (they never hold inRequiredGroup true with supplied "
            "false). Spec demands `[false]`. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(f"[{_ov('false', 'false', 'true')}]", "[false]"),
    },
    {
        "id": "weak-supplied-or-both",
        "kind": "uniqueness",
        "expect": "reject",
        # Mis-nest the connectives: `supplied ∨ (individuallyRequired ∧
        # inRequiredGroup)` instead of `supplied ∧ (individuallyRequired ∨
        # inRequiredGroup)`. A same-token, same-binder reshape of the predicate
        # that is a DIFFERENT Boolean function — the near-miss a spec pinning only
        # "reads all three observations" would admit.
        "module": _map("a.supplied || (a.individuallyRequired && a.inRequiredGroup)"),
        "refinement": (
            "swapping the conjunction and disjunction forwards every provided "
            "option regardless of obligation, and additionally forwards a "
            "doubly-mandatory option whose value was never provided. A faithful "
            "real counterpart both over-threads optional provided values and looks "
            "up absent ones, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the ensures: the connectives do not commute — `supplied ∨ "
            "(A ∧ B)` is a different Boolean function from `supplied ∧ (A ∨ B)`. "
            "Refuted at input `[¬supplied ∧ individuallyRequired ∧ "
            "inRequiredGroup]`, the remaining unprobed matrix row: the spec demands "
            "`[false]` (no value was provided) but this rival returns `[true]`. If "
            "it verified => SPEC-TOO-WEAK (the ensures would be pinning only which "
            "observations are read, not how they combine)."
        ),
        "witness": _witness(f"[{_ov('false', 'true', 'true')}]", "[false]"),
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # The RIGHT per-option verdict for every option, and the right number of
        # them — reported in reverse declaration order. Every ported rival is
        # order-preserving, so this is the only case that shows the ensures pins
        # ORDER and not just the multiset of verdicts.
        "module": _impl("    return ((options.map forwarded).reverse)"),
        "refinement": (
            "reversing the verdict list corresponds to a selection that walks the "
            "declared options backwards and emits the forwarded values in the "
            "opposite order. Argument re-parsing is positional in the values it "
            "receives, so the values are attached to the wrong options as soon as "
            "two declared options differ in verdict; a faithful real counterpart "
            "misroutes them and would NOT resolve."
        ),
        "rationale": (
            "REJECT from the ensures `out = forwardedAll options`: `forwardedAll` "
            "is front-recursive over DECLARATION ORDER, so it pins position, not "
            "just the multiset of verdicts. Refuted at the two-element input "
            "`[forwardable, non-forwardable]`, where the spec demands `[true, "
            "false]` and this rival returns `[false, true]`. This is the ONLY case "
            "attacking the order binder — all six ported rivals are "
            "order-preserving — so without it a spec pinning only the verdict "
            "multiset would have passed the whole battery. If it verified => "
            "SPEC-TOO-WEAK (order unconstrained)."
        ),
        "witness": _witness(
            f"[{_ov('true', 'true', 'false')}, {_ov('false', 'false', 'false')}]",
            "[true, false]"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 10 SPEC cases (2
# soundness positives, 1 admissibility, 1 mandatory frame-mutation, 6 uniqueness
# rivals) and no AXIOM_TESTS. This battery carries 13: the 9 ported/re-aimed
# cases below plus 4 ADDED BY AUDIT (pos-control-inlined-map, weak-mutex-only,
# weak-supplied-or-both, weak-reverse-order) that have no nagini counterpart and
# close gaps the port left — see the coverage note in the footer. The sibling contracts ONE function
# `select_forwarded(actions: List[int])` over a bit-encoded `List[int]` carrier
# (supplied/mandatory/in_mandated_set = bits 0/1/2 of each int) with a read-only
# half-permission precondition; this bundle contracts the SAME selection over a
# `List OptionView` (a record of the three observed Bools), which is the
# Lean-family narrowing of the same modeled behaviour.
#
#   nagini case                kind          -> here                     disposition
#   ---------------------------------------------------------------------------------
#   pos-control-helper         soundness     -> pos-control-direct       RE-EXPRESSED
#   pos-control-local          soundness     -> pos-control-local        PORTED
#   admiss-f2p-shaped-input    admissibility -> admiss-grounded          RE-AIMED
#   uniq-frame-mutate          uniqueness    -> (none)                   VACUOUS
#   uniq-prepatch-predicate    uniqueness    -> weak-prepatch-predicate  PORTED
#   uniq-over-forward          uniqueness    -> weak-over-forward        PORTED
#   uniq-drop-supplied         uniqueness    -> weak-drop-supplied       PORTED
#   uniq-drop-last             uniqueness    -> weak-skip-first          PORTED
#   uniq-empty                 uniqueness    -> weak-empty               PORTED
#   uniq-identity              uniqueness    -> weak-forward-all         PORTED
#   AXIOM_TESTS ([])           -                (none)                   VACUOUS
#
# RE-EXPRESSED (pos-control-helper -> pos-control-direct): the nagini honest
#   grounded control replaces the inlined disjunction with the @Pure helper
#   `forward(a)` consulted inside the backward fold. On this carrier `forwarded`
#   IS that helper and the ensures IS `out = forwardedAll options`, so the honest
#   cheapest impl is simply `return forwardedAll options` — the same argument (the
#   grounded pin is satisfiable only by the real per-option work; no wrong echo
#   verifies) as a loop-free correct impl. The loop-specific proof is retuned to a
#   bare loom_solve.
# PORTED (pos-control-local): bind the per-option verdict to a typed local before
#   prepending; same value flow, different executable shape, frozen proof closes
#   as-is.
# RE-AIMED (admiss-f2p-shaped-input -> admiss-grounded): the nagini case
#   self-called the function on an F2P-shaped input to exercise the read-only
#   fractional-permission precondition. This method has no `require` and no heap
#   permission, so that probe is vacuous; re-aimed at the residual total-domain
#   risk (a degenerate post-image) by discharging a live in-region assert pinning
#   the three F2P-discriminating verdicts.
# VACUOUS (uniq-frame-mutate) — DEMONSTRATED, not merely argued. The sibling's
#   MANDATORY frame rival writes through the read-only 1/2-permission input list
#   and is rejected for INSUFFICIENT PERMISSION. Velvet is referentially
#   transparent, the input is an immutable value, no `mut` binder, no heap, no
#   aliasing, no permission system — there is no read-only input to overwrite and
#   no substitute probe. The audit tried to land the rival anyway (assign to
#   `options` inside the impl region) and the compiler refuses the file outright:
#   "`options` cannot be mutated, only variables declared using `let mut` can be
#   mutated". So the class is not merely unmodeled here, it is unrepresentable:
#   the rival cannot be WRITTEN, let alone verified. Omitted as vacuous,
#   NOT fabricated. The sibling's read-only obligation is here structurally
#   guaranteed by the absence of `mut`, which the frozen spec already encodes.
# PORTED (the six uniqueness rivals): each nagini value-surface rival carries
#   across intact, only the carrier changing from a bit-encoded `List[int]` fold
#   to a `List OptionView` map. weak-prepatch-predicate (the headline pre-image
#   `supplied ∧ individuallyRequired`), weak-over-forward (`supplied` alone),
#   weak-drop-supplied (obligation without provided), weak-skip-first (nagini
#   uniq-drop-last: skip the first-declared option — front-recursive `forwardedAll`
#   over declaration order makes the head the first-declared option, so skipping
#   it is the same divergence), weak-empty (forward nothing), and weak-forward-all
#   (nagini uniq-identity: return every option's verdict `true` = the unfiltered
#   copy). Each carries its nagini refinement argument, now backed by a
#   machine-checked witness.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
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
# DROPPED (AXIOM_TESTS): the sibling declares no axiom (meta.json axioms == [],
#   deep_model_references == []); the selection is modeled deeply. Nothing for
#   G-AX, and the G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE (revised by the audit). The single
#   impl-constraining clause (`out = forwardedAll options`) is DEFENDED by three
#   positives and the admissibility case and ATTACKED by nine rivals. The nine
#   witnesses probe all EIGHT rows of the (supplied, individuallyRequired,
#   inRequiredGroup) matrix plus two two-element inputs:
#     [T,F,T] prepatch      [T,F,F] over-forward    [F,T,F] drop-supplied
#     [F,F,F] forward-all   [T,T,T] empty           [F,F,T] mutex-only
#     [F,T,T] supplied-or-both
#     [[T,T,F],[F,F,F]] skip-first (length) and reverse-order (order)
#   The ported six covered only six rows; `weak-mutex-only` ([F,F,T]) and
#   `weak-supplied-or-both` ([F,T,T]) close the matrix, and the latter is the
#   only rival that mis-nests the CONNECTIVES rather than dropping a binder — a
#   spec pinning merely "all three observations are read" would admit it.
#   The LIST-SHAPE binders are now split: weak-skip-first attacks LENGTH and
#   weak-reverse-order attacks ORDER. Every ported rival was order-preserving, so
#   before the audit a spec pinning only the verdict MULTISET would have passed
#   the entire battery.
#
# WITNESS MECHANICS — and the honest limit of the gold-side half. Each reject
#   case's witness now carries TWO checked lines: the post-image the frozen spec
#   fold demands at the input (`forwardedAll <input> = <value> := by decide`,
#   about the transparent fold only, hence true in both builds) and the rival's
#   violation there (`selectForwardedTester <input> = false := by decide`). All
#   nine re-checked with scripts/lean_verify.sh: rival exit 0, gold exit 1.
#   BUT gold's exit 1 is NOT a semantic refutation on this carrier. The frozen
#   impl's `while` loop extracts to well-founded recursion the kernel does not
#   reduce, so `decide` on gold reports "did not reduce to isTrue or isFalse ...
#   reduction got stuck". `#eval selectForwardedTester` returns `true` on gold at
#   all eight points, so gold genuinely satisfies the postcondition there — the
#   compiler establishes it, the kernel cannot. Consequence: the gate's
#   discrimination half is satisfied by the frozen impl's LOOP SHAPE, and a
#   merely-reshaped CORRECT loop-free rival would fail gold identically. What
#   actually attributes each rejection is the RIVAL-side half, which is a genuine
#   decision: `decide` reduced the rival's program and found the postcondition
#   FALSE. Measured control: the weak-prepatch-predicate witness built against the
#   CORRECT loop-free impl `return (forwardedAll options)` fails with "decide
#   proved that the proposition ... = false is false" — the opposite verdict — so
#   the rival-side half does discriminate correct from wrong. Each rival's
#   wrongness at its own point was also confirmed independently against the frozen
#   solution by `<rival's pure output> ≠ forwardedAll <input> := by decide`.
#   No witness binds a hypothesis, so no consistency probe is needed.
AXIOM_TESTS = []
