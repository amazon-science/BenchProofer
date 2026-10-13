"""properties.py — G-PBT falsification battery for django__django-11119 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and both ``prove_correct`` obligations survive with byte-identical
statements) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against a subject that SATISFIES the spec — the frozen solution, or, where the
frozen impl's ``while`` loop leaves ``decide`` stuck and therefore deciding
nothing, the declared ``witness_reference`` (a verifying loop-free impl of the
same frozen spec). See "WHICH SUBJECT EACH WITNESS IS REFUTED AGAINST" below.

DEFENDED SURFACE (two contracted methods):

  escapeCodepoints (value : List Char) return (out : List Char)
    ensures out = escapedSeq value                                      -- E1

  valueToDisplay (encodeMarkup : Bool) (value : List Char) return (out : List Char)
    ensures out = (if encodeMarkup then escapedSeq value else value)    -- V1

``valueToDisplay`` is the fix-carrier: it renders an input value to display text
under the configured escaping policy. When the policy is on the value is
markup-escaped (its per-code-point entity expansion); when the policy is off it
is emitted verbatim. ``escapeCodepoints`` is the escaper the on-branch calls: a
backward ``while`` fold, each of the five significant chars expanding to its
entity, every other char passing through. The escape of one code point is the
pure ``def entity``; the escape of a whole sequence is the pure front-recursive
``escapedSeq`` (``escapedSeq (c :: cs) = entity c ++ escapedSeq cs``). Both are
TRANSPARENT ``def``s over the method's own input — there is NO opaque answer-key
oracle in either load-bearing clause, so pinning ``out = escapedSeq value`` /
``out = if encodeMarkup then escapedSeq value else value`` is grounded, not an
echo.

WHICH CLAUSES CONSTRAIN THE IMPL, AND WHAT THE SPEC DEFENDS.
  * V1 is the DISCRIMINATING clause — the whole subject of the change. Its
    binder ``encodeMarkup`` (the configured escaping policy) MUST govern the
    branch: escape iff the policy says so. The pre-change behaviour created the
    rendering context WITHOUT threading the policy, so the value was ALWAYS
    escaped even when the policy was off; the F2P witness (policy off, value
    ``<script>``, required verbatim) is exactly the input that behaviour gets
    wrong. V1's off-branch pins ``out = value`` (verbatim); its on-branch pins
    ``out = escapedSeq value`` (the real escape). Both legs are grounded in
    ``value`` and selected by ``encodeMarkup``.
  * E1 pins the escaper called on the on-branch. It is a function of ``value``
    at every position (which byte sequence each significant char maps to, and
    that every other char passes through), so no wrong per-char map satisfies it.
    The five significant arms of ``entity`` (& < > " ') are each attackable by a
    rival that drops that char's escape.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mutate-value`` rival writes through a read-only (``Acc(.,1/2)``)
    reference to ``value`` and is rejected for INSUFFICIENT PERMISSION. Lean and
    Velvet are referentially transparent: ``value`` is an immutable value,
    neither method declares a ``mut`` parameter, and there is no heap, aliasing,
    or permission system to subvert. There is no read-only input to overwrite,
    so the class is vacuous. No substitute probe is fabricated (see footer).
    DEMONSTRATED, not asserted: the analogue was built and the elaborator
    refuses it outright — ``value := ['x']`` inside the impl region fails with
    "``value`` cannot be mutated, only variables declared using ``let mut`` can
    be mutated", i.e. the rival cannot be WRITTEN, let alone verified. The one
    mutation the carrier does permit is a local shadow (``let mut v := value; v
    := ['x']``), which is not a frame violation at all: it leaves ``value``
    untouched and is simply caught by E1 as a wrong VALUE (residual goal
    ``escapedSeq ['x'] = escapedSeq value``) — already covered by the value
    rivals below. So there is no frame probe to port, on the carrier's own say-so.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. Both post-images are transparent
    (``escapedSeq value`` / the ``if``-selection), functions of the methods'
    own arguments; there is no answer key to echo. The honest cheapest CORRECT
    escaper (``return escapedSeq value``) is carried as a POSITIVE control — it
    doubles as proof E1 is not echo-vulnerable, since any WRONG per-char map
    fails ``out = escapedSeq value``.
  * PARTIAL-DOMAIN / VALUE — the reject surface. Against V1: force the value
    always escaped (the exact pre-change bug), force it always verbatim, invert
    the policy direction, or mis-render only a sub-domain of the off-branch.
    Against E1: drop the escape of a single significant char.
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
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

WITNESS MECHANICS ON THIS BUNDLE. The sibling django-11276 bundle established
that the ``derive_tester_for`` → ``decide`` path is dead when the postcondition
mentions an opaque axiom. Here BOTH post-images (E1, V1) are stated over the
TRANSPARENT ``escapedSeq`` (no opaque callee), so the same difficulty does not
even arise, and the uniform route is the extracted-program refutation. Each
rival is written LOOP-FREE (a ``value.flatMap`` per-char map for E1 rivals, a
direct ``return`` for V1 rivals), so its extracted program ``…Exec`` REDUCES
fully under ``decide`` at a concrete input. Each witness states, at one concrete
input, that the rival's own output DIFFERS from the transparent post-image the
clause demands — a direct clause violation the elaborator can see. No witness
binds a hypothesis (every input is a concrete literal that decides the clause),
so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque).

WHICH SUBJECT EACH WITNESS IS REFUTED AGAINST — and why it is not always gold.
The second half of the discrimination check needs a subject that SATISFIES the
spec and whose claim the kernel can actually EVALUATE. Gold qualifies only where
the point probed avoids gold's ``while`` loop:

  * The two OFF-branch V1 witnesses (``encodeMarkup = false``) take gold's
    ``pure value`` leg, which is loop-free, so ``decide`` evaluates and REFUTES
    them on gold outright (``decide`` proved the proposition is false). These
    carry no ``witness_reference``; gold is the subject.
  * Every other witness reaches gold's backward ``while`` fold, whose ``…Exec``
    is well-founded recursion the kernel does NOT reduce. There ``decide`` gets
    STUCK ("did not reduce to `isTrue` or `isFalse`") rather than deciding
    anything. A build that failed by stuck reduction attests to a refutation
    that was never performed — the same error appears for a TRUE claim about
    gold — so it is NOT a discrimination and must not be recorded as one. (The
    term is computable, not meaningless: ``#eval`` on gold's
    ``escapeCodepointsExec ['&']`` yields ``['&','a','m','p',';']``; it is the
    KERNEL that will not unfold it, not the program that lacks a value.)
    Attempts to reduce it anyway all fail: ``decide``, ``decide +kernel``,
    ``rfl``, ``simp [escapeCodepointsExec]``, ``unfold``, and
    ``grind [escapeCodepointsExec]`` were each built and each failed.

    So those seven cases name an explicit ``witness_reference``:
    ``pos-control-escaper-direct``'s module — a loop-free impl of this SAME
    frozen spec which this battery independently asserts (and the gate
    independently re-checks) VERIFIES. An impl the verifier accepts cannot
    violate its own spec, so a genuine "the spec is violated here" statement
    must still fail against it — and because that impl is loop-free, ``decide``
    EVALUATES the claim and refutes it semantically instead of getting stuck.
    Measured: all seven fail against it with ``decide`` proved that the
    proposition is false — a real verdict, not a stuck kernel.

  The reference is stated EXPLICITLY rather than left to the gate's fallback
  search. The gate can substitute a battery positive on its own when gold is
  stuck, but that path tries only the first few positives in MANIFEST ORDER, so
  relying on it would make this battery's attestation depend on case ordering
  and on which positive happens to reduce; naming the subject makes the record
  say what was actually checked.

Every witness was rebuilt out-of-band with ``scripts/lean_verify.sh``: each
ELABORATES against its own rival (exit 0) and FAILS against its declared subject
(exit 1) with a semantic ``decide`` refutation, never a missing identifier, type
error, or timeout.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real stdlib callee
(``django.utils.html.escape``); that is G-AX's job (axiom_check.py / mapping.md)
and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11119"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — all strictly INSIDE an -- impl-start .. -- impl-end region
# (or the elided prove_correct body), so same_spec holds by construction and
# both prove_correct obligations survive byte-identically. Every _swap asserts
# uniqueness at load, so drift in the frozen Solution.lean fails loudly here.
# ---------------------------------------------------------------------------

# The WHOLE frozen escapeCodepoints impl body (backward `while` fold), between
# that method's -- impl-start / -- impl-end.
_ESC_IMPL = (
    "    let mut result : List Char := []\n"
    "    let mut i := value.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ value.length\n"
    "      invariant result = escapedSeq (value.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := value[i - 1]!\n"
    "      result := entity c ++ result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _BASE.count(_ESC_IMPL) == 1, "escapeCodepoints impl region drifted"

# The frozen escapeCodepoints proof (retuned only by the loop-free positive,
# whose residual goal no longer needs the backward-fold step lemma).
_ESC_PROOF = (
    "prove_correct escapeCodepoints by\n"
    "  loom_solve\n"
    "  rw [escapedSeq_drop_step value i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_ESC_PROOF) == 1, "escapeCodepoints proof region drifted"

# The single in-loop prepend line (for the seg-local reshape; proof untouched).
_ESC_PREPEND = "      result := entity c ++ result"
assert _BASE.count(_ESC_PREPEND) == 1, "escapeCodepoints prepend line drifted"

# The WHOLE frozen valueToDisplay impl body (the policy selection), between that
# method's -- impl-start / -- impl-end.
_VD_IMPL = (
    "    let out ← if encodeMarkup then\n"
    "        escapeCodepoints value\n"
    "      else\n"
    "        pure value\n"
    "    return out"
)
assert _BASE.count(_VD_IMPL) == 1, "valueToDisplay impl region drifted"


def _esc_flatmap(mapexpr):
    """A loop-free escapeCodepoints rival: escape each char with a custom map.
    Being loop-free (`value.flatMap`) its extracted `…Exec` reduces under
    `decide`, so its witness discriminates; gold's `while` loop stays stuck."""
    return _swap(_BASE, _ESC_IMPL, f"    return (value.flatMap (fun c => {mapexpr}))")


