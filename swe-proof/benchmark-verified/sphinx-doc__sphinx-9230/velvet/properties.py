"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9230 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct resolveParamMethod`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  resolveParamMethod (descriptor : List Char) (mayCarryType : Bool)
      return (out : ParsedParam)
    ensures out = resolveParam descriptor mayCarryType                    -- C1
    ensures mayCarryType = false →
              out = { name := descriptor, typeName := none }              -- C2
    ensures out.typeName = none → out.name = descriptor                   -- C3
    ensures ∀ t a, severTail descriptor = some (t, a) → mayCarryType = true →
              out = { name := a, typeName := some t }                     -- C4

The method resolves one parameter descriptor into a name and an optional inline
type. When the descriptor may carry a type and separates at the LAST run of
whitespace into a non-empty leading part and a trailing word, the leading part
becomes the recorded type and the trailing word the name; otherwise the
descriptor passes through untouched with no recorded type. The separation of one
descriptor is the pure ``def severTail`` (with ``rstripWs``/``tailWord``/
``beforeTailWord``); the per-descriptor outcome is the pure ``def resolveParam``.
Both are TRANSPARENT ``def``s over the method's own inputs — there is NO opaque
answer-key oracle in the load-bearing clause, so pinning ``out = resolveParam
descriptor mayCarryType`` is grounded, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. C1 (``out = resolveParam descriptor
mayCarryType``) is the total pin: it fixes the result at every input point of
both binders. C2 pins the ``mayCarryType = false`` sub-domain (pass-through with
no type); C3 pins the internal invariant that a no-type result leaves the name
equal to the descriptor; C4 pins the two-part sub-domain (last-whitespace
separation records ``(type, name)``). C2–C4 are all functions of the two input
binders — none is an input-independent constant — so each is separately
attackable by a rival that mishandles its sub-domain.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mut-*`` rivals write through a read-only (``Acc(.,1/2)``) reference
    to the token run and are rejected for INSUFFICIENT PERMISSION. Lean and
    Velvet are referentially transparent: the descriptor is an immutable value,
    this bundle declares no ``mut`` parameter, and there is no heap, aliasing, or
    permission system to subvert. There is no read-only input to overwrite, so
    the class is vacuous. No substitute probe is fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. C1's post-image is ``resolveParam
    descriptor mayCarryType``, a transparent ``def`` over the method's own
    arguments; there is no answer key to echo. The honest cheapest CORRECT impl
    (``return resolveParam descriptor mayCarryType``) is carried as a POSITIVE
    control instead — it doubles as proof the spec is not echo-vulnerable, since
    any WRONG resolution fails ``out = resolveParam descriptor mayCarryType``.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. The two nagini functions
    (name-side, type-side) are collapsed here into ONE method returning both
    fields in one ``ParsedParam``, so the name-side and type-side rivals become
    single rivals over the combined structure. A rival can separate at the FIRST
    whitespace instead of the last (the pre-change behaviour — correct on a
    single-whitespace descriptor, wrong on a multi-whitespace type), ignore the
    ``mayCarryType`` flag, swap the recorded name and type, or drop the recorded
    type entirely.
  * DIVERGENCE - nothing to ship, but the class is CLOSED BY THE SEMANTICS, and
    neither reason recorded here before was right. The nagini sibling carries no
    ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case, so there is nothing to
    port.
    The first reason given, that the class is "unreachable because the frozen impl
    is loop-free, so no diverging impl can be written", is FALSE and was measured
    false: an impl that opens with a ``while true`` spin loop and returns an
    unambiguously wrong value is in scope, since it edits only the impl region.
    Loop-freeness of the FROZEN impl bounds nothing, because a rival supplies its
    own body.
    The second reason, that under ``loom.semantics.termination "partial"`` the
    postcondition is claimed only of terminating runs so a diverging impl
    satisfies every ``ensures`` vacuously and is a KNOWN spec hole recorded for a
    ``partial`` cohort, is FALSE about this artifact. Line 4 reads ``"total"``, as
    it does in all 500 velvet bundles, and the option cannot drift from the file's
    ``open TotalCorrectness`` because the ``set_option`` elaborator itself runs
    ``openScope `TotalCorrectness`` (``Loom/MonadAlgebras/WP/Options.lean``, lines
    169-186). The cohort has no referent and the doc it cited no longer exists.
    Under ``total`` a postcondition is claimed of ALL runs, so every loop a rival
    splices owes a descent obligation ``measure b' < measure b``. Re-measured on
    THIS bundle with real builds, each proof reduced to a bare ``loom_solve``: the
    unmeasured spin loop is refused at elaboration (``Decreasing annotations are
    required in total correctness semantics``), and the sharper shape that CARRIES
    a measure the body never shrinks (``while q > 0 / invariant 0 <= q /
    done_with q = 0 / decreasing q``, body ``q := q``) is REJECTED on the
    measure's own goal, ``case «decreasing_1: q»`` with residual ``q < q``
    unsolved. A diverging rival is therefore rejected, not admitted.
    No reject case is written even so, and the reason is the WITNESS contract: a
    case needs a witness that ELABORATES against the rival, and the rival's module
    does not compile at all, since the descent obligation fails at the ``method``
    ahead of any appended tester. Recorded as REJECTED-BY-SPEC, not as a hole.

WITNESS MECHANICS ON THIS BUNDLE. Both the spec function ``resolveParam`` and its
callee ``severTail`` are TRANSPARENT ``def``s that ``decide`` reduces fully at a
concrete input, and the frozen impl is loop-free, so its extracted program
``resolveParamMethodExec`` — the ``NonDetT``-run of the ``do`` body — also
reduces under ``decide``. Each witness therefore states, at one concrete input,

    (match resolveParamMethodExec <descr> <flag> with | DivM.res r => r | _ => default)
        ≠ resolveParam <descr> <flag>

i.e. the rival's own output DIFFERS from the transparent post-image C1 demands —
a direct C1 violation the elaborator can see by computation. Against the FROZEN
solution the same statement fails: gold's extracted program computes exactly
``resolveParam <descr> <flag>``, so ``decide`` proves the ``≠`` FALSE and the
witness FAILS on gold — exactly the discrimination the gate requires. Every input
is a concrete decidable literal (no opaque term, no hypothesis), so no
consistency probe is needed. No banned token (sorry/admit/native_decide/axiom).
Each witness was checked out-of-band with ``scripts/lean_verify.sh``: every one
ELABORATES against its rival (exit 0) and FAILS against gold (exit 1), where the
gold-side error is ``Tactic `decide` proved that the proposition ... is false``
— the kernel COMPUTING both sides and refuting the concrete claim, not a stuck
reduction or a name error. Re-derived independently by the audit for all five.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries no axiom
tests (``AXIOM_TESTS = []`` there too); the A-reference deep model of the
last-whitespace separation is validated by axiom_check.py / G-AX, and the G-PBT
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9230"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, everything strictly
# ---- BETWEEN the method's `-- impl-start` / `-- impl-end`. Every variant
# ---- replaces exactly this text, so each edit lies wholly inside the one
# ---- impl region and same_spec holds by construction (asserted at load).
_IMPL = (
    "    let out : ParsedParam :=\n"
    "      if mayCarryType then\n"
    "        match severTail descriptor with\n"
    "        | some (typ, nm) => { name := nm, typeName := some typ }\n"
    "        | none           => { name := descriptor, typeName := none }\n"
    "      else\n"
    "        { name := descriptor, typeName := none }\n"
    "    return out"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A loop-free reshape may retune THIS block (elided
# from the spec view); most variants leave it as-is. Rivals leave it as-is too —
# the rejection is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct resolveParamMethod by\n"
    "  loom_solve\n"
    "  simp_all [resolveParam]"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for a reshape whose residual
    goal no longer matches the frozen tactic script)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble + builder. C1's carrier is transparent and the impl is
# ---- loop-free, so the extracted program reduces under `decide`; the witness
# ---- refutes C1 directly against the transparent `resolveParam`. Checked in a
# ---- file whose `prove_correct` block is stripped, so no tactic script can mask
# ---- the verdict.
_EXTRACT = "extract_program_for resolveParamMethod\n\n"


def _witness(descr, flag):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match resolveParamMethodExec ({descr}) {flag} with"
        " | DivM.res r => r | _ => default)\n"
        f"        ≠ resolveParam ({descr}) {flag} := by\n"
        "  decide\n"
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
        # Reshape: report the resolution of the descriptor DIRECTLY via the
        # transparent `def`, no inline branch/match. C1 is literally `out =
        # resolveParam descriptor mayCarryType`, so this is the cheapest HONEST
        # correct impl — and, since `resolveParam …` is GROUNDED in the inputs
        # (not an opaque answer key), it doubles as proof the spec is not
        # echo-vulnerable (any WRONG resolution fails C1). The inline branch is
        # gone, so the residual C2/C3/C4 goals no longer reduce under the frozen
        # `simp_all [resolveParam]` and are closed by unfolding + case-splitting
        # on both binders instead.
        "module": _impl_reproved(
            "    return (resolveParam descriptor mayCarryType)",
            "prove_correct resolveParamMethod by\n"
            "  loom_solve <;>\n"
            "    (intros <;>\n"
            "     simp_all [resolveParam] <;>\n"
            "     (cases mayCarryType <;> cases hs : severTail descriptor <;>"
            " simp_all))"),
        "rationale": (
            "the post-image `resolveParam descriptor mayCarryType` is GROUNDED "
            "in the inputs (a total transparent `def`, no opaque answer key), so "
            "`return resolveParam descriptor mayCarryType` is the honest cheapest "
            "CORRECT impl; C1 is literally that equation, so it MUST verify, else "
            "C1 is SPEC-TOO-STRONG. Ports the nagini honest-cheapest-impl control "
            "(the echo-attempt-honest analogue): the cheapest impl satisfying the "
            "grounded pin, showing the spec is not echo-vulnerable."
        ),
    },
    {
        "id": "pos-control-sev-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the last-whitespace separation to a typed local `sev`
        # before the branch, then match on it. Same value flow (`sev = severTail
        # descriptor`), different control shape; the frozen proof still closes
        # unchanged. Ports the nagini pos-control local-variable reshapes
        # (pos-control-name's named-index and pos-control-type's local-staging),
        # collapsed into one reshape over the combined method.
        "module": _impl(
            "    let sev := severTail descriptor\n"
            "    let out : ParsedParam :=\n"
            "      if mayCarryType then\n"
            "        match sev with\n"
            "        | some (typ, nm) => { name := nm, typeName := some typ }\n"
            "        | none           => { name := descriptor, typeName := none }\n"
            "      else\n"
            "        { name := descriptor, typeName := none }\n"
            "    return out"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the "
            "last-whitespace separation to a typed local before branching on it) "
            "must verify; the value flow is unchanged (`sev = severTail "
            "descriptor`) so C1–C4 still discharge and the frozen proof closes "
            "as-is. Ports the nagini pos-control local-variable reshapes. If it "
            "fails => SPEC-TOO-STRONG (over-fit to the inline-match code form)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-name. That case established the
    # read-only precondition `Acc(list_pred(.),1/2)` on an F2P-shaped input and
    # derived an F2P-shaped fact from it. This method carries NO `require` clause
    # (the pre-conditions region is empty), so nothing could exclude a normal
    # input and the classic "a normal input is admitted" probe is vacuous.
    # Re-aimed at the residual admissibility risk on a total domain: that the
    # four-clause post-image is jointly SATISFIABLE by a gold-shaped computation.
    # The frozen impl discharging all four ensures IS that witness. MUST verify,
    # else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the resolver is total over every "
            "descriptor and flag; the gold impl discharging all four ensures is "
            "the admissibility witness that the post-image (C1 plus C2/C3/C4) is "
            "jointly satisfiable. Near-trivial precisely because the precondition "
            "is empty. Re-aimed from the nagini admiss-name, whose read-only "
            "fractional-permission half has no counterpart on this "
            "referentially-transparent carrier. Else SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Between them they attack every
    # clause (C1/C2/C3/C4) and vary BOTH input binders (`descriptor` and
    # `mayCarryType`), at four distinct input points.
    # =====================================================================
    {
        "id": "rival-sever-first-whitespace",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-change behaviour: separate at the FIRST run of whitespace
        # instead of the last. Correct on a single-whitespace descriptor (there
        # is only one run), WRONG on any descriptor whose type part itself
        # contains whitespace — the genuine partial-domain break. Ports the
        # nagini prepatch name/type pair (the old first-whitespace separation)
        # (the two sides of the old first-whitespace separation), collapsed into
        # one rival over the combined result.
        "module": _impl(
            "    let out : ParsedParam :=\n"
            "      if mayCarryType then\n"
            "        let fw := descriptor.takeWhile (fun c => !isWs c)\n"
            "        let rest := (descriptor.dropWhile (fun c => !isWs c))"
            ".dropWhile isWs\n"
            "        if rest.isEmpty then { name := descriptor, typeName := none }\n"
            "        else { name := rest, typeName := some fw }\n"
            "      else\n"
            "        { name := descriptor, typeName := none }\n"
            "    return out"),
        "refinement": (
            "this IS the pre-change behaviour: separate on the FIRST whitespace "
            "run, at most once. A faithful real patch keeping the first-whitespace "
            "separation resolves a descriptor whose type expression contains "
            "spaces (the issue's bracketed-type case) into the head token as the "
            "type and the rest as the name — mangling the type and the name — so "
            "it does NOT resolve the F2P, which pins the whole bracketed type as "
            "the type and only the final word as the name. This is the exact "
            "defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C1/C4: `resolveParam` pins the LAST-whitespace "
            "separation (`severTail`), so on a multi-whitespace descriptor the "
            "first-whitespace rival records a different (type, name) pair than "
            "the post-image demands. Refuted at input `\"dict(a, b) x\"` with "
            "`mayCarryType = true` — a descriptor whose type part itself contains "
            "whitespace, where first- and last-whitespace separation diverge. If "
            "it verified => SPEC-TOO-WEAK (admits the reported bug)."
        ),
        "witness": _witness('"dict(a, b) x".toList', "true"),
    },
    {
        "id": "rival-ignore-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the may-carry-type flag: always attempt to separate, even when
        # the descriptor may NOT carry an inline type. Attacks C2 (the flag=false
        # sub-domain must pass the descriptor through untouched with no type).
        "module": _impl(
            "    let out : ParsedParam :=\n"
            "      match severTail descriptor with\n"
            "      | some (typ, nm) => { name := nm, typeName := some typ }\n"
            "      | none           => { name := descriptor, typeName := none }\n"
            "    return out"),
        "refinement": (
            "ignores the flag that says whether this descriptor kind may carry an "
            "inline type, separating unconditionally. A faithful real patch that "
            "resolved a type out of a descriptor whose field kind does NOT support "
            "inline types would record a spurious type on those fields, changing "
            "their rendered output, so it would NOT resolve (the F2P and the "
            "companion field-list assertions pin the untyped-kind behaviour to "
            "pass-through)."
        ),
        "rationale": (
            "REJECT from C2 (`mayCarryType = false → out = { name := descriptor, "
            "typeName := none }`): on a separable descriptor with the flag FALSE "
            "the rival records a type and shortens the name, violating C2. "
            "Refuted at input `\"int age\"` with `mayCarryType = false` — the ONLY "
            "witness that moves the `mayCarryType` binder to `false`, so the "
            "battery discriminates that binder. If it verified => SPEC-TOO-WEAK "
            "(the flag sub-domain would be unconstrained)."
        ),
        "witness": _witness('"int age".toList', "false"),
    },
    {
        "id": "rival-swap-name-type",
        "kind": "uniqueness",
        "expect": "reject",
        # Swap the recorded name and type: record the leading part as the name
        # and the trailing word as the type. Attacks C4 (which pins name := a
        # (the trailing word) and typeName := some t (the leading part)).
        "module": _impl(
            "    let out : ParsedParam :=\n"
            "      if mayCarryType then\n"
            "        match severTail descriptor with\n"
            "        | some (typ, nm) => { name := typ, typeName := some nm }\n"
            "        | none           => { name := descriptor, typeName := none }\n"
            "      else\n"
            "        { name := descriptor, typeName := none }\n"
            "    return out"),
        "refinement": (
            "swaps the two resolved parts — records the leading part as the name "
            "and the trailing word as the type. A faithful real patch that "
            "assigned the two locals in the wrong order would render the type "
            "text as the parameter name and vice versa, so it would NOT resolve "
            "(the F2P pins the trailing word as the name and the leading part as "
            "the type)."
        ),
        "rationale": (
            "REJECT from C4 (`severTail descriptor = some (t, a) ∧ mayCarryType = "
            "true → out = { name := a, typeName := some t }`): the rival returns "
            "`{ name := t, typeName := some a }`, the swap, violating C4. Refuted "
            "at input `\"a b\"` with `mayCarryType = true` — a distinct point from "
            "the other rivals (a minimal two-word separable descriptor). If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness('"a b".toList', "true"),
    },
    {
        "id": "rival-drop-type",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the trailing word as the name (correct) but DROP the recorded
        # type: typeName stays none even on a separable descriptor. Attacks C4
        # (typeName must be `some t`) — a near-miss that gets the name right.
        "module": _impl(
            "    let out : ParsedParam :=\n"
            "      if mayCarryType then\n"
            "        match severTail descriptor with\n"
            "        | some (_, nm) => { name := nm, typeName := none }\n"
            "        | none         => { name := descriptor, typeName := none }\n"
            "      else\n"
            "        { name := descriptor, typeName := none }\n"
            "    return out"),
        "refinement": (
            "resolves the trailing word as the name correctly but records NO "
            "inline type. A faithful real patch that separated the descriptor but "
            "never wrote the type local would render the parameter with its name "
            "correct but its inline type dropped, so it would NOT resolve (the "
            "F2P pins the inline type to be present and equal to the leading "
            "part)."
        ),
        "rationale": (
            "REJECT from C4 (`… → out = { name := a, typeName := some t }`): the "
            "rival returns `typeName := none` where C4 demands `some t`, so it "
            "violates C4 even though the name is right — a near-miss the total "
            "pin catches. Refuted at input `\"x y\"` with `mayCarryType = true` — "
            "a distinct point again, so the four uniqueness witnesses probe four "
            "distinct inputs (pts=4). If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness('"x y".toList', "true"),
    },
    {
        "id": "rival-clear-name-on-no-sever",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Attacks the one branch and the one clause the rest of
        # the battery leaves untouched: the `severTail = none` PASS-THROUGH arm
        # (reached with the flag TRUE, so `rival-ignore-flag`'s flag=false point
        # does not cover it) and C3 (`typeName = none → name = descriptor`). The
        # rival keeps the separable case exactly right and only mishandles the
        # NON-separable descriptor: instead of passing it through untouched it
        # returns an empty name. Every other rival differs from gold only on a
        # separable descriptor, so every other witness reduces through the `some`
        # arm; this is the only case whose witness input makes `severTail` return
        # `none`.
        "module": _impl(
            "    let out : ParsedParam :=\n"
            "      if mayCarryType then\n"
            "        match severTail descriptor with\n"
            "        | some (typ, nm) => { name := nm, typeName := some typ }\n"
            "        | none           => { name := [], typeName := none }\n"
            "      else\n"
            "        { name := descriptor, typeName := none }\n"
            "    return out"),
        "refinement": (
            "drops the descriptor on the floor in the no-separation case: a "
            "descriptor that does NOT separate into two parts must survive "
            "untouched, and this rival blanks it. A faithful real patch that "
            "cleared the name local when the separation found nothing to split "
            "would render every ordinary single-word parameter with an EMPTY "
            "name — so it does not resolve the F2P, whose companion assertions "
            "pin the plain single-word parameters (rendered by exactly this "
            "no-separation path) to their own text. Strictly more damaging than "
            "the reported defect, and on the same code path the fix touches."
        ),
        "rationale": (
            "REJECT from C3 (`out.typeName = none → out.name = descriptor`) and "
            "from C1: at a single-word descriptor `severTail` yields `none`, so "
            "the post-image demands `{ name := descriptor, typeName := none }` "
            "and the rival returns `{ name := [], typeName := none }` — a "
            "`typeName = none` result whose name is NOT the descriptor, the "
            "exact shape C3 forbids. Refuted at input `\"age\"` with "
            "`mayCarryType = true`, a FIFTH distinct point and the only witness "
            "in the battery that reduces through `severTail = none`. Added by "
            "the audit: C3 and the pass-through arm were previously argued to be "
            "defended-by-construction rather than attacked. If it verified => "
            "SPEC-TOO-WEAK (the no-separation branch would be unconstrained)."
        ),
        "witness": _witness('"age".toList', "true"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                   -> here
#   -----------------------------------------------------------------------
#   pos-control-name              -> pos-control-sev-local     RE-SHAPED (merged)
#   pos-control-type              -> pos-control-sev-local     (merged, see below)
#   (echo — see assessment)       -> pos-control-direct        RE-EXPRESSED
#   admiss-name                   -> admiss-gold-total          RE-AIMED
#   frame-mut-name                -> (none)                     VACUOUS
#   frame-mut-type                -> (none)                     VACUOUS
#   prepatch-name (remainder)     -> rival-sever-first-whitespace PORTED (merged)
#   prepatch-type (first token)   -> rival-sever-first-whitespace (merged)
#   partial-domain-name-n2        -> (subsumed by swap/drop)    RE-EXPRESSED
#   partial-domain-type-offbyone  -> rival-drop-type            RE-EXPRESSED
#   (no direct sibling)           -> rival-ignore-flag          ADDED (C2 binder)
#   (no direct sibling)           -> rival-swap-name-type       ADDED (C4)
#   (no direct sibling)           -> rival-clear-name-on-no-sever  ADDED BY AUDIT
#                                                               (C3 + none-arm)
#   AXIOM_TESTS ([])              -> (none)                     DROPPED (empty)
#
# 8 velvet SPEC cases: 2 soundness, 1 admissibility, 5 uniqueness.
#
# WHY THE COUNT SHRINKS (carrier narrowing, not omission). The nagini bundle
#   models TWO functions — a name-side (`parsed_argument_name`) and a type-side
#   (`parsed_argument_type`), each with its own gold impl, positive, partial-
#   domain rival, prepatch rival, and frame-mutation rival. This velvet bundle
#   models ONE method returning BOTH the name and the optional type in one
#   `ParsedParam`, so every name-side/type-side PAIR collapses to a single case
#   over the combined structure: one positive reshape, one prepatch rival (the
#   first-whitespace separation, whose two nagini sides — "name = remainder" and
#   "type = first token" — are the SAME wrong separation observed on the two
#   fields), and the partial-domain rivals become field-targeted rivals on the
#   one result.
#
# RE-SHAPED / MERGED (pos-control-name + pos-control-type -> pos-control-sev-local):
#   the nagini file carries a local-variable reshape on each side (named-index on
#   the name side; local-staging on the type side). Here the single method takes
#   one local-staging reshape (bind `severTail descriptor` to `sev` before the
#   branch) that exercises the same "different code shape, same value flow"
#   argument for both fields at once; the frozen proof closes unchanged.
# RE-EXPRESSED (honest-cheapest-impl -> pos-control-direct): the nagini positives
#   assert, in-region, that the built value equals the @Pure oracle applied to the
#   input. Here the oracle IS the transparent `resolveParam` and C1 already IS
#   `out = resolveParam descriptor mayCarryType`, so the honest cheapest impl is
#   `return resolveParam descriptor mayCarryType` — the same grounded-pin argument
#   as a loop-free correct impl (proof retuned since the inline branch is gone).
# RE-AIMED (admiss-name -> admiss-gold-total): the nagini case established the
#   read-only fractional-permission precondition on an F2P-shaped input. This
#   method has no `require` and no heap permission, so that probe is vacuous;
#   re-aimed at the residual total-domain risk (four-clause joint satisfiability),
#   witnessed by the frozen impl discharging all four ensures.
# PORTED / MERGED (prepatch-* -> rival-sever-first-whitespace): the nagini prepatch
#   pair is the old FIRST-whitespace separation observed separately on the name
#   ("whole remainder after the first token") and the type ("first token only").
#   On the combined method these are one impl — separate at the first whitespace —
#   whose (name, type) pair differs from the last-whitespace post-image on any
#   multi-whitespace descriptor. Its refinement is intact (keeping the
#   first-whitespace separation mangles the bracketed-type descriptor and does not
#   resolve), now backed by a machine-checked witness at `"dict(a, b) x"`.
# RE-EXPRESSED (partial-domain-* -> rival-drop-type + rival-swap-name-type):
#   the nagini partial-domain rivals diverge on a sub-domain (first token as name
#   for n==2; off-by-one truncation of the type). Here the analogous near-misses
#   over the combined result are rival-drop-type (name right, type dropped — a
#   truncation of the recorded type to nothing) and rival-swap-name-type (name and
#   type transposed). Both are genuine C4 violations with machine-checked
#   witnesses, not fabricated wrongness.
# ADDED (rival-ignore-flag): no direct nagini sibling (nagini's two functions did
#   not model the may-carry-type gate as an input; it was a fixed field-kind
#   property). Here `mayCarryType` is a modeled INPUT BINDER, so a rival that
#   ignores it is a real SPEC-TOO-WEAK risk on C2 and the only witness that moves
#   the flag binder to `false`. Real divergence with a machine-checked witness.
# FRAME-MUTATION (frame-mut-name/type): VACUOUS. The nagini rivals write through a
#   read-only (1/2) reference to the token run and are rejected for insufficient
#   permission. Velvet is referentially transparent, both inputs are immutable
#   values, no `mut` binder, no heap, no aliasing, no permission system. There is
#   no read-only input to overwrite. No substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
# DROPPED (AXIOM_TESTS): the nagini file's AXIOM_TESTS is already empty (the
#   last-whitespace separation is an A-reference deep model validated by
#   axiom_check.py / G-AX, not a consumed axiom); the G-PBT gate ignores
#   AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. C1 (the total pin) is attacked by
#   rival-sever-first-whitespace (a whole-result divergence on a multi-whitespace
#   descriptor); C2 (the flag=false sub-domain) by rival-ignore-flag; C4 (the
#   two-part separation records `(type, name)`) by rival-swap-name-type and
#   rival-drop-type. C3 (`typeName = none → name = descriptor`) is attacked by
#   rival-clear-name-on-no-sever, ADDED BY THE AUDIT. The claim previously made
#   here — that C3 "cannot be violated in isolation" and so is defended by the
#   positives rather than attacked — was FALSE: that rival keeps the separable
#   case exactly right and violates C3 only on the non-separable descriptor, is
#   in scope, and is rejected with a machine-checked witness at `"age"`. Its
#   witness is also the only one in the battery that reduces through the
#   `severTail = none` PASS-THROUGH arm; the other four all differ from gold on a
#   separable descriptor and so exercise only the `some` arm. Both input binders
#   are varied: `mayCarryType` is moved to `false` by rival-ignore-flag and held
#   `true` by the other four; `descriptor` ranges over five DISTINCT points —
#   `"dict(a, b) x"`, `"int age"`, `"a b"`, `"x y"`, `"age"` — so pts=5 and no
#   binder is held fixed by every witness. The two `severTail` arms are both
#   probed, which is the meaningful (verdict-changing) variation behind that
#   count, not five spellings of one point.
#
# WITNESS MECHANICS: both `resolveParam` and `severTail` are transparent `def`s
#   and the impl is loop-free, so each rival's extracted program
#   `resolveParamMethodExec` reduces fully under `decide`; each witness refutes C1
#   directly against the transparent `resolveParam` at a concrete input. Against
#   gold the extracted program computes exactly `resolveParam <descr> <flag>`, so
#   `decide` proves the `≠` FALSE and the witness FAILS — the required
#   discrimination. No witness binds a hypothesis (every input is a concrete
#   literal), so no consistency probe is needed. All five re-checked with
#   scripts/lean_verify.sh by the audit: rival exit 0, gold exit 1 with
#   `Tactic `decide` proved that the proposition ... is false` — a SEMANTIC
#   refutation of the concrete claim on the gold side, not a stuck reduction, a
#   missing identifier or a timeout.
#
# AUDIT RECORD (independent adversarial re-derivation of this battery).
#   Attack A (statement integrity): every case's diff against the frozen file is
#     confined to the impl region, plus a retuned `prove_correct` body on the two
#     cases that declare one. No `ensures` clause, method header or `pure` region
#     is touched by any case.
#   Attack B (witness re-derivation): all 5 reject witnesses rebuilt on both
#     subjects; rival exit 0 / gold exit 1 in every case, with the gold-side
#     failure being `decide` proving the proposition FALSE.
#   Attack C (is the rival wrong, or just different): each of the 5 rivals
#     differs from gold OBSERVABLY at its witness input — confirmed by that same
#     `decide`, which computes both sides. None is definitionally equal to gold.
#   Attack D (SPEC-TOO-WEAK probes, 4 NEW wrong impls, all REJECTED): pre-strip
#     the descriptor before resolving; substitute Lean's ASCII-only
#     `Char.isWhitespace` for the modeled 29-code-point alphabet (agrees with
#     gold on every ASCII input, differs at U+00A0 — the spec still catches it);
#     special-case the empty descriptor; record a spurious EMPTY type on the
#     no-separation arm. No spec hole found.
#   Attack E (SPEC-TOO-STRONG probes, 2 NEW correct reshapes, both VERIFY):
#     `match mayCarryType with` in place of the `if`; `severTail`'s body spelled
#     out inline. Both needed a retuned proof (a case split on the flag, or
#     `grind [resolveParam, severTail]`) — the frozen script is tuned to the
#     frozen shape — but both close, so the spec is not over-fit to the
#     inline-match code form.
#   The one FALSE claim found (the divergence rationale) is corrected in the
#   header; the one GAP found (C3 / the pass-through arm, previously argued as
#   defended-by-construction) is closed by rival-clear-name-on-no-sever.
AXIOM_TESTS = []
