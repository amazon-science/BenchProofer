"""properties.py — PBT falsification battery for django__django-16560.

NOT a Nagini module; a record of adversarial cases the runner
(``swebench_nagini.pbt``) executes. Each SPEC case is a full ``model.py`` variant
that shares the FROZEN spec byte-for-byte (region-surgery: only text inside an
``# impl-start`` / ``# impl-end`` region is changed, so ``markers.same_spec`` is
guaranteed True) and swaps in a candidate implementation; it is checked by the
Nagini verifier. ``expect:"verify"`` passes iff (same_spec AND verifies);
``expect:"reject"`` passes iff (same_spec AND does NOT verify).

DEFENDED SURFACE (five contracted functions over an ``Optional[int]`` token
domain; the null token is the neutral "no classifier" marker):

  configured_code(code)                  Ensures(Result() is code)
  surfaced_violation_code(rc, violated)  Requires(violated); Ensures(Result() is rc)
  validate_rule(rc, violated)            Ensures(not violated);
                                         Exsures(ValidationFailure, violated)
  constraints_equal(ak, ac, bk, bc)      Ensures(Result()==(ak==bk and ac is bc))
  keyword_bundle_names_code(rc)          Ensures(Result()==(rc is not None))

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — N/A. No input carries a heap permission (``Acc(...)``); every
    parameter is a plain immutable token (``Optional[int]`` / ``int`` / ``bool``).
    There is no read-only half-permission input to overwrite, so the
    frame-mutation probe does not apply (has_readonly_input = False).
  * UNGROUNDED-ORACLE ECHO — N/A. Every postcondition is GROUNDED in the function
    arguments (identity ``is`` / a boolean of the args, fully unfolded). There is
    no ``@Pure`` answer-key / opaque marker an impl could echo without doing the
    work, so there is no WRONG echo to build. Instead we include honest cheapest-
    impl POSITIVE CONTROLS (pos-*) that must verify.
  * CONTROL-FLOW-EFFECT — APPLIES to ``validate_rule``: its observable is the
    raise/return decision (``Ensures(not violated)`` pins the normal exit to
    EXACTLY ``not violated``; ``Exsures(ValidationFailure, violated)`` pins the
    exceptional exit to EXACTLY ``violated`` and to the ValidationFailure TYPE).
    Several rivals attack this surface, and one control
    (``nonvacuity-validate-raise-reachable``) pins the RAISING PATH as reachable —
    without it every one of those rivals' rejections would be a claim about a
    branch the verifier never has to consider. Note that the foreign exception
    type a wrong-type rival raises must be one Nagini MODELS: only ``Exception``
    and ``ConnectionRefusedError`` are (resources/builtins.json), and a rival may
    not declare its own class without breaking same_spec, so ``raise
    ValueError()`` is a front-end translation failure — no Viper verdict, hence
    no evidence about the spec at all.
  * PARTIAL-DOMAIN / VALUE — APPLIES to ``constraints_equal`` and the per-token
    functions: a rival correct on part of the token domain but diverging on a
    sub-domain (classifier-only-differing rules; a present classifier; a
    None-vs-non-None split; the ``is`` vs ``==`` divergence on the token domain).

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the one
library value-flow (ValidationError store-verbatim ``code``) is NOT a consumed
``@ContractOnly`` axiom — it is validated end-to-end by axiom_check.py / G-AX
against the real callee, not by the Nagini proof. So there is no axiom-soundness /
axiom-containment obligation to probe here.
"""
from pathlib import Path

