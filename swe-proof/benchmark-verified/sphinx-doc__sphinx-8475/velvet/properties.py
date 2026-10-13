"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8475 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct resolveLinkStatus`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method).

  resolveLinkStatus (headProbe : Probe) (getProbe : Probe) return (out : LinkStatus)
    ensures out = resolveLinkStatusSpec headProbe getProbe

The method reports the status of a remote target from a lightweight first probe
(``headProbe``) and, when that probe's failure warrants a full-fetch retry, a
second probe (``getProbe``). Each ``Probe`` is either ``reached b`` (a response
was obtained; ``b`` records whether the final location equals the requested one)
or ``failed e`` (the attempt raised a ``RequestFailure``: ``statusError code``,
``redirectLoop``, or ``otherFailure``). ``resolveLinkStatusSpec`` is a fully
unfolded ``def`` in the ``pure`` region (the ``axioms`` region declares NO
``axiom`` — there is no opaque answer key to echo), composing three grounded
sub-behaviours over the two input binders:

    * classifyReached — a reached target is ``working`` iff its final location is
      the requested one, else ``redirected`` (reads the ``reached`` bit);
    * retriable       — a first-probe failure is retried with a full fetch iff it
      is a status-carrying failure OR a redirect-budget exhaustion, NOT any other
      failure (this is the changed sub-behaviour: the retry set is WIDENED to
      include the redirect-budget exhaustion);
    * classifyUnhandled — a failure that reaches the top-level handler is read by
      its status code (401 -> ``working``, 503 -> ``ignored``, else ``broken``);
      a redirect-budget exhaustion and every other failure are ``broken``.

The discriminating content of the fix is ``retriable`` on the redirect-budget
exhaustion: the failing test drives a target that loops on the lightweight probe
(a redirect-budget exhaustion) but answers a full fetch successfully, and the
target must be reported ``working`` — the pre-image skeleton did NOT retry that
failure and reported it ``broken`` (Solution_prepatch.lean).

TWO INPUT BINDERS, both free (no ``require`` clause): ``headProbe`` and
``getProbe``. Each ranges over ``reached b`` (both ``b`` values) and ``failed e``
(all three ``RequestFailure`` shapes, the status code observed at 401/503/other).
The reject witnesses move both binders across BOTH ``Probe`` constructors, both
``reached`` bits, and every failure shape, so no arm is left pinned.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The class exists on the nagini sibling
    because a by-reference input may carry a fractional heap permission an impl
    can overwrite in place. Both inputs here are immutable ``Probe`` VALUES, this
    bundle declares no ``mut`` binder, and Lean/Velvet are referentially
    transparent — there is no heap, no aliasing, and no read-only input to
    overwrite. No substitute probe is fabricated (per the porting map, this class
    is legitimately dropped, reported not faked). (The sibling additionally notes
    its frame lane is vacuous already because both its inputs are pass-by-value
    scalars.)
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records.
    ``resolveLinkStatusSpec`` is a total, fully unfolded function of the method's
    own two arguments (the ``axioms`` region declares no ``axiom``). There is no
    opaque answer key an echo could carry, so the positive controls are honest
    cheapest-reshape controls.
  * SOUNDNESS positives — APPLY. A structurally different but faithful dispatch
    must still verify, else SPEC-TOO-STRONG.
  * ADMISSIBILITY — the sibling asserts the precondition ADMITS the F2P-shaped
    input AND that the gold logic resolves it to the ``working`` success the
    failing test expects. This bundle carries NO ``require`` clause, so the
    precondition-admission half is degenerate; the case is RE-AIMED at the
    residual total-domain risk that the post-image is DEGENERATE at the
    interesting point — via an in-region assert pinning that the F2P scenario (a
    redirect-budget exhaustion on the first probe, a reached full fetch) resolves
    to ``working`` (and NOT ``broken``), and that a non-retriable first failure
    resolves to ``broken``. The impl is kept verbatim so the method's own
    obligation still discharges.
  * PARTIAL-DOMAIN / VALUE — the heart of this surface. A rival right on part of
    the domain that mis-routes ONE sub-behaviour: the retry set (each of the
    three failure shapes independently), the never-retry-on-success edge, the
    reached-target classification, and the top-level status-code reading.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (a match, no
loop): its extracted program reduces fully under ``decide``, and the sole
``ensures`` is a bare equality with no quantifier, so the tester route is
AVAILABLE (``prove_postcondition_decidable_for`` succeeds). Each reject rival
carries a machine-checked refutation ``witness`` — a Velvet tester statement
``resolveLinkStatusTester <headProbe> <getProbe> = false`` at ONE concrete input
pair, checked in a file whose ``prove_correct`` block has been stripped so no
tactic script can mask the verdict. Every witness was SEEN to discriminate with
two real builds: it ELABORATES against its rival (exit 0) and FAILS against the
frozen solution (``decide`` proves the proposition false, exit 1). Every witness
states its refutation at concrete literals and binds nothing in its head, so
there is no consistency obligation to satisfy.

