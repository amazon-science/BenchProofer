"""properties.py — G-PBT falsification battery for django__django-15741 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, the
``prove_correct`` tactic body — is changed, both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct lookupValue``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes
iff (in scope AND the file elaborates with every obligation closed);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` discriminates: the witness must ELABORATE against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE (one modeled method over a name carrier that may arrive
already resolved or deferred):

  lookupValue (nm : Name) return (out : Except LookupErr (List Char))
    ensures out = Except.ok (resolveName (force nm))            -- (Q) VALUE pin

The desired behaviour: a name supplied either already resolved OR as a deferred
computation is resolved to a concrete sequence of code points BEFORE it is used
as a lookup name, so the lookup never fails on a deferred name, and the result
is exactly the value associated with the forced (resolved) content. ``force``
is a total projection to the underlying content (``force (eager s) = s``,
``force (deferred s) = s``); the method has NO ``require`` clause, so the
admitted input domain is total. There is exactly ONE input binder, ``nm``, a
two-arm carrier (``eager`` / ``deferred``) each carrying a ``List Char``
payload.

CARRIER — the decisive fact of this port. ``resolveName : List Char → List
Char`` is an OPAQUE axiom (the unchanged downstream name→value resolution); the
kernel knows NOTHING about its value at any concrete input — that is exactly
what keeps the surface faithful (no concrete resolved value is pinned,
directive 7/8). The single postcondition clause (Q) has THREE transparent facets
even over the opaque callee (an earlier revision said TWO and enumerated only the
first two; the FIFTH audit landed the third, see reject-corrupt-served-value):

  * the RESULT CONSTRUCTOR is transparent: (Q) pins ``out`` to ``Except.ok
    (...)`` — never ``Except.error``. A rival that returns ``Except.error`` (the
    pre-patch crash, or an unconditional failure) violates (Q) at ANY input,
    decidable WITHOUT evaluating ``resolveName`` (``Except.error ≠ Except.ok``).
  * the ARGUMENT fed to the opaque callee is transparent: (Q) requires the
    argument to be ``force nm`` (the full resolved content). A rival that feeds
    ``resolveName`` a DIFFERENT sequence (empty, truncated, first-dropped) is
    refuted by CONDITIONING on the carrier — the hypothesis ``resolveName <wrong>
    ≠ resolveName <full>`` describes the sub-domain where the two calls differ
    (a stronger statement than any single literal input, since we cannot compute
    the opaque value). The single hypothesis is weak and self-satisfiable (two
    distinct arguments to an opaque function need not agree), so the refuting
    input genuinely exists; two hypotheses about the SAME term are never used.
  * the callee's ANSWER is transparently PASSED THROUGH: (Q) pins ``out`` to
    ``Except.ok (resolveName (force nm))`` — the callee's own result, unaltered.
    A rival that applies the callee to the HONEST argument and then ALTERS what
    came back (reverse it, truncate it, overwrite a code point of it) violates
    (Q) without ever mis-keying the lookup, and is refuted by conditioning on
    the ALTERATION rather than on the argument: ``f (resolveName A) ≠ resolveName
    A`` for a concrete rewriting ``f``. Distinct from the argument facet in
    which SIDE of the callee the fault sits on, and it is the facet the sibling's
    value-PRESERVATION family is about. ships as reject-corrupt-served-value.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    mandatory frame-mutation rivals (write ``requested_name.content`` through a
    read-only ``Acc(list_pred(...),1/2)`` reference — append / index-store)
    because its input is held at a fractional heap permission an impl can
    illegally overwrite. Lean and Velvet are referentially transparent: ``nm`` is
    an immutable value, this bundle declares NO ``mut`` binder, there is no heap
    and no aliasing — so there is no read-only field to mutate and no substitute
    probe to build. Not fabricated (per the porting map, this class is vacuous
    here).
  * DIVERGENCE / NON-TERMINATION - nothing to ship here, and the reason is neither
    vacuity nor a spec hole: the class is CLOSED BY THE SEMANTICS. This slot has
    been wrong twice and both errors are retracted.
    (i) The first revision called the class "vacuous on this backend" because the
    impl region "admits no non-terminating rival to express". False: a rival owns
    the whole impl region and can splice a loop of its own.
    (ii) The audit then said that a spliced ``while True do pure ()`` prefix
    VERIFIES under this bundle's ``set_option loom.semantics.termination "total"``,
    on the ground that the postcondition is claimed only of terminating runs so the
    value pin (Q) is satisfied on an unreachable exit, and recorded that as an
    escalated spec-level finding with a corpus census (``mode=partial,
    outcome=VERIFIES``; "401 of 500 velvet bundles"). Every part of that is false.
    "Claimed only of terminating runs" is the PARTIAL rule; under ``total`` a
    postcondition is claimed of ALL runs, and the verifier demands a decreasing
    measure on every loop. The option cannot drift from the file's
    ``open TotalCorrectness DemonicChoice``, because the ``set_option`` elaborator
    itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). And the census has no
    referent: all 500 velvet bundles set ``"total"``.
    Re-measured on THIS instance, proof reduced to a bare ``loom_solve``: the
    unmeasured spun prefix is REJECTED at elaboration (``Decreasing annotations are
    required in total correctness semantics``), and the sharper shape that CARRIES a
    measure which does not decrease (``while q > 0 / invariant 0 ≤ q /
    done_with q = 0 / decreasing q``, body ``q := q``) is REJECTED on the measure's
    own goal - ``case «decreasing_1: q»``, residual ``⊢ q < q``. Nothing is
    escalated; the frozen option needs no flipping, because it is already ``total``.
    The DISPOSITION is still "no case here", and for a WITNESS reason rather than
    a spec one — but the third audit corrected the reason itself, which was stated
    too broadly. The claim was that "a rejected diverging rival's module does not
    compile at all (the obligation fails at the ``method`` itself, ahead of any
    appended tester), so the gate would return ``witness-unproven``". That holds
    for the UNMEASURED shape only, and it was re-confirmed: the witness file built
    over ``while True do pure ()`` fails at the loop itself (exit 1, ``Decreasing
    annotations are required in total correctness semantics``), ahead of any
    tester, so indeed no witness can elaborate. It is FALSE for the sharper
    measured-non-decreasing shape: that rival's failure is at the measure's own
    goal inside ``prove_correct``, and ``witness_file`` STRIPS ``prove_correct``,
    so its module compiles fine with a witness appended (measured: a trivial
    ``example : (1:Nat)+1 = 2`` witness over it builds, exit 0). So "the module
    does not compile" is not why that shape ships no case.
    The real reason it ships none is stronger and is about the CLAIM, not the
    build: a measured-non-decreasing rival is value-CORRECT — its body is
    ``q := q`` and it returns the honest ``Except.ok (resolveName (force nm))`` —
    so there is no input at which it contradicts (Q), and a witness must assert a
    violation of the spec. There is nothing true to assert. (Confirmed
    incidentally: on that rival ``(lookupValue nm).run`` does not reduce at all, a
    type-reveal printing the unnormalised ``NonDetT.run (lookupValue nm)``, which
    is the gate's own ``loop-unification`` stuck class — so even a forged witness
    there would be screened as undecided rather than recorded.) A rival rejected
    ONLY for its termination measure is not a spec falsification on this lane;
    ``variant_scope`` and the ``total`` semantics already reject it, which is the
    correct behaviour, and the reject lane's job is attributing a rejection to (Q).
    Not fabricated, and no longer claimed vacuous or holed.
  * UNGROUNDED-ORACLE ECHO — the nagini note frames its "wrong key" family
    (empty / truncated / deferred-skip) as PARTIAL-DOMAIN attacks, NOT true
    ungrounded echoes, because (Q) pins ``out`` to ``resolveName (force nm)``:
    the opaque callee's own value applied to the GROUNDED argument ``force nm``,
    with no free oracle value to echo. Same here — the only way to satisfy (Q)
    is to feed the honest resolved content, so the wrong-key rivals below are
    carried as the partial-domain attacks they are (refuted by conditioning on
    the argument facet).

WITNESS MECHANICS ON THIS BUNDLE. The postcondition is a bare equality with no
unbounded quantifier, but the method returns a ``noncomputable`` value (its RHS
applies the opaque ``resolveName``), so the ``extract_program_for`` /
``<name>Exec`` route does not compile (``depends on ... which has no executable
code``). Each witness therefore reaches the contract DIRECTLY over the method's
own ``.run``: ``(lookupValue nm).run`` reduces to ``DivM.res <the returned
value>``, and ``(lookupValue nm).run ≠ DivM.res (Except.ok (resolveName (force
nm)))`` says the impl's result contradicts the spec's grounded answer at that
concrete ``nm``. Checked in a file whose ``prove_correct`` block is stripped, so
no tactic script can mask the verdict; the method has no ``require`` clause, so
every input reaches the postcondition. Each witness ELABORATES against its rival
and FAILS against the frozen solution — both halves checked out-of-band with
``scripts/lean_verify.sh`` (rival exit 0, gold exit 1) for every reject case.
The SEVEN conditioned witnesses that bind a hypothesis over the opaque term
(reject-empty-key, reject-deferred-empty-key, reject-drop-last,
reject-skip-first, reject-guarded-selfvalue, reject-guarded-input-content,
reject-corrupt-served-value — an earlier revision of this note said "two", which
undercounted them, then "four" and then "five", each of which predated a later
case) each keep exactly ONE hypothesis, so nothing constrains the same term twice
and the hypothesis is satisfiable. Three shapes of hypothesis are used, and they
are exercised in opposite directions on purpose. The argument-facet ones relate
two DISTINCT opaque arguments by DISEQUALITY (``resolveName A ≠ resolveName B``
for syntactically distinct A, B, which an opaque function need not identify);
reject-guarded-selfvalue asserts an EQUALITY between one opaque application and a
literal (``resolveName ['H',':','i'] = ['H',':','i']``, which nothing forbids —
an opaque function may map a name to itself); and reject-corrupt-served-value
relates ONE opaque application to a REWRITING of itself by disequality
(``(resolveName A).set 0 'X' ≠ resolveName A``, which nothing forbids either —
nothing makes an opaque function's value at a name a fixed point of overwriting
its first code point). Confirmed rather than argued: the gate's consistency probe
was re-run against all of them out-of-band and every one FAILS (exit 1, no
``False`` derivable from the hypothesis alone — reject-guarded-selfvalue reports
``simp_all made no progress``), so each refuting input genuinely exists and there
is no ``witness-inconsistent`` risk.

ADMISSIBILITY on a total carrier. The method has NO ``require`` clause, and an
earlier revision of this file read that as making the lane vacuous. It does not:
the analogue of PRECOND-TOO-STRONG on a total domain is the obligation being
UNSATISFIABLE at exactly an F2P-shaped input, and the frozen proof verifying does
not speak to that (it discharges (Q) universally without ever exhibiting the
post-image at the concrete input the behaviour is about). ``admiss-f2p-shaped-input``
tests it directly, by evaluation at ``nm = Name.deferred ['D','A','T','E']`` as a
``have`` ahead of the verbatim frozen body; see that case and the ACCOUNTING block.
(An earlier revision of this paragraph named ``['H',':','i']`` here, which is the
input the eager-carrier reject witnesses use, not the one the admissibility case
actually discharges at — corrected by audit against the case's own source.)

AXIOM lane: DROPPED. The ``axioms`` region declares ``resolveName``, validated
by G-AX (``axiom_check.py`` runs the real ``get_format`` against the
resolved-name-function property), NOT this gate's concern; and the gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15741"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the two CODE lines of the frozen impl body. The three
# ---- comment lines above them are also inside the region, but anchoring on the
# ---- code keeps the surgery unambiguous. Lies wholly inside the single
# ---- -- impl-start / -- impl-end region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so each edit keeps same_spec by
# ---- construction and leaves the frozen `prove_correct lookupValue` statement
# ---- intact.
_IMPL = (
    "    let key := force nm\n"
    "    return Except.ok (resolveName key)"
)
assert _BASE.count(_IMPL) == 1, "lookupValue impl region drifted from expected text"


def _impl(new_body: str) -> str:
    """Full Solution.lean variant with ONLY lookupValue's impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- the frozen `prove_correct` tactic body, and the re-proving variant. A