INSTANCE = "django__django-16560"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each unique inside model.py; verified at load) ----
_A_CONFIGURED = "    return code\n"
_A_SURFACED = "    return rule_code\n"
_A_VALIDATE = "    if violated:\n        raise ValidationFailure()\n    return\n"
_A_EQUAL = "    return a_key == b_key and a_code is b_code\n"
_A_KWNAMES = "    return rule_code is not None\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally-different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG. These keep every grounded obligation; they
    # only reshape the executable surface (no fragile induction lemma needed
    # — the contracts are point-wise over immutable tokens).
    # =====================================================================
    {
        "id": "pos-configured-ternary",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: a None-split branch that returns `code` either way.
        # Still observationally `Result() is code` for every token.
        "module": _swap(
            _BASE, _A_CONFIGURED,
            "    if code is None:\n"
            "        return code\n"
            "    else:\n"
            "        return code\n",
        ),
        "rationale": "a correct branch-reshaped impl of the identity echo must "
                     "verify Ensures(Result() is code); else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-surfaced-local",
        "kind": "soundness",
        "expect": "verify",
        # Local-variable reshape: bind then return. Same value flow.
        "module": _swap(
            _BASE, _A_SURFACED,
            "    out = rule_code  # type: Optional[int]\n"
            "    return out\n",
        ),
        "rationale": "binding the classifier to a typed local before returning "
                     "keeps Result() is rule_code; a correct reshape must verify.",
    },
    {
        "id": "pos-validate-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Branch-reorder of the control flow: handle the no-violation case in the
        # `if` and raise in the `else`. Same raise-iff-violated semantics; keeps
        # both Ensures(not violated) and Exsures(ValidationFailure, violated).
        "module": _swap(
            _BASE, _A_VALIDATE,
            "    if not violated:\n"
            "        return\n"
            "    raise ValidationFailure()\n",
        ),
        "rationale": "reordering the raise/return branches preserves the exact "
                     "raise-iff-violated control flow; must verify (else "
                     "SPEC-TOO-STRONG on the Exsures/Ensures pair).",
    },
    {
        "id": "pos-equal-commuted",
        "kind": "soundness",
        "expect": "verify",
        # Conjunction reorder: classifier term first, payload term second.
        # `and` is commutative so the boolean equals the gold predicate; the
        # Ensures pins value equality, not term order, so this must verify.
        "module": _swap(
            _BASE, _A_EQUAL,
            "    return a_code is b_code and a_key == b_key\n",
        ),
        "rationale": "commuting the equality conjuncts yields the same boolean "
                     "(Result()==(a_key==b_key and a_code is b_code)); must verify.",
    },
    {
        "id": "pos-kwnames-isnot",
        "kind": "soundness",
        "expect": "verify",
        # Spell the presence predicate via an explicit None comparison structured
        # as a branch returning the literal booleans. Same truth on every token.
        "module": _swap(
            _BASE, _A_KWNAMES,
            "    if rule_code is None:\n"
            "        return False\n"
            "    return True\n",
        ),
        "rationale": "branch over None returning the literal booleans equals "
                     "(rule_code is not None); a correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive-control self-call confirming the
    # precondition admits a normal F2P-shaped input. surfaced_violation_code
    # is the only function with a non-trivial Requires (violated == True);
    # an in-region caller establishes it for the violation-reporting input.
    # =====================================================================
    {
        "id": "admiss-surfaced-violated",
        "kind": "admissibility",
        "expect": "verify",
        # Inside validate_rule's impl region (a None-returning function whose
        # control flow we keep verbatim) call surfaced_violation_code on an
        # F2P-shaped violation-reporting input: the rule's own classifier
        # (symbolic rule_code, NOT a literal — avoids any int-identity subtlety)
        # with violated=True. This is a NON-recursive call (different function) so
        # no termination obligation arises. Establishing Requires(violated) for
        # this normal input is the admissibility witness; the post then gives
        # `sample is rule_code` by direct variable substitution. If the Requires
        # could not be met for this normal input, PRECOND-TOO-STRONG.
        "module": _swap(
            _BASE, _A_VALIDATE,
            "    sample = surfaced_violation_code(rule_code, True)  # type: Optional[int]\n"
            "    Assert(sample is rule_code)\n"
            "    if violated:\n"
            "        raise ValidationFailure()\n"
            "    return\n",
        ),
        "rationale": "the Requires(violated) precondition of surfaced_violation_"
                     "code is established for a normal violation-reporting input "
                     "(violated=True, a present classifier) and the post pins the "
                     "carried classifier; verifies (else PRECOND-TOO-STRONG). The "
                     "validate_rule control flow is kept verbatim so its own "
                     "obligations still discharge.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the spec that
    # MUST be rejected. Each carries the refinement argument that its faithful
    # real patch would NOT resolve the F2P/P2P.
    # =====================================================================

    # ---- CONTROL-FLOW-EFFECT (validate_rule) ----
    {
        "id": "weak-validate-never-raises",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the raise entirely: always returns normally. At the normal exit
        # `violated` may be True, so Ensures(not violated) is FALSE.
        "module": _swap(
            _BASE, _A_VALIDATE,
            "    return\n",
        ),
        "refinement": "the real patched validate() must `raise ValidationError` "
                      "on a reported violation; an impl that never raises fails "
                      "test_validate_custom_error / test_validate_conditon_custom_"
                      "error (which assert the error is raised with cm.exception."
                      "code == the classifier). It would NOT resolve.",
        "rationale": "REJECT from Ensures(not violated): the normal return is "
                     "reachable when violated=True, violating the postcondition.",
    },
    {
        "id": "weak-validate-always-raises",
        "kind": "uniqueness",
        "expect": "reject",
        # Raises unconditionally: raises even when not violated, violating
        # Exsures(ValidationFailure, violated) (the exception is thrown when
        # `violated` is False, where Exsures permits none).
        "module": _swap(
            _BASE, _A_VALIDATE,
            "    raise ValidationFailure()\n",
        ),
        "refinement": "the real validate() must fall through (return None) when "
                      "the underlying check reports NO violation; an always-raising "
                      "impl breaks every P2P validate() path with a satisfied "
                      "constraint (and the no-violation branch of the F2P tests). "
                      "It would NOT resolve.",
        "rationale": "REJECT from Exsures(ValidationFailure, violated): an "
                     "exception thrown when violated=False is not licensed by the "
                     "Exsures condition.",
    },
    {
        "id": "weak-validate-wrong-exc-type",
        "kind": "uniqueness",
        "expect": "reject",
        # Raises a DIFFERENT exception type on violation. Exsures pins the type to
        # ValidationFailure; a foreign exception is an uncaught/unlicensed throw.
        #
        # WHY ConnectionRefusedError, of all things. The foreign type has to be one
        # Nagini can TRANSLATE, and it has to come from inside the impl region: a
        # rival may not declare a second exception class, because a new top-level
        # def/class changes the projected spec view and breaks same_spec. That
        # leaves the builtin exception types Nagini models, and there are exactly
        # two -- `nagini_translation/resources/builtins.json` declares `Exception`
        # ("extends": "object") and `ConnectionRefusedError` ("extends":
        # "Exception"), and nothing else. `ValueError` is absent from that file, so
        # `raise ValueError()` is "Not supported: Unsupported builtin function" --
        # a front-end TRANSLATION failure, which reaches no Viper verdict at all
        # and so cannot be evidence that the SPEC turned the rival down (Nagini
        # exits 1, the rejection code, either way; see `nagini._no_verdict`).
        # ConnectionRefusedError is preferred over `Exception` because it is a
        # SIBLING of ValidationFailure under Exception rather than a SUPERtype of
        # it -- a genuinely foreign type, so the rejection cannot be read as an
        # artefact of raising a base class. Neither is a subtype of
        # ValidationFailure, so neither is licensed by the Exsures.
        "module": _swap(
            _BASE, _A_VALIDATE,
            "    if violated:\n"
            "        raise ConnectionRefusedError()\n"
            "    return\n",
        ),
        "refinement": "the real validate() raises django's ValidationError "
                      "(caught by `with self.assertRaises(ValidationError)` in the "
                      "F2P tests). Raising a foreign exception type fails those "
                      "assertRaises. It would NOT resolve. ConnectionRefusedError "
                      "stands in for 'some other exception class' -- the identity "
                      "of the foreign type is immaterial to the refinement, only "
                      "that it is not the validation failure the tests catch.",
        "rationale": "REJECT from Exsures(ValidationFailure, violated): the "
                     "exceptional postcondition is typed to ValidationFailure; a "
                     "ConnectionRefusedError on the violation path is unlicensed. "
                     "Measured: 'Postcondition of validate_rule might not hold. "
                     "Assertion \"method only raises exceptions of type "
                     "ValidationFailure\" might not hold.' -- the TYPE obligation "
                     "of the Exsures, which is the one this case claims, and the "
                     "only error reported. Non-vacuous: the raising branch is "
                     "reachable, pinned by the `nonvacuity-validate-raise-reachable` "
                     "control below.",
    },
    {
        "id": "nonvacuity-validate-raise-reachable",
        "kind": "uniqueness",
        "expect": "reject",
        # NON-VACUITY CONTROL for the three validate_rule reject cases above (and
        # for `pos-validate-negated-guard`). All four turn on what happens ON THE
        # RAISING PATH, and every claim about that path is empty if the path is not
        # reachable: a raise guarded by an infeasible condition VERIFIES while
        # proving nothing, so "the wrong exception type is rejected" would be a
        # statement about a branch Viper never has to consider.
        #
        # The probe is the frozen-correct impl with `Assert(False)` spliced in ahead
        # of the raise. It must be REJECTED, and rejected on the Assert: a failing
        # `Assert(False)` is exactly the statement "the verifier cannot rule this
        # program point out", i.e. `violated` is satisfiable here under the frozen
        # Requires (which constrains only termination). If this case ever flips to
        # `verified`, the raising path has gone dead and the sibling rejections
        # stop being evidence about the exception type.
        #
        # Spliced into the CORRECT impl, not into the wrong-type rival, so that the
        # failing Assert is the ONLY obligation that can break and the reject is
        # unambiguously attributable to reachability. (In the rival the Assert
        # failure MASKS the type error -- everything after an unprovable assertion
        # is checked under a false path condition -- so that variant would report
        # the same single Assert error while telling you less.) The path condition
        # at the Assert is byte-identical in both: same frozen Requires, same
        # `if violated:` guard, the raise statement comes after.
        #
        # `kind` is "uniqueness" (=> SPEC-TOO-WEAK) because a dead raising path
        # means the exceptional lane of the contract constrains nothing an impl
        # could get wrong, which is a spec that is too weak, not one too strong.
        "module": _swap(
            _BASE, _A_VALIDATE,
            "    if violated:\n"
            "        Assert(False)\n"
            "        raise ValidationFailure()\n"
            "    return\n",
        ),
        "refinement": "not a candidate implementation and not a refinement claim: "
                      "an instrumentation probe. `Assert(False)` is not something a "
                      "real patch could contain, so there is nothing to resolve -- "
                      "it exists to keep the sibling reject cases honest.",
        "rationale": "REJECT on the ASSERT, which is the non-vacuity signal: "
                     "'Assert might fail. Assertion False might not hold.' at the "
                     "spliced line. That the verifier cannot discharge False at "
                     "the raise site is precisely the fact that `violated` is "
                     "satisfiable there, so the raising branch is live and the "
                     "wrong-exception-type and always-raises rejections are "
                     "statements about a reachable path. A `verified` outcome here "
                     "would mean the branch is infeasible and those rejections are "
                     "vacuous.",
    },

    # ---- PARTIAL-DOMAIN / VALUE rivals ----
    {
        "id": "weak-equal-drops-classifier",
        "kind": "uniqueness",
        "expect": "reject",
        # The prepatch __eq__: compares everything EXCEPT the classifier. Diverges
        # on the sub-domain a_key==b_key but a_code is not b_code (returns True
        # where the spec requires False).
        "module": _swap(
            _BASE, _A_EQUAL,
            "    return a_key == b_key\n",
        ),
        "refinement": "the pre-patch __eq__ (no violation_error_code conjunct) "
                      "reports two rules that differ ONLY in classifier as equal; "
                      "test_eq (CheckConstraintTests / UniqueConstraintTests) "
                      "assertNotEqual on exactly that pair fails. It would NOT "
                      "resolve (this is model_prepatch_3).",
        "rationale": "REJECT from Ensures(Result()==(a_key==b_key and a_code is "
                     "b_code)): on a_key==b_key, a_code is not b_code the impl "
                     "returns True but the spec requires False.",
    },
    {
        "id": "weak-equal-only-classifier",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the payload conjunct: compares ONLY the classifier. Diverges where
        # a_code is b_code but a_key != b_key (returns True where spec needs False).
        "module": _swap(
            _BASE, _A_EQUAL,
            "    return a_code is b_code\n",
        ),
        "refinement": "ignoring the non-classifier facets (name/fields/check) "
                      "reports two structurally-different rules that happen to "
                      "share a classifier as equal — breaking the pre-existing "
                      "__eq__ contract the P2P equality tests (and the unchanged "
                      "facets of test_eq) rely on. It would NOT resolve.",
        "rationale": "REJECT from the postcondition: on a_code is b_code with "
                     "a_key != b_key the impl returns True, the spec requires "
                     "False.",
    },
    {
        "id": "weak-equal-eqeq-on-token",
        "kind": "uniqueness",
        "expect": "reject",
        # Uses `==` instead of `is` on the classifier token. The spec pins the
        # classifier comparison to identity (`is`). `==` and `is` need not coincide
        # over the full Optional[int] token domain (non-interned ints), so the
        # verifier cannot prove the boolean equals the `is`-based spec predicate.
        "module": _swap(
            _BASE, _A_EQUAL,
            "    return a_key == b_key and a_code == b_code\n",
        ),
        "refinement": "the model pins classifier comparison to identity `is` "
                      "(faithful to the interned-string `==` of the real __eq__, "
                      "mapping.md §2). `==` is not provably equal to `is` over the "
                      "whole token domain, so this is a genuinely different "
                      "predicate on the abstraction; it is a deliberate near-miss "
                      "whose refinement is the identity/equality token bijection — "
                      "a faithful `is`-based real patch is required.",
        "rationale": "REJECT from Ensures(...==(... and a_code is b_code)): the "
                     "verifier cannot discharge `a_code == b_code` <=> "
                     "`a_code is b_code` over Optional[int], so the postcondition "
                     "is not provable.",
    },
    {
        "id": "weak-kwnames-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Always names the classifier — even for the neutral None marker.
        "module": _swap(
            _BASE, _A_KWNAMES,
            "    return True\n",
        ),
        "refinement": "always emitting the violation_error_code kwarg (even when "
                      "the classifier is the neutral None) makes deconstruct() "
                      "advertise an absent classifier; test_deconstruction (which "
                      "asserts the key is OMITTED when no code is set) and "
                      "test_repr_with_violation_error_code fail. It would NOT "
                      "resolve.",
        "rationale": "REJECT from Ensures(Result()==(rule_code is not None)): on "
                     "rule_code is None the impl returns True, the spec requires "
                     "False.",
    },
    {
        "id": "weak-kwnames-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        # The prepatch deconstruct: never names the classifier.
        "module": _swap(
            _BASE, _A_KWNAMES,
            "    return False\n",
        ),
        "refinement": "the pre-patch deconstruct never emits violation_error_code; "
                      "test_deconstruction asserts a present classifier appears in "
                      "the kwargs, which fails. It would NOT resolve (this is "
                      "model_prepatch_4).",
        "rationale": "REJECT from Ensures(Result()==(rule_code is not None)): on a "
                     "present (non-None) classifier the impl returns False, the "
                     "spec requires True.",
    },
    {
        "id": "weak-configured-drops-code",
        "kind": "uniqueness",
        "expect": "reject",
        # The prepatch __init__: returns the neutral None regardless of input.
        "module": _swap(
            _BASE, _A_CONFIGURED,
            "    return None\n",
        ),
        "refinement": "the pre-patch constructor has no violation_error_code "
                      "parameter, so the configured classifier is dropped (always "
                      "None); test_custom_violation_code_message (asserts the "
                      "configured classifier is retained) fails. It would NOT "
                      "resolve (this is model_prepatch_2).",
        "rationale": "REJECT from Ensures(Result() is code): on a present "
                     "classifier the impl returns None, the spec requires the "
                     "supplied token.",
    },
    {
        "id": "weak-surfaced-drops-code",
        "kind": "uniqueness",
        "expect": "reject",
        # The prepatch violation site: ValidationError(msg) with no code -> None.
        "module": _swap(
            _BASE, _A_SURFACED,
            "    return None\n",
        ),
        "refinement": "the pre-patch validate() raises ValidationError(msg) with "
                      "NO code argument, so the surfaced failure carries None "
                      "instead of the rule's classifier; test_validate_custom_error "
                      "/ test_validate_conditon_custom_error (assert cm.exception."
                      "code == the classifier) fail. It would NOT resolve (this is "
                      "model_prepatch).",
        "rationale": "REJECT from Ensures(Result() is rule_code): on a present "
                     "classifier the impl returns None, the spec requires the "
                     "rule's own classifier token.",
    },
]


# No @ContractOnly axioms and no A-reference deep models in this bundle
# (meta.json axioms == [], deep_model_references == []). The single library
# value-flow (ValidationError store-verbatim `code`) is validated by
# axiom_check.py / G-AX against the real callee, not consumed by the Nagini proof,
# so the axiom lane has no obligation to probe here.
AXIOM_TESTS = []