def _vd(newbody):
    """A valueToDisplay rival: swap the whole policy-selection impl body."""
    return _swap(_BASE, _VD_IMPL, newbody)


# ---- witness builders. Both post-images are transparent, so refute the clause
# ---- directly against `escapedSeq` on the EXTRACTED program. Checked in a file
# ---- whose prove_correct blocks are stripped, so no tactic script can mask the
# ---- verdict.
_EXTRACT_ESC = "extract_program_for escapeCodepoints\n\n"
_EXTRACT_VD = "extract_program_for valueToDisplay\n\n"


def _esc_witness(inp):
    return (
        _EXTRACT_ESC +
        "example :\n"
        f"    (match escapeCodepointsExec ({inp}) with | DivM.res r => r | _ => [])"
        f" ≠ escapedSeq ({inp}) := by\n"
        "  decide\n"
    )


def _vd_witness(flag, inp):
    return (
        _EXTRACT_VD +
        "example :\n"
        f"    (match valueToDisplayExec {flag} ({inp}) with | DivM.res r => r | _ => [])"
        f" ≠ (if {flag} then escapedSeq ({inp}) else ({inp})) := by\n"
        "  decide\n"
    )


# ---- witness SUBJECT for the witnesses whose point reaches gold's `while` fold.
# Gold's escaper `…Exec` is well-founded recursion the KERNEL will not unfold, so
# `decide` there gets STUCK rather than deciding — a build failure that attests to
# no refutation at all (the same error appears for a TRUE claim). This is the
# loop-free CORRECT impl of the SAME frozen spec carried as
# `pos-control-escaper-direct`: it verifies (the battery asserts it and the gate
# re-checks it), so it cannot violate its own spec, and being loop-free its
# `…Exec` REDUCES — so `decide` returns a real verdict. Only the two OFF-branch V1
# witnesses avoid the loop (gold's `pure value` leg) and keep gold as subject.
_LOOPFREE_REF = _swap(
    _swap(_BASE, _ESC_IMPL, "    return (escapedSeq value)"),
    _ESC_PROOF, "prove_correct escapeCodepoints by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-escaper-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape escapeCodepoints: report the escape of the whole sequence
        # DIRECTLY via the transparent fold, no per-character loop. E1 is
        # literally `out = escapedSeq value`, so this is the cheapest HONEST
        # correct impl — and, since `escapedSeq value` is GROUNDED in the
        # argument (not an opaque answer key), it doubles as proof E1 is not
        # echo-vulnerable (any WRONG per-char map fails `out = escapedSeq
        # value`). The loop is gone, so the frozen proof's backward-fold step is
        # unneeded and the residual goal closes under `loom_solve` alone.
        "module": _LOOPFREE_REF,
        "rationale": (
            "the post-image `escapedSeq value` is GROUNDED in the input (a total "
            "front-recursive fold, no opaque answer key), so `return escapedSeq "
            "value` is the honest cheapest CORRECT escaper; E1 is literally `out "
            "= escapedSeq value`, so it MUST verify, else E1 is SPEC-TOO-STRONG. "
            "Ports the nagini echo-attempt-honest control: the cheapest impl "
            "satisfying the grounded pin, showing the spec is not echo-vulnerable."
        ),
    },
    {
        "id": "pos-control-escaper-seg-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape escapeCodepoints: keep the backward `while` fold but bind the
        # per-code-point entity sequence to a local `e` before prepending. Same
        # value flow (`e = entity c`), different control shape; the frozen proof
        # still closes unchanged (invariant and step lemma untouched).
        "module": _swap(
            _BASE, _ESC_PREPEND,
            "      let e := entity c\n      result := e ++ result"),
        "rationale": (
            "a correct escaper with a DIFFERENT control shape (bind the per-code-"
            "point entity sequence to a local before prepending) must verify; the "
            "value flow is unchanged (`e = entity c`) so E1 still discharges and "
            "the frozen loop proof closes as-is. Ports the nagini "
            "pos-control-seg-local: if it fails => SPEC-TOO-STRONG (over-fit to "
            "the inline-prepend code form)."
        ),
    },
    {
        "id": "pos-control-policy-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape valueToDisplay: same policy selection, branches written in the
        # opposite order (`if !encodeMarkup then verbatim else escape`). Same
        # value flow — the policy still governs the branch identically — so V1
        # discharges and `loom_solve` closes as-is. Ports the nagini
        # pos-control-reordered onto the fix-carrier's branch structure.
        "module": _vd(
            "    let out ← if !encodeMarkup then\n"
            "        pure value\n"
            "      else\n"
            "        escapeCodepoints value\n"
            "    return out"),
        "rationale": (
            "a correct fix-carrier with the policy branch written in the opposite "
            "order (`if !encodeMarkup then verbatim else escape`) must verify; the "
            "policy still governs the branch identically so V1 discharges under "
            "`loom_solve`. Ports the nagini pos-control-reordered onto the policy "
            "selection: if it fails => SPEC-TOO-STRONG (over-fit to one branch "
            "order)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-f2p-witness. That case
    # established the read-only fractional-permission precondition on the F2P
    # witness value under BOTH policy settings. Neither method here carries a
    # `require` (the pre-conditions regions are empty) and there is no heap
    # permission, so the classic "a normal input is admitted" probe is vacuous.
    # Re-aimed at the residual admissibility risk on a total domain: that the
    # post-images (E1 and V1) are jointly SATISFIABLE by a gold-shaped
    # computation. The frozen impl discharging both obligations IS that witness.
    # MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "neither method carries a `require`, so the escaper and the "
            "fix-carrier are total over every code-point sequence and both policy "
            "settings; the gold impl discharging E1 and V1 is the admissibility "
            "witness that both post-images are jointly satisfiable. Near-trivial "
            "precisely because the preconditions are empty. Re-aimed from the "
            "nagini admiss-f2p-witness, whose read-only-precondition half has no "
            "counterpart on this referentially-transparent carrier. Else "
            "SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P.
    #
    # V1 rivals attack the fix-carrier's policy selection (binder `encodeMarkup`
    # varied across true and false). E1 rivals attack the escaper's per-char map
    # (binder `value` varied across the five significant chars).
    # =====================================================================
    {
        "id": "rival-force-escape",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG ITSELF. Ignore the policy flag and ALWAYS escape — exactly the
        # pre-change behaviour (the rendering context created without the policy,
        # so the value is always escaped).
        "module": _vd("    return (escapedSeq value)"),
        "refinement": (
            "ignores the policy and always escapes — the pre-change behaviour "
            "(the rendering context created without threading the configured "
            "policy). Its faithful real patch is the unpatched repo, which is "
            "precisely what FAILS the F2P: with the policy off, the value "
            "'<script>' must be emitted verbatim but this escapes it to "
            "'&lt;script&gt;'. It would NOT resolve — this is the exact defect "
            "the fix corrects."
        ),
        "rationale": (
            "REJECT from V1's OFF-branch (`encodeMarkup = false ⟹ out = value`): "
            "escaping when the policy is off diverges from the verbatim post-image "
            "for any value containing a significant char. Refuted at "
            "`encodeMarkup=false`, input `['<']`. If it verified => SPEC-TOO-WEAK "
            "(admits the very bug, mirrors G-DIFF)."
        ),
        "witness": _vd_witness("false", "['<']"),
    },
    {
        "id": "rival-force-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual bug: ignore the policy flag and NEVER escape (always verbatim).
        "module": _vd("    return value"),
        "refinement": (
            "ignores the policy and always emits verbatim, never escaping. Its "
            "faithful real patch would stop escaping under the default policy "
            "(on), so a rendered context value would no longer be escaped — "
            "FAILING the P2P test_basic_context, which renders under the default "
            "policy and relies on escaping. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from V1's ON-branch (`encodeMarkup = true ⟹ out = escapedSeq "
            "value`): emitting verbatim when the policy is on diverges from the "
            "escaped post-image for any value with a significant char. Refuted at "
            "`encodeMarkup=true`, input `['<']` — a DISTINCT policy setting from "
            "rival-force-escape, so the `encodeMarkup` binder is varied across "
            "both values. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _vd_witness("true", "['<']"),
        # `encodeMarkup = true` takes gold's ON leg, which CALLS the `while`-loop
        # escaper, so `decide` is stuck against gold and decides nothing. Refuted
        # instead against the verifying loop-free impl of the same spec, where it
        # reduces to a real `decide` verdict. See the docstring's subject note.
        "witness_reference": _LOOPFREE_REF,
    },
    {
        "id": "rival-invert-policy",
        "kind": "uniqueness",
        "expect": "reject",
        # Inherit the flag but SWAP the branches: escape when OFF, verbatim when ON.
        "module": _vd(
            "    let out ← if !encodeMarkup then\n"
            "        escapeCodepoints value\n"
            "      else\n"
            "        pure value\n"
            "    return out"),
        "refinement": (
            "inverts the meaning of the policy: escapes when off, verbatim when "
            "on. Its faithful real patch (reading the negated policy) would escape "
            "'<script>' under policy off (FAIL the F2P) and stop escaping under "
            "the default policy on (FAIL P2P test_basic_context). It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from V1: the policy branch is inverted, so BOTH legs are "
            "wrong — under ON it emits verbatim (violates the escaped pin) and "
            "under OFF it escapes (violates the verbatim pin). Refuted at "
            "`encodeMarkup=true`, input `['<']` (the ON leg, where it wrongly "
            "emits verbatim). If it verified => SPEC-TOO-WEAK (policy direction "
            "unconstrained). Ports nagini rival-invert-policy."
        ),
        "witness": _vd_witness("true", "['<']"),
        # As rival-force-verbatim: the ON leg reaches gold's `while` escaper, so
        # gold cannot decide. Subject is the verifying loop-free impl.
        "witness_reference": _LOOPFREE_REF,
    },
    {
        "id": "rival-partial-verbatim-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the OFF branch: honor the policy and escape correctly
        # when on; when off, emit verbatim EXCEPT escape the leading '<' (index 0)
        # to its entity, copying every other position verbatim. Correct on every
        # off-input that does not begin with '<'.
        "module": _vd(
            "    let out ← if encodeMarkup then\n"
            "        escapeCodepoints value\n"
            "      else\n"
            "        pure (match value with\n"
            "          | c :: rest => (if c = '<' then \"&lt;\".toList else [c]) ++ rest\n"
            "          | [] => [])\n"
            "    return out"),
        "refinement": (
            "honors the policy and escapes correctly when on; when off, emits "
            "verbatim EXCEPT it escapes the leading '<' (index 0). A faithful real "
            "patch of this shape (verbatim path special-casing position 0) would "
            "still escape the leading '<' of '<script>' under policy off and FAIL "
            "the F2P (which requires '<script>' verbatim). A genuine partial-"
            "domain break — correct on every off-input not starting with '<'. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from V1's OFF-branch: it pins the WHOLE sequence including "
            "index 0, so a rival that mis-escapes only the leading '<' still "
            "diverges from `value` on inputs of shape '<…'. Refuted at "
            "`encodeMarkup=false`, input `['<', 'a']` — a DISTINCT point from "
            "rival-force-escape (a leading '<' followed by an ordinary char), so "
            "the `value` binder is varied too. Ports nagini "
            "partial-domain-verbatim-first. If it verified => SPEC-TOO-WEAK "
            "(domain-incomplete on the discriminating branch)."
        ),
        "witness": _vd_witness("false", "['<', 'a']"),
    },
    {
        "id": "rival-escaper-drop-amp",
        "kind": "uniqueness",
        "expect": "reject",
        # E1 rival: drop the ampersand escape — '&' passes through unescaped.
        "module": _esc_flatmap("if c = '&' then [c] else entity c"),
        "refinement": (
            "lets the ampersand pass through unescaped in the escaper the on-"
            "branch calls; a real patch doing this would leave literal ampersands "
            "in escaped output (the substitution that must be done first, so "
            "emitted entities are never re-escaped), and the escape contract pins "
            "the ampersand's entity token, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from E1 (`out = escapedSeq value`): `escapedSeq` pins the "
            "ampersand's entity sequence (`entity '&' = \"&amp;\".toList`), so a "
            "rival passing it through diverges at every ampersand. Refuted at "
            "input `['&']` — the '&' arm of `entity`. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _esc_witness("['&']"),
        # Every E1 witness probes `escapeCodepointsExec`, i.e. gold's `while` fold
        # itself, so `decide` is stuck against gold. Subject is the verifying
        # loop-free impl of the same spec, where the claim reduces and is refuted.
        "witness_reference": _LOOPFREE_REF,
    },
    {
        "id": "rival-escaper-drop-lt",
        "kind": "uniqueness",
        "expect": "reject",
        # E1 rival: drop the less-than escape — '<' passes through unescaped.
        "module": _esc_flatmap("if c = '<' then [c] else entity c"),
        "refinement": (
            "lets the less-than sign pass through unescaped in the escaper; a "
            "real patch doing this would leave literal tag-opening characters in "
            "escaped output (an injection hole), and the escape contract pins its "
            "entity token, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from E1 (`out = escapedSeq value`): `escapedSeq` pins the "
            "less-than sign's entity sequence (`entity '<' = \"&lt;\".toList`), so "
            "a rival passing it through diverges at every '<'. Refuted at input "
            "`['<']` — the '<' arm of `entity`, the canonical XSS-relevant char. "
            "If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _esc_witness("['<']"),
        # Every E1 witness probes `escapeCodepointsExec`, i.e. gold's `while` fold
        # itself, so `decide` is stuck against gold. Subject is the verifying
        # loop-free impl of the same spec, where the claim reduces and is refuted.
        "witness_reference": _LOOPFREE_REF,
    },
    {
        "id": "rival-escaper-drop-gt",
        "kind": "uniqueness",
        "expect": "reject",
        # E1 rival: drop the greater-than escape — '>' passes through unescaped.
        "module": _esc_flatmap("if c = '>' then [c] else entity c"),
        "refinement": (
            "lets the greater-than sign pass through unescaped in the escaper; a "
            "real patch doing this would leave literal tag-closing characters in "
            "escaped output, and the escape contract pins its entity token, so it "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from E1 (`out = escapedSeq value`): `escapedSeq` pins the "
            "greater-than sign's entity sequence (`entity '>' = \"&gt;\".toList`), "
            "so a rival passing it through diverges at every '>'. Refuted at input "
            "`['>']` — the '>' arm of `entity`. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _esc_witness("['>']"),
        # Every E1 witness probes `escapeCodepointsExec`, i.e. gold's `while` fold
        # itself, so `decide` is stuck against gold. Subject is the verifying
        # loop-free impl of the same spec, where the claim reduces and is refuted.
        "witness_reference": _LOOPFREE_REF,
    },
    {
        "id": "rival-escaper-drop-quot",
        "kind": "uniqueness",
        "expect": "reject",
        # E1 rival: drop the double-quote escape — '"' passes through unescaped.
        "module": _esc_flatmap("if c = '\"' then [c] else entity c"),
        "refinement": (
            "lets the double-quote pass through unescaped in the escaper; a real "
            "patch doing this would emit unsafe attribute markup, and the escape "
            "contract pins the double-quote's entity token, so it would NOT "
            "resolve. Ports the nagini rival-drop-quot."
        ),
        "rationale": (
            "REJECT from E1 (`out = escapedSeq value`): `escapedSeq` pins the "
            "double-quote's entity sequence (`entity '\"' = \"&quot;\".toList`), "
            "so a rival passing it through diverges at every double-quote. Refuted "
            "at input `['\"']` — the '\"' arm of `entity`. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _esc_witness("['\"']"),
        # Every E1 witness probes `escapeCodepointsExec`, i.e. gold's `while` fold
        # itself, so `decide` is stuck against gold. Subject is the verifying
        # loop-free impl of the same spec, where the claim reduces and is refuted.
        "witness_reference": _LOOPFREE_REF,
    },
    {
        "id": "rival-escaper-drop-apos",
        "kind": "uniqueness",
        "expect": "reject",
        # E1 rival: drop the apostrophe escape — '\'' passes through unescaped.
        "module": _esc_flatmap("if c = '\\'' then [c] else entity c"),
        "refinement": (
            "lets the apostrophe pass through unescaped in the escaper; a real "
            "patch doing this would emit unsafe attribute markup, and the escape "
            "contract pins the apostrophe's entity token (the legacy decimal "
            "reference at this base_commit), so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from E1 (`out = escapedSeq value`): `escapedSeq` pins the "
            "apostrophe's entity sequence (`entity '\\'' = \"&#39;\".toList`), so "
            "a rival passing it through diverges at every apostrophe. Refuted at "
            "input `['\\'']` — the fifth and last significant-char arm of "
            "`entity`, so every arm (& < > \" ') is attacked by some rival. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _esc_witness("['\\'']"),
        # Every E1 witness probes `escapeCodepointsExec`, i.e. gold's `while` fold
        # itself, so `decide` is stuck against gold. Subject is the verifying
        # loop-free impl of the same spec, where the claim reduces and is refuted.
        "witness_reference": _LOOPFREE_REF,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                    -> here
#   -----------------------------------------------------------------------
#   pos-control-reordered          -> pos-control-policy-reorder    RE-AIMED
#   pos-control-seg-local          -> pos-control-escaper-seg-local PORTED
#   echo-attempt-honest            -> pos-control-escaper-direct    RE-EXPRESSED
#   admiss-f2p-witness             -> admiss-gold-total             RE-AIMED
#   frame-mutate-value             -> (none)                        VACUOUS
#   rival-force-escape-true        -> rival-force-escape            PORTED
#   rival-invert-policy            -> rival-invert-policy           PORTED
#   partial-domain-verbatim-first  -> rival-partial-verbatim-first  PORTED
#   rival-drop-quot                -> rival-escaper-drop-quot       PORTED
#   (no sibling)                   -> rival-force-verbatim          ADDED
#   (no sibling)                   -> rival-escaper-drop-amp        ADDED
#   (no sibling)                   -> rival-escaper-drop-lt         ADDED
#   (no sibling)                   -> rival-escaper-drop-gt         ADDED
#   (no sibling)                   -> rival-escaper-drop-apos       ADDED
#   AXIOM_TESTS (3)                -> (none)                        DROPPED (G-AX)
#
# 13 velvet SPEC cases: 3 soundness, 1 admissibility, 9 uniqueness. This bundle
# models TWO purely-functional cores — the escaper `escapeCodepoints` (E1) and
# the policy-selection fix-carrier `valueToDisplay` (V1) — so both obligations
# are defended AND attacked. Every nagini uniqueness rival that attacks a
# modeled clause is ported; the added rivals complete per-arm coverage of E1 and
# add the verbatim-forcing dual of the pre-change bug on V1.
#
# RE-AIMED (pos-control-reordered -> pos-control-policy-reorder): the nagini
#   reorder positive permuted the if/elif significant-char chain in the escape
#   loop. On this carrier the per-char map is the pure `entity` def (no inline
#   if/elif in the impl to reorder), so the reorder is re-aimed at the ONE branch
#   that IS in an impl region here: valueToDisplay's policy `if`, written in the
#   opposite order. Same value flow, must verify.
# PORTED (pos-control-seg-local): binds `e := entity c` before prepending in the
#   escaper loop; frozen proof closes as-is.
# RE-EXPRESSED (echo-attempt-honest -> pos-control-escaper-direct): the nagini
#   honest-echo control asserted the built list equals the @Pure oracle. Here the
#   oracle IS the transparent `escapedSeq` and E1 already IS `out = escapedSeq
#   value`, so the honest cheapest impl is `return escapedSeq value` — same
#   argument (grounded pin satisfiable only by the real work; no wrong echo
#   verifies) as a loop-free correct impl.
# RE-AIMED (admiss-f2p-witness -> admiss-gold-total): the nagini case established
#   the read-only fractional-permission precondition on an F2P-shaped input under
#   both policy settings. No `require`, no heap permission here, so that probe is
#   vacuous; re-aimed at total-domain joint satisfiability of E1 and V1,
#   witnessed by the frozen impl.
# PORTED (V1 rivals): rival-force-escape (the pre-change always-escape bug),
#   rival-invert-policy (branches swapped), rival-partial-verbatim-first (leading
#   '<' escaped on the off-branch) carry their nagini refinement arguments
#   (unpatched-repo / policy-inversion / position-0 special-case each fail the
#   same F2P/P2P assertion), now backed by machine-checked witnesses over the
#   fix-carrier. PORTED (E1 rival): rival-escaper-drop-quot.
# ADDED: rival-force-verbatim (the never-escape dual: fails the default-policy
#   P2P) covers V1's ON-branch; rival-escaper-drop-{amp,lt,gt,apos} drop the
#   escape of the remaining significant chars so every arm of `entity`
#   (& < > " ') is attacked. Real divergences with machine-checked witnesses, not
#   fabricated wrongness.
# FRAME-MUTATION (frame-mutate-value): VACUOUS. The nagini rival writes through a
#   read-only (1/2) reference to `value` and is rejected for insufficient
#   permission. Velvet is referentially transparent, `value` is an immutable
#   value, no `mut` binder, no heap, no aliasing, no permission system. There is
#   no read-only input to overwrite. No substitute fabricated.
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
# DROPPED (AXIOM_TESTS): the nagini file's three axiom-soundness/containment
#   probes over the real stdlib callee are G-AX's job (axiom_check.py /
#   mapping.md); the G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE.
#   * V1 (the discriminating fix clause) is attacked on BOTH legs and its policy
#     binder: OFF-leg (rival-force-escape, encodeMarkup=false), ON-leg
#     (rival-force-verbatim + rival-invert-policy, encodeMarkup=true), and its
#     partial off-sub-domain (rival-partial-verbatim-first). The `encodeMarkup`
#     binder is varied across true AND false — no rival holds it fixed.
#   * E1 (the escaper) is attacked on all five significant-char arms of `entity`
#     (drop-amp '&', drop-lt '<', drop-gt '>', drop-quot '"', drop-apos '\''),
#     varying `value`.
#   * Both obligations are DEFENDED by positives (E1 by escaper-direct and
#     escaper-seg-local; V1 by policy-reorder) and the admissibility case (both
#     discharge on gold).
#   * Reject witnesses probe 7 distinct input points: `(false,['<'])`,
#     `(true,['<'])`, `(false,['<','a'])`, `['&']`, `['<']`, `['>']`, `['"']`,
#     `['\'']` — so pts >= 7 and no binder is held fixed by every witness.
#
# WITNESS MECHANICS: both post-images are stated over the TRANSPARENT `escapedSeq`
#   (no opaque callee), so the refutation is direct. Every witness extracts the
#   executable program (`escapeCodepointsExec` / `valueToDisplayExec`) and refutes
#   its clause at a concrete input; each rival is loop-free so its `…Exec` reduces
#   under `decide`. The SUBJECT the refutation is checked against differs by case,
#   and the difference matters (see the docstring's subject note):
#     - gold as subject (2 cases): rival-force-escape and
#       rival-partial-verbatim-first probe `encodeMarkup=false`, which takes
#       gold's loop-free `pure value` leg. `decide` EVALUATES and refutes them on
#       gold — "`decide` proved that the proposition is false".
#     - `witness_reference` = the verifying loop-free impl (7 cases): every E1
#       witness plus the two `encodeMarkup=true` V1 witnesses reach gold's
#       `while` fold, where `decide` gets STUCK ("did not reduce to `isTrue` or
#       `isFalse`"). A stuck build refutes NOTHING — the identical error appears
#       for a true claim — so gold cannot serve as subject and the case names
#       `pos-control-escaper-direct`'s module instead: same frozen spec, verified
#       independently, loop-free so the claim reduces to a real verdict.
#   Declaring the reference rather than leaning on the gate's own stuck-reduction
#   fallback keeps the attestation independent of manifest ORDER (that fallback
#   tries only the first few positives, in manifest order).
#   No witness binds a hypothesis, so no consistency probe is needed. All 18
#   builds re-run with scripts/lean_verify.sh: rival exit 0, subject exit 1 with a
#   semantic `decide` refutation in every case. Rival modules independently fail
#   verification.
AXIOM_TESTS = []