AXIOM lane: DROPPED. The axiom lane is G-AX's job and this gate ignores
``AXIOM_TESTS`` regardless. This bundle consumes no ``axiom`` (``retriable`` /
``classifyReached`` / ``classifyUnhandled`` are modeled DEEPLY; the binding of
``RequestFailure`` to the real request-exception hierarchy is an A-reference
validated by ``axiom_check.py`` / G-AX). The sibling's two ``AXIOM_TESTS``
(``ax-sound-is_retryable`` soundness, ``ax-contain-reachable-kinds`` containment)
live entirely in that lane.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8475"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or is the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method between the impl markers.
_IMPL = (
    "    let out : LinkStatus :=\n"
    "      match headProbe with\n"
    "      | .reached sameTarget => classifyReached sameTarget\n"
    "      | .failed e =>\n"
    "          -- The first probe failed: decide whether to retry with a full fetch.\n"
    "          -- A status-carrying failure OR a redirect-budget exhaustion is\n"
    "          -- retried; any other failure is not.\n"
    "          if retriable e then\n"
    "            match getProbe with\n"
    "            | .reached sameTarget => classifyReached sameTarget\n"
    "            | .failed e2          => classifyUnhandled e2\n"
    "          else\n"
    "            classifyUnhandled e\n"
    "    return out\n"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the (retuned) proof without disturbing the obligation.
_IMPL_TOP = "    let out : LinkStatus :=\n"
assert _BASE.count(_IMPL_TOP) == 1, "impl top-line drifted from expected text"

# The FULL frozen proof body. A reshape whose do-block shape defeats the frozen
# script retunes THIS block (elided from the spec view); an admissibility case
# adds a `decide` arm to close its ground assert. Rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct resolveLinkStatus by\n  loom_solve\n"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_body):
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- WITNESSES. The sole `ensures` is a bare equality (no quantifier), so the
# ---- velvet tester route is available: `resolveLinkStatusTester <headProbe>
# ---- <getProbe> = false` says the extracted program's result violates the
# ---- postcondition at that concrete input pair. Checked in a file whose
# ---- `prove_correct` block has been stripped so no tactic script can mask the
# ---- verdict; the testers come from the directives inside the witness (present
# ---- on both the rival and the gold build by construction). Every argument is a
# ---- concrete literal so `decide` reduces fully; the head binds nothing.
_TESTER = (
    "extract_program_for resolveLinkStatus\n"
    "prove_precondition_decidable_for resolveLinkStatus\n"
    "prove_postcondition_decidable_for resolveLinkStatus\n"
    "derive_tester_for resolveLinkStatus\n\n"
)


def _witness(head, get):
    return _TESTER + (
        f"example : resolveLinkStatusTester ({head}) ({get}) = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-explicit-dispatch",
        "kind": "soundness",
        "expect": "verify",
        # Ports the sibling's pos-explicit-dispatch: instead of the `retriable`
        # guard, dispatch explicitly on the failure constructor — the
        # non-retriable failure reaches the top-level handler directly, and every
        # OTHER failure (the two retried shapes) runs the full-fetch retry. Same
        # decision value on every input. The do-block's shape defeats the frozen
        # `loom_solve`, so the proof is retuned to a constructor case-split whose
        # arms each close by `rfl`.
        "module": _impl_reproved(
            "    let out : LinkStatus :=\n"
            "      match headProbe with\n"
            "      | .reached b => classifyReached b\n"
            "      | .failed e =>\n"
            "          match e with\n"
            "          | .otherFailure => classifyUnhandled e\n"
            "          | _ =>\n"
            "            match getProbe with\n"
            "            | .reached b => classifyReached b\n"
            "            | .failed e2  => classifyUnhandled e2\n"
            "    return out\n",
            "prove_correct resolveLinkStatus by\n"
            "  loom_solve\n"
            "  rcases headProbe with b | e\n"
            "  · rfl\n"
            "  · cases e <;> rfl\n"),
        "rationale": "explicit per-constructor dispatch is behaviourally identical "
                     "to the `retriable` guard: the non-retriable failure "
                     "(otherFailure) reaches the top-level handler, and the two "
                     "retried shapes (statusError / redirectLoop) run the full-fetch "
                     "retry, so `out = resolveLinkStatusSpec headProbe getProbe` holds "
                     "on every input. A correct reshape must verify, else "
                     "SPEC-TOO-STRONG on the dispatch form. The proof is retuned "
                     "(elided from the spec view); the obligation statement is "
                     "byte-identical.",
    },
    {
        "id": "pos-negated-branch",
        "kind": "soundness",
        "expect": "verify",
        # Ports the sibling's pos-negated-branch: branch on the NEGATION of the
        # retry predicate with the arms reordered (the non-retried failure first).
        # Equivalent value on every input; the frozen `loom_solve` still closes it.
        "module": _impl(
            "    let out : LinkStatus :=\n"
            "      match headProbe with\n"
            "      | .reached b => classifyReached b\n"
            "      | .failed e =>\n"
            "          if !retriable e then classifyUnhandled e\n"
            "          else\n"
            "            match getProbe with\n"
            "            | .reached b => classifyReached b\n"
            "            | .failed e2  => classifyUnhandled e2\n"
            "    return out\n"),
        "rationale": "branch on the negation of the retry predicate with the arms "
                     "swapped (the non-retried failure taken first) computes the SAME "
                     "status on every input, so the ensures still holds; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on branch order. "
                     "Frozen proof script unchanged.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The sibling's admiss-f2p-shape asserts the
    # precondition ADMITS the F2P input and the gold logic resolves it to the
    # `working` success. This bundle has NO `require` clause, so the
    # precondition-admission half is degenerate (every input is in-domain). It is
    # re-aimed at the residual total-domain risk — that the post-image is
    # DEGENERATE at the interesting point — via an in-region assert pinning that
    # the F2P scenario resolves to `working` (and NOT `broken`) and that a
    # non-retriable first failure resolves to `broken`. The impl is kept verbatim
    # so the method's own obligation still discharges; the proof gains a `decide`
    # arm to clear the ground assert (allowed — the tactic body is elided). The
    # assert is LIVE: a false claim leaves an unsolved `decide` goal.
    # =====================================================================
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `admiss\n"
                "      (resolveLinkStatusSpec (Probe.failed RequestFailure.redirectLoop) (Probe.reached true) = LinkStatus.working\n"
                "       ∧ resolveLinkStatusSpec (Probe.failed RequestFailure.redirectLoop) (Probe.reached true) ≠ LinkStatus.broken\n"
                "       ∧ resolveLinkStatusSpec (Probe.failed RequestFailure.otherFailure) (Probe.reached true) = LinkStatus.broken))\n"
                + _IMPL_TOP),
            _PROOF,
            "prove_correct resolveLinkStatus by\n  loom_solve <;> decide\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: a first-probe redirect-budget exhaustion whose "
                     "full fetch reaches the target resolves to `working` (and NOT "
                     "`broken`) — the behaviour the failing test demands — while a "
                     "non-retriable first failure resolves to `broken`. The in-region "
                     "assert must discharge (else the obligation is degenerate at the "
                     "interesting point); the impl is kept verbatim so "
                     "`out = resolveLinkStatusSpec headProbe getProbe` discharges too. "
                     "Since the method is total there is no precondition to "
                     "over-strengthen; this defends against a hollow post-image.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input pair (both binders and every Probe/failure shape exercised)
    # and the refinement argument for why its faithful real counterpart would NOT
    # resolve the failing test (or would regress a PASS_TO_PASS test).
    # =====================================================================
    {
        "id": "weak-prepatch-no-redirect-retry",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image rival (sibling weak-prepatch-kind1-only): retry a
        # status-carrying failure but NOT a redirect-budget exhaustion. Correct on
        # the whole domain except a first-probe redirect-budget exhaustion, where
        # it reports the unhandled failure instead of the retried full fetch.
        "module": _impl(
            "    let out : LinkStatus :=\n"
            "      match headProbe with\n"
            "      | .reached b => classifyReached b\n"
            "      | .failed e =>\n"
            "          let retry : Bool :=\n"
            "            match e with\n"
            "            | .statusError _ => true\n"
            "            | .redirectLoop  => false\n"
            "            | .otherFailure  => false\n"
            "          if retry then\n"
            "            match getProbe with\n"
            "            | .reached b => classifyReached b\n"
            "            | .failed e2  => classifyUnhandled e2\n"
            "          else classifyUnhandled e\n"
            "    return out\n"),
        "refinement": "this is the pre-image classification: the first probe's "
                      "failure is retried with a full fetch ONLY for a status-carrying "
                      "failure, so a redirect-budget exhaustion escapes the retry and "
                      "reaches the top-level handler (reported broken). Its faithful "
                      "real counterpart is the unchanged repo, which reports the "
                      "redirect-looping target as broken instead of retrying it — "
                      "exactly the failing test, which now asserts the target is "
                      "reported working. It would NOT resolve.",
        "rationale": "REJECT from the ensures via `retriable` on the redirect-budget "
                     "exhaustion: the spec retries it (full fetch stands), the rival "
                     "does not (unhandled failure -> broken). Refuted at headProbe = "
                     "failed redirectLoop, getProbe = reached true, where the spec "
                     "gives `working` and the rival `broken`. If it verified => "
                     "SPEC-TOO-WEAK (the widened retry set is unenforced).",
        "witness": _witness("Probe.failed RequestFailure.redirectLoop",
                            "Probe.reached true"),
    },
    {
        "id": "weak-redirect-only-no-status-retry",
        "kind": "uniqueness",
        "expect": "reject",
        # Inverse partial miss (sibling weak-kind2-only): retry a redirect-budget
        # exhaustion but NOT a status-carrying failure. Wrong on a first-probe
        # status failure whose full fetch would succeed.
        "module": _impl(
            "    let out : LinkStatus :=\n"
            "      match headProbe with\n"
            "      | .reached b => classifyReached b\n"
            "      | .failed e =>\n"
            "          let retry : Bool :=\n"
            "            match e with\n"
            "            | .statusError _ => false\n"
            "            | .redirectLoop  => true\n"
            "            | .otherFailure  => false\n"
            "          if retry then\n"
            "            match getProbe with\n"
            "            | .reached b => classifyReached b\n"
            "            | .failed e2  => classifyUnhandled e2\n"
            "          else classifyUnhandled e\n"
            "    return out\n"),
        "refinement": "a real counterpart that dropped the status-carrying failure "
                      "from the retry set (retrying only the redirect-budget "
                      "exhaustion) would stop falling back to a full fetch for a "
                      "lightweight-probe status error — regressing the long-standing "
                      "fallback that a server which errors on the lightweight probe but "
                      "answers the full fetch relies on. It fails the PASS_TO_PASS "
                      "tests that pin that fallback. It would NOT resolve.",
        "rationale": "REJECT from the ensures via `retriable` on the status-carrying "
                     "failure: the spec retries it, the rival does not. Refuted at "
                     "headProbe = failed (statusError 0), getProbe = reached false, "
                     "where the spec gives `redirected` (the full fetch reached a "
                     "different location) and the rival `broken`. This is the ONLY "
                     "reject witness whose getProbe reached-bit is `false`, so it "
                     "varies that sub-binder. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("Probe.failed (RequestFailure.statusError 0)",
                            "Probe.reached false"),
    },
    {
        "id": "weak-overcatch-other-failure",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-retry (sibling weak-overcatch-kind3): retry on ANY first-probe
        # failure, including the non-retriable one. Correct on the retried shapes;
        # wrong on a first-probe otherFailure, where the authoritative failure is
        # masked by the full fetch.
        "module": _impl(
            "    let out : LinkStatus :=\n"
            "      match headProbe with\n"
            "      | .reached b => classifyReached b\n"
            "      | .failed _ =>\n"
            "          match getProbe with\n"
            "          | .reached b => classifyReached b\n"
            "          | .failed e2  => classifyUnhandled e2\n"
            "    return out\n"),
        "refinement": "a real counterpart that retried EVERY first-probe failure "
                      "(catching all request failures, not the narrow retry set) would "
                      "retry connection/TLS/decoding failures the full fetch cannot "
                      "fix, and would turn a genuinely-broken target `working` whenever "
                      "the full fetch happens to succeed for an unrelated reason. "
                      "SCOPE OF THIS CLAIM (measured, not asserted): the shipped "
                      "regression suite does NOT catch it — in every shipped failing "
                      "scenario both probes fail the same way, so widening the retry "
                      "set leaves each reported status unchanged, and it resolves the "
                      "failing test too. The divergence is therefore UNTESTED by the "
                      "suite and the argument is a faithfulness one: the modeled "
                      "behaviour keeps a non-retriable first failure AUTHORITATIVE "
                      "(mapping.md ties the retry set to a narrow, enumerated "
                      "membership test, not to `any failure`), so this rival is a "
                      "different behaviour that happens to be suite-indistinguishable. "
                      "It is a spec-strength rival, not a test-regression rival.",
        "rationale": "REJECT from the ensures: on a non-retriable first failure the "
                     "spec routes it to the top-level handler (otherFailure -> "
                     "broken), but the rival runs the full fetch. Refuted at headProbe "
                     "= failed otherFailure, getProbe = reached true, where the spec "
                     "gives `broken` and the rival `working`. If it verified => "
                     "SPEC-TOO-WEAK (the retry set is not bounded below).",
        "witness": _witness("Probe.failed RequestFailure.otherFailure",
                            "Probe.reached true"),
    },
    {
        "id": "weak-always-get",
        "kind": "uniqueness",
        "expect": "reject",
        # Degenerate echo (sibling weak-always-get): ignore the first probe
        # entirely and always report the full fetch's outcome. Violates the
        # never-retry-on-success edge (a reached first probe must stand).
        "module": _impl(
            "    let out : LinkStatus :=\n"
            "      match getProbe with\n"
            "      | .reached b => classifyReached b\n"
            "      | .failed e2  => classifyUnhandled e2\n"
            "    return out\n"),
        "refinement": "a real counterpart that dropped the first-probe short-circuit "
                      "and always issued the full fetch would double-request and report "
                      "the full fetch's outcome even where the lightweight probe "
                      "already reached the target — changing the reported status for "
                      "already-working targets and masking a non-retriable first "
                      "failure. It is not the modeled fix (which keeps the first "
                      "probe's outcome authoritative on success and on a non-retriable "
                      "failure) and would fail the PASS_TO_PASS first-probe-success "
                      "cases. It would NOT resolve.",
        "rationale": "REJECT from the ensures: on a reached first probe the spec "
                     "classifies IT (never consulting getProbe), but the rival returns "
                     "the full fetch's classification. Refuted at headProbe = reached "
                     "true, getProbe = failed otherFailure, where the spec gives "
                     "`working` and the rival `broken`. This is one of only two reject "
                     "witnesses whose headProbe is `reached`, varying that binder off "
                     "`failed`. If it verified => SPEC-TOO-WEAK (the first-probe "
                     "short-circuit is unpinned).",
        "witness": _witness("Probe.reached true",
                            "Probe.failed RequestFailure.otherFailure"),
    },
    {
        "id": "weak-reached-ignores-target",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (richer carrier): the sibling's kind-collapsed model reports a
        # reached first probe as the single success value 0; this carrier splits
        # `reached b` into working/redirected by the `sameTarget` bit. This rival
        # reports every reached first probe as `working`, ignoring that bit —
        # attacking the classifyReached sub-behaviour, which the sibling cannot
        # express and which no other rival probes.
        "module": _impl(
            "    let out : LinkStatus :=\n"
            "      match headProbe with\n"
            "      | .reached _ => LinkStatus.working\n"
            "      | .failed e =>\n"
            "          if retriable e then\n"
            "            match getProbe with\n"
            "            | .reached b => classifyReached b\n"
            "            | .failed e2  => classifyUnhandled e2\n"
            "          else classifyUnhandled e\n"
            "    return out\n"),
        "refinement": "a real counterpart that reported every reached target as "
                      "`working` regardless of whether the request was sent onward to a "
                      "different final location would report a redirected target as "
                      "working — regressing the redirect-detection the PASS_TO_PASS "
                      "follow-redirects cases pin (they assert a target whose final "
                      "location differs is reported redirected, not working). It would "
                      "NOT resolve.",
        "rationale": "REJECT from the ensures via `classifyReached`: a reached first "
                     "probe whose final location DIFFERS is `redirected`, not "
                     "`working`. Refuted at headProbe = reached false, getProbe = "
                     "reached true, where the spec gives `redirected` and the rival "
                     "`working`. This is the ONLY reject witness whose headProbe "
                     "reached-bit is `false`, so it varies that sub-binder. If it "
                     "verified => SPEC-TOO-WEAK (the reached-target classification is "
                     "unpinned).",
        "witness": _witness("Probe.reached false", "Probe.reached true"),
    },
    {
        "id": "weak-unhandled-drops-status-read",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (richer carrier): the sibling's kind-collapsed model does not
        # observe the top-level handler's status-code reading; this carrier's
        # classifyUnhandled reads 401 -> working / 503 -> ignored / else broken.
        # This rival drops the 401 read (reporting a 401 status failure as
        # broken), attacking classifyUnhandled and varying the status `code`
        # sub-binder no other rival moves.
        "module": _impl(
            "    let classifyTop : RequestFailure → LinkStatus := fun e =>\n"
            "      match e with\n"
            "      | .statusError 503 => LinkStatus.ignored\n"
            "      | .statusError _   => LinkStatus.broken\n"
            "      | .redirectLoop    => LinkStatus.broken\n"
            "      | .otherFailure    => LinkStatus.broken\n"
            "    let out : LinkStatus :=\n"
            "      match headProbe with\n"
            "      | .reached b => classifyReached b\n"
            "      | .failed e =>\n"
            "          if retriable e then\n"
            "            match getProbe with\n"
            "            | .reached b => classifyReached b\n"
            "            | .failed e2  => classifyTop e2\n"
            "          else classifyTop e\n"
            "    return out\n"),
        "refinement": "a real counterpart that dropped the authorization-challenge "
                      "read from the top-level handler would report a target answering "
                      "with that status as broken instead of working. SCOPE OF THIS "
                      "CLAIM (measured, not asserted): NO shipped regression test "
                      "exercises that status — the shipped handlers answer only "
                      "200/204/302/405/500 — so the suite does NOT catch this rival, "
                      "and it resolves the failing test too. The argument is therefore "
                      "a faithfulness one, not a test-regression one: the top-level "
                      "status reading is behaviour the change under test leaves "
                      "UNTOUCHED, and mapping.md §3 pins each of the two special status "
                      "reads to the real handler (validated by G-AX), so a rival that "
                      "drops one is unfaithful to the modeled surface even though the "
                      "suite is blind to it. Kept because it is the only rival that "
                      "attacks the handler's status read.",
        "rationale": "REJECT from the ensures via `classifyUnhandled`: a "
                     "status-carrying failure reaching the top-level handler with code "
                     "401 is `working`, not `broken`. Refuted at headProbe = failed "
                     "(statusError 0) [retried], getProbe = failed (statusError 401) "
                     "[reaches the handler], where the spec gives `working` and the "
                     "rival `broken`. This is the ONLY reject witness whose getProbe is "
                     "a `failed` probe carrying a specific status code, so it varies "
                     "the `code` sub-binder. If it verified => SPEC-TOO-WEAK (the "
                     "status-code reading is unpinned).",
        "witness": _witness("Probe.failed (RequestFailure.statusError 0)",
                            "Probe.failed (RequestFailure.statusError 401)"),
    },
    {
        "id": "weak-get-reached-ignores-target",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (clause gap). `classifyReached` is applied at TWO
        # distinct sites: to the first probe, and to the SECOND probe on the
        # retry path. weak-reached-ignores-target attacks only the first site,
        # so a rival that reads the reached bit correctly on the first probe and
        # drops it on the retried one was unattacked. This rival does exactly
        # that: on the retry path every reached full fetch is reported
        # `working`, so a retried probe that landed on a DIFFERENT final
        # location is misreported.
        "module": _impl(
            "    let out : LinkStatus :=\n"
            "      match headProbe with\n"
            "      | .reached b => classifyReached b\n"
            "      | .failed e =>\n"
            "          if retriable e then\n"
            "            match getProbe with\n"
            "            | .reached _ => LinkStatus.working\n"
            "            | .failed e2  => classifyUnhandled e2\n"
            "          else classifyUnhandled e\n"
            "    return out\n"),
        "refinement": "a real counterpart that, on the retry path only, reported a "
                      "reached target as `working` without comparing its final location "
                      "to the requested one would lose redirect detection for exactly "
                      "the targets that needed the full fetch. That IS caught by the "
                      "shipped suite: the scenario where the lightweight probe is "
                      "refused and the full fetch is then relocated is a shipped "
                      "regression test, and it asserts the relocated final location is "
                      "reported — this rival reports the plain success instead. It would "
                      "NOT resolve (it regresses that test).",
        "rationale": "REJECT from the ensures via `classifyReached` at its SECOND "
                     "application site: on the retry path a reached full fetch whose "
                     "final location differs is `redirected`, not `working`. Refuted at "
                     "headProbe = failed redirectLoop [retried], getProbe = reached "
                     "false, where the spec gives `redirected` and the rival `working`. "
                     "Complements weak-reached-ignores-target, which pins the bit only "
                     "at the FIRST site. If it verified => SPEC-TOO-WEAK (the "
                     "reached-target classification is unpinned on the retry path).",
        "witness": _witness("Probe.failed RequestFailure.redirectLoop",
                            "Probe.reached false"),
    },
    {
        "id": "weak-handler-reads-first-failure",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (clause gap). When the first probe fails retriably AND
        # the second probe also fails, the spec routes the SECOND failure to the
        # top-level handler. No existing rival attacks WHICH of the two failures
        # is read there: every prior rival either changes the retry set or the
        # handler's own reading. This rival keeps both of those intact and reads
        # the FIRST failure at the handler instead of the second.
        "module": _impl(
            "    let out : LinkStatus :=\n"
            "      match headProbe with\n"
            "      | .reached b => classifyReached b\n"
            "      | .failed e =>\n"
            "          if retriable e then\n"
            "            match getProbe with\n"
            "            | .reached b => classifyReached b\n"
            "            | .failed _   => classifyUnhandled e\n"
            "          else classifyUnhandled e\n"
            "    return out\n"),
        "refinement": "a real counterpart that reported the FIRST attempt's failure "
                      "when the retried attempt also failed would attribute the outcome "
                      "to a superseded probe: the status actually observed by the "
                      "authoritative second attempt would be discarded in favour of the "
                      "one that triggered the retry. SCOPE OF THIS CLAIM (measured): in "
                      "every shipped failing scenario both attempts fail identically, so "
                      "the suite does not distinguish them and this rival resolves the "
                      "failing test too — the argument is a faithfulness one. It is "
                      "nonetheless unfaithful to the modeled control flow, where the "
                      "retried attempt's failure is the one that propagates to the "
                      "handler (mapping.md §1: the handler classifies the exception that "
                      "escapes the retry, which is the second attempt's).",
        "rationale": "REJECT from the ensures: on a retried first failure whose second "
                     "probe ALSO fails, the spec applies `classifyUnhandled` to the "
                     "SECOND failure, not the first. Refuted at headProbe = failed "
                     "(statusError 401), getProbe = failed (statusError 0), where the "
                     "spec gives `broken` (reading the second failure) and the rival "
                     "`working` (reading the first). Attacks a clause no other rival "
                     "touches — it leaves both the retry set and the handler's reading "
                     "intact and changes only WHICH failure is read. If it verified => "
                     "SPEC-TOO-WEAK (the propagated-failure identity is unpinned).",
        "witness": _witness("Probe.failed (RequestFailure.statusError 401)",
                            "Probe.failed (RequestFailure.statusError 0)"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (2
# soundness positives, 1 admissibility, 4 uniqueness) plus 2 AXIOM_TESTS,
# over a probe_outcome(head_kind, get_kind) -> int surface whose failure carrier
# is COLLAPSED to a scalar kind {0,1,2,3}. This bundle models the SAME dispatch
# over a RICHER carrier: `Probe` (reached b | failed e) with an explicit
# `RequestFailure` split (statusError code | redirectLoop | otherFailure) and the
# reached-target and top-level-handler classifications spelled out. The value
# surface carries across intact; the richer carrier exposes two extra structural
# sub-behaviours (classifyReached, classifyUnhandled) the scalar-kind model
# cannot express, each getting an added binder-coverage rival.
#
#   sibling case               kind          -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-explicit-dispatch      soundness     -> pos-explicit-dispatch         PORTED (reproved)
#   pos-negated-branch         soundness     -> pos-negated-branch            PORTED
#   admiss-f2p-shape           admissibility -> admiss-f2p-shape              RE-AIMED
#   weak-prepatch-kind1-only   uniqueness    -> weak-prepatch-no-redirect-retry   PORTED
#   weak-kind2-only            uniqueness    -> weak-redirect-only-no-status-retry PORTED
#   weak-overcatch-kind3       uniqueness    -> weak-overcatch-other-failure  PORTED
#   weak-always-get            uniqueness    -> weak-always-get               PORTED
#   (—)                        uniqueness    -> weak-reached-ignores-target   ADDED (carrier)
#   (—)                        uniqueness    -> weak-unhandled-drops-status-read ADDED (carrier)
#   (—)                        uniqueness    -> weak-get-reached-ignores-target ADDED (audit)
#   (—)                        uniqueness    -> weak-handler-reads-first-failure ADDED (audit)
#   FRAME-MUTATION (vacuous)                 -> (none)                        VACUOUS
#   ax-sound-is_retryable      axiom         -> (none)                        DROPPED (G-AX lane)
#   ax-contain-reachable-kinds axiom         -> (none)                        DROPPED (G-AX lane)
#
# 6 ported, 1 re-aimed, 4 added, 1 vacuous, 2 axiom-lane dropped = 11 velvet SPEC
# cases (2 verify soundness + 1 verify admissibility + 8 reject uniqueness). Case
# count parity with nagini is NOT the target; coverage of the modeled surface is.
#
# ADDED BY AUDIT (2). An independent audit re-derived every rival and found two
#   clauses of resolveLinkStatusSpec that no shipped rival attacked, each closed
#   by a rival whose witness was SEEN to discriminate (rival exit 0, gold exit 1,
#   gold's failure being `decide` proving the tester proposition false):
#   * weak-get-reached-ignores-target — `classifyReached` is applied at TWO sites
#     (the first probe, and the retried probe). Only the first was pinned, so a
#     rival correct at the first site and wrong at the second was admissible.
#   * weak-handler-reads-first-failure — when both probes fail, WHICH failure
#     reaches the top-level handler was unpinned: every prior rival changed the
#     retry set or the handler's reading, none changed the failure's identity.
#   The audit also re-ran 3 further wrong impls (dropping the other special
#   status read, making the retry decision depend on the status code, and
#   swapping the two special status reads) and 3 correct reshapes (a single
#   simultaneous match on both binders, a factored per-probe classification
#   lambda, and a match on the retry predicate's Bool alongside getProbe). All 3
#   wrong impls were REJECTED and all 3 reshapes VERIFIED under the frozen proof
#   script, so no spec hole in either direction was found; those probes are not
#   shipped as cases because the two above already pin their clauses.
#
# REFINEMENT PROSE CORRECTED BY AUDIT (2). Two rivals claimed a PASS_TO_PASS
#   regression the shipped suite does not actually produce. Measured by
#   simulating every shipped scenario through both the frozen spec and the rival:
#   weak-overcatch-other-failure and weak-unhandled-drops-status-read are BOTH
#   suite-indistinguishable from the frozen behaviour (in every shipped failing
#   scenario both probes fail the same way, and no shipped handler answers either
#   of the two specially-read statuses). Both rivals are still genuinely WRONG
#   against the spec and are kept — only their refinement text was corrected to
#   state a faithfulness argument and to record the measured limit of the suite,
#   instead of asserting a regression that does not occur.
#
# PORTED (positives): pos-explicit-dispatch dispatches on the failure constructor
#   (non-retriable failure to the handler, the two retried shapes to the full
#   fetch) — the reshape whose do-block defeats the frozen `loom_solve`, so its
#   proof is retuned to a constructor case-split (verified to build, exit 0).
#   pos-negated-branch branches on the negated retry predicate with the arms
#   swapped; the frozen `loom_solve` still closes it (verified, exit 0).
# RE-AIMED (admiss-f2p-shape): the sibling asserts the precondition admits the
#   F2P input and the gold logic resolves it to the working success. This bundle
#   has NO `require` clause, so the admission half is degenerate; re-aimed at the
#   residual risk of a DEGENERATE post-image via a live in-region assert pinning
#   the F2P scenario to `working` (and NOT `broken`) and a non-retriable failure
#   to `broken`. Impl kept verbatim; proof gains a `decide` arm (verified, exit 0).
# VACUOUS (frame-mutation): the sibling records its own frame lane as vacuous
#   (both inputs are pass-by-value scalars). On this backend it is vacuous for the
#   stronger reason that Lean/Velvet are referentially transparent: both `Probe`
#   inputs are immutable values, this bundle declares no `mut` binder, there is no
#   heap and no aliasing. No read-only input to overwrite, no substitute probe.
#   Reported, not fabricated.
# PORTED (the four value rivals): the sibling's is_retryable(kind)==(kind∈{1,2})
#   maps to `retriable` over the RequestFailure split (statusError↔kind 1,
#   redirectLoop↔kind 2, otherFailure↔kind 3). weak-prepatch-kind1-only ->
#   weak-prepatch-no-redirect-retry (retry statusError only — the pre-image, the
#   F2P discriminator). weak-kind2-only -> weak-redirect-only-no-status-retry
#   (retry redirectLoop only — regresses the existing fallback). weak-overcatch-
#   kind3 -> weak-overcatch-other-failure (retry everything — masks authoritative
#   failures). weak-always-get -> weak-always-get (ignore the first probe). Each
#   carries a witness SEEN to discriminate (two real builds: rival exit 0, gold
#   exit 1).
# ADDED (2, carrier-driven): the scalar-kind model collapses a reached probe to
#   the single success value 0 and does not observe the top-level status-code
#   read, so it has no analogue for classifyReached or classifyUnhandled.
#   weak-reached-ignores-target attacks classifyReached (a redirected reach must
#   NOT be reported working) — refutable only via the reached `sameTarget` bit.
#   weak-unhandled-drops-status-read attacks classifyUnhandled (a 401 status
#   failure at the handler must be working, not broken) — refutable only via the
#   status `code` sub-binder. Each closes a structural clause of
#   resolveLinkStatusSpec as independently attacked.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 8 distinct input pairs,
# no two rivals refuted at the same point):
#   headProbe — reached true (weak-always-get), reached false
#               (weak-reached-ignores-target), failed redirectLoop
#               (weak-prepatch-no-redirect-retry, weak-get-reached-ignores-
#               target), failed statusError (weak-redirect-only-no-status-retry,
#               weak-unhandled-drops-status-read, weak-handler-reads-first-
#               failure), failed otherFailure (weak-overcatch-other-failure):
#               BOTH Probe constructors, BOTH reached bits, ALL three failure
#               shapes, and the failure's status `code` moved off 0 (weak-
#               handler-reads-first-failure pins headProbe at statusError 401).
#   getProbe  — reached true (weak-prepatch-no-redirect-retry, weak-overcatch-
#               other-failure, weak-reached-ignores-target), reached false
#               (weak-redirect-only-no-status-retry, weak-get-reached-ignores-
#               target), failed otherFailure (weak-always-get), failed
#               statusError 401 (weak-unhandled-drops-status-read), failed
#               statusError 0 (weak-handler-reads-first-failure): both Probe
#               constructors, both reached bits, and the status `code` varied
#               across BOTH a specially-read value and a plain one — so the
#               handler's reading is discriminated from its mere presence.
#   Every independent sub-behaviour of resolveLinkStatusSpec is attacked: the
#   retry-set membership on each failure shape (prepatch / redirect-only /
#   overcatch), the never-retry-on-success edge (always-get), the reached-target
#   classification at BOTH of its application sites (reached-ignores-target for
#   the first probe, get-reached-ignores-target for the retried one), the
#   top-level status read (unhandled-drops-status-read), and WHICH of two
#   failures reaches that handler (handler-reads-first-failure). No two rivals
#   are refuted at the same point.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (retriable/classifyReached/classifyUnhandled are deep models; the
#   RequestFailure↔requests-exception-hierarchy binding is an A-reference checked
#   by axiom_check.py / G-AX), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
