"""properties.py — G-PBT falsification battery for django__django-13821 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct verifyVersion`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  verifyVersion (info : List Nat) (versionStr : List Char)
      return (out : Except (List Char) Unit)
    ensures out = checkSpec info versionStr

The method is a start-up guard on a reported version tuple. It FAILS with a
diagnostic exactly when the reported version sorts strictly below the required
minimum, and SUCCEEDS (with no value) otherwise. The pure region pins the whole
outcome as a total function of the method's own two inputs:

  checkSpec info versionStr
    = if lexLt info requiredVersion then Except.error (errorMessage versionStr)
      else Except.ok ()

with ``requiredVersion = [3, 9, 0]``, ``lexLt`` the lexicographic strict order on
the version tuple (a prefix ranks below its extension), and ``errorMessage`` the
diagnostic that echoes the reported version STRING. So the sole ensures pins TWO
independent behaviours:

  * (D) the DECISION — error-vs-ok is fixed in BOTH directions by
        ``lexLt info requiredVersion``: every strictly-below tuple MUST fail,
        every at-or-above tuple MUST succeed. There is no slack; a rival that
        misclassifies ANY tuple on EITHER side violates the ensures.
  * (M) the diagnostic PAYLOAD — on the failing branch the surfaced value is
        ``errorMessage versionStr``, which carries the reported version string
        through unchanged. A rival that decides correctly but drops / mangles the
        echoed string violates the ensures on the payload half.

Both INPUT binders are free (no ``require`` clause) and the post-image must hold
for EVERY value of each:
  * ``info``       — the reported version tuple; drives the decision (D).
  * ``versionStr`` — the reported version string; carried by the payload (M).

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rival keeps the gold body verbatim then writes back into a
    read-only sequence input carrying only a fractional heap permission
    (``Acc(list_pred(version),1/2)``) and is rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: every parameter
    is an immutable value, this bundle declares no ``mut`` binder, there is no
    heap and no aliasing. There is no read-only input to overwrite and no
    permission system to trip, so the class is vacuous. No substitute is
    fabricated.
  * TERMINATION / NON-TERMINATION — NOT LANDABLE AS A REJECT CASE, but for a
    reason opposite to the one an earlier revision of this docstring gave.
    CORRECTION: this bundle runs under ``loom.semantics.termination "total"``,
    NOT ``"partial"``. The frozen ``set_option`` says ``"total"``; the previous
    text asserted ``"partial"`` and derived its whole disposition from that, and
    since the two settings invert the correct disposition, both halves of that
    reading were wrong. Under ``"total"`` a diverging rival does NOT verify
    vacuously — it is rejected outright, measured: a ``while tooOld`` loop with
    no decreasing annotation gives ``error: Decreasing annotations are required
    in total correctness semantics`` (exit 1).
    Landing it as an ``expect="reject"`` case nevertheless fails, on the WITNESS
    half rather than the outcome half, and this is the demonstrated reason it is
    not shipped. The rejection is a whole-file linter error, so the witness file
    built from that rival carries the SAME error, and the tester never becomes
    decidable: ``decide`` reports ``Decidable instance did not reduce`` and
    ``decide +kernel`` / ``simp [verifyVersionTester, …]`` / ``unfold`` all fail
    the same way (four tactic shapes tried, all exit 1). The gate's own
    ``_check_witness`` was run on the case and returns ``witness-unproven``, an
    inconclusive outcome — NOT a pass. A ``witness_reference`` does not rescue
    it either: the reference replaces the GOLD side, while the half that fails
    here is the RIVAL side. So the class is genuinely unlandable on this
    carrier: the rival is rejected for a reason no per-input refutation can
    attribute, because there is no input at which the rival returns a wrong
    VALUE — it returns gold's value or none at all.
    A second residual was once recorded here as a real spec hole: a loop that
    supplies a measure the checker accepts while never exiting, making the whole
    post-loop continuation vacuous and laundering an arbitrary return value. It is
    RETRACTED, by rebuilding the exact shape it named. ``while true / done_with
    False / decreasing k`` with body ``k := k + 1`` is REJECTED (exit 1) on the
    measure's own descent goal: ``case «decreasing_1: k»``, residual
    ``⊢ k + 1 < k``. The checker does not merely demand a measure under ``total``,
    it discharges the descent, so no unchecked measure is available to make the
    continuation unreachable. Nothing is escalated on this axis and no hole is open.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is ``checkSpec info versionStr``, and ``checkSpec`` / ``lexLt`` /
    ``requiredVersion`` / ``errorMessage`` are concrete ``def``s in the ``pure``
    region computing the outcome from the method's own arguments (the ``axioms``
    region is empty; there is no opaque answer key to echo). The unique satisfier
    IS the grounded decision-plus-payload, so there is no wrong echo to build;
    the honest controls are the cheapest faithful reshapes (the ``pos-*`` cases).
  * CONTROL-FLOW-EFFECT — captured by the value abstraction, not lost to it. The
    single behavioural effect (fail-vs-succeed) is exactly the ``Except`` carrier
    of the return value: ``Except.error`` ↔ the diagnostic is raised,
    ``Except.ok ()`` ↔ normal return. So the fail/succeed fork is fully observable
    to the ensures; the always-fail / always-succeed rivals are its
    discriminators.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. A rival can be correct on most of
    the version domain yet diverge on a sub-domain: the major-only rival is right
    on the 2.x/4.x major boundary but wrong on the 3.8-vs-3.9 minor boundary
    (the F2P), and the pre-threshold rival is right below the old minimum but
    wrong on the versions between the two thresholds.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop):
its extracted program reduces fully under ``decide``. Each reject rival carries
a machine-checked refutation ``witness`` — a Velvet tester statement
``verifyVersionTester <info> <versionStr> = false`` at ONE concrete input,
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. (``prove_postcondition_decidable_for`` cannot on its
own synthesize ``DecidableEq`` for the ``Except (List Char) Unit`` return
carrier, so each witness first ``deriving instance DecidableEq for Except`` — an
instance, not an assumption: no ``axiom`` / ``sorry`` / ``native_decide`` is
involved, and the frozen solution rejects the witnesses all the same.) Both
halves were checked out-of-band with ``scripts/lean_verify.sh``: every witness
ELABORATES against its rival and FAILS (``decide`` proves the proposition false)
against the frozen solution, so each rejection is a genuine spec refutation and
not mechanical tactic breakage.

The audit additionally ran the FORGERY test on all eight reject cases, because a
gold-side exit code is evidence only if it TRACKS THE CLAIM. For each case the
witness was rebuilt with its claim flipped (``= false`` → ``= true``) and built
against both impls. Every case inverted exactly: the flipped claim VERIFIES
against the frozen solution (exit 0) and FAILS against the rival (exit 1, with
``decide`` proving the flipped proposition false). So on each of these inputs the
kernel genuinely evaluates the tester and gold's verdict is the opposite of the
rival's — none of these rejections rests on a stuck reduction, a missing
identifier or a type error, and each gold-side signature is a plain evaluation
refutation naming the concrete input.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no
deep-model reference; ``lexLt`` / ``errorMessage`` are I-ops (language
primitives modeled directly), refinement-checked by ``conformance_check.py``
(G-CONF), not axiomatized. Nothing in the proof rests on an axiom, and this gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13821"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block (and, for reshapes/admissibility, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- Fail with the diagnostic exactly when the reported version sorts below the\n"
    "    -- required minimum; otherwise succeed.\n"
    "    let tooOld : Bool := lexLt info [3, 9, 0]\n"
    "    let out : Except (List Char) Unit :=\n"
    "      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()\n"
    "    return out\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct verifyVersion by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `verifyVersionTester <info> <versionStr> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped. The
# ---- `Except (List Char) Unit` return carrier needs a decidable-equality
# ---- instance for the tester derivation; it is derived, not assumed.
_DEC = "deriving instance DecidableEq for Except\n\n"
_TESTER = (_DEC +
           "extract_program_for verifyVersion\n"
           "prove_precondition_decidable_for verifyVersion\n"
           "prove_postcondition_decidable_for verifyVersion\n"
           "derive_tester_for verifyVersion\n\n")


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the decision-plus-payload value
    # identical and only reshapes the executable surface, so the reproof stays
    # a `loom_solve` away from the frozen script.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the below-threshold guard and swap the two arms
        # (succeed first). Same outcome on every input — `!tooOld` succeeds
        # exactly where `tooOld` failed, and the failing arm still surfaces the
        # same diagnostic payload. Proof retuned (the do-block changed shape).
        "module": _impl_reproved(
            "    let notOld : Bool := ! lexLt info [3, 9, 0]\n"
            "    let out : Except (List Char) Unit :=\n"
            "      if notOld then Except.ok () else Except.error (errorMessage versionStr)\n"
            "    return out",
            "prove_correct verifyVersion by\n  loom_solve <;> simp_all [checkSpec]"),
        "rationale": "negating the below-threshold guard and swapping the two "
                     "arms computes the SAME outcome on every input (`!tooOld` "
                     "succeeds exactly where `tooOld` fails, and the failing arm "
                     "surfaces the same `errorMessage versionStr`), so "
                     "`out = checkSpec info versionStr` still holds; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on branch order.",
    },
    {
        "id": "pos-required-version-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: name the threshold through the pure `requiredVersion` selector
        # (definitionally `[3, 9, 0]`) instead of the inline literal, and bind
        # the diagnostic to a typed local before surfacing it. Same value flow;
        # the reproof stays a `loom_solve` away.
        "module": _impl_reproved(
            "    let tooOld : Bool := lexLt info requiredVersion\n"
            "    let msg : List Char := errorMessage versionStr\n"
            "    let out : Except (List Char) Unit :=\n"
            "      if tooOld then Except.error msg else Except.ok ()\n"
            "    return out",
            "prove_correct verifyVersion by\n  loom_solve <;> simp_all [checkSpec]"),
        "rationale": "naming the threshold through the pure `requiredVersion` "
                     "selector (definitionally the same tuple) and binding the "
                     "diagnostic to a typed local leaves the decision and the "
                     "surfaced payload identical, so "
                     "`out = checkSpec info versionStr` is unchanged; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on threshold "
                     "naming / payload binding.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). The
    # residual admissibility risk on a total-domain spec is that the decision
    # is DEGENERATE at the interesting point — a threshold that never separated
    # the below-case from the boundary would read like a live one. This case
    # discharges an in-region assert pinning that the required threshold
    # genuinely distinguishes the F2P below-case from the at-threshold boundary:
    # the F2P tuple sorts strictly below, the boundary tuple does not. The rest
    # of the impl is kept verbatim so the method's own obligation still
    # discharges; the proof is retuned to also close the assert VC.
    # =====================================================================
    {
        "id": "admiss-threshold-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # STRENGTHENED by the audit. The previous form asserted only the two
        # `lexLt` facts — the GUARD's non-degeneracy. That leaves the obligation
        # itself untouched: the analogue of PRECOND-TOO-STRONG on a total carrier
        # is the POST-IMAGE being unsatisfiable at an F2P-shaped input, and a
        # guard-only assert cannot see that (a spec whose `checkSpec` was
        # unsatisfiable at that point would still pass a `lexLt`-only probe). So
        # the assert now discharges `checkSpec` ITSELF, by evaluation, at both
        # F2P-shaped points — the below-case with its full diagnostic payload
        # (`errorMessage` applied to the reported string) and the at-threshold
        # boundary — before the frozen obligation is closed verbatim. The two
        # `lexLt` conjuncts are kept so the non-degeneracy claim still holds.
        # Checked load-bearing: falsifying ONE conjunct (the boundary made to
        # demand an error) makes the same proof FAIL (exit 1), so the assert is
        # discharged rather than skipped.
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (checkSpec [3, 8, 11, 1] \"3.8.11.1\".toList\n"
            "         = Except.error (errorMessage \"3.8.11.1\".toList) ∧\n"
            "       checkSpec [3, 9, 0] \"3.9.0\".toList = Except.ok () ∧\n"
            "       lexLt [3, 8, 11, 1] requiredVersion = true ∧\n"
            "       lexLt [3, 9, 0] requiredVersion = false))\n"
            "    let tooOld : Bool := lexLt info [3, 9, 0]\n"
            "    let out : Except (List Char) Unit :=\n"
            "      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()\n"
            "    return out",
            "prove_correct verifyVersion by\n"
            "  loom_solve <;> simp [checkSpec, errorMessage, lexLt]"),
        "rationale": "the obligation is SATISFIABLE, and non-degenerate, at the "
                     "F2P-shaped input. The assert discharges the post-image "
                     "`checkSpec` itself by evaluation at two concrete points: "
                     "at the below-case it really does equal "
                     "`Except.error (errorMessage <the reported string>)` — the "
                     "decision AND the payload, so neither half is vacuous — and "
                     "at the at-threshold boundary it really does equal "
                     "`Except.ok ()`. The two `lexLt` conjuncts add that the "
                     "threshold genuinely forks on that boundary. If the "
                     "post-image were unsatisfiable at an F2P-shaped input (the "
                     "total-carrier analogue of PRECOND-TOO-STRONG) this assert "
                     "could not discharge. The impl is kept verbatim so the "
                     "ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful
    # real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-always-succeed",
        "kind": "uniqueness",
        "expect": "reject",
        # Never fails — always takes the success path (the fail fork is removed).
        "module": _impl(
            "    let out : Except (List Char) Unit := Except.ok ()\n"
            "    return out"),
        "refinement": "always succeeding is what a real patch that DELETED the "
                      "guard (or its raise) would do — it never rejects any "
                      "reported version, so a runtime below the required minimum "
                      "passes start-up. It fails the F2P test, which reports a "
                      "below-minimum version and asserts the diagnostic IS "
                      "raised. It would NOT resolve.",
        "rationale": "REJECT from `out = checkSpec info versionStr` on the "
                     "decision (D): for a strictly-below tuple the post-image "
                     "demands `Except.error (errorMessage versionStr)` but the "
                     "rival succeeds. Refuted at a below-minimum tuple with a "
                     "major component under 3 — a point where the major-only "
                     "rival is CORRECT, so this rival carries its own separating "
                     "input rather than sharing one.",
        "witness": _witness(
            'verifyVersionTester [2, 0, 0] "x".toList'),
    },
    {
        "id": "weak-always-fail",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual: always fails — every input takes the fail path (the success
        # fork is removed), surfacing the diagnostic payload the spec would carry
        # only on the below-threshold branch.
        "module": _impl(
            "    let out : Except (List Char) Unit := Except.error (errorMessage versionStr)\n"
            "    return out"),
        "refinement": "always failing is what a real patch that hard-coded the "
                      "guard true (or compared against an impossibly-high "
                      "minimum) would do — it rejects EVERY reported version, "
                      "including the modern runtimes the project supports. It "
                      "fails every start-up path requiring the guard to succeed "
                      "on an in-spec version (the boundary tuple, or newer). It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = checkSpec info versionStr` on the "
                     "decision (D, dual): for an at-or-above tuple the post-image "
                     "demands `Except.ok ()` but the rival fails. Refuted at the "
                     "at-threshold boundary tuple (with an empty version string, "
                     "varying the `versionStr` binder against the other "
                     "witnesses).",
        "witness": _witness(
            'verifyVersionTester [3, 9, 0] "".toList'),
    },
    {
        "id": "weak-major-only",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: decides the fail/succeed fork from the MAJOR component
        # alone (fail iff the tuple is empty, or its head is below 3). Correct on
        # the major-version sub-domain — a 2.x tuple fails, a 4.x tuple succeeds —
        # but on any 3.x tuple it ALWAYS succeeds, so it is wrong on the
        # minor-version boundary the required threshold introduces.
        "module": _impl(
            "    let tooOld : Bool := match info with\n"
            "      | []      => true\n"
            "      | h :: _  => h < 3\n"
            "    let out : Except (List Char) Unit :=\n"
            "      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()\n"
            "    return out"),
        "refinement": "comparing only the MAJOR component to 3 is what a real "
                      "patch guarding on `version[0] < 3` would do. It is correct "
                      "on the major-version sub-domain (a 2.x runtime rejected, a "
                      "4.x accepted) but ALWAYS accepts any 3.x runtime, so it "
                      "does NOT reject a 3.x tuple below the required minimum — "
                      "including the F2P discriminator. It fails the F2P test "
                      "(expects the diagnostic on a 3.x below-minimum version). A "
                      "genuine PARTIAL-DOMAIN break on the minor-version "
                      "boundary; it would NOT resolve.",
        "rationale": "REJECT from `out = checkSpec info versionStr` on the "
                     "decision (D): for a 3.x tuple below the minimum the rival "
                     "sets `tooOld = false` (head 3, not < 3) and succeeds, but "
                     "the post-image demands the diagnostic. PARTIAL-DOMAIN: the "
                     "rival pins only the major-component sub-domain, dropping "
                     "the minor/patch ordering the spec requires. Refuted at a "
                     "3.x below-minimum tuple — the sub-domain where it is wrong "
                     "and both boundary rivals above are not.",
        "witness": _witness(
            'verifyVersionTester [3, 0, 0] "y".toList'),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: compares against the OLD, lower threshold
        # instead of the required one. Correct below the old threshold, wrong on
        # the versions that sort between the two thresholds — exactly the range
        # the required-minimum change newly rejects.
        "module": _impl(
            "    let tooOld : Bool := lexLt info [3, 8, 3]\n"
            "    let out : Except (List Char) Unit :=\n"
            "      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()\n"
            "    return out"),
        "refinement": "this IS the pre-patch behaviour: the guard compares "
                      "against the OLD, lower threshold. Its faithful real "
                      "counterpart is the unchanged repo, which ACCEPTS a version "
                      "at or above the old threshold but below the required one — "
                      "exactly the range the F2P version lives in, and exactly "
                      "the bug the required-minimum change fixes. The F2P test "
                      "now asserts the diagnostic IS raised on that version. It "
                      "would NOT resolve — the precise change the spec senses "
                      "(G-DIFF).",
        "rationale": "REJECT from `out = checkSpec info versionStr` on the "
                     "decision (D): the rival's `tooOld` reflects the OLD "
                     "threshold, so for a tuple at/above the old minimum but "
                     "below the required one it succeeds, where the post-image "
                     "(pinned to `lexLt info requiredVersion`) demands the "
                     "diagnostic. Refuted at the F2P below-minimum tuple. "
                     "Supporting near-miss carrying the strongest refinement (it "
                     "is the literal pre-patch).",
        "witness": _witness(
            'verifyVersionTester [3, 8, 11, 1] "z".toList'),
    },
    {
        "id": "weak-message-drops-version",
        "kind": "uniqueness",
        "expect": "reject",
        # PAYLOAD rival (M): the fail/succeed DECISION is exactly right — the
        # frozen guard is kept verbatim — but the surfaced diagnostic omits the
        # reported version string instead of echoing it. Built to abuse
        # `versionStr`, the free input the payload carries: every decision rival
        # above surfaces the correct `errorMessage versionStr` on its fail branch
        # (or never reaches it), so none of them attests that the payload carries
        # `versionStr` through. This one is wrong exactly because it drops it.
        "module": _impl(
            "    let tooOld : Bool := lexLt info [3, 9, 0]\n"
            "    let out : Except (List Char) Unit :=\n"
            "      if tooOld then\n"
            "        Except.error (\"SQLite 3.9.0 or later is required (found \".toList\n"
            "                        ++ \").\".toList)\n"
            "      else Except.ok ()\n"
            "    return out"),
        "refinement": "a counterpart whose diagnostic names the requirement but "
                      "omits the reported version renders the surfaced failure "
                      "without the version actually found, so the F2P test — "
                      "which asserts the EXACT diagnostic text, reported version "
                      "included — still fails on the message comparison even "
                      "though the reject decision is right. It would NOT resolve.",
        "rationale": "REJECT from `out = checkSpec info versionStr` on the "
                     "payload (M): the failing branch of the post-image surfaces "
                     "`errorMessage versionStr`, which splices the reported "
                     "version string into the diagnostic; the rival surfaces the "
                     "diagnostic with that string dropped, so at a below-minimum "
                     "tuple with a NON-EMPTY version string the two messages "
                     "differ. Refuted at a below-minimum tuple whose version "
                     "string is non-empty — the point that makes the post-image's "
                     "dependence on `versionStr` observable (every decision rival "
                     "holds this half correct).",
        "witness": _witness(
            'verifyVersionTester [3, 8, 2] "w".toList'),
    },
    # --- added by the audit (attack D): three sub-domains the five rivals above
    # --- leave unattacked. Each was built as a NEW wrong impl, confirmed
    # --- rejected, and given a witness whose gold-side failure is a plain
    # --- `decide` evaluation refutation with a clean forgery inversion.
    {
        "id": "weak-boundary-nonstrict",
        "kind": "uniqueness",
        "expect": "reject",
        # OFF-BY-ONE at exactly the threshold: compares NON-strictly, by negating
        # the reversed comparison (`!lexLt requiredVersion info` is "info ≤
        # required"), so the at-threshold tuple is misclassified as too old. This
        # is the ONE point every rival above gets right: `weak-always-fail` also
        # errs at [3,9,0] but errs EVERYWHERE, and the three partial-domain
        # rivals all classify the boundary correctly. So no existing witness
        # attests that the comparison is STRICT rather than non-strict — the
        # single most likely real-world mistake in a version guard.
        "module": _impl(
            "    let tooOld : Bool := ! lexLt [3, 9, 0] info\n"
            "    let out : Except (List Char) Unit :=\n"
            "      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()\n"
            "    return out"),
        "refinement": "a counterpart written with `<=` where the requirement is "
                      "`<` rejects the EXACT minimum the project declares "
                      "supported, so a runtime at precisely the required version "
                      "fails start-up. It breaks the start-up paths that must "
                      "succeed at the declared minimum while still passing the "
                      "below-minimum case, so it would NOT resolve.",
        "rationale": "REJECT from `out = checkSpec info versionStr` on the "
                     "decision (D) at the BOUNDARY: the post-image is pinned to "
                     "the STRICT order `lexLt info requiredVersion`, which is "
                     "false at the threshold tuple and demands `Except.ok ()`; "
                     "the rival's non-strict test is true there and surfaces the "
                     "diagnostic. Refuted at the at-threshold tuple — the one "
                     "point that separates strict from non-strict, and the only "
                     "input where this rival differs from the frozen impl at "
                     "all, so its rejection attributes to strictness alone.",
        "witness": _witness(
            'verifyVersionTester [3, 9, 0] "3.9.0".toList'),
    },
    {
        "id": "weak-pad-short-tuple",
        "kind": "uniqueness",
        "expect": "reject",
        # PREFIX / ARITY sub-domain: right-pads the reported tuple with zeros
        # before comparing. On any tuple already at least as long as the
        # threshold this is identical to the frozen impl, so all five rivals
        # above are blind to it; it diverges only on a SHORT tuple, where the
        # spec's prefix rule applies. `lexLt` ranks a strict prefix BELOW its
        # extension, so a two-component tuple at the threshold's first two
        # components sorts below the threshold; padded to three components it
        # compares equal and is wrongly accepted.
        "module": _impl(
            "    let tooOld : Bool := lexLt (info ++ [0, 0, 0]) [3, 9, 0]\n"
            "    let out : Except (List Char) Unit :=\n"
            "      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()\n"
            "    return out"),
        "refinement": "a counterpart that normalises the reported tuple to a "
                      "fixed arity by zero-padding before comparing treats a "
                      "shorter reported version as though its missing components "
                      "were zeros, which silently accepts a runtime the ordering "
                      "places below the minimum. It misclassifies exactly the "
                      "short-tuple sub-domain and would NOT resolve.",
        "rationale": "REJECT from `out = checkSpec info versionStr` on the "
                     "decision (D) over the PREFIX sub-domain: `lexLt` ranks a "
                     "strict prefix below its extension, so at a two-component "
                     "tuple matching the threshold's leading components the "
                     "post-image demands the diagnostic; the rival's padded "
                     "operand compares equal and succeeds. Refuted at that "
                     "short tuple — a sub-domain no other rival reaches, since "
                     "every existing witness uses a tuple at least as long as "
                     "the threshold, where padding is a no-op.",
        "witness": _witness(
            'verifyVersionTester [3, 9] "3.9".toList'),
    },
    {
        "id": "weak-message-names-old-threshold",
        "kind": "uniqueness",
        "expect": "reject",
        # PAYLOAD rival (M), second axis. `weak-message-drops-version` attacks
        # the ECHOED input; this attacks the FIXED text around it. The decision
        # is exactly right and `versionStr` IS carried through, so the only
        # divergence is the required-version stated in the diagnostic. Without
        # this, nothing attests that the message names the threshold the spec
        # pins rather than some other one.
        "module": _impl(
            "    let tooOld : Bool := lexLt info [3, 9, 0]\n"
            "    let out : Except (List Char) Unit :=\n"
            "      if tooOld then\n"
            "        Except.error (\"SQLite 3.8.3 or later is required (found \".toList\n"
            "                        ++ versionStr ++ \").\".toList)\n"
            "      else Except.ok ()\n"
            "    return out"),
        "refinement": "a counterpart whose diagnostic still names the OLD "
                      "required version, while the guard itself enforces the new "
                      "one, surfaces a message that contradicts the check it "
                      "reports. The F2P test asserts the EXACT diagnostic text, "
                      "so it fails on the message comparison even though the "
                      "reject decision is right. It would NOT resolve.",
        "rationale": "REJECT from `out = checkSpec info versionStr` on the "
                     "payload (M), text axis: the failing branch of the "
                     "post-image is `errorMessage versionStr`, whose fixed "
                     "prefix names the required version the spec pins; the rival "
                     "keeps the echoed `versionStr` but states a DIFFERENT "
                     "required version, so the two messages differ on every "
                     "below-minimum input. Refuted at the F2P below-case. "
                     "Complements `weak-message-drops-version`: that one drops "
                     "the echoed input, this one corrupts the surrounding text, "
                     "and neither refutes the other.",
        "witness": _witness(
            'verifyVersionTester [3, 8, 11, 1] "3.8.11.1".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness — one of which is the mandatory frame-
# mutation rival, one the diverging-reject rival). Every one is accounted for
# below. The sibling models the same start-up guard over a single READ-ONLY
# sequence input carrying a fractional heap permission, with the below-threshold
# decision computed by a verified `while` loop and a `MustTerminate` obligation;
# this backend models the same guard STRAIGHT-LINE over a `List Nat`, with the
# ordering as the pure `lexLt` and the outcome (incl. the diagnostic payload) as
# `checkSpec`. The decision surface carries across intact; the permission
# surface, the loop, and the termination obligation do not exist here — but this
# backend ADDS an observable the sibling's `None`-returning guard does not model:
# the diagnostic PAYLOAD (`errorMessage versionStr`), which gets its own rival.
#
#   sibling case            -> here                              disposition
#   -----------------------------------------------------------------------
#   pos-branch-reorder      -> pos-branch-reorder                PORTED (reshaped
#                                                                 straight-line)
#   admiss-reads            -> admiss-threshold-nondegenerate    RE-AIMED
#   frame-mut-write         -> (none)                            VACUOUS
#   weak-always-accept      -> weak-always-succeed               PORTED
#   weak-always-reject      -> weak-always-fail                  PORTED
#   weak-major-only         -> weak-major-only                   PORTED
#   weak-diverge-reject     -> (none)                            UNLANDABLE
#                                                                 (witness half;
#                                                                  see below)
#   weak-prepatch           -> weak-prepatch                     PORTED
#   (no sibling)            -> pos-required-version-local        ADDED (2nd pos.)
#   (no sibling)            -> weak-message-drops-version        ADDED (binder cov.)
#   (no sibling)            -> weak-boundary-nonstrict           ADDED (audit: D)
#   (no sibling)            -> weak-pad-short-tuple              ADDED (audit: D)
#   (no sibling)            -> weak-message-names-old-threshold  ADDED (audit: D)
#
# 5 ported, 1 re-aimed, 1 vacuous, 1 unlandable; 1 extra positive + 4 rivals
# added (1 binder-coverage at port time, 3 by the audit).
#
# VACUOUS (frame-mut-write): the sibling's MANDATORY frame-mutation rival keeps
#   the gold body verbatim then writes back into a read-only sequence input
#   granted only at half permission, and must be rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent: every parameter is an
#   immutable value, the method declares no `mut` binder, there is no heap and no
#   aliasing. There is no read-only input to overwrite and no permission system
#   to trip, so the class is vacuous. No substitute is fabricated.
# UNLANDABLE (weak-diverge-reject) — CORRECTED BY THE AUDIT. The previous note
#   here said this bundle runs under `loom.semantics.termination "partial"` and
#   that a diverging rival VERIFIES, so nothing was shippable. Both halves were
#   wrong: the frozen `set_option` is `"total"`, and the audit's measurements are
#   the opposite of what that note claimed.
#     * `while tooOld` with NO decreasing annotation, gold body otherwise: exit 1,
#       `error: Decreasing annotations are required in total correctness
#       semantics`. REJECTED, not verified.
#     * the canonical corpus probe shape (a bare `while True do pure ()` prefix
#       spliced at the head of the impl region): exit 1, same error. Nothing in
#       the corpus admits it, because nothing in the corpus is `partial`.
#   So the class is NOT a `partial` hole. There is no `partial` cohort at all:
#   all 500 velvet bundles set "total" and open TotalCorrectness, and the
#   `set_option` elaborator itself runs `openScope `TotalCorrectness`
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so the option and the `open`
#   cannot disagree. Citing such a cohort here was the error.
#   It is nevertheless not shippable as an expect="reject" case, for a reason on
#   the WITNESS half rather than the outcome half, and this is the demonstrated
#   evidence. The rejection is a whole-file linter error, so the witness file
#   built from the rival inherits it and the tester never becomes decidable.
#   Four tactic shapes were tried against the rival and all failed (exit 1):
#   `decide` (`Decidable instance did not reduce`), `decide +kernel`,
#   `simp [verifyVersionTester, verifyVersionExec, checkSpec, lexLt]`, and
#   `unfold verifyVersionTester; simp_all`. The gate's own `_check_witness` was
#   then run on the assembled case and returned `witness-unproven` — an
#   INCONCLUSIVE outcome, which is not a pass, so shipping it would fail G-PBT
#   rather than strengthen it. `witness_reference` does not help: it substitutes
#   the GOLD side, and the half that fails here is the RIVAL side. The deeper
#   reason is semantic, not tactical — there is no input at which this rival
#   returns a WRONG value, since it returns gold's value or never returns, and a
#   per-input value refutation is the only thing a witness can state.
#   A DIFFERENT residual in this class was escalated here as a genuine spec hole:
#   a loop that supplies a measure the checker accepts while never exiting, making
#   the entire post-loop continuation vacuous and laundering an arbitrary return
#   value. The earlier note reported the exact shape `while true / done_with False
#   / decreasing k` (body `k := k+1`) as VERIFYING at exit 0 with a wrong
#   `Except.ok ()`, reproduced twice, plus an `assert False` after the loop also
#   verifying. THAT MEASUREMENT DOES NOT REPRODUCE and the escalation is RETRACTED.
#   Rebuilt against the spec as it stands, that same loop spliced at the impl
#   anchor is REJECTED: exit 1, `unsolved goals`, `case «decreasing_1: k»`,
#   residual `k + 1 < k`. So the measure is not merely demanded, its descent is
#   discharged, and there is no unchecked measure by which a continuation could be
#   made unreachable. The mechanism is in Loom:
#   `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop`
#   (`Loom/MonadAlgebras/NonDetT/Basic.lean:544`) takes `measure : β -> Nat` and
#   emits the goal `measure b' < measure b`; only the `PartialCorrectness` twin
#   (:211) takes an `Option ℕ` and DISCARDS it. No change to the frozen
#   Solution.lean is needed or wanted: nothing is open on this axis.
# RE-AIMED + STRENGTHENED (admissibility): the sibling asserts the
#   half-permission admits reading a normal runtime-version list. This backend's
#   method has NO precondition and no permission surface, so that probe is
#   degenerate (every input is in-domain). The port re-aimed it at guard
#   non-degeneracy (two `lexLt` facts); the audit found that too weak — a
#   `lexLt`-only assert cannot see an unsatisfiable POST-IMAGE, which is the
#   total-carrier analogue of PRECOND-TOO-STRONG. It now discharges `checkSpec`
#   itself by evaluation at two F2P-shaped points (the below-case WITH its
#   diagnostic payload, and the at-threshold boundary) before closing the frozen
#   obligation verbatim, keeping the two `lexLt` conjuncts for non-degeneracy.
#   Confirmed load-bearing: falsifying one conjunct makes the same proof fail
#   (exit 1), so the assert is discharged rather than skipped.
# PORTED-RESHAPED (pos-branch-reorder): the sibling's positive control swaps the
#   two MUTUALLY-EXCLUSIVE early-exit branches of its comparison loop. This
#   backend's frozen impl is straight-line (no loop), so the exact loop reshape
#   does not exist; the reshape SPIRIT — "structurally different, behaviourally
#   identical, guard negated / arms swapped" — is carried by negating the
#   below-threshold guard and swapping the success / fail arms. Same outcome on
#   every input; the reproof is `loom_solve`.
# ADDED (pos-required-version-local): a second positive control this backend
#   affords — name the threshold through the pure `requiredVersion` selector and
#   bind the diagnostic to a typed local. Guards the spec against being
#   SPEC-TOO-STRONG on threshold naming / payload binding, a reshape axis the
#   sibling's inline loop does not have.
# ADDED (weak-message-drops-version): the sibling's guard returns `None` on both
#   paths — it has NO diagnostic payload to model. This backend's ensures pins
#   the failing-branch payload to `errorMessage versionStr`, an independent
#   top-level behaviour (M) with its own free input `versionStr`. A battery whose
#   every rival attacked only the decision (D) would hold `versionStr` fixed and
#   never demonstrate the spec's dependence on it, so this rival keeps the
#   decision exactly right and drops the reported version from the diagnostic —
#   refuted at a below-minimum tuple with a non-empty version string, the point
#   that makes (M) observable. Its faithful counterpart raises a diagnostic
#   missing the found version and still fails the F2P message assertion.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders of
#   the sole ensures (8 reject cases, 7 distinct input points):
#     info        — [2,0,0] (always-succeed, below w/ major<3);
#                   [3,9,0] (always-fail, at-threshold boundary; and
#                     boundary-nonstrict, where it is the ONLY separating point);
#                   [3,0,0] (major-only, 3.x below minimum);
#                   [3,8,11,1] (prepatch, F2P between-thresholds; and
#                     message-names-old-threshold);
#                   [3,8,2] (message-drops-version, below minimum);
#                   [3,9] (pad-short-tuple, SHORT tuple — the prefix sub-domain,
#                     where a tuple shorter than the threshold sorts below its
#                     extension; no other witness has arity < 3):
#                   varied across major<3 / at-threshold / 3.x-below / between-
#                   thresholds / short-arity — never held fixed, and the arity of
#                   `info` itself now varies (2, 3 and 4 components).
#     versionStr  — "x" / "" / "y" / "z" / "w" / "3.9.0" / "3.9" / "3.8.11.1":
#                   both empty and non-empty, and two rivals' witnesses DEPEND on
#                   the value: message-drops-version needs it non-empty (its
#                   divergence is exactly the dropped string) and
#                   message-names-old-threshold carries it through correctly while
#                   corrupting the surrounding text.
#   Every independent top-level behaviour of the post-image is attacked: the
#   fail-vs-succeed decision in BOTH directions (always-succeed / always-fail),
#   the STRICTNESS of the comparison at the threshold (boundary-nonstrict), the
#   minor-version sub-domain (major-only), the prefix/arity sub-domain
#   (pad-short-tuple), the threshold value (prepatch), and the diagnostic payload
#   on BOTH of its axes — the echoed input (message-drops-version) and the fixed
#   text (message-names-old-threshold).
#
# AUDIT PROBES THAT FOUND NO HOLE (recorded so the next reader need not re-run
#   them). Correct reshapes that VERIFY, so the spec is not too strong on these
#   axes: a `match` on the guard's Bool instead of an `if`; the decision returned
#   inline from the `return` with no `let`; and the diagnostic spelled out
#   literally rather than through `errorMessage` (all exit 0). Wrong impls that
#   are REJECTED, so the spec is not too weak on these axes: a too-HIGH threshold
#   ([3,9,1] instead of the required minimum) and a constant-measure terminating
#   loop wrapped around a wrong value (both exit 1). The three audit-added rivals
#   above came from this sweep; these are the probes that did not become cases.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (`lexLt` / `errorMessage` are I-ops checked
# by G-CONF), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
