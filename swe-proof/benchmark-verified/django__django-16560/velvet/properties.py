"""properties.py — G-PBT falsification battery for django__django-16560 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (five contracted methods over an optional short-code token
domain, ``ErrCode = Option (List Char)``; ``none`` is the neutral "no code"
marker). Each method is one independent observable projection of a constraint,
and each carries exactly one load-bearing post-image:

  recordErrorCode  (supplied)             ensures out = recordedCode supplied
  serializeWithCode(base, code)           ensures out = withCodeKwarg base code
  constraintsEqual (otherEqual, cA, cB)   ensures out = constraintEq otherEqual cA cB
  renderConstraint (base, code, shown)    ensures out = renderedWithCode base code shown
  validateWithCode (isValid, code)        ensures out = checkResult isValid code
                                          ensures isValid = false → out = Except.error code
                                          ensures isValid = true  → out = Except.ok ()

None of the five has a precondition (no ``require`` clause anywhere), so the
admitted input domain is total: every value of every carrier is in scope.
``otherEqual``, ``base`` (both flavours), ``shown`` and ``isValid`` are FREE
inputs standing for unchanged sub-computations — the post-images must hold for
EVERY value they take, which is what makes the partial-domain rivals below
genuinely refutable at a concrete point.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    an input may carry a fractional heap permission an impl can overwrite. Lean
    and Velvet are referentially transparent: every parameter is an immutable
    value (no ``mut`` binder in this bundle), there is no heap and no aliasing,
    so there is no read-only input to mutate and no substitute probe to build.
    Not fabricated.
  * IDENTITY-vs-EQUALITY — VACUOUS on this carrier. On nagini the code
    comparison is pinned to token IDENTITY, which is strictly finer than value
    equality, so an equality-based impl is a genuine near-miss. Here the code
    carrier is a plain inductive value (``Option (List Char)``) whose only
    comparison IS structural equality; the finer relation does not exist, so
    that rival collapses onto the frozen impl and no discriminating witness can
    exist. Reported as an omission (see the module footer), not faked. Its
    partial-domain SPIRIT is carried by ``weak-equal-presence-only``, which
    compares only whether a code is present rather than which code it is.
  * UNGROUNDED-ORACLE ECHO — N/A. Every post-image is a total, fully unfolded
    function of the method's own arguments (``recordedCode``, ``withCodeKwarg``,
    ``constraintEq``, ``renderedWithCode``, ``checkResult`` are all concrete
    ``def``s in the ``pure`` region, and the ``axioms`` region is empty — there
    is no opaque answer key to echo). So there is no WRONG echo to build.
    Instead we carry honest cheapest-reshape POSITIVE CONTROLS (``pos-*``).
  * REPORT/ACCEPT-DECISION — APPLIES to ``validateWithCode``: its observable is
    the accept-vs-report decision AND the payload the report carries. Three
    ensures clauses pin it: the accept branch to EXACTLY ``isValid = true``, the
    report branch to EXACTLY ``isValid = false``, and the report's payload to
    the constraint's own code. Three rivals attack this surface.
  * PARTIAL-DOMAIN / VALUE — APPLIES to all five: a rival right on part of the
    token domain but diverging on a sub-domain (the ``none`` marker vs a present
    code; two distinct present codes; agreeing-vs-differing other fields).
  * FREE-INPUT PRESERVATION — APPLIES to ``serializeWithCode`` and
    ``renderConstraint``. Each post-image has TWO independent halves: the
    presence decision (does the code entry / fragment appear?) and the passage
    of the free input through it (are the pre-existing bindings, the base
    rendering, and the rendered code value carried into the result unchanged?).
    A rival can get the decision exactly right and still lose the free input, so
    that half is attacked on its own by ``weak-serialize-drops-base``,
    ``weak-render-drops-base`` and ``weak-render-omits-shown``. Without them
    every witness on those obligations would sit at the same free-input value
    and a rival mishandling only that input would go uncaught.

WITNESS PLACEMENT. Rivals do not share refutation points unless they fail there
for the same reason. Where one rival is a near-miss of another, its witness sits
on the sub-domain that SEPARATES them, so its rationale's sub-domain claim is
machine-checked rather than asserted: ``weak-equal-presence-only`` is refuted at
the mirror of ``weak-equal-ignores-code``'s point and additionally discharges
the post-image POSITIVELY on the set-vs-unset boundary (where it agrees with the
spec and the blunter rival does not — that half fails against the blunter
rival's impl); ``weak-check-never-reports`` is refuted with no code configured,
the half of the optional domain on which ``weak-check-report-drops-code``
provably agrees with the frozen solution.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; every unchanged
sub-computation is a free input, owed no contract). There is no
axiom-soundness / axiom-containment obligation to probe here, and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16560"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside one impl region and is
# ---- unique inside Solution.lean; both facts asserted at load by _swap) ----
_A_RECORD = (
    "    let mut out : ErrCode := none\n"
    "    if supplied ≠ none then\n"
    "      out := supplied\n"
    "    return out\n"
)
_A_SERIALIZE = (
    "    let out := match code with\n"
    "      | none   => base\n"
    "      | some c => base ++ [(\"violation_error_code\", c)]\n"
)
_A_EQUAL = "    let out := otherEqual && (codeA == codeB)\n"
_A_RENDER = (
    "    let out := match code with\n"
    "      | none   => base\n"
    "      | some _ => base ++ \" violation_error_code=\".toList ++ shown\n"
)
_A_CHECK = (
    "    let out : Except ErrCode Unit :=\n"
    "      if isValid then Except.ok () else Except.error code\n"
)

# ---- proof-body anchors. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (markers._elide_prove_correct keeps only the header),
# ---- so a positive control that reshapes an impl may retune its tactic script
# ---- without touching the spec or dropping the obligation. Each body line is
# ---- unique in the file because the helper it unfolds is method-specific.
_T_RECORD = "  loom_solve <;> simp_all [recordedCode]\n"
_T_SERIALIZE = "  loom_solve <;> simp_all [withCodeKwarg]\n"
_T_EQUAL = "  loom_solve <;> simp_all [constraintEq]\n"
_T_RENDER = "  loom_solve <;> simp_all [renderedWithCode]\n"


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape one impl region AND retune that method's tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester
# ---- machinery: `<name>Tester args = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` blocks have been stripped, so no
# ---- tactic script can mask the verdict.
def _tester(method, pre=""):
    return (f"{pre}extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n")


# `prove_postcondition_decidable_for validateWithCode` cannot synthesize
# `DecidableEq` for the report carrier on its own (the two implication clauses
# need equality of `Except ErrCode Unit` to be decidable), so that witness
# derives the instance first. It is an instance, not an assumption: no `axiom`,
# `sorry` or `native_decide` is involved, and the frozen solution rejects these
# witnesses all the same.
_DEC_REPORT = "deriving instance DecidableEq for Except\n\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps every obligation and only reshapes
    # the executable surface; the contracts are point-wise over immutable
    # values, so no induction is needed and each reproof stays one `cases`
    # away from the frozen script.
    # =====================================================================
    {
        "id": "pos-record-match",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: a total case split on the optional input that rebuilds the
        # same token in each arm, replacing the mutable-accumulator form.
        # Observationally `recordedCode supplied` for every token.
        "module": _swap2(
            _A_RECORD,
            "    let out : ErrCode := match supplied with\n"
            "      | none   => none\n"
            "      | some c => some c\n"
            "    return out\n",
            _T_RECORD,
            "  loom_solve <;> (cases supplied <;> simp_all [recordedCode])\n",
        ),
        "rationale": "a correct case-split reshape of the recorded-code echo "
                     "must satisfy `out = recordedCode supplied` on both arms "
                     "of the optional domain; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-serialize-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the same two-arm decision written present-first. The set of
        # bindings produced is unchanged on both arms.
        "module": _swap2(
            _A_SERIALIZE,
            "    let out := match code with\n"
            "      | some c => base ++ [(\"violation_error_code\", c)]\n"
            "      | none   => base\n",
            _T_SERIALIZE,
            "  loom_solve <;> (cases code <;> simp_all [withCodeKwarg])\n",
        ),
        "rationale": "reordering the two arms of the presence decision yields "
                     "the same bindings, so `out = withCodeKwarg base code` "
                     "still holds pointwise; a correct reshape must verify.",
    },
    {
        "id": "pos-equal-commuted",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: conjunction reorder — code term first, other-fields term
        # second. `&&` is commutative, and the post pins the boolean VALUE, not
        # the term order, so this must verify.
        "module": _swap2(
            _A_EQUAL, "    let out := (codeA == codeB) && otherEqual\n",
            _T_EQUAL,
            "  loom_solve <;> (cases otherEqual <;> simp_all [constraintEq])\n",
        ),
        "rationale": "commuting the two conjuncts computes the same boolean, so "
                     "`out = constraintEq otherEqual codeA codeB` is unchanged; "
                     "must verify (else SPEC-TOO-STRONG on term order).",
    },
    {
        "id": "pos-render-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: same two-arm decision, present-first. Identical text on both
        # arms.
        "module": _swap2(
            _A_RENDER,
            "    let out := match code with\n"
            "      | some _ => base ++ \" violation_error_code=\".toList ++ shown\n"
            "      | none   => base\n",
            _T_RENDER,
            "  loom_solve <;> (cases code <;> simp_all [renderedWithCode])\n",
        ),
        "rationale": "reordering the arms of the textual-fragment decision "
                     "produces the same characters on both arms, so "
                     "`out = renderedWithCode base code shown` holds; must "
                     "verify.",
    },
    {
        "id": "pos-check-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Branch reorder of the accept/report decision: test the report case
        # first and accept in the else. Same accept-iff-valid decision and the
        # same carried payload, so all THREE ensures clauses still hold.
        "module": _swap2(
            _A_CHECK,
            "    let out : Except ErrCode Unit :=\n"
            "      if isValid = false then Except.error code else Except.ok ()\n",
            "  loom_solve <;> simp_all [checkResult]\n",
            "  loom_solve <;> (cases isValid <;> simp_all [checkResult])\n",
        ),
        "rationale": "negating the guard and swapping the branches preserves "
                     "the accept-iff-valid decision and the carried payload, so "
                     "all three clauses (`out = checkResult isValid code` and "
                     "both implications) still discharge; must verify.",
    },
    {
        "id": "pos-check-carried-local",
        "kind": "soundness",
        "expect": "verify",
        # Local-binding reshape: bind the payload to a typed local, then
        # report it. Same value flow, so the report still exposes the exact
        # code. Tactic script untouched — this one needs no retuning.
        "module": _swap(
            _BASE, _A_CHECK,
            "    let reported : ErrCode := code\n"
            "    let out : Except ErrCode Unit :=\n"
            "      if isValid then Except.ok () else Except.error reported\n",
        ),
        "rationale": "binding the payload to a typed local before reporting "
                     "leaves `isValid = false → out = Except.error code` "
                     "intact; a correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method in this bundle has a `require` clause, so
    # there is no precondition that could exclude an F2P-shaped input; the
    # usual "a normal input satisfies the precondition" probe is vacuously
    # satisfied. The remaining admissibility risk on a total domain is that
    # the post-image is UNSATISFIABLE at the interesting point — a spec no
    # impl can meet reads exactly like a spec every impl meets. So this case
    # discharges an in-region `assert` at the F2P-shaped report point,
    # SYMBOLICALLY in the constraint's own code: the verifier must establish
    # that the post-image really does demand a report carrying that exact code
    # on the reporting branch, and an acceptance carrying nothing on the other.
    # The surrounding impl is kept verbatim so the method's own obligations
    # still discharge. The assert is live, not decoration: replacing it with a
    # false claim about the same point leaves an unsolved `False` goal.
    # =====================================================================
    {
        "id": "admiss-report-carries-code",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _A_CHECK,
            "    assert (with_name_prefix `assert\n"
            "      (checkResult false code = Except.error code ∧\n"
            "       checkResult true code = Except.ok ()))\n" + _A_CHECK,
        ),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: for a symbolic code it demands exactly "
                     "a report carrying that code on the reporting branch and a "
                     "payload-free acceptance otherwise. The in-region assert "
                     "must discharge (else PRECOND-TOO-STRONG / an "
                     "unsatisfiable obligation); the impl is kept verbatim so "
                     "the three ensures clauses still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================

    # ---- the recorded code ----
    {
        "id": "weak-record-drops-code",
        "kind": "uniqueness",
        "expect": "reject",
        # Records the neutral marker regardless of what was supplied.
        "module": _swap(_BASE, _A_RECORD,
                        "    let out : ErrCode := none\n    return out\n"),
        "refinement": "a counterpart that does not retain the optionally "
                      "supplied code has nothing to surface later, so the "
                      "failing tests that construct a constraint with a code "
                      "and then read it back still observe the absent default "
                      "and still fail. It would NOT resolve.",
        "rationale": "REJECT from `out = recordedCode supplied`: at a present "
                     "supplied code the impl yields the absent marker where the "
                     "post-image demands that code.",
        "witness": _tester("recordErrorCode") +
                   'example : recordErrorCodeTester (some "a".toList) = false := by\n'
                   "  decide\n",
    },
    {
        "id": "weak-record-neutral-becomes-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The partial-domain DUAL of the rival above, and the only shape that
        # can be refuted on the OTHER half of the optional domain: the supplied
        # code is retained faithfully whenever one is given, but the absent
        # marker is coerced into a present-but-EMPTY code. Correct on every
        # present code, wrong exactly at `none` — so this rival is what
        # demonstrates that the post-image constrains `supplied` at the absent
        # marker too, not merely that it echoes a present token.
        "module": _swap(
            _BASE, _A_RECORD,
            "    let out : ErrCode := some (supplied.getD [])\n"
            "    return out\n"),
        "refinement": "a counterpart that records an empty code where nothing "
                      "was supplied makes EVERY constraint carry a code, so the "
                      "unchanged assertions that pin the projections of a "
                      "constraint with no code configured — its serialized "
                      "bindings (which must omit the code entry entirely) and "
                      "its textual form (which must show no code fragment) — "
                      "observe a spurious empty code instead and fail. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = recordedCode supplied`: at the absent "
                     "marker the post-image demands the absent marker back, and "
                     "the impl yields a present (empty) code. Refuted at "
                     "`supplied = none`, the sub-domain no other rival on this "
                     "obligation probes.",
        "witness": _tester("recordErrorCode") +
                   "example : recordErrorCodeTester none = false := by\n"
                   "  decide\n",
    },

    # ---- the serialized bindings ----
    {
        "id": "weak-serialize-never-names",
        "kind": "uniqueness",
        "expect": "reject",
        # Never adds the code binding — emits only the pre-existing bindings.
        "module": _swap(_BASE, _A_SERIALIZE, "    let out := base\n"),
        "refinement": "a counterpart whose serialized bindings never gain the "
                      "code entry cannot round-trip a constraint that has one, "
                      "so the failing test asserting the entry is PRESENT for a "
                      "set code still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = withCodeKwarg base code`: at a present "
                     "code the impl omits the binding the post-image requires.",
        "witness": _tester("serializeWithCode") +
                   "example : serializeWithCodeTester [] (some \"a\".toList) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-serialize-always-names",
        "kind": "uniqueness",
        "expect": "reject",
        # Always adds the binding — even for the neutral marker, where it
        # binds the empty value. Right on present codes, wrong on `none`: the
        # partial-domain dual of the case above.
        "module": _swap(
            _BASE, _A_SERIALIZE,
            "    let out := base ++ [(\"violation_error_code\", code.getD [])]\n"),
        "refinement": "a counterpart that always emits the code entry makes an "
                      "unset code indistinguishable from a set one, so the "
                      "failing test asserting the entry is OMITTED when no code "
                      "is configured still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = withCodeKwarg base code`: at the "
                     "absent marker the impl adds a binding the post-image "
                     "forbids (it requires the bindings unchanged there).",
        "witness": _tester("serializeWithCode") +
                   "example : serializeWithCodeTester [] none = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-serialize-drops-base",
        "kind": "uniqueness",
        "expect": "reject",
        # Gets the PRESENCE decision exactly right — the code entry appears
        # exactly when a code is set — and corrupts the OTHER half of the
        # post-image: on the present branch the pre-existing bindings are
        # discarded instead of extended. Built specifically to abuse `base`,
        # the free input standing for the bindings a constraint already has:
        # the two rivals above are wrong for every value of `base`, so neither
        # attests that the post-image PRESERVES it.
        "module": _swap(
            _BASE, _A_SERIALIZE,
            "    let out := match code with\n"
            "      | none   => base\n"
            "      | some c => [(\"violation_error_code\", c)]\n"),
        "refinement": "a counterpart that replaces the serialized bindings with "
                      "the lone code entry loses every binding a constraint "
                      "already round-trips (its name and its message among "
                      "them), so the failing test that pins the FULL set of "
                      "bindings for a constraint carrying a code — name and "
                      "message alongside the code entry — still fails, and the "
                      "unchanged round-trip assertions break as well. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = withCodeKwarg base code`, whose present "
                     "branch is `base ++ [entry]`: with a non-empty `base` and a "
                     "present code the impl emits the entry ALONE where the "
                     "post-image demands the pre-existing bindings followed by "
                     "it. Refuted at a non-empty `base`, which is what makes the "
                     "post-image's dependence on that input observable.",
        "witness": _tester("serializeWithCode") +
                   "example : serializeWithCodeTester [(\"name\", \"n\".toList)] "
                   "(some \"a\".toList) = false := by\n  decide\n",
    },

    # ---- structural equality ----
    {
        "id": "weak-equal-ignores-code",
        "kind": "uniqueness",
        "expect": "reject",
        # Consults only the other observable fields: diverges on the
        # sub-domain where those agree but the codes differ (returns true
        # where the post-image requires false).
        "module": _swap(_BASE, _A_EQUAL, "    let out := otherEqual\n"),
        "refinement": "a counterpart whose equality ignores the code reports "
                      "two constraints differing ONLY in code as equal, which "
                      "is exactly the pair the failing equality tests assert to "
                      "be unequal. It would NOT resolve.",
        "rationale": "REJECT from `out = constraintEq otherEqual codeA codeB`: "
                     "with the other fields agreeing and two distinct codes the "
                     "impl returns true, the post-image false.",
        "witness": _tester("constraintsEqual") +
                   "example : constraintsEqualTester true (some \"a\".toList) "
                   "(some \"b\".toList) = false := by\n  decide\n",
    },
    {
        "id": "weak-equal-code-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the other-fields conjunct: diverges where the codes agree but
        # the other fields do not.
        "module": _swap(_BASE, _A_EQUAL, "    let out := (codeA == codeB)\n"),
        "refinement": "ignoring the other observable fields reports two "
                      "structurally different constraints that happen to share "
                      "a code as equal, breaking the pre-existing equality "
                      "contract the unchanged equality assertions rely on. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = constraintEq otherEqual codeA codeB`: "
                     "with equal codes and disagreeing other fields the impl "
                     "returns true, the post-image false.",
        "witness": _tester("constraintsEqual") +
                   "example : constraintsEqualTester false (some \"a\".toList) "
                   "(some \"a\".toList) = false := by\n  decide\n",
    },
    {
        "id": "weak-equal-presence-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: compares only WHETHER a code is present, not WHICH code.
        # Agrees with the frozen post-image everywhere except on two distinct
        # present codes — the finest partial-domain split this carrier admits,
        # and the closest honest counterpart to nagini's identity-vs-equality
        # probe (see the module footer).
        "module": _swap(
            _BASE, _A_EQUAL,
            "    let out := otherEqual && (codeA.isSome == codeB.isSome)\n"),
        "refinement": "comparing only whether a code is set still reports two "
                      "constraints that differ only in WHICH code they carry as "
                      "equal, so the failing equality tests — which distinguish "
                      "exactly that pair — still fail. It would NOT resolve.",
        "rationale": "REJECT from `out = constraintEq otherEqual codeA codeB`: "
                     "the post-image compares the code VALUES, so at two "
                     "distinct present codes with agreeing other fields the "
                     "impl returns true and the post-image false. Refuted at the "
                     "MIRROR point of weak-equal-ignores-code (the two codes "
                     "exchanged), so this near-miss carries its own refutation "
                     "input rather than the blunter rival's, and the first code "
                     "is not held fixed across the battery. The second example "
                     "makes the near-miss claim machine-checked instead of "
                     "merely asserted: on the presence boundary (one code set, "
                     "the other not) this rival SATISFIES the post-image, which "
                     "is exactly where weak-equal-ignores-code violates it — so "
                     "the two rivals are distinct predicates, not one attack "
                     "written twice.",
        "witness": _tester("constraintsEqual") +
                   "example : constraintsEqualTester true (some \"b\".toList) "
                   "(some \"a\".toList) = false := by\n  decide\n\n"
                   "-- The near-miss attestation: on the set-vs-unset boundary "
                   "this rival\n-- agrees with the post-image, so its divergence "
                   "really is confined to\n-- two DISTINCT set codes. (This half "
                   "holds of the frozen solution too;\n-- the half above is what "
                   "makes the snippet discriminate.)\n"
                   "example : constraintsEqualTester true none "
                   "(some \"a\".toList) = true := by\n  decide\n",
    },

    # ---- the textual form ----
    {
        "id": "weak-render-never-shows",
        "kind": "uniqueness",
        "expect": "reject",
        # Never appends the fragment: the base rendering only.
        "module": _swap(_BASE, _A_RENDER, "    let out := base\n"),
        "refinement": "a counterpart whose textual form never shows the code "
                      "leaves a configured code invisible, so the failing tests "
                      "that assert the rendered text CONTAINS the code fragment "
                      "still fail. It would NOT resolve.",
        "rationale": "REJECT from `out = renderedWithCode base code shown`: at "
                     "a present code the impl omits the fragment the post-image "
                     "requires.",
        "witness": _tester("renderConstraint") +
                   "example : renderConstraintTester \"x\".toList "
                   "(some \"a\".toList) \"y\".toList = false := by\n  decide\n",
    },
    {
        "id": "weak-render-always-shows",
        "kind": "uniqueness",
        "expect": "reject",
        # Always appends the fragment — even for the neutral marker. Right on
        # present codes, wrong on `none`.
        "module": _swap(
            _BASE, _A_RENDER,
            "    let out := base ++ \" violation_error_code=\".toList ++ shown\n"),
        "refinement": "a counterpart that always appends the fragment changes "
                      "the textual form of every constraint that has no code, "
                      "breaking the unchanged rendering assertions that pin the "
                      "no-code text exactly. It would NOT resolve.",
        "rationale": "REJECT from `out = renderedWithCode base code shown`: at "
                     "the absent marker the impl appends a fragment the "
                     "post-image forbids (it requires the base text there).",
        "witness": _tester("renderConstraint") +
                   "example : renderConstraintTester \"x\".toList none "
                   "\"y\".toList = false := by\n  decide\n",
    },
    {
        "id": "weak-render-drops-base",
        "kind": "uniqueness",
        "expect": "reject",
        # Gets the presence DECISION right (the fragment appears exactly when a
        # code is set) and corrupts the other half of the post-image: on the
        # present branch the base rendering is discarded and only the fragment
        # is emitted. Built to abuse `base` — the free input standing for the
        # rendering a constraint already produces. The two rivals above are
        # wrong for EVERY value of `base`, so neither attests that the
        # post-image carries it through; this one is wrong exactly because it
        # drops it.
        "module": _swap(
            _BASE, _A_RENDER,
            "    let out := match code with\n"
            "      | none   => base\n"
            "      | some _ => \" violation_error_code=\".toList ++ shown\n"),
        "refinement": "a counterpart that emits only the code fragment loses "
                      "everything the textual form of a constraint already "
                      "shows, so the failing tests — which pin the WHOLE "
                      "rendered text of a constraint carrying a code, base part "
                      "included — still fail, and every unchanged rendering "
                      "assertion breaks too. It would NOT resolve.",
        "rationale": "REJECT from `out = renderedWithCode base code shown`, "
                     "whose present branch is `base ++ fragment ++ shown`: with "
                     "a non-empty `base` and a present code the impl emits the "
                     "fragment alone where the post-image demands the base text "
                     "first. Refuted at a base rendering distinct from the one "
                     "the rivals above use, which is what makes the post-image's "
                     "dependence on that input observable.",
        "witness": _tester("renderConstraint") +
                   "example : renderConstraintTester \"b\".toList "
                   "(some \"a\".toList) \"y\".toList = false := by\n  decide\n",
    },
    {
        "id": "weak-render-omits-shown",
        "kind": "uniqueness",
        "expect": "reject",
        # The sharpest rival on this surface: the presence decision is right AND
        # the base text is carried through — only the rendered code VALUE is
        # missing, so the text announces a code and then shows none. Built to
        # abuse `shown`, the free input standing for the unchanged formatting of
        # the code value.
        "module": _swap(
            _BASE, _A_RENDER,
            "    let out := match code with\n"
            "      | none   => base\n"
            "      | some _ => base ++ \" violation_error_code=\".toList\n"),
        "refinement": "a counterpart whose textual form names the code but omits "
                      "its value renders a constraint's code as blank, so the "
                      "failing tests that compare the rendered text against one "
                      "containing the configured code's value still fail. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = renderedWithCode base code shown`: the "
                     "present branch appends `shown` after the key fragment and "
                     "the impl stops at the fragment, so at any non-empty "
                     "rendered value the texts differ. Refuted at a rendered "
                     "value distinct from the one the rivals above use, so the "
                     "battery moves that input rather than holding it fixed.",
        "witness": _tester("renderConstraint") +
                   "example : renderConstraintTester \"x\".toList "
                   "(some \"a\".toList) \"v\".toList = false := by\n  decide\n",
    },

    # ---- the accept/report decision ----
    {
        "id": "weak-check-never-reports",
        "kind": "uniqueness",
        "expect": "reject",
        # Accepts unconditionally: never reports, even on a violation.
        "module": _swap(_BASE, _A_CHECK,
                        "    let out : Except ErrCode Unit := Except.ok ()\n"),
        "refinement": "a counterpart that never reports a violation cannot "
                      "surface any error at all, so the failing tests that "
                      "require a violation to be reported (and then read its "
                      "code) still fail. It would NOT resolve.",
        "rationale": "REJECT from `isValid = false → out = Except.error code`: "
                     "on the reporting branch the impl accepts, where the "
                     "post-image demands a report. Refuted with NO code "
                     "configured on purpose: the report DECISION is pinned "
                     "independently of the payload, so this rival is wrong there "
                     "too, and weak-check-report-drops-code below can only be "
                     "refuted at a configured code (with none configured its "
                     "report coincides with the frozen one). Between the three "
                     "rivals on this obligation both inputs therefore move — "
                     "`isValid` over both branches and `code` over both halves "
                     "of the optional domain — instead of one code value being "
                     "probed three times.",
        "witness": _tester("validateWithCode", _DEC_REPORT) +
                   "example : validateWithCodeTester false none "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-check-always-reports",
        "kind": "uniqueness",
        "expect": "reject",
        # Reports unconditionally: reports even on a valid instance.
        "module": _swap(_BASE, _A_CHECK,
                        "    let out : Except ErrCode Unit := Except.error code\n"),
        "refinement": "a counterpart that reports even a satisfied constraint "
                      "breaks every unchanged path where a check passes "
                      "silently, including the accepting half of the failing "
                      "tests. It would NOT resolve.",
        "rationale": "REJECT from `isValid = true → out = Except.ok ()`: on the "
                     "accepting branch the impl reports, which that clause "
                     "forbids.",
        "witness": _tester("validateWithCode", _DEC_REPORT) +
                   "example : validateWithCodeTester true (some \"a\".toList) "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-check-report-drops-code",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps the accept/report DECISION exactly right and corrupts only the
        # PAYLOAD: the report carries the neutral marker instead of the
        # constraint's code. The sharpest rival on this surface — it satisfies
        # the decision clauses' shape and fails only on the carried value.
        "module": _swap(
            _BASE, _A_CHECK,
            "    let out : Except ErrCode Unit :=\n"
            "      if isValid then Except.ok () else Except.error none\n"),
        "refinement": "a counterpart whose report carries no code makes the "
                      "surfaced failure indistinguishable from an unclassified "
                      "one, so the failing tests that read the reported code "
                      "off the raised failure and compare it to the "
                      "constraint's own still fail. It would NOT resolve.",
        "rationale": "REJECT from `isValid = false → out = Except.error code` "
                     "(and from `out = checkResult isValid code`): the decision "
                     "is right but the report carries the absent marker where "
                     "the post-image demands the constraint's code.",
        "witness": _tester("validateWithCode", _DEC_REPORT) +
                   "example : validateWithCodeTester false (some \"a\".toList) "
                   "= false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 16 cases (5 soundness
# positives, 1 admissibility, 10 uniqueness rivals); every one is accounted for
# below. The sibling contracts five per-token functions; this bundle contracts
# five per-projection methods, and the two sets of five are NOT the same
# partition — one sibling function is re-sited onto a different projection and
# two land on the same method here — so the mapping is stated case by case.
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------
#   pos-configured-ternary        -> pos-record-match                 PORTED
#   pos-surfaced-local            -> pos-check-carried-local          PORTED
#   pos-validate-negated-guard    -> pos-check-negated-guard          PORTED
#   pos-equal-commuted            -> pos-equal-commuted               PORTED
#   pos-kwnames-isnot             -> pos-serialize-arms-reordered     PORTED
#   admiss-surfaced-violated      -> admiss-report-carries-code       RE-AIMED
#   weak-configured-drops-code    -> weak-record-drops-code           PORTED
#   weak-surfaced-drops-code      -> weak-check-report-drops-code     PORTED
#   weak-validate-never-raises    -> weak-check-never-reports         PORTED
#   weak-validate-always-raises   -> weak-check-always-reports        PORTED
#   weak-validate-wrong-exc-type  -> weak-check-report-drops-code     MERGED
#   weak-equal-drops-classifier   -> weak-equal-ignores-code          PORTED
#   weak-equal-only-classifier    -> weak-equal-code-only             PORTED
#   weak-equal-eqeq-on-token      -> (none)                           OMITTED
#   weak-kwnames-always-true      -> weak-serialize-always-names      PORTED
#   weak-kwnames-always-false     -> weak-serialize-never-names       PORTED
#
# 13 ported, 1 merged, 1 re-aimed, 1 omitted = 16.
#
# RE-SITED (a note on two of the "ported" rows, not a separate class): the
#   sibling models the presence decision as a bare boolean and the carried
#   failure payload as its own function. Here those behaviours ARE the
#   serialized bindings and the reported reject value respectively, so
#   pos-kwnames-isnot / weak-kwnames-always-{true,false} land on
#   serializeWithCode, and pos-surfaced-local / weak-surfaced-drops-code land
#   on validateWithCode (which carries all three of this bundle's report
#   clauses). The ARGUMENT is unchanged in each; only the carrier is.
# RE-AIMED (admissibility): the sibling's case establishes a precondition for a
#   normal input. No method here has a `require` clause, so that probe is
#   vacuous — nothing could exclude a normal input. It is re-aimed at the
#   residual admissibility risk on a total domain: that the post-image is
#   UNSATISFIABLE at the interesting point. The case discharges an in-region
#   assertion that the post-image demands exactly a report carrying the
#   symbolic code, and a payload-free acceptance otherwise.
# MERGED: the sibling's "reports the wrong failure TYPE" rival has no
#   counterpart — the report carrier here has a single error constructor, so
#   the only observable a report can get wrong is its payload. That attack is
#   already covered by weak-check-report-drops-code.
# OMITTED (1, and the only one): the identity-vs-equality near-miss on the code
#   token. On the sibling's carrier the code comparison is pinned to a relation
#   strictly finer than value equality, so an equality-based impl is genuinely
#   a different predicate. This carrier has no such relation — the code is a
#   plain inductive value and structural equality IS its comparison — so that
#   rival is byte-identical to the frozen impl and NO witness can discriminate
#   it. Omitted because the distinction collapses on this carrier, not because
#   it was hard: weak-equal-presence-only carries its partial-domain spirit
#   (compare whether a code is set rather than which code it is) and does
#   discriminate.
# Frame/permission-mutation: the sibling already records this class as N/A (no
#   input carries a heap permission) and it is VACUOUS here for a stronger
#   reason: this backend is referentially transparent and this bundle declares
#   no `mut` binder at all, so there is no read-only input to overwrite. No
#   substitute fabricated.
# ADDED (8, no sibling counterpart). Four come from the surface itself: the
#   sibling does not model the textual projection at all, so
#   pos-render-arms-reordered and weak-render-{never,always}-shows are new, and
#   weak-equal-presence-only is new. The other four are BINDER-COVERAGE rivals,
#   added because the post-images here take free inputs the sibling's per-token
#   functions do not have, and a battery that never moves such an input says
#   nothing about the spec's dependence on it:
#     weak-serialize-drops-base        — presence decision right, the
#         pre-existing bindings discarded on the present branch (abuses `base`).
#     weak-render-drops-base           — presence decision right, the base
#         rendering discarded on the present branch (abuses `base`).
#     weak-render-omits-shown          — presence decision AND base text right,
#         the rendered code value omitted (abuses `shown`).
#     weak-record-neutral-becomes-empty — every supplied code retained
#         faithfully, the absent marker coerced to a present empty code; the
#         partial-domain dual of weak-record-drops-code and the only rival on
#         that obligation refutable at `supplied = none`.
#   Each is refuted at a concrete point the pre-existing rivals do not probe, so
#   `base`, `shown` and the absent half of the optional domain are now varied
#   rather than pinned. None is a fabricated wrongness: each is a real
#   divergence from its post-image with a machine-checked witness, and each
#   carries the refinement argument for why its faithful counterpart would still
#   leave the failing tests failing.
#
# WITNESS DISTINCTNESS. Two rivals may share a refutation point only if they
#   really fail there for the same reason. Where one rival is a NEAR-MISS of
#   another, its witness is placed on the sub-domain that separates them:
#     weak-equal-presence-only is refuted at the MIRROR of
#       weak-equal-ignores-code's point (the two codes exchanged) and carries a
#       second `example` discharging the post-image POSITIVELY on the
#       set-vs-unset boundary — the sub-domain where it agrees with the spec and
#       weak-equal-ignores-code does not. That second half fails against
#       weak-equal-ignores-code's impl, so the near-miss claim is machine-
#       checked, not asserted. It holds of the frozen solution too; the first
#       half is what makes the snippet discriminate.
#     weak-check-never-reports is refuted with NO code configured, because the
#       report DECISION is pinned independently of the payload, whereas
#       weak-check-report-drops-code can only be refuted at a configured code
#       (with none configured its report coincides with the frozen one —
#       verified). So the three rivals on that obligation move both inputs.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares
# no axiom, so there is nothing there to probe.
AXIOM_TESTS = []