# ---- case may legitimately re-prove the SAME obligation (variant_scope keeps
# ---- the `prove_correct lookupValue` header and forbids new axioms / sorry /
# ---- new theorems; only the tactic body may differ), and a positive control
# ---- MUST be allowed to, or the only impls that can pass are the ones the
# ---- frozen script already happens to close — which on this carrier means the
# ---- ones that are DEFINITIONALLY the frozen impl, i.e. no soundness test at
# ---- all. See the DEFINITIONAL-EQUALITY block in the ACCOUNTING notes.
_FROZEN_TAC = "prove_correct lookupValue by\n  loom_solve"
_REPROVE_TAC = ("prove_correct lookupValue by\n"
                "  loom_solve <;> simp_all [force, Name.content]")
assert _BASE.count(_FROZEN_TAC) == 1, "prove_correct body drifted from expected text"


def _impl_reproved(new_body: str) -> str:
    """`_impl(new_body)`, with the frozen tactic body replaced by `_REPROVE_TAC`.

    Same obligation, same statement, different SCRIPT — the one degree of
    freedom `variant_scope` grants a variant beyond the impl region.
    """
    return _swap(_impl(new_body), _FROZEN_TAC, _REPROVE_TAC)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Ports the nagini
    # positive-control ARGUMENT ("a faithful, structurally-different correct impl
    # is not rejected") onto this carrier — the two nagini positives (local-bound
    # reshape, redundant framing assert) have no direct counterpart on a two-line
    # functional impl.
    #
    # READ THIS BEFORE TRUSTING THE THREE CASES IMMEDIATELY BELOW. They keep the
    # frozen `prove_correct ... loom_solve` body verbatim and each verifies (exit
    # 0), but the second audit measured what that verification is worth: all
    # three, and the admissibility case, are DEFINITIONALLY EQUAL to the frozen
    # impl — `rfl` alone closes `(lookupValue nm).run = DivM.res (Except.ok
    # (resolveName (force nm)))` against each of them, exactly as against gold. On
    # this carrier `let` is a definitional binding, `have` is erased, and inlining
    # `force nm` rewrites no term, so "a different shape" here is a different
    # SPELLING of one term. They are kept (they are honest, cheap, and they do
    # pin that the frozen script is not sensitive to those spellings) but they
    # cannot detect SPEC-TOO-STRONG, because a spec cannot be over-fit to a form
    # that IS the frozen form. The lane's actual weight is carried by
    # pos-match-carrier and pos-branch-both-arms-content further down, which fail
    # that `rfl` probe.
    # =====================================================================
    {
        "id": "pos-inline-force",
        "kind": "soundness",
        "expect": "verify",
        # Inline the forced key: `resolveName (force nm)` directly, no `let`.
        "module": _impl("    return Except.ok (resolveName (force nm))"),
        "rationale": "PASS SOURCE = (Q) out = Except.ok (resolveName (force nm)). "
                     "Inlining the forced key (dropping the intermediate `let key "
                     ":= force nm` and writing `resolveName (force nm)` directly) "
                     "is observationally identical to the frozen impl, so (Q) "
                     "discharges and the frozen `loom_solve` body closes it "
                     "unchanged. A structurally different faithful reshape MUST "
                     "verify; if it cannot, the spec is over-fit to the exact "
                     "return FORM (SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-let-value",
        "kind": "soundness",
        "expect": "verify",
        # Bind the resolved value into an intermediate local, then wrap it.
        "module": _impl(
            "    let key := force nm\n"
            "    let value := resolveName key\n"
            "    return Except.ok value"),
        "rationale": "PASS SOURCE = (Q). Forcing the name, binding the resolved "
                     "value to an intermediate local `value`, and returning "
                     "`Except.ok value` (an extra binding, same semantics) is "
                     "observationally identical to the direct form, so (Q) still "
                     "discharges and the frozen `loom_solve` body closes it "
                     "unchanged. A faithful reshape MUST verify, else "
                     "SPEC-TOO-STRONG.",
    },

    # ---------------------------------------------------------------------
    # The two positives that are NOT definitionally the frozen impl. LANDED BY
    # THE SECOND AUDIT, and they are the ones that carry the soundness lane.
    #
    # Measured, not argued: the probe
    #   example (nm : Name) : (lookupValue nm).run
    #       = DivM.res (Except.ok (resolveName (force nm))) := by rfl
    # closes by `rfl` ALONE against the frozen solution and against all four of
    # the pre-existing expect="verify" cases (exit 0 x5). That means every one of
    # them normalises to the frozen impl's own normal form: `let` is a
    # definitional binding, `have` is erased, and inlining `force nm` changes no
    # term. They are TYPOGRAPHICAL reshapes, so the frozen `loom_solve` closes
    # them for the same reason it closes gold, and SPEC-TOO-STRONG was never
    # actually probed — the spec cannot be over-fit to a form that IS the frozen
    # form. The two cases below fail that same `rfl` probe (exit 1: "The
    # left-hand side NonDetT.run (lookupValue nm) is not definitionally equal to
    # the right-hand side"), so they are the first positives on this bundle whose
    # verification is a real obligation discharge rather than an identity.
    #
    # They re-prove (`loom_solve <;> simp_all [force, Name.content]`), which is
    # in scope and is what 428 of the 500 velvet batteries do for exactly this
    # reason (re-measured by the FOURTH audit against every velvet manifest: 428
    # carry at least one case whose `prove_correct` tactic body differs from the
    # frozen one, and in all 428 at least one of those is an expect="verify"
    # case; an earlier revision of this line said 413, which does not reproduce);
    # under the FROZEN script alone both fail (exit 1, residual
    # `⊢ Except.ok (resolveName ...) = Except.ok (resolveName (force nm))` with
    # the carrier destructed), which is tactic-shape brittleness, not a spec
    # defect. An earlier revision recorded both shapes in a prose "audit probes"
    # note as reshapes that were checked and found provable, but shipped NEITHER
    # as a case — so the battery's soundness lane consisted entirely of
    # definitional identities while the note claimed the direction was covered.
    # ---------------------------------------------------------------------
    {
        "id": "pos-match-carrier",
        "kind": "soundness",
        "expect": "verify",
        # Dispatch on the carrier ARM instead of projecting through `force`:
        # each arm resolves its own payload directly. Case-splits the input, so
        # the residual goal is per-arm and no longer closes by reflexivity.
        "module": _impl_reproved(
            "    match nm with\n"
            "    | .eager s => return Except.ok (resolveName s)\n"
            "    | .deferred s => return Except.ok (resolveName s)"),
        "rationale": "PASS SOURCE = (Q) out = Except.ok (resolveName (force nm)). "
                     "Matching on the carrier and resolving each arm's payload "
                     "directly is faithful — `force` IS the projection to the "
                     "payload on both arms, so both arms feed the honest resolved "
                     "content — but it is NOT definitionally the frozen impl: the "
                     "`rfl` probe above fails on it (exit 1), because the impl now "
                     "case-splits `nm` while the spec's RHS still applies `force` to "
                     "the undestructed binder. So the obligation is genuinely "
                     "re-discharged (`simp_all [force, Name.content]` supplies the "
                     "per-arm identification) rather than closed by reflexivity. "
                     "This is the real SPEC-TOO-STRONG probe: if a correct impl that "
                     "reaches the payload by DESTRUCTING the carrier could not be "
                     "proven, the spec would be over-fit to reaching it by "
                     "projection, i.e. to the frozen impl's own form. It can, so no "
                     "soundness hole. Audit build: verifies exit 0.",
    },
    {
        "id": "pos-branch-both-arms-content",
        "kind": "soundness",
        "expect": "verify",
        # Branch on the deferred TAG and resolve `nm.content` on BOTH arms —
        # bypassing `force` entirely while remaining correct, since `force` is
        # exactly `Name.content`. Introduces an `if`, so an if-split survives
        # into the residual goal and reflexivity no longer closes it.
        "module": _impl_reproved(
            "    if nm.isDeferred then\n"
            "      return Except.ok (resolveName nm.content)\n"
            "    else\n"
            "      return Except.ok (resolveName nm.content)"),
        "rationale": "PASS SOURCE = (Q). Both arms of the tag test resolve "
                     "`nm.content`, which is exactly what `force` unfolds to, so "
                     "the impl is correct AND treats the two carriers identically "
                     "— the property the desired behaviour is about, reached "
                     "WITHOUT calling the projection the spec names. Not "
                     "definitionally the frozen impl (`rfl` probe fails, exit 1: "
                     "the `if` on the tag survives into the goal, and the spec's "
                     "RHS is stated over `force nm`), so verification is a real "
                     "discharge. Two independent things must hold for it to pass: "
                     "that `force` and the content projection agree, and that a "
                     "vacuous tag split does not perturb (Q). Distinct from "
                     "pos-match-carrier, which destructs the carrier rather than "
                     "testing its tag, and from the frozen impl, which does "
                     "neither. If either could not be established the spec would "
                     "be over-fit to the projection SPELLING (SPEC-TOO-STRONG). "
                     "Audit build: verifies exit 0.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — the third direction this gate exists
    # to test. Landed by AUDIT: an earlier revision recorded the lane as VACUOUS
    # because the method declares no `require` clause, which is not the right
    # test on a total carrier. The analogue here is the obligation being
    # UNSATISFIABLE at exactly an F2P-shaped input, and that is directly
    # testable: discharge the post-image at the concrete input, as a `have`,
    # before closing the frozen obligation verbatim.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        # The post-image is satisfiable at an F2P-shaped DEFERRED name, it agrees
        # there with the already-resolved name of the same content, and it is not
        # the failure outcome. Stated as a proof-carrying `have` inside the impl
        # region (elided from the spec view, so same_spec holds), then the frozen
        # body runs unchanged so (Q) still discharges under the frozen tactic.
        "module": _impl(
            "    have hadm : ∃ out : Except LookupErr (List Char),\n"
            "        out = Except.ok (resolveName (force (Name.deferred ['D','A','T','E'])))\n"
            "        ∧ out = Except.ok (resolveName (force (Name.eager ['D','A','T','E'])))\n"
            "        ∧ out ≠ Except.error LookupErr.unresolvedName := by\n"
            "      refine ⟨Except.ok (resolveName ['D','A','T','E']), ?_, ?_, ?_⟩ <;>\n"
            "        simp [force, Name.content]\n"
            "    let key := force nm\n"
            "    return Except.ok (resolveName key)"),
        "rationale": "PASS SOURCE = (Q) out = Except.ok (resolveName (force nm)), "
                     "discharged AT A CONCRETE F2P-SHAPED INPUT before the frozen "
                     "body closes it in general. The admitted input domain is "
                     "total (no `require` clause), so the residual "
                     "PRECOND-TOO-STRONG risk on this carrier is not a rejected "
                     "input but an UNSATISFIABLE post-image at a normal input. "
                     "The `have` refutes exactly that, on three counts at nm = "
                     "Name.deferred ['D','A','T','E']: (i) some `out` satisfies "
                     "(Q) there, so the obligation is not unsatisfiable at the "
                     "deferred carrier; (ii) the SAME `out` satisfies (Q) at the "
                     "eager name of identical content, so the spec genuinely "
                     "identifies the two carriers rather than admitting them "
                     "separately — the property the desired behaviour is about; "
                     "(iii) that `out` is not Except.error, so the post-image is "
                     "non-degenerate (a spec satisfiable only by the failure "
                     "outcome would admit the normal input in name only). If any "
                     "of the three could not be established the `have` would not "
                     "discharge => PRECOND-TOO-STRONG / unsatisfiable post-image. "
                     "Content, not decoration: the negative control that swaps "
                     "clause (ii)'s name for ['X'] FAILS (audit build, exit 1, "
                     "`unsolved goals ⊢ resolveName ['D','A','T','E'] = "
                     "resolveName ['X']`), so the `have` is not provable for an "
                     "arbitrary pair of names. Ports the sibling's "
                     "admiss-f2p-shaped-input onto this carrier.",
    },

    {
        "id": "pos-framing-have",
        "kind": "soundness",
        "expect": "verify",
        # The frozen body, preceded by a redundant TRUE framing fact: forcing a
        # name is exactly the projection to its content. Adds an obligation
        # (the `have` must be discharged), removes none.
        "module": _impl(
            "    have hframe : force nm = nm.content := rfl\n"
            "    let key := force nm\n"
            "    return Except.ok (resolveName key)"),
        "rationale": "PASS SOURCE = (Q), with the frozen body kept VERBATIM and a "
                     "redundant framing fact `force nm = nm.content` proved ahead "
                     "of it by `rfl`. This is the direct port of the sibling "
                     "battery's redundant-framing positive (previously recorded as "
                     "FOLDED into the two reshapes, which understated the battery: "
                     "the two reshapes both perturb the RETURN form, while this one "
                     "leaves the return form alone and instead ADDS an obligation). "
                     "The added fact is exactly what `force` unfolds to, so it must "
                     "hold and the frozen `loom_solve` body must still close (Q). If "
                     "it cannot, the spec/`force` definition are mis-stated relative "
                     "to each other (SPEC-TOO-STRONG). Verified out-of-band with a "
                     "real build, EXIT 0.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input that ELABORATES against the rival and FAILS against gold.
    # They attack the single postcondition clause (Q) on its two transparent
    # facets (see the module docstring): the RESULT CONSTRUCTOR (ok vs error)
    # and the ARGUMENT fed to the opaque callee (full vs wrong resolved content,
    # via conditioning).
    # =====================================================================

    # ---- (Q) constructor facet: the result must be Except.ok, never error ----
    {
        "id": "reject-deferred-error",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: an already-resolved name is looked up, but a
        # DEFERRED name is not forced first and so fails the lookup.
        "module": _impl(
            "    if nm.isDeferred then\n"
            "      return Except.error LookupErr.unresolvedName\n"
            "    else\n"
            "      return Except.ok (resolveName nm.content)"),
        "refinement": "this is the pre-patch behaviour: a name that arrives "
                      "deferred is used as a lookup name in its unforced state, "
                      "which fails. The failing example supplies a deferred name "
                      "and expects the lookup to succeed and return the same value "
                      "as the already-resolved form; a variant that fails on the "
                      "deferred name leaves that assertion RED. Its faithful real "
                      "counterpart (resolve only the already-resolved branch) is "
                      "precisely what does NOT resolve the F2P tests test_date_lazy "
                      "and test_get_format_lazy_format — it would NOT resolve.",
        "rationale": "REJECT from (Q) out = Except.ok (resolveName (force nm)): on "
                     "a deferred name the rival returns Except.error, but (Q) pins "
                     "the constructor to Except.ok. Refuted at nm = Name.deferred "
                     "['A'] — a fully transparent facet (Except.error ≠ Except.ok), "
                     "decidable without evaluating resolveName. Attacks the result "
                     "constructor; the wrong-key rivals below attack the argument.",
        "witness":
            "example : (lookupValue (Name.deferred ['A'])).run\n"
            "    ≠ DivM.res (Except.ok (resolveName ['A'])) := by\n"
            "  simp only [lookupValue, Name.isDeferred, Name.content, if_true,\n"
            "    NonDetT.run, Pure.pure]\n"
            "  intro h\n"
            "  exact Except.noConfusion (DivM.res.inj h)\n",
    },
    {
        "id": "reject-always-error",
        "kind": "uniqueness",
        "expect": "reject",
        # Unconditional failure: never resolves any name, even an eager one.
        "module": _impl("    return Except.error LookupErr.unresolvedName"),
        "refinement": "returning a failure for every name corresponds to a patch "
                      "that never resolves the lookup at all — strictly worse than "
                      "the pre-patch behaviour, which at least resolved eager "
                      "names. Every format lookup (eager or lazy) that the F2P and "
                      "P2P tests perform would fail, so it would NOT resolve. A "
                      "near-miss on the constructor facet that reject-deferred-error "
                      "does not subsume: it fails on an EAGER name too, so it is "
                      "witnessed at an eager input.",
        "rationale": "REJECT from (Q): the rival returns Except.error "
                     "unconditionally, so (Q) fails at any input — witnessed at the "
                     "eager name ['H',':','i'], distinct from the deferred witness "
                     "above so the binder `nm` is varied across both carriers. "
                     "Transparent constructor facet (Except.error ≠ Except.ok).",
        "witness":
            "example : (lookupValue (Name.eager ['H',':','i'])).run\n"
            "    ≠ DivM.res (Except.ok (resolveName ['H',':','i'])) := by\n"
            "  simp only [lookupValue, NonDetT.run, Pure.pure]\n"
            "  intro h\n"
            "  exact Except.noConfusion (DivM.res.inj h)\n",
    },

    # ---- (Q) argument facet: the callee must see `force nm`, not a wrong key ----
    {
        "id": "reject-deferred-empty-key",
        "kind": "uniqueness",
        "expect": "reject",
        # THE faithful shape of the sibling's deferred-skip rival: the deferred
        # branch is not forced, so the lookup receives an EMPTY key while the
        # already-resolved branch is handled correctly. Constructor stays `ok`,
        # so the constructor-facet rivals do NOT subsume this one.
        "module": _impl(
            "    if nm.isDeferred then\n"
            "      return Except.ok (resolveName [])\n"
            "    else\n"
            "      return Except.ok (resolveName (force nm))"),
        "refinement": "the sibling battery's deferred-skip rival leaves the "
                      "name's character buffer EMPTY on the deferred branch and "
                      "feeds that empty key to the downstream resolution — it does "
                      "not raise, it silently resolves the wrong name. That is the "
                      "half of the failure family the constructor-facet rivals miss: "
                      "a patch that handles an already-resolved name correctly and "
                      "quietly looks up nothing for a deferred one still returns a "
                      "value, so it fails the F2P assertions on the VALUE (the "
                      "deferred and already-resolved forms must agree) rather than "
                      "by crashing. A faithful such patch does NOT resolve.",
        "rationale": "REJECT from (Q) out = Except.ok (resolveName (force nm)): on a "
                     "DEFERRED name the rival feeds resolveName the empty list, not "
                     "force nm, while keeping the Except.ok constructor — so neither "
                     "the constructor-facet rivals (which are refuted by ok≠error) "
                     "nor the eager-witnessed argument-facet rivals (whose witnesses "
                     "all sit at Name.eager, where this rival AGREES with gold) "
                     "cover it. This is the only case that attacks the ARGUMENT "
                     "facet at the DEFERRED carrier, which is precisely the carrier "
                     "the desired behaviour is about. Conditioned on the opaque "
                     "callee via the single weak hypothesis `resolveName [] ≠ "
                     "resolveName ['D','A','T','E']`, refuted at nm = Name.deferred "
                     "['D','A','T','E']. Self-satisfiable (two distinct arguments to "
                     "an opaque function need not agree), so the refuting input "
                     "genuinely exists.",
        "witness":
            "example (h : resolveName [] ≠ resolveName ['D','A','T','E']) :\n"
            "    (lookupValue (Name.deferred ['D','A','T','E'])).run\n"
            "      ≠ DivM.res (Except.ok (resolveName ['D','A','T','E'])) := by\n"
            "  simp only [lookupValue, Name.isDeferred, Name.content, force, if_true,\n"
            "    NonDetT.run, Pure.pure]\n"
            "  intro heq\n"
            "  exact h (Except.ok.inj (DivM.res.inj heq))\n",
    },
    {
        "id": "reject-empty-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Feed the opaque callee an EMPTY key regardless of the name's content
        # (the distilled empty-key shape). Correct only on the one input whose
        # resolved content is empty — a partial-domain attack.
        "module": _impl("    return Except.ok (resolveName [])"),
        "refinement": "resolving every name to the empty key corresponds to a "
                      "patch that passed an unresolved/empty name to the downstream "
                      "resolution — the failure family the bug is about (the name "
                      "never reaches the lookup as its real characters). The value "
                      "for the empty key differs from the value for a real format "
                      "name, so the F2P assertions on the actual value would fail. "
                      "It agrees with gold only on the empty-content input, "
                      "diverging everywhere else — verify-not-resolve. It would NOT "
                      "resolve.",
        "rationale": "REJECT from (Q) out = Except.ok (resolveName (force nm)): the "
                     "rival feeds resolveName the empty list, so its argument is "
                     "not force nm. The value pin references the OPAQUE resolveName, "
                     "so the refutation is stated by CONDITIONING on the carrier — "
                     "the hypothesis `resolveName [] ≠ resolveName ['A']` describes "
                     "the sub-domain where the rival is wrong. The single "
                     "hypothesis is weak and self-satisfiable (two distinct "
                     "arguments to an opaque function need not agree), so the "
                     "refuting input genuinely exists.",
        "witness":
            "example (h : resolveName [] ≠ resolveName ['A']) :\n"
            "    (lookupValue (Name.eager ['A'])).run\n"
            "      ≠ DivM.res (Except.ok (resolveName ['A'])) := by\n"
            "  simp only [lookupValue, NonDetT.run, Pure.pure]\n"
            "  intro heq\n"
            "  exact h (Except.ok.inj (DivM.res.inj heq))\n",
    },
    {
        "id": "reject-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Truncate the LAST code point of the resolved content before the lookup
        # (partial-domain, the len-1 boundary). Correct only when dropping the
        # last code point leaves the value unchanged — wrong in general.
        "module": _impl(
            "    let key := (force nm).dropLast\n"
            "    return Except.ok (resolveName key)"),
        "refinement": "truncating the last code point corresponds to a patch that "
                      "resolved the name to the wrong string (e.g. \"H:\" instead of "
                      "\"H:i\"). The downstream resolution keyed on the truncated "
                      "name returns a different value, so the F2P assertions on the "
                      "full-name value fail. A faithful such patch does NOT resolve.",
        "rationale": "REJECT from (Q): the rival feeds resolveName the resolved "
                     "content with its last element dropped, not force nm. "
                     "Conditioned on the opaque callee via the single weak "
                     "hypothesis `resolveName ['H',':'] ≠ resolveName ['H',':','i']` "
                     "(the truncated-vs-full sub-domain), refuted at nm = "
                     "Name.eager ['H',':','i']. Self-satisfiable (distinct opaque "
                     "arguments), so the refuting input exists.",
        "witness":
            "example (h : resolveName ['H',':'] ≠ resolveName ['H',':','i']) :\n"
            "    (lookupValue (Name.eager ['H',':','i'])).run\n"
            "      ≠ DivM.res (Except.ok (resolveName ['H',':','i'])) := by\n"
            "  simp only [lookupValue, Name.content, force, NonDetT.run, Pure.pure,\n"
            "    List.dropLast]\n"
            "  intro heq\n"
            "  exact h (Except.ok.inj (DivM.res.inj heq))\n",
    },
    {
        "id": "reject-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the FIRST code point (the opposite boundary from drop-last).
        # Supporting partial-domain near-miss.
        "module": _impl(
            "    let key := (force nm).tail\n"
            "    return Except.ok (resolveName key)"),
        "refinement": "dropping the first code point resolves the name to a "
                      "different string (\":i\" instead of \"H:i\"); the downstream "
                      "resolution returns the wrong value and the F2P assertions "
                      "fail. Supporting partial-domain near-miss on the opposite "
                      "boundary from reject-drop-last; a faithful such patch does "
                      "NOT resolve.",
        "rationale": "REJECT from (Q): the rival feeds resolveName the resolved "
                     "content with its first element dropped, not force nm. "
                     "Conditioned on the opaque callee via the single weak "
                     "hypothesis `resolveName [':','i'] ≠ resolveName ['H',':','i']`, "
                     "refuted at nm = Name.eager ['H',':','i']. Self-satisfiable "
                     "(distinct opaque arguments), so the refuting input exists.",
        "witness":
            "example (h : resolveName [':','i'] ≠ resolveName ['H',':','i']) :\n"
            "    (lookupValue (Name.eager ['H',':','i'])).run\n"
            "      ≠ DivM.res (Except.ok (resolveName ['H',':','i'])) := by\n"
            "  simp only [lookupValue, Name.content, force, NonDetT.run, Pure.pure,\n"
            "    List.tail]\n"
            "  intro heq\n"
            "  exact h (Except.ok.inj (DivM.res.inj heq))\n",
    },

    # ---- (Q) argument facet, GUARDED sub-domain: the one shape the six rivals
    # ---- above leave unattacked. LANDED BY THE THIRD AUDIT. Every pre-existing
    # ---- rival is wrong UNCONDITIONALLY on its own carrier arm (or on every
    # ---- input), so all six are refuted at a point the RIVAL's own control flow
    # ---- reaches unconditionally. None of them tests whether (Q) still binds on
    # ---- a sub-domain the rival reaches only under a GUARD over the opaque
    # ---- callee's own result — which is the shape the sibling's alias-dead-branch
    # ---- case is about, and which the port's accounting table omitted entirely
    # ---- (see the OMISSION note in the ACCOUNTING block).
    {
        "id": "reject-guarded-selfvalue",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct EVERYWHERE except on the sub-domain where the resolved value
        # happens to equal the resolved name itself; there it returns the empty
        # value. The guard is stated over the OPAQUE callee's result, so the
        # verifier cannot prove the branch dead — it must discharge (Q) on it.
        "module": _impl(
            "    let key := force nm\n"
            "    if resolveName key = key then\n"
            "      return Except.ok []\n"
            "    else\n"
            "      return Except.ok (resolveName key)"),
        "refinement": "handing back an empty value for exactly those names the "
                      "downstream resolution answers with the name itself "
                      "corresponds to a patch that resolves the name correctly and "
                      "then special-cases the (large, ordinary) family of names the "
                      "lookup keeps no separate value for and returns unchanged. The "
                      "reported symptom is addressed — a deferred name IS forced, so "
                      "the F2P assertions on the lazily-supplied name hold — while "
                      "every request for a name in that family is served an empty "
                      "value instead of the name it asked with, so the P2P "
                      "assertions that read those names' values fail. FAIL_TO_PASS "
                      "passes and PASS_TO_PASS does not: a faithful such patch does "
                      "NOT resolve. This is the ONLY rival here whose fault lives on "
                      "a guarded sub-domain rather than on a whole carrier arm.",
        "rationale": "REJECT from (Q) out = Except.ok (resolveName (force nm)): on "
                     "the guarded branch the rival returns Except.ok [], but (Q) "
                     "pins out to Except.ok (resolveName (force nm)) there too. "
                     "Distinct from all six rivals above in WHERE the fault lives: "
                     "each of those is wrong unconditionally on an arm the control "
                     "flow always reaches, so its witness sits at a point reached "
                     "with no guard; this one is correct except under a condition "
                     "over the opaque callee's own RESULT. That is what makes it "
                     "non-subsumed — it tests that (Q) binds on a branch the "
                     "verifier cannot prove dead, rather than on a branch it always "
                     "takes. Because resolveName is opaque, `resolveName key = key` "
                     "is SATISFIABLE (nothing forbids the resolution of a name from "
                     "being that name), so the branch is live and the obligation "
                     "must be discharged on it — audit build, rejected exit 1 with "
                     "the guard in the hypothesis context and the residual goal "
                     "`if_pos : resolveName (force nm) = force nm ⊢ Except.ok [] = "
                     "Except.ok (resolveName (force nm))`. Conditioned on the "
                     "carrier via the single weak hypothesis `resolveName "
                     "['H',':','i'] = ['H',':','i']` (an EQUALITY over the opaque "
                     "term, where the six rivals above all use a disequality — so "
                     "the consistency probe is exercised in the opposite direction "
                     "too), refuted at nm = Name.eager ['H',':','i'].",
        "witness":
            "example (h : resolveName ['H',':','i'] = ['H',':','i']) :\n"
            "    (lookupValue (Name.eager ['H',':','i'])).run\n"
            "      ≠ DivM.res (Except.ok (resolveName ['H',':','i'])) := by\n"
            "  simp only [lookupValue, Name.content, force, NonDetT.run, Pure.pure, h,\n"
            "    if_true]\n"
            "  intro heq\n"
            "  exact absurd (Except.ok.inj (DivM.res.inj heq)) (by simp [h])\n",
    },

    # ---- (Q) argument facet, guarded on a TRANSPARENT predicate over the INPUT.
    # ---- LANDED BY THE FOURTH AUDIT. reject-guarded-selfvalue guards on the
    # ---- OPAQUE callee's result, and the other six are wrong unconditionally on
    # ---- a whole carrier arm — so every existing rival is either wrong on an arm
    # ---- the control flow always reaches, or wrong on a sub-domain the verifier
    # ---- cannot even see into. None of them asks whether (Q) binds on a branch
    # ---- the verifier CAN decide: a guard over the resolved content itself,
    # ---- taken at exactly one concrete name and honest at every other. That is
    # ---- the shape a targeted patch actually has, and it is the shape a spec
    # ---- that only pinned (Q) "generically" would admit.
    {
        "id": "reject-guarded-input-content",
        "kind": "uniqueness",
        "expect": "reject",
        # Honest EVERYWHERE except at one concrete resolved content, where the
        # key is truncated. The guard is over the input's own resolved content,
        # so it is fully transparent — the verifier can decide which branch a
        # given name takes, and must still discharge (Q) on the guarded one.
        "module": _impl(
            "    let key := force nm\n"
            "    if key = ['D','A','T','E'] then\n"
            "      return Except.ok (resolveName key.dropLast)\n"
            "    else\n"
            "      return Except.ok (resolveName key)"),
        "refinement": "resolving all but the last code point for exactly one "
                      "name and correctly for every other corresponds to a patch "
                      "that forces the deferred name — so the reported symptom "
                      "looks addressed — and then mis-keys the lookup on a single "
                      "name it special-cases. Every request for THAT name is "
                      "served the value of a different (truncated) name, so the "
                      "assertions that read that one name's value fail while all "
                      "the others pass. A faithful such patch does NOT resolve. "
                      "It is the narrowest wrong impl in this battery: its fault "
                      "domain is a single input, where reject-empty-key and "
                      "reject-drop-last are wrong at almost every input.",
        "rationale": "REJECT from (Q) out = Except.ok (resolveName (force nm)): on "
                     "the guarded branch the rival feeds resolveName the "
                     "truncated content, but (Q) pins the argument to force nm "
                     "there too. Non-subsumed on the WHERE-the-fault-lives axis, "
                     "and distinctly from reject-guarded-selfvalue: that case's "
                     "guard is over the OPAQUE callee's result, which the "
                     "verifier cannot decide either way, so its branch is live "
                     "only because nothing can rule it out. This guard is over "
                     "the INPUT's own resolved content — fully transparent, "
                     "decidable, and taken at exactly one name — so it tests that "
                     "(Q) binds pointwise rather than merely generically: a spec "
                     "that constrained the key only up to some equivalence the "
                     "verifier could discharge symbolically would admit this "
                     "rival. Audit build: rejected exit 1, with the guard live in "
                     "context and the residual on (Q)'s own goal — `if_pos : "
                     "force nm = ['D','A','T','E'] ⊢ Except.ok (resolveName "
                     "(force nm).dropLast) = Except.ok (resolveName (force nm))`. "
                     "Conditioned on the opaque callee via the single weak "
                     "hypothesis `resolveName ['D','A','T'] ≠ resolveName "
                     "['D','A','T','E']`, refuted at nm = Name.deferred "
                     "['D','A','T','E'] — the DEFERRED carrier, so the case also "
                     "adds a second deferred-carrier argument-facet witness. "
                     "Self-satisfiable (distinct opaque arguments need not "
                     "agree): consistency probe exit 1, `h : ¬resolveName "
                     "['D','A','T'] = resolveName ['D','A','T','E'] ⊢ False` "
                     "unsolved. Witness rival exit 0, gold exit 1 (SEMANTIC: gold "
                     "prints `resolveName ['D','A','T','E'] = resolveName "
                     "['D','A','T','E']`, i.e. gold's answer IS the spec's answer "
                     "there); claim-flip gold exit 0 / rival exit 1, so gold's "
                     "exit code tracks the claim; type-reveal prints a CONCRETE "
                     "equation on both sides, never `True`.",
        "witness":
            "example (h : resolveName ['D','A','T'] ≠ resolveName ['D','A','T','E']) :\n"
            "    (lookupValue (Name.deferred ['D','A','T','E'])).run\n"
            "      ≠ DivM.res (Except.ok (resolveName ['D','A','T','E'])) := by\n"
            "  simp only [lookupValue, Name.content, force, NonDetT.run, Pure.pure,\n"
            "    List.dropLast, if_true]\n"
            "  intro heq\n"
            "  exact h (Except.ok.inj (DivM.res.inj heq))\n",
    },

    # ---- (Q) PASS-THROUGH facet: the callee's ANSWER must be handed back
    # ---- unaltered. LANDED BY THE FIFTH AUDIT, and it closes the one real gap
    # ---- that pass found. Every rival above attacks (Q) on the INPUT side of
    # ---- the callee — the constructor it wraps the answer in, or the argument
    # ---- it keys the lookup with — or returns a constant on a guarded branch.
    # ---- None of them applies the callee to the HONEST argument and then
    # ---- corrupts what came back, which is the OUTPUT side and is exactly what
    # ---- the sibling's value-PRESERVATION family is about. The accounting table
    # ---- recorded that whole family as VACUOUS ("no heap"), which was measured
    # ---- and is wrong for this member of it: what is vacuous here is writing
    # ---- through a value ANOTHER holder can observe (there is no such holder on
    # ---- a referentially-transparent carrier), NOT altering the value this
    # ---- request itself serves. See the PRESERVATION FAMILY note.
    {
        "id": "reject-corrupt-served-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Key the lookup HONESTLY (`force nm`, the full resolved content — so
        # every argument-facet witness above AGREES with this rival), then
        # overwrite the first code point of the value that came back before
        # serving it. Constructor stays `ok`, argument stays honest; only the
        # ANSWER is altered.
        "module": _impl(
            "    let key := force nm\n"
            "    let mut served := resolveName key\n"
            "    served := served.set 0 'X'\n"
            "    return Except.ok served"),
        "refinement": "serving an altered copy of the value the downstream "
                      "resolution handed back corresponds to a patch that "
                      "resolves the name correctly — so the reported symptom "
                      "looks addressed, a deferred name IS forced and the lookup "
                      "is keyed on its real characters — and then rewrites a code "
                      "point of the value on the way out. Every request, eager or "
                      "deferred, is served a value that differs from the one the "
                      "lookup holds for that name, so the assertions that read any "
                      "name's actual value fail. A faithful such patch does NOT "
                      "resolve. It is the port of the sibling battery's value-"
                      "PRESERVATION shape onto a carrier with no heap: the sibling "
                      "rival writes into a value the lookup KEEPS and later re-"
                      "serves, which needs a holder this carrier does not have, but "
                      "the observable consequence it is built to catch — the value "
                      "this request serves is not the value the lookup answered "
                      "with — survives the port intact and is what this case pins.",
        "rationale": "REJECT from (Q) out = Except.ok (resolveName (force nm)): the "
                     "rival returns Except.ok of an ALTERED copy of the callee's "
                     "answer. Non-subsumed on a NEW axis — which SIDE of the opaque "
                     "callee the fault sits on. The constructor-facet rivals wrap "
                     "the wrong constructor; the five argument-facet rivals mis-key "
                     "the lookup, so their witnesses all condition on two distinct "
                     "ARGUMENTS disagreeing; reject-guarded-selfvalue and "
                     "reject-guarded-input-content are wrong only on a guarded "
                     "sub-domain. This rival keys the lookup with exactly force nm "
                     "— it AGREES with gold on every argument-facet witness point — "
                     "and is wrong at every input on the OUTPUT side instead. So it "
                     "tests that (Q) pins the callee's answer to be passed through "
                     "unaltered, not merely that the callee is called on the right "
                     "name: a spec that constrained only the lookup KEY would admit "
                     "it. Conditioned on the opaque callee via the single weak "
                     "hypothesis `(resolveName ['H',':','i']).set 0 'X' ≠ "
                     "resolveName ['H',':','i']` — an alteration-vs-original "
                     "disequality, where the argument-facet rivals all relate two "
                     "distinct arguments — refuted at nm = Name.eager "
                     "['H',':','i']. Self-satisfiable (nothing forces an opaque "
                     "function's value at a name to be a fixed point of overwriting "
                     "its first code point): consistency probe exit 1, `⊢ False` "
                     "unsolved. Audit builds: module rejected on (Q)'s own goal "
                     "under the frozen tactic, under the re-proving tactic AND "
                     "under an aggressive `first | rfl | aesop | omega | trivial` "
                     "body (exit 1 x3, residual `⊢ Except.ok ((resolveName (force "
                     "nm)).set 0 'X') = Except.ok (resolveName (force nm))`), so "
                     "the rejection is not an artifact of the frozen script's "
                     "shape. Witness rival exit 0, gold exit 1; claim-flip gold "
                     "exit 0 / rival exit 1, so gold's exit code tracks the claim; "
                     "type-reveal prints a CONCRETE equation on both sides, never "
                     "`True` (gold `DivM.res (Except.ok (resolveName "
                     "['H',':','i'])) = ...` against the rival's `DivM.res "
                     "(Except.ok ((resolveName ['H',':','i']).set 0 'X')) = ...`).",
        "witness":
            "example (h : (resolveName ['H',':','i']).set 0 'X'\n"
            "    ≠ resolveName ['H',':','i']) :\n"
            "    (lookupValue (Name.eager ['H',':','i'])).run\n"
            "      ≠ DivM.res (Except.ok (resolveName ['H',':','i'])) := by\n"
            "  simp only [lookupValue, Name.content, force, NonDetT.run, Pure.pure]\n"
            "  intro heq\n"
            "  exact h (Except.ok.inj (DivM.res.inj heq))\n",
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 12 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation, 7 uniqueness rivals) plus a
# 3-case AXIOM lane. An earlier revision of this line said "9 SPEC cases (… 4
# uniqueness rivals)" and the mapping table below listed only 9, which is a
# MISCOUNT the third audit corrected against the sibling file: nagini declares
# 12 SPEC ids, and the three the table never named — preserve-poison-store,
# preserve-poison-accum, alias-dead-branch — are exactly the value-PRESERVATION
# family. The third audit ported one of them (alias-dead-branch, as
# reject-guarded-selfvalue) and recorded the other two as vacuous for the same
# heap reason as the frame-mutation pair. The FIFTH audit found that HALF wrong
# and split it: what is vacuous is the sibling's MECHANISM (writing through a
# value another holder observes), not its SUBSTANCE (the value this request
# serves differs from the one the callee answered with), and the substance is
# expressible here on a facet of (Q) no other rival touches. So
# preserve-poison-store now ships as reject-corrupt-served-value, and only
# preserve-poison-accum remains vacuous — demonstrated by build, not asserted,
# in the PRESERVATION FAMILY note. This bundle carries 15 (5 soundness, 1
# admissibility, 9 uniqueness) — the eighth rival,
# reject-guarded-input-content, is not a port of any sibling case: it was added
# by the FOURTH audit to cover a shape the sibling battery has no analogue for
# (a fault guarded on a transparent predicate over the input's own resolved
# content, wrong at exactly one name). Recorded as ADDED rather than PORTED in
# the table below, so the nagini mapping stays a mapping. The two added by the
# second audit are
# pos-match-carrier and pos-branch-both-arms-content, the only positives here that are not
# definitionally the frozen impl. This bundle models a NARROWER surface: nagini contracts the
# imperative resolve-then-lookup loop (`lookup_format` over a `FormatType` with a
# `.content` list held at fractional permission, plus @ContractOnly `resolve` /
# `format_value` / `do_lookup`), whereas velvet models the single
# purely-functional core `lookupValue`: force the name, then apply the opaque
# `resolveName` to the forced content. The whole imperative copy loop collapses
# into `force nm` (a total projection) and the postcondition's
# `format_value(resolve(...))` becomes the single clause `out = Except.ok
# (resolveName (force nm))`. Every sibling case is accounted for below.
#
#   sibling case (nagini)         -> here
#   -----------------------------------------------------------------------
#   pos-control-localbound        -> pos-inline-force / pos-let-value   PORTED (arg.)
#                                    + pos-match-carrier                PORTED (audit 2)
#                                    + pos-branch-both-arms-content     PORTED (audit 2)
#   pos-control-extra-assert      -> pos-framing-have                   PORTED (audit)
#   admiss-f2p-shaped-input       -> admiss-f2p-shaped-input           PORTED (audit)
#   frame-mut-append              -> (none)                             VACUOUS (no heap)
#   frame-mut-store               -> (none)                             VACUOUS (no heap)
#   uniq-empty-key                -> reject-empty-key                   PORTED (arg. cond.)
#   uniq-deferred-skip            -> reject-deferred-empty-key          PORTED (arg. cond.)
#                                    + reject-deferred-error            PORTED (ctor)
#   uniq-drop-last                -> reject-drop-last                   PORTED (arg. cond.)
#   uniq-skip-first               -> reject-skip-first                  PORTED (arg. cond.)
#   preserve-poison-store         -> reject-corrupt-served-value        PORTED (audit 5)
#   preserve-poison-accum         -> (none)                             VACUOUS (no heap)
#   alias-dead-branch             -> reject-guarded-selfvalue           PORTED (audit 3)
#   (no sibling analogue)         -> reject-guarded-input-content       ADDED  (audit 4)
#   AXIOM_TESTS (x3)              -> (none)                             DROPPED (G-AX)
#
# THE PRESERVATION FAMILY (three sibling cases the table did not name until the
#   third audit). All three are about what happens to the VALUE the downstream
#   resolution hands back, and on this carrier they split two-EXPRESSIBLE to
#   one-vacuous. The third audit split them two-vacuous to one; the FIFTH audit
#   corrected that, because it had conflated the sibling's MECHANISM with its
#   SUBSTANCE. Recorded in full, since the correction is the substantive one this
#   file has taken on this lane:
#   * preserve-poison-store: EXPRESSIBLE, and it was the one real gap the fifth
#     audit found. The MECHANISM does not port — the sibling serves the right
#     value and then WRITES into the value the lookup retains, which needs full
#     `list_pred` permission the requester only holds at `Wildcard`, and this
#     carrier has no heap, no permissions and no second holder. Measured: an
#     impl-region `val := ['X']` after `let val := resolveName key` is refused
#     with "`val` cannot be mutated, only variables declared using `let mut` can
#     be mutated" (exit 1). But the OBSERVABLE the sibling case is built to catch
#     — the value served for a name is not the value the lookup answered with —
#     survives the port exactly, and it lands on the PASS-THROUGH facet of (Q)
#     (see the CARRIER note), which is the OUTPUT side of the opaque callee and
#     which no other rival in this battery touches: the argument-facet five all
#     mis-key the lookup and therefore AGREE with gold on the output side. So it
#     ships as reject-corrupt-served-value (`let mut served := resolveName key;
#     served := served.set 0 'X'`), rejected on (Q)'s own goal under the frozen,
#     re-proving AND aggressive tactics. An earlier revision of this note used
#     the `let mut` rewrite to argue the case AWAY ("it mutates a LOCAL COPY,
#     which no later requester can observe, so it degenerates into an ordinary
#     wrong-value rival already covered by the argument-facet lane"). Both halves
#     were wrong: the local copy is the value THIS request returns, so (Q)
#     observes it even though no later requester does; and it is not covered by
#     the argument-facet lane, whose rivals are all wrong on the callee's INPUT.
#   * preserve-poison-accum: VACUOUS, and demonstrated by build rather than
#     argued. Its fault is specifically the aliasing ACCUMULATION of a read
#     permission across two lookups of the same name, and that shape is refused
#     by the carrier: `let a := resolveName key; let b := resolveName key;
#     a := b.set 0 'X'` fails with "`a` cannot be mutated, only variables
#     declared using `let mut` can be mutated" (exit 1). Re-declaring `a` as
#     `let mut` does not reconstruct THIS case — it erases the aliasing, leaving
#     a single-lookup corruption, which is exactly reject-corrupt-served-value
#     and is already carried. The distinction this sibling case turns on — an
#     unaccumulable read permission on a value the callee KEEPS — has no referent
#     on a referentially-transparent carrier where `resolveName key` is a value,
#     not an object anyone else holds.
#   * alias-dead-branch: EXPRESSIBLE, and it was the one real gap. The sibling
#     case is NOT a permission rejection: it is rejected by the POSTCONDITION, on
#     a branch guarded by `served is name` that the verifier cannot prove dead
#     (which is the whole point of the sibling's Wildcard-on-both-sides
#     modelling). That structure ports directly, because the analogue of "the
#     value served for this name IS this name" is `resolveName key = key`, a guard
#     over the OPAQUE callee's own result — so the verifier cannot prove the
#     branch dead here either, and must discharge (Q) on it. It ships as
#     reject-guarded-selfvalue. Recording it as covered would have been wrong on
#     the substance as well as the count: every other rival in this battery is
#     wrong UNCONDITIONALLY on a carrier arm the control flow always reaches, so
#     none of them tested whether (Q) still binds on a guarded sub-domain.
#
# PORTED (5 positives): the two nagini positives are loop reshapes (bind the loop
#   bound to a local; add a redundant framing assert). On this carrier the copy
#   loop does not exist — it is the single total projection `force nm` — so those
#   exact reshapes have no counterpart. The ARGUMENT ("a faithful
#   structurally-different correct impl must verify") is carried by the two
#   reshapes native to this carrier: pos-inline-force (drop the intermediate
#   `let key`) and pos-let-value (bind the resolved value to an intermediate
#   local). An earlier revision recorded the redundant-assert positive as FOLDED
#   into those two; audit found that understated the battery, since both reshapes
#   perturb the RETURN form and neither ADDS an obligation the way the sibling's
#   framing assert does. It ports directly as pos-framing-have (`have hframe :
#   force nm = nm.content := rfl` ahead of the verbatim frozen body); note that
#   velvet's `assert` command does not accept an unnamed proposition here
#   (`Failed to parse an assertion without names`), so the framing fact is stated
#   as a proof-carrying `have`, which is the stronger form anyway.
# ON THE DEFERRED-SKIP PORT (corrected by audit): the sibling's uniq-deferred-skip
#   leaves the name buffer EMPTY on the deferred branch and feeds that empty key
#   downstream — an ARGUMENT-facet fault that still returns a value. An earlier
#   revision mapped it onto reject-deferred-error alone, which converts it into a
#   CONSTRUCTOR-facet fault (return `error`) and thereby left the argument facet
#   untested at the deferred carrier — the one carrier the desired behaviour is
#   actually about, since all three argument-facet witnesses sit at `Name.eager`,
#   where an eager-correct/deferred-wrong rival agrees with gold. Both shapes are
#   now carried: reject-deferred-empty-key (the faithful argument-facet port) and
#   reject-deferred-error (the pre-patch constructor-facet shape).
# PORTED (admissibility, LANDED BY AUDIT): the sibling injects an F2P-shaped
#   FormatType witness and asserts it satisfies the fractional-permission
#   Requires. An earlier revision of this file dropped the lane as VACUOUS on the
#   reasoning "no `require` clause, so nothing to admit", with the residual
#   total-domain risk waved off as covered by the frozen proof verifying. That
#   reasoning is INADMISSIBLE and was corrected by audit. "The frozen obligation
#   has no precondition" is not a vacuity argument: the analogue on a total
#   carrier is the obligation being unsatisfiable at exactly an F2P-shaped INPUT,
#   which the frozen proof verifying does not address — that proof discharges (Q)
#   universally without ever exhibiting the post-image at the concrete input the
#   behaviour is about, so it cannot distinguish a spec that is satisfiable there
#   from one that is not. Dropping the lane removed one of the three directions
#   this gate exists to test (it is the ONLY detector of PRECOND-TOO-STRONG), and
#   the coverage reporter flagged exactly that. It ships as
#   admiss-f2p-shaped-input, which discharges the post-image's three
#   admissibility facts at nm = Name.deferred ['D','A','T','E'] BY EVALUATION as a
#   `have` before closing the frozen obligation verbatim. Load-bearing in both
#   directions, re-measured independently by audit with real builds: the case
#   verifies (exit 0); its clause (ii) with the eager name swapped to ['X'] fails
#   (exit 1, `case refine_2 ⊢ resolveName ['D','A','T','E'] = resolveName ['X']`),
#   so the carrier-identification clause is not provable for an arbitrary pair of
#   names; and clause (iii) flipped to CLAIM the error outcome fails (exit 1,
#   `case refine_3 ⊢ False`), so the non-degeneracy clause is not free either.
# VACUOUS (frame-mutation x2): the sibling carries these MANDATORY because
#   requested_name.content is held at `Acc(list_pred(...),1/2)` (read-only) an
#   impl could illegally append to / index-store into. This backend is
#   referentially transparent and declares no `mut` binder — the single input
#   `nm` is an immutable value with no heap footprint — so there is no read-only
#   field to overwrite and no substitute probe. Not fabricated.
# DIVERGENCE (no case; CLOSED BY THE SEMANTICS, neither vacuity nor a spec hole):
#   the nagini sibling ships no diverge-*/nonterm-*/weak-diverge case for this
#   instance, so there is nothing to PORT. Two earlier reasons are retracted.
#   The first called the class vacuous because the impl region "admits no
#   non-terminating rival to express"; that is false, since a rival owns the whole
#   impl region and can splice a loop of its own. The second said that under this
#   bundle's `set_option loom.semantics.termination "total"` a spliced
#   `while True do pure ()` prefix VERIFIES, and recorded a corpus-wide spec hole
#   (401 of 500 velvet bundles, "this instance among them: mode=partial,
#   outcome=VERIFIES") closeable only by flipping the option to "total". That is the
#   `partial` rule stated against a `total` file, and the census has no referent:
#   all 500 velvet bundles read "total", including this one, so there is nothing to
#   flip. Under "total" a postcondition is claimed of ALL runs and every loop must
#   carry a decreasing measure. Re-measured here: the unmeasured spun prefix is
#   REJECTED at elaboration (`Decreasing annotations are required in total
#   correctness semantics`), and a loop carrying a NON-decreasing measure
#   (`while q > 0 ... decreasing q`, body `q := q`) is rejected on the measure's own
#   goal -- `case «decreasing_1: q»`, residual `q < q`.
#   The DISPOSITION is still "no case here", now for a WITNESS reason — with the
#   reason narrowed by the third audit, which measured it per shape instead of
#   asserting it for both. For the UNMEASURED shape the original reason holds and
#   was re-confirmed: the witness file fails at the loop itself, ahead of any
#   tester (exit 1, `Decreasing annotations are required ...`), so no witness can
#   elaborate against it. For the MEASURED-non-decreasing shape it is false —
#   `witness_file` strips `prove_correct`, which is where that rival's only error
#   lives, so its module compiles with a witness appended (trivial witness, exit
#   0). That shape ships no case for a stronger reason: it is value-CORRECT
#   (`q := q`, honest return), so no input violates (Q) and there is no true
#   refutation to state. A rejection owed solely to a termination measure is not
#   attributable to (Q), which is what this lane's witnesses must attribute to.
#   Nothing is re-reported as a finding because there is no finding.
# PORTED (6 rivals): uniq-deferred-skip ports as BOTH reject-deferred-empty-key
#   (the faithful argument-facet shape: the deferred branch silently resolves the
#   empty key, refuted by conditioning at nm = Name.deferred ['D','A','T','E'])
#   and reject-deferred-error (fail the deferred branch outright, refuted on the
#   transparent CONSTRUCTOR facet of (Q), Except.error ≠ Except.ok) — plus
#   reject-always-error as a non-subsumed near-miss (fails on eager too).
#   uniq-empty-key / uniq-drop-last / uniq-skip-first port as reject-empty-key /
#   reject-drop-last / reject-skip-first, each feeding resolveName a wrong
#   resolved content and refuted on the ARGUMENT facet by CONDITIONING on the
#   opaque resolveName. Each carries a machine-checked witness that ELABORATES
#   against the rival and FAILS against the frozen solution (two real builds per
#   case), and every gold-side failure was read by audit to confirm it is a
#   SEMANTIC refusal — the goal reduces to `resolveName <full> = resolveName
#   <full>` / `Except.ok = Except.ok`, i.e. gold satisfies the very claim the
#   rival violates — rather than an unknown identifier, a type error or a stuck
#   reduction.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   resolved-name-function property against the real get_format) and this gate
#   ignores AXIOM_TESTS regardless.
#
# COVERAGE. All THREE kind lanes are now present, so all three directions this
# gate exists to test are reachable: soundness (SPEC-TOO-STRONG),
# admissibility (PRECOND-TOO-STRONG), uniqueness (SPEC-TOO-WEAK). Present is not
# the same as LOAD-BEARING, and for the soundness lane the two are worth keeping
# apart: of its five cases, three (pos-inline-force, pos-let-value,
# pos-framing-have) are definitionally the frozen impl and so cannot fail for a
# spec reason, while two (pos-match-carrier, pos-branch-both-arms-content) are
# not and can. The sole
# obligation (`prove_correct lookupValue`) is defended
# (pos-inline-force, pos-let-value, pos-framing-have, pos-match-carrier,
# pos-branch-both-arms-content), probed for satisfiability
# at an F2P-shaped input (admiss-f2p-shaped-input) and attacked (NINE reject
# rivals). The single postcondition clause (Q) is attacked on ALL THREE transparent
# facets — the result CONSTRUCTOR (reject-deferred-error, reject-always-error),
# the callee ARGUMENT (reject-empty-key, reject-drop-last, reject-skip-first,
# reject-deferred-empty-key, reject-guarded-input-content) and, since the fifth
# audit, the callee's ANSWER PASS-THROUGH (reject-corrupt-served-value, the only
# rival that is wrong on the OUTPUT side of the opaque callee while agreeing with
# gold on the lookup key) — and the ARGUMENT
# facet is now attacked at BOTH
# carriers, eager and deferred, which is what makes the battery attest that the
# spec depends on the deferred carrier's content and not merely on its tag.
# WHERE the fault lives is a third axis, added by the third audit: SEVEN of the
# rivals named above (all but the guarded pair named next) are each wrong
# UNCONDITIONALLY on a branch the rival's own control flow always reaches, so
# every one of their witnesses sits at an unguarded point — six of them faulting
# on the callee's input side, reject-corrupt-served-value on its output side.
# TWO rivals' faults live on a GUARDED sub-domain, and the fourth audit
# split that axis in two because the two guards are decidable in opposite ways.
# reject-guarded-selfvalue guards on `resolveName key = key`, a condition over
# the OPAQUE callee's own result that the verifier cannot decide either way, so
# its branch is live only because nothing can rule it out; it attests that (Q)
# binds on a branch that is merely reachable rather than always taken, and it
# inverts the hypothesis direction (the conditioned witnesses above all assume a
# DISEQUALITY over the opaque term, this one an EQUALITY, so the consistency
# probe is exercised both ways). reject-guarded-input-content guards on
# `force nm = ['D','A','T','E']`, a TRANSPARENT predicate over the input's own
# resolved content: the verifier can decide which branch any given name takes,
# the fault domain is a single input, and (Q) must still discharge there. That is
# the pointwise direction — a spec constraining the key only up to some
# equivalence a tactic could discharge symbolically would admit it — and no
# other case in this battery reaches it. The sole input binder `nm` is varied
# across the reject witnesses: both carriers (Name.deferred ['A'],
# Name.deferred ['D','A','T','E'] x2; Name.eager ['H',':','i'] and ['A']) and
# multiple content values.
#
# AUDIT PROBES that found NO hole (recorded so the next reader need not redo
# them; all were built with the real verifier). SPEC-TOO-WEAK direction — six new
# wrong impls beyond those shipped above, each REJECTED (exit 1): resolve the
# reversed content; resolve the content concatenated with itself; return a literal
# `Except.ok []` ignoring the name entirely; invert the branches (fail on the
# already-resolved name, succeed on the deferred one); truncate only on the
# deferred branch; and resolve the empty key only on the deferred branch (this
# last one was good enough to keep, and ships as reject-deferred-empty-key).
# SPEC-TOO-STRONG direction — two new correct reshapes, both PROVABLE and so no
# soundness hole: `match nm with | .eager s => ... | .deferred s => ...` (closes
# with `loom_solve <;> simp_all [force, Name.content]`) and returning
# `Except.ok (resolveName nm.content)` directly, bypassing `force` (closes with
# `loom_solve <;> simp [force, Name.content]`). Both fail under the FROZEN
# `loom_solve` body alone, which is tactic-shape brittleness rather than a spec
# defect — worth knowing, since it is exactly the confound the witness
# requirement exists to neutralise.
#   CORRECTED BY THE SECOND AUDIT: recording those two reshapes here, as prose,
#   while shipping NEITHER as a case was itself the defect. They were the only
#   probes on this bundle that a genuinely non-frozen-shaped correct impl could
#   fail, and leaving them in a comment meant the gate never ran them — so the
#   soundness lane that DID ship consisted of four cases every one of which is
#   definitionally the frozen impl (`rfl` probe, exit 0 on all four and on gold).
#   The first, `match`, now ships as pos-match-carrier; a tag-split variant of the
#   second ships as pos-branch-both-arms-content. The bare
#   `Except.ok (resolveName nm.content)` form is deliberately NOT shipped as a
#   third: measured, it IS definitionally the frozen impl (`rfl` probe exit 0,
#   since `force` unfolds to `Name.content` with no case split), so as a case it
#   would have added another identity rather than another test.
#
# INDEPENDENT AUDIT, second pass (all figures below are `scripts/lean_verify.sh`
# exit codes from real builds re-run out-of-band, not a self-report):
#   * STATEMENT INTEGRITY. For all cases, the whole file MINUS the impl region and
#     minus the `prove_correct` tactic body hashes IDENTICALLY to the frozen
#     file's, so the `method lookupValue … ensures out = Except.ok (resolveName
#     (force nm))` header and the `prove_correct lookupValue` header are
#     byte-identical everywhere. No case reformats a statement. Re-derived by the
#     second audit at a FINER grain than a whole-file hash, which is the check that
#     actually binds: a line-level diff of each case against the frozen file shows
#     every changed line falling inside the impl span (frozen lines 76-82) — so the
#     `axiom resolveName` declaration, the `Name` carrier, `Name.content`, `force`,
#     and the `ensures` clause are untouched by every case, which an elided-region
#     hash cannot certify (it elides `axioms`/`pure` too, where a weakened `force`
#     would hide). An earlier revision quoted a specific digest, `6f4a750612a392d1…`,
#     for this claim; that digest does not reproduce under any strip convention
#     tried (impl-region dropped, with/without markers, with/without the
#     `prove_correct` body, with/without trailing newline: the values are
#     bc038a670805ca0e / c919098e7882ebad / 53672022ee1f2906 / 691461a2b30b772a /
#     …), so it was an unverifiable decoration on a claim that is TRUE and is now
#     stated in a reproducible form instead. The conclusion is unchanged; only the
#     evidence for it is now checkable.
#   * ALL SIX reject witnesses rebuilt twice: rival exit 0, gold exit 1, in every
#     case. The four CONDITIONED witnesses' consistency probes all fail (exit 1),
#     i.e. no `False` follows from their hypotheses, so each refuting input exists.
#   * FORGERY TEST (mandatory here — no gold_signature is a plain evaluation; both
#     signature classes checked). Flipping ONLY the claim (`≠` -> `=`) makes gold's
#     exit code MOVE, in all six cases: the flipped claim BUILDS against the frozen
#     solution (exit 0) and FAILS against every rival (exit 1) — the exact mirror of
#     the shipped witnesses. So gold's exit code tracks the claim and carries real
#     information; none of these cases is hollow.
#   * TYPE-REVEAL, on both signature classes, replacing the closing step with a
#     deliberate type error to print the hypothesis's REAL type. It is a CONCRETE
#     equation on both sides, never `True` — gold prints `resolveName (force
#     (Name.eager ['A'])) = resolveName ['A']` where the rival prints `resolveName
#     [] = resolveName ['A']`, and on the constructor facet gold prints
#     `Except.ok … = Except.ok …` where the rival prints `Except.error
#     LookupErr.unresolvedName = Except.ok …`. So `simp` did NOT prove the
#     equation away; the gold-side failure is the semantic fact that gold's answer
#     IS the spec's answer at that input.
#   * NO RIVAL IS VACUOUS. Each of the six differs from the frozen impl observably
#     at its own witness point, which the reveal probe above prints as two
#     syntactically distinct arguments to the opaque callee (or two distinct
#     constructors). No `Nat`-truncation / `Option`-collapse / coercion trap
#     applies: the carrier is `List Char` under an opaque function, where distinct
#     arguments are never definitionally equal.
#   * SPEC-TOO-WEAK, eight FURTHER new wrong impls beyond the six shipped and the
#     six already recorded above — all REJECTED (exit 1): key chosen by the TAG
#     alone, ignoring content; reverse the content on the deferred branch only;
#     error on the EAGER branch only (the mirror of the pre-patch shape); `take 1`
#     of the content; apply the opaque callee TWICE; truncate only when the content
#     exceeds two code points; echo the forced content as the value, bypassing the
#     callee; and return a literal `Except.ok []`. No spec hole found.
#   * SPEC-TOO-STRONG, five FURTHER new correct reshapes — all PROVABLE (exit 0):
#     `match` on the carrier; an `if` on the tag whose BOTH branches force
#     correctly; the content projection directly; re-wrapping the forced content in
#     an eager name before forcing again; and `(force nm) ++ []`. No soundness hole.
#   * DEMONIC-CHOICE axis (new attack, no earlier pass probed it). This bundle
#     sets `loom.semantics.choice "demonic"`, so a rival may pick its lookup key
#     NONDETERMINISTICALLY and every branch must satisfy (Q). Two such rivals were
#     built — pick a `Bool` under `let b :| (b = true ∨ b = false)` and under
#     `let b :| True`, then key off it (honest content on one branch, empty on the
#     other). BOTH are REJECTED (exit 1) and the residual goal names the
#     nondeterministic binder explicitly: `i : Bool ⊢ Except.ok (resolveName (if i
#     = true then force nm else [])) = Except.ok (resolveName (force nm))`. So the
#     spec is not weakened by demonic choice: it constrains the key on EVERY
#     branch, not merely on some reachable one. No hole; recorded because the
#     nondeterminism knob is otherwise unattacked by the whole battery.
#     TOOLING NOTE (a real bug, reported not worked around): stating the same
#     rival over the KEY directly — `let key :| (key = force nm ∨ key = [])`, the
#     natural phrasing — does not compile, and not for a spec reason: `failed to
#     synthesize Findable fun key => typeWithName (key = force nm ∨ key = []) …`,
#     because `List Char` has no `Encodable`/`FinEnum` instance for the pick to
#     enumerate, followed by a cascading `Failed to parse an assertion without
#     names: WPGen sorry`. Nondeterministic picks on this carrier are therefore
#     expressible only over a finitely-enumerable type (hence the `Bool` detour
#     above); the `List Char` phrasing is blocked by the instance search, not by
#     the spec.
#   * The docstring's TOOLING claim was re-measured, not taken on trust:
#     `extract_program_for lookupValue` really does fail with `depends on
#     declaration 'lookupValue', which has no executable code` (exit 1), so the
#     `<name>Exec` route is genuinely unavailable and the `.run` route the
#     witnesses use is the right one.
#
# INDEPENDENT AUDIT, third pass (78 real `scripts/lean_verify.sh` builds; every
# exit code below was observed, none carried over from the record above).
#   * STATEMENT INTEGRITY (attack A) re-derived at line grain with a
#     SequenceMatcher diff of every case against the frozen file. All changed
#     spans fall inside the impl region (frozen lines 76-82) or on the
#     `prove_correct` tactic line (86): pos-inline-force/pos-let-value/the six
#     original rivals touch only 80-81, admiss-f2p-shaped-input and
#     pos-framing-have INSERT at 80, and pos-match-carrier /
#     pos-branch-both-arms-content touch 80-81 plus line 86. So the `axiom
#     resolveName` declaration, the `Name` carrier, `Name.content`, `force` and
#     the `ensures` clause are byte-identical in all 13 cases. No case reformats
#     a statement.
#   * WITNESS DISCRIMINATION (attack B) re-run for all six pre-existing rivals
#     through the gate's OWN `witness_file` construction: rival exit 0, gold exit
#     1, six for six. The four conditioned witnesses' consistency probes fail
#     (exit 1), so no `False` follows from their hypotheses.
#   * FORGERY (attack B′) — no gold_signature here is a plain evaluation, so this
#     was mandatory, and BOTH halves were run for all six. Claim-flip (`≠` -> `=`,
#     with `force` supplied to simp): gold exit 0, rival exit 1, six for six — so
#     gold's exit code MOVES with the claim and carries information about it.
#     Type-reveal (closing step replaced by `exact (h : Nat)` / `exact (heq :
#     Nat)`) prints a CONCRETE equation on BOTH sides in all six, never `has type
#     True`, so `simp` did not prove the equation away. The pairs are decisive:
#     gold prints `... (resolveName ['H',':','i']) = ... (resolveName ['H',':','i'])`
#     where reject-drop-last prints `... (resolveName ['H',':']) = ...`, and on the
#     constructor facet gold prints `... (Except.ok (resolveName (force (Name.deferred
#     ['A'])))) = ...` where reject-deferred-error prints `... (Except.error
#     LookupErr.unresolvedName) = ...`. Gold's failure is the semantic fact that
#     gold's answer IS the spec's answer at the witness point.
#   * DEFEQ re-measurement (attack C, hollow-positive direction). The `rfl` probe
#     was re-run on all six positives and on gold: exit 0 for gold,
#     pos-inline-force, pos-let-value, pos-framing-have and
#     admiss-f2p-shaped-input; exit 1 for pos-match-carrier and
#     pos-branch-both-arms-content (`Tactic `rfl` failed: The left-hand side
#     NonDetT.run (lookupValue nm) is not definitionally equal to ...`). The
#     second audit's reclassification is CONFIRMED, in both directions.
#   * NO RIVAL IS VACUOUS. The type-reveal above prints, per rival, an argument or
#     constructor syntactically distinct from gold's at the witness point.
#   * SPEC-TOO-WEAK (attack D), four NEW wrong impls beyond every one recorded
#     above — all REJECTED (exit 1), each on the postcondition's own goal, so no
#     hole: upper-casing the resolved content (`⊢ Except.ok (resolveName
#     (List.map Char.toUpper (force nm))) = Except.ok (resolveName (force nm))`, a
#     near-miss that AGREES with gold on the already-upper-case F2P-shaped name);
#     a key built from the content's LENGTH alone (`List.replicate (force
#     nm).length 'x'`); a hard-coded constant key (`resolveName ['D','A','T','E']`,
#     correct at exactly one input); and a LOOP-BEARING wrong impl (a measured,
#     properly-decreasing `while` prefix ahead of a `dropLast` key), which is
#     rejected with the loop's own hypotheses in context and the residual `⊢
#     Except.ok (resolveName (force nm).dropLast) = Except.ok (resolveName (force
#     nm))`. That last one also probes the loop axis the whole battery otherwise
#     leaves alone; note its WITNESS cannot be landed (see the TOOLING note below).
#   * SPEC-TOO-STRONG (attack E), three NEW correct reshapes — all PROVABLE, so no
#     soundness hole: `let mut key := force nm; key := force nm` (exit 0 under the
#     FROZEN tactic, and defeq to gold, rfl probe exit 0); `[] ++ force nm` (exit 0
#     frozen, defeq); and a LOOP-BEARING correct impl (measured decreasing `while`
#     prefix, honest return) which verifies under the frozen tactic (exit 0) and is
#     NOT defeq to gold (rfl probe exit 1). The last is the more interesting datum:
#     the spec accepts a correct impl whose term does not normalise to gold's.
#   * OMISSION RE-DERIVATION (attack F) found the pass's one real defect: the
#     accounting table listed 9 of the sibling's 12 SPEC cases and silently omitted
#     the three-case PRESERVATION family. Re-derived per case with builds — two are
#     vacuous (the carrier refuses the write: "`val` cannot be mutated, only
#     variables declared using `let mut` can be mutated"), one was EXPRESSIBLE and
#     is now landed as reject-guarded-selfvalue. Full reasoning in the
#     PRESERVATION FAMILY note. reject-guarded-selfvalue's own evidence: rival exit
#     0, gold exit 1 (a SEMANTIC refutation — `heq : DivM.res (Except.ok
#     ['H',':','i']) = DivM.res (Except.ok ['H',':','i']) ⊢ False`, i.e. gold's
#     answer satisfies the claim), consistency probe exit 1, claim-flip gold exit 0
#     / rival exit 1, and a type-reveal printing `DivM.res (Except.ok
#     ['H',':','i']) = ...` on gold against `DivM.res (Except.ok []) = ...` on the
#     rival. Rejected as a module at exit 1 with the guard live in context.
#   * DIVERGENCE (attack F′) re-measured per shape against this bundle's `"total"`
#     setting, which corrected an over-broad reason in two places; see the
#     DIVERGENCE bullet in the module docstring and the DIVERGENCE note below.
#     Also re-confirmed corpus-wide: 500 of 500 velvet bundles set `"total"` and 0
#     set `"partial"`, so the retracted `mode=partial` census indeed has no
#     referent.
#   * TOOLING NOTE (a real limitation, reported not worked around). A witness
#     against ANY loop-bearing rival cannot discriminate on this carrier: built
#     against the loop-bearing `dropLast` rival above, the standard witness shape
#     fails with `Application type mismatch: The argument heq has type (NonDetT.run
#     do let _ ← forIn Lean.Loop.mk 1 fun x r => ...)`, i.e. the unnormalised loop
#     term — which is exactly the gate's own `loop-unification` stuck class
#     (`_STUCK_UNIFICATION_TERM = "forIn Lean.Loop.mk"`). So a loop-bearing rival
#     here would be recorded `witness-undecided`, correctly, rather than as a
#     rejection. That is why the loop axis is probed as an out-of-band module build
#     (rejected on the postcondition goal, quoted above) and ships no case: the
#     rejection is real but no witness can attribute it.
#
# INDEPENDENT AUDIT, fourth pass (117 real `scripts/lean_verify.sh` builds; every
# exit code below was observed in this pass, none carried over from the records
# above, and the gate was re-run at the end).
#   * STATEMENT INTEGRITY (attack A) re-derived with a SequenceMatcher line diff
#     of every case against the frozen file, and every case additionally re-run
#     through `variant_scope.variant_problems` (all "ok"). Changed spans: the six
#     original rivals + pos-inline-force + pos-let-value touch only frozen lines
#     80-81; admiss-f2p-shaped-input and pos-framing-have INSERT at 80;
#     pos-match-carrier / pos-branch-both-arms-content touch 80-81 plus the
#     tactic line 86; reject-guarded-selfvalue touches 81. So the `axiom
#     resolveName` declaration, the `Name` carrier, `Name.content`, `force` and
#     the `ensures` clause are byte-identical in every case. No statement is
#     reformatted, restated or weakened anywhere.
#   * WITNESS DISCRIMINATION (attack B), all SEVEN pre-existing rivals rebuilt
#     through the gate's own `witness_file`: rival exit 0, gold exit 1, seven for
#     seven. Consistency probes (the five conditioned witnesses) all exit 1 —
#     `⊢ False` unsolved from the hypothesis alone on four, `simp_all made no
#     progress` on reject-guarded-selfvalue — so every refuting input exists.
#   * FORGERY (attack B′), mandatory here since no gold_signature is a plain
#     evaluation, and BOTH halves run for all seven. Claim-flip (`≠`->`=`): gold
#     exit 0, rival exit 1, seven for seven, so gold's exit code MOVES with the
#     claim and therefore carried information about it. Type-reveal (`exact (h :
#     Nat)` / `exact (heq : Nat)`) prints a CONCRETE equation on BOTH sides in all
#     seven and `has type True` in NONE, so `simp` never proved the equation away.
#     The pairs are decisive per facet: on the argument facet gold prints
#     `resolveName ['H',':','i'] = resolveName ['H',':','i']` where
#     reject-drop-last prints `resolveName ['H',':'] = ...`; on the constructor
#     facet gold prints `Except.ok (resolveName (force (Name.deferred ['A'])))
#     = ...` where reject-deferred-error prints `Except.error
#     LookupErr.unresolvedName = ...`; on the guarded facet gold prints
#     `Except.ok ['H',':','i'] = ...` where reject-guarded-selfvalue prints
#     `Except.ok [] = ...`. Gold's failure is in every case the semantic fact
#     that gold's answer IS the spec's answer at the witness point.
#   * NO RIVAL IS VACUOUS (attack C), and checked twice over. Each rival's module
#     was rebuilt and its residual read: all seven fail on (Q)'s OWN goal
#     (`case «ensures_1: out = Except.ok (resolveName (force nm))»`) with the
#     wrong argument or constructor printed in the goal, never on a tactic
#     mismatch. Each was ALSO rebuilt under the battery's stronger re-proving
#     tactic (`loom_solve <;> simp_all [force, Name.content]`) — still rejected,
#     seven for seven — so no rejection here is an artifact of the frozen script's
#     shape, which is the confound this whole lane exists to rule out.
#   * DEFEQ re-measurement (hollow-positive direction): the `rfl` probe exits 0 on
#     gold, pos-inline-force, pos-let-value, pos-framing-have and
#     admiss-f2p-shaped-input, and exits 1 on pos-match-carrier and
#     pos-branch-both-arms-content (`Tactic `rfl` failed: ... NonDetT.run
#     (lookupValue nm) is not definitionally equal to ...`). The battery's own
#     classification of which positives are load-bearing is CONFIRMED in both
#     directions, and the docstring's honesty about the three identity positives
#     is accurate rather than generous.
#   * ADMISSIBILITY re-measured as load-bearing in both directions: the case
#     verifies (exit 0), its clause (ii) with the eager name swapped to ['X']
#     fails (exit 1, `case refine_2 ⊢ resolveName ['D','A','T','E'] = resolveName
#     ['X']`), and clause (iii) flipped to CLAIM the error outcome fails (exit 1,
#     `case refine_3 ⊢ False`). So neither the carrier-identification clause nor
#     the non-degeneracy clause is free, and the recorded negative controls
#     reproduce exactly as written.
#   * SPEC-TOO-WEAK (attack D), THIRTEEN new wrong impls beyond every one recorded
#     above — all REJECTED (exit 1), each on (Q)'s own goal, so no spec hole:
#     wrong at exactly the F2P-shaped input (this one was good enough to keep, and
#     ships as reject-guarded-input-content); honest only on length-4 keys;
#     filter one code point out of the key; extend the key with an extra code
#     point; apply the callee twice; echo the forced content, bypassing the callee;
#     a literal `Except.ok []`; key chosen by the carrier TAG alone; wrong on the
#     EAGER arm only; ERROR on a branch guarded by the opaque callee's result;
#     substitute a different key at empty content; reverse the content on the
#     eager arm only; and a demonic pick over a Bool keying honest-vs-truncated
#     (rejected with the nondeterministic binder in context: `i : Bool ⊢ Except.ok
#     (resolveName (if i = true then force nm else [])) ...`), which confirms (Q)
#     constrains EVERY branch and not merely some reachable one. Four rivals were
#     additionally re-run under an AGGRESSIVE tactic body (`loom_solve <;>
#     simp_all [...] <;> first | rfl | aesop | omega | trivial`) to check the
#     in-scope tactic freedom cannot be turned into a hole: all four still
#     rejected. An infeasible demonic pick (`bb :| (bb = true ∧ bb = false)`)
#     guarding a wrong return is also rejected, under both the frozen and the
#     aggressive script — so the vacuous-guard evasion does not land here.
#   * SPEC-TOO-STRONG (attack E), SIX new correct reshapes — no soundness hole:
#     `(force nm).reverse.reverse` (exit 0 under the FROZEN tactic), an `if` on
#     `(force nm).isEmpty` whose both branches are honest (exit 0 frozen), `map
#     id` over the content (exit 1 frozen, exit 0 re-proved), a `match` inside a
#     `let` (exit 1 frozen, exit 0 re-proved), the content projection directly
#     (exit 1 frozen — and defeq to gold, rfl probe exit 0), and a measured
#     decreasing loop ahead of an honest return (exit 0 under the FROZEN tactic,
#     and NOT defeq to gold, rfl probe exit 1). Two of these fail only under the
#     frozen script and pass re-proved, which is the same tactic-shape brittleness
#     recorded above, not a spec defect — and the last is the sharpest datum in
#     this direction: the spec accepts a correct impl whose term does not
#     normalise to gold's.
#   * FRAME class re-derived (attack F) rather than taken from the note: an
#     impl-region `nm := Name.eager ['X']` is refused with "`nm` cannot be
#     mutated, only variables declared using `let mut` can be mutated" (exit 1),
#     and so is `nm.content := ['X']`. The input genuinely cannot be written on
#     this carrier, so the sibling's two frame-mutation rivals are vacuous here by
#     demonstration.
#   * PRESERVATION family re-derived: the two vacuity claims reproduce with the
#     exact quoted errors (`val`/`a` cannot be mutated, exit 1), and the
#     `alias-dead-branch` port (reject-guarded-selfvalue) is confirmed real by the
#     full witness/forgery battery above.
#   * DIVERGENCE (attack F′) re-measured against this bundle's `"total"` setting,
#     with the loop syntax corrected (the clauses go on the `while` header, before
#     `do`; an earlier pass's `invariant`-inside-`do` shape fails at the PARSER,
#     `unexpected token 'invariant'`, which measures nothing about termination).
#     With the correct syntax: an UNMEASURED `while True do pure ()` prefix is
#     rejected at elaboration (`Decreasing annotations are required in total
#     correctness semantics`) and a witness file over it fails at the loop itself,
#     ahead of any tester (exit 1) — so no witness can elaborate, confirming the
#     recorded per-shape reason. A MEASURED-NON-DECREASING loop (`decreasing q`,
#     body `q := q`) is rejected on the measure's own goal (`case «decreasing_1:
#     q»`, residual `⊢ q < q`) while a trivial witness over it BUILDS (exit 0),
#     also as recorded — and it is value-CORRECT, so there is no true refutation
#     of (Q) to state. A measured PROPERLY-decreasing loop ahead of a WRONG
#     (`dropLast`) return is rejected on (Q)'s goal, but its witness cannot
#     discriminate: it fails with `Application type mismatch ... forIn
#     Lean.Loop.mk`, the gate's own `loop-unification` stuck class, so such a case
#     would be recorded `witness-undecided`. The TOOLING NOTE is therefore
#     accurate and the "no case here" disposition is correct under `"total"`.
#   * TOOLING claims re-measured, not trusted: `extract_program_for lookupValue`
#     really does fail (`depends on declaration 'lookupValue', which has no
#     executable code`, exit 1), so the `.run` route the witnesses use is the only
#     one available; and an unnamed `assert force nm = nm.content` really is
#     refused (`Failed to parse an assertion without names`), so stating the
#     framing fact as a `have` is forced rather than preferred.
#   * COVERAGE reporter: `obl=1 cases=13 (+6/-7) binders=1 pts=4-4 ok`, no
#     findings, and the four witness points are genuinely distinct values across
#     both carriers rather than two spellings of one point (confirmed by the
#     type-reveal, which prints a different concrete argument per rival). (That
#     count was current for the 13-case battery of the fourth pass; the fifth
#     audit re-ran the reporter and re-states it below.)
#   * The one prose defect found: the count "413 of the 500 velvet batteries"
#     re-prove. Re-measured over every velvet manifest, the figure is 428 (and in
#     all 428 at least one re-proving case is an expect="verify" case; 126 have a
#     re-proving REJECT case — the fifth audit re-measured this companion figure
#     as 128, see below). Corrected in place. No other claim in this file
#     failed re-derivation.
#
# INDEPENDENT AUDIT, fifth pass (real `scripts/lean_verify.sh` builds; every exit
# code below was observed, none inferred). The 14-case battery of the fourth pass
# was re-derived end to end and stood up on every lane BUT ONE, where a recorded
# vacuity claim was wrong and cost the battery a whole facet of (Q).
#   * STATEMENT INTEGRITY (attack A): 14/14 in `variant_scope`, every changed
#     line inside the impl region or on the `prove_correct` tactic line. No case
#     reformats, weakens or restates the `ensures` clause.
#   * WITNESS DISCRIMINATION re-derived (attack B) for all 8 reject cases from the
#     manifest text, not from the recorded note: rival exit 0 / gold exit 1, eight
#     for eight; consistency probe exit 1 on all 6 witnesses that bind a
#     hypothesis (2 bind none, so no probe applies).
#   * FORGERY (attack B′) re-run for all 8, both halves. Claim-flip on the
#     CONCLUSION only — an earlier pass of this audit flipped every `≠` in the
#     statement including the one inside the hypothesis binder, which silently
#     turns 4 of the cases into a different claim and makes the comparison
#     meaningless; flipping only the conclusion gives gold exit 0 / rival exit 1,
#     eight for eight. Type-reveal prints a concrete equation on both sides in
#     8/8 and `has type True` in none.
#   * NO RIVAL IS DEFINITIONALLY GOLD (attack C): all 8 rival modules rebuilt
#     under BOTH the frozen and the re-proving tactic — exit 1 in all 16 builds,
#     each on `case «ensures_1: out = Except.ok (resolveName (force nm))»` with
#     the wrong argument, constructor or altered answer printed in the goal.
#   * SPEC-TOO-WEAK (attack D), 12 further wrong impls beyond the fourth pass's
#     thirteen (a constant key on the deferred arm, double application, echoing
#     the content, a length guard, a demonic pick, an infeasible demonic guard,
#     eager truncation, empty-content-only substitution, and four re-runs under an
#     aggressive `first | rfl | aesop | omega | trivial` body): ALL rejected, each
#     on (Q)'s own goal — the demonic ones on the `choice_1` goal, which confirms
#     again that (Q) binds every branch. No spec hole.
#   * SPEC-TOO-STRONG (attack E), 6 further correct reshapes: all provable, two
#     only when re-proved (the same in-scope tactic brittleness recorded above).
#     No soundness hole.
#   * DIVERGENCE (attack F′) re-measured against this bundle's own `"total"`
#     setting, including the combination the earlier passes had not measured (a
#     NON-decreasing measure AND a wrong return): same `Application type mismatch
#     ... forIn Lean.Loop.mk` stuck class as the decreasing-and-wrong shape, i.e.
#     `witness-undecided`, so the "no case here" disposition holds for that
#     combination too. The corpus census reproduces: 500/500 velvet bundles set
#     `"total"`, 0 set `"partial"`, so the retraction recorded above is correct.
#   * THE ONE REAL DEFECT (attack F, omission re-derivation): the accounting table
#     recorded the sibling's `preserve-poison-store` as VACUOUS (no heap). The
#     MECHANISM is vacuous — re-confirmed, `val := ...` after `let val := ...` is
#     refused, exit 1 — but the SUBSTANCE is expressible, and it attacks the
#     PASS-THROUGH facet of (Q) that no shipped rival touched: honest argument,
#     corrupted answer. Measured on `let mut served := resolveName key; served :=
#     served.set 0 'X'`: module exit 1 under the frozen, re-proving AND aggressive
#     tactics, residual `⊢ Except.ok ((resolveName (force nm)).set 0 'X') =
#     Except.ok (resolveName (force nm))`; witness rival exit 0 / gold exit 1 /
#     probe exit 1; claim-flip gold exit 0 / rival exit 1; type-reveal concrete on
#     both sides. Two sibling-shaped variants (reverse the answer, truncate the
#     answer) reject on the same facet. LANDED as reject-corrupt-served-value, and
#     the PRESERVATION FAMILY note and mapping table are corrected accordingly.
#     The `preserve-poison-accum` vacuity claim, by contrast, reproduces: the
#     aliasing-accumulation write is refused by the carrier (exit 1).
#   * COVERAGE reporter re-run after landing: `obl=1 cases=15 (+6/-9) binders=1
#     pts=4-4 ok`, 0 findings.
#   * PROSE re-derived rather than trusted: `extract_program_for` really fails
#     (no executable code), an unnamed `assert` really is refused, the
#     `let key :| (...)` shape really fails to synthesize, and the 428 re-proving
#     figure reproduces exactly. Its companion figure did NOT: 128 velvet
#     batteries carry a re-proving REJECT case, not 126. Corrected above.
#   * NO SPEC HOLE was found in either direction, and nothing is escalated. The
#     frozen `Solution.lean`, `meta.json` and `instance.json` were not touched.
#
# No frame/permission rival is fabricated (that class is vacuous on a
# referentially-transparent carrier with no `mut` binder — demonstrated by build
# in the PRESERVATION FAMILY note above, where the carrier refuses the write at
# elaboration).
#
# DIVERGENCE, final disposition. This paragraph previously read "Divergence is a
# real, already-escalated SPEC-level hole rather than a vacuous class", which the
# third audit deleted as a STALE CONTRADICTION: it is the retracted (ii) claim
# from the module docstring's own DIVERGENCE bullet, left standing in the closing
# summary after that bullet was corrected. Nothing about divergence is escalated
# and there is no hole. This bundle sets
# `loom.semantics.termination "total"` (as do all 500 velvet bundles), so a
# diverging rival is REJECTED, which is the correct behaviour and not a spec
# defect. It ships no case for the per-shape witness reasons measured in the
# DIVERGENCE bullet: the unmeasured shape admits no elaborating witness, and the
# measured-non-decreasing shape is value-correct, so no true refutation of (Q)
# exists to state. Anyone reading this file for the divergence disposition should
# read that bullet, not this summary.
AXIOM_TESTS = []
